# 설계사 쪽 고통 수집기 — 소비자가 아니라 보험설계사·GA 가 쓴 글을 커뮤니티에서 찾고 설계사용 앱 평점을 본다
"""
실행: uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml --with google-play-scraper python -X utf8 collect_fc.py
산출: research/work/wide/fc_raw.jsonl, research/work/wide/fc_apps.jsonl
네이버는 2초 간격으로 돈다. 작성자 이름은 저장하지 않는다.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from google_play_scraper import app as play_app, search as play_search

from collect_wide import Clien, Dcinside, NaverCafe, NaverKin, Pann, Ppomppu

OUT = Path(__file__).resolve().parents[1] / "work" / "wide"
QUERIES = [
    "보험설계사 디비 비용", "설계사 불량 디비", "설계사 환수", "설계사 수수료 분급", "GA 수수료 개편 설계사",
    "설계사 고객 관리 앱", "설계사 보장분석 프로그램", "설계사 그만두고 싶다", "보험 영업 고객 없어",
    "설계사 승환 계약", "설계사 정착지원금", "설계사 개척 영업", "설계사 민원 해촉", "설계사 초년도 수입",
]
APP_TERMS = ["보험설계사", "설계사 영업", "보험 영업 관리", "보장분석 설계사", "보험 설계사 고객관리", "GA 보험 영업", "FC 영업 지원"]


def main():
    seen, rows = set(), []
    for cls, delay in ((Dcinside, 1), (Clien, 1), (Pann, 1), (Ppomppu, 1), (NaverCafe, 2), (NaverKin, 2)):
        site = cls()
        for q in QUERIES:
            time.sleep(delay)
            try:
                items = site.search(q, 1)
            except Exception as e:  # noqa: BLE001
                print(site.name, q, type(e).__name__)
                items = []
            for it in items:
                if it["url"] in seen:
                    continue
                seen.add(it["url"])
                rows.append({"site": site.name, "query": q, **it})
        print(site.name, "누적", len(rows), site.errors[:2], flush=True)
    with (OUT / "fc_raw.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    apps = {}
    for term in APP_TERMS:
        url = "https://itunes.apple.com/search?" + urllib.parse.urlencode({"term": term, "country": "kr", "entity": "software", "limit": 15})
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            for r in json.load(resp)["results"]:
                apps[("ios", r["trackId"])] = {"platform": "ios", "name": r["trackName"], "dev": r.get("sellerName", ""), "rating": round(r.get("averageUserRating", 0), 2), "count": r.get("userRatingCount", 0), "updated": r.get("currentVersionReleaseDate", "")[:10], "term": term, "desc": r.get("description", "")[:120].replace("\n", " ")}
        time.sleep(3.2)
        for h in play_search(term, lang="ko", country="kr", n_hits=15):
            pkg = h.get("appId")
            if not pkg or ("android", pkg) in apps:
                continue
            try:
                d = play_app(pkg, lang="ko", country="kr")
            except Exception:  # noqa: BLE001
                continue
            hist = d.get("histogram") or [0] * 5
            total = sum(hist) or 1
            apps[("android", pkg)] = {"platform": "android", "name": d["title"], "dev": d.get("developer", ""), "rating": round(d.get("score") or 0, 2), "count": d.get("ratings") or 0, "low": round(100 * (hist[0] + hist[1]) / total, 1), "installs": d.get("installs"), "term": term, "desc": (d.get("description") or "")[:120].replace("\n", " ")}
    with (OUT / "fc_apps.jsonl").open("w", encoding="utf-8") as f:
        for a in apps.values():
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    print("글", len(rows), "앱", len(apps))


if __name__ == "__main__":
    main()
