# 영상 메타 JSON 에서 id·업로드일·제목·길이·설명 앞부분을 뽑는다
import sys, json, glob; sys.stdout.reconfigure(encoding="utf-8")
for f in sorted(glob.glob("*.json")):
    if f.startswith("search"): continue
    try: d = json.load(open(f, encoding="utf-8"))
    except Exception as e: print(f, "ERR", e); continue
    desc = (d.get("description") or "").replace("\n", " ")[:300]
    print(f"{d['id']}\t{d.get('upload_date')}\t{d.get('duration')}\t{d.get('title')}\n    desc: {desc}")
