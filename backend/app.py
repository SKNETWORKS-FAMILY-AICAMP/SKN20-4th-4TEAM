import os
import warnings
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator, RootModel
import uvicorn
import json
from datetime import datetime
import re

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage 
from typing import List,Optional, Dict
from database import save_chat, create_chat_session
from sqlalchemy import text
from database import (
    get_user_by_email,
    create_user,
    verify_password,
    engine
)


templates = Jinja2Templates(directory="templates")
warnings.filterwarnings("ignore")
load_dotenv()

# 환경변수 확인
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY 없음! .env 확인해줘")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    print("⚠️ TAVILY_API_KEY 없음 - 웹검색 기능 사용 불가")

# ========================================
# FastAPI 앱 설정
# ========================================
app = FastAPI(title="창업 지원 AI 어시스턴트 API")

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 배포 시에는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 모델

class CalendarEvent(BaseModel):
    title: str = Field(description="일정 제목 (예: 지원사업 마감)")
    date: str = Field(description="YYYY-MM-DD 형식의 날짜")
    description: Optional[str] = Field(None, description="일정에 대한 간단한 설명")
    
    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v):
        """날짜 형식 검증"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            # 형식이 맞지 않으면 현재 연도로 시도
            raise ValueError(f'날짜는 YYYY-MM-DD 형식이어야 합니다: {v}')

class CalendarEventList(RootModel[List[CalendarEvent]]):
    pass

class ChatRequest(BaseModel):
    question: str
    chat_history: List[dict] = []
    session_id: int | None = None

class LoginRequest(BaseModel):
    email: str
    password: str
    session_id: int | None = None

# ✅ 수정 1: ChatResponse에 session_id 필드 추가
class ChatResponse(BaseModel):
    answer: str
    source_type: str  # "internal-rag", "web-search", "fallback"
    calendar_suggestion: Optional[List[CalendarEvent]] = None
    session_id: Optional[int] = None  # ← 추가

class SaveEventRequest(BaseModel):
    title: str
    date: str
    description: Optional[str] = None

# ========================================
# 벡터DB 및 LLM 초기화
# ========================================
print("📚 벡터DB 로딩 중...")
embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# 벡터DB 경로 확인
vectorstore_path = "./chroma_startup_all"
if not os.path.exists(vectorstore_path):
    print(f"⚠️ 경고: {vectorstore_path} 디렉토리가 없습니다.")
    print("벡터DB를 먼저 생성해주세요.")

try:
    vectorstore = Chroma(
        persist_directory=vectorstore_path,
        collection_name="startup_all_rag",
        embedding_function=embedding_model,
    )
    
    all_data = vectorstore.get()
    ids = all_data.get("ids", [])
    print(f"✅ 벡터DB 로드 완료 / 총 벡터 개수: {len(ids)}")
except Exception as e:
    print(f"❌ 벡터DB 로드 실패: {e}")
    print("벡터DB 없이 실행됩니다. 웹검색과 Fallback만 사용 가능합니다.")
    vectorstore = None

# LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ========================================
# 프롬프트 정의
# ========================================

CONTEXTUALIZE_Q_SYSTEM_PROMPT = """
너는 사용자의 질문이 매우 짧거나 불완전해도, 
최근 채팅 히스토리를 활용해 *의미가 명확한 독립 질문*을 반드시 생성하는 역할이다.

규칙:
1. 히스토리에 등장한 주제(예: 창업 지원, 공간, 입주 요건, 지원금 등)를 분석한다.
2. 현재 질문이 짧거나 모호하면 히스토리에서 가장 최근 주제를 자동으로 결합해 명확한 질문으로 만든다.
3. 단어 1~4자짜리 질문(예: '안양은?', '창원?')도 반드시 완전한 질문으로 재작성한다.
4. 단순히 원문을 되풀이하지 않는다.
5. 절대 답변하지 말고, 독립된 질문만 반환한다.

출력: 사용자가 실제로 물어보려는 의도를 완전히 드러내는 질문 1개만 출력.
"""

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
        ])

# 관련성 검증 프롬프트
relevance_check_prompt = ChatPromptTemplate.from_template("""
당신은 문서와 질문의 관련성을 엄격하게 판단하는 전문가입니다.

[질문]
{question}

[검색된 문서 샘플]
{documents}

[판단 기준]
1. 질문의 핵심 주제와 문서의 내용이 직접적으로 관련되는가?
2. 문서가 질문에 대한 구체적인 정보를 제공하는가?
3. 단순히 유사한 단어가 있는 것이 아니라, 실제 답변 가능한 내용인가?

다음 중 하나로만 답변: "관련있음" 또는 "관련없음"

