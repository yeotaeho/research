# 넓힌 조사 집계 — 판정 결과를 분야별 표로 합치고 CSV 를 쓴다. 자체 점검은 assert 로 한다
"""
실행: uv run --no-project python -X utf8 wide_analyze.py [--pains] [--check 시드]
산출: community_wide_judged.csv, field_signals.csv
--pains 분야별 고통 문구를 출력한다. --check 표본 40건을 판정과 함께 출력한다(사람이 읽어 정확도를 잰다).
"""
import argparse
import csv
import glob
import json
import random
import re
import statistics as st
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDE = ROOT / "work" / "wide"
RECENT = "2024-11"
TODAY = date(2026, 11, 5)


def jsonl(pattern):
    return [json.loads(line) for path in sorted(glob.glob(str(WIDE / pattern))) for line in open(path, encoding="utf-8") if line.strip()]


def load():
    sample = {r["id"]: r for r in jsonl("sample_posts.jsonl")}
    judged = jsonl("judged_c*.jsonl")
    assert len(judged) == len(sample), (len(judged), len(sample))
    assert {j["id"] for j in judged} == set(sample), "판정 id 가 표본과 다르다"
    return [{**sample[j["id"]], **j} for j in judged]


def signal(p):
    return p["fit"] and p["real"] and p["recurring"]


def age_days(d):
    y, m, dd = map(int, d.split("-"))
    return (TODAY - date(y, m, dd)).days


def field_table(posts):
    cands = jsonl("candidates.jsonl")
    recent, ages, comments = Counter(), defaultdict(list), defaultdict(list)
    for r in cands:
        if r["posted_date"] >= RECENT:
            recent[r["category"]] += 1
        if r["site"] in ("dcinside", "clien") and r["posted_date"]:
            ages[r["category"]].append(age_days(r["posted_date"]))
        if r["site"] in ("clien", "pann") and str(r.get("comments", "")).isdigit():
            comments[r["category"]].append(int(r["comments"]))
    by = defaultdict(list)
    for p in posts:
        by[p["category"]].append(p)
    rows = []
    for field, ps in by.items():
        n = len(ps)
        sig = [p for p in ps if signal(p)]
        pct = lambda k: round(100 * sum(1 for p in sig if p[k]) / len(sig)) if sig else 0
        rows.append({
            "field": field, "sample": n, "signal_pct": round(100 * len(sig) / n),
            "candidates_recent": recent[field], "signal_est": round(recent[field] * len(sig) / n),
            "money_pct": pct("money"), "seeking_pct": pct("seeking"), "tool_pct": pct("tool"),
            "tool_signal_est": round(recent[field] * sum(1 for p in sig if p["tool"]) / n),
            "no_kin_sample": sum(1 for p in ps if p["site"] != "naver_kin"),
            "no_kin_tool": sum(1 for p in sig if p["tool"] and p["site"] != "naver_kin"),
            "median_age_days": int(st.median(ages[field])) if ages[field] else "",
            "median_comments": int(st.median(comments[field])) if comments[field] else "",
        })
    rows.sort(key=lambda r: -r["tool_signal_est"])
    return rows


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def short_name(name):
    return re.split(r"\s*[-–:|(ㅣ®]\s*", name, maxsplit=1)[0].strip()[:18]


