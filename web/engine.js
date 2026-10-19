// Decision engine: pure functions, no AI. Fit, dealbreakers, leader, tipping point (confidence arrives in slice 4).
export const TIE_MARGIN = 0.1;

function cellOf(cells, o, v) {
  return cells.find((c) => c.option === o && c.value === v);
}
const known = (c) => c && c.score != null;

// Per-option fit. status: 'ok' | 'ruledOut' | 'unknown'
export function computeFits(options, values, cells, failAt = 3) {
  return options.map((o) => {
    let num = 0; let den = 0;
    const ruledOutBy = []; const unresolved = [];
    for (const v of values) {
      const c = cellOf(cells, o.id, v.id);
      if (v.dealbreaker) {
        if (!known(c)) unresolved.push(v.id);
        else if (c.score <= failAt) ruledOutBy.push(v.id);
      }
      if (!known(c) || !(v.weight > 0)) continue;
      num += v.weight * c.score; den += v.weight;
    }
    if (ruledOutBy.length) return { id: o.id, name: o.name, fit: 0, status: 'ruledOut', ruledOutBy, unresolved };
    if (den === 0) return { id: o.id, name: o.name, fit: null, status: 'unknown', ruledOutBy, unresolved };
    return { id: o.id, name: o.name, fit: num / den, status: 'ok', ruledOutBy, unresolved };
  });
}

// Leader, or why there is none. reason: 'allZero' | 'allRuledOut' | 'noKnown' | 'tie' | null
export function findLeader(options, values, cells, failAt = 3) {
  const fits = computeFits(options, values, cells, failAt);
  if (!values.length || values.every((v) => !(v.weight > 0))) return { fits, leader: null, reason: 'allZero' };
  if (fits.every((f) => f.status === 'ruledOut')) return { fits, leader: null, reason: 'allRuledOut' };
  const cands = fits.filter((f) => f.status === 'ok').sort((a, b) => b.fit - a.fit);
  if (!cands.length) return { fits, leader: null, reason: 'noKnown' };
  if (cands.length > 1 && cands[0].fit - cands[1].fit < TIE_MARGIN) {
    return { fits, leader: null, reason: 'tie', tied: [cands[0].id, cands[1].id] };
  }
  return { fits, leader: cands[0].id, reason: null };
}

// Nearest whole-number weight change (one value at a time) that makes a different option the single leader.
export function tippingPoint(options, values, cells, failAt = 3) {
  const base = findLeader(options, values, cells, failAt);
  if (!base.leader) return null;
  let best = null;
  for (const v of values) {
    let hit = null;
    for (let d = 1; d <= 10 && !hit; d++) {
      for (const w of [v.weight + d, v.weight - d]) {
        if (w < 0 || w > 10) continue;
        const trial = values.map((x) => (x.id === v.id ? { ...x, weight: w } : x));
        const r = findLeader(options, trial, cells, failAt);
        if (r.leader && r.leader !== base.leader) { hit = { valueId: v.id, from: v.weight, to: w, steps: d, newLeader: r.leader }; break; }
      }
    }
    if (hit && (!best || hit.steps < best.steps)) best = hit;
  }
  return best ? { ...best, leader: base.leader } : { leader: base.leader, valueId: null, steps: null };
}

export function tippingSentence(tp, options, values) {
  if (!tp) return '';
  const name = (id) => (options.find((o) => o.id === id) || {}).name;
  if (!tp.valueId) return `No single importance change flips this — ${name(tp.leader)} leads across the board.`;
  const v = values.find((x) => x.id === tp.valueId);
  const dir = tp.to > tp.from ? `more than ${tp.to - 1}/10` : `less than ${tp.to + 1}/10`;
  return `${name(tp.leader)} leads unless ${v.name} matters ${dir} — then ${name(tp.newLeader)} takes the lead.`;
}

export function compute(state, failAt = 3) {
  const { options, values, cells } = state;
  const lead = findLeader(options, values, cells, failAt);
  const tp = lead.leader ? tippingPoint(options, values, cells, failAt) : null;
  return { ...lead, tipping: tp, sentence: tippingSentence(tp, options, values) };
}

// Clarity heuristic (0–100): how well supported and how stable the picture is. Not a probability of being right.
export function confidence(options, values, cells, answered, { failAt = 3, target = 5 } = {}) {
  const active = values.filter((v) => v.weight > 0);
  const inGrid = (c) => options.some((o) => o.id === c.option) && active.some((v) => v.id === c.value);
  const total = options.length * active.length;
  const knownCount = cells.filter((c) => inGrid(c) && c.score != null).length;
  const evidence = total ? knownCount / total : 0;
  const completeness = Math.min(1, answered / target);

  const lead = findLeader(options, values, cells, failAt);
  let stability = 0; let tp = null; let control = 0;
  if (lead.leader) {
    tp = tippingPoint(options, values, cells, failAt);
    stability = tp.valueId == null ? 1 : Math.min(1, Math.max(0, (tp.steps - 1) / 4));
    let all = 0; let own = 0;
    for (const v of active) {
      const c = cells.find((x) => x.option === lead.leader && x.value === v.id);
      if (!c || c.score == null) continue;
      all += v.weight * c.score;
      if (!c.dependsOnOthers) own += v.weight * c.score;
    }
    control = all > 0 ? own / all : 1;
  }
  // A leader that looks stable on thin evidence isn't: stability and control count only as much as the evidence behind them.
  stability *= evidence;
  control *= evidence;

  const parts = { evidence, completeness, stability, control };
  const score = Math.round(100 * (0.3 * evidence + 0.2 * completeness + 0.35 * stability + 0.15 * control));
  const label = score >= 75 ? 'High' : score >= 50 ? 'Medium' : 'Low';
  const weakest = Object.keys(parts).reduce((a, b) => (parts[b] < parts[a] ? b : a));
  return { score, label, parts, weakest, raise: raiseLine(weakest, { options, active, cells, lead, tp, values }) };
}

function raiseLine(weakest, { options, active, cells, lead, tp, values }) {
  const oName = (id) => (options.find((o) => o.id === id) || {}).name;
  if (weakest === 'evidence') {
    const sorted = [...active].sort((a, b) => b.weight - a.weight);
    for (const v of sorted) {
      for (const o of options) {
        const c = cells.find((x) => x.option === o.id && x.value === v.id);
        if (!c || c.score == null) return `Telling us more about ${v.name} for ${o.name} would raise this.`;
      }
    }
    return 'Telling us more about each option would raise this.';
  }
  if (weakest === 'completeness') return 'Answering a few more questions would raise this.';
  if (weakest === 'stability') {
    if (lead.leader && tp && tp.valueId) {
      const v = values.find((x) => x.id === tp.valueId);
      return `Your options are close — how much ${v.name} really matters decides it.`;
    }
    return 'Your options are level so far — sharing what pulls you toward one would raise this.';
  }
  return `Much of ${oName(lead.leader)}'s appeal depends on other people — knowing where they stand would raise this.`;
}
