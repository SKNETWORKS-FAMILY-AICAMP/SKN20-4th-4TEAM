import os
import warnings
import pickle
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from dotenv import load_dotenv

# 경고메세지 삭제
warnings.filterwarnings('ignore')
load_dotenv()

# openapi key 확인
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError('.env확인, key없음')

# ============================================
# 유틸리티 함수
# ============================================
def format_date(date_str):
    """날짜 포맷 변환 (20251201 → 2025-12-01)"""
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def clean_html(text):
    """간단한 HTML 태그 제거"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# documents 
def create_announcement_document(item):
    """announcement 항목을 Document로 변환"""
    page_content = f"""
【사업 공고】 {item.get('biz_pbanc_nm', '제목 없음')}

■ 사업 개요
{item.get('pbanc_ctnt', '내용 없음')}

■ 신청 대상
- 대상 유형: {item.get('aply_trgt', '')}
- 상세 조건:
{item.get('aply_trgt_ctnt', '')}

■ 제외 대상
{item.get('aply_excl_trgt_ctnt', '')}

■ 지원 정보
- 분류: {item.get('supt_biz_clsfc', '')}
- 지역: {item.get('supt_regin', '')}
- 창업 연수: {item.get('biz_enyy', '')}
- 대상 연령: {item.get('biz_trgt_age', '')}
- 감독 기관: {item.get('sprv_inst', '')}

■ 신청 정보
- 접수 기간: {format_date(item.get('pbanc_rcpt_bgng_dt', ''))} ~ {format_date(item.get('pbanc_rcpt_end_dt', ''))}
- 온라인 신청: {item.get('aply_mthd_onli_rcpt_istc', '해당 없음')}
- 상세 페이지: {item.get('detl_pg_url', '')}
- 안내 페이지: {item.get('biz_gdnc_url', '')}

■ 주관 기관
- 기관명: {item.get('pbanc_ntrp_nm', '')}
- 담당 부서: {item.get('biz_prch_dprt_nm', '')}
- 연락처: {item.get('prch_cnpl_no', '')}
    """.strip()
    
    metadata = {
        "source": "k-startup",
        "data_type": "announcement",
        "biz_id": item.get('pbanc_sn'),
        "biz_name": item.get('biz_pbanc_nm', ''),
        "category": item.get('supt_biz_clsfc', ''),
        "region": item.get('supt_regin', ''),
        "start_date": item.get('pbanc_rcpt_bgng_dt', ''),
        "end_date": item.get('pbanc_rcpt_end_dt', ''),
        "is_recruiting": item.get('rcrt_prgs_yn', ''),
        "supervisor": item.get('sprv_inst', ''),
        "url": item.get('detl_pg_url', '')
    }
    
    return Document(page_content=page_content, metadata=metadata)

def create_stat_document(item):
    """stat 항목을 Document로 변환"""
    page_content = f"""
【창업 통계/연구 자료】 {item.get('titl_nm', '제목 없음')}

■ 내용
{clean_html(item.get('ctnt', ''))}

■ 파일 정보
- 파일명: {item.get('file_nm', '')}
- 상세 페이지: {item.get('detl_pg_url', '')}
    """.strip()
    
    metadata = {
        "source": "k-startup",
        "data_type": "stat",
        "title": item.get('titl_nm', ''),
        "file_name": item.get('file_nm', ''),
        "register_date": item.get('fstm_reg_dt', ''),
        "modified_date": item.get('last_mdfcn_dt', ''),
        "url": item.get('detl_pg_url', '')
    }
    
    return Document(page_content=page_content, metadata=metadata)

def create_space_document(item):
    """space 항목을 Document로 변환"""
    page_content = f"""
【창업 공간】 {item.get('spce_nm', '공간명 없음')}

■ 센터 정보
- 센터명: {item.get('cntr_nm', '')}
- 센터 유형: {item.get('cntr_type_nm', '')}

