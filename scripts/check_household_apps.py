# 집안일 분담 앱 경쟁 수치 재확인 — iTunes Search API 로 출시일·평가 수를 세고 Play 상세를 대조한다
import json
import urllib.parse
import urllib.request
from google_play_scraper import app as play_app, search as play_search
from google_play_scraper.exceptions import NotFoundError

TERMS = ["집안일 분담", "가사 분담", "가사분담", "집안일 관리", "집안일 앱", "커플 집안일", "부부 집안일", "집안일 체크리스트", "집안일 공유"]
WORDS = ("집안일", "가사", "분담", "chore", "살림")

seen: dict[int, dict] = {}
for term in TERMS:
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": term, "country": "kr", "entity": "software", "limit": 50}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        for r in json.load(resp)["results"]:
            text = (r["trackName"] + " " + r.get("description", "")[:400]).lower()
            if any(w in r["trackName"].lower() for w in WORDS) or ("집안일" in text and "분담" in text):
                seen[r["trackId"]] = r

rows = sorted(seen.values(), key=lambda r: r["releaseDate"], reverse=True)
print(f"iOS 관련 앱 {len(rows)}개")
y26 = [r for r in rows if r["releaseDate"][:4] == "2026"]
print(f"2026 출시 {len(y26)}개, 그중 평가 5건 이하 {sum(1 for r in y26 if r.get('userRatingCount', 0) <= 5)}개")
print("평가 10건 이상:")
for r in sorted(rows, key=lambda r: -r.get("userRatingCount", 0)):
    if r.get("userRatingCount", 0) >= 10:
        print(
            f"  {r['trackName'][:40]} | {r['sellerName'][:24]} | {r['releaseDate'][:10]} | "
            f"{r.get('averageUserRating', 0):.1f} ({r.get('userRatingCount', 0)}) | {r.get('formattedPrice')}"
        )

print("\nPlay 상세")
for name in ["가사함께 집안일", "TwoDo 커플 부부 공유 할일", "Nipto 집안일 나누기", "Home Tasker 집안일"]:
    hits = [h for h in play_search(name, lang="ko", country="kr", n_hits=5) if h.get("appId")]
    if not hits:
        print(f"  {name}: 검색 결과 없음")
    for h in hits[:1]:
        try:
            d = play_app(h["appId"], lang="ko", country="kr")
        except NotFoundError:
            print(f"  {h['appId']}: 상세 404")
            continue
        print(
            f"  {d['title'][:40]} | {d['developer'][:20]} | 출시 {d.get('released')} | "
            f"{d.get('score') and round(d['score'], 1)} ({d.get('ratings')}) | 설치 {d.get('installs')} | IAP {d.get('inAppProductPrice')}"
        )
