// 1인 전문가 설문지 v0.1(pro_survey_v0.1.md)을 구글 폼으로 만든다 — script.google.com 새 프로젝트에 붙여 넣고 build 를 한 번 실행
//
// 실행: script.google.com → 새 프로젝트 → Code.gs 내용을 이 파일로 바꾸고 저장 → 함수 build 선택 → 실행 → 권한 허용
// 결과: 실행 로그에 편집 URL 과 응답 URL 이 찍힌다. 두 번 실행하면 폼이 둘 생기니 한 번만 돌린다.
// 분기: Q1 "3명 이상", Q2 "없다" 는 종료 페이지로 간다. 마무리 페이지 다음은 바로 제출이다.

const CONTINUE = FormApp.PageNavigationType.CONTINUE;

function build() {
  const form = FormApp.create('혼자 일하는 전문가의 고객 받기·재거래 설문 (5분, 커피 기프티콘)');
  form
    .setDescription(
      [
        '안녕하세요. 혼자 일하시는 전문가분들이 숨고·크몽·당근 같은 플랫폼을 어떻게 쓰시는지, 한 번 거래한 고객과 다시 어떻게 연결되는지 조사하고 있습니다. 창업을 준비하는 개인 조사이고 상품 판매나 광고가 아닙니다.',
        '',
        '• 소요 시간은 5분입니다.',
        '• 혼자(또는 1~2명과) 일하고 최근 3개월 안에 플랫폼으로 고객을 받으신 분이 끝까지 응답하시면, 선착순 30분께 커피 기프티콘을 문자로 드립니다(응답 마감 뒤 1주일 안).',
        '• 전화번호는 기프티콘과 인터뷰 연락에만 쓰고 발송 뒤 지웁니다. 응답은 통계로만 씁니다.',
        '• 15분 전화 인터뷰에 응해 주시는 분께는 1만 원 기프티콘을 더 드립니다(5분).',
      ].join('\n')
    )
    .setCollectEmail(false)
    .setLimitOneResponsePerUser(false)
    .setAllowResponseEdits(false)
    .setProgressBar(true)
    .setShowLinkToRespondAgain(false)
    .setConfirmationMessage('감사합니다. 조건에 맞는 분께 응답 마감 뒤 1주일 안에 문자로 기프티콘을 보내 드립니다.');

  // 섹션 1·2. 자격. 분기가 걸리는 문항은 한 페이지에 하나만 둔다(한 페이지에 둘이면 마지막 것만 적용된다).
  const q1 = form.addMultipleChoiceItem().setTitle('지금 일하시는 형태는요?').setRequired(true);
  page(form, '응답 자격 확인');
  const q2 = form
    .addMultipleChoiceItem()
    .setTitle('최근 3개월 안에 숨고·크몽·당근·네이버 같은 플랫폼으로 고객을 받은 적이 있나요?')
    .setRequired(true);

  // 섹션 3. 기본
  page(form, '기본');
  mc(form, '주로 하시는 일은요?', [
    '청소(입주·거주·에어컨)', '수리·설치(가전·수도·전기·조립)', '이사·운송', '과외·레슨',
    '뷰티(헤어·네일·속눈썹·피부)', '디자인·영상', '개발·IT', '사진·촬영', '인테리어·시공',
  ], true, true);
  mc(form, '이 일을 하신 지 얼마나 됐나요?', ['1년 미만', '1~3년', '3~5년', '5년 이상']);
  cb(form, '최근 3개월 안에 고객을 받는 데 쓴 곳을 모두 골라 주세요.', [
    '숨고', '크몽', '당근 비즈프로필·동네 광고', '네이버 스마트플레이스·예약·톡톡', '카카오 톡채널', '인스타그램',
    '과외 플랫폼(김과외 등)', '청소·수리 플랫폼(미소·청소연구소 등)', '지인 소개',
  ], true, true);

  // 섹션 4. 플랫폼에 쓰는 돈 (H1·H2)
  page(form, '플랫폼에 쓰는 돈');
  mc(form, '지난 한 달, 플랫폼에 쓴 돈을 다 합치면 얼마쯤인가요? 캐시·멤버십·수수료·광고비를 모두 포함합니다.', [
    '0원', '1~5만 원', '5~10만 원', '10~20만 원', '20~50만 원', '50만 원 이상', '잘 모르겠다',
  ]);
  mc(form, '그중 가장 많이 나간 곳은요?', [
    '숨고 캐시·멤버십', '크몽 수수료·광고', '당근 광고', '네이버 광고·결제 수수료', '카카오 메시지',
    '과외·청소 플랫폼 수수료', '기타', '쓴 돈이 없다',
  ]);
  mc(form, '숨고를 쓰신다면, 지난달 보낸 견적은 몇 건인가요?', ['숨고 안 씀', '1~5건', '6~20건', '21~50건', '51건 이상']);
  mc(form, '숨고를 쓰신다면, 그중 성사된 건 몇 건인가요?', ['숨고 안 씀', '0건', '1~2건', '3~5건', '6~10건', '11건 이상']);
  mc(form, '숨고 멤버십(성장 플랜)은요?', ['숨고 안 씀', '쓰고 있다', '썼다가 끊었다', '쓴 적 없다', '뭔지 모른다']);
  mc(form, '플랫폼에 낸 돈 중 "성사도 안 됐는데 날렸다"고 느끼는 비율은요?', ['거의 없다', '10% 안팎', '30% 안팎', '절반 이상', '모르겠다']);
  mc(form, '가장 아까웠던 돈은 어떤 것이었나요?', [
    '고객이 열람만 하고 답 없는 견적', '가격만 묻고 사라진 요청', '광고 클릭만 되고 문의 없음', '거래 수수료', '멤버십·구독료',
  ], false, true);

  // 섹션 5. 다시 찾아오는 고객 (H3)
  page(form, '다시 찾아오는 고객');
  mc(form, '최근 3개월 거래 중 "전에 한 번 이상 거래했던 고객"은 얼마나 되나요?', ['거의 없다', '10~30%', '30~50%', '절반 이상', '모르겠다']);
  cb(form, '다시 찾는 고객은 보통 어떻게 연락해 오나요? 모두 골라 주세요.', [
    '플랫폼에서 다시 요청·주문한다', '개인 카톡', '카카오 톡채널', '전화·문자', '당근 채팅·단골', '네이버 예약·톡톡', '인스타 DM',
    '재거래 고객이 거의 없다',
  ]);
  cb(form, '한 번 거래한 고객의 연락처와 거래 이력은 어디에 있나요? 모두 골라 주세요.', [
    '따로 안 남긴다(기억·대화창)', '휴대폰 연락처', '카톡 친구·채팅방', '엑셀·구글 시트·메모 앱',
    '네이버 예약·당근 비즈프로필의 고객 목록', '예약·고객관리 앱(이름은 기타에 적어 주세요)',
  ], true, true);
  mc(form, '최근 3개월, 고객에게 먼저 연락해서 다시 일을 받은 적이 있나요?', ['없다', '1~2번', '매달 있다', '주기를 정해 두고 한다(에어컨 1년 등)']);
  cb(form, '재거래 고객과 일하며 겪은 일을 모두 골라 주세요.', [
    '전 견적·가격이 안 남아 다시 흥정했다', '추가금·수정 범위로 다퉜다', '노쇼·당일 취소', '입금 확인을 놓쳤다',
    '문의 답이 늦어 놓쳤다', '전에 보낸 파일·사진을 못 찾았다', '특별히 없다',
  ]);

  // 섹션 6. 도구와 지불 (H4·H5)
  page(form, '도구와 지불');
  cb(form, '지금 돈 내고 쓰는 도구가 있나요? 모두 골라 주세요.', [
    '없다', '예약·고객관리 앱(이름은 기타에 적어 주세요)', '회계·세금(캐시노트·삼쩜삼 등)', '견적서·전자계약',
    '메시지 발송(알림톡 등)', '디자인·편집 도구',
  ], true, true);
  form.addTextItem().setTitle('플랫폼이나 도구를 쓰며 가장 불편한 것 하나만 적어 주세요.').setRequired(false);
  mc(form, '다음 중 월 1~3만 원을 내고라도 해결하고 싶은 것 하나만 골라 주세요.', [
    '거래한 고객 명단이 저절로 정리되고 재방문 시기에 알려 주는 것',
    '견적서·추가금 확정·전후 사진이 남는 거래 기록',
    '예약금 받기·노쇼 방지',
    '숨고·당근·네이버·카톡 문의를 한 화면에서 보는 것',
    '캐시·광고비가 어디서 새는지 보여 주는 것',
    '후기 요청·관리',
    '돈 내고 해결할 것은 없다',
  ]);
  mc(form, '방금 고른 것을 지금 월 2만 원에 쓸 수 있다면요?', ['바로 쓴다', '한 달 무료로 써 보고 정한다', '안 쓴다', '위에서 "없다"를 골랐다']);
  form.addTextItem().setTitle('"안 쓴다"면 이유를 한 줄만 적어 주세요.').setRequired(false);

  // 섹션 7. 마무리
  page(form, '마무리');
  mc(form, '15분 전화 인터뷰(1만 원 기프티콘 추가)에 응해 주실 수 있나요?', ['가능하다', '어렵다']);
  form
    .addTextItem()
    .setTitle('기프티콘·인터뷰 연락을 받을 휴대폰 번호')
    .setHelpText('숫자만 적어 주세요. 예) 01012345678')
    .setRequired(true)
    .setValidation(
      FormApp.createTextValidation().setHelpText('01로 시작하는 숫자 10~11자리로 적어 주세요.').requireTextMatchesPattern('^01[0-9]{8,9}$').build()
    );
  cb(form, '전화번호를 기프티콘·인터뷰 연락에만 쓰고 발송 뒤 지우는 데 동의합니다.', ['동의한다']);
  form.addParagraphTextItem().setTitle('하고 싶은 말').setRequired(false);

  // 섹션 8. 종료(자격 밖). 마무리 페이지에서 순서대로 넘어오면 제출, Q1·Q2 분기로 오면 이 페이지를 보고 제출.
  const endPage = page(
    form,
    '응답 종료',
    '응답해 주셔서 감사합니다. 이번 설문은 혼자 또는 1~2명과 일하며 최근 3개월 안에 플랫폼을 쓰신 분이 대상이라 여기서 마칩니다.'
  ).setGoToPage(FormApp.PageNavigationType.SUBMIT);

  q1.setChoices([
    q1.createChoice('혼자 한다', CONTINUE),
    q1.createChoice('직원·동업자 1~2명과 한다', CONTINUE),
    q1.createChoice('3명 이상과 한다', endPage),
    q1.createChoice('직장에 다니며 부업으로 한다', CONTINUE),
  ]);
  q2.setChoices([q2.createChoice('있다', CONTINUE), q2.createChoice('없다', endPage)]);

  Logger.log('편집: ' + form.getEditUrl());
  Logger.log('응답: ' + form.getPublishedUrl());
}

