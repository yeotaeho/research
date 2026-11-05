# 수집 결과 점검 — CSV 를 다시 읽어 행 수·플랫폼별·분야별 건수·rating 분포·날짜 범위를 찍는다
import csv
import sys
from collections import Counter
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "appstore_low_reviews.csv"
with path.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

print(f"행 수: {len(rows)}")
print(f"review_id 중복: {len(rows) - len({(r['platform'], r['review_id']) for r in rows})}")
print(f"body<10: {sum(len(r['body']) < 10 for r in rows)}")
print("플랫폼:", dict(Counter(r["platform"] for r in rows)))
print("rating:", dict(Counter(r["rating"] for r in rows)))
dates = sorted(r["review_date"] for r in rows)
print(f"날짜: {dates[0]} ~ {dates[-1]}")

print("\n분야별 (ios/android/합):")
by_cat = Counter((r["category"], r["platform"]) for r in rows)
for cat in dict.fromkeys(r["category"] for r in rows):
    i, a = by_cat[(cat, "ios")], by_cat[(cat, "android")]
    print(f"  {cat:<12} {i:>5} {a:>5} {i + a:>5}")

print("\n앱별 (ios/android):")
by_app = Counter((r["category"], r["app_name"], r["platform"]) for r in rows)
for cat, name in dict.fromkeys((r["category"], r["app_name"]) for r in rows):
    print(f"  {cat:<12} {name:<18} {by_app[(cat, name, 'ios')]:>4} {by_app[(cat, name, 'android')]:>4}")