답변:""")

# Query Transformation
qt_prompt = ChatPromptTemplate.from_template("""
다음 사용자 질문을 벡터 검색에 적합한 '핵심 키워드 중심 문장'으로 바꾸세요.
불필요한 말은 제거하고, 핵심 조건만 남기세요.

원본 질문: {question}

변환된 검색용 문장:""")

# 멀티쿼리 생성
multi_query_prompt = ChatPromptTemplate.from_template("""
다음 질문에 대해 3가지 다른 관점의 검색 쿼리를 생성하세요.
각 쿼리는 한 줄로 구분하여 출력하세요.
번호나 설명 없이 쿼리만 출력하세요.

원본 질문: {question}""")

# 기본 RAG 프롬프트
rag_prompt = ChatPromptTemplate.from_messages([
    ("system", """
당신은 예비·초기 창업자를 도와주는 '창업 지원 통합 AI 어시스턴트'입니다.
     
[중요: 현재 시점]
- 오늘 날짜: 2026년 1월 11일
- 사용자가 "4월", "3월" 등 월만 언급하면 → 2026년을 의미합니다
- 문맥에 202６년 이하 과거 날짜만 있는 경우:
  * 절대 연도를 2026년으로 바꾸지 마세요
  * "2026년 일정은 아직 공지되지 않았습니다" 안내
  * 과거 정보를 현재/미래 정보로 변조하지 마세요
- 사용자가 원하는 것은 2026년 정보이지만, 없으면 솔직히 말하세요

[사용 가능한 정보 유형]
- 지원사업 공고 (announcement)
- 실패/재도전 사례 (cases)
- 창업 공간 정보 (space)
- 법령: 중소기업창업 지원법 등 (law)
- 통계, 매뉴얼 등 참고 자료

[답변 원칙]
1. 반드시 제공된 문맥(Context) 안의 정보만 사용하세요.
2. 문맥에 없는 내용은 추측하지 말고 솔직하게 말하세요.
3. 질문 성격에 따라 다음 정보 유형을 우선 활용하세요.
   - 지원사업·신청 가능 여부 → announcement
   - 법적 정의·자격 요건 → law
   - 조언·주의점 → cases
   - 공간·입주 → space
4. 핵심 답변 후 필요하면 bullet로 정리하세요.
5. 마지막에 참고 근거 유형을 요약하세요.
6. ⚠️ 날짜 관련 답변 시 반드시 연도를 명시하세요.
"""),
    ("human", "[문맥]\n{context}\n\n[질문]\n{question}\n\n[답변]")
])

# 법령 전용 프롬프트
law_prompt = ChatPromptTemplate.from_messages([
    ("system", """
당신은 중소기업창업 지원법을 바탕으로 창업 제도와 요건을 설명하는 AI입니다.

[규칙]
1. 반드시 문맥에 있는 법령 내용만 사용하세요.
2. 가능하면 조문 번호(제○조)를 함께 제시하세요.
3. 문맥에 없는 내용은 "제공된 법령 문서에서 해당 내용은 확인되지 않습니다."라고 답하세요.
4. 답변 끝에 "※ 본 답변은 일반 정보 제공이며, 구체적인 법률 자문은 아닙니다."를 포함하세요.
"""),
    ("human", "[법령 문맥]\n{context}\n\n[질문]\n{question}\n\n[설명]")
])

# 지원사업 추천 프롬프트
recommend_prompt = ChatPromptTemplate.from_messages([
    ("system", """
당신은 예비·초기 창업자에게 가장 적합한 지원사업을 추천하는 전문가 AI입니다.

[목표]
사용자의 조건(나이, 지역, 업종, 창업 단계 등)을 기준으로
'실질적인 도움이 되는 사업(자금·공간·R&D·시제품·교육)'을 우선적으로 추천합니다.

[추천 우선순위]
1. 현금성 지원(사업화 자금, 시제품 제작비, R&D)
2. 입주 공간, 장비 지원
3. 액셀러레이팅, 멘토링
4. 단순 교육/특강은 마지막 순위

[추천 규칙]
1. 반드시 announcement 문서만 사용
2. 사용자 조건과 '지역·연령·단계·업종'이 명확히 맞는 것만 추천
3. 최대 2개까지만 추천
4. 조건이 맞는 사업이 없으면 솔직하게 말하기
5. IT·서비스업이면 '기술·콘텐츠·플랫폼' 키워드 포함 사업 우선

[출력 형식]
▪ 추천 사업명
▪ 왜 이 사용자에게 적합한지
▪ 지원 내용(자금/공간/교육 중 무엇인지 명확히)
▪ 신청 대상 요약
▪ 접수 기간
▪ 주의사항

