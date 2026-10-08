import requests
import json

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzr758VEVM0e85ep9AYFMorQAz7gWh7mP064IkGoy-jkaz6_GwmRJriSsNNuWXXa1CMWA/exec"

# 1. 비공개 시트에서 수집 대상 URL 목록 가져오기
res = requests.get(f"{WEB_APP_URL}?action=getUrls")
url_tasks = res.json()

# 2. 크롤링 수행 후 시트에 저장할 때 (POST)
# items = [[구분, 브랜드, 세대, 품목명, 단가, 날짜, URL], ...]
payload = {"items": collected_data}
post_res = requests.post(WEB_APP_URL, json=payload)
print(post_res.json())
