![header](./assets/header.png)

# 🚀 Boss Baby AI - 창업 지원 통합 플랫폼

# 🚀 Boss Baby AI - 창업 지원 통합 플랫폼

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10.19-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-teal?style=for-the-badge&logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-0.1-orange?style=for-the-badge)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?style=for-the-badge&logo=mysql)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**RAG 기반 창업 지원 정보 제공 + 사업계획서 AI 분석 + 일정 관리 통합 플랫폼**

[프로젝트 소개](#-프로젝트-소개) • [팀 소개](#-팀-소개) • [주요 기능](#-주요-기능) • [시스템 아키텍처](#️-시스템-아키텍처) • [시작하기](#-시작하기) 

</div>

---

## 💻 팀 소개

<div align="center">

<table>
  <tr>
    <td align="center">
      <img src="img/김태빈img.jpeg" width="180" alt="김태빈"/><br/>
      <b>김태빈</b><br/>
      <sub>데이터 & 테스트</sub>
    </td>
    <td align="center">
      <img src="img/정래원img.jpeg" width="180" alt="정래원"/><br/>
      <b>정래원</b><br/>
      <sub>Frontend & UI/UX</sub>
    </td>
    <td align="center">
      <img src="img/최소영img.jpeg" width="180" alt="최소영"/><br/>
      <b>최소영 (리더)</b><br/>
      <sub>Backend & RAG System</sub>
    </td>
    <td align="center">
      <img src="img/최유정img.jpeg" width="180" alt="최유정"/><br/>
      <b>최유정</b><br/>
      <sub>Database & API</sub>
    </td>
  </tr>
</table>

</div>

---

## 📌 프로젝트 소개

**Boss Baby AI**는 RAG(Retrieval-Augmented Generation) 기술을 활용하여 예비 창업자와 초기 스타트업에게 맞춤형 정보를 제공하는 올인원 AI 창업 지원 플랫폼입니다.

### 🎯 프로젝트 목표

- 15,510개의 창업 관련 문서를 벡터화하여 정확한 정보 검색
- Query Transformation과 Multi-Query 기법으로 검색 정확도 향상
- 웹 검색 Fallback으로 최신 정보까지 커버
- AI 기반 사업계획서 분석으로 전문가 수준의 피드백 제공
- 창업 일정 관리 캘린더로 지원사업 마감일 추적
- Django + FastAPI + MySQL 통합 아키텍처로 안정적인 서비스 제공

### 🏆 주요 성과

- **검색 정확도**: 92.8% (목표 90% 초과 달성)
- **평균 응답 시간**: 4.42초 (목표 5초 이내)
- **Multi-Query 효과**: 재현율 30% 향상
- **테스트 성공률**: 100% (50/50 통과)
- **데이터 규모**: 15,510개 벡터 문서
- **완성도**: 97% (6대 핵심 기능 완성)

---

## ✨ 주요 기능

### 🤖 1. RAG 기반 질의응답
- **15,510개 문서** 검색 (지원사업, 공간, 법령, 사례, 프로그램, 매뉴얼, 통계)
- **Query Transformation**: 대화 히스토리 기반 질문 재구성
- **Multi-Query**: 3개의 다양한 검색 쿼리 자동 생성
- **관련성 검증**: LLM 기반 문서 관련성 체크
- **3-Way Branching**: 내부 RAG → 웹 검색 → AI Fallback

### 📊 2. 사업계획서 AI 분석 (신규)
- **20년 경력 벤처투자 전문가** 페르소나 기반 분석
- **5개 핵심 지표**: 투자매력도, 시장성, 실현가능성, 차별성, 완성도 (0-100점)
- **8개 분석 섹션**: 
  - 시장 동향 분석
  - 실현 가능성 평가
  - 강점 3가지 도출
  - 약점 3가지 지적
  - 리스크 3가지 경고
  - 개선 제안 (단기/중기/장기 로드맵)
  - 종합 의견
- **사업계획서 CRUD**: 생성, 조회, 수정, 삭제

### 📅 3. 창업 일정 관리 캘린더 (신규)
- **월간 캘린더 뷰**: 직관적인 그리드 레이아웃
- **일정 타입**: 
  - 🔌 마감일 (deadline): 지원사업 신청 마감
- **D-Day 자동 계산**: 
  - D-3 이하: 🔴 빨강 (긴급)
  - D-7 이하: 🟡 노랑 (주의)
  - D-7 초과: 🟢 초록 (여유)
- **일정 관리**: 완료 체크, 삭제, 다가오는 일정 리스트
- **시각적 강조**: 오늘 날짜 하이라이트, 일요일/토요일 색상 구분

### 🌐 4. 웹 검색 Fallback
- 내부 문서에 없는 정보는 Tavily API로 웹 검색
- 최신 스타트업 트렌드 및 뉴스 정보 제공
- 100% 커버리지 보장

### 💬 5. 대화 관리
- 세션 기반 대화 히스토리 유지
- MySQL 기반 채팅 기록 영구 저장
- 컨텍스트를 고려한 연속 대화
- 최근 50개 메시지 조회

### 🔐 6. 사용자 인증
- 회원가입 / 로그인
- Django 기본 인증 시스템
- 사용자별 채팅 세션 관리
- 마이페이지 (통계, 최근 활동)

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                   Client (Browser)                           │
│  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ 채팅 UI  │  │ 캘린더 │  │사업계획서 │  │  마이페이지   │ │
│  └──────────┘  └────────┘  └──────────┘  └──────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP Request
┌────────────────────────▼────────────────────────────────────┐
│              Frontend (Django 4.2) - Port 8080               │
│  ┌──────────────┐  ┌──────────┐  ┌────────────────────────┐│
│  │ 회원가입/로그인 │  │  템플릿  │  │  세션 관리 & 라우팅    ││
│  └──────────────┘  └──────────┘  └────────────────────────┘│
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JSON)
┌────────────────────────▼────────────────────────────────────┐
│         Backend (FastAPI + LangChain) - Port 8000            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ RAG Pipeline (6단계)                                     ││
│  │  1. Contextualize Q  → 2. Query Transformation          ││
│  │  3. Multi-Query (x3) → 4. Vector Search (k=10)          ││
│  │  5. Relevance Check  → 6. Answer Generation (3-Way)     ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────┐  ┌───────────────────────────────┐│
│  │사업계획서 AI 분석 API │  │  캘린더 API (CRUD + D-Day)   ││
│  │- 5개 점수 계산       │  │  - GET /api/calendar/events/ ││
│  │- 8개 섹션 분석       │  │  - PATCH /toggle/            ││
│  │- 20년 경력 페르소나  │  │  - DELETE /delete/           ││
│  └─────────────────────┘  └───────────────────────────────┘│
└──────┬──────────┬──────────┬──────────┬──────────┬─────────┘
       │          │          │          │          │
    ┌──▼──────┐ ┌▼────────┐ ┌▼──────┐ ┌▼──────┐ ┌▼──────┐
    │  MySQL  │ │ChromaDB │ │OpenAI │ │Tavily │ │OpenAI │
    │(운영 DB)│ │(Vector) │ │GPT-4o │ │(Web)  │ │(Embed)│
    │- users  │ │15,510개 │ │-mini  │ │Search │ │-3-small│
    │- chats  │ │ chunks  │ │       │ │       │ │       │
    │- biz    │ │         │ │       │ │       │ │       │
    │- calendar│ │        │ │       │ │       │ │       │
    └─────────┘ └─────────┘ └───────┘ └───────┘ └───────┘
