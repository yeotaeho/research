# 분야별 앱과 평점 수집기 — 스토어 검색으로 앱을 찾아 평점·평가 수·설치 수·1·2점 비율을 표로 만든다
"""
실행: uv run --no-project --with requests --with google-play-scraper python -X utf8 collect_wide_apps.py
산출: research/apps_by_field.csv. iTunes Search API 는 분당 약 20회 제한이라 3.2초 간격으로 부른다.
기존 49개 앱은 평점 칸이 없었으므로 collect_low_reviews.APPS 를 그대로 상세 조회해 같은 표에 넣는다.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from google_play_scraper import app as play_app, search as play_search
from google_play_scraper.exceptions import NotFoundError

from collect_low_reviews import APPS

OUT = Path(__file__).resolve().parents[1] / "apps_by_field.csv"
COLS = "field,platform,app_name,developer,app_id,store_url,rating,ratings_count,low_share_pct,installs,price,iap,released,updated,source".split(",")

TERMS = {
    "보험·실손 청구": ["실손보험 청구", "보험금 청구", "보험 분석"],
    "세금·연말정산": ["세금 환급", "종합소득세", "연말정산"],
    "취업·이직·직장": ["채용", "이직", "자소서"],
    "임금·프리랜서 정산": ["급여 계산", "알바 근무 관리", "프리랜서 정산"],
    "부모님·노인 돌봄": ["요양", "부모님 돌봄", "치매"],
    "반려동물": ["동물병원", "펫보험", "강아지 산책"],
    "자동차·정비": ["자동차 정비", "내차 관리", "중고차"],
    "여행·숙박·항공": ["여행 일정", "항공권", "숙소 예약"],
    "결혼·웨딩": ["결혼 준비", "웨딩", "모바일 청첩장"],
    "임신·출산·난임": ["임신", "난임", "출산 준비"],
    "미용·피부·외모": ["미용실 예약", "피부과 시술", "탈모"],
    "집수리·설비·가전": ["집수리", "인테리어", "가전 청소"],
    "통신·인터넷·렌탈": ["알뜰폰", "인터넷 가입", "렌탈"],
    "지원금·복지 신청": ["정부 지원금", "숨은 돈 찾기", "복지"],
    "입시·학원·학부모": ["입시", "학원 관리", "학부모"],
    "정신건강·외로움": ["심리상담", "우울", "마음 건강"],
    "임대차·이웃 분쟁": ["전월세", "부동산 계약", "층간소음"],
    "연애·소개팅": ["소개팅", "결혼정보", "데이팅"],
    "가족·명절·시댁": ["가족 일정", "가족 앨범", "커플"],
    "디지털·계정·피싱": ["사진 정리", "스팸 차단", "보이스피싱"],
    "중고거래·사기": ["중고거래", "사기 조회", "안전거래"],
    "자영업·소상공인": ["사장님", "매장 관리", "직원 관리"],
    "식재료·냉장고": ["냉장고 관리", "유통기한", "식재료 관리"],
    "옷·패션": ["옷장 관리", "코디", "의류 수거"],
    "장례·상속": ["상속", "장례", "상조"],
    "이용권 중도 환불": ["헬스장", "회원권 양도", "운동 예약"],
    "공연·티켓팅": ["티켓 예매", "콘서트", "티켓 양도"],
    "소액 분쟁·내용증명": ["법률 상담", "내용증명", "차용증"],
}
KEEP_PER_STORE = 12


def itunes(term):
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode({"term": term, "country": "kr", "entity": "software", "limit": 25})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)["results"]
        except OSError as e:
            print(f"  itunes {term}: {e}", file=sys.stderr, flush=True)
            time.sleep(30)
    return []


def ios_row(field, r, source):
    return {
        "field": field, "platform": "ios", "app_name": r["trackName"], "developer": r.get("sellerName", ""),
        "app_id": str(r["trackId"]), "store_url": f"https://apps.apple.com/kr/app/id{r['trackId']}",
        "rating": round(r.get("averageUserRating", 0), 2), "ratings_count": r.get("userRatingCount", 0),
        "low_share_pct": "", "installs": "", "price": r.get("formattedPrice", ""), "iap": "",
        "released": r.get("releaseDate", "")[:10], "updated": r.get("currentVersionReleaseDate", "")[:10], "source": source,
    }


def play_row(field, pkg, source):
    try:
        d = play_app(pkg, lang="ko", country="kr")
    except (NotFoundError, Exception) as e:  # noqa: BLE001
        print(f"  play {pkg}: {type(e).__name__}", file=sys.stderr, flush=True)
        return None
    hist = d.get("histogram") or [0] * 5
    total = sum(hist)
    return {
        "field": field, "platform": "android", "app_name": d["title"], "developer": d.get("developer", ""),
        "app_id": pkg, "store_url": f"https://play.google.com/store/apps/details?id={pkg}&hl=ko&gl=kr",
        "rating": round(d.get("score") or 0, 2), "ratings_count": d.get("ratings") or 0,
        "low_share_pct": round(100 * (hist[0] + hist[1]) / total, 1) if total else "",
        "installs": d.get("installs") or "", "price": d.get("price") or 0, "iap": d.get("inAppProductPrice") or "",
        "released": d.get("released") or "", "updated": time.strftime("%Y-%m-%d", time.gmtime(d["updated"])) if d.get("updated") else "", "source": source,
    }


def main():
    rows = []
    # 기존 49개 앱. iOS 는 trackId 로 lookup 한다
    for cat, name, track, pkg in APPS:
        if track:
            with urllib.request.urlopen(f"https://itunes.apple.com/lookup?id={track}&country=kr", timeout=30) as resp:
                got = json.load(resp)["results"]
            if got:
                rows.append(ios_row(cat, got[0], "기존 49개"))
            time.sleep(3.2)
        if pkg:
            row = play_row(cat, pkg, "기존 49개")
            if row:
                rows.append(row)
        print(f"기존 {name}", file=sys.stderr, flush=True)

    for field, terms in TERMS.items():
        ios, pkgs = {}, {}
        for term in terms:
            for r in itunes(term):
                ios.setdefault(r["trackId"], (r, term))
            time.sleep(3.2)
            try:
                for h in play_search(term, lang="ko", country="kr", n_hits=30):
                    if h.get("appId"):
                        pkgs.setdefault(h["appId"], (h.get("ratings") or h.get("score") or 0, term))
            except Exception as e:  # noqa: BLE001
                print(f"  play search {term}: {type(e).__name__}", file=sys.stderr, flush=True)
        top_ios = sorted(ios.values(), key=lambda x: -x[0].get("userRatingCount", 0))[:KEEP_PER_STORE]
        rows += [ios_row(field, r, f"검색:{term}") for r, term in top_ios]
        play_rows = [play_row(field, p, f"검색:{term}") for p, (_, term) in list(pkgs.items())[:40]]
        play_rows = sorted((x for x in play_rows if x), key=lambda x: -x["ratings_count"])[:KEEP_PER_STORE]
        rows += play_rows
        print(f"{field}: ios {len(top_ios)} android {len(play_rows)}", file=sys.stderr, flush=True)

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)
    print(f"저장 {OUT} {len(rows)}행", file=sys.stderr)


if __name__ == "__main__":
    main()
