# 돈 내고 겪는 불만 글(A)과 "이런 거 있으면" 소원 글(B)을 분야 제한 없이 커뮤니티에서 모은다
"""
실행: uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml python -X utf8 scripts/collect_paid_wish.py
산출: research/work/wide/pw_raw.jsonl (track 열이 A/B). 네이버는 2초 간격. 작성자 이름은 저장하지 않는다.
"""
import json
import time
from pathlib import Path

from collect_complaints import Clien, Cook82, Dcinside, NaverKin, Pann, Ppomppu
from collect_wide import NaverCafe

OUT = Path(__file__).resolve().parents[1] / "work" / "wide"
WISH = ["이런 앱 있으면 좋겠다", "이런 서비스 있으면 좋겠다", "이런 앱 없나요", "이런 서비스 없나요", "해주는 앱 없나요",
        "해주는 서비스 없나요", "대신 해주는 서비스 없나", "왜 이런 앱이 없지", "누가 만들어주면 좋겠다", "있으면 돈 내고 쓸",
        "돈 내고라도 쓰고 싶은", "이런 거 만들어주세요", "자동으로 해주는 앱 없나", "이런 기능 있는 앱 없나", "이런 거 있으면 편할텐데",
        "있으면 좋을텐데 앱", "이런 서비스 왜 없을까"]
PAID = ["돈 아까운 구독", "구독 해지하고 싶은데", "수수료 너무 비싸", "돈 냈는데 서비스가", "유료인데 왜 이래", "돈 주고 샀는데 후회",
        "비용 대비 별로 서비스", "매달 나가는 돈 아까운", "돈 내고 쓰는 앱 추천", "유료로 쓰는 앱 뭐", "구독 서비스 뭐 쓰세요",
        "매달 구독료 얼마 나가", "돈 내고 쓰는 서비스 만족", "유료 결제한 거 중 제일", "고정비 줄이기 구독", "돈 주고 맡겼는데",
        "업체에 돈 주고 후회", "대행 맡겼는데 별로", "돈 주고 상담받았는데", "돈 아깝지 않은 서비스"]


def main():
    seen, rows = set(), []
    for cls, delay in ((Dcinside, 1), (Clien, 1), (Pann, 1), (Ppomppu, 1), (Cook82, 1), (NaverCafe, 2), (NaverKin, 2)):
        site = cls()
        for track, qs in (("B", WISH), ("A", PAID)):
            for q in qs:
                time.sleep(delay)
                try:
                    items = site.search(q, 1)
                except Exception as e:  # noqa: BLE001
                    print(site.name, q, type(e).__name__, flush=True)
                    items = []
                for it in items:
                    if it["url"] in seen:
                        continue
                    seen.add(it["url"])
                    rows.append({"track": track, "site": site.name, "query": q, **it})
        print(site.name, "누적", len(rows), site.errors[:2], flush=True)
        with (OUT / "pw_raw.jsonl").open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("끝", len(rows))


if __name__ == "__main__":
    main()