function page(form, title, help) {
  const p = form.addPageBreakItem().setTitle(title);
  if (help) p.setHelpText(help);
  return p;
}

function mc(form, title, values, required = true, other = false) {
  const it = form.addMultipleChoiceItem().setTitle(title).setRequired(required);
  it.setChoices(values.map((v) => it.createChoice(v)));
  if (other) it.showOtherOption(true);
  return it;
}

function cb(form, title, values, required = true, other = false) {
  const it = form.addCheckboxItem().setTitle(title).setRequired(required).setChoiceValues(values);
  if (other) it.showOtherOption(true);
  return it;
}

// 배포 뒤 추가(11/9): 응답이 어느 채널에서 왔는지 묻는 문항을 마무리 섹션 끝에 넣는다. 이미 있으면 건너뛴다.
function addSource() {
  const form = FormApp.openById('1jkFe02qO1n-6R7qmY6ULJ1xAIYDasxHAqC_a5QFZbY4');
  const title = '이 설문을 어디서 보셨나요?';
  if (form.getItems().some((i) => i.getTitle() === title)) { Logger.log('이미 있음'); return; }
  const it = form.addMultipleChoiceItem().setTitle(title).setRequired(true);
  it.setChoices(['아프니까 사장이다', '만렙사장', '청소동우회', '공부방·과외 카페', '뷰티 카페(뷰앤잡·맨사 등)', '카카오 오픈채팅', '디스콰이엇·OKKY', '지인 소개'].map((v) => it.createChoice(v)));
  it.showOtherOption(true);
  const end = form.getItems().filter((i) => i.getType() === FormApp.ItemType.PAGE_BREAK).pop(); // 마지막 페이지 나누기 = 응답 종료
  form.moveItem(it.getIndex(), end.getIndex());
  Logger.log('추가 위치 ' + it.getIndex() + ' / 전체 ' + form.getItems().length);
}

