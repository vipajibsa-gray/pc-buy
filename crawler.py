import os
import json
import time
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. 구글 스프레드시트 인증 설정
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# GitHub Secret에 저장된 JSON 키 로드
service_account_info = json.loads(os.environ["GCP_SA_KEY"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, SCOPE)
client = gspread.authorize(creds)

# 스프레드시트 열기
SHEET_NAME = "매입리스트 및 가격"
doc = client.open(SHEET_NAME)

source_sheet = doc.worksheet("월드 수집 URL")
target_sheet = doc.worksheet("매입품목 및 가격")

# 2. '월드 수집 URL' 탭에서 URL 및 기본 분류 정보 가져오기
rows = source_sheet.get_all_values()
# 헤더 제외 (구분, 브랜드, 모델, URL)
url_tasks = rows[1:]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

collected_data = []
today_str = datetime.now().strftime("%Y-%m-%d")

print(f"[{datetime.now()}] 총 {len(url_tasks)}개 URL 크롤링 시작...")

last_category = ""
last_brand = ""

for row in url_tasks:
    if not row or len(row) < 4:
        continue
    
    # 병합된 셀이나 빈칸일 경우 직전 값 유지 처리
    cat = row[0].strip() if row[0].strip() else last_category
    brand = row[1].strip() if row[1].strip() else last_brand
    model = row[2].strip()
    target_url = row[3].strip()

    if cat: last_category = cat
    if brand: last_brand = brand

    if not target_url.startswith("http"):
        continue

    try:
        res = requests.get(target_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # 월드메모리 가격 테이블 파싱 (테이블 행 탐색)
        items = soup.select("table tbody tr")
        for item in items:
            cols = item.find_all("td")
            if len(cols) >= 2:
                # 품목명과 가격 텍스트 추출
                item_name = cols[0].get_text(strip=True)
                raw_price = cols[1].get_text(strip=True)
                price = "".join(filter(str.isdigit, raw_price))

                if item_name and price:
                    collected_data.append([
                        cat,           # 구분 (예: CPU, 메모리)
                        brand,         # 브랜드 (예: 인텔, AMD)
                        model,         # 세대/분류 (예: 16세대, 삼성 DDR5)
                        item_name,     # 품목명
                        int(price),    # 매입단가(원)
                        today_str,     # 수집일시
                        target_url     # 수집 URL
                    ])

        print(f"수집 완료: {cat} > {brand} > {model}")

    except Exception as e:
        print(f"에러 발생 ({target_url}): {e}")

    # ★ 서버 과부하 및 IP 차단 방지를 위한 요청 간 1.5~2.5초 지연
    time.sleep(random.uniform(1.5, 2.5))

# 3. '매입품목 및 가격' 탭 업데이트
if collected_data:
    # 기존 데이터 영역 비우기 (헤더 행은 유지)
    target_sheet.resize(rows=1)
    
    # 새 데이터 한번에 밀어넣기
    target_sheet.append_rows(collected_data)
    print(f"총 {len(collected_data)}개 품목이 구글 시트에 업데이트되었습니다.")
else:
    print("수집된 데이터가 없습니다.")