import time
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# ★ 1단계에서 발급받은 Apps Script 웹 앱 URL을 여기에 붙여넣으세요.
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzr758VEVM0e85ep9AYFMorQAz7gWh7mP064IkGoy-jkaz6_GwmRJriSsNNuWXXa1CMWA/exec"

def main():
    print(f"[{datetime.now()}] 비공개 구글 시트에서 URL 목록 가져오는 중...")
    try:
        # 비공개 시트의 [월드 수집 URL] 목록 불러오기
        res = requests.get(f"{WEB_APP_URL}?action=getUrls", timeout=20)
        url_tasks = res.json()
    except Exception as e:
        print(f"URL 목록 불러오기 실패: {e}")
        return

    print(f"총 {len(url_tasks)}개 수집 대상 확인 완료. 크롤링을 시작합니다.")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    collected_data = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for task in url_tasks:
        cat = task.get("category", "")
        brand = task.get("brand", "")
        model = task.get("model", "")
        target_url = task.get("url", "")

        if not target_url.startswith("http"):
            continue

        try:
            r = requests.get(target_url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")

            # 월드메모리 가격 테이블 파싱
            rows = soup.select("table tbody tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    item_name = cols[0].get_text(strip=True)
                    raw_price = cols[1].get_text(strip=True)
                    price_digits = "".join(filter(str.isdigit, raw_price))

                    if item_name and price_digits:
                        collected_data.append([
                            cat,
                            brand,
                            model,
                            item_name,
                            int(price_digits),
                            today_str,
                            target_url
                        ])
            print(f"수집 성공: [{cat}] {brand} {model}")
        except Exception as e:
            print(f"수집 실패 ({target_url}): {e}")

        # 상대 서버 과부하 방지 (1.5 ~ 2.5초 지연)
        time.sleep(random.uniform(1.5, 2.5))

    # 비공개 구글 시트의 [매입품목 및 가격] 탭에 결과 전송
    if collected_data:
        print(f"총 {len(collected_data)}개 품목 수집 완료. 구글 시트로 업데이트 전송 중...")
        try:
            post_res = requests.post(WEB_APP_URL, json={"items": collected_data}, timeout=30)
            print(f"시트 반영 결과: {post_res.text}")
        except Exception as e:
            print(f"시트 전송 에러: {e}")
    else:
        print("수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
