# 1인 서비스 전문가가 플랫폼 비용을 이야기하는 네이버 카페를 찾는다 — 카페 이름별 글 수와 최근 제목
"""
실행: uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml python -X utf8 scripts/find_pro_cafes.py
산출: research/work/wide/pro_cafes.jsonl. 네이버는 2초 간격. 작성자 이름은 저장하지 않는다.
"""
import collections
import json
import time
from pathlib import Path

from collect_wide import NaverCafe

OUT = Path(__file__).resolve().parents[1] / "work" / "wide" / "pro_cafes.jsonl"
QUERIES = ["숨고 캐시 아깝", "숨고 견적 비용 고수", "숨고 멤버십 인상", "크몽 수수료 전문가", "미소 파트너 수수료", "청소업체 숨고 견적",
           "네이버 예약 노쇼 원장", "1인샵 예약 관리 원장", "과외 중개 수수료 선생", "김과외 수수료", "이사업체 견적 플랫폼 수수료",
           "에어컨 청소 업체 홍보 비용", "출장 수리 업체 광고비", "재방문 고객 관리 사장님 카톡"]


def main():
    site = NaverCafe()
    rows = []
    for q in QUERIES:
        for page in (1, 2):
            time.sleep(2)
            try:
                items = site.search(q, page)
            except Exception as e:  # noqa: BLE001
                print(q, page, type(e).__name__, flush=True)
                break
            for it in items:
                rows.append({"query": q, **it})
            if len(items) < 5:
                break
        print(q, len(rows), flush=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cafes = collections.Counter(r.get("board", "") for r in rows)
    print("\n카페별 글 수")
    for name, n in cafes.most_common(30):
        print(f"{n:3d}  {name}")


if __name__ == "__main__":
    main()
