# 크몽·위시켓·탈잉·당근(비즈프로필·광고)에 돈을 내는 판매자·튜터·사장님 쪽 글과 저평점 리뷰를 모은다
"""
실행: uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml --with google-play-scraper python -X utf8 scripts/collect_platform_pro.py
산출: research/work/wide/platform_pro_posts.jsonl, platform_pro_reviews.jsonl. 네이버는 2초 간격. 작성자 이름은 저장하지 않는다.
"""
import json
import re
import time
import urllib.request
from pathlib import Path

from google_play_scraper import Sort, reviews as play_reviews, search as play_search

from collect_complaints import Clien, Dcinside, NaverKin, Pann, Ppomppu
from collect_wide import NaverCafe

OUT = Path(__file__).resolve().parents[1] / "work" / "wide"
QUERIES = {
    "크몽": ["크몽 수수료 전문가", "크몽 전문가 광고비", "크몽 정산 지연", "크몽 직거래 제재", "크몽 판매 안 돼"],
    "위시켓": ["위시켓 수수료", "위시켓 프리랜서 후기", "위시켓 프로젝트 지원 안 돼", "위시켓 미팅 비용"],
    "탈잉": ["탈잉 튜터 수수료", "탈잉 정산", "탈잉 튜터 후기", "탈잉 클래스 등록"],
    "당근": ["당근 광고 효과 사장님", "당근 비즈프로필 광고비", "당근 광고 돈 아깝", "당근 전문가 찾기 견적", "당근 동네업체 후기 관리"],
}
# 판매자·사장님 쪽 리뷰만 남기는 말
SELLER = re.compile(r"(수수료|정산|전문가|판매자|튜터|강사|사장님|광고비|광고|비즈프로필|입찰|지원했|파트너|프리랜서|의뢰 받|주문 받)")
APPS = {"크몽": "크몽", "위시켓": "위시켓", "탈잉": "탈잉", "당근": "당근", "당근 비즈니스": "당근 비즈니스"}
IOS_IDS = {"크몽": "1116694237", "위시켓": "1046604548", "탈잉": "1187420322", "당근": "1018769995"}


def ios_reviews(app_id, pages=5):
    out = []
    for p in range(1, pages + 1):
        url = f"https://itunes.apple.com/kr/rss/customerreviews/page={p}/id={app_id}/sortby=mostrecent/json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        except Exception:  # noqa: BLE001
            break
        entries = data.get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        for e in entries:
            if "im:rating" not in e:
                continue
            out.append({"platform": "ios", "rating": int(e["im:rating"]["label"]), "date": e.get("updated", {}).get("label", "")[:10], "title": e.get("title", {}).get("label", ""), "body": e.get("content", {}).get("label", "")})
        time.sleep(1.5)
    return out


def main():
    rows = []
    sites = [(Dcinside(), 1), (Clien(), 1), (Pann(), 1), (Ppomppu(), 1), (NaverCafe(), 2), (NaverKin(), 2)]
    for site, delay in sites:
        for plat, qs in QUERIES.items():
            for q in qs:
                time.sleep(delay)
                try:
                    items = site.search(q, 1)
                except Exception as e:  # noqa: BLE001
                    print(site.name, q, type(e).__name__, flush=True)
                    continue
                for it in items:
                    rows.append({"plat": plat, "site": site.name, "query": q, **it})
        print(site.name, "누적", len(rows), flush=True)
    with (OUT / "platform_pro_posts.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    revs = []
    for plat, term in APPS.items():
        try:
            hits = play_search(term, lang="ko", country="kr", n_hits=3)
            pkg = next((h["appId"] for h in hits if term.split()[0] in h["title"]), None)
            if pkg:
                rs, _ = play_reviews(pkg, lang="ko", country="kr", sort=Sort.NEWEST, count=400)
                for r in rs:
                    if r["score"] <= 2:
                        revs.append({"plat": plat, "app": pkg, "platform": "android", "rating": r["score"], "date": str(r["at"])[:10], "title": "", "body": r["content"] or ""})
        except Exception as e:  # noqa: BLE001
            print("play", plat, type(e).__name__, flush=True)
        time.sleep(2)
    for plat, app_id in IOS_IDS.items():
        for r in ios_reviews(app_id):
            if r["rating"] <= 2:
                revs.append({"plat": plat, "app": app_id, **r})
    for r in revs:
        r["seller_side"] = bool(SELLER.search(r["title"] + " " + r["body"]))
    with (OUT / "platform_pro_reviews.jsonl").open("w", encoding="utf-8") as f:
        for r in revs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("글", len(rows), "저평점 리뷰", len(revs), "판매자 쪽", sum(r["seller_side"] for r in revs))


if __name__ == "__main__":
    main()
