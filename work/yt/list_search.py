import sys; sys.stdout.reconfigure(encoding="utf-8")
import json, glob
seen = {}
for f in sorted(glob.glob("search*.jsonl")):
    for line in open(f, encoding="utf-8"):
        try: d = json.loads(line)
        except: continue
        vid = d.get("id")
        if not vid or vid in seen: 
            if vid: seen[vid]["q"].add(f)
            continue
        seen[vid] = {"title": d.get("title",""), "dur": d.get("duration"), "views": d.get("view_count"), "q": {f}}
for vid, d in seen.items():
    print(f"{vid}\t{d['dur']}\t{d['views']}\t{','.join(sorted(x.replace('search','').replace('.jsonl','') for x in d['q']))}\t{d['title']}")
print(len(seen))
