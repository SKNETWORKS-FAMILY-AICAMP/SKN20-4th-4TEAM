import os
import warnings
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage 
from typing import List
from backend.database import save_chat



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
class ChatRequest(BaseModel):
    question: str
    chat_history: List[dict] = []

class ChatResponse(BaseModel):
    answer: str
    source_type: str  # "internal-rag", "web-search", "fallback"

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
      
    Returns:
        tuple: (answer, source_type)
    """
    lc_chat_history = []
    for msg in chat_history :
        if msg.get('role')== 'user':
            lc_chat_history.append(HumanMessage(content=msg['content']))
        elif msg.get('role') == 'assistant':
            lc_chat_history.append(AIMessage(content=msg['content']))

    # 1. 독립 질문 생성 (Contextualize) - LLM의 최종 답변 생성 및 웹 검색에 사용
    try:
        standalone_question = contextualize_q_chain.invoke({
            'chat_history' : lc_chat_history,
            'input' : question
        })
    except Exception as e:
        print(f'질문 재구성 오류: {e}. 원본 질문 사용.')
        standalone_question = question

    print(f'[히스토리] 독립 질문: {standalone_question}')

    # 2. 내부 RAG 검색용 Query Transform (QT) 
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

    print(f"[QT] 변환 (내부 RAG): {rag_qt_query}")
    
    # 3. 멀티 쿼리 (MQ) - 내부 RAG 검색에 사용
    try:
        mq_text = multi_query_chain.invoke({"question": rag_qt_query})
        queries = [line.strip() for line in mq_text.splitlines() if line.strip()]
    except Exception as e:
        queries = [rag_qt_query]
    print(f"[멀티쿼리] {len(queries)}개: {queries}")

    # 4. Vector search (멀티쿼리)
    all_docs = search_documents(queries)
    print(f"[검색] 총 {len(all_docs)}개 문서 후보 확보")

    # 5. 유사도 필터링
    filtered_docs = filter_by_similarity(all_docs, similarity_threshold)
    print(f"[1차 필터링] 유사도 >={similarity_threshold}: {len(filtered_docs)}개")

    is_relevant = False
    
    if filtered_docs:
        print("[2차 필터링] LLM 관련성 검증 중...")
        is_relevant = check_relevance(standalone_question, filtered_docs)

    # 6. 최종 분기: 내부 RAG vs. 웹 검색/Fallback
    if is_relevant:
        print("✅ 내부 문서가 질문과 관련있음 → 내부 RAG 실행")
        useful = filtered_docs[:top_k]
        # 최종 답변 생성에는 히스토리 반영된 독립 질문 사용
        answer = rag_answer_from_docs(standalone_question, useful)
        return answer, "internal-rag"
    else:
        print("⚠️ 내부 문서 (없거나/무관) → 웹검색으로 전환")
        
        # 6-1. 웹 검색 쿼리 최적화: standalone_question을 qt_chain에 재활용하여 검색 정확도 개선
        try:
            web_search_query = qt_chain.invoke({"question": standalone_question})
        except Exception as e:
            print(f"⚠️ 웹 쿼리 변환 오류: {e}")
            web_search_query = standalone_question
        print(f"[웹QT/재활용] 변환: {web_search_query}")

        try:
            # 최적화된 쿼리를 웹 검색에 사용
            web_docs = web_search(web_search_query)
        except Exception as e:
            print(f"⚠️ 웹검색 실패: {e}")
            answer = fallback_chain.invoke({"question": standalone_question})
            return answer, "fallback"

        if not web_docs:
            print("⚠️ 웹검색 결과 없음 → LLM 자체지식으로 응답")
            answer = fallback_chain.invoke({"question": standalone_question})
            return answer, "fallback"
        
        answer = rag_answer_from_docs(standalone_question, web_docs)
        return answer, "web-search"


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

        # 🔑 기본값 먼저 선언 (중요)
        source_type = "unknown"

        # 사용자 질문 저장
        save_chat(role="user", content=question)

        answer, source_type = multi_query_rag_with_qt(question, chat_history)

        # AI 응답 저장
        save_chat(role="assistant", content=answer)

        return ChatResponse(answer=answer, source_type=source_type)

    except Exception as e:
        print(f"[API 오류] {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        return ChatResponse(answer=answer, source_type="ai-analysis")
        
    except Exception as e:
        print(f"[분석 API 오류] {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

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