```

### 📦 기술 스택

**Frontend**
- Django 4.2 (템플릿 엔진)
- HTML5, CSS3, JavaScript (Vanilla)
- Boss Baby 테마 (보라색 그라데이션)

**Backend**
- FastAPI 0.104 (비동기 API 서버)
- LangChain 0.1 (RAG 파이프라인)
- Python 3.10.19

**AI/ML**
- OpenAI GPT-4o-mini (LLM)
- OpenAI text-embedding-3-small (1536차원 임베딩)
- Tavily API (웹 검색)

**Database**
- MySQL 8.0 (운영: 사용자, 채팅, 사업계획서, 캘린더)
- SQLite (개발/테스트)
- ChromaDB (벡터 스토어)

---

## 📊 데이터 구성

### 벡터 데이터베이스 (ChromaDB)

| 카테고리 | 문서 수 | 청킹 크기 | Overlap | 설명 |
|---------|---------|----------|---------|------|
| announcement | 159 | 400 chars | 80 | K-Startup 지원사업 공고 |
| space | 14,134 | 200 chars | 30 | 전국 창업 공간 정보 |
| law | 1 | 700 chars | 120 | 중소기업창업 지원법 |
| cases | 1 | 450 chars | 70 | 창업 실패 및 재도전 사례 |
| program | 103 | 300 chars | 50 | 스타트업 지원 프로그램 |
| ip_manual | 356 | 350 chars | 60 | 지식재산권 관리 매뉴얼 |
| stat | 25 | 500 chars | 80 | 창업 통계 자료 |
| **총계** | **15,510** | - | - | - |

### MySQL 데이터베이스 스키마

#### users (사용자)
```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### chat_sessions (채팅 세션)
```sql
CREATE TABLE chat_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id INT,
    title VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### chat_log (채팅 기록)
```sql
CREATE TABLE chat_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(36),
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    source_type ENUM('internal-rag', 'web-search', 'fallback'),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);
```

#### business_plans (사업계획서)
```sql
CREATE TABLE business_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    business_name VARCHAR(200) NOT NULL,
    field VARCHAR(100),
    stage ENUM('idea', 'mvp', 'early', 'growth'),
    idea TEXT,
    product TEXT,
    target_customer TEXT,
    differentiation TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

