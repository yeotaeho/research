# CSV 빈칸 보충 — 네이버 블로그·지식iN 의 날짜와 뽐뿌·82cook 의 본문 앞부분을 글 페이지에서 받아 채운다
import csv
import re
import sys
import time
from html import unescape
from pathlib import Path

from bs4 import BeautifulSoup
from curl_cffi import requests

CSV = Path(__file__).parent.parent / "community_complaints.csv"
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


def get(s, url, **kw):
    try:
        r = s.get(url, timeout=20, **kw)
        return r.text if r.status_code == 200 else ""
    except Exception as e:  # noqa: BLE001
        print(f"  실패 {type(e).__name__} {url[:70]}", file=sys.stderr)
        return ""


def blog_date(s, url):
    m = re.search(r"blog\.naver\.com/([^/]+)/(\d+)", url)
    if not m:
        return ""
    html = get(s, f"https://m.blog.naver.com/PostView.naver?blogId={m[1]}&logNo={m[2]}",
               headers={"User-Agent": IPHONE, "Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://m.naver.com/"})
    d = re.search(r'class="blog_date">\s*(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.', html) or re.search(r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\d{1,2}:\d{2}", html)
    return f"{d[1]}-{int(d[2]):02d}-{int(d[3]):02d}" if d else ""


def kin_date(s, url):
    html = get(s, url)
    d = re.search(r"작성일</span>\s*(\d{4})\.(\d{2})\.(\d{2})", html) or re.search(r'class="answerDate">(\d{4})\.(\d{2})\.(\d{2})', html)
    return f"{d[1]}-{d[2]}-{d[3]}" if d else ""


def body(s, url, sel):
    el = BeautifulSoup(get(s, url), "lxml").select_one(sel)
    return re.sub(r"\s+", " ", el.get_text(" ")).strip()[:300] if el else ""


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
    s = requests.Session(impersonate="chrome124")
    s.headers.update({"Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://www.naver.com/"})
    filled = {"date": 0, "excerpt": 0}
    for r in rows:
        r["title"], r["excerpt"] = unescape(r["title"]), unescape(r["excerpt"])  # RSS 본문의 &#39; 같은 엔티티
        site = r["site"]
        if site in ("naver_blog", "naver_kin") and not r["posted_date"]:
            time.sleep(1)
            r["posted_date"] = blog_date(s, r["url"]) if site == "naver_blog" else kin_date(s, r["url"])
            filled["date"] += bool(r["posted_date"])
        elif site in ("ppomppu", "82cook") and r["excerpt"] == r["title"]:
            time.sleep(1)
            text = body(s, r["url"], "td.board-contents" if site == "ppomppu" else "#articleBody")
            if text:
                r["excerpt"] = text
                filled["excerpt"] += 1
    with open(CSV, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print("채움", filled)


if __name__ == "__main__":
    main()
