# community_complaints.csv 를 다시 읽어 행 수·사이트별·분야별 건수·날짜 범위·중복·빈칸을 확인한다
import csv
from collections import Counter
from pathlib import Path

CSV = Path(__file__).parent.parent / "community_complaints.csv"
rows = list(csv.DictReader(open(CSV, encoding="utf-8-sig")))
print("rows", len(rows), "| columns", list(rows[0].keys()))
print("url 중복", len(rows) - len({r["url"] for r in rows}))
for col in ("category", "pain_summary", "matched_keyword", "title", "url"):
    print(f"빈 {col}", sum(1 for r in rows if not r[col]))
print("40자 초과 요약", sum(1 for r in rows if len(r["pain_summary"]) > 40))
dates = sorted(r["posted_date"] for r in rows if r["posted_date"])
print("날짜 범위", dates[0] if dates else None, "~", dates[-1] if dates else None, "| 날짜 없음", len(rows) - len(dates))
print("\n사이트별")
for k, v in Counter(r["site"] for r in rows).most_common():
    print(f"  {k:12} {v}")
print("\n분야별")
for k, v in Counter(r["category"] for r in rows).most_common():
    print(f"  {k:16} {v}")
