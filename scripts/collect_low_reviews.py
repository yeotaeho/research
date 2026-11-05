# 저평점 리뷰 수집기 — 한국 일상 앱의 1·2점 리뷰를 App Store RSS 와 Google Play 에서 모아 CSV 하나로 쓴다
# 실행: uv run --no-project --with requests --with google-play-scraper python research/scripts/collect_low_reviews.py
import csv
import re
import sys
import time
from pathlib import Path

import requests
from google_play_scraper import Sort, reviews

OUT = Path(__file__).resolve().parents[1] / "appstore_low_reviews.csv"
COLUMNS = [
    "platform", "category", "app_name", "app_id", "store_url", "rating", "review_date",
    "app_version", "title", "body", "thumbs_up", "review_id",
]
MIN_BODY = 10
IOS_PAGES = 10
SLEEP = 0.5
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}

# (분야, 앱 이름, iOS trackId, Android 패키지). None 은 그 스토어에 없음.
# 다노(마이다노)는 양쪽 스토어에서 사라져 제외, 브로콜리는 Play 에 없어 토스로 대체, 버닛→번핏, 미라클나잇→Renight(개명).
APPS = [
    ("가계부·돈관리", "뱅크샐러드", 1195804784, "com.rainist.banksalad2"),
    ("가계부·돈관리", "편한가계부", 560481810, "com.realbyteapps.moneymanagerfree"),
    ("가계부·돈관리", "똑똑가계부", None, "com.dencreak.spbook"),
    ("가계부·돈관리", "토스", 839333328, "viva.republica.toss"),
    ("할일·루틴·생산성", "마이루틴", 1518956326, "com.minding.myroutine"),
    ("할일·루틴·생산성", "챌린저스", 1438855824, "kr.co.whitecube.chlngers"),
    ("할일·루틴·생산성", "TickTick", 626144601, "com.ticktick.task"),
    ("할일·루틴·생산성", "Todoist", 572688855, "com.todoist"),
    ("할일·루틴·생산성", "투두메이트", 1505220130, "com.undefined.mate"),
    ("수면·알람", "알라미", 1163786766, "droom.sleepIfUCan"),
    ("수면·알람", "Sleep Cycle", 320606217, "com.northcube.sleepcycle"),
    ("수면·알람", "Renight(미라클나잇)", 1619362440, "com.munice.miraclenight_android"),
    ("건강·운동", "플랜핏", 1511876936, "com.mih.planfit"),
    ("건강·운동", "번핏", 1503464984, "com.bunnit.haja.android"),
    ("건강·운동", "런데이", 1042937618, "com.hanbit.rundayfree"),
    ("건강·운동", "Noom", 634598719, "com.wsl.noom"),
    ("건강·운동", "인아웃", 1599210729, "com.taejinketo.inout_webview"),
    ("식단·다이어트", "밀리그램", 1514163957, "com.lefal.mealligram"),
    ("식단·다이어트", "다이어트신", 981460948, "com.diet.calorie160105"),
    ("식단·다이어트", "필라이즈", 1595472563, "com.pillyze.health"),
    ("교통·이동", "카카오T", 981110422, "com.kakao.taxi"),
    ("교통·이동", "티맵", 431589174, "com.skt.tmap.ku"),
    ("교통·이동", "카카오맵", 304608425, "net.daum.android.map"),
    ("교통·이동", "네이버지도", 311867728, "com.nhn.android.nmap"),
    ("교통·이동", "카카오버스", 1095206186, "com.astroframe.seoulbus"),
    ("교통·이동", "지하철종결자", 580488128, "teamDoppelGanger.SmarterSubway"),
    ("교통·이동", "모두의주차장", 780174422, "com.parkingshare.mobile"),
    ("배달·음식", "배달의민족", 378084485, "com.sampleapp"),
    ("배달·음식", "쿠팡이츠", 1445504255, "com.coupang.mobile.eats"),
    ("배달·음식", "요기요", 543831532, "com.fineapp.yogiyo"),
    ("쇼핑·중고", "당근", 1018769995, "com.towneers.www"),
    ("쇼핑·중고", "번개장터", 395672275, "kr.co.quicket"),
    ("쇼핑·중고", "쿠팡", 454434967, "com.coupang.mobile"),
    ("집안일·생활서비스", "청소연구소", 1215174815, "kr.co.cleaninglab.user"),
    ("집안일·생활서비스", "미소", 1071778654, "com.miso"),
    ("집안일·생활서비스", "런드리고", 1453485913, "com.laundrygo.android"),
    ("집안일·생활서비스", "세탁특공대", 1049236217, "com.washswat.android"),
    ("육아", "베이비타임", 1052459780, "yducky.application.babytime"),
    ("육아", "맘스다이어리", 669378713, "com.moms.momsdiary"),
    ("육아", "키즈노트", 527574743, "com.vaultmicro.kidsnote"),
    ("반려동물", "핏펫", 1335906446, "kr.co.fitpet"),
    ("반려동물", "펫프렌즈", 1086466469, "com.fineappstudio.android.petfriends"),
    ("공부·자기계발", "열품타", 1441909643, "com.pallo.passiontimerscoped"),
    ("공부·자기계발", "스픽", 1286609883, "com.selabs.speak"),
    ("공부·자기계발", "밀리의서재", 1213788923, "kr.co.millie.millieshelf"),
    ("공부·자기계발", "클래스101", 1320607634, "net.pedaling.class101"),
    ("병원·약", "똑닥", 1014889755, "com.bbros.sayup"),
    ("병원·약", "굿닥", 517637141, "com.ksncho.hospitalinfo"),
    ("행정·공과금", "정부24", 586454505, "kr.go.minwon.m"),
]