마지막 줄: [참고: 지원사업 공고]
"""),
    ("human", "[지원사업 문맥]\n{context}\n\n[사용자 조건]\n{question}\n\n위 형식에 맞춰 추천해 주세요.")
])

# ✅ 수정 4: 일정 추출 프롬프트 개선 (더 명확한 지시)
EXTRACT_SCHEDULE_PROMPT = """
당신은 창업 지원 관련 대화에서 **캘린더에 저장 가능한 확정 일정만 추출하는 전문 비서**입니다.

[중요: 현재 시점]
- 오늘 날짜: 2026년 1월 11일
- 사용자가 "3월"이라고 하면 → 2026년 3월을 의미합니다
- 사용자가 "올해"라고 하면 → 2026년을 의미합니다
- 과거(2026년 1월 11일 이전)의 일정은 절대 추출하지 마세요

[대화 컨텍스트]
- 원래 질문: {question}
- AI 답변: {answer}

[추출 규칙] ⚠️ 매우 중요
1. 답변에서 다음 정보를 찾아 JSON 배열로 반환하세요:
   - 지원사업명, 공고명, 프로그램명, 컨퍼런스명, 행사명
   - 마감일, 접수 기간, 신청 기한, 행사 날짜

2. 날짜 표현 처리 (반드시 2026년 기준):
   - "3월 15일" → "2026-03-15"
   - "3월 중순" → "2026-03-15"
   - "3월 말" → "2026-03-31"
   - "6월 10일" → "2026-06-10"
   - 연도가 없는 모든 날짜 → **무조건 2026년**으로 가정

3. ⭐ 특별 규칙: 기간 일정 처리 (매우 중요!)
   
   A. 기간 표현 패턴 인식:
   - "3월 11일부터 13일까지"
   - "3월 11일 ~ 13일"
   - "3/11 ~ 3/13"
   - "3/11-3/13"
   - "접수: 3.11 ~ 3.13"
   - "기간: 3월 11일(화) ~ 13일(목)"
   
   B. 같은 행사명 + 연속된 날짜 = 기간 일정:
   답변에 다음과 같이 나오면:
   - IFS 창업박람회 2026-04-02
   - IFS 창업박람회 2026-04-03  
   - IFS 창업박람회 2026-04-04
   
   이것은 **3일짜리 기간 일정**입니다!
   
   C. 기간 일정 처리 방법:
   같은 제목의 행사가 여러 날짜에 있으면 → **첫날과 마지막날만** 추출
   
   올바른 출력:
   [
     {{
       "title": "[시작] IFS 창업박람회",
       "date": "2026-04-02",
       "description": "행사 시작 (기간: 4/2~4/4)"
     }},
     {{
       "title": "[마감] IFS 창업박람회",
       "date": "2026-04-04",
       "description": "행사 종료 (기간: 4/2~4/4)"
     }}
   ]
   
   잘못된 출력 (절대 금지):
   ❌ 3개로 분리 (4/2, 4/3, 4/4)
   ❌ [시작], [마감] 태그 없이 추출
   
   D. 단일 날짜 행사:
   하루짜리 행사는 1개만 추출, [시작]/[마감] 태그 불필요
   
   E. 여러 행사 혼합:
   - IFS 창업박람회 (4/2~4/4) → 2개 ([시작], [마감])
   - 베페 베이비페어 (4/2~4/4) → 2개 ([시작], [마감])
   - 단일 세미나 (4/5) → 1개
   
4. ❗ 과거 일정 절대 금지
   - 2026년 1월 11일 **이전**의 날짜는 절대 추출하지 마세요
   - 답변에 "2025년", "2024년" 등이 있으면 → 해당 일정 제외
   - 과거 행사는 이미 끝났으므로 캘린더에 저장할 필요 없음

5. ❗ 날짜를 정확히 특정할 수 없는 경우
   (예: 날짜 미정, 전국 순회, 추후 공지, 빈 문자열 등)
   → ❌ 해당 항목은 절대 JSON에 포함하지 마세요

6. 중복 제거 필수:
   같은 행사명이 여러 번 나오면 → 시작일/마지막일만 추출
   중간 날짜는 모두 생략

