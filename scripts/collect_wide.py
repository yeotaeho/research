# 넓힌 분야 커뮤니티 수집기 — collect_complaints 의 사이트 파서를 재사용해 새 분야를 돌리고, 네이버 카페 검색을 더한다
"""
실행:
  uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml python -X utf8 collect_wide.py [--limit N] [--sites a,b]
산출: research/work/wide/raw_<사이트>.jsonl (필터 통과 후보).
기존 12개 분야는 예전 덤프(work/community_raw.jsonl)에 있으므로 새로 도는 것은 네이버 카페뿐이다. 비교할 때 같은 사이트 묶음으로 맞추기 위해서다.
"""
import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup

from collect_complaints import (
    CATEGORIES as OLD_FIELDS, EMOTIONS, Clien, Cook82, Dcinside, NaverBase, NaverKin, Pann, Ppomppu,
    clean, norm_date, relevant,
)

OUT = Path(__file__).resolve().parents[1] / "work" / "wide"

# 분야 → (검색어 토픽, 관련어). 관련어는 결과 필터에만 쓴다.
NEW_FIELDS = {
    "보험·실손 청구": (["실비 청구", "보험금 청구", "보험 해지", "보험 설계사"], ["실손", "실비", "보험금", "보험사", "설계사", "보장", "특약", "부지급", "청구"]),
    "세금·연말정산": (["연말정산", "종합소득세", "세금 신고", "세금 환급"], ["홈택스", "세무사", "3.3", "부가세", "소득공제", "원천징수", "삼쩜삼", "세금"]),
    "취업·이직·직장": (["이직 준비", "자소서", "면접", "퇴사"], ["취준", "취업", "이력서", "채용", "야근", "연차", "상사", "회사", "직장", "경력기술서", "공고"]),
    "임금·프리랜서 정산": (["임금체불", "주휴수당", "프리랜서 정산", "알바"], ["월급", "퇴직금", "근로계약", "외주", "미수금", "대금", "급여", "사장", "노동청"]),
    "부모님·노인 돌봄": (["부모님 병원", "요양원", "치매", "요양보호사"], ["노인", "어머니", "아버지", "엄마", "아빠", "간병", "장기요양", "등급", "간병인", "주간보호", "부모님"]),
    "반려동물": (["동물병원", "강아지 산책", "펫보험", "고양이 화장실"], ["반려", "강아지", "고양이", "진료비", "미용", "사료", "배변", "털", "펫시터", "장례"]),
    "자동차·정비": (["자동차 정비", "자동차 보험", "중고차", "세차"], ["정비소", "수리비", "바가지", "과태료", "범칙금", "타이어", "엔진오일", "접촉사고", "블랙박스", "공업사", "차"]),
    "여행·숙박·항공": (["여행 계획", "항공권 환불", "숙소 예약", "패키지 여행"], ["호텔", "수하물", "취소 수수료", "위약금", "항공사", "여행사", "환전", "캐리어", "일정", "여행"]),
    "결혼·웨딩": (["결혼 준비", "스드메", "예식장", "축의금"], ["웨딩", "혼수", "상견례", "신혼", "청첩장", "본식", "플래너", "하객", "답례", "결혼"]),
    "임신·출산·난임": (["난임", "산후조리원", "임신 중", "출산"], ["시험관", "임산부", "입덧", "조리원", "산후", "배란", "임신", "난임"]),
    "미용·피부·외모": (["피부과", "미용실", "탈모", "네일"], ["시술", "염색", "펌", "바가지", "리프팅", "여드름", "디자이너", "커트", "왁싱", "피부"]),
    "집수리·설비·가전": (["누수", "곰팡이", "인테리어 업체", "에어컨 청소"], ["보일러", "하자", "수리기사", "출장비", "AS", "철거", "도배", "장판", "결로", "수리", "고장"]),
    "통신·인터넷·렌탈": (["인터넷 해지", "통신사 위약금", "정수기 렌탈", "휴대폰 요금"], ["약정", "알뜰폰", "위약금", "렌탈", "공시지원금", "해지", "상담원", "요금제", "통신사"]),
    "지원금·복지 신청": (["정부 지원금", "청년 지원", "복지 신청", "실업급여"], ["신청", "자격", "수급", "청년도약", "월세 지원", "바우처", "국민연금", "건강보험료", "고용보험", "지원금"]),
    "입시·학원·학부모": (["학원비", "학원 상담", "입시 정보", "학교 준비물"], ["수능", "수시", "내신", "과외", "학부모", "담임", "초등", "중등", "고등", "학원", "입시"]),
    "정신건강·외로움": (["우울", "정신과", "심리상담", "외로움"], ["공황", "상담 비용", "불안", "부작용", "무기력", "번아웃", "친구", "고립", "상담"]),
    "임대차·이웃 분쟁": (["전세 보증금", "집주인 수리", "층간소음", "부동산 중개"], ["복비", "갱신", "보증보험", "임대인", "임차인", "퇴거", "역전세", "집주인", "윗집", "옆집", "보증금"]),
    "연애·소개팅": (["소개팅", "결혼정보회사", "데이팅앱", "소개팅앱"], ["듀오", "가연", "틴더", "연애", "매칭", "소개", "소개팅"]),
    "가족·명절·시댁": (["명절", "시댁", "부부 싸움", "친정"], ["시어머니", "제사", "차례", "며느리", "처가", "남편", "아내", "시부모", "시댁"]),
    "디지털·계정·피싱": (["비밀번호 분실", "스팸 문자", "보이스피싱", "사진 정리"], ["저장공간", "휴대폰 교체", "데이터 옮기", "피싱", "스미싱", "개인정보", "해킹", "클라우드", "도용", "스팸", "비밀번호"]),
    "중고거래·사기": (["중고거래 사기", "당근 노쇼", "번개장터 환불", "중고나라"], ["당근", "번개장터", "사기", "노쇼", "직거래", "택배거래", "더치트", "중고"]),
    "자영업·소상공인": (["배달앱 수수료", "자영업 세금", "가게 알바", "매장 운영"], ["사장", "매장", "가게", "수수료", "임대료", "포스", "재고", "폐업", "직원", "자영업", "손님"]),
    "식재료·냉장고": (["냉장고 정리", "유통기한", "음식물 쓰레기", "식재료 버림"], ["식재료", "냉장고", "썩", "소비기한", "버리", "상해", "유통기한"]),
    "옷·패션": (["옷 사이즈", "옷 정리", "옷 수선", "의류 수거"], ["코디", "옷장", "수선", "드라이", "사이즈", "입을 옷", "옷"]),
    "장례·상속": (["장례 절차", "상속 절차", "사망 후 서류", "상조"], ["유품", "사망신고", "상속세", "상속 포기", "납골", "화장", "장례", "상속"]),
    "이용권 중도 환불": (["헬스장 환불", "PT 환불", "필라테스 환불", "학원 환불"], ["중도 해지", "위약금", "회원권", "양도", "폐업", "먹튀", "환불"]),
    "공연·티켓팅": (["티켓팅", "암표", "콘서트 예매", "취소표"], ["피켓팅", "매크로", "예매", "콘서트", "티켓"]),
    "소액 분쟁·내용증명": (["내용증명", "소액소송", "지급명령", "돈 안 갚"], ["소송", "변호사", "고소", "채무", "차용증", "받을 돈", "법무사"]),
}


