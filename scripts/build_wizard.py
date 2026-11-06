# 위자드 빌드와 링크 점검 — artifact.html 을 독립 페이지 index.html 로 감싸고 외부 링크가 살아 있는지 확인한다
import argparse
import base64
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

WIZARD = Path(__file__).resolve().parents[1] / "wizard"
REPO = "yeotaeho/refund-guide"
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
# 페이지 이름 → 검색 설명. 빈 이름이 첫 페이지, gym 은 헬스장 환불 계산기다
PAGES = {
    "": "잠결 결제, 무료체험 전환 결제를 어디에 뭐라고 보내야 환불되는지 결제 유형별로 알려 드립니다.",
    "gym": "헬스장·PT·필라테스·요가 이용권을 중간에 그만둘 때 얼마를 돌려받을 수 있는지 계산하고 업체와 카드사에 보낼 문구를 알려 드립니다.",
}
HEAD = (
    '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<meta name="description" content="{description}">'
    "<style>body{margin:0}[hidden]{display:none!important}</style></head><body>"
)


def set_const(html: str, name: str, value: str) -> str:
    out, n = re.subn(rf'const {name} = ".*?";', f'const {name} = "{value}";', html, count=1)
    assert n == 1, f"{name} 상수를 찾지 못함"
    return out


def status(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return str(resp.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except OSError as e:
        return f"연결 실패 {e}"


def publish(page: Path, repo_path: str, message: str) -> None:
    # 공개 저장소에는 페이지 파일만 둔다. research/ 가 딸려 가지 않도록 clone 없이 API 로 교체한다
    api = f"repos/{REPO}/contents/{repo_path}"
    body = {"message": message + TRAILER, "content": base64.b64encode(page.read_bytes()).decode()}
    current = subprocess.run(["gh", "api", api, "--jq", ".sha"], capture_output=True, text=True)
    if current.returncode == 0:
        body["sha"] = current.stdout.strip()
    subprocess.run(["gh", "api", api, "-X", "PUT", "--input", "-", "--jq", ".commit.html_url"], input=json.dumps(body), text=True, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="", choices=list(PAGES), help="빈 값은 첫 페이지, gym 은 헬스장 환불 계산기")
    ap.add_argument("--form", help="제보 폼 주소. artifact.html 에도 기록한다")
    ap.add_argument("--counter", help="GoatCounter 코드. index.html 에만 넣는다")
    ap.add_argument("--publish", metavar="커밋메시지", help="링크 점검을 통과하면 공개 저장소에 올린다")
    args = ap.parse_args()

    folder = WIZARD / args.page
    src = folder / "artifact.html"
    html = src.read_text(encoding="utf-8")
    if args.form:
        assert args.form.startswith("https://"), "제보 폼 주소는 https 여야 한다"
        html = set_const(html, "REPORT_FORM_URL", args.form)
        src.write_text(html, encoding="utf-8")
    page = set_const(html, "COUNTER_CODE", args.counter) if args.counter else html
    title = re.search(r"<title>.*?</title>\n?", page).group(0)
    page = page.replace(title, "", 1)
    head = HEAD.replace("{description}", PAGES[args.page]).replace("</head>", title.strip() + "</head>")
    (folder / "index.html").write_text(head + page + "</body></html>", encoding="utf-8")

    bad = 0
    for url in sorted(set(re.findall(r'href="(https://[^"]+)"', html))):
        code = status(url)
        print(f"{code}  {url}")
        bad += code not in ("200", "401", "403")
    print(f"index.html 생성. 문제 링크 {bad}개")
    if bad:
        return 1
    if args.publish:
        publish(folder / "index.html", f"{args.page}/index.html".lstrip("/"), args.publish)
    return 0


if __name__ == "__main__":
    sys.exit(main())
