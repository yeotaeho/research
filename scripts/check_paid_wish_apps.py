# 돈·소원 조사에서 나온 후보 자리마다 기존 앱이 있는지 양쪽 스토어에서 이름·평점·평가 수를 본다
"""
실행: uv run --no-project --with google-play-scraper python -X utf8 scripts/check_paid_wish_apps.py
산출: research/work/wide/pw_apps.jsonl. iTunes 는 3.2초 간격.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from google_play_scraper import app as play_app, search as play_search

OUT = Path(__file__).resolve().parents[1] / "work" / "wide" / "pw_apps.jsonl"
TERMS = {
    "구독 관리": ["구독 관리", "정기결제 관리", "왓섭"],
    "해지 대행": ["해지 대행", "구독 해지"],
    "전화 대행": ["전화 대행", "AI 전화 예약", "전화 대신"],
    "전세대출 매물": ["전세대출 가능 매물", "허그 전세대출 매물"],
    "여행 일정 공동 편집": ["여행 일정 공유", "트리플 여행", "여행 플래너"],
    "1인 사업자 고객 관리": ["소상공인 고객관리", "예약 관리 사장님", "1인샵 예약", "견적서 앱"],
    "소상공인 매출 통합": ["매출 관리 사장님", "POS 매출 확인"],
    "이사 가전 설치 회수": ["가전 설치 회수", "이사 가전 이전설치"],
    "단지 부채 비율": ["아파트 근저당 조회", "등기 조회 아파트"],
    "아르바이트 급여 기록": ["알바 급여 계산", "일용직 일당 기록"],
}


def itunes(term):
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode({"term": term, "country": "kr", "entity": "software", "limit": 8})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)["results"]


def main():
    rows = []
    for slot, terms in TERMS.items():
        for term in terms:
            try:
                for r in itunes(term):
                    rows.append({"slot": slot, "term": term, "platform": "ios", "name": r["trackName"], "dev": r.get("sellerName", ""), "rating": round(r.get("averageUserRating", 0), 2), "count": r.get("userRatingCount", 0), "updated": r.get("currentVersionReleaseDate", "")[:10], "desc": r.get("description", "")[:100].replace("\n", " ")})
            except Exception as e:  # noqa: BLE001
                print("ios", term, type(e).__name__, flush=True)
            time.sleep(3.2)
            try:
                for h in play_search(term, lang="ko", country="kr", n_hits=6):
                    pkg = h.get("appId")
                    if not pkg:
                        continue
                    d = play_app(pkg, lang="ko", country="kr")
                    rows.append({"slot": slot, "term": term, "platform": "android", "name": d["title"], "dev": d.get("developer", ""), "rating": round(d.get("score") or 0, 2), "count": d.get("ratings") or 0, "installs": d.get("installs"), "updated": "", "desc": (d.get("description") or "")[:100].replace("\n", " ")})
            except Exception as e:  # noqa: BLE001
                print("android", term, type(e).__name__, flush=True)
        print(slot, len(rows), flush=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("끝", len(rows))


if __name__ == "__main__":
    main()
