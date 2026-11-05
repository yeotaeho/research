# 블로그·뉴스 URL 본문을 텍스트로 가져온다 — 네이버 블로그는 모바일 변환, 그 외는 Jina → curl_cffi 직접 → insane-search engine 순서로 시도
# 사용: python fetch_text.py <URL> [<출력 txt>]
import os
import re
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from curl_cffi import requests

WORK = "C:/project/trend/research/work"
CA = os.path.join(WORK, "cacert.pem")
ENGINE_DIR = (
    "C:/Users/여태호/.claude/plugins/cache/gptaku-plugins/insane-search/0.8.2/skills/insane-search"
)
IPHONE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def html_to_text(html: str, selectors: list[str] | None = None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "iframe", "svg"]):
        t.decompose()
    node = None
    for sel in selectors or []:
        node = soup.select_one(sel)
        if node:
            break
    if node is None:
        node = soup.find("article") or soup.find("main") or soup.body or soup
    text = node.get_text("\n")
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def meta_date(html: str) -> str:
    m = re.search(
        r'(?:article:published_time|datePublished|og:regDate|publish(?:ed)?_?date)"?\s*(?:content|=)\s*"?([0-9]{4}[-./][0-9]{1,2}[-./][0-9]{1,2}[^"<]*)',
        html,
        flags=re.I,
    )
    if m:
        return m.group(1)[:25]
    m = re.search(r'class="[^"]*(?:se_publishDate|date|blog_date|publish)[^"]*"[^>]*>([^<]{6,40})<', html)
    return m.group(1).strip() if m else ""


def session(impersonate: str = "chrome124") -> requests.Session:
    s = requests.Session(impersonate=impersonate, verify=CA if os.path.exists(CA) else True)
    s.headers.update({"Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5"})
    return s


def fetch_naver_blog(url: str) -> tuple[str, str]:
    p = urlparse(url)
    if "PostView" in p.path or "logNo" in p.query:
        q = parse_qs(p.query)
        blog_id, log_no = q.get("blogId", [""])[0], q.get("logNo", [""])[0]
    else:
        parts = [x for x in p.path.split("/") if x]
        blog_id, log_no = parts[0], parts[1]
    murl = f"https://m.blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
    s = session("safari_ios")
    s.headers.update({"User-Agent": IPHONE_UA, "Referer": "https://m.naver.com/"})
    r = s.get(murl, timeout=30)
    r.raise_for_status()
    html = r.text
    text = html_to_text(html, ["div.se-main-container", "#postViewArea", "div#viewTypeSelector", "div.post_ct"])
    title = ""
    m = re.search(r'<meta property="og:title" content="([^"]*)"', html)
    if m:
        title = m.group(1)
    date = meta_date(html)
    m2 = re.search(r'class="blog_date">([^<]+)<', html) or re.search(r'class="se_publishDate[^"]*">([^<]+)<', html)
    if m2:
        date = m2.group(1).strip()
    return f"TITLE: {title}\nDATE: {date}\nURL: {url}\n\n{text}", "naver_mobile"


def fetch_jina(url: str) -> str:
    r = requests.get(f"https://r.jina.ai/{url}", timeout=90, verify=CA if os.path.exists(CA) else True,
                     headers={"X-Return-Format": "markdown"})
    if r.status_code != 200:
        raise RuntimeError(f"jina {r.status_code}")
    t = r.text
    if len(t) < 1500 or "Just a moment" in t[:3000] or "Access Denied" in t[:3000]:
        raise RuntimeError("jina too short/blocked")
    return t


def fetch_direct(url: str) -> str:
    last = None
    for imp in ("chrome124", "safari", "safari_ios"):
        try:
            s = session(imp)
            if imp == "safari_ios":
                s.headers["User-Agent"] = IPHONE_UA
            r = s.get(url, timeout=30)
            if r.status_code == 200 and len(r.text) > 2000:
                html = r.text
                title = re.search(r"<title>(.*?)</title>", html, flags=re.S)
                head = f"TITLE: {title.group(1).strip() if title else ''}\nDATE: {meta_date(html)}\nURL: {url}\n\n"
                return head + html_to_text(html)
            last = RuntimeError(f"direct {imp} {r.status_code} len={len(r.text)}")
        except Exception as e:  # noqa: BLE001
            last = e
    raise last or RuntimeError("direct failed")


def fetch_engine(url: str) -> str:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", CURL_CA_BUNDLE=CA, SSL_CERT_FILE=CA)
    p = subprocess.run(
        [sys.executable, "-m", "engine", url],
        cwd=ENGINE_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )
    if p.returncode != 0 or len(p.stdout) < 1000:
        raise RuntimeError(f"engine failed: {p.stderr[-800:]}")
    html = p.stdout
    title = re.search(r"<title>(.*?)</title>", html, flags=re.S)
    head = f"TITLE: {title.group(1).strip() if title else ''}\nDATE: {meta_date(html)}\nURL: {url}\n\n"
    return head + html_to_text(html)


def fetch(url: str) -> tuple[str, str]:
    host = urlparse(url).netloc
    if "blog.naver.com" in host:
        return fetch_naver_blog(url)
    errors = []
    for name, fn in (("jina", fetch_jina), ("direct", fetch_direct), ("engine", fetch_engine)):
        try:
            return fn(url), name
        except Exception as e:  # noqa: BLE001
            errors.append(f"{name}: {e}")
    raise RuntimeError(" | ".join(errors))


def main() -> None:
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    text, how = fetch(url)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[{how}] {len(text)} chars -> {out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(f"[{how}]")
        print(text)


if __name__ == "__main__":
    main()