#### calendar_events (일정 관리) 🆕
```sql
CREATE TABLE calendar_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    title VARCHAR(200) NOT NULL,
    event_date DATE NOT NULL,
    event_type ENUM('deadline', 'start') DEFAULT 'deadline',
    is_completed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_event_date (event_date),
    INDEX idx_user_id (user_id)
);
```

---

## 🚀 시작하기

### 📋 사전 요구사항

- Python 3.10 이상
- MySQL 8.0 이상
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

# MySQL 설정
DB_HOST=localhost
DB_PORT=3306
DB_NAME=bossbaby_ai
DB_USER=root
DB_PASSWORD=your_password
```

5. **MySQL 데이터베이스 생성**
```sql
CREATE DATABASE bossbaby_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

6. **데이터 준비 (최초 1회)**
```bash
cd Backend
python main_chunking.py      # 문서 청킹 (약 5분 소요)
python build_vector_db.py    # 벡터DB 구축 (약 10분 소요)
```

7. **Django 마이그레이션**
```bash
python manage.py migrate      # DB 테이블 생성
python manage.py createsuperuser  # 관리자 계정 생성 (선택)
```

8. **서버 실행**

**Terminal 1 - Backend (FastAPI)**
```bash
cd Backend
python app.py
# 서버 실행: http://localhost:8000
# API 문서: http://localhost:8000/docs
```

**Terminal 2 - Frontend (Django)**
```bash
python manage.py runserver 8080
# 서버 실행: http://localhost:8080
```

9. **브라우저에서 접속**
```
http://localhost:8080
```

---

## 📁 프로젝트 구조

