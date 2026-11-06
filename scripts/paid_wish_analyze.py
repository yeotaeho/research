# 돈 내고 겪는 불만(A)과 소원(B) 판정 결과를 모아 표로 만든다 — 불만 종류, 반복 결제 비율, 소원 영역, 융합 후보
"""
실행: uv run --no-project python -X utf8 scripts/paid_wish_analyze.py [--list]
입력: work/wide/judged_pay_*.jsonl (기존 40분야 표본), judged_pw_a_*.jsonl (새 수집 A), judged_pw_b_*.jsonl (새 수집 B),
      judged_wish.jsonl (기존 표본 소원), judged_review_wish.jsonl (리뷰 소원)
산출: paid_pain_posts.csv, wish_posts.csv, work/wide/paid_wish_table.txt
"""
import collections
import csv
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
W = R / "work" / "wide"


def load(pattern):
    out = {}
    for f in sorted(W.glob(pattern)):
        for line in f.open(encoding="utf-8"):
            line = line.strip()
            if line:
                d = json.loads(line)
                if "id" in d:
                    out[(f.name, d["id"])] = d
    return out


def tsv(name):
    rows = {}
    with (W / name).open(encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < len(hdr):
                continue
            d = dict(zip(hdr, parts))
            rows[int(d["id"])] = d
    return rows


def existing_bucket(s):
    if "없" in s:
        return "없어 보임"
    if "모름" in s or not s:
        return "모름"
    return "있음"


def main():
    listing = "--list" in sys.argv
    out = []
    old = tsv("mined_pay_sample.tsv")
    new = tsv("pw_a_sample.tsv")
    pains, happy = [], collections.Counter()
    for (_, i), d in load("judged_pay_*.jsonl").items():
        if d.get("paid_pain") == 1 and i in old:
            pains.append({"source": "기존표본", "field": old[i]["category"], "site": old[i]["site"], "date": old[i]["date"], "paid_for": d.get("paid_for", ""), "amount": d.get("amount", ""), "complaint": d.get("complaint", ""), "alt": d.get("alt", ""), "recurring": "", "url": old[i]["url"]})
    for (_, i), d in load("judged_pw_a_*.jsonl").items():
        if i not in new:
            continue
        if d.get("happy") == 1 and d.get("paid_for"):
            happy[d["paid_for"]] += 1
        if d.get("paid_pain") == 1:
            pains.append({"source": "새수집", "field": new[i]["query"], "site": new[i]["site"], "date": new[i]["date"], "paid_for": d.get("paid_for", ""), "amount": d.get("amount", ""), "complaint": d.get("complaint", ""), "alt": d.get("alt", ""), "recurring": d.get("recurring", ""), "url": new[i]["url"]})
    with (R / "paid_pain_posts.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(pains[0].keys()))
        w.writeheader()
        w.writerows(pains)
    newp = [p for p in pains if p["source"] == "새수집"]
    out.append(f"## A. 돈 내고 겪은 불만 글 {len(pains)}건 (기존 표본 {len(pains) - len(newp)}, 새 수집 {len(newp)})")
    out.append("불만 종류: " + ", ".join(f"{k} {v}" for k, v in collections.Counter(p["complaint"] for p in pains).most_common()))
    out.append(f"새 수집 중 반복 결제(구독·월납·수수료): {sum(1 for p in newp if str(p['recurring']) == '1')}/{len(newp)}")
    out.append("만족하며 낸다고 적은 것: " + ", ".join(f"{k} {v}" for k, v in happy.most_common(20)))
    if listing:
        out.append("\n새 수집 결제 불만 전부 (무엇에 | 금액 | 반복 | 불만 | 다른 방식)")
        for p in sorted(newp, key=lambda p: (p["complaint"], p["paid_for"])):
            out.append(f"- {p['paid_for']} | {p['amount']} | {p['recurring']} | {p['complaint']} | {p['alt']}")

    wishes = []
    oldw = tsv("mined_wish_all.tsv")
    for (_, i), d in load("judged_wish.jsonl").items():
        if d.get("wish") == 1 and i in oldw:
            wishes.append({"source": "기존표본", "domain": oldw[i]["category"], "want": d.get("want", ""), "pay_signal": d.get("pay_signal", 0), "existing": d.get("existing", ""), "fusion": d.get("fusion", ""), "url": oldw[i]["url"]})
    newb = tsv("pw_b_sample.tsv")
    for (_, i), d in load("judged_pw_b_*.jsonl").items():
        if d.get("wish") == 1 and i in newb:
            wishes.append({"source": "새수집", "domain": d.get("domain", ""), "want": d.get("want", ""), "pay_signal": d.get("pay_signal", 0), "existing": d.get("existing", ""), "fusion": d.get("fusion", ""), "url": newb[i]["url"]})
    rv = tsv("review_wish_sample.tsv")
    for (_, i), d in load("judged_review_wish.jsonl").items():
        if d.get("wish") == 1 and d.get("kind") == "다른 서비스" and i in rv:
            wishes.append({"source": "리뷰", "domain": d.get("category", ""), "want": f"[{d.get('app', '')}] {d.get('want', '')}", "pay_signal": 0, "existing": "", "fusion": d.get("fusion", ""), "url": ""})
    with (R / "wish_posts.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(wishes[0].keys()))
        w.writeheader()
        w.writerows(wishes)
    neww = [w for w in wishes if w["source"] == "새수집"]
    out.append(f"\n## B. 소원 {len(wishes)}건 (기존 표본 {sum(w['source'] == '기존표본' for w in wishes)}, 새 수집 {len(neww)}, 리뷰 융합형 {sum(w['source'] == '리뷰' for w in wishes)})")
    out.append(f"돈 내겠다는 신호: {sum(1 for w in wishes if str(w['pay_signal']) == '1')}")
    out.append("영역(새 수집): " + ", ".join(f"{k} {v}" for k, v in collections.Counter(w["domain"] for w in neww).most_common(25)))
    out.append("기존 서비스 판단(새 수집): " + ", ".join(f"{k} {v}" for k, v in collections.Counter(existing_bucket(w["existing"]) for w in neww).most_common()))
    if listing:
        out.append("\n소원 전부 (출처 | 영역 | 원하는 것 | 돈 | 기존 | 융합)")
        for w in sorted(wishes, key=lambda w: (w["source"], w["domain"])):
            out.append(f"- {w['source']} | {w['domain']} | {w['want']} | {w['pay_signal']} | {w['existing']} | {w['fusion']}")
    text = "\n".join(out)
    (W / "paid_wish_table.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