■ 위치 정보
- 주소: {item.get('addr', '')}
    """.strip()
    
    metadata = {
        "source": "k-startup",
        "data_type": "space",
        "space_id": item.get('spce_id'),
        "center_id": item.get('cntr_id'),
        "center_name": item.get('cntr_nm', ''),
        "center_type": item.get('cntr_type_nm', ''),
        "space_name": item.get('spce_nm', ''),
        "address": item.get('addr', ''),
        "space_type": item.get('spce_type_nm', ''),
        "space_count": item.get('spce_cnt', 0),
        "area": item.get('excuse_ar', ''),
        "rent": item.get('rent', 0),
        "management_fee": item.get('guam', 0),
        "reservation": item.get('rsvt_psbl_clss', ''),
        "homepage": item.get('hmpg', ''),
        "building_name": item.get('buld_nm', ''),
        "postal_code": item.get('pstno', ''),
        "latitude": item.get('latde', ''),
        "longitude": item.get('lgtde', ''),
        "current_tenant": item.get('seat_co', ''),
        "center_intro": clean_html(item.get('cntr_intrd_type_nm', ''))
    }
    
    return Document(page_content=page_content, metadata=metadata)



# 1. JSON → Document 변환
print("=" * 60)
print("1단계: JSON → Document 변환")
print("=" * 60)

with open("../data/dataset.json", "r", encoding="utf-8") as f:
    data = json.load(f)
documents = []

# announcement 처리
print("\nannouncement 문서 생성 중...")
for item in data.get("announcement", []):
    doc = create_announcement_document(item)
    documents.append(doc)
print(f"  → {len([d for d in documents if d.metadata['data_type'] == 'announcement'])}개 완료")

# stat 처리
print("stat 문서 생성 중...")
for item in data.get("stat", []):
    doc = create_stat_document(item)
    documents.append(doc)
print(f"  → {len([d for d in documents if d.metadata['data_type'] == 'stat'])}개 완료")

# space 처리
print("space 문서 생성 중...")
for item in data.get("space", []):
    doc = create_space_document(item)
    documents.append(doc)
print(f"  → {len([d for d in documents if d.metadata['data_type'] == 'space'])}개 완료")

print(f"\n총 {len(documents)}개의 Document 생성 완료!")

# 추가 TXT 파일들 → Document로 합치기

print("\n" + "=" * 60)
print("2단계: 추가 TXT → Document 변환")
print("=" * 60)

# (1) data 폴더 안의 큰 txt 파일들
plain_txt_files = [
    ("../data/중소기업창업_지원법.txt", "law"),       
    ("../data/failure_cases_all.txt", "cases"), 
]

for path, dtype in plain_txt_files:
    if not os.path.exists(path):
        print(f"  [경고] {path} 파일을 찾을 수 없습니다. (건너뜀)")
        continue

    print(f"\n▶ TXT 문서 로드 중: {path}")
    loader = TextLoader(path, encoding="utf-8")
    txt_docs = loader.load()  

    for d in txt_docs:
        # 기존 메타데이터에 data_type, source를 붙여줌
        d.metadata = d.metadata or {}
        d.metadata["source"] = os.path.basename(path)
        d.metadata["data_type"] = dtype

        documents.append(d)

    print(f"  → {len(txt_docs)}개 Document 추가 (data_type='{dtype}')")


# (2) 압축 풀고 생긴 txt 폴더들
chunked_txt_dirs = [
    ("../data/스타트업지원프로그램txt", "program_chunk"),
    ("../data/지식재산관리매뉴얼txt", "ip_manual_chunk"),
]

for dir_path, dtype in chunked_txt_dirs:
    if not os.path.exists(dir_path):
        print(f"\n  [경고] {dir_path} 폴더를 찾을 수 없습니다. (건너뜀)")
        continue

    print(f"\n▶ 폴더 내 TXT 로드 중: {dir_path}")
    loader = DirectoryLoader(
        dir_path,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    dir_docs = loader.load()

    for d in dir_docs:
        d.metadata = d.metadata or {}
        d.metadata["source"] = d.metadata.get("source", dir_path)
        d.metadata["data_type"] = dtype
        d.metadata["file_name"] = os.path.basename(d.metadata["source"])

        documents.append(d)

    print(f"  → {len(dir_docs)}개 Document 추가 (data_type='{dtype}')")

print(f"\n✅ JSON + TXT 합산 Document 총 개수: {len(documents)}개")


# # documents.pkl 저장 (백업)
# with open("documents.pkl", "wb") as f:
#     pickle.dump(documents, f)
# print(" documents.pkl 저장 완료 (백업)")


# 3. 청킹 (타입별 세밀 튜닝)
print("\n" + "=" * 60)
print("3단계: 문서 청킹")
print("=" * 60)

# 타입별 splitter 설정
default_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=['\n\n', '\n', '.', ',', ' ', '']
)

splitter_map = {
    # 사업 공고
    "announcement": RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80,
        separators=['\n\n', '\n', '.', ',', ' ', '']
    ),
    # 통계/연구
    "stat": RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=['\n\n', '\n', '.', ',', ' ', '']
    ),
    # 창업 공간
    "space": RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=30,
        separators=['\n\n', '\n', '.', ',', ' ', '']
    ),
    # 법령
    "law": RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120,
        separators=['\n\n', '\n', '제', '.', ' ', '']
    ),
    # 실패 사례
    "cases": RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=70,
        separators=['\n\n', '\n', '.', ',', ' ', '']
    ),
}

final_docs = []

print(f"\n청킹 대상 원본 Document 수: {len(documents)}개")

for d in documents:
    dtype = d.metadata.get("data_type", "")

    # 이미 청킹된 zip 데이터는 그대로 사용
    if dtype in ("program_chunk", "ip_manual_chunk"):
        final_docs.append(d)
        continue

    # 2) 타입별 splitter 선택
    splitter = splitter_map.get(dtype, default_splitter)
    chunks = splitter.split_documents([d])
    final_docs.extend(chunks)

print(f" 최종 청킹 결과: {len(final_docs)}개 Document")

# 청킹 파일 저장
with open("chunked_documents.pkl", "wb") as f:
    pickle.dump(final_docs, f)

print(" chunked_documents.pkl 저장 완료")


# # (옵션) 타입별 샘플 몇 개만 확인해보기
# print("\n=== 샘플 청킹 미리보기 ===")

# def preview_by_type(target_type, n=2):
#     print(f"\n[타입: {target_type}] 샘플 {n}개")
#     count = 0
#     for doc in final_docs:
#         if doc.metadata.get("data_type") == target_type:
#             count += 1
#             print(f"\n--- {target_type} chunk #{count} (길이: {len(doc.page_content)}) ---")
#             print(doc.page_content[:300], "...")
#             if count >= n:
#                 break

# for t in ["announcement", "law", "cases"]:
#     preview_by_type(t)
