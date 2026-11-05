# 콜드메일 대상 앱의 저평점 리뷰에서 결제·구독·환불 불만 비율과 대표 문구를 뽑아 마크다운 표로 찍는다
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

TARGETS = ["플랜핏", "알라미", "마이루틴", "밀리그램", "스픽", "똑닥", "Sleep Cycle", "Noom", "챌린저스", "클래스101", "Renight(미라클나잇)", "런데이", "투두메이트", "열품타", "필라이즈"]
PAY = re.compile(r"구독|결제|환불|유료|멤버십|자동결제|해지|갱신|청구")
THEMES = {
    "무료체험·자동전환": re.compile(r"무료|체험|자동|전환|갱신"),
    "해지했는데 결제": re.compile(r"해지|취소했|취소 했|끊었"),
    "환불 무응답·거절": re.compile(r"환불"),
    "결제 유도·다크패턴": re.compile(r"유도|실수로|잘못 눌|비몽사몽|잠결|팝업|몰래"),
    "가격·표시 혼동": re.compile(r"일주일|주당|연간|1년|년 결제|가격"),
}

agg = defaultdict(lambda: {"n": 0, "pay": 0, "themes": Counter(), "samples": [], "platforms": Counter()})
with (ROOT / "appstore_low_reviews.csv").open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        app = r["app_name"]
        if app not in TARGETS:
            continue
        a = agg[app]
        a["n"] += 1
        a["platforms"][r["platform"]] += 1
        body = (r["title"] + " " + r["body"]).strip()
        if PAY.search(body):
            a["pay"] += 1
            for name, rx in THEMES.items():
                if rx.search(body):
                    a["themes"][name] += 1
            if len(a["samples"]) < 3 and 30 <= len(body) <= 140:
                a["samples"].append(body)

print("| 앱 | 저평점 리뷰 | 결제·구독·환불 불만 | 비율 | 상위 주제 |")
print("|---|---|---|---|---|")
for app, a in sorted(agg.items(), key=lambda kv: -kv[1]["pay"] / max(kv[1]["n"], 1)):
    top = ", ".join(f"{k} {v}" for k, v in a["themes"].most_common(3))
    plat = " / ".join(f"{k} {v}" for k, v in sorted(a["platforms"].items()))
    print(f"| {app} | {a['n']} ({plat}) | {a['pay']} | {a['pay']*100//a['n']}% | {top} |")

print("\n## 대표 문구 (앱별 3개, 140자 이내)\n")
for app, a in sorted(agg.items(), key=lambda kv: -kv[1]["pay"] / max(kv[1]["n"], 1)):
    print(f"### {app}")
    for s in a["samples"]:
        print(f"- {s}")
    print()
