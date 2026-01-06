#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실패·재도전 사례 데이터 수집/정제 파이프라인
여러 PDF 사례집에서 구조화된 데이터셋을 생성합니다.
"""

import re
import json
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import pymupdf as fitz


@dataclass
class FailureCase:
    """실패·재도전 사례 데이터 구조"""
    id: str
    source_pdf: str  # 👈 어떤 PDF에서 왔는지 추가
    source_title: str
    source_page_range: str
    representative_name: str
    company_name: str
    industry: str
    service_description: str
    founding_year: Optional[str]
    revenue: Optional[str]
    homepage: Optional[str]
    previous_business: str
    first_startup_year: Optional[str]
    closure_year: Optional[str]
    main_failure_reason: str
    sub_failure_reasons: List[str]
    team_issue: str
    funding_issue: str
    mental_impact: str
    recovery_process: str
    pivot_or_retry: str
    support_program: str
    new_approach: str
    key_differentiator: str
    current_achievement: str
    result_after_retry: str
    key_lesson: str
    advice_quote: str
    raw_chunk: str


def load_pdf(pdf_path: str) -> List[tuple]:
    """
    PDF 파일을 로드하여 페이지별 텍스트를 추출합니다.
    
    Args:
        pdf_path: PDF 파일 경로
    
    Returns:
        (page_number, page_text) 튜플의 리스트
    """
    print(f"📖 PDF 로딩 중: {pdf_path}")
    doc = fitz.open(pdf_path)
    pages = []
    
    # 일반 텍스트 추출
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        pages.append((page_num + 1, text))
    
    doc.close()
    print(f"✅ 총 {len(pages)}페이지 로드 완료")
    return pages


def preprocess_page_text(text: str) -> str:
    """
    페이지 텍스트 전처리: 불필요한 공백/줄바꿈 정리
    
    Args:
        text: 원본 텍스트
    
    Returns:
        전처리된 텍스트
    """
    # 연속된 공백을 하나로
    text = re.sub(r' +', ' ', text)
    
    # 3개 이상의 연속 줄바꿈을 2개로
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 페이지 번호 패턴 제거 (단독 숫자 라인)
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
    
    return text.strip()


def extract_company_info(text: str) -> Dict[str, Optional[str]]:
    """
    회사 정보 박스에서 기본 정보를 추출합니다.
    
    Args:
        text: 사례 텍스트
    
    Returns:
        회사 기본 정보 딕셔너리
    """
    info = {
        'company_name': None,
        'founding_year': None,
        'homepage': None,
        'service_description': None,
        'revenue': None
    }
    
    # 회사설립 정보 추출
    founding_match = re.search(r'회사설립\s*[　\s]*([\d년월일\s,]+)', text)
    if founding_match:
        founding_text = founding_match.group(1).strip()
        # 연도 추출
        year_match = re.search(r'(\d{4})년', founding_text)
        if year_match:
            info['founding_year'] = year_match.group(1)
    
    # 홈페이지
    homepage_match = re.search(r'홈페이지\s*[　\s]*(https?://[^\s]+)', text)
    if homepage_match:
        info['homepage'] = homepage_match.group(1).strip()
    
    # 주요사업
    service_match = re.search(r'주요사업\s*[　\s]*(.+?)(?:\n|매출액)', text, re.DOTALL)
    if service_match:
        info['service_description'] = service_match.group(1).strip()
    
    # 매출액
    revenue_match = re.search(r'매출액\s*[　\s]*(.+?)(?:\(|$)', text)
    if revenue_match:
        info['revenue'] = revenue_match.group(1).strip()
    
    return info


def classify_industry(service_description: str, company_name: str) -> str:
    """
    서비스 설명을 기반으로 업종을 분류합니다.
    
    Args:
        service_description: 서비스 설명
        company_name: 회사명
    
    Returns:
        업종 분류
    """
    # None 값 처리
    service_description = service_description or ""
    company_name = company_name or ""
    
    text = (service_description + " " + company_name).lower()
    
    if any(kw in text for kw in ['교육', '학습', '학원', '에듀', '온라인 방과후']):
        return '에듀테크'
    elif any(kw in text for kw in ['패션', '쇼핑', '의류', '옷', '편집숍']):
        return '패션테크'
    elif any(kw in text for kw in ['식품', '먹거리', '식재료', '음식', '팔도감']):
        return '푸드테크'
    elif any(kw in text for kw in ['농업', '스마트팜', '식물', '재배']):
        return '애그테크'
    elif any(kw in text for kw in ['반려동물', '펫', '애완동물']):
        return '펫테크'
    elif any(kw in text for kw in ['앱', '모바일', '플랫폼', '소프트웨어']):
        return 'IT/소프트웨어'
    elif any(kw in text for kw in ['iot', 'led', '기술', '하드웨어']):
        return '하드웨어/IoT'
    else:
        return '기타'


def extract_failure_reasons(text: str) -> tuple:
    """
    실패 원인을 추출합니다.
    
    Args:
        text: 사례 텍스트
    
    Returns:
        (main_reason, sub_reasons) 튜플
    """
    main_reason = ""
    sub_reasons = []
    
    # 주요 실패 원인 패턴
    patterns = [
        r'폐업의 가장 큰 요인은[^?]*?\?\s*(.+?)(?:\n\n|Q\.|$)',
        r'폐업[을를] [결정한|하게 된] 이유는[^?]*?\?\s*(.+?)(?:\n\n|Q\.|$)',
        r'그만[두게|뒀고].*?이유는[^?]*?\?\s*(.+?)(?:\n\n|Q\.|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            main_reason = match.group(1).strip()
            # 첫 1-2문장만 추출
            sentences = re.split(r'[.!?]\s+', main_reason)
            main_reason = '. '.join(sentences[:2]) + '.'
            break
    
    # 부가적 실패 요인 키워드
    failure_keywords = {
        '준비 부족': ['준비가 되어 있지 않', '경험이 없', '미숙했'],
        '사업 확장 실패': ['무리해서', '감당해야 할 일', '역량이 부족'],
        '초심 상실': ['초심 자체가 흔들', '다른 방향으로'],
        '수익 모델 불명확': ['수익 모델이 명확하지', '의미 있는 수익'],
        '선택과 집중 실패': ['선택과 집중을 하지 못'],
        '시장 미스매치': ['시장에서 유효', '경쟁자가 많'],
    }
    
    for reason, keywords in failure_keywords.items():
        if any(kw in text for kw in keywords):
            sub_reasons.append(reason)
    
    return main_reason, sub_reasons


def extract_issues(text: str) -> tuple:
    """
    팀/자금 이슈를 추출합니다.
    
    Args:
        text: 사례 텍스트
    
    Returns:
        (team_issue, funding_issue) 튜플
    """
    team_issue = "없음"
    funding_issue = "없음"
    
    # 팀 이슈
    team_patterns = [
        r'팀원.*?(\d+명)',
        r'함께 일했던 사람',
        r'직무가 겹',
        r'조직 관리',
        r'구성원'
    ]
    
    for pattern in team_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            # 관련 문맥 추출
            match = re.search(r'([^.]*(?:' + pattern + ')[^.]*\.)', text, re.IGNORECASE)
            if match:
                team_issue = match.group(1).strip()
                break
    
    # 자금 이슈
    funding_patterns = [
        r'빚.*?[갚았|없었]',
        r'대출',
        r'지원받은 금액',
        r'투자.*?(\d+억)',
        r'금전적.*?[지원|타격|어려]',
        r'자금'
    ]
    
    for pattern in funding_patterns:
        match = re.search(r'([^.]*(?:' + pattern + ')[^.]*\.)', text, re.IGNORECASE)
        if match:
            funding_issue = match.group(1).strip()
            break
    
    return team_issue, funding_issue


def extract_key_lesson(text: str) -> str:
    """
    핵심 교훈을 추출합니다.
    
    Args:
        text: 사례 텍스트
    
    Returns:
        핵심 교훈
    """
    # 큰 따옴표로 강조된 교훈 박스 찾기
    quote_pattern = r'"([^"]{20,})"'
    quotes = re.findall(quote_pattern, text)
    
    if quotes:
        # 가장 긴 인용문을 선택 (보통 핵심 교훈)
        return max(quotes, key=len)
    
    # 교훈 관련 질문-답변 패턴
    lesson_patterns = [
        r'실패.*?어떤 의미[^?]*?\?\s*(.{50,300}?)(?:\n\n|Q\.|$)',
        r'배운.*?점[^?]*?\?\s*(.{50,300}?)(?:\n\n|Q\.|$)',
        r'교훈[^?]*?\?\s*(.{50,300}?)(?:\n\n|Q\.|$)',
    ]
    
    for pattern in lesson_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return "명시적 교훈 없음"


def extract_advice_quote(text: str) -> str:
    """
    조언/명언을 추출합니다.
    
    Args:
        text: 사례 텍스트
    
    Returns:
        조언 문구
    """
    # 큰 따옴표로 된 조언 패턴
    quote_pattern = r'"([^"]{15,150})"'
    quotes = re.findall(quote_pattern, text)
    
    # 조언성 키워드를 포함한 인용문 우선
    advice_keywords = ['해야', '하세요', '하라', '추천', '중요', '필요']
    
    for quote in quotes:
        if any(kw in quote for kw in advice_keywords):
            return quote
    
    # 그 외 첫 번째 적절한 길이의 인용문
    for quote in quotes:
        if 20 < len(quote) < 100:
            return quote
    
    return ""


def split_into_cases(pages: List[tuple]) -> List[Dict]:
    """
    페이지들을 사례 단위로 청킹합니다.
    
    Args:
        pages: (page_number, page_text) 리스트
    
    Returns:
        사례 정보 딕셔너리 리스트
    """
    cases = []
    current_case = None
    current_pages = []
    current_text = []
    
    # Chapter 또는 회사명 패턴
    chapter_pattern = r'Chapter\.(\d+)'
    company_pattern = r'^([가-힣a-zA-Z0-9\s\.]+)$'  # 한 줄에 회사명만 있는 경우
    
    for page_num, text in pages:
        # 프롤로그, 목차 등 건너뛰기
        if page_num < 6:
            continue
        
        # Chapter 시작 감지
        chapter_match = re.search(chapter_pattern, text)
        is_new_case = False
        
        if chapter_match:
            is_new_case = True
        else:
            # 회사명 패턴 감지 (한 줄에 3-20자 길이의 텍스트)
            lines = text.strip().split('\n')
            if lines and len(lines[0]) > 0:
                first_line = lines[0].strip()
                # 짧은 회사명 같은 단일 라인 감지
                if 2 < len(first_line) < 30 and not first_line[0].isdigit():
                    is_new_case = True
        
        if is_new_case:
            # 이전 케이스 저장
            if current_case and len(current_text) > 1:  # 최소한 2페이지 이상
                current_case['page_range'] = f"{current_pages[0]}-{current_pages[-1]}"
                current_case['text'] = '\n\n'.join(current_text)
                cases.append(current_case)
            
            # 새 케이스 시작
            current_case = {
                'chapter': chapter_match.group(1) if chapter_match else 'unknown',
                'start_page': page_num
            }
            current_pages = [page_num]
            current_text = [preprocess_page_text(text)]
        elif current_case:
            # 현재 케이스에 페이지 추가
            current_pages.append(page_num)
            current_text.append(preprocess_page_text(text))
    
    # 마지막 케이스 저장
    if current_case and len(current_text) > 1:
        current_case['page_range'] = f"{current_pages[0]}-{current_pages[-1]}"
        current_case['text'] = '\n\n'.join(current_text)
        cases.append(current_case)
    
    print(f"✅ {len(cases)}개의 사례 청크 생성 완료")
    return cases


def extract_structured_case(case_dict: Dict, case_index: int, pdf_name: str) -> FailureCase:
    """
    사례 텍스트를 구조화된 데이터로 변환합니다.
    
    Args:
        case_dict: 사례 정보 딕셔너리
        case_index: 사례 인덱스
        pdf_name: PDF 파일명
    
    Returns:
        FailureCase 객체
    """
    text = case_dict['text']
    
    # 제목 추출 (첫 번째 줄 또는 Chapter 다음 줄)
    lines = text.split('\n')
    title = lines[0] if lines else f"사례 {case_index + 1}"
    
    # 대표자명 추출
    rep_pattern = r'([가-힣]{2,4})\s*대표'
    rep_match = re.search(rep_pattern, text)
    representative_name = rep_match.group(1) if rep_match else ""
    
    # 회사명 추출 (괄호 안의 회사명)
    company_pattern = r'([㈜(주)][^\s,]+)'
    company_match = re.search(company_pattern, text)
    company_name = company_match.group(1) if company_match else ""
    
    # 회사 정보 추출
    company_info = extract_company_info(text)
    
    # 업종 분류
    industry = classify_industry(
        company_info.get('service_description', ''),
        company_name
    )
    
    # 실패 원인 추출
    main_failure_reason, sub_failure_reasons = extract_failure_reasons(text)
    
    # 이슈 추출
    team_issue, funding_issue = extract_issues(text)
    
    # 이전 사업 추출
    previous_business = ""
    prev_patterns = [
        r'이전에.*?([^.]{20,100}사업)',
        r'처음.*?창업.*?([^.]{20,100})',
        r'첫.*?사업.*?([^.]{20,100})'
    ]
    for pattern in prev_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            previous_business = match.group(1).strip()
            break
    
    # 재도전 방식
    pivot_or_retry = "신규 아이템"
    if re.search(r'같은|동일|비슷한.*?분야', text, re.IGNORECASE):
        pivot_or_retry = "동일 업종 피벗"
    elif re.search(r'완전히 다른|새로운 분야', text, re.IGNORECASE):
        pivot_or_retry = "신규 업종 도전"
    
    # 지원 프로그램
    support_program = ""
    if '재도전 성공 패키지' in text or '재도전성공패키지' in text:
        support_program = "재도전성공패키지"
    if 'TIPS' in text or '팁스' in text:
        support_program += ", TIPS" if support_program else "TIPS"
    
    # 심리적 영향
    mental_impact = ""
    mental_patterns = [
        r'폐업.*?[결정|이후].*?([^.]{20,100}[심정|상황|느낌])',
        r'심리적.*?([^.]{20,100})',
        r'힘들.*?([^.]{20,100})'
    ]
    for pattern in mental_patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            mental_impact = match.group(1).strip()
            break
    
    # 현재 성과
    current_achievement = ""
    achievement_patterns = [
        r'성과.*?([^.]{30,150})',
        r'매출.*?(\d+억)',
        r'투자.*?(\d+억)',
        r'(\d+만).*?[다운로드|회원]'
    ]
    for pattern in achievement_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            current_achievement += match.group(0) + ". "
    
    # 교훈 및 조언
    key_lesson = extract_key_lesson(text)
    advice_quote = extract_advice_quote(text)
    
    # FailureCase 객체 생성
    return FailureCase(
        id=f"case_{str(case_index + 1).zfill(3)}",
        source_pdf=pdf_name,  # 👈 추가
        source_title=title.strip(),
        source_page_range=case_dict['page_range'],
        representative_name=representative_name,
        company_name=company_name,
        industry=industry,
        service_description=company_info.get('service_description', ''),
        founding_year=company_info.get('founding_year'),
        revenue=company_info.get('revenue'),
        homepage=company_info.get('homepage'),
        previous_business=previous_business,
        first_startup_year=None,
        closure_year=None,
        main_failure_reason=main_failure_reason,
        sub_failure_reasons=sub_failure_reasons,
        team_issue=team_issue,
        funding_issue=funding_issue,
        mental_impact=mental_impact,
        recovery_process="",
        pivot_or_retry=pivot_or_retry,
        support_program=support_program,
        new_approach="",
        key_differentiator="",
        current_achievement=current_achievement.strip(),
        result_after_retry="성장중/성공",
        key_lesson=key_lesson,
        advice_quote=advice_quote,
        raw_chunk=text
    )


def save_as_txt(cases: List[FailureCase], output_path: str):
    """
    TXT 형식으로 저장합니다.
    (사례별 요약 + 원문 청크를 사람이 읽기 좋은 형태로 정리)
    
    Args:
        cases: FailureCase 객체 리스트
        output_path: 출력 파일 경로
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if not cases:
        print("⚠️ 저장할 케이스가 없습니다.")
        return
    
    lines = []
    for case in cases:
        lines.append(f"=== {case.id} | {case.company_name or '회사명 미상'} | {case.source_pdf} ===")  # 👈 PDF명 추가
        lines.append(f"제목: {case.source_title}")
        lines.append(f"페이지 범위: {case.source_page_range}")
        lines.append(f"대표자: {case.representative_name or '정보 없음'}")
        lines.append(f"업종: {case.industry}")
        lines.append("")
        lines.append(f"[주요 실패 원인]")
        lines.append(case.main_failure_reason or "정보 없음")
        lines.append("")
        lines.append(f"[부가 실패 요인]")
        lines.append(", ".join(case.sub_failure_reasons) if case.sub_failure_reasons else "정보 없음")
        lines.append("")
        lines.append(f"[핵심 교훈]")
        lines.append(case.key_lesson or "정보 없음")
        lines.append("")
        lines.append(f"[조언/인용문]")
        lines.append(case.advice_quote or "정보 없음")
        lines.append("")
        lines.append(f"[원문 청크]")
        lines.append(case.raw_chunk.strip())
        lines.append("\n" + "-" * 80 + "\n")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"✅ TXT 저장 완료: {output_path}")


