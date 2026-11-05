# 커뮤니티 생활 불편 글 수집기 — 사이트별 검색 페이지를 분야×감정 키워드로 돌려 CSV 로 만든다
"""
실행:
  uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml \
    python research/scripts/collect_complaints.py [--raw raw.jsonl] [--only-summarized] [--sites clien,dcinside]
  ... --from-raw raw.jsonl --only-summarized      # 수집 없이 덤프에서 CSV 만 다시 만들기

pain_summary 는 사람이 검토해 쓴 research/scripts/pain_summaries.json (url → {pain_summary, category}) 에서 붙인다.
--only-summarized 를 주면 요약이 있는 행만 CSV 에 남긴다 (최종본). 그 뒤 fill_details.py 로 네이버 날짜·뽐뿌/82cook 본문을 채운다.
"""
import argparse
import csv
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests

HERE = Path(__file__).parent
OUT_CSV = HERE.parent / "community_complaints.csv"
SUMMARIES = HERE / "pain_summaries.json"
COLS = "site,board,category,title,url,posted_date,views,comments,likes,excerpt,pain_summary,matched_keyword".split(",")

# 분야 → (검색어 토픽, 관련어). 관련어는 결과 필터에만 쓴다.
CATEGORIES = {
    "출퇴근·이동": (["출근길", "지하철", "버스", "주차"], ["출퇴근", "퇴근", "통근", "환승", "배차", "택시", "운전", "교통", "정체", "만원"]),
    "집안일·청소·세탁": (["집안일", "청소", "빨래", "설거지"], ["세탁", "건조기", "분리수거", "쓰레기", "음식물", "걸레", "화장실 청소", "정리"]),
    "식사·요리·장보기": (["요리", "장보기", "식사 준비", "반찬"], ["메뉴", "식재료", "마트", "끼니", "밥 해", "저녁 메뉴", "도시락", "식단", "배달"]),
    "육아": (["육아", "등원", "어린이집", "아기"], ["아이", "등하원", "유치원", "돌봄", "워킹맘", "독박", "이유식", "기저귀", "학원"]),
    "건강·운동·수면": (["운동", "수면", "불면", "피로"], ["잠", "헬스", "다이어트", "두통", "거북목", "허리", "피곤", "체력", "수면 부족"]),
    "돈관리·공과금·구독": (["공과금", "구독 해지", "가계부", "관리비"], ["구독", "자동결제", "카드값", "통신비", "보험료", "고지서", "납부", "요금"]),
    "병원·약·예약": (["병원 예약", "병원 대기", "약 복용", "처방"], ["병원", "약국", "진료", "대기", "접수", "처방전", "약 챙", "진료 예약", "검진"]),
    "행정·서류·민원": (["주민센터", "서류 발급", "공인인증서", "민원"], ["등본", "인증서", "정부24", "행정", "서류", "신분증", "본인인증", "관공서", "서류 떼"]),
    "쇼핑·배송·반품": (["택배", "반품", "배송", "교환"], ["환불", "배송조회", "택배기사", "부재", "경비실", "택배함", "오배송", "포장"]),
    "공부·자기계발·집중": (["공부 집중", "자기계발", "독서 습관", "인강"], ["집중", "작심삼일", "미루", "공부", "영어 공부", "자격증", "습관", "딴짓"]),
    "인간관계·모임·일정조율": (["약속 잡기", "모임", "단톡방", "일정 조율"], ["약속", "경조사", "축의금", "연락", "카톡", "답장", "시간 맞추", "동창회", "회식"]),
    "1인가구·주거·이사": (["자취", "이사", "월세", "혼자 살"], ["1인가구", "원룸", "집주인", "전세", "관리실", "층간소음", "집 구하", "부동산", "짐"]),
}
EMOTIONS = ["불편", "귀찮", "스트레스", "매번"]  # 검색어에 붙이는 감정 키워드 (요청 간 1초라 네 개로 줄였다)
COMPLAINT_RE = re.compile("불편|짜증|귀찮|번거|스트레스|매번|왜 이렇게|힘들|개선|피곤|지겹|고통|힘드|귓찬|빡치|열받")
EXCLUDE_RE = re.compile(
    "불편한 편의점|불편 한 편의점|광고|협찬|이벤트|할인|쿠폰|\\[속보\\]|단독\\]|기사|뉴스|리뷰|후기|추천템|내돈내산|체험단|분양|공지|"
    "대통령|국회|의원|정당|민주당|국힘|선거|북한|트럼프|주식|코인|성경|기도|교회"
)
TODAY = date.today()