def apps_summary():
    """검색 잡음을 뺀 핵심 앱을 앱 단위로 합친다. Play 평점은 전 세계 합산이라 한국 앱만 믿을 수 있다."""
    from collect_wide_reviews import core_rows

    rows = core_rows() + [r for r in csv.DictReader((ROOT / "apps_by_field.csv").open(encoding="utf-8-sig")) if r["source"] == "기존 49개"]
    merged = {}
    for r in rows:
        m = merged.setdefault((r["field"], short_name(r["app_name"])), {"field": r["field"], "app": short_name(r["app_name"]), "android": "", "android_count": 0, "low_pct": "", "installs": "", "ios": "", "ios_count": 0})
        if r["platform"] == "android" and int(r["ratings_count"]) >= m["android_count"]:
            m.update(android=r["rating"], android_count=int(r["ratings_count"]), low_pct=r["low_share_pct"], installs=r["installs"])
        if r["platform"] == "ios" and int(r["ratings_count"]) >= m["ios_count"]:
            m.update(ios=r["rating"], ios_count=int(r["ratings_count"]))
    apps = list(merged.values())
    write_csv(ROOT / "apps_core.csv", apps)
    assert len({(a["field"], a["app"]) for a in apps}) == len(apps)
    by = defaultdict(list)
    for a in apps:
        by[a["field"]].append(a)
    for field, xs in by.items():
        xs.sort(key=lambda a: -(a["android_count"] + a["ios_count"]))
        parts = []
        for a in xs[:5]:
            bits = []
            if a["android"] != "":
                bits.append(f"안드 {a['android']}({a['android_count']:,}, 1·2점 {a['low_pct']}%)")
            if a["ios"] != "":
                bits.append(f"iOS {a['ios']}({a['ios_count']:,})")
            parts.append(f"{a['app']} " + " ".join(bits))
        print(f"| {field} | " + " · ".join(parts) + " |")
    print()
    print("안드로이드 1·2점 비율 높은 앱 (평가 300건 이상)")
    low = [a for a in apps if a["low_pct"] != "" and a["android_count"] >= 300]
    for a in sorted(low, key=lambda a: -float(a["low_pct"]))[:24]:
        print(f"| {a['app']} | {a['field']} | {a['android']} | {a['android_count']:,} | {a['low_pct']}% | {a['installs']} | {a['ios'] or '-'} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pains", action="store_true")
    ap.add_argument("--check", type=int)
    ap.add_argument("--apps", action="store_true", help="핵심 앱만 합쳐 apps_core.csv 를 쓰고 분야별 요약과 저평점 목록을 출력한다")
    args = ap.parse_args()
    if args.apps:
        apps_summary()
        return
    posts = load()

    if args.check is not None:
        for p in random.Random(args.check).sample(posts, 40):
            print(f"{p['id']}|{p['category']}|fit{p['fit']} real{p['real']} rec{p['recurring']} tool{p['tool']}|{p['pain']}\n   {p['title'][:60]} // {p['snippet'][:170]}")
        return

    rows = field_table(posts)
    assert sum(r["sample"] for r in rows) == len(posts)
    write_csv(ROOT / "field_signals.csv", rows)
    write_csv(ROOT / "community_wide_judged.csv", [
        {k: p.get(k, "") for k in ("category", "site", "board", "title", "url", "posted_date", "views", "comments", "likes", "snippet", "fit", "real", "recurring", "money", "seeking", "tool", "pain")}
        for p in posts
    ])

    if args.pains:
        by = defaultdict(list)
        for p in posts:
            if signal(p):
                by[p["category"]].append(("$" if p["money"] else "") + ("?" if p["seeking"] else "") + ("" if p["tool"] else "x") + " " + p["pain"])
        for r in rows:
            print(f"## {r['field']} ({len(by[r['field']])})")
            print(" / ".join(by[r["field"]]))
        return

    print("분야 | 후보(2년) | 신호% | 추정글 | 돈% | 찾음% | 도구% | 도구로 줄일 글 | 중간나이(일) | 중간댓글")
    for r in rows:
        print(f"{r['field']} | {r['candidates_recent']} | {r['signal_pct']} | {r['signal_est']} | {r['money_pct']} | {r['seeking_pct']} | {r['tool_pct']} | {r['tool_signal_est']} | {r['median_age_days']} | {r['median_comments']}")

    themes = defaultdict(Counter)
    samples = {r["id"]: r for r in jsonl("sample_reviews.jsonl")}
    for j in jsonl("judged_r*.jsonl"):
        themes[samples[j["id"]]["category"]][j["theme"]] += 1
    print("\n리뷰 유형 (표본 약 20건씩)")
    for f, c in themes.items():
        print(f"{f}: " + ", ".join(f"{k} {v}" for k, v in c.most_common(4)))


if __name__ == "__main__":
    main()
