# research/ 의 CSV 4개를 csv 모듈로 다시 읽어 행 수·컬럼 수·빈 필수칸·중복 키를 점검한다
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "appstore_low_reviews.csv": ("review_id", ["platform", "category", "app_name", "rating", "review_date", "body"]),
    "community_complaints.csv": ("url", ["site", "category", "title", "url", "pain_summary"]),
    "modoo_yechang_stats.csv": (None, ["program", "cohort", "stage", "metric", "value", "source_url"]),
    "modoo_yechang_reviews.csv": (None, ["program", "year", "stage", "outcome", "source_url"]),
}

ok = True
for name, (key, required) in FILES.items():
    path = ROOT / name
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        rows = list(reader)
    widths = Counter(len([v for v in r.values() if v is not None]) for r in rows)
    bad_width = {w: c for w, c in widths.items() if w != len(header)}
    empties = {col: sum(1 for r in rows if not (r.get(col) or "").strip()) for col in required}
    empties = {c: n for c, n in empties.items() if n}
    dup = 0
    if key:
        keys = Counter(r[key] for r in rows)
        dup = sum(c - 1 for c in keys.values() if c > 1)
    newline_rows = sum(1 for r in rows if any("\n" in (v or "") for v in r.values()))
    status = "OK" if not bad_width and not empties and not dup and not newline_rows else "CHECK"
    if status != "OK":
        ok = False
    print(f"{status:5} {name}: rows={len(rows)} cols={len(header)} "
          f"bad_width={bad_width or '-'} empty={empties or '-'} dup_{key or 'key'}={dup} newline_rows={newline_rows}")

sys.exit(0 if ok else 1)