def process_single_pdf(pdf_path: str) -> List[FailureCase]:
    """
    단일 PDF를 처리합니다.
    
    Args:
        pdf_path: PDF 파일 경로
    
    Returns:
        FailureCase 객체 리스트
    """
    pdf_name = os.path.basename(pdf_path)
    print(f"\n{'='*60}")
    print(f"처리 중: {pdf_name}")
    print(f"{'='*60}")
    
    # 1. PDF 로드
    pages = load_pdf(pdf_path)
    
    # 2. 사례 청킹
    case_chunks = split_into_cases(pages)
    
    # 3. 구조화
    print(f"\n📊 사례 구조화 중...")
    structured_cases = []
    for idx, case_chunk in enumerate(case_chunks):
        print(f"  처리 중: Case {idx + 1}/{len(case_chunks)}")
        structured_case = extract_structured_case(case_chunk, idx, pdf_name)
        structured_cases.append(structured_case)
    
    print(f"✅ {len(structured_cases)}개 사례 구조화 완료")
    return structured_cases


def main():
    """메인 파이프라인 실행"""
    print("=" * 60)
    print("실패·재도전 사례 데이터 수집/정제 파이프라인 (다중 PDF)")
    print("=" * 60)
    
    # 🔥 처리할 파일 목록 (PDF)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_to_process = [
        ('failure_case.pdf', 'pdf'),
        ('failure_case2.pdf', 'pdf')
    ]
    
    # 파일 경로 찾기
    file_paths = []
    for file_name, file_type in files_to_process:
        # 1. 스크립트 디렉토리에서 찾기
        path = os.path.join(script_dir, file_name)
        
        # 2. 현재 작업 디렉토리에서 찾기
        if not os.path.exists(path):
            path = os.path.join(os.getcwd(), file_name)
        
        # 3. 상위 디렉토리의 data 폴더에서 찾기
        if not os.path.exists(path):
            parent_dir = os.path.dirname(script_dir)
            path = os.path.join(parent_dir, 'data', file_name)
        
        # 4. 프로젝트 root의 data 폴더에서 찾기
        if not os.path.exists(path):
            project_root = os.path.dirname(os.path.dirname(script_dir))
            path = os.path.join(project_root, 'data', file_name)
        
        if os.path.exists(path):
            file_paths.append((path, file_type))
            print(f"✅ 발견: {file_name} ({file_type.upper()})")
        else:
            print(f"⚠️  없음: {file_name} (건너뜀)")
    
    if not file_paths:
        print(f"\n❌ 에러: 처리할 파일이 없습니다.")
        print(f"   스크립트 디렉토리: {script_dir}")
        print(f"   현재 작업 디렉토리: {os.getcwd()}")
        sys.exit(1)
    
    # 모든 파일 처리
    all_cases = []
    case_counter = 0
    
    for file_path, file_type in file_paths:
        if file_type == 'pdf':
            cases = process_single_pdf(file_path)
        else:
            print(f"⚠️  지원하지 않는 파일 형식: {file_type}")
            continue
        
        # ID 재할당 (전체 통합 ID)
        for case in cases:
            case_counter += 1
            case.id = f"case_{str(case_counter).zfill(3)}"
        
        all_cases.extend(cases)
    
    print(f"\n{'='*60}")
    print(f"✨ 전체 {len(all_cases)}개 사례 통합 완료!")
    print(f"{'='*60}")
    
    # 출력 디렉토리 생성
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, 'data', 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # TXT 저장
    txt_path = os.path.join(output_dir, 'failure_cases_all.txt')  # 👈 파일명 변경
    save_as_txt(all_cases, txt_path)
    
    print("\n" + "=" * 60)
    print("✨ 모든 처리 완료!")
    print(f"📁 출력 위치: {output_dir}")
    print(f"📄 파일명: failure_cases_all.txt")
    print("=" * 60)
  
    

if __name__ == "__main__":
    main()