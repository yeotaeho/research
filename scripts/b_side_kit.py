# B 쪽 콜드메일 묶음 생성 — 앱별 결제 불만 수치·리포트(HTML)·메일 본문·공개 연락처를 research/b_side/ 에 쓴다
import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import markdown
from google_play_scraper import app as play_app
from google_play_scraper.exceptions import NotFoundError

from b_side_classify import RECENT_FROM, REFUND_DENIED, ROOT, TARGETS, THEMES, classify, load_reviews, text_of

OUT = ROOT / "b_side"
PERIOD = f"{RECENT_FROM}~2026-11"
DARK_PATTERN = {
    "무료체험 뒤 유료 전환": "숨은 갱신(유료 전환 전 고지·동의)",
    "모르는 사이 결제·자동 갱신": "숨은 갱신(자동 갱신·증액 전 고지·동의)",
    "해지·취소가 어렵거나 해지 뒤 결제": "취소·탈퇴 등의 방해",
    "결제 유도·잘못 누름": "잘못된 계층구조, 반복간섭",
    "가격을 잘못 알고 결제": "가격 표시 전반. 순차공개 가격책정과 가까울 수 있음",
    "환불·결제 취소 요청": "6개 유형 밖. 청약철회(전자상거래법 제17·18조) 쪽 문제",
    "결제했는데 반영 안 됨": "6개 유형 밖. 결제·복원 오류",
}


def quotable(text: str) -> bool:
    return 25 <= len(text) <= 110 and not re.search(r"\d{7,}|@|https?:", text)


def safe(text: str) -> str:
    return html.escape(re.sub(r"[*_`|#\[\]]", " ", text), quote=False)


def stats(rows: list[dict]) -> dict:
    recent = [r for r in rows if r["review_date"][:7] >= RECENT_FROM]
    pay = [(r, classify(text_of(r))) for r in recent]
    pay = [(r, t) for r, t in pay if t]
    themes = Counter(t for _, ts in pay for t in ts)
    denied = sum(1 for r, _ in pay if REFUND_DENIED.search(text_of(r)))
    return {"n_all": len(rows), "n": len(recent), "pay": len(pay), "themes": themes, "denied": denied, "hits": pay}


def report_md(app: str, s: dict, peers: list[tuple[str, int, int]]) -> str:
    rate = s["pay"] * 100 // max(s["n"], 1)
    lines = [
        f"# {app} 한국 저평점 리뷰의 결제 불만 분석",
        f"작성 2026-11-05. 대상 기간 {PERIOD}. 한국 App Store·Google Play 의 1·2점 리뷰만 봤습니다.",
        "## 요약",
        "| 항목 | 값 |\n|---|---|",
        f"| 기간 내 저평점 리뷰 | {s['n']}건 |",
        f"| 그중 돈이 나간 일·환불·해지 불만 | **{s['pay']}건 ({rate}%)** |",
        f"| 그중 환불 거절·무응답을 말한 글 | {s['denied']}건 |",
        "## 유형별",
        "한 리뷰가 여러 유형에 들어갈 수 있어 합은 위 건수보다 큽니다. 대표 문장은 공개 리뷰 원문이고 작성자 정보는 넣지 않았습니다.",
    ]
    for theme, cnt in s["themes"].most_common():
        lines.append(f"### {theme} ({cnt}건)")
        picks = [text_of(r) for r, ts in sorted(s["hits"], key=lambda x: x[0]["review_date"], reverse=True) if theme in ts and quotable(text_of(r))][:2]
        lines.extend(f"- {safe(p)}" for p in picks)
    lines += [
        "## 공정위 다크패턴 6개 유형과 닿는 지점",
        "2025-02-14 시행 전자상거래법의 유형과 리뷰 불만을 나란히 놓은 표입니다. **실제 결제·해지 화면은 보지 않았고, 위반 여부를 판단한 것이 아닙니다.** 법률 의견이 아닙니다.",
        "| 리뷰 유형 | 건수 | 가까운 규정 |\n|---|---|---|",
    ]
    lines += [f"| {t} | {c} | {DARK_PATTERN[t]} |" for t, c in s["themes"].most_common()]
    if len(peers) > 1:
        lines += ["## 같은 분야 앱과 비교", "같은 분류 기준·같은 기간의 비율입니다. 기간 내 저평점 30건 이상인 앱만 넣었습니다.", "| 앱 | 저평점 | 결제 불만 | 비율 |\n|---|---|---|---|"]
        for name, n, p in sorted(peers, key=lambda x: -x[2] / max(x[1], 1)):
            mark = "**" if name == app else ""
            lines.append(f"| {mark}{name}{mark} | {n} | {p} | {p * 100 // max(n, 1)}% |")
    lines += [
        "## 이 분석의 한계",
        "- 저평점만 모았으므로 전체 사용자 중 불만 비율이 아닙니다. 저평점 안에서의 구성비입니다.",
        "- 수집 범위는 iOS 최근 리뷰 최대 500건 중 저평점, Android 1점 200건·2점 100건 최신순입니다.",
        "- 분류는 키워드 규칙입니다. 표본을 사람이 읽어 확인한 결과 분류된 글의 95% 안팎이 실제 결제·환불·해지 불만이었고, 일부 불만은 놓쳐 건수는 실제보다 조금 적습니다.",
        "- 스토어 정책상 환불 권한이 사업자에게 없는 경우도 있어, 불만이 곧 사업자 잘못이라는 뜻은 아닙니다.",
    ]
    return "\n".join(_block(lines))


