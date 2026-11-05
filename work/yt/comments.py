# info.json 에서 자막 종류·설명·댓글을 뽑는다
import sys, json; sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("subs:", list((d.get("subtitles") or {}).keys()), "auto:", list((d.get("automatic_captions") or {}).keys())[:5])
print("upload:", d.get("upload_date"), "title:", d.get("title"))
print("DESC:", (d.get("description") or "").replace("\n", " ")[:1500])
for c in (d.get("comments") or [])[:30]:
    print("-", (c.get("text") or "").replace("\n", " ")[:400])