def norm_date(s):
    s = (s or "").strip()
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        return f"{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.search(r"(\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        return f"20{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}"
    m = re.search(r"(\d+)\s*(분|시간|일|주|개월|년)\s*전", s)
    if m:
        n = int(m[1])
        days = {"분": 0, "시간": 0, "일": n, "주": 7 * n, "개월": 30 * n, "년": 365 * n}[m[2]]
        return (TODAY - timedelta(days=days)).isoformat()
    if re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", s) or s in ("어제", "오늘"):
        return (TODAY - timedelta(days=1 if s == "어제" else 0)).isoformat()
    return ""


def num(s):
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*([kK만])?", s or "")
    if not m:
        return ""
    n = float(m[1].replace(",", ""))
    return str(int(n * {"k": 1000, "K": 1000, "만": 10000}.get(m[2], 1)))


def clean(s, n=300):
    return re.sub(r"\s+", " ", (s or "")).strip()[:n]


class Site:
    name = ""
    page_param = None
    pages = 1
    body_sel = None  # 검색 결과에 스니펫이 없으면 본문을 한 번 더 받는다
    body_cap = 80

    def __init__(self):
        self.s = requests.Session(impersonate="chrome124")
        self.s.headers.update({"Accept-Language": "ko-KR,ko;q=0.9", "Referer": "https://www.google.com/"})
        self.errors = []
        self.bodies = 0

    def get(self, url):
        for attempt in range(3):
            try:
                r = self.s.get(url, timeout=25)
            except Exception as e:  # noqa: BLE001
                self.errors.append(f"{type(e).__name__}: {str(e)[:60]}")
                time.sleep(2)
                continue
            if r.status_code == 429:
                time.sleep(30)
                continue
            if r.status_code != 200:
                self.errors.append(f"HTTP {r.status_code} {url[:80]}")
                return None
            return r
        self.errors.append(f"포기 {url[:80]}")
        return None

    def search(self, q, page):  # -> list[dict]
        raise NotImplementedError

    def body(self, url):
        if not self.body_sel or self.bodies >= self.body_cap:
            return ""
        self.bodies += 1
        time.sleep(1)
        r = self.get(url)
        if not r:
            return ""
        el = BeautifulSoup(r.text, "lxml").select_one(self.body_sel)
        return clean(el.get_text(" ") if el else "", 300)


class Clien(Site):
    name = "clien"

    def search(self, q, page):
        r = self.get(f"https://www.clien.net/service/search?q={quote(q)}&sort=recency&boardCd=park&p={page - 1}")
        out = []
        for it in BeautifulSoup(r.text, "lxml").select("div.list_item") if r else []:
            a = it.select_one("a.subject_fixed")
            if not a:
                continue
            ts = it.select_one("span.timestamp")
            out.append({
                "board": "모두의공원", "title": a.get("title") or a.get_text(strip=True),
                "url": "https://www.clien.net" + a["href"].split("?")[0],
                "posted_date": norm_date(ts.get_text() if ts else ""),
                "views": num(it.select_one("span.hit").get_text() if it.select_one("span.hit") else ""),
                "comments": it.get("data-comment-count", ""), "likes": num(it.select_one("div.list_symph").get_text()),
                "snippet": clean(it.select_one("div.preview").get_text() if it.select_one("div.preview") else ""),
            })
        return out


class Ppomppu(Site):
    name = "ppomppu"
    body_sel = "td.board-contents"

    def search(self, q, page):
        r = self.get(f"https://www.ppomppu.co.kr/zboard/zboard.php?id=freeboard&search_type=sub_memo&keyword={quote(q)}&page={page}")
        out = []
        for tr in BeautifulSoup(r.text, "lxml").select("tr.baseList") if r else []:
            a = tr.select_one("a.baseList-title")
            no = re.search(r"no=(\d+)", a["href"]) if a else None
            if not no:
                continue
            t = tr.select_one("time.baseList-time")
            out.append({
                "board": "자유게시판", "title": a.get_text(strip=True),
                "url": f"https://www.ppomppu.co.kr/zboard/view.php?id=freeboard&no={no[1]}",
                "posted_date": norm_date(t.get("title") if t else ""),
                "views": num(tr.select_one("td.baseList-views").get_text()),
                "comments": num(tr.select_one("span.baseList-c").get_text() if tr.select_one("span.baseList-c") else ""),
                "likes": num(tr.select_one("td.baseList-rec").get_text()), "snippet": "",
            })
        return out


class Fmkorea(Site):
    name = "fmkorea"
    pages = 2

    def search(self, q, page):
        r = self.get(f"https://www.fmkorea.com/index.php?act=IS&is_keyword={quote(q)}&mid=home&where=document&page={page}")
        out = []
        for a in BeautifulSoup(r.text, "lxml").select("li > dl > dt > a") if r else []:
            li = a.parent.parent.parent
            title = a.get_text(" ", strip=True)
            m = re.match(r"\[(.+?)\]\s*(.*)", title)
            out.append({
                "board": m[1] if m else "", "title": m[2] if m else title, "url": urljoin("https://www.fmkorea.com/", a["href"]),
                "posted_date": norm_date(li.select_one("span.time").get_text() if li.select_one("span.time") else ""),
                "views": "", "comments": num(li.select_one("span.reply").get_text() if li.select_one("span.reply") else ""),
                "likes": num(li.select_one("span.recomNum").get_text() if li.select_one("span.recomNum") else ""),
                "snippet": clean(li.select_one("dd").get_text(" ") if li.select_one("dd") else ""),
            })
        return out


class Dcinside(Site):
    name = "dcinside"

    def search(self, q, page):
        r = self.get(f"https://search.dcinside.com/post/p/{page}/sort/latest/q/{quote(q)}")
        out = []
        for li in BeautifulSoup(r.text, "lxml").select("ul.sch_result_list li") if r else []:
            a = li.select_one("a.tit_txt")
            if not a:
                continue
            dsc = li.select_one("p.link_dsc_txt:not(.dsc_sub)")
            out.append({
                "board": li.select_one("a.sub_txt").get_text(strip=True) if li.select_one("a.sub_txt") else "",
                "title": a.get_text(" ", strip=True), "url": a["href"],
                "posted_date": norm_date(li.select_one("span.date_time").get_text() if li.select_one("span.date_time") else ""),
                "views": "", "comments": "", "likes": "", "snippet": clean(dsc.get_text(" ") if dsc else ""),
            })
        return out


class Pann(Site):
    name = "pann"

    def search(self, q, page):
        r = self.get(f"https://pann.nate.com/search?q={quote(q)}&page={page}")
        out = []
        for li in BeautifulSoup(r.text, "lxml").select("li:has(> div.tit)") if r else []:
            a = li.select_one("a.subject")
            if not a:
                continue
            out.append({
                "board": li.select_one("span.part").get_text(strip=True) if li.select_one("span.part") else "톡톡",
                "title": a.get_text(" ", strip=True), "url": urljoin("https://pann.nate.com/", a["href"]),
                "posted_date": norm_date(li.select_one("span.date").get_text() if li.select_one("span.date") else ""),
                "views": "", "comments": num(li.select_one("span.reple-num").get_text() if li.select_one("span.reple-num") else ""),
                "likes": "", "snippet": clean(li.select_one("div.txt").get_text(" ") if li.select_one("div.txt") else ""),
            })
        return out


class Cook82(Site):
    name = "82cook"
    body_sel = "#articleBody"

    def search(self, q, page):
        r = self.get(f"https://www.82cook.com/entiz/enti.php?bn=15&searchType=search&search1=1&keys={quote(q)}&page={page}")
        out = []
        for tr in BeautifulSoup(r.text, "lxml").select("tr:not(.noticeList):has(td.regdate)") if r else []:
            a = tr.select_one("td.title a")
            n = re.search(r"num=(\d+)", a["href"]) if a else None
            if not n:
                continue
            nums = tr.select("td.numbers")
            em = tr.select_one("td.title em")
            out.append({
                "board": "자유게시판", "title": a.get_text(" ", strip=True),
                "url": f"https://www.82cook.com/entiz/read.php?bn=15&num={n[1]}",
                "posted_date": norm_date(tr.select_one("td.regdate").get("title", "")),
                "views": num(nums[-1].get_text()) if nums else "", "comments": num(em.get_text()) if em else "", "likes": "", "snippet": "",
            })
        return out


class NaverBase(Site):
    def __init__(self):
        super().__init__()
        self.s.get("https://www.naver.com/", timeout=10)  # 쿠키 워밍 (references/naver.md)
        self.s.headers["Referer"] = "https://www.naver.com/"


class NaverBlog(NaverBase):
    name = "naver_blog"

    def search(self, q, page):
        r = self.get(f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={quote(q)}&start={(page - 1) * 30 + 1}")
        out = []
        for it in BeautifulSoup(r.text, "lxml").select('div[data-template-id="ugcItem"]') if r else []:
            h = it.select_one("span.sds-comps-text-type-headline1")
            a = h.find_parent("a") if h else None
            if not a or "blog.naver.com" not in a.get("href", ""):
                continue
            # body2 첫 칸은 블로그 이름, 날짜는 그 다음 칸 — 날짜로 읽히는 첫 span 을 쓴다
            dates = [norm_date(s.get_text()) for s in it.select("span.sds-comps-text-type-body2")]
            body = it.select_one("span.sds-comps-text-type-body1")
            out.append({
                "board": "블로그", "title": h.get_text(" ", strip=True), "url": a["href"].split("?")[0],
                "posted_date": next((d for d in dates if d), ""), "views": "", "comments": "", "likes": "",
                "snippet": clean(body.get_text(" ") if body else ""),
            })
        return out


class NaverKin(NaverBase):
    name = "naver_kin"
    pages = 2

    def search(self, q, page):
        r = self.get(f"https://search.naver.com/search.naver?where=kin&query={quote(q)}&start={(page - 1) * 10 + 1}")
        out = []
        for h in BeautifulSoup(r.text, "lxml").select("span.sds-comps-text-type-headline2") if r else []:
            a = h.find_parent("a")
            if not a or "kin.naver.com/qna" not in a.get("href", ""):
                continue
            box, body, date = a, None, ""
            for _ in range(12):  # 질문 본문(body1)과 날짜(body3) span 이 든 조상까지 올라간다
                box = box.parent
                if box is None:
                    break
                body = body or box.select_one("span.sds-comps-text-type-body1")
                date = date or next((d for d in (norm_date(s.get_text()) for s in box.select("span.sds-comps-text-type-body3")) if d), "")
                if body and date:
                    break
            out.append({
                "board": "지식iN", "title": h.get_text(" ", strip=True), "url": a["href"],
                "posted_date": date, "views": "", "comments": "", "likes": "",
                "snippet": clean(body.get_text(" ") if body else ""),
            })
        return out


class Brunch(Site):
    name = "brunch"

    def search(self, q, page):
        r = self.get(f"https://api.brunch.co.kr/v1/search/article?q={quote(q)}&page={page}&pageSize=20")
        out = []
        for it in (r.json().get("data", {}).get("list", []) if r else []):
            ts = it.get("publishTime") or 0
            out.append({
                "board": "에세이", "title": it.get("title", ""), "url": f"https://brunch.co.kr/@{it.get('profileId')}/{it.get('no')}",
                "posted_date": datetime.fromtimestamp(ts / 1000).date().isoformat() if ts else "",
                "views": num(str(it.get("viewCount") or "")), "comments": str(it.get("commentCount", "")), "likes": str(it.get("likeCount", "")),
                "snippet": clean(it.get("contentSummary") or ""),
            })
        return out


SITES = {c.name: c for c in (Clien, Ppomppu, Fmkorea, Dcinside, Pann, Cook82, NaverBlog, NaverKin, Brunch)}


def relevant(text, topics, related):
    kws = [k for k in topics + related if k in text]
    if not kws or EXCLUDE_RE.search(text):
        return None
    emo = COMPLAINT_RE.search(text)
    return (kws[0] + ("·" + emo[0] if emo else "")) if emo else None


def run_site(cls, seen, lock, limit):
    site = cls()
    rows = []
    done = 0
    for cat, (topics, related) in CATEGORIES.items():
        for topic in topics:
            for emo in EMOTIONS:
                for page in range(1, site.pages + 1):
                    done += 1
                    if limit and done > limit:
                        break
                    time.sleep(1)
                    try:
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
                        if not kw and site.body_sel and topic.split()[0] in it["title"] and not EXCLUDE_RE.search(it["title"]):
                            it["snippet"] = site.body(it["url"])
                            kw = relevant(it["title"] + " " + it["snippet"], topics, related)
                        if not kw:
                            continue
                        # 검토 순서용 점수 — 제목에 불편 표현·토픽이 있으면 생활 불편 글일 확률이 높다
                        score = 2 * bool(COMPLAINT_RE.search(it["title"])) + any(k in it["title"] for k in topics + related)
                        rows.append({"site": site.name, "category": cat, "excerpt": it["snippet"] or it["title"],
                                     "matched_keyword": kw, "score": score, **it})
    print(f"[{site.name}] rows={len(rows)} errors={len(site.errors)} {site.errors[:3]}", file=sys.stderr)
    return rows, site.errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", help="필터 통과 후보를 JSONL 로 남길 경로")
    ap.add_argument("--only-summarized", action="store_true")
    ap.add_argument("--sites", default=",".join(SITES))
    ap.add_argument("--limit", type=int, default=0, help="사이트당 검색 요청 수 상한 (연기 테스트용)")
    ap.add_argument("--from-raw", help="수집을 건너뛰고 이 JSONL 로 CSV 만 다시 만든다")
    args = ap.parse_args()
    summaries = json.loads(SUMMARIES.read_text(encoding="utf-8")) if SUMMARIES.exists() else {}
    rows, errors = [], {}
    if args.from_raw:
        rows = [json.loads(line) for line in open(args.from_raw, encoding="utf-8")]
    else:
        seen, lock = set(), __import__("threading").Lock()
        with ThreadPoolExecutor(max_workers=len(SITES)) as ex:
            futs = {ex.submit(run_site, SITES[n], seen, lock, args.limit): n for n in args.sites.split(",")}
            for f, n in futs.items():
                r, e = f.result()
                rows += r
                errors[n] = e
        if args.raw:
            with open(args.raw, "w", encoding="utf-8") as fp:
                for r in rows:
                    fp.write(json.dumps(r, ensure_ascii=False) + "\n")
    kept = []
    for r in rows:
        r.setdefault("excerpt", r.get("snippet") or r["title"])  # reddit_rss.py 산출 행은 excerpt 가 없다
        s = summaries.get(r["url"])  # {"pain_summary": ..., "category": ...} — 사람이 검토해 쓴 요약
        r["pain_summary"] = s["pain_summary"] if s else ""
        if s and s.get("category"):
            r["category"] = s["category"]
        if args.only_summarized and not r["pain_summary"]:
            continue
        kept.append(r)
    kept.sort(key=lambda r: (list(CATEGORIES).index(r["category"]), r["site"], r.get("posted_date", "")))
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=COLS, quoting=csv.QUOTE_ALL, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)
    print(f"CSV {OUT_CSV} rows={len(kept)} (후보 {len(rows)})")
    for n, e in errors.items():
        if e:
            print(f"  {n}: {len(e)} errors, e.g. {e[0]}")


if __name__ == "__main__":
    main()
