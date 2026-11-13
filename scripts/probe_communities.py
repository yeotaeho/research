# 설문 배포 후보 네이버 카페 9곳의 공개 정보를 모은다 — 회원 수·등급 조건·게시판·최근 글 활동·설문 글 흔적
"""
실행: CURL_CA_BUNDLE=work/cacert.pem uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with pyyaml --with lxml python -X utf8 scripts/probe_communities.py
산출: work/community/cafes.json. 로그인 없이 열리는 것만 읽는다. 작성자 닉네임·키는 저장하지 않는다(등급 이름만).
"""
import collections
import json
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:/Users/여태호/.claude/plugins/cache/gptaku-plugins/insane-search/0.8.2/skills/insane-search")
sys.path.insert(0, str(Path(__file__).parent))
from engine import fetch  # noqa: E402
from collect_wide import NaverCafe  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "work" / "community" / "cafes.json"
API = "https://apis.naver.com/cafe-web"
CAFES = {  # cluburl: (검색에서 카페를 가려낼 낱말, 검색어에 쓸 이름)
    "jihosoccer123": ("아프니까", "아프니까 사장이다"), "whduddn0317": ("만렙사장", "만렙사장"), "clean365": ("청소동우회", "청소동우회"),
    "makegoodstudy": ("성공하는 공부방", "성공하는 공부방 운영하기"), "hikicks": ("과외구하기", "과외구하기 카페"), "bnjob": ("뷰앤잡", "뷰앤잡"),
    "sassinail": ("맨사", "맨사 네일"), "pibumoimcafe": ("최고피부관리사", "최고피부관리사모임"), "overseer": ("셀프 인테리어", "셀프 인테리어 My Home"),
}
KEYS = {
    "플랫폼": r"숨고|크몽|당근|미소|네이버 ?예약|플레이스|배민|배달의민족|쿠팡이츠|요기요|김과외|오늘의집|탈잉",
    "단골·재방문": r"단골|재방문|재구매|재계약|고객 ?관리", "노쇼·취소": r"노쇼|당일 ?취소|예약금", "견적·단가": r"견적|단가|흥정|깎",
    "광고·홍보": r"광고|홍보|마케팅|블로그 ?체험|인스타", "직원·알바": r"직원|알바|구인", "세금·정산": r"세금|부가세|종소세|세무|미수",
    "진상·분쟁": r"진상|환불|컴플레인|리뷰 ?테러|분쟁", "매출": r"매출|손님이 ?없|일감|비수기",
}
BOARD = r"설문|투표|여론|홍보|광고|업체|질문|자유|공지|등업|가입"


def get(url):
    time.sleep(1)
    r = fetch(url, timeout=20)
    try:
        return json.loads(r.content or "")
    except ValueError:
        return {}


def probe(club, key, name, search):
    g = get(f"{API}/cafe2/CafeGateInfo.json?cluburl={club}").get("message", {}).get("result", {})
    info = g.get("cafeInfoView", {})
    cid = info.get("cafeId")
    out = {"club": club, "name": info.get("cafeName"), "cafeId": cid, "members": g.get("memberCount"), "opened": info.get("openDate"),
           "level_system": g.get("useMemberLevel")}
    if not cid:
        return out
    lv = get(f"{API}/cafe-mobile/CafeMemberLevelInfo?cafeId={cid}").get("message", {}).get("result", {}).get("memberLevelList", [])
    out["levels"] = [{"name": x["memberlevelname"], "type": x["leveluptype"], "글": x["articlecount"], "댓글": x["commentcount"],
                      "방문": x["visitcount"], "가입주": x["joindtcondition"]} for x in lv if x.get("useyn") == "Y"]
    menus = get(f"{API}/cafe2/SideMenuList?cafeId={cid}").get("message", {}).get("result", {}).get("menus", [])
    out["menu_count"] = sum(1 for m in menus if m["menuType"] != "S")
    out["menus_flagged"] = [(m["menuName"].strip().replace("&amp;", "&"), m["lastUpdateDate"][:10]) for m in menus
                            if re.search(BOARD, m["menuName"])]
    posts = []
    for page in range(1, 7):
        d = get(f"{API}/cafe-boardlist-api/v1/cafes/{cid}/menus/0/articles?page={page}&pageSize=50&sortBy=TIME&viewType=L")
        items = [a["item"] for a in d.get("result", {}).get("articleList", []) if a.get("type") == "ARTICLE"]
        if not items:
            break
        for it in items:
            posts.append({"ts": it["writeDateTimestamp"], "menu": it.get("menuName", ""), "subject": it.get("subject", ""),
                          "summary": (it.get("summary") or "")[:200], "comments": it.get("commentCount", 0), "reads": it.get("readCount", 0),
                          "level": (it.get("writerInfo") or {}).get("memberLevelName", ""), "open": it.get("openArticle")})
    out["posts"] = posts
    if len(posts) > 1:
        span_h = (posts[0]["ts"] - posts[-1]["ts"]) / 3.6e6
        out["sampled"] = len(posts)
        out["span_hours"] = round(span_h, 1)
        out["posts_per_day"] = round(len(posts) / span_h * 24) if span_h else None
        out["median_reads"] = statistics.median(p["reads"] for p in posts)
        out["median_comments"] = statistics.median(p["comments"] for p in posts)
        out["zero_comment_share"] = round(sum(p["comments"] == 0 for p in posts) / len(posts), 2)
        out["top_menus"] = collections.Counter(p["menu"] for p in posts).most_common(8)
        out["writer_levels"] = collections.Counter(p["level"] for p in posts).most_common(6)
        out["keyword_share"] = {k: round(sum(bool(re.search(p_, x["subject"] + " " + x["summary"])) for x in posts) / len(posts), 3)
                                for k, p_ in KEYS.items()}
    hits = {}
    for q in (f"{name} 설문조사", f"{name} 설문 기프티콘"):
        time.sleep(2)
        try:
            for it in search.search(q, 1):
                if key in it["board"] and re.search(r"설문|인터뷰", it["title"] + it["snippet"]):
                    hits[it["url"]] = {"title": it["title"], "date": it["posted_date"]}
        except Exception as e:  # noqa: BLE001
            out.setdefault("search_errors", []).append(type(e).__name__)
    out["survey_posts"] = list(hits.values())
    return out


def main():
    search = NaverCafe()
    rows = []
    for club, (key, name) in CAFES.items():
        r = probe(club, key, name, search)
        rows.append(r)
        print(r.get("name"), r.get("members"), r.get("posts_per_day"), len(r.get("survey_posts", [])), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
