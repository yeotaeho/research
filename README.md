# research — B2C 아이템 조사 자료 (2026-11-04 수집)

일상생활의 반복되는 불편·피로·고통을 찾고, 2027 모두의 창업·예비창업패키지 지원을 준비하기 위한 원자료다. 레포는 public 이므로 이 폴더는 **커밋하지 않는다**(제3자 리뷰·커뮤니티 글 원문이 들어 있다). 작성자 이름·닉네임은 어느 파일에도 넣지 않았다.

## 파일

| 파일 | 행 | 내용 |
|---|---|---|
| `appstore_low_reviews.csv` | 21,336 | 일상 앱 49개의 1·2점 리뷰. iOS 8,614(최근 500건 중 저평점) + Android 12,722(1점 200·2점 100 최신순). 14개 분야. 1점 16,266·2점 5,070 |
| `community_complaints.csv` | 404 | 9개 커뮤니티에서 고른 "생활 속 반복되는 번거로움" 글. 12개 분야 모두 20건 이상. `pain_summary` 는 한 줄 요약 |
| `modoo_yechang_stats.csv` | 260 | 모두의 창업 2026 1·2차와 예창패 2023~2027 의 지원자·선발·경쟁률·분야·라운드·평가·예산 수치. 한 사실에 한 행, 출처마다 행 |
| `community_wide_judged.csv` | 1,600 | **40개 분야 판정 표본(11/5).** 글마다 분야 적합·실제 고통·반복·돈·해결 찾음·도구로 줄임과 고통 문구 |
| `field_signals.csv` | 40 | 분야별 집계. 전체 후보 12,397건은 `work/wide/candidates.jsonl` |
| `apps_by_field.csv` · `apps_core.csv` | 772 · 186 | 분야별 앱과 평점·평가 수·설치 수·1·2점 비율. core 는 검색 잡음을 손으로 뺀 앱 단위 표 |
| `appstore_low_reviews_wide.csv` | 29,037 | 새 분야 핵심 앱의 1·2점 리뷰. 컬럼은 `appstore_low_reviews.csv` 와 같다 |
| `modoo_yechang_reviews.csv` | 214 | 합격·불합격·심사위원 시점 후기. 심사 질문·점수 포인트·조언. 모두의 창업 134·예창패 80 |

컬럼은 각 파일 첫 줄에 있다. 모두 UTF-8(BOM)·쉼표·전 필드 큰따옴표라 엑셀에서 바로 열린다.

## 후보 아이템 문서

| 파일 | 내용 |
|---|---|
| `wide_field_research_v0.1.md` | **40개 분야로 넓힌 조사(11/5).** 어느 분야가 도구로 줄일 수 있는 고통인가, 앱과 평점, 저평점의 함정 |
| `insurance_note_v0.1.md` | 보험·실손 반응과 막힌 자리, 지인에게 물을 것 |
| `candidate_items_v0.1.md` | 후보 3개와 보류 목록, **조사 뒤 세 후보 비교(순서 1 → 2 → 3)** |
| `launch_kit_v0.1.md` | **후보 1 다음 할 일.** 순서, 132 질문, 제보 폼 문항, 모집 글 |
| `refund_validation_plan_v0.1.md` · `b_side_outreach_v0.1.md` · `b_side/` · `wizard/` | 후보 1 잠결 결제 되찾기. 검증 계획, 앱 사업자 메일·리포트, 무료 위자드. 위자드 빌드는 `scripts/build_wizard.py`, 메일·리포트 생성은 `scripts/b_side_kit.py` |
| `gym_validation_plan_v0.1.md` · `wizard/gym/` | 헬스장 환불 계산기. 후보 1 과 나란히 시험. 가설, 폼, 모집, 근거 표. 계산 점검은 `node wizard/gym/check.js` |
| `paid_wish_research_v0.1.md` | **돈이 흐르는 고통과 소원(11/5).** 소비자원 2025 연보 상위 30 품목, 돈 내고 겪은 불만 272건(`paid_pain_posts.csv`), 돈 내는 앱 26개의 불만과 다른 방식, 소원 102건(`wish_posts.csv`)과 융합 후보, 자리별 기존 앱. 결론은 사업자(1인 전문가) 쪽 |
| `pro_interview_kit_v0.1.md` | **1인 서비스 전문가 인터뷰 키트(11/5).** 가설 H1~H5, 5명 구성과 찾을 카페, 접근 문구, 질문 15개, 기록 표, 판정 규칙, 플랫폼 요금 사실표. 기록은 `work/pro_interviews.tsv`(레포 밖) |
| `platform_compare_v0.1.md` | **숨고·크몽·위시켓·탈잉·당근 비교(11/6).** 누가 내나, 과금, 규모, 플랫폼 밖 거래 규정, 전문가 쪽 불만, A-① 적합도. 당근이 무료 경쟁자 |
| `pro_survey_v0.1.md` | **1인 전문가 설문지(11/9).** 인터뷰 대신 구글 폼 26문항, 스크리닝 분기, 기프티콘·개인정보 운영, 배포 채널, 설문용 H1~H5 판정 비율, 일정 |
| `community_probe_v0.1.md` | **설문 배포 후보 커뮤니티 조사(11/10).** 네이버 카페 9곳의 회원 수·하루 글 수·반응·등급 조건·과거 설문 글, 카페 밖(OKKY·디스콰이엇·당근 모임·오픈채팅) 접근 결과, 바뀐 배포 순서 |
| `survey_posts_v0.1.md` | **설문 배포 문구(11/10).** 지인 카톡, 만렙사장·공부방·아프니까 사장이다 게시글, 청소동우회·뷰앤잡 운영진 쪽지, 보충용 문구, 날짜별 일정 |
| `completion_card_concept_v0.1.md` | **작업 완료 카드 콘셉트(11/11).** 설문 배포가 막혀 먼저 만들기로 한 뒤의 판단. 무엇을 만드나, 카카오톡·당근·숨고·예약 앱과의 차별점(기억·기록·동의), 만들지 않는 것, 11/14 미팅 질문, 반응 판정 기준 |
| `card_demo/delivery_card.html` | **납품 카드 시제품(11/12).** 11/14 디자이너 미팅용. 고객 화면·만들기·카드함 세 화면, 예시 데이터, 서버 없음. 게시 주소 https://claude.ai/artifact/83b14dBgDHNyXA8JyqbdVC |
| `designer_meeting_questions_v0.1.md` | **디자이너 미팅 질문지(11/12).** 11/14 미팅용. 듣기 14문항, 시제품 관찰과 4문항, 약속 4문항, 청소 실무자 통화용 6문항, 들고 갈 한 장, 기록 표, 답에 따른 다음 행동. 시제품은 듣기 뒤에 꺼낸다. 11/13 전달받은 대화를 반영해 고침(내용은 콘셉트 문서 "11/13 에 들은 것") |
| `household_validation_plan_v0.1.md` | 후보 2 집안일 장부. 규제 벽 없음, 앱 75개 중 승자 없음, 1회 결산으로 모양 변경 |
| `refill_validation_plan_v0.1.md` | 후보 3 재처방 비서. 원내처방·대리처방 제외, 12/24 비대면 규칙 안내만 시험 |
| `work/household_research.md` · `work/refill_research.md` | 위 두 문서의 조사 원문과 출처 전체. 표기 주의는 각 계획 문서의 "확인" 열 |

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
