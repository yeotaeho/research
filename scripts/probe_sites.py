# 커뮤니티 검색 페이지 접근 가능 여부 탐침 — 상태코드·크기·결과 링크 수를 찍어 수집기 설계에 쓴다
import sys
import time
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests

KW = quote("불편")
TARGETS = {
    "clien": f"https://www.clien.net/service/search?q={KW}&sort=recency&boardCd=park",
    "ppomppu": f"https://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard&search_type=sub_memo&keyword={KW}",
    "ppomppu2": f"https://www.ppomppu.co.kr/search_bbs.php?search_type=sub_memo&keyword={KW}&bbs_id=freeboard",
    "fmkorea": f"https://www.fmkorea.com/search.php?mid=home&search_target=title_content&search_keyword={KW}",
    "fmkorea2": f"https://www.fmkorea.com/index.php?act=IS&is_keyword={KW}&mid=home&where=document",
    "theqoo": f"https://theqoo.net/index.php?mid=square&search_target=title_content&search_keyword={KW}",
    "theqoo2": f"https://theqoo.net/index.php?act=IS&is_keyword={KW}&mid=square&where=document",
    "theqoo3": f"https://theqoo.net/square?search_target=title_content&search_keyword={KW}",
    "dcinside": f"https://search.dcinside.com/post/q/{KW}",
    "pann": f"https://pann.nate.com/search?q={KW}",
    "pann2": f"https://pann.nate.com/search?searchType=A&q={KW}",
    "instiz": f"https://www.instiz.net/search?k={KW}",
    "82cook": f"https://www.82cook.com/entiz/enti.php?bn=15&searchType=search&search1=1&keys={KW}",
    "brunch": f"https://brunch.co.kr/search?q={KW}",
    "brunch_api": f"https://api.brunch.co.kr/v1/search/article?q={KW}&page=1&pageSize=20",
    "naver_blog": f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={KW}",
    "naver_blog2": f"https://search.naver.com/search.naver?where=blog&query={KW}",
    "naver_kin": f"https://search.naver.com/search.naver?where=kin&query={KW}",
    "reddit": "https://www.reddit.com/r/korea/search.rss?q=annoying+daily+life&restrict_sr=1",
}


def main(only=None):
    s = requests.Session(impersonate="chrome124")
    s.headers.update({"Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://www.google.com/"})
    for name, url in TARGETS.items():
        if only and name not in only:
            continue
        try:
            if name.startswith("naver"):
                s.get("https://www.naver.com/", timeout=10)
                s.headers["Referer"] = "https://www.naver.com/"
            r = s.get(url, timeout=20)
            soup = BeautifulSoup(r.text, "lxml")
            links = [a.get("href", "") for a in soup.find_all("a", href=True)]
            title = (soup.title.string or "").strip()[:60] if soup.title else ""
            print(f"{name:12} {r.status_code} {len(r.content):>8}B links={len(links):4} title={title!r}")
        except Exception as e:  # noqa: BLE001
            print(f"{name:12} ERR {type(e).__name__}: {str(e)[:80]}")
        time.sleep(1)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
