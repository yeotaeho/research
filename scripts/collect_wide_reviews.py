# 넓힌 분야 핵심 앱의 1·2점 리뷰 수집기 — 검색 잡음을 손으로 걷어 낸 CORE 목록만 기존과 같은 방식으로 받는다
"""
실행: uv run --no-project --with requests --with google-play-scraper python -X utf8 collect_wide_reviews.py
입력: research/apps_by_field.csv. 산출: research/appstore_low_reviews_wide.csv (컬럼은 appstore_low_reviews.csv 와 같다).
CORE 는 스토어 검색 결과에서 게임·해외 전용·무관한 앱을 뺀 분야별 한국 앱이다. 판단은 내가 앱 이름과 제작사를 보고 했다.
"""
import csv
import sys
from pathlib import Path

from collect_low_reviews import COLUMNS, MIN_BODY, android_reviews, failures, ios_reviews

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "appstore_low_reviews_wide.csv"

CORE = {
    "보험·실손 청구": ["청구의신", "굿리치", "보닥", "시그널플래너", "라이프캐치", "메디패스", "건강보험25시", "DB손해보험"],
    "세금·연말정산": ["삼쩜삼", "손택스", "쌤157", "스마트 위택스", "비즈넵", "덧셈"],
    "취업·이직·직장": ["사람인", "잡코리아", "리멤버", "블라인드"],
    "임금·프리랜서 정산": ["하우머치", "기그 - 알바앱", "Tica", "오늘근무", "월급계산기", "크몽", "알바몬"],
    "부모님·노인 돌봄": ["케어네이션", "케어닥", "스마트장기요양", "치매체크"],
    "반려동물": ["어바웃펫", "와요 펫시터", "펫피"],
    "자동차·정비": ["마이클", "카닥", "엔카", "헤이딜러", "첫차"],
    "여행·숙박·항공": ["NOL", "여기어때", "아고다", "스카이스캐너", "Trip.com"],
    "결혼·웨딩": ["웨딩북", "아이웨딩"],
    "임신·출산·난임": ["핑크다이어리", "봄 캘린더", "해피문데이"],
    "미용·피부·외모": ["화해", "강남언니", "캐시닥", "마메드네"],
    "집수리·설비·가전": ["오늘의집", "숨고", "모두연결"],
    "통신·인터넷·렌탈": ["U+one", "T world", "PASS by KT"],
    "지원금·복지 신청": ["복지로", "어카운트인포", "정부24"],
    "입시·학원·학부모": ["하이클래스", "통통통", "학원친구", "진학닷컴", "EBSi", "런즈", "매쓰플랫"],
    "정신건강·외로움": ["마인드카페", "하루콩", "무디 Moodee"],
    "임대차·이웃 분쟁": ["직방", "다방", "호갱노노", "피터팬", "자리톡", "삼삼엠투"],
    "연애·소개팅": ["Tinder", "정오의데이트", "글램", "위피", "심쿵", "브릿지"],
    "가족·명절·시댁": ["비트윈", "썸원", "TimeTree", "FamilyAlbum"],
    "디지털·계정·피싱": ["후후", "후스콜", "알약", "정리: 휴대폰"],
    "중고거래·사기": ["당근", "번개장터", "중고나라", "헬로마켓"],
    "자영업·소상공인": ["배민사장님", "쿠팡이츠 사장님", "요기요 사장님", "캐시노트", "오늘얼마", "시프티", "기그 사장님"],
    "식재료·냉장고": ["BEEP", "원더 프리지", "냉장고 파먹기", "냉장고파먹기", "유통기한 언제지", "거꾸로레시피", "요리백과", "유통기한 관리"],
    "옷·패션": ["에이클로젯", "룩핀", "빼기", "지그재그"],
    "장례·상속": ["모바일 부고장", "경조사 다이어리", "안심상속"],
    "이용권 중도 환불": ["다짐", "운동닥터", "니짐내짐"],
    "공연·티켓팅": ["NOL", "위버스"],
    "소액 분쟁·내용증명": ["로톡", "전자소송포털", "우체국", "생활법률", "시대문서"],
}


def core_rows():
    """apps_by_field.csv 에서 CORE 에 든 앱 행을 돌려준다. 같은 분야·스토어·ID 는 한 번만."""
    seen, out = set(), []
    for r in csv.DictReader((ROOT / "apps_by_field.csv").open(encoding="utf-8-sig")):
        names = CORE.get(r["field"])
        if not names or not any(n in r["app_name"] for n in names):
            continue
        key = (r["field"], r["platform"], r["app_id"])
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def main():
    old = {(r["platform"], r["app_id"]) for r in csv.DictReader((ROOT / "appstore_low_reviews.csv").open(encoding="utf-8-sig"))}
    done, rows = set(), []
    for r in core_rows():
        key = (r["platform"], r["app_id"])
        if key in old or key in done:
            continue
        done.add(key)
        name = r["app_name"].split(" - ")[0].split(" | ")[0].strip()[:30]
        got = ios_reviews(r["field"], name, int(r["app_id"])) if r["platform"] == "ios" else android_reviews(r["field"], name, r["app_id"])
        print(f"{r['platform']:8}{r['field']:16}{name:<30}{len(got):>5}", file=sys.stderr, flush=True)
        rows += got
    seen, out = set(), []
    for r in rows:
        key = (r["platform"], r["review_id"])
        if key in seen or len(r["body"]) < MIN_BODY or r["rating"] not in (1, 2):
            continue
        seen.add(key)
        out.append(r)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(out)
    print(f"저장 {OUT} {len(out)}행, 앱 {len(done)}개, 실패 {failures}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
