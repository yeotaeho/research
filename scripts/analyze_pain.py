# 커뮤니티 불만글의 한 줄 요약을 분야별로 모두 찍고, 앱 리뷰에서 기능 요청·결제 불만 비율과 표본을 분야별로 뽑는다
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# 1. 커뮤니티: 분야별 pain_summary 전부
by_cat = defaultdict(list)
with (ROOT / "community_complaints.csv").open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        by_cat[r["category"]].append((r["site"], r["pain_summary"], r["posted_date"][:4]))

print("=" * 20, "커뮤니티 pain_summary (분야별)", "=" * 20)
for cat, items in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
    print(f"\n## {cat} ({len(items)})")
    for site, pain, year in items:
        print(f"- [{site} {year}] {pain}")

# 2. 앱 리뷰: 분야별 기능 요청·결제 불만 비율과 표본
REQ = re.compile(r"있었으면|추가해|추가 해|추가됐으면|기능이 없|지원이 안|지원 안|지원해|됐으면|해주세요|해 주세요|해줬으면|만들어주|넣어주")
PAY = re.compile(r"구독|결제|환불|유료|멤버십|자동결제|해지")
BUG = re.compile(r"튕|오류|먹통|로그인|인증|느려|렉|버그|안 열|안열|실행이 안|업데이트")

stats = defaultdict(lambda: {"n": 0, "req": 0, "pay": 0, "bug": 0, "apps": Counter(), "samples": []})
with (ROOT / "appstore_low_reviews.csv").open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        s = stats[r["category"]]
        body = (r["title"] + " " + r["body"]).strip()
        s["n"] += 1
        s["apps"][r["app_name"]] += 1
        if PAY.search(body):
            s["pay"] += 1
        if BUG.search(body):
            s["bug"] += 1
        if REQ.search(body) and not BUG.search(body):
            s["req"] += 1
            if len(s["samples"]) < 10 and 40 <= len(body) <= 300:
                s["samples"].append((r["app_name"], body.replace("\n", " ")[:160]))

print("\n\n", "=" * 20, "앱 리뷰 분야별 집계", "=" * 20)
print("분야 | 건수 | 결제·구독 불만% | 결함% | 기능요청(결함 제외)% | 앱(건수)")
for cat, s in sorted(stats.items(), key=lambda kv: -kv[1]["n"]):
    n = s["n"]
    apps = ", ".join(f"{a}({c})" for a, c in s["apps"].most_common(6))
    print(f"{cat} | {n} | {s['pay']*100//n}% | {s['bug']*100//n}% | {s['req']*100//n}% | {apps}")

print("\n\n", "=" * 20, "앱 리뷰 기능 요청 표본 (결함 제외)", "=" * 20)
for cat, s in sorted(stats.items(), key=lambda kv: -kv[1]["n"]):
    print(f"\n## {cat}")
    for app, body in s["samples"]:
        print(f"- [{app}] {body}")