7. 출력은 반드시 JSON 배열만 허용합니다
   - 일정이 없으면 반드시 [] 만 출력하세요
   - 다른 설명, 주석, 문장은 절대 출력하지 마세요
   - ```json 같은 마크다운 코드블록도 사용하지 마세요

[출력 형식]
[
  {{
    "title": "행사명 또는 지원사업명",
    "date": "YYYY-MM-DD",
    "description": "간단한 설명"
  }}
]

[구체적 예시]

예시 1 - 기간 일정 (3일 행사):
입력 데이터:
- IFS 창업박람회 2026-04-02
- IFS 창업박람회 2026-04-03
- IFS 창업박람회 2026-04-04

출력:
[
  {{
    "title": "[시작] IFS 창업박람회",
    "date": "2026-04-02",
    "description": "행사 시작 (4/2~4/4)"
  }},
  {{
    "title": "[마감] IFS 창업박람회",
    "date": "2026-04-04",
    "description": "행사 종료 (4/2~4/4)"
  }}
]

예시 2 - 여러 기간 행사 혼합:
입력:
- A행사 4/2, 4/3, 4/4
- B행사 4/5, 4/6
- C세미나 4/10 (하루)

출력:
[
  {{"title": "[시작] A행사", "date": "2026-04-02"}},
  {{"title": "[마감] A행사", "date": "2026-04-04"}},
  {{"title": "[시작] B행사", "date": "2026-04-05"}},
  {{"title": "[마감] B행사", "date": "2026-04-06"}},
  {{"title": "C세미나", "date": "2026-04-10"}}
]

예시 3 - 접수 기간 표현:
입력: "접수: 3/11 ~ 3/13"
출력:
[
  {{"title": "[시작] 접수", "date": "2026-03-11"}},
  {{"title": "[마감] 접수", "date": "2026-03-13"}}
]

[잘못된 예시]
❌ {{"title": "행사", "date": "2025-06-10"}} → 과거 날짜
❌ {{"title": "IFS박람회", "date": "2026-04-02"}}, {{"title": "IFS박람회", "date": "2026-04-03"}} → 중복, [시작]/[마감] 없음
❌ {{"title": "행사", "date": ""}} → 날짜 없음
❌ 같은 행사를 3개로 쪼갬

[올바른 예시]
✅ {{"title": "[시작] AI 컨퍼런스", "date": "2026-03-15"}}
✅ {{"title": "[마감] AI 컨퍼런스", "date": "2026-03-17"}}
✅ {{"title": "단일 세미나", "date": "2026-04-10"}}
✅ [] → 추출 가능한 일정이 없을 때

⚠️ 금지 사항:
- "date": "" 사용 금지
- 날짜 추측 금지
- 과거 날짜(2026-01-11 이전) 추출 금지
- 기간 일정을 날짜별로 쪼개기 금지
- 같은 행사명 중복 추출 금지
- [시작]/[마감] 태그 누락 금지
- 마크다운 코드블록(```json) 사용 금지
"""


# Fallback 프롬프트
fallback_prompt = ChatPromptTemplate.from_template("""
질문: {question}

내부 문서에서 관련 정보를 찾지 못했습니다.
일반적인 지식을 바탕으로 답변해주세요.

