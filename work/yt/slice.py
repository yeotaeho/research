# 평문 자막의 문자 범위를 한 줄로 출력한다
import sys; sys.stdout.reconfigure(encoding="utf-8")
t = open(sys.argv[1], encoding="utf-8").read().replace("\n", " ")
a = int(sys.argv[2]); b = int(sys.argv[3]) if len(sys.argv) > 3 else len(t)
print(f"[{a}:{b} of {len(t)}]"); print(t[a:b])
