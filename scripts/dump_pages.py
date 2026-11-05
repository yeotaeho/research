# 검색 결과 HTML 을 파일로 떨어뜨린다 — 파서 작성 전 구조 확인용
import sys
import time
from pathlib import Path

from curl_cffi import requests

sys.path.insert(0, str(Path(__file__).parent))
from probe_sites import TARGETS  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
names = set(sys.argv[2:]) or set(TARGETS)
s = requests.Session(impersonate="chrome124")
s.headers.update({"Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://www.google.com/"})
for name, url in TARGETS.items():
    if name not in names:
        continue
    if name.startswith("naver"):
        s.get("https://www.naver.com/", timeout=10)
        s.headers["Referer"] = "https://www.naver.com/"
    r = s.get(url, timeout=20)
    (out / f"{name}.html").write_text(r.text, encoding="utf-8")
    print(name, r.status_code, len(r.content))
    time.sleep(1)