class NaverCafe(NaverBase):
    name = "naver_cafe"

    def search(self, q, page):
        r = self.get(f"https://search.naver.com/search.naver?ssc=tab.cafe.all&query={quote(q)}&start={(page - 1) * 10 + 1}")
        out = []
        for li in BeautifulSoup(r.text, "lxml").select("ul.lst_view li.bx") if r else []:
            a = li.select_one("a.title_link")
            if not a or "cafe.naver.com" not in a.get("href", ""):
                continue
            cafe = li.select_one("a.name")
            date = li.select_one("span.sub")
            body = li.select_one("a.dsc_link") or li.select_one("div.dsc_wrap")
            out.append({
                "board": clean(cafe.get_text(" ", strip=True) if cafe else "", 40), "title": a.get_text(" ", strip=True),
                "url": a["href"].split("?")[0], "posted_date": norm_date(date.get_text() if date else ""),
                "views": "", "comments": "", "likes": "", "snippet": clean(body.get_text(" ") if body else ""),
            })
        return out


SITES = {c.name: c for c in (Clien, Ppomppu, Dcinside, Pann, Cook82, NaverKin, NaverCafe)}


def run_site(cls, fields, seen, lock, limit, emotions=EMOTIONS, delay=1, pages=None):
    site = cls()
    path = OUT / f"raw_{site.name}.jsonl"
    done = kept = 0
    with path.open("w", encoding="utf-8") as fp:
        for field, (topics, related) in fields.items():
            for topic in topics:
                for emo in emotions:
                    for page in range(1, (pages or site.pages) + 1):
                        done += 1
                        if limit and done > limit:
                            print(f"[{site.name}] 제한 도달 후보 {kept} 오류 {site.errors[:3]}", file=sys.stderr, flush=True)
                            return
                        time.sleep(delay)
                        before = len(site.errors)
                        try:
                            items = site.search(f"{topic} {emo}", page)
                            if not items and len(site.errors) > before and "403" in site.errors[-1]:
                                # 네이버는 초당 2회쯤에서 수백 건 뒤 403 을 준다(11/5 실측). 쉬었다 한 번 더 시도한다
                                print(f"[{site.name}] 403, 3분 쉼. {field}", file=sys.stderr, flush=True)
                                time.sleep(180)
                                items = site.search(f"{topic} {emo}", page)
                        except Exception as e:  # noqa: BLE001
                            site.errors.append(f"parse {type(e).__name__}: {str(e)[:60]}")
                            items = []
                        for it in items:
                            with lock:
                                if it["url"] in seen:
                                    continue
                                seen.add(it["url"])
                            text = it["title"] + " " + it["snippet"]
                            kw = relevant(text, topics, related)
                            if not kw and site.body_sel and topic.split()[0] in it["title"]:
                                it["snippet"] = site.body(it["url"])
                                kw = relevant(it["title"] + " " + it["snippet"], topics, related)
                            if not kw:
                                continue
                            kept += 1
                            fp.write(json.dumps({"site": site.name, "category": field, "matched_keyword": kw, "query": f"{topic} {emo}", **it}, ensure_ascii=False) + "\n")
                            fp.flush()
    print(f"[{site.name}] 요청 {done} 후보 {kept} 오류 {len(site.errors)} {site.errors[:3]}", file=sys.stderr, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sites", default=",".join(SITES))
    ap.add_argument("--naver", action="store_true", help="카페·지식iN 만 40개 분야를 천천히 다시 돈다. 분야 간 요청 수를 같게 맞춘다")
    args = ap.parse_args()
    if args.naver:
        seen, lock = set(), threading.Lock()
        for name in ("naver_cafe", "naver_kin"):
            run_site(SITES[name], {**OLD_FIELDS, **NEW_FIELDS}, seen, lock, args.limit, emotions=["불편", "스트레스"], delay=2, pages=1)
        return
    seen, lock = set(), threading.Lock()
    with ThreadPoolExecutor(max_workers=len(SITES)) as ex:
        futs = []
        for name in args.sites.split(","):
            fields = {**OLD_FIELDS, **NEW_FIELDS} if name == "naver_cafe" else NEW_FIELDS
            futs.append(ex.submit(run_site, SITES[name], fields, seen, lock, args.limit))
        for f in futs:
            f.result()


if __name__ == "__main__":
    main()