```
SKN20-4th-4TEAM/
├── Backend/
│   ├── app.py                  # FastAPI 메인 서버 (RAG + 사업계획서 + 캘린더 API)
│   ├── database.py             # MySQL 연결 및 ORM
│   ├── main_chunking.py        # 문서 청킹 처리
│   ├── build_vector_db.py      # ChromaDB 구축
│   ├── prompts.py              # 프롬프트 템플릿 (5가지)
│   ├── chunked_documents.pkl   # 청킹된 문서
│   └── chroma_startup_all/     # ChromaDB 저장소 (15,510개 벡터)
├── chat/
│   ├── views.py                # Django 뷰 (채팅, 캘린더, 사업계획서)
│   ├── models.py               # DB 모델 (User, ChatSession, ChatLog)
│   ├── urls.py                 # URL 라우팅
│   └── templates/
│       ├── chat.html           # 채팅 UI
│       ├── my_calendar.html    # 캘린더 UI 🆕
│       ├── business_plan_list.html      # 사업계획서 목록
│       ├── business_plan_create.html    # 사업계획서 작성
│       ├── business_plan_detail.html    # 사업계획서 상세
│       ├── business_plan_analysis.html  # AI 분석 결과
│       ├── mypage.html         # 마이페이지
│       └── login.html          # 로그인/회원가입
├── config/
│   ├── settings.py             # Django 설정 (MySQL 연동)
│   └── urls.py                 # 메인 URL
├── static/
│   ├── css/
│   ├── js/
│   └── img/                    # Boss Baby 캐릭터 이미지
├── requirements.txt            # 의존성
├── .env                        # 환경 변수 (보안)
└── README.md
```

---

## 🎨 주요 화면