failures = []  # (platform, app_name, reason)


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def ios_reviews(cat, name, track_id):
    rows = []
    url_t = f"https://itunes.apple.com/kr/rss/customerreviews/page={{}}/id={track_id}/sortby=mostrecent/json"
    for page in range(1, IOS_PAGES + 1):
        r = None
        for attempt in range(3):
            r = requests.get(url_t.format(page), headers=UA, timeout=30)
            if r.status_code != 429:
                break
            log(f"  ios {name} p{page} 429 — 60초 대기")
            time.sleep(60)
        if r.status_code == 404:
            break
        if r.status_code != 200:
            failures.append(("ios", name, f"p{page} HTTP {r.status_code}"))
            break
        entries = r.json().get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        # Apple RSS 는 간헐적으로 한 페이지를 비워 돌려준다(1페이지가 비고 2페이지에 50건). 빈 페이지에서 멈추지 않고 10페이지까지 간다.
        for e in entries:
            if "im:rating" not in e:
                continue
            rating = int(e["im:rating"]["label"])
            if rating not in (1, 2):
                continue
            rows.append({
                "platform": "ios", "category": cat, "app_name": name, "app_id": str(track_id),
                "store_url": f"https://apps.apple.com/kr/app/id{track_id}",
                "rating": rating, "review_date": e["updated"]["label"][:10],
                "app_version": e.get("im:version", {}).get("label", ""),
                "title": clean(e.get("title", {}).get("label")),
                "body": clean(e.get("content", {}).get("label")),
                "thumbs_up": e.get("im:voteSum", {}).get("label", "0"),
                "review_id": e["id"]["label"],
            })
        time.sleep(SLEEP)
    return rows


def android_reviews(cat, name, pkg):
    rows = []
    for score, count in ((1, 200), (2, 100)):
        try:
            result, _ = reviews(pkg, lang="ko", country="kr", sort=Sort.NEWEST, filter_score_with=score, count=count)
        except Exception as e:  # noqa: BLE001
            failures.append(("android", name, f"score={score} {e!r}"))
            continue
        for rv in result:
            rows.append({
                "platform": "android", "category": cat, "app_name": name, "app_id": pkg,
                "store_url": f"https://play.google.com/store/apps/details?id={pkg}&hl=ko&gl=kr",
                "rating": rv["score"], "review_date": rv["at"].strftime("%Y-%m-%d"),
                "app_version": rv.get("reviewCreatedVersion") or "",
                "title": "", "body": clean(rv.get("content")),
                "thumbs_up": rv.get("thumbsUpCount", 0),
                "review_id": rv["reviewId"],
            })
        time.sleep(SLEEP)
    return rows


def main():
    platforms = set(sys.argv[1:]) or {"ios", "android"}
    rows = []
    for cat, name, track_id, pkg in APPS:
        if "ios" in platforms and track_id:
            got = ios_reviews(cat, name, track_id)
            log(f"ios     {name:<16} {len(got):>4}")
            rows += got
        if "android" in platforms and pkg:
            got = android_reviews(cat, name, pkg)
            log(f"android {name:<16} {len(got):>4}")
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
    log(f"\n저장 {OUT} — 원본 {len(rows)} 행 → 중복·짧은 본문 제거 후 {len(out)} 행")
    if failures:
        log("실패:")
        for fl in failures:
            log(f"  {fl}")


if __name__ == "__main__":
    main()
