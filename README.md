# research — B2C 아이템 조사 자료 (2026-11-04 수집)

일상생활의 반복되는 불편·피로·고통을 찾고, 2027 모두의 창업·예비창업패키지 지원을 준비하기 위한 원자료다. 레포는 public 이므로 이 폴더는 **커밋하지 않는다**(제3자 리뷰·커뮤니티 글 원문이 들어 있다). 작성자 이름·닉네임은 어느 파일에도 넣지 않았다.

## 파일

| 파일 | 행 | 내용 |
|---|---|---|
| `appstore_low_reviews.csv` | 21,336 | 일상 앱 49개의 1·2점 리뷰. iOS 8,614(최근 500건 중 저평점) + Android 12,722(1점 200·2점 100 최신순). 14개 분야. 1점 16,266·2점 5,070 |
| `community_complaints.csv` | 404 | 9개 커뮤니티에서 고른 "생활 속 반복되는 번거로움" 글. 12개 분야 모두 20건 이상. `pain_summary` 는 한 줄 요약 |
| `modoo_yechang_stats.csv` | 260 | 모두의 창업 2026 1·2차와 예창패 2023~2027 의 지원자·선발·경쟁률·분야·라운드·평가·예산 수치. 한 사실에 한 행, 출처마다 행 |
| `modoo_yechang_reviews.csv` | 214 | 합격·불합격·심사위원 시점 후기. 심사 질문·점수 포인트·조언. 모두의 창업 134·예창패 80 |

컬럼은 각 파일 첫 줄에 있다. 모두 UTF-8(BOM)·쉼표·전 필드 큰따옴표라 엑셀에서 바로 열린다.

## 먼저 볼 것

- **예창패는 2026 에 300명(2025 는 780~810명)으로 줄었고 경쟁률 약 49:1 이다.** 2027 정부 예산안(9/1)에는 예창패 0원, 모두의 창업 4,411억·2만 명·평균 3천만 원으로 잡혀 있다. 통합은 12월 국회 의결 전까지 미확정이고 중기부는 7/28 "확정된 사항 아님" 이라 했다. `modoo_yechang_stats.csv` 의 cohort 2026·2027 행.
- 예창패 공고문에는 평가 항목 4개(문제인식·실현가능성·성장전략·팀구성)만 있고 **항목별 점수는 비공개**다. 과락이 60점 미만(2024·2025)에서 70점 미만(2026)으로 올랐다. 가점은 서류에만 최대 3점.
- 모두의 창업 2차 1R 평가 항목 7개(문제 정의·창업 의지·아이디어 구체성·시장 수요·수익모델·초기 고객 확보 전략·사회적 가치), 책임멘토 3인 서면. 재도전 가점 최대 4점.
- 후기에서 반복된 심사 질문은 다섯 가지다. 첫 고객 100명이 누구인가, 가격과 수익 모델의 근거, 대기업·기존 서비스 대비 차별점, 혼자 협약기간 안에 만들 수 있나, 고객을 몇 명 만났고 무엇을 검증했나.

## 분야별 가장 많이 반복된 불만 (요약)

앱 리뷰는 구독·결제·환불, 업데이트 뒤 UI 변경, 튕김·동기화 오류, 로그인·본인인증 반복이 분야를 가리지 않고 상위다. 서비스형(배달·청소·세탁)은 품질·지연·고객센터가 절반 이상이다.

커뮤니티 글의 고통은 다르다. 설거지·빨래 같은 집안일의 끝없음, 매일 "뭐 해먹지", 운동 "나가는 시작", 구독 해지 버튼 못 찾기, 같은 약 재처방에 긴 대기, 공동인증서 발급·갱신 반복, 단톡방·약속 날짜 조율, 혼자 끼니 해결, 택배 오배송·반품 포기. 분야별 상위 3개는 `community_complaints.csv` 를 category 로 묶어 `pain_summary` 를 읽으면 된다.

## 수집 방법과 한계

- 앱 리뷰: Apple 은 공개 RSS(`itunes.apple.com/kr/rss/customerreviews`, 앱당 최근 500건), Android 는 `google-play-scraper`. iOS 는 RSS 가 간헐적으로 빈 페이지를 돌려줘 실행마다 ±10% 흔들린다. 다노는 서비스 종료, 브로콜리는 토스로 대체, 버닛은 번핏·미라클나잇은 Renight 로 수집.
- 커뮤니티: 클리앙·뽐뿌·디시·네이트판·82cook·브런치·네이버 블로그·지식iN·레딧. 후보 5,832건 중 상품 단건 욕·광고·뉴스·리뷰를 빼고 404건을 골랐다(전수 분류가 아니라 상위 후보 선별). 인스티즈는 Cloudflare 봇 검증, 에펨코리아는 HTTP 430 차단, 더쿠는 검색이 로그인 전용, 블라인드·네이버 카페는 로그인 필요라 제외.
- 통계·후기: 공고문 PDF 11개(`downloads/`)와 중기부·정책브리핑·언론·블로그·유튜브 자막. note 앞에 `1차 출처`(공고·보도자료·언론)와 `2차 출처`(블로그·포털) 를 적었다. 예창패 공식 선정자 수·기관별 경쟁률은 비공개라 언론 인용으로 대체했다. 모두의 창업 1기 권역 오디션·파이널 결과는 11월 현재 미발표.

## 재실행

```bash
cd C:\project\trend && uv run --no-project --with requests --with google-play-scraper python research/scripts/collect_low_reviews.py
```

```bash
cd C:\project\trend && uv run --no-project --with "curl_cffi>=0.15" --with beautifulsoup4 --with lxml python research/scripts/collect_complaints.py --from-raw research/work/community_raw.jsonl --only-summarized
```

```bash
cd C:\project\trend && uv run --no-project python -I -X utf8 research/scripts/build_csv.py
```

```bash
cd C:\project\trend && uv run --no-project python -X utf8 research/scripts/validate_all.py
```

`work/` 에는 재실행에 필요한 원본 덤프(`community_raw.jsonl`, `reviews_*.jsonl`, 유튜브 자막 `yt/`)만 남겼다. 스크립트 설명은 각 파일 첫 줄 주석에 있다.
