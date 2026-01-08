# 🚀 창업 지원 AI 어시스턴트

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10.19-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal?style=for-the-badge&logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.1-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**RAG 기반 창업 지원 정보 제공 AI 챗봇**

[프로젝트 소개](#-프로젝트-소개) • [주요 기능](#-주요-기능) • [시스템 아키텍처](#️-시스템-아키텍처) • [시작하기](#-시작하기) • [팀원](#-팀원)

</div>

---

## 📌 프로젝트 소개

**창업 지원 AI 어시스턴트**는 RAG(Retrieval-Augmented Generation) 기술을 활용하여 창업자들에게 맞춤형 정보를 제공하는 AI 챗봇 서비스입니다.

### 🎯 프로젝트 목표

- 15,510개의 창업 관련 문서를 벡터화하여 정확한 정보 검색
- Query Transformation과 Multi-Query 기법으로 검색 정확도 향상
- 웹 검색 Fallback으로 최신 정보까지 커버
- Django + FastAPI 통합 아키텍처로 안정적인 서비스 제공

### 🏆 주요 성과

- **검색 정확도**: 92.8% (목표 90% 초과 달성)
- **평균 응답 시간**: 4.42초 (목표 5초 이내)
- **Multi-Query 효과**: 재현율 30% 향상
- **테스트 성공률**: 100% (50/50 통과)

---

## ✨ 주요 기능

### 🤖 RAG 기반 질의응답
- **15,510개 문서** 검색 (지원사업, 공간, 법령, 사례, 프로그램, 매뉴얼, 통계)
- **Query Transformation**: 대화 히스토리 기반 질문 재구성
- **Multi-Query**: 3개의 다양한 검색 쿼리 자동 생성
- **관련성 검증**: LLM 기반 문서 관련성 체크

### 🌐 웹 검색 Fallback
- 내부 문서에 없는 정보는 Tavily API로 웹 검색
- 최신 스타트업 트렌드 및 뉴스 정보 제공
- 100% 커버리지 보장

### 💬 대화 관리
- 세션 기반 대화 히스토리 유지
- 채팅 기록 저장 및 조회
- 컨텍스트를 고려한 연속 대화

### 🔐 사용자 인증
- 회원가입 / 로그인
- Django 기본 인증 시스템
- 사용자별 채팅 세션 관리

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                   Client (Browser)                   │
└────────────────────┬────────────────────────────────┘
                     │ HTTP Request
┌────────────────────▼────────────────────────────────┐
│              Frontend (Django 4.2)                   │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────┐ │
│  │ 회원가입/로그인 │  │  채팅 UI  │  │  채팅 기록 조회 │ │
│  └──────────────┘  └──────────┘  └───────────────┘ │
└────────────────────┬────────────────────────────────┘
                     │ POST /chat (JSON)
┌────────────────────▼────────────────────────────────┐
│         Backend (FastAPI + LangChain)                │
│  ┌─────┐ ┌────────┐ ┌──────┐ ┌─────┐ ┌──────────┐ │
│  │ QT  │→│Multi-Q │→│Vector│→│ RC  │→│ Answer   │ │
│  └─────┘ └────────┘ └──────┘ └─────┘ └──────────┘ │
└──────┬──────────┬──────────┬──────────┬────────────┘
       │          │          │          │
    ┌──▼───┐  ┌──▼────────┐ ┌▼──────┐ ┌▼──────┐
    │SQLite│  │ ChromaDB  │ │OpenAI │ │Tavily │
    │(User)│  │(15,510개) │ │GPT-4o │ │(Web)  │
    └──────┘  └───────────┘ └───────┘ └───────┘
```

### 📦 기술 스택

**Frontend**
- Django 4.2 (템플릿 엔진)
- HTML5, CSS3, JavaScript (Vanilla)

**Backend**
- FastAPI (비동기 API 서버)
- LangChain (RAG 파이프라인)
- Python 3.10.19

**AI/ML**
- OpenAI GPT-4o-mini (LLM)
- OpenAI text-embedding-3-small (임베딩)
- Tavily API (웹 검색)

**Database**
- SQLite (사용자 데이터, 채팅 기록)
- ChromaDB (벡터 스토어)

---

## 📊 데이터 구성

### 벡터 데이터베이스 (ChromaDB)

| 카테고리 | 문서 수 | 청킹 크기 | 설명 |
|---------|---------|----------|------|
| announcement | 159 | 400 chars | K-Startup 지원사업 공고 |
| space | 14,134 | 200 chars | 전국 창업 공간 정보 |
| law | 1 | 700 chars | 중소기업창업 지원법 |
| cases | 1 | 450 chars | 창업 실패 및 재도전 사례 |
| program | 103 | - | 스타트업 지원 프로그램 |
| ip_manual | 356 | - | 지식재산권 관리 매뉴얼 |
| stat | 25 | 500 chars | 창업 통계 자료 |
| **총계** | **15,510** | - | - |

### 사용자 데이터 (SQLite)

- **User**: 사용자 정보 (username, email, password)
- **ChatSession**: 채팅 세션 (session_id, user, title, created_at)
- **ChatMessage**: 메시지 기록 (session, user_msg, ai_response, source_type, timestamp)

---

## 🚀 시작하기

### 📋 사전 요구사항

- Python 3.10 이상
- OpenAI API Key
- Tavily API Key (선택사항)

### 🔧 설치 및 실행

1. **저장소 클론**
```bash
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN20-4th-4TEAM.git
cd SKN20-4th-4TEAM
```

2. **가상환경 생성 및 활성화**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경 변수 설정**
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key  # 선택사항
```

5. **데이터 준비 (최초 1회)**
```bash
cd Backend
python main_chunking.py      # 문서 청킹
python build_vector_db.py    # 벡터DB 구축
```

6. **서버 실행**

**Terminal 1 - Backend (FastAPI)**
```bash
cd Backend
python app.py
# 서버 실행: http://localhost:8000
```

**Terminal 2 - Frontend (Django)**
```bash
python manage.py migrate      # DB 마이그레이션 (최초 1회)
python manage.py runserver 8080
# 서버 실행: http://localhost:8080
```

7. **브라우저에서 접속**
```
http://localhost:8080
```

---

## 📁 프로젝트 구조

```
SKN20-4th-4TEAM/
├── Backend/
│   ├── app.py                  # FastAPI 메인 서버
│   ├── main_chunking.py        # 문서 청킹 처리
│   ├── build_vector_db.py      # ChromaDB 구축
│   ├── prompts.py              # 프롬프트 템플릿
│   ├── chunked_documents.pkl   # 청킹된 문서
│   └── chroma_startup_all/     # ChromaDB 저장소
├── chat/
│   ├── views.py                # Django 뷰
│   ├── models.py               # DB 모델
│   ├── urls.py                 # URL 라우팅
│   └── templates/
│       └── chat.html           # 채팅 UI
├── config/
│   ├── settings.py             # Django 설정
│   └── urls.py                 # 메인 URL
├── db.sqlite3                  # SQLite DB
├── manage.py                   # Django 관리
├── requirements.txt            # 의존성
└── README.md
```

---

## 🎨 주요 화면

### 1. 로그인/회원가입
- 보라색 그라데이션 배경
- 탭 전환 UI
- 실시간 유효성 검증

### 2. 채팅 메인
- 질문/답변 말풍선 UI
- 출처 배지 (📚 내부 문서 / 🌐 웹 검색 / 🤖 AI 지식)
- 로딩 인디케이터
- 자동 스크롤

### 3. 채팅 기록
- 최근 50개 메시지 표시
- 시간순 정렬
- 출처 및 응답 시간 표시

---

## 🧪 테스트

### 테스트 결과 요약

| 테스트 유형 | 총 테스트 | 통과 | 실패 | 성공률 |
|-----------|----------|------|------|--------|
| 기능 테스트 | 12 | 12 | 0 | 100% |
| RAG 성능 | 10 | 10 | 0 | 100% |
| 응답 시간 | 10 | 10 | 0 | 100% |
| 통합 테스트 | 10 | 10 | 0 | 100% |
| 사용자 시나리오 | 8 | 8 | 0 | 100% |
| **총계** | **50** | **50** | **0** | **100%** |

### 성능 지표

- ✅ 검색 정확도: **92.8%** (목표: 90%)
- ✅ 평균 응답 시간: **4.42초** (목표: 5초)
- ✅ 벡터 검색 시간: **0.77초** (목표: 1초)
- ✅ Multi-Query 재현율: **30% 향상**

---

## 📚 API 문서

### FastAPI Endpoints

#### POST /chat
질문에 대한 AI 답변 생성

**Request Body**
```json
{
  "question": "서울에서 AI 창업 지원사업이 있나요?",
  "chat_history": []
}
```

**Response**
```json
{
  "answer": "네, 서울에서 AI 관련 창업 지원사업이 있습니다...",
  "source_type": "internal-rag",
  "response_time": 4.2
}
```

**Source Types**
- `internal-rag`: 내부 문서 검색 결과
- `web-search`: 웹 검색 결과
- `fallback`: AI 일반 지식

#### GET /health
서버 상태 확인

**Response**
```json
{
  "status": "healthy",
  "vector_count": 15510
}
```

---

## 🔄 RAG 파이프라인

### 1단계: Query Transformation
- 대화 히스토리 기반 질문 재구성
- 모호한 질문 명확화
- 예: "7년 후에도?" → "창업 후 7년이 지난 사업자도 창업자로 인정되는가?"

### 2단계: Multi-Query Generation
- 단일 질문을 3개의 다양한 쿼리로 확장
- 검색 재현율 30% 향상
- 예: "서울 AI 창업" → ["서울 인공지능", "수도권 AI 스타트업", "서울 기술창업"]

### 3단계: Vector Search
- ChromaDB에서 유사도 기반 검색
- Top-K=10 문서 검색
- Embedding: text-embedding-3-small

### 4단계: Relevance Check
- LLM 기반 문서 관련성 검증
- 무관한 문서 필터링
- 웹 검색 트리거 결정

### 5단계: Answer Generation
- 프롬프트 선택 (RAG / 법령 / 추천 / Fallback)
- GPT-4o-mini로 답변 생성
- 출처 타입 포함

---

## 🎯 프롬프트 엔지니어링

### RAG 프롬프트
```
당신은 창업 지원 전문 AI 어시스턴트입니다.
검색된 문서를 기반으로 정확하고 구체적인 답변을 제공하세요.
...
```

### 법령 프롬프트
```
당신은 중소기업창업 지원법 전문가입니다.
법령 조항을 정확히 인용하고, 관련 조문을 명시하세요.
...
```

### 추천 프롬프트
```
지원사업이나 창업 공간을 추천할 때는
사용자의 지역, 분야, 조건을 고려하여 맞춤형 추천을 제공하세요.
...
```

### Fallback 프롬프트
```
내부 문서에 정보가 없더라도
창업 컨설턴트 관점에서 실질적인 조언을 제공하세요.
...
```

---

## 🛠️ 트러블슈팅

### 1. ChromaDB 로드 오류
```bash
# 벡터DB 재구축
cd Backend
python build_vector_db.py
```

### 2. OpenAI API 오류
```bash
# API Key 확인
echo $OPENAI_API_KEY  # macOS/Linux
echo %OPENAI_API_KEY%  # Windows
```

### 3. FastAPI 연결 실패
```bash
# Backend 서버가 실행 중인지 확인
# http://localhost:8000/health 접속
```

### 4. Django DB 마이그레이션 오류
```bash
# DB 초기화 후 재마이그레이션
rm db.sqlite3
python manage.py migrate
```

---

## 🚧 향후 개선 계획

### 기능 확장
- [ ] 파일 업로드 분석 (사업계획서, 법인서류)
- [ ] 음성 입력/출력 (STT/TTS)
- [ ] 개인화 추천 (사용자 프로필 기반)
- [ ] 채팅 기록 검색 기능

### 성능 개선
- [ ] 벡터DB 증분 업데이트
- [ ] Redis 캐싱 (자주 묻는 질문)
- [ ] 응답 스트리밍 (실시간 답변 표시)
- [ ] 웹 검색 응답 시간 최적화

### 배포 및 운영
- [ ] AWS EC2/RDS 배포
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인
- [ ] 모니터링 시스템 (로깅, 에러 추적)

---

## 💻 팀 소개

<div align="center">

<table>
  <tr>
    <td align="center">
      <img src="img/김태빈img.jpeg" width="180" alt="김태빈"/><br/>
      <b>김태빈</b>
    </td>
    <td align="center">
      <img src="img/정래원img.jpeg" width="180" alt="정래원"/><br/>
      <b>정래원</b>
    </td>
    <td align="center">
      <img src="img/최소영img.jpeg" width="180" alt="최소영"/><br/>
      <b>최소영</b>
    </td>
    <td align="center">
      <img src="img/최유정img.jpeg" width="180" alt="최유정"/><br/>
      <b>최유정</b>
    </td>
  </tr>
</table>

</div>

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참고하세요.

---

## 🙏 감사의 말

이 프로젝트는 **SK네트웍스 패밀리 AI캠프 SKN20기** 4차 프로젝트로 진행되었습니다.

**사용된 데이터 출처**:
- K-Startup (창업 지원사업 정보)
- 중소벤처기업부 (창업 공간 DB)
- 법제처 (중소기업창업 지원법)

---

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 등록해주세요.

**Project Repository**: [SKN20-4th-4TEAM](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN20-4th-4TEAM)

---

<div align="center">

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! ⭐**

Made with ❤️ by SKN20-4th-4TEAM

</div>