// 11/10 추가: 고충 섹션(플랫폼 섹션 앞), 기본 섹션 문항 3개, Q2 종료 분기 해제. 이미 있으면 건너뛴다.
function addPain() {
  const form = FormApp.openById('1jkFe02qO1n-6R7qmY6ULJ1xAIYDasxHAqC_a5QFZbY4');
  const G1 = '요즘 일하면서 가장 힘든 것을 3개까지 골라 주세요.';
  if (form.getItems().some((i) => i.getTitle() === G1)) { Logger.log('이미 있음'); return; }
  const find = (prefix) => form.getItems().find((i) => i.getTitle().indexOf(prefix) === 0);
  const PAINS = ['새 손님 구하기·일감 부족', '견적 흥정·저가 경쟁', '진상·추가 요구·결과 분쟁', '노쇼·당일 취소', '미수금·입금 지연', '후기·리뷰 관리',
    '광고·홍보를 어떻게 할지', '플랫폼 수수료·광고비', '다시 찾는 손님 관리', '세금·서류', '체력·멘탈·쉬는 날', '일손 구하기'];
  let p = find('플랫폼에 쓰는 돈').getIndex();
  const put = (it) => { form.moveItem(it.getIndex(), p); p += 1; return it; };

  // 기본 섹션 끝에 3문항
  const a1 = form.addMultipleChoiceItem().setTitle('손님이 가장 많이 오는 경로 하나만 골라 주세요.').setRequired(true);
  a1.setChoices(['숨고·크몽 같은 매칭 플랫폼', '소개·단골', '네이버 검색·블로그·플레이스', '당근', '인스타그램', '전단·현수막·오프라인'].map((v) => a1.createChoice(v)));
  a1.showOtherOption(true); put(a1);
  const a2 = form.addMultipleChoiceItem().setTitle('한 달에 거래(작업·수업·시술)는 몇 건쯤 하시나요?').setRequired(true);
  a2.setChoices(['10건 미만', '10~30건', '30~60건', '60~100건', '100건 이상'].map((v) => a2.createChoice(v))); put(a2);
  const a3 = form.addMultipleChoiceItem().setTitle('거래 1건의 평균 금액은 얼마쯤인가요?').setRequired(true);
  a3.setChoices(['3만 원 미만', '3~10만 원', '10~30만 원', '30~100만 원', '100만 원 이상'].map((v) => a3.createChoice(v))); put(a3);

  // 고충 섹션
  put(form.addPageBreakItem().setTitle('요즘 가장 힘든 것'));
  const g1 = form.addCheckboxItem().setTitle(G1).setRequired(true).setChoiceValues(PAINS);
  g1.showOtherOption(true);
  g1.setValidation(FormApp.createCheckboxValidation().setHelpText('3개까지만 골라 주세요.').requireSelectAtMost(3).build());
  put(g1);
  const g2 = form.addMultipleChoiceItem().setTitle('그중 하나만 해결된다면 무엇인가요?').setRequired(true);
  g2.setChoices(PAINS.map((v) => g2.createChoice(v))); g2.showOtherOption(true); put(g2);
  put(form.addTextItem().setTitle('지난 한 달 가장 힘들었던 일을 한 줄로 적어 주세요.').setRequired(false));

  // Q2: 플랫폼을 안 써도 계속 진행
  const C = FormApp.PageNavigationType.CONTINUE;
  const q2 = find('최근 3개월 안에 숨고').asMultipleChoiceItem();
  q2.setChoices([q2.createChoice('있다', C), q2.createChoice('없다', C)]);
  const q11 = find('플랫폼에 낸 돈 중').asMultipleChoiceItem();
  q11.setChoices(['거의 없다', '10% 안팎', '30% 안팎', '절반 이상', '모르겠다', '플랫폼을 안 쓴다'].map((v) => q11.createChoice(v)));

  // 안내문·종료 문구에서 플랫폼 조건 제거
  form.setDescription(form.getDescription().replace('혼자(또는 1~2명과) 일하고 최근 3개월 안에 플랫폼으로 고객을 받으신 분이', '혼자(또는 1~2명과) 일하시는 분이')
    .replace('숨고·크몽·당근 같은 플랫폼을 어떻게 쓰시는지, 한 번 거래한 고객과 다시 어떻게 연결되는지', '일하시면서 무엇이 가장 힘든지, 손님을 어떻게 받고 다시 만나시는지'));
  find('응답 종료').asPageBreakItem().setHelpText('응답해 주셔서 감사합니다. 이번 설문은 혼자 또는 1~2명과 일하시는 분이 대상이라 여기서 마칩니다.');
  Logger.log('완료. 전체 항목 ' + form.getItems().length);
}
