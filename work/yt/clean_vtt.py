# VTT 자막에서 타임스탬프·태그를 제거하고 연속 중복 줄을 없애 평문으로 만든다
import sys, re
sys.stdout.reconfigure(encoding="utf-8")
src = sys.argv[1]
out = []
prev = None
for line in open(src, encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in line or re.fullmatch(r"\d+", line):
        continue
    line = re.sub(r"<[^>]+>", "", line)
    line = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", line).strip()
    if not line or line == prev:
        continue
    out.append(line)
    prev = line
text = "\n".join(out)
if len(sys.argv) > 2:
    open(sys.argv[2], "w", encoding="utf-8").write(text)
    print(len(text))
else:
    print(text)