def _block(lines: list[str]) -> list[str]:
    # 표 행은 붙이고 나머지는 빈 줄로 나눈다
    out: list[str] = []
    for line in lines:
        if line.startswith("|") and out and out[-1].startswith("|"):
            out.append(line)
        elif line.startswith("- ") and out and out[-1].startswith("- "):
            out.append(line)
        else:
            out += ["", line]
    return out[1:]


def page(title: str, body_md: str) -> str:
    body = markdown.markdown(body_md, extensions=["tables"])
    return (
        f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>'
        "<style>body{font:15px/1.65 'Malgun Gothic','Apple SD Gothic Neo',sans-serif;max-width:720px;margin:32px auto;padding:0 16px;color:#222}"
        "h1{font-size:22px}h2{font-size:17px;margin-top:28px;border-top:1px solid #ddd;padding-top:14px}h3{font-size:15px;margin:16px 0 4px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:6px 8px;text-align:left}th{background:#f4f4f2}</style></head>"
        f"<body>{body}</body></html>"
    )


def email(app: str, s: dict, to: str) -> str:
    rate = s["pay"] * 100 // max(s["n"], 1)
    top = s["themes"].most_common(2)
    name = app.split("(")[0]
    return "\n".join([
        f"## {app}",
        "",
        f"- 받는 곳. {to}",
        f"- 첨부. `b_side/{slug(app)}_report.html`",
        f"- 제목. [{name}] 한국 저평점 리뷰 {s['n']}건 분석 리포트를 보내 드립니다",
        "",
        "안녕하세요. 여태호입니다. 한국 앱의 결제·환불 불만을 데이터로 정리하는 작은 프로젝트를 하고 있습니다.",
        "",
        f"{name}의 한국 스토어 1·2점 리뷰 중 최근 2년 치 {s['n']}건을 분류했습니다. 그중 {s['pay']}건({rate}%)이 돈이 나간 일, 환불, 해지에 관한 불만입니다. 많은 유형은 \"{top[0][0]}\" {top[0][1]}건, \"{top[1][0]}\" {top[1][1]}건입니다.",
        "",
        "유형별 건수와 대표 문장, 같은 분야 앱과의 비교를 첨부했습니다. 비용이나 조건은 없습니다.",
        "",
        "한 가지만 여쭙고 싶습니다. 이런 분석이 결제·환불 흐름을 고치는 데 쓸모가 있을까요? 20분만 의견을 들려주시면 감사하겠습니다. 다음 주 중 편한 시간을 알려 주시면 맞추겠습니다.",
        "",
        "여태호 / [연락처]",
    ])


def slug(app: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "_", app).strip("_")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    OUT.mkdir(exist_ok=True)
    rows = load_reviews()
    by_app: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_app[r["app_name"]].append(r)
    category = {a: v[0]["category"] for a, v in by_app.items()}
    all_stats = {a: stats(v) for a, v in by_app.items()}

    table, mails = [], []
    for app in TARGETS:
        s = all_stats[app]
        android = next((r["app_id"] for r in by_app[app] if r["platform"] == "android"), None)
        to = "못 찾음. 스토어 페이지 확인"
        if android:
            try:
                info = play_app(android, lang="ko", country="kr")
                to = f"{info.get('developerEmail') or '이메일 없음'} ({info.get('developer')})"
            except NotFoundError:
                pass
        peers = [(a, all_stats[a]["n"], all_stats[a]["pay"]) for a in by_app if category[a] == category[app] and all_stats[a]["n"] >= 30]
        md = report_md(app, s, peers)
        (OUT / f"{slug(app)}_report.html").write_text(page(f"{app} 결제 불만 분석", md), encoding="utf-8")
        top = ", ".join(f"{k} {v}" for k, v in s["themes"].most_common(3))
        table.append(f"| {app} | {s['n']} | {s['pay']} | **{s['pay'] * 100 // max(s['n'], 1)}%** | {s['denied']} | {top} | {to} |")
        mails.append(email(app, s, to))

    (OUT / "emails.md").write_text("# 앱별 메일 본문\n\n보내는 순서대로다. `[연락처]` 만 채우고 리포트를 첨부한다.\n\n" + "\n\n---\n\n".join(mails) + "\n", encoding="utf-8")
    head = "| 앱 | 저평점(최근 2년) | 결제 불만 | 비율 | 환불 거절·무응답 언급 | 상위 유형 | 공개 연락처 |\n|---|---|---|---|---|---|---|"
    (OUT / "numbers.md").write_text(f"# 앱별 수치 ({PERIOD})\n\n{head}\n" + "\n".join(table) + "\n", encoding="utf-8")
    print(head)
    print("\n".join(table))


if __name__ == "__main__":
    main()
