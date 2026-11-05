# 앱 ID 탐색 — 앱 이름으로 iTunes(kr)·Google Play(kr) 후보를 찍어 수집 목록을 손으로 확정하기 위한 보조 스크립트
import sys
import time

import requests
from google_play_scraper import search

APPS = {
    "가계부·돈관리": ["뱅크샐러드", "편한가계부", "똑똑가계부", "브로콜리 가계부"],
    "할일·루틴·생산성": ["마이루틴", "챌린저스", "TickTick", "Todoist", "투두메이트"],
    "수면·알람": ["알라미", "Sleep Cycle", "미라클나잇"],
    "건강·운동": ["플랜핏", "버닛", "런데이", "다노", "Noom", "인아웃"],
    "식단·다이어트": ["밀리그램", "다이어트신", "필라이즈"],
    "교통·이동": ["카카오T", "티맵", "카카오맵", "네이버지도", "카카오버스", "지하철종결자", "모두의주차장"],
    "배달·음식": ["배달의민족", "쿠팡이츠", "요기요"],
    "쇼핑·중고": ["당근", "번개장터", "쿠팡"],
    "집안일·생활서비스": ["청소연구소", "미소", "런드리고", "세탁특공대"],
    "육아": ["베이비타임", "맘스다이어리", "키즈노트"],
    "반려동물": ["핏펫", "펫프렌즈"],
    "공부·자기계발": ["열품타", "스픽", "밀리의서재", "클래스101"],
    "병원·약": ["똑닥", "굿닥"],
    "행정·공과금": ["정부24"],
}

UA = {"User-Agent": "Mozilla/5.0 (research script)"}


def ios(term):
    r = requests.get(
        "https://itunes.apple.com/search",
        params={"term": term, "country": "kr", "entity": "software", "limit": 5},
        headers=UA,
        timeout=20,
    )
    r.raise_for_status()
    return [(x["trackId"], x["trackName"], x.get("userRatingCount", 0)) for x in r.json()["results"]]


def android(term):
    return [(x["appId"], x["title"], x.get("installs")) for x in search(term, lang="ko", country="kr", n_hits=5)]


for cat, names in APPS.items():
    for name in names:
        print(f"\n## [{cat}] {name}")
        try:
            for tid, tname, cnt in ios(name):
                print(f"  ios     {tid:<12} {cnt:>8}  {tname}")
        except Exception as e:  # noqa: BLE001
            print(f"  ios     ERR {e}", file=sys.stderr)
        try:
            for pkg, title, inst in android(name):
                print(f"  android {str(pkg):<40} {str(inst or ''):>16}  {title}")
        except Exception as e:  # noqa: BLE001
            print(f"  android ERR {e}", file=sys.stderr)
        time.sleep(0.5)