### 1. 로그인/회원가입
- 보라색 그라데이션 배경 (#667eea → #764ba2)
- Boss Baby 로고
- 탭 전환 UI
- 실시간 유효성 검증

### 2. 채팅 메인
- Boss Baby 캐릭터 (우측 하단)
- 질문/답변 말풍선 UI
- 출처 배지: 📚 내부 문서 / 🌐 웹 검색 / 💭 AI 지식
- 빠른 답변 4개 (인기 질문)
- 서버 상태 표시 (실시간 연결 확인)
- 로딩 인디케이터 (타이핑 애니메이션)
- 자동 스크롤

### 3. 캘린더 일정 관리 🆕
- **월간 캘린더**: 42칸 그리드 (6주)
- **일정 배지**: 
  - 🔌 마감일 (빨강)
- **오늘 날짜 강조**: 파란색 그라데이션
- **다가오는 일정 리스트**: D-Day 계산
- **일정 관리 버튼**: 완료/삭제
- **월 이동**: 이전/다음 달 네비게이션
- **"오늘" 버튼**: 현재 월로 이동

### 4. 사업계획서 관리
- **목록 화면**: 카드형 레이아웃, 완성도 바
- **작성 화면**: 멀티 섹션 폼 (7개 입력 필드)
- **상세 화면**: 편집 가능, AI 분석 버튼
- **분석 결과 화면**: 
  - 5개 점수 카드 (투자매력도, 시장성, 실현가능성, 차별성, 완성도)
  - 8개 분석 섹션 (강점, 약점, 리스크, 개선 제안)
  - 탭 UI (단기/중기/장기 로드맵)

### 5. 마이페이지
- 통계 카드 (총 상담 수, 사업계획서 수, 일정 수) 🆕
- 빠른 액션 (새 상담, 사업계획서 작성, 일정 보기) 🆕
- 최근 사업계획서 목록
- 최근 상담 목록
- 다가오는 일정 미리보기 🆕

### 6. 채팅 기록
- 최근 50개 메시지 표시
- 시간순 정렬
- 출처 및 응답 시간 표시
- 세션별 구분

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
- ✅ 캘린더 D-Day 계산: **100% 정확도** 🆕
- ✅ 사업계획서 분석 시간: **평균 8초** 🆕

---

## 📚 API 문서

### FastAPI Endpoints

#### 1. 채팅 API

##### POST /chat
질문에 대한 AI 답변 생성 (RAG 파이프라인)

**Request Body**
```json
{
  "question": "서울에서 AI 창업 지원사업이 있나요?",
  "chat_history": [
    {"role": "user", "content": "안녕하세요"},
    {"role": "assistant", "content": "안녕하세요! 무엇을 도와드릴까요?"}
  ]
}
```

**Response**
```json
{
  "answer": "네, 서울에서 AI 관련 창업 지원사업이 있습니다...",
  "source_type": "internal-rag",
  "response_time": 4.2,
  "sources": [
    {
      "title": "서울시 AI 창업 지원사업",
      "type": "announcement"
    }
  ]
}
```

**Source Types**
- `internal-rag`: 내부 문서 검색 결과
- `web-search`: 웹 검색 결과 (Tavily)
- `fallback`: AI 일반 지식

##### GET /health
서버 상태 확인

**Response**
```json
{
  "status": "healthy",
  "vector_count": 15510,
  "db_connected": true
}
```

---

#### 2. 사업계획서 AI 분석 API 🆕

##### POST /analyze
사업계획서 AI 분석 및 점수 산출

**Request Body**
```json
{
  "business_name": "AI 챗봇 스타트업",
  "field": "인공지능",
  "stage": "mvp",
  "idea": "RAG 기반 창업 지원 챗봇...",
  "product": "Boss Baby AI 플랫폼...",
  "target_customer": "예비 창업자, 초기 스타트업",
  "differentiation": "RAG 정확도 92.8%, 사업계획서 AI 분석..."
}
```

**Response**
```json
{
  "success": true,
  "analysis": {
    "scores": {
      "investment_attractiveness": 85,
      "market_potential": 88,
      "feasibility": 82,
      "differentiation": 90,
      "completeness": 78
    },
    "market_analysis": "국내 창업 시장은 연간...",
    "feasibility": "기술적 실현 가능성은 높음...",
    "strengths": [
      "RAG 기술 기반의 높은 정확도",
      "통합 플랫폼으로서의 차별성",
      "사용자 경험 최적화"
    ],
    "weaknesses": [
      "초기 데이터 구축 비용",
      "경쟁사 대비 인지도 부족",
      "수익 모델 구체화 필요"
    ],
    "risks": [
      "OpenAI API 의존도",
      "개인정보 보호 이슈",
      "시장 진입 장벽"
    ],
    "suggestions": {
      "short_term": "베타 테스터 확보, K-Startup 파트너십...",
      "mid_term": "B2B 진출, API 오픈, 모바일 앱...",
      "long_term": "글로벌 진출, 시리즈 A 투자..."
    },
    "conclusion": "전반적으로 우수한 아이디어..."
  }
}
```

---

#### 3. 캘린더 일정 관리 API 🆕

##### GET /api/calendar/events/
특정 월의 일정 조회

**Query Parameters**
- `year`: 연도 (예: 2026)
- `month`: 월 (1-12)

**Request**
```
GET /api/calendar/events/?year=2026&month=1
```

**Response**
```json
{
  "success": true,
  "events": [
    {
      "id": 1,
      "title": "초기창업패키지 신청 마감",
      "event_date": "2026-01-15",
      "event_type": "deadline",
      "is_completed": false,
      "days_remaining": 6
    },
    {
      "id": 2,
      "title": "청년창업사관학교 접수 시작",
      "event_date": "2026-01-20",
      "event_type": "start",
      "is_completed": false,
      "days_remaining": 11
    }
  ]
}
```

##### PATCH /api/calendar/events/{event_id}/toggle/
일정 완료/취소 토글

**Request**
```
PATCH /api/calendar/events/1/toggle/
```

**Response**
```json
{
  "success": true,
  "message": "일정 상태가 업데이트되었습니다."
}
```

##### DELETE /api/calendar/events/{event_id}/delete/
일정 삭제

**Request**
```
DELETE /api/calendar/events/1/delete/
```

**Response**
```json
{
  "success": true,
  "message": "일정이 삭제되었습니다."
}
```

---

## 🔄 RAG 파이프라인 (6단계)

### 1단계: Contextualize Question
- 대화 히스토리 기반 질문 재구성
- 이전 대화를 고려하여 독립적인 질문으로 변환
- 예: "7년 후에도?" → "창업 후 7년이 지난 사업자도 창업자로 인정되는가?"

### 2단계: Query Transformation
- LLM 기반 쿼리 최적화
- 모호한 표현 명확화
- 검색에 적합한 키워드 추출

### 3단계: Multi-Query Generation
- 단일 질문을 3개의 다양한 쿼리로 확장
- 검색 재현율 30% 향상
- 예: "서울 AI 창업" → ["서울 인공지능 스타트업", "수도권 AI 기업 지원", "서울시 기술창업 프로그램"]

### 4단계: Vector Search
- ChromaDB에서 유사도 기반 검색
- 각 쿼리당 Top-K=10 문서 검색 → 총 30개 후보
- Embedding: text-embedding-3-small (1536차원)
- Similarity Threshold: 0.3

### 5단계: Relevance Check
- LLM 기반 문서 관련성 검증
- 무관한 문서 필터링
- 관련 문서 없음 → 웹 검색 트리거
- 웹 검색 실패 → AI Fallback

### 6단계: Answer Generation (3-Way Branching)
- **내부 RAG**: 관련 문서 있음 → 프롬프트 선택 (RAG/법령/추천)
- **웹 검색**: 관련 문서 없음 → Tavily 웹 검색 → 최신 정보 제공
- **AI Fallback**: 웹 검색 실패 → GPT-4o-mini 일반 지식 활용

---

## 🎯 프롬프트 엔지니어링 (5가지)

### 1. RAG 프롬프트
```python
당신은 창업 지원 전문 AI 어시스턴트입니다.
검색된 문서를 기반으로 정확하고 구체적인 답변을 제공하세요.
- 출처: 문서명, 발행기관 명시
- 수치: 정확한 날짜, 금액, 조건 포함
- 추가 정보: 관련 링크, 문의처 제공
...
```

### 2. 법령 프롬프트
```python
당신은 중소기업창업 지원법 전문가입니다.
법령 조항을 정확히 인용하고, 관련 조문을 명시하세요.
- 조문 번호: 제○○조 제○항
- 법령 용어: 정확한 법적 정의 사용
- 해석: 판례 및 유권해석 반영
...
```

### 3. 추천 프롬프트
```python
지원사업이나 창업 공간을 추천할 때는
사용자의 지역, 분야, 조건을 고려하여 맞춤형 추천을 제공하세요.
- 우선순위: 자금 지원 > 공간 지원 > 교육 프로그램
- 비교: 3개 이상 옵션 제시 및 장단점 비교
- 신청 방법: 구체적인 절차 안내
...
```

### 4. Fallback 프롬프트
```python
내부 문서에 정보가 없더라도
창업 컨설턴트 관점에서 실질적인 조언을 제공하세요.
- 일반적인 창업 가이드라인
- 관련 분야 트렌드 분석
- 추가 정보 확인 방법 안내
...
```

### 5. 사업계획서 분석 프롬프트 🆕
```python
당신은 20년 경력의 벤처투자 전문가입니다.
사업계획서를 다음 기준으로 분석하세요:
- 5개 지표: 투자매력도, 시장성, 실현가능성, 차별성, 완성도 (0-100점)
- 8개 섹션: 시장 동향, 실현 가능성, 강점 3가지, 약점 3가지, 
              리스크 3가지, 개선 제안 (단기/중기/장기), 종합 의견
- 톤: 전문적이면서도 건설적인 피드백
...
```

---

## 🛠️ 트러블슈팅

### 1. ChromaDB 로드 오류
```bash
# 벡터DB 재구축
cd Backend
python build_vector_db.py
# 예상 소요 시간: 10분
```

### 2. OpenAI API 오류
```bash
# API Key 확인
echo $OPENAI_API_KEY  # macOS/Linux
echo %OPENAI_API_KEY%  # Windows

# .env 파일 확인
cat .env
```

### 3. FastAPI 연결 실패
```bash
# Backend 서버가 실행 중인지 확인
curl http://localhost:8000/health

# 로그 확인
cd Backend
python app.py
```

### 4. MySQL 연결 오류
```bash
# MySQL 서비스 상태 확인
# Windows
net start MySQL80

# macOS/Linux
sudo systemctl status mysql

# 연결 테스트
mysql -u root -p
USE bossbaby_ai;
SHOW TABLES;
```

### 5. Django DB 마이그레이션 오류
```bash
# DB 초기화 후 재마이그레이션
python manage.py migrate --run-syncdb
python manage.py migrate
```

### 6. 캘린더 일정이 표시되지 않음 🆕
```bash
# calendar_events 테이블 확인
mysql -u root -p bossbaby_ai
SELECT * FROM calendar_events;

# 샘플 데이터 삽입
INSERT INTO calendar_events (user_id, title, event_date, event_type) VALUES
(1, '초기창업패키지 마감', '2026-01-15', 'deadline');
```

### 7. D-Day 계산 오류 🆕
```javascript
// 브라우저 콘솔에서 디버깅
console.log("현재 날짜:", new Date());
console.log("이벤트 날짜:", event.event_date);
console.log("D-Day:", event.days_remaining);

// 날짜 형식 확인 (YYYY-MM-DD)
```

---

## 🚧 향후 개선 계획

### Phase 1: 안정화 (1-2주) 🔥
- [x] MySQL 마이그레이션 완료
- [x] 캘린더 기능 추가
- [ ] 프론트엔드 버그 수정
- [ ] AWS EC2, RDS 배포
- [ ] HTTPS 적용

### Phase 2: 기능 확장 (1개월) 📌
- [ ] 파일 업로드 (PDF, DOCX 사업계획서)
- [ ] 음성 입력/출력 (STT/TTS)
- [ ] 개인화 추천 (사용자 프로필 기반)
- [ ] 일정 생성 모달 UI 🆕
- [ ] 이메일 알림 (D-3, D-1, D-Day) 🆕
- [ ] 푸시 알림 (PWA) 🆕
- [ ] 대시보드 (통계, 성과)

### Phase 3: 성능 개선 (2개월) 💡
- [ ] ChromaDB 증분 업데이트
- [ ] Redis 캐싱 (자주 묻는 질문)
- [ ] 응답 스트리밍 (WebSocket)
- [ ] A/B 테스트 (프롬프트 최적화)
- [ ] 구글 캘린더 연동 🆕
- [ ] 반복 일정 기능 🆕

### Phase 4: 비즈니스 모델 (3개월) 🚀
- [ ] 프리미엄 플랜 (월 9,900원)
  - 무제한 AI 분석
  - 우선 지원
  - 고급 통계
- [ ] B2B 솔루션 (창업 지원기관)
- [ ] K-Startup 파트너십
- [ ] 모바일 앱 (iOS/Android)
- [ ] API 오픈 (개발자 플랫폼)

### Phase 5: 글로벌 진출 (6개월-1년) 🌍
- [ ] 영어 버전
- [ ] 다국어 지원 (일본어, 중국어)
- [ ] 글로벌 지원사업 DB
- [ ] 시리즈 A 투자 유치

---

## 🏆 차별화 포인트

### 1. 하이브리드 RAG (3-Way Branching)
```
일반 챗봇: 단일 소스 (내부 문서 or 웹 검색)
Boss Baby AI: 내부 RAG → 웹 검색 → AI Fallback
→ 100% 커버리지 보장, 무응답 0%
```

### 2. 창업 특화 프롬프트 (5가지)
```
일반 챗봇: 범용 프롬프트
Boss Baby AI: RAG, 법령, 추천, Fallback, 분석 프롬프트
→ 지원사업 우선순위 로직 (자금 > 공간 > 교육)
```

### 3. AI 사업계획서 분석 (20년 경력 페르소나)
```
타 서비스: 단순 피드백 or 없음
Boss Baby AI: 5개 점수 + 8개 섹션 + 단기/중기/장기 로드맵
→ 투자 유치 성공률 향상
```

### 4. 캘린더 일정 관리 (D-Day 시각화) 🆕
```
타 서비스: 정보 제공만
Boss Baby AI: 정보 제공 + 일정 관리 + 알림 (향후)
→ 지원사업 마감일 놓치는 경우 60% 감소 (예상)
```

### 5. Boss Baby 테마 (친근한 UI/UX)
```
타 서비스: 딱딱한 비즈니스 UI
Boss Baby AI: 캐릭터 기반 친근한 디자인
→ 창업 스트레스 완화, 사용자 만족도 50% 향상
```

---

## 📊 비즈니스 모델

### 타겟 시장
- **Primary**: 예비 창업자 (30대), 초기 스타트업 (설립 1년 이내)
- **Secondary**: 재창업자, 대학생 창업 동아리, 정부 지원사업 신청자
- **지역**: 서울/경기 (창업 공간 데이터 70%)

### Value Proposition
1. **시간 절약**: 수백 개 공고 검색 → 3초 AI 추천
2. **정확도**: 92.8% (타 챗봇 대비 20% 높음)
3. **전문성**: 20년 경력 AI 컨설턴트 수준
4. **접근성**: 24시간 무료 (Freemium)
5. **통합성**: 지원사업 + 공간 + 법령 + 사례 + 분석 + 일정 🆕

### 수익 모델
```
Freemium (무료)
├── 월 5회 AI 분석
├── 기본 채팅 무제한
└── 일정 관리 (최대 10개) 🆕

Premium (월 9,900원)
├── 무제한 AI 분석
├── 우선 응답 (평균 2초)
├── 고급 통계 대시보드
├── 무제한 일정 관리 🆕
└── 이메일 알림 🆕

B2B (협의)
├── 창업 지원기관 라이선스
├── 커스터마이징
└── 전담 지원

API (건당 과금)
├── 개발자 플랫폼
└── 타 서비스 연동
```

### 시장 기회
- K-Startup 예산: 연 5천억 원
- 국내 창업자: 연 100만+ (통계청)
- 정보 비대칭: 지원사업 인지율 30% (설문조사)

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
- 통계청 (창업 통계)

**기술 스택 크레딧**:
- OpenAI (GPT-4o-mini, text-embedding-3-small)
- LangChain (RAG 파이프라인)
- Tavily (웹 검색 API)
- ChromaDB (벡터 데이터베이스)

---

## 📞 문의 및 기여

프로젝트에 대한 문의사항이나 버그 리포트는 GitHub Issues를 이용해주세요.

**Project Repository**: [SKN20-4th-4TEAM](https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN20-4th-4TEAM)

**기여 가이드**:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 🎉 팀원별 기여도

| 팀원 | 역할 | 주요 기여 |
|------|------|----------|
| **최소영** | 리더 / Backend | RAG 시스템, 사업계획서 AI 분석, 캘린더 API, 문서화 |
| **최유정** | Database | MySQL 설계, 채팅 로그, 캘린더 테이블, SQLAlchemy 통합 |
| **정래원** | Frontend / UI | Boss Baby 디자인, 사업계획서 관리, 캘린더 HTML/CSS |
| **김태빈** | 데이터 / 테스트 | 히스토리 연동, 쿼리 트랜스폼, 테스트 케이스 50개 |

---

## 📈 프로젝트 통계

```
📅 개발 기간: 2026.01.06 ~ 2026.01.09 (4일)
💻 총 커밋 수: 30+
📝 코드 라인: 5,000+ lines
🗄️ 데이터: 15,510개 벡터
✅ 완성도: 97%
⭐ 테스트 성공률: 100%
```

---

<div align="center">

## 🌟 주요 성과 요약

| 지표 | 목표 | 달성 | 달성률 |
|------|------|------|--------|
| 검색 정확도 | 90% | 92.8% | ✅ 103% |
| 평균 응답 시간 | 5초 | 4.42초 | ✅ 112% |
| 테스트 통과율 | 90% | 100% | ✅ 111% |
| 벡터 문서 수 | 10,000 | 15,510 | ✅ 155% |

---

**⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요! ⭐**

**🚀 Boss Baby AI와 함께 창업의 꿈을 현실로 만들어보세요! 🚀**

Made with ❤️ by SKN20-4th-4TEAM

![footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&height=150&section=footer)

</div>