답변:""")

# 체인 생성
qt_chain = qt_prompt | llm | StrOutputParser()
multi_query_chain = multi_query_prompt | llm | StrOutputParser()
relevance_chain = relevance_check_prompt | llm | StrOutputParser()
fallback_chain = fallback_prompt | llm | StrOutputParser()
contextualize_q_chain = contextualize_q_prompt | llm | StrOutputParser()

# ✅ 수정 4: JsonOutputParser 사용으로 변경
extract_prompt_template = ChatPromptTemplate.from_template(EXTRACT_SCHEDULE_PROMPT)
extract_chain = extract_prompt_template | ChatOpenAI(model="gpt-4o-mini", temperature=0) | StrOutputParser()


# ========================================
# 헬퍼 함수
# ========================================

def choose_prompt(question: str):
    """질문 유형에 따라 적절한 프롬프트 선택"""
    recommend_keywords = ["추천", "맞는", "신청할 수 있는", "지원해주는", 
                         "사업 알려줘", "혜택", "지원금", "지원사업"]
    law_keywords = ["정의", "자격", "요건", "지원법", "법에서", "법상", "제도", "시행", "규정"]
    
    if any(k in question for k in recommend_keywords):
        return recommend_prompt, "recommend_prompt"
    if any(k in question for k in law_keywords):
        return law_prompt, "law_prompt"
    return rag_prompt, "rag_prompt"

def format_docs_as_context(docs):
    """RAG 프롬프트에 넣기 좋은 컨텍스트로 변환 (출처 메타데이터 포함)"""
    if not docs:
        return ""
    parts = []
    for i, d in enumerate(docs, 1):
        if isinstance(d, Document):
            src = d.metadata.get("source", d.metadata.get("url", "unknown"))
            parts.append(f"[문서 {i}] (출처: {src})\n{d.page_content}")
    return "\n\n---\n\n".join(parts)

def search_documents(queries, k_per_query=10):
    """vectorstore에서 멀티쿼리 검색 후 중복제거 → (Document, similarity) 리스트 반환"""
    if vectorstore is None:
        return []
    
    all_docs_with_scores = []
    seen_contents = set()

    for q in queries:
        try:
            docs_with_scores = vectorstore.similarity_search_with_score(q, k=k_per_query)
        except Exception as e:
            print("⚠️ vectorstore.similarity_search_with_score 오류:", e)
            docs_with_scores = []

        for doc, distance in docs_with_scores:
            if doc.page_content in seen_contents:
                continue
            seen_contents.add(doc.page_content)
            similarity = max(0.0, 1.0 - (distance / 2.0))
            all_docs_with_scores.append((doc, similarity))
            
    return all_docs_with_scores

def filter_by_similarity(docs_with_scores, threshold=0.3):
    return [(doc, sim) for doc, sim in docs_with_scores if sim >= threshold]

def check_relevance(question, docs_with_scores):
    """LLM에게 상위 N개 문서로 관련성 물어보기 -> True/False 반환"""
    top_docs = docs_with_scores[:5]
    if not top_docs:
        return False
    docs_text = "\n\n---\n\n".join(
        f"[문서 {i+1}] (출처: {doc.metadata.get('source', 'unknown')})\n{doc.page_content[:600]}"
        for i, (doc, _) in enumerate(top_docs)
    )
    try:
        res = relevance_chain.invoke({"question": question, "documents": docs_text})
        return "관련있음" in res
    except Exception as e:
        print(f"⚠️ 관련성 검증 오류: {e}")
        return False

def web_search(query: str, k=3):
    """Tavily API 기반 웹검색"""
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY가 설정되지 않았습니다.")
    
    try:
        retriever = TavilySearchAPIRetriever(k=k)
        results = retriever.invoke(query) 

        docs = []
        for r in results:
            if isinstance(r, Document):
                docs.append(r)
            elif isinstance(r, dict):
                content = r.get("content") or r.get("snippet") or r.get("title") or str(r)
                docs.append(Document(
                    page_content=content,
                    metadata={"source": "web", "url": r.get("url", "unknown")}
                ))
            else:
                docs.append(Document(
                    page_content=str(r),
                    metadata={"source": "web"}
                ))
        return docs
        
    except Exception as e:
        raise RuntimeError(f"Tavily 웹검색 오류: {e}")

def rag_answer_from_docs(question: str, documents):
    """문서 리스트를 받아 RAG 응답 생성"""
    docs = []
    for item in documents:
        if isinstance(item, tuple):
            docs.append(item[0])
        else:
            docs.append(item)
    
    context = format_docs_as_context(docs)
    if not context.strip():
        print("⚠️ context 비어있음 -> fallback LLM으로 이동")
        return fallback_chain.invoke({"question": question})

    prompt, pname = choose_prompt(question)
    print(f"[프롬프트 사용] {pname} (문서 기반)")
    
    try:
        answer = (prompt | llm | StrOutputParser()).invoke({
            "context": context,
            "question": question
        })
        return answer
    except Exception as e:
        print(f"⚠️ RAG 생성 오류: {e}")
        return fallback_chain.invoke({"question": question})


# ========================================
# 일정 추출 함수
# ========================================

def parse_date_flexibly(date_str: str) -> str:
    """다양한 날짜 표현을 YYYY-MM-DD 형식으로 변환"""
    current_year = 2026
    
    # 이미 YYYY-MM-DD 형식인 경우
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    # "3월 15일" 형식
    match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', date_str)
    if match:
        month, day = match.groups()
        return f"{current_year}-{int(month):02d}-{int(day):02d}"
    
    # "3월 중순" 형식
    match = re.search(r'(\d{1,2})월\s*중순', date_str)
    if match:
        month = match.group(1)
        return f"{current_year}-{int(month):02d}-15"
    
    # "3월 말" 형식
    match = re.search(r'(\d{1,2})월\s*말', date_str)
    if match:
        month = int(match.group(1))
        # 월별 마지막 날
        last_days = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 
                    7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
        return f"{current_year}-{month:02d}-{last_days.get(month, 30):02d}"
    
    return date_str

# ✅ 수정 4: JSON 추출 로직 대폭 개선
def extract_json_from_text(text: str) -> str:
    """LLM 응답에서 JSON 배열만 정확히 추출"""
    # 1. 마크다운 코드블록 제거
    text = re.sub(r'```json\s*|\s*```', '', text)
    
    # 2. JSON 배열 찾기 (가장 큰 배열 선택)
    json_pattern = r'\[[\s\S]*?\]'
    matches = re.findall(json_pattern, text)
    
    if not matches:
        return "[]"
    
    # 가장 긴 매칭 (가장 완전한 JSON일 가능성 높음)
    longest_match = max(matches, key=len)
    return longest_match.strip()

def extract_calendar_events(question: str, answer: str) -> List[CalendarEvent]:
    """
    [대폭 개선된 함수]
    - JSON 추출 로직 강화
    - 더 상세한 로깅
    - 오류 처리 개선
    """
    try:
        print(f"📅 일정 추출 시작...")
        print(f"   질문: {question[:100]}...")
        print(f"   답변 길이: {len(answer)} 문자")
        
        # LLM에게 일정 추출 요청
        raw_result = extract_chain.invoke({
            "question": question,
            "answer": answer
        })
        
        print(f"   📝 LLM 원본 응답: {raw_result[:300]}...")
        
        # ✅ 개선된 JSON 추출
        json_text = extract_json_from_text(raw_result)
        print(f"   🔍 추출된 JSON: {json_text[:200]}...")
        
        # JSON 파싱
        try:
            events_data = json.loads(json_text)
            
            if not isinstance(events_data, list):
                print(f"⚠️ 응답이 리스트가 아님: {type(events_data)}")
                return []
            
            if len(events_data) == 0:
                print("ℹ️ 추출된 일정이 없습니다 (빈 배열)")
                return []
            
            # CalendarEvent 객체로 변환
            calendar_events = []
            for idx, item in enumerate(events_data):
                try:
                    # 날짜 필드가 없거나 비어 있으면 스킵
                    raw_date = item.get("date", "").strip()
                    if not raw_date:
                        print(f"   ⚠️ 일정 #{idx+1}: 날짜 없음 → 스킵")
                        continue

                    # 날짜 파싱
                    parsed_date = parse_date_flexibly(raw_date)
                    item["date"] = parsed_date
                    
                    event = CalendarEvent(**item)
                    calendar_events.append(event)
                    print(f"   ✅ 일정 #{idx+1} 추출 성공: {event.title} ({event.date})")

                except Exception as e:
                    print(f"   ⚠️ 일정 #{idx+1} 파싱 실패: {e}")
                    print(f"      데이터: {item}")
                    continue
            
            print(f"📅 최종 추출 완료: 총 {len(calendar_events)}개 일정")
            return calendar_events
            
        except json.JSONDecodeError as je:
            print(f"❌ JSON 파싱 실패: {je}")
            print(f"   시도한 JSON: {json_text}")
            return []
            
    except Exception as e:
        print(f"❌ 일정 추출 중 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
        return []

# ✅ 수정 3: 일정 추출 의도 감지 함수 완화
def detect_schedule_intent(question: str, answer: str) -> bool:
    """
    [개선된 함수]
    더 유연한 일정 추출 조건
    - 답변에 날짜가 있으면 일정 추출 시도
    """
    # 기본 키워드 체크
    schedule_keywords = [
        "기록", "저장", "캘린더", "일정",
        "마감", "접수", "신청기간", "기한",
        "언제까지", "마감일", "접수기간",
        "신청 기간", "모집 기간"
    ]
    
    question_lower = question.lower()
    if any(k in question_lower for k in schedule_keywords):
        print("🔍 일정 키워드 감지됨")
        return True
    
    # ✅ 개선: 답변에 날짜 패턴이 있으면 무조건 시도
    date_patterns = [
        r'\d{4}[-./]\d{1,2}[-./]\d{1,2}',  # 2026-03-15
        r'\d{1,2}월\s*\d{1,2}일',          # 3월 15일
        r'\d{1,2}월\s*(초|중순|말)',        # 3월 말
        r'(접수|마감|신청)\s*(기간|기한)',  # 접수 기간
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, answer):
            print(f"🔍 답변에서 날짜 패턴 발견: {pattern}")
            return True
    
    print("ℹ️ 일정 관련 내용 없음")
    return False

# ========================================
# 메인 RAG 함수
# ========================================
def multi_query_rag_with_qt(question: str, chat_history: List[dict], top_k=10, similarity_threshold=0.3):
    """
    전체 흐름:
      1) 독립 질문 생성 (Contextualize)
      2) 쿼리 트랜스폼 (QT) - 내부 RAG용
      3) 멀티쿼리 생성 (MQ)
      4) 벡터검색
      5) 최종 분기: 내부 RAG vs. 웹검색/Fallback
      6) [수정] 일정 추출 로직 개선
      
    Returns:
        tuple: (answer, source_type, calendar_events)  ← ✅ 항상 3개 반환
    """
    lc_chat_history = []
    for msg in chat_history :
        if msg.get('role')== 'user':
            lc_chat_history.append(HumanMessage(content=msg['content']))
        elif msg.get('role') == 'assistant':
            lc_chat_history.append(AIMessage(content=msg['content']))

    # 1. 독립 질문 생성 (Contextualize)
    try:
        standalone_question = contextualize_q_chain.invoke({
            'chat_history' : lc_chat_history,
            'input' : question
        })
    except Exception as e:
        print(f'⚠️ 질문 재구성 오류: {e}. 원본 질문 사용.')
        standalone_question = question

    print(f'[히스토리] 독립 질문: {standalone_question}')

    # 2. Query Transform
    try:
        qt_result = qt_chain.invoke({"question": standalone_question})
        if isinstance(qt_result, str):
            rag_qt_query = qt_result
        elif hasattr(qt_result, "content"):
            rag_qt_query = qt_result.content
        elif isinstance(qt_result, dict):
            rag_qt_query = qt_result.get("text") or qt_result.get("output")
        else:
            rag_qt_query = standalone_question
    except Exception as e:
        print(f"[QT ERROR] {e}")
        rag_qt_query = standalone_question

    print(f"[QT] 변환: {rag_qt_query}")
    
    # 3. 멀티 쿼리 (MQ)
    try:
        mq_text = multi_query_chain.invoke({"question": rag_qt_query})
        queries = [line.strip() for line in mq_text.splitlines() if line.strip()]
    except Exception as e:
        queries = [rag_qt_query]
    print(f"[멀티쿼리] {len(queries)}개: {queries}")

    # 4. Vector search
    all_docs = search_documents(queries)
    print(f"[검색] 총 {len(all_docs)}개 문서 후보 확보")

    # 5. 유사도 필터링
    filtered_docs = filter_by_similarity(all_docs, similarity_threshold)
    print(f"[1차 필터링] 유사도 >={similarity_threshold}: {len(filtered_docs)}개")

    is_relevant = False
    
    if filtered_docs:
        print("[2차 필터링] LLM 관련성 검증 중...")
        is_relevant = check_relevance(standalone_question, filtered_docs)

    # 6. 최종 분기 로직
    if is_relevant:
        print("✅ 내부 RAG 실행 중...")
        useful = filtered_docs[:top_k]
        answer = rag_answer_from_docs(standalone_question, useful)
        source_type = "internal-rag"
    else:
        print("⚠️ 내부 문서 (없거나/무관) → 웹검색으로 전환")
        
        try:
            web_search_query = qt_chain.invoke({"question": standalone_question})
        except Exception as e:
            print(f"⚠️ 웹 쿼리 변환 오류: {e}")
            web_search_query = standalone_question
        print(f"[웹QT] 변환: {web_search_query}")

        try:
            web_docs = web_search(web_search_query)
        except Exception as e:
            print(f"⚠️ 웹검색 실패: {e}")
            answer = fallback_chain.invoke({"question": standalone_question})
            # ✅ 수정 2: 항상 3개 값 반환
            return answer, "fallback", []

        if not web_docs:
            print("⚠️ 웹검색 결과 없음 → LLM 자체지식으로 응답")
            answer = fallback_chain.invoke({"question": standalone_question})
            # ✅ 수정 2: 항상 3개 값 반환
            return answer, "fallback", []
        
        answer = rag_answer_from_docs(standalone_question, web_docs)
        source_type = "web-search"

    # 7. [개선된] 일정 추출 로직
    calendar_events = []
    
    # ✅ 수정 3: 개선된 의도 감지 함수 사용
    if detect_schedule_intent(question, answer):
        print("📅 일정 관련 내용 감지 → 일정 추출 시도")
        calendar_events = extract_calendar_events(standalone_question, answer)
        
        if calendar_events:
            print(f"✅ {len(calendar_events)}개 일정 추출 완료")
            for evt in calendar_events:
                print(f"   - {evt.title} ({evt.date})")
        else:
            print("⚠️ 일정을 추출하지 못했습니다")
    else:
        print("ℹ️ 일정 추출 조건 미충족")

    # ✅ 수정 2: 항상 3개 값 반환
    return answer, source_type, calendar_events

# ========================================
# API 엔드포인트
# ========================================
@app.get("/")
async def root():
    return {
        "message": "창업 지원 AI 어시스턴트 API가 실행 중입니다.",
        "vectordb_loaded": vectorstore is not None,
        "tavily_enabled": bool(TAVILY_API_KEY)
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        question = request.question.strip()
        chat_history = request.chat_history

        if not question:
            raise HTTPException(status_code=400, detail="질문이 비어있습니다.")

        print(f"\n{'='*60}")
        print(f"[API 요청] {question}")
        print(f"[API 요청] 히스토리 길이: {len(chat_history)}")
        print(f"{'='*60}")

        # ✅ 1. session_id 먼저 확보
        session_id = request.session_id
        if session_id is None:
            session_id = create_chat_session()
            print(f"[세션 생성] session_id={session_id}")

        # ✅ 2. 사용자 메시지 저장
        save_chat(
            session_id=session_id,
            role="user",
            content=question
        )

        # ✅ 3. RAG 실행 (3개 값 받기)
        answer, source_type, calendar_suggestion = multi_query_rag_with_qt(
            question, 
            chat_history
        )

        # ✅ 4. AI 응답 저장
        save_chat(
            session_id=session_id,
            role="assistant",
            content=answer,
            source_type=source_type
        )

        # ✅ 5. 응답 반환 (session_id 포함)
        return ChatResponse(
            answer=answer,
            source_type=source_type,
            calendar_suggestion=calendar_suggestion,
            session_id=session_id  # ✅ 수정 1: session_id 반환
        )

    except Exception as e:
        print(f"[API 오류] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{session_id}")
def get_chat_history(session_id: int):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT role, content
                FROM chat_log
                WHERE session_id = :sid
                ORDER BY created_at
            """),
            {"sid": session_id}
        )

        rows = result.fetchall()

    return [
        {"role": r.role, "content": r.content}
        for r in rows
    ]

