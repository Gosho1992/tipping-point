// node --test tests/engine.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { computeFits, findLeader, tippingPoint, tippingSentence } from '../web/engine.js';

const options = [{ id: 'A', name: 'Berlin' }, { id: 'B', name: 'San Francisco' }, { id: 'W', name: 'Wait / neither' }];
const mkValues = (career = 6) => [
  { id: 'V1', name: 'Career growth', weight: career, dealbreaker: false },
  { id: 'V2', name: 'Family nearby', weight: 7, dealbreaker: false },
  { id: 'V3', name: 'Income', weight: 4, dealbreaker: false },
];
const grid = { A: [3, 8, 6], B: [8, 2, 6], W: [3, 9, 3] };
const cells = Object.entries(grid).flatMap(([o, s]) => s.map((score, i) => ({ option: o, value: `V${i + 1}`, score, cites: ['S1'] })));
const withScore = (o, v, score) => cells.map((c) => (c.option === o && c.value === v ? { ...c, score } : c));

test("Ayesha's flip: Berlin leads at 6, San Francisco at 9", () => {
  assert.equal(findLeader(options, mkValues(6), cells).leader, 'A');
  assert.equal(findLeader(options, mkValues(8), cells).leader, 'A');
  assert.equal(findLeader(options, mkValues(9), cells).leader, 'B');
});

test('tipping point names career growth and the threshold', () => {
  const tp = tippingPoint(options, mkValues(6), cells);
  assert.equal(tp.valueId, 'V1'); assert.equal(tp.to, 9); assert.equal(tp.newLeader, 'B');
  assert.equal(tippingSentence(tp, options, mkValues(6)),
    'Berlin leads unless Career growth matters more than 8/10 — then San Francisco takes the lead.');
});

test('"less than" direction', () => {
  const tp = tippingPoint(options, mkValues(9), cells); // SF leads; lowering career flips back
  assert.equal(tp.leader, 'B'); assert.ok(tp.to < tp.from);
  assert.match(tippingSentence(tp, options, mkValues(9)), /matters less than \d+\/10/);
});

test('no single change flips it', () => {
  const dominant = withScore('A', 'V1', 10).map((c) => (c.option === 'A' ? { ...c, score: 10 } : c));
  const tp = tippingPoint(options, mkValues(6), dominant);
  assert.equal(tp.valueId, null);
  assert.match(tippingSentence(tp, options, mkValues(6)), /^No single importance change flips this — Berlin leads/);
});

test('all weights zero: no leader', () => {
  const vals = mkValues(0).map((v) => ({ ...v, weight: 0 }));
  const r = findLeader(options, vals, cells);
  assert.equal(r.leader, null); assert.equal(r.reason, 'allZero');
  assert.equal(tippingPoint(options, vals, cells), null);
});

test('option with all scores unknown has unknown fit and cannot lead', () => {
  const c = cells.map((x) => (x.option === 'A' ? { ...x, score: null } : x));
  const fits = computeFits(options, mkValues(6), c);
  assert.equal(fits[0].status, 'unknown'); assert.equal(fits[0].fit, null);
  assert.notEqual(findLeader(options, mkValues(6), c).leader, 'A');
});

test('no option has a known fit', () => {
  const c = cells.map((x) => ({ ...x, score: null }));
  assert.equal(findLeader(options, mkValues(6), c).reason, 'noKnown');
});

test('unknown cells are left out of the average', () => {
  const c = withScore('A', 'V3', null);
  const f = computeFits(options, mkValues(6), c)[0];
  assert.equal(f.fit, (6 * 3 + 7 * 8) / 13);
});

test('dealbreaker: score 3 rules out, 4 does not', () => {
  const vals = mkValues(6).map((v) => (v.id === 'V2' ? { ...v, dealbreaker: true } : v));
  const at3 = computeFits(options, vals, withScore('B', 'V2', 3))[1];
  assert.equal(at3.status, 'ruledOut'); assert.equal(at3.fit, 0); assert.deepEqual(at3.ruledOutBy, ['V2']);
  assert.equal(computeFits(options, vals, withScore('B', 'V2', 4))[1].status, 'ok');
});

test('dealbreaker with unknown score is unresolved, not ruled out', () => {
  const vals = mkValues(6).map((v) => (v.id === 'V2' ? { ...v, dealbreaker: true } : v));
  const f = computeFits(options, vals, withScore('A', 'V2', null))[0];
  assert.equal(f.status, 'ok'); assert.deepEqual(f.unresolved, ['V2']);
});

