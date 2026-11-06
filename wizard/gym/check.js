// 헬스장 환불 계산 점검 — artifact.html 의 계산 함수를 꺼내 예시 값으로 확인한다. 실행: node check.js
const fs = require("fs");
const assert = require("assert");
const html = fs.readFileSync(__dirname + "/artifact.html", "utf8");
const code = html.split("// calc:start")[1].split("// calc:end")[0];
const { refundCalc, periodUnits } = new Function(code + "; return { refundCalc, periodUnits };")();

// PT 30회 150만 원 중 10회 사용: 50만 원과 15만 원을 뺀다
assert.deepStrictEqual(refundCalc({ paid: 1500000, total: 30, used: 10 }), { usedAmt: 500000, penaltyAmt: 150000, refund: 850000, perUnit: 50000, gap: null });
// 업체 책임이면 위약금이 없다
assert.strictEqual(refundCalc({ paid: 1500000, total: 30, used: 10, penalty: false }).refund, 1000000);
// 거의 다 쓰면 0 아래로 내려가지 않는다
assert.strictEqual(refundCalc({ paid: 1000000, total: 10, used: 10 }).refund, 0);
assert.strictEqual(refundCalc({ paid: 1000000, total: 10, used: 12 }).usedAmt, 1000000);
// 업체 제시액과의 차이. 제시액 0 도 값으로 다룬다
assert.strictEqual(refundCalc({ paid: 1250000, total: 25, used: 5, offer: 625000 }).gap, 250000);
assert.strictEqual(refundCalc({ paid: 1250000, total: 25, used: 5, offer: 0 }).gap, 875000);
// 기간권: 2026년 365일, 3월 1일 통지면 60일을 쓴 것이다
assert.deepStrictEqual(periodUnits("2026-01-01", "2026-12-31", "2026-03-01"), { total: 365, used: 60 });
// 시작 전 통지는 이용분 0, 끝난 뒤 통지는 전체. 끝이 시작보다 앞이면 계산하지 않는다
assert.strictEqual(periodUnits("2026-01-10", "2026-02-10", "2026-01-01").used, 0);
assert.strictEqual(periodUnits("2026-01-10", "2026-02-10", "2026-05-01").used, 32);
assert.strictEqual(periodUnits("2026-02-10", "2026-01-10", "2026-01-01"), null);
// 변호사 해설 예시: 100만 원 5개월권을 1개월(약 20%) 쓰면 약 70만 원
const u = periodUnits("2026-01-01", "2026-05-31", "2026-01-30");
assert.ok(Math.abs(refundCalc({ paid: 1000000, ...u }).refund - 700000) < 5000);
console.log("계산 점검 통과");