@app.post("/login")
def login(request: LoginRequest):
    user = get_user_by_email(request.email)

    # 1️⃣ 회원 없으면 자동 회원가입 (정책상 OK라면)
    if user is None:
        user_id = create_user(request.email, request.password)
    else:
        # 2️⃣ 비밀번호 검증
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")
        user_id = user.user_id

    # 3️⃣ session_id가 있으면 세션에 user_id 연결
    if request.session_id:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE chat_sessions
                    SET user_id = :uid
                    WHERE session_id = :sid
                """),
                {"uid": user_id, "sid": request.session_id}
            )
            conn.commit()

    return {
        "user_id": user_id
    }

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {
        "status": "healthy",
        "vectordb": "loaded" if vectorstore else "not_loaded",
        "web_search": "enabled" if TAVILY_API_KEY else "disabled"
    }

@app.post("/analyze", response_model=ChatResponse)
async def analyze(request: ChatRequest):
    """
    사업계획서 AI 전문가 분석 엔드포인트
    - question: 분석할 사업계획서 내용
    - 반환: answer(분석 결과), source_type("ai-analysis")
    """
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="분석할 내용이 비어있습니다.")
        
        print(f"\n{'='*60}")
        print(f"[분석 API 요청] 질문 길이: {len(question)} 문자")
        print(f"{'='*60}")
        
        # 분석용 시스템 프롬프트
        analysis_system_prompt = """당신은 20년 경력의 벤처 투자 전문가이자 사업 컨설턴트입니다. 