test('weight-0 dealbreaker still applies', () => {
  const vals = mkValues(6).map((v) => (v.id === 'V3' ? { ...v, weight: 0, dealbreaker: true } : v));
  assert.equal(computeFits(options, vals, withScore('A', 'V3', 1))[0].status, 'ruledOut');
});

test('every option ruled out: no leader', () => {
  const vals = mkValues(6).map((v) => (v.id === 'V2' ? { ...v, dealbreaker: true } : v));
  const c = cells.map((x) => (x.value === 'V2' ? { ...x, score: 2 } : x));
  const r = findLeader(options, vals, c);
  assert.equal(r.leader, null); assert.equal(r.reason, 'allRuledOut');
});

test('top two within 0.1 is a tie, not a leader', () => {
  const r = findLeader(options, mkValues(6), [
    { option: 'A', value: 'V1', score: 7 }, { option: 'B', value: 'V1', score: 7 }, { option: 'W', value: 'V1', score: 2 },
  ]);
  assert.equal(r.reason, 'tie'); assert.equal(r.leader, null);
});

import { confidence } from '../web/engine.js';

test('confidence: full evidence, 5 answers, stable leader, all own control = 100', () => {
  const dominant = cells.map((c) => (c.option === 'A' ? { ...c, score: 10 } : c));
  const r = confidence(options, mkValues(6), dominant, 5);
  assert.equal(r.parts.evidence, 1); assert.equal(r.parts.completeness, 1);
  assert.equal(r.parts.stability, 1); assert.equal(r.parts.control, 1);
  assert.equal(r.score, 100); assert.equal(r.label, 'High');
});

test('confidence: Ayesha board — tipping point 3 steps away gives stability 0.5', () => {
  const r = confidence(options, mkValues(6), cells, 5);
  assert.equal(r.parts.stability, 0.5);
  assert.equal(r.weakest, 'stability');
  assert.equal(r.raise, 'Your options are close — how much Career growth really matters decides it.');
});

test('confidence: no leader means stability and control are 0, still shown', () => {
  const r = confidence(options, mkValues(6), cells.map((c) => ({ ...c, score: null })), 2);
  assert.equal(r.parts.stability, 0); assert.equal(r.parts.control, 0); assert.equal(r.parts.evidence, 0);
  assert.equal(r.score, Math.round(100 * 0.2 * 0.4)); assert.equal(r.label, 'Low');
  assert.equal(r.weakest, 'evidence');
  assert.equal(r.raise, 'Telling us more about Family nearby for Berlin would raise this.');
});

test('confidence: completeness counts answers against the target and caps at 1', () => {
  assert.equal(confidence(options, mkValues(6), cells, 2).parts.completeness, 0.4);
  assert.equal(confidence(options, mkValues(6), cells, 9).parts.completeness, 1);
});

test('confidence: unknown cells lower evidence coverage', () => {
  const r = confidence(options, mkValues(6), withScore('W', 'V3', null), 5);
  assert.equal(r.parts.evidence, 8 / 9);
});

test('confidence: control counts the share of the leader that depends on others', () => {
  const c = cells.map((x) => (x.option === 'A' && x.value === 'V2' ? { ...x, dependsOnOthers: true } : x));
  const r = confidence(options, mkValues(6), c, 5);
  const all = 6 * 3 + 7 * 8 + 4 * 6;
  assert.equal(r.parts.control, (all - 7 * 8) / all);
});

test('confidence: thin evidence keeps clarity low even with an unflippable leader', () => {
  const thin = [
    { option: 'A', value: 'V1', score: 7, cites: ['S1'] },
    { option: 'B', value: 'V2', score: 3, cites: ['S1'] },
    { option: 'W', value: 'V1', score: 5, cites: ['S1'] },
  ];
  const vals = [{ id: 'V1', name: 'Open conversation', weight: 5 }, { id: 'V2', name: 'Feeling valued', weight: 5 }];
  const r = confidence(options, vals, thin, 1);
  assert.equal(r.parts.evidence, 0.5);
  assert.ok(r.parts.stability <= 0.5 && r.parts.control <= 0.5);
  assert.equal(r.label, 'Low');
});
