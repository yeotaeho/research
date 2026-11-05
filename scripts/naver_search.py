# 네이버 검색(블로그·뉴스·통합 탭)을 curl_cffi 로 돌려 결과 URL·제목·날짜를 JSON lines 로 뽑는다
# 사용: python naver_search.py "<검색어>" [--tab post|news|web|all] [--pages 1] [--sort date|sim]
import argparse
import json
import os
import re
import sys
from urllib.parse import quote

from bs4 import BeautifulSoup
from curl_cffi import requests

CA = "C:/project/trend/research/work/cacert.pem"
POST_RE = re.compile(r"https://blog\.naver\.com/[A-Za-z0-9_\-]+/\d+")


def search(query: str, tab: str, pages: int, sort: str) -> list[dict]:
    s = requests.Session(impersonate="chrome124", verify=CA if os.path.exists(CA) else True)
    s.headers.update({"Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://www.google.com/"})
    s.get("https://www.naver.com/", timeout=15)
    s.headers["Referer"] = "https://www.naver.com/"
    where = {"post": "post", "news": "news", "web": "web", "all": "nexearch"}[tab]
    results: dict[str, dict] = {}
    for page in range(pages):
        start = 1 + page * 10
        url = f"https://search.naver.com/search.naver?where={where}&query={quote(query)}&start={start}"
        if sort == "date":
            url += "&sm=tab_opt&sort=1" if tab == "news" else "&sm=tab_opt&nso=so:dd"
        r = s.get(url, timeout=25)
        if r.status_code != 200:
            print(f"page {page+1}: HTTP {r.status_code}", file=sys.stderr)
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if tab == "post" and not POST_RE.fullmatch(href):
                continue
            if tab == "news" and "n.news.naver.com" not in href and "news.naver.com" not in href and not href.startswith("http"):
                continue
            if tab in ("web", "all") and not href.startswith("http"):
                continue
            if "naver.com" in href and tab in ("web", "all") and "blog.naver.com" not in href and "cafe.naver.com" not in href:
                continue
            text = a.get_text(" ", strip=True)
            if not text or len(text) < 6:
                continue
            cur = results.setdefault(href, {"url": href, "title": "", "snippets": []})
            if len(text) > len(cur["title"]) and len(text) < 200:
                cur["title"] = text
        # dates are near the links in the result card; capture "N일 전" / "2026.05.21." patterns
        for card in soup.select("div.sds-comps-base-layout, li.bx, div.view_wrap"):
            links = [a["href"] for a in card.find_all("a", href=True) if a["href"] in results]
            if not links:
                continue
            txt = card.get_text(" ", strip=True)
            m = re.search(r"(\d{4}\.\d{1,2}\.\d{1,2}\.?|\d+\s*(?:일|시간|분|주|개월)\s*전|어제)", txt)
            for href in set(links):
                if m and not results[href].get("date"):
                    results[href]["date"] = m.group(1)
                snippet = txt[:300]
                if snippet not in results[href]["snippets"]:
                    results[href]["snippets"].append(snippet)
    out = []
    for r_ in results.values():
        r_["snippet"] = (r_["snippets"][0] if r_["snippets"] else "")[:300]
        del r_["snippets"]
        out.append(r_)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--tab", default="post", choices=["post", "news", "web", "all"])
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--sort", default="sim", choices=["sim", "date"])
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    for row in search(a.query, a.tab, a.pages, a.sort):
        print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
