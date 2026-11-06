# 저평점 리뷰 결제 불만 분류기 — 단어 언급이 아니라 돈이 나간 일·환불·해지 불만만 세고 표본 정확도를 재는 데 쓴다
import csv
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECENT_FROM = "2024-11"  # 최근 24개월

_PAY = r"(결제|결재|과금|청구)"
_PAID = r"((결제|결재|과금|청구)\s*(가|이)?\s*(되|됐|됨|돼|됬|나갔|나감|했네)|빠져\s*나|인출|돈\s*(이\s*)?나[가갔]|뜯어|빼\s*가)"
THEMES = {
    "무료체험 뒤 유료 전환": re.compile(
        rf"(무료\s*체험|체험|무료\s*(기간|이용|사용)|\d+\s*일\s*무료).{{0,50}}{_PAID}|{_PAID}.{{0,50}}(무료\s*체험|체험\s*(기간|이|끝|후)|무료\s*기간)"
    ),
    "모르는 사이 결제·자동 갱신": re.compile(
        rf"자동\s*(결제|결재|갱신|과금|연장|구독)|정기\s*(결제|결재).{{0,30}}(몰랐|모르|되어|됐|돼|됨)|"
        rf"(모르게|몰랐|모르고|모르는).{{0,30}}{_PAID}|{_PAID}.{{0,30}}(몰랐|모르게|기억.{{0,6}}없)|"
        rf"(알림|안내|고지|문자|메일).{{0,12}}없.{{0,30}}{_PAID}|{_PAID}.{{0,30}}(알림|안내|고지|문자|메일).{{0,12}}없|"
        rf"갑자기.{{0,16}}{_PAID}|저절로.{{0,20}}{_PAY}|(맘대로|마음대로|지맘대로).{{0,16}}{_PAY}|사용\s*(안|하지\s*않).{{0,30}}{_PAID}"
    ),
    "해지·취소가 어렵거나 해지 뒤 결제": re.compile(
        rf"(해지|구독\s*취소|구독취소|구독\s*해제|탈퇴).{{0,30}}(못|안\s*되|안되|없|어렵|복잡|찾|번거|방법|어디|모르)|"
        rf"(해지|구독\s*취소|구독취소|취소|끊었).{{0,24}}(했|한지|했는데|했음|했더니|오래).{{0,50}}{_PAID}"
    ),
    "환불·결제 취소 요청": re.compile(r"환불|(결제|결재|구독|자동결제).{0,14}취소.{0,8}(해\s*주|부탁|요청|바랍|해줘)|취소\s*(부탁|요청)"),
    "결제했는데 반영 안 됨": re.compile(r"(결제|결재|구독|구매).{0,30}(반영|복원|적용).{0,12}(안|못)|유료\s*기능\s*(이\s*)?해제"),
    "결제 유도·잘못 누름": re.compile(
        rf"(잠결|비몽사몽|실수로|잘못\s*눌|모르고\s*눌).{{0,40}}{_PAY}|{_PAY}.{{0,40}}(유도|실수로|잘못\s*눌)|(유도|유료\s*유도).{{0,6}}(심|많|너무|계속)"
    ),
    "가격을 잘못 알고 결제": re.compile(
        rf"(인줄|줄\s*알).{{0,40}}{_PAID}|{_PAID}.{{0,40}}(인줄|줄\s*알았)|(주당|일주일에|매주|한\s*달|월).{{0,24}}(인줄|줄\s*알)|할인.{{0,30}}{_PAID}.{{0,20}}(넘|더|비싸|다른)"
    ),
}
REFUND_DENIED = re.compile(r"환불.{0,40}(무응답|응답|답변|답장|답이|연락|거절|거부|안\s*해|안해|안\s*돼|안돼|안\s*됨|안됨|불가|처리\s*안|못\s*받|안\s*되|안되)")


def text_of(r: dict) -> str:
    return (r["title"] + " " + r["body"]).replace("\n", " ").strip()


def classify(text: str) -> list[str]:
    return [name for name, rx in THEMES.items() if rx.search(text)]


def load_reviews() -> list[dict]:
    with (ROOT / "appstore_low_reviews.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# 최근 2년 저평점에서 결제 불만 비율이 높은 순으로 고르고 보내는 순서로 둔다. 한국 팀이 먼저, 해외 본사(Sleep Cycle)는 끝이다
TARGETS = ["Renight(미라클나잇)", "인아웃", "마이루틴", "플랜핏", "클래스101", "알라미", "스픽", "모두의주차장", "미소", "Sleep Cycle"]

if __name__ == "__main__":
    # 정확도 표본. 사람이 읽고 세므로 결과를 파일에 남기지 않는다
    sys.stdout.reconfigure(encoding="utf-8")
    assert classify("7일 무료체험 끝나고 알림 없이 결제됐어요")
    assert "해지·취소가 어렵거나 해지 뒤 결제" in classify("구독 취소했는데 또 결제됨")
    assert "해지·취소가 어렵거나 해지 뒤 결제" in classify("구독취소 하고싶은데 방법을 모르겠네요")
    assert "환불·결제 취소 요청" in classify("결제 취소해주세요")
    assert not classify("유료결재를 해야 알림 오나요")
    assert not classify("결국엔 또 다 유료네요")
    assert not classify("유료로 쓰는데 앱이 자꾸 튕겨요 오류 고쳐주세요")
    assert not classify("업데이트 후 동기화가 안 돼요")
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 29
    rows = [r for r in load_reviews() if r["app_name"] in TARGETS]
    hit = [r for r in rows if classify(text_of(r))]
    miss = [r for r in rows if not classify(text_of(r)) and re.search(r"구독|결제|결재|유료|멤버십|해지", text_of(r))]
    print(f"대상 {len(rows)} 분류됨 {len(hit)} 단어만 있고 제외 {len(miss)}")
    random.seed(seed)
    print("\n-- 분류됨 표본 40 (이 중 돈·환불·해지 불만이 아닌 것을 센다)")
    for i, r in enumerate(random.sample(hit, 40), 1):
        print(f"{i:2}. [{r['app_name'][:6]}] {','.join(t[:5] for t in classify(text_of(r)))} | {text_of(r)[:92]}")
    print("\n-- 제외 표본 30 (이 중 돈·환불·해지 불만인데 놓친 것을 센다)")
    for i, r in enumerate(random.sample(miss, 30), 1):
        print(f"{i:2}. [{r['app_name'][:6]}] {text_of(r)[:92]}")
