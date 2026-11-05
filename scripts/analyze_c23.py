# 후보 2·3(집안일 장부·재처방 비서) 관련 신호를 수집 CSV 에서 세어 work/c23_signals.txt 로 쓴다
import csv
import re
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "work" / "c23_signals.txt"
lines: list[str] = []


def say(s: str = "") -> None:
    lines.append(s)


def load(name: str) -> list[dict]:
    with open(ROOT / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def theme_count(rows: list[dict], themes: dict[str, str], text=lambda r: r["title"] + " " + r["body"]) -> None:
    n = len(rows)
    for k, p in themes.items():
        c = sum(1 for r in rows if re.search(p, text(r)))
        say(f"  {k}: {c}/{n} ({c * 100 // max(n, 1)}%)")


def samples(rows: list[dict], pat: str, k: int = 6, width: int = 110) -> None:
    out = [r for r in rows if re.search(pat, r["title"] + " " + r["body"])]
    for r in out[:k]:
        body = (r["title"] + " " + r["body"]).replace("\n", " ")
        say(f"    · [{r['app_name']} {r['platform']} {r['review_date'][:7]}] {body[:width]}")


ar = load("appstore_low_reviews.csv")
cm = load("community_complaints.csv")
by_app = collections.defaultdict(list)
for r in ar:
    by_app[r["app_name"]].append(r)

# ---------------- 후보 3 재처방 비서 ----------------
say("# 후보 3 재처방 비서 — 앱 리뷰 신호")
for app in ["똑닥", "굿닥"]:
    rows = by_app[app]
    say(f"\n## {app} 저평점 {len(rows)}건")
    theme_count(rows, {
        "대기·순번·선착순": r"대기|순번|선착|접수 ?마감|접수가|줄",
        "유료·결제·환불": r"결제|유료|구독|환불|멤버십|천백|1,?100",
        "장애·오류": r"오류|장애|에러|튕|먹통|안 ?됨|안 ?되",
        "비대면·처방·약": r"비대면|처방|재진|초진|약 ?배송|약국",
        "병원 정보 부정확": r"정보가|틀리|다르|없는 병원|폐업|영업 ?시간",
        "노인·앱 못 쓰는 사람": r"어르신|노인|부모님|할머니|할아버지",
    })
    say("  비대면·처방 표본")
    samples(rows, r"비대면|처방|재진|약 ?배송")

say("\n## 커뮤니티 병원·약 35건 중 재처방·대기 23건의 세부")
med = [r for r in cm if re.search("병원|약", r["category"])]
sub = {
    "같은 약 재처방인데 매번 진료·대기": r"같은 약|재처방|10초|15초|1분 진료|매번 (병원|진료|검사)",
    "처방 일수 제한(14일·일주일치)": r"14일|일주일치|2주마다|주기|떨어질",
    "원내처방·약값 싼 병원 찾기": r"원내|약값|싼 병원|발품",
    "비대면 제한·금지": r"비대면",
    "대리처방 서류": r"대리",
    "탈모·여드름·안약 등 비급여": r"탈모|여드름|안약|인공눈물|주사제",
}
for k, p in sub.items():
    c = [r for r in med if re.search(p, r["title"] + r["excerpt"] + r["pain_summary"])]
    say(f"  {k}: {len(c)}")
say("  연도 분포: " + str(collections.Counter(r["posted_date"][:4] for r in med).most_common()))
say("  사이트 분포: " + str(collections.Counter(r["site"] for r in med).most_common()))

# ---------------- 후보 2 집안일 장부 ----------------
say("\n\n# 후보 2 집안일 장부 — 앱 리뷰 신호")
say("\n## 집안일 외주 앱(청소연구소·미소·런드리고·세탁특공대) — 돈 쓰는 대체재의 불만")
house = [r for r in ar if r["category"] == "집안일·생활서비스"]
say(f"  합계 {len(house)}건: " + str(collections.Counter(r["app_name"] for r in house).most_common()))
theme_count(house, {
    "가격·비쌈": r"비싸|가격|요금|인상|올랐",
    "품질·대충": r"대충|엉망|더러|파손|분실|망가|훼손",
    "취소·배정 실패": r"취소|배정|노쇼|안 ?오|연락 ?없",
    "환불·결제": r"환불|결제|구독|정기",
})

say("\n## 공유형 앱(투두메이트·베이비타임·키즈노트) — 둘 이상이 같이 쓰는 기록의 불만")
shared = [r for r in ar if r["app_name"] in ("투두메이트", "베이비타임", "키즈노트")]
say(f"  합계 {len(shared)}건: " + str(collections.Counter(r["app_name"] for r in shared).most_common()))
theme_count(shared, {
    "동기화·공유 깨짐": r"동기화|공유|연동|같이|가족|친구|초대",
    "기록 유실": r"날아|날라|사라|삭제|유실|초기화|복구",
    "알림 문제": r"알림|푸시",
    "결제·구독": r"결제|구독|유료|환불|프리미엄",
    "잔소리·압박감": r"잔소리|압박|부담|스트레스|강박",
})
say("  동기화·공유 표본")
samples(shared, r"동기화|공유|가족|친구|초대", k=8)

say("\n## 커뮤니티 집안일·육아 63건의 세부")
home = [r for r in cm if re.search("집안일|육아", r["category"])]
sub2 = {
    "분담·독박·나만 함": r"분담|나만|혼자|떠넘|떠안|독박|왜 매번 내가|혼자 책임|같이 안|안 도와",
    "일 자체가 귀찮음·힘듦(설거지·빨래·청소)": r"귀찮|번거|싫어|미루|지침|힘듦|스트레스",
    "보이지 않는 일(식단·준비물·물건 위치·일정)": r"식단|준비물|물건 위치|일정|기억|머리가",
    "도구·요령 불만(냄새·건조기·거름망)": r"냄새|건조|거름망|배수구|먼지|물통|밥솥",
}
for k, p in sub2.items():
    c = [r for r in home if re.search(p, r["title"] + r["excerpt"] + r["pain_summary"])]
    say(f"  {k}: {len(c)}")
say("  연도 분포: " + str(collections.Counter(r["posted_date"][:4] for r in home).most_common()))
say("  사이트 분포: " + str(collections.Counter(r["site"] for r in home).most_common()))
viewed = sorted([r for r in home if r["views"].isdigit()], key=lambda r: -int(r["views"]))[:8]
say("  조회수 상위")
for r in viewed:
    say(f"    · [{r['site']} {r['posted_date'][:4]}] 조회 {r['views']} 댓글 {r['comments']} | {r['pain_summary']}")

# ---------------- 심사 후기에서 규제·생활 앱 언급 ----------------
say("\n\n# 후기 214건에서 규제·의료·생활 앱 언급")
rv = load("modoo_yechang_reviews.csv")


def rv_text(r: dict) -> str:
    return " ".join(r[k] for k in ("item_summary", "judge_questions", "scoring_points", "advice"))


for k, p in {
    "의료·헬스케어·병원·약": r"의료|헬스|병원|약국|처방|복약|환자",
    "규제·법률·인허가": r"규제|법률|인허가|허가|법적|의료법|식약처",
    "가사·가족·커플·육아 생활 앱": r"가사|집안일|가족|커플|부부|육아|맘",
    "플랫폼·양면시장 질문(공급자 모집)": r"공급자|양면|플랫폼|제보|콜드스타트|초기 데이터",
}.items():
    hit = [r for r in rv if re.search(p, rv_text(r))]
    say(f"\n## {k}: {len(hit)}건")
    for r in hit[:8]:
        say(f"  · [{r['program']} {r['year']} {r['outcome']}] {r['item_summary'][:60]} | Q: {r['judge_questions'][:90]} | 조언: {r['advice'][:80]}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
print(f"\n-> {OUT}")
