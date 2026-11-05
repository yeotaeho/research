# 레딧 r/korea·r/Living_in_Korea 검색 RSS — 429 가 잦아 TLS 지문을 바꿔 가며 30초 간격으로 2회 재시도한다
import html
import json
import re
import sys
import time
from xml.etree import ElementTree as ET

from curl_cffi import requests

SUBS = ["korea", "Living_in_Korea"]
QUERIES = ["annoying daily life", "frustrating everyday", "hate how every time", "inconvenient korea"]
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch(url):
    for imp in ("safari_ios", "safari", "chrome"):
        for _ in range(2):
            r = requests.get(url, impersonate=imp, timeout=25, headers={"Accept": "application/rss+xml,application/atom+xml,*/*"})
            if r.status_code == 200 and b"<feed" in r.content:
                return r.text
            print(f"  {imp} {r.status_code}", file=sys.stderr)
            if r.status_code != 429:
                break
            time.sleep(30)
    return None


def main(out):
    rows = []
    for sub in SUBS:
        for q in QUERIES:
            xml = fetch(f"https://www.reddit.com/r/{sub}/search.rss?q={q.replace(' ', '+')}&restrict_sr=1&sort=relevance&t=all")
            if not xml:
                print(f"{sub}/{q}: 실패", file=sys.stderr)
                continue
            for e in ET.fromstring(xml).findall("a:entry", NS):
                link = e.find("a:link", NS).get("href")
                content = html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(e.findtext("a:content", "", NS))))
                rows.append({"site": "reddit", "board": f"r/{sub}", "title": e.findtext("a:title", "", NS), "url": link,
                             "posted_date": e.findtext("a:updated", "", NS)[:10], "views": "", "comments": "", "likes": "",
                             "snippet": re.sub(r"\s+", " ", content).strip()[:300], "matched_keyword": q})
            time.sleep(1)
    seen = set()
    with open(out, "w", encoding="utf-8") as fp:
        for r in rows:
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"reddit rows={len(seen)}")


if __name__ == "__main__":
    main(sys.argv[1])
