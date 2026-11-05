# JSONL 을 다시 읽어 행 수·키·분포를 확인한다
import sys, json, collections; sys.stdout.reconfigure(encoding="utf-8")
KEYS = ["program","year","stage","outcome","item_type","item_summary","judge_questions","scoring_points","advice","source_site","source_url","published_date"]
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
print("rows:", len(rows))
bad = [i for i, r in enumerate(rows) if list(r.keys()) != KEYS or not all(isinstance(v, str) for v in r.values())]
print("key/type violations:", bad)
print("program:", dict(collections.Counter(r["program"] for r in rows)))
print("program x outcome:", dict(collections.Counter((r["program"], r["outcome"]) for r in rows)))
print("stage:", dict(collections.Counter(r["stage"] for r in rows)))
print("urls unique:", len({r["source_url"] for r in rows}))
print("judge_questions filled:", sum(1 for r in rows if r["judge_questions"]))
