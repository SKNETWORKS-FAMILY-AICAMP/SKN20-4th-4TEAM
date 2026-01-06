# 데이터 json 형태로 저장

import requests
import json

SERVICE_KEY = "89fcf0de975649ae553ae81e625a1afe7004fc06dbb419730cc18d10d8a023ce"

URLS = {
    "announcement": "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01",  # 지원사업 공고 정보
    "stat": "https://apis.data.go.kr/B552735/kisedKstartupService01/getStatisticalInformation01",   # 창업관련 콘텐츠 정보
    "space": "https://apis.data.go.kr/B552735/kisedSlpService/getCenterSpaceList"  # 창업공간플랫폼(창업공간)_조회
}

result = {}
MAX_PAGE = 1000

for key, url in URLS.items():
    print(f"\n요청 중: {key} ...")
    all_items = []
    
    for page in range(1, MAX_PAGE + 1):
        params = {
            "serviceKey": SERVICE_KEY,
            "page": page,
            "perPage": 100,
            "returnType": "json"
        }
        
        try:
            res = requests.get(url, params=params)
            res.raise_for_status()
            data = res.json()
            
            items = data.get("data", [])
            
            if not items:
                print(f"  {key} {page}페이지: 데이터 없음 (종료)")
                break
            
            # announcement 필터링
            if key == "announcement":
                print(f"  {page}페이지: 원본 {len(items)}개")
                
                if page == 1 and items:
                    print(f"  첫 항목 키 목록: {list(items[0].keys())}")
                    print(f"  rcrt_prgs_yn 값 예시: {items[0].get('rcrt_prgs_yn')}")
                
                filtered_items = [
                    item for item in items 
                    if item.get("rcrt_prgs_yn", "").upper() == "Y"  # rcrt_prgs_yn 모집집행여부 Y인 것만
                ]
                print(f"  필터링 후: {len(filtered_items)}개")
                all_items.extend(filtered_items)
            
            # space 필터링
            elif key == "space":
                print(f"  {page}페이지: 원본 {len(items)}개")
                
                if page == 1 and items:
                    print(f"  첫 항목 키 목록: {list(items[0].keys())}")
                    print(f"  spce_cnt 값 예시: {items[0].get('spce_cnt')}")
                
                filtered_items = [
                    item for item in items 
                    if str(item.get("spce_cnt", "0")) != "0"  # spce_cnt 공간 수 0인 것 제외
                ]
                print(f"  필터링 후: {len(filtered_items)}개")
                all_items.extend(filtered_items)
            
            # stat은 필터링 없이 전체 추가
            else:
                print(f"  {page}페이지: {len(items)}개 추가")
                all_items.extend(items)
            
        except Exception as e:
            print(f"  {key} {page}페이지 요청 실패:", e)
            break
    
    result[key] = all_items
    print(f"{key} 총 {len(all_items)}개 수집 완료\n")

# JSON 저장
with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("완료: dataset.json 저장됨")