사업계획서를 철저히 분석하고 구체적이고 실용적인 조언을 제공합니다."""
        
        # 기존 llm 객체 사용
        analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", analysis_system_prompt),
            ("human", "{question}")
        ])
        
        analysis_chain = analysis_prompt | llm | StrOutputParser()
        
        # 분석 실행
        answer = analysis_chain.invoke({"question": question})
        
        print(f"[분석 API 응답] 분석 결과 길이: {len(answer)} 문자")
        
        return ChatResponse(
            answer=answer, 
            source_type="ai-analysis",
            calendar_suggestion=None,
            session_id=None
        )
        
    except Exception as e:
        print(f"[분석 API 오류] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

@app.get("/my_calendar", response_class=HTMLResponse)
async def get_calendar_page(request: Request):
    # my_calendar.html 파일을 브라우저에 띄워줍니다.
    return templates.TemplateResponse("my_calendar.html", {"request": request})

@app.post("/my_calendar")
async def save_calendar_event(event: SaveEventRequest):
    try:
        print(f"📌 일정 기록 요청 수신: {event.title} - {event.date}")
        
        # TODO: 여기에 database.py의 저장 함수를 연결하면 실제 DB에 쌓입니다.
        # 예: save_calendar_event_to_db(event.title, event.date, event.description)
        
        return {"status": "success", "message": "일정이 캘린더에 기록되었습니다!"}
    except Exception as e:
        print(f"❌ 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# 서버 실행
# ========================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 창업 지원 AI 어시스턴트 API 서버 시작...")
    print("="*60)
    print(f"📚 벡터DB: {'✅ 로드됨' if vectorstore else '❌ 없음'}")
    print(f"🌐 웹검색: {'✅ 활성화' if TAVILY_API_KEY else '❌ 비활성화'}")
    print(f"🔗 서버 주소: http://localhost:8000")
    print(f"📖 API 문서: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)