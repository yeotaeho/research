# 넓힌 조사 판정 준비 — 40개 분야 후보 글과 저평점 리뷰에서 표본을 뽑아 판정 묶음 파일로 나눈다
"""
실행: uv run --no-project python -X utf8 wide_prepare.py
입력: work/community_raw.jsonl(기존 12개 분야), work/wide/raw_*.jsonl(새 28개 분야와 네이버 40개 분야), appstore_low_reviews_wide.csv
산출: work/wide/candidates.jsonl(전체 후보), work/wide/batch_c*.tsv(글 판정 묶음), work/wide/batch_r*.tsv(리뷰 판정 묶음)
표본은 최근 2년 글에서 사이트별로 고르게 뽑는다. 카페 글이 많아 그냥 뽑으면 한 사이트 판정이 되기 때문이다.
"""
import csv
import glob
import json
import random
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDE = ROOT / "work" / "wide"
RECENT = "2024-11"
BASE_SITES = {"clien", "ppomppu", "dcinside", "pann", "82cook"}
PER_FIELD_POSTS = 40
PER_FIELD_REVIEWS = 20
POST_BATCHES = 6
REVIEW_BATCHES = 2


def one_line(s, n):
    return re.sub(r"\s+", " ", s or "").replace("\t", " ").strip()[:n]


def load_candidates():
    rows, seen = [], set()
    for line in (ROOT / "work" / "community_raw.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["site"] in BASE_SITES:
            rows.append(r)
    for path in glob.glob(str(WIDE / "raw_*.jsonl")):
        rows += [json.loads(line) for line in open(path, encoding="utf-8")]
    out = []
    for r in rows:
        if r["url"] not in seen:
            seen.add(r["url"])
            out.append({k: r.get(k, "") for k in ("site", "board", "category", "title", "url", "posted_date", "views", "comments", "likes", "snippet")})
    return out


def sample_posts(rows, rng):
    by_field = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["posted_date"] >= RECENT:
            by_field[r["category"]][r["site"]].append(r)
    picked = []
    for field, sites in by_field.items():
        pools = [rng.sample(v, len(v)) for v in sites.values()]
        chosen = []
        while len(chosen) < PER_FIELD_POSTS and any(pools):
            for pool in pools:
                if pool and len(chosen) < PER_FIELD_POSTS:
                    chosen.append(pool.pop())
        picked += chosen
    return picked


def main():
    rng = random.Random(1105)
    rows = load_candidates()
    with (WIDE / "candidates.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    posts = sample_posts(rows, rng)
    rng.shuffle(posts)
    for i in range(POST_BATCHES):
        with (WIDE / f"batch_c{i + 1}.tsv").open("w", encoding="utf-8") as f:
            for j, r in list(enumerate(posts))[i::POST_BATCHES]:
                f.write(f"c{j}\t{r['category']}\t{r['site']}\t{one_line(r['title'], 80)}\t{one_line(r['snippet'], 180)}\n")
    with (WIDE / "sample_posts.jsonl").open("w", encoding="utf-8") as f:
        for j, r in enumerate(posts):
            f.write(json.dumps({"id": f"c{j}", **r}, ensure_ascii=False) + "\n")

    reviews = defaultdict(list)
    for r in csv.DictReader((ROOT / "appstore_low_reviews_wide.csv").open(encoding="utf-8-sig")):
        if r["review_date"] >= RECENT:
            reviews[r["category"]].append(r)
    sampled = []
    for field, rs in reviews.items():
        sampled += rng.sample(rs, min(PER_FIELD_REVIEWS, len(rs)))
    rng.shuffle(sampled)
    for i in range(REVIEW_BATCHES):
        with (WIDE / f"batch_r{i + 1}.tsv").open("w", encoding="utf-8") as f:
            for j, r in list(enumerate(sampled))[i::REVIEW_BATCHES]:
                f.write(f"r{j}\t{r['category']}\t{one_line(r['app_name'], 20)}\t{one_line(r['title'] + ' ' + r['body'], 180)}\n")
    with (WIDE / "sample_reviews.jsonl").open("w", encoding="utf-8") as f:
        for j, r in enumerate(sampled):
            f.write(json.dumps({"id": f"r{j}", "category": r["category"], "app_name": r["app_name"], "review_date": r["review_date"], "text": one_line(r["title"] + " " + r["body"], 180)}, ensure_ascii=False) + "\n")
    print(f"후보 {len(rows)} 글 표본 {len(posts)} 리뷰 표본 {len(sampled)}")


if __name__ == "__main__":
    main()
