// The decision board. Built once per render; slider and score changes patch it in place so dragging stays smooth.
import { h } from './dom.js';
import { state, save, activeStatements } from './store.js';
import { post, messageFor, getSettings } from './api.js';
import { citeChips } from './cites.js';
import { compute, confidence } from './engine.js';

const ui = { busy: false, error: '', editing: new Set(), settings: { dealbreakerFail: 3, targetAnswers: 5 }, fBusy: false, fError: '' };
getSettings().then((s) => { ui.settings = s; });

const optName = (id) => (state.options.find((o) => o.id === id) || {}).name;
const valName = (id) => (state.values.find((v) => v.id === id) || {}).name;
const cellOf = (o, v) => state.cells.find((c) => c.option === o && c.value === v);

async function fetchScores(go) {
  ui.busy = true; ui.error = ''; go();
  try {
    const res = await post('/api/scores', {
      options: state.options.map(({ id, name }) => ({ id, name })),
      values: state.values.map(({ id, name }) => ({ id, name: name.trim() })),
      statements: activeStatements().map(({ id, title, text }) => ({ id, title, text })),
    });
    if (res.crisis) { state.crisis = true; save(); ui.busy = false; go(); return; }
    state.cells = res.cells.map((c) => ({
      option: c.option, value: c.value, score: c.score, suggested: c.score, reason: c.reason, cites: c.cites,
      dependsOnOthers: c.depends_on_others, insufficient: c.insufficient, adjusted: false,
    }));
    state.scoresFetched = true;
    save();
  } catch (err) {
    ui.error = messageFor(err);
  }
  ui.busy = false;
  go();
}

async function fetchFutures(go) {
  ui.fBusy = true; ui.fError = '';
  try {
    const res = await post('/api/futures', {
      options: state.options.map(({ id, name }) => ({ id, name })),
      statements: activeStatements().map(({ id, title, text }) => ({ id, title, text })),
    });
    if (res.crisis) { state.crisis = true; save(); ui.fBusy = false; go(); return; }
    state.futures = res.cards;
    state.futuresFetched = true;
    save();
  } catch (err) {
    ui.fError = messageFor(err);
  }
  ui.fBusy = false;
  go();
}

function futuresView(go) {
  let body;
  if (!state.futuresFetched) {
    if (!ui.fBusy && !ui.fError) queueMicrotask(() => fetchFutures(go));
    body = ui.fError
      ? h('div', {}, h('p', { class: 'error', role: 'alert' }, ui.fError), h('button', { class: 'secondary', type: 'button', onclick: () => fetchFutures(go) }, 'Try again'))
      : h('p', { class: 'muted' }, 'Picturing each option from your own words…');
    return body;
  }
  return h('div', { class: 'future-cards' }, state.options.map((o) => {
    const card = state.futures.find((c) => c.option === o.id) || { sentences: [] };
    return h('article', { class: 'future-card' },
      h('h3', {}, o.name),
      card.sentences.length
        ? card.sentences.map((snt, i) => h('div', { class: 'future-line' }, h('p', {}, snt.text), citeChips(`fut-${o.id}-${i}`, snt.cites)))
        : h('p', { class: 'muted' }, 'Not enough from you yet to picture this one.'));
  }));
}

function waiting(go) {
  return h('main', { class: 'page narrow' },
    h('h1', { class: 'frame-title' }, 'Your decision board'),
    ui.error
      ? [h('p', { class: 'error', role: 'alert' }, ui.error), h('button', { class: 'primary', type: 'button', onclick: () => fetchScores(go) }, 'Try again')]
      : h('p', { class: 'lede' }, 'Scoring each option against what matters to you, using only your own words…'),
  );
}

const NO_LEADER = {
  allZero: () => 'Give at least one value some importance to compare your options.',
  noKnown: () => 'Not enough from you yet to compare these options — you can set scores yourself in the grid.',
  allRuledOut: () => 'Every option breaks at least one of your dealbreakers.',
  tie: (r) => `Too close to call between ${optName(r.tied[0])} and ${optName(r.tied[1])} — a small shift in what matters decides it.`,
};

export function boardView(go) {
  if (!state.scoresFetched) {
    if (!ui.busy && !ui.error) queueMicrotask(() => fetchScores(go));
    return waiting(go);
  }

  // ----- static structure -----
  const sentence = h('p', { class: 'tip-sentence' });
  const clarityFill = h('span', { class: 'clarity-fill' });
  const clarityNum = h('span', { class: 'clarity-num' });
  const clarityRaise = h('p', { class: 'small' });
  const clarityBox = h('section', { class: 'panel clarity-panel' },
    h('h2', {}, 'Clarity'),
    h('div', { class: 'clarity-head' }, h('span', { class: 'clarity-track', 'aria-hidden': 'true' }, clarityFill), clarityNum),
    clarityRaise,
    h('p', { class: 'muted small' }, 'A heuristic for how well supported and how steady this board is — not the chance that any choice is right.'));
  const tipHint = h('p', { class: 'tip-hint muted small' });
  const cards = state.options.map((o) => {
    const fit = h('span', { class: 'fit-num' });
    const bar = h('span', { class: 'fit-bar-fill' });
    const tag = h('p', { class: 'lead-tag' });
    const status = h('div', { class: 'card-status' });
    const el = h('article', { class: 'option-card' },
      h('h2', { class: 'option-name' }, o.name),
      h('p', { class: 'fit' }, fit, h('span', { class: 'fit-of' }, ' / 10')),
      h('span', { class: 'fit-bar', 'aria-hidden': 'true' }, bar),
      tag, status);
    return { o, el, fit, bar, tag, status };
  });

  const sliders = state.values.map((v) => {
    const num = h('output', { class: 'weight-num' }, String(v.weight));
    const range = h('input', { type: 'range', min: 0, max: 10, step: 1, value: v.weight, 'aria-label': `How much ${v.name} matters` });
    range.addEventListener('input', () => { v.weight = Number(range.value); num.textContent = range.value; save(); update(); });
    return h('li', { class: 'weight-row' },
      h('div', { class: 'weight-label' }, h('strong', {}, v.name), v.dealbreaker ? h('span', { class: 'badge' }, 'Dealbreaker') : null),
      h('div', { class: 'weight-control' }, range, num));
  });

  const cellRefs = [];
  const table = h('table', { class: 'score-grid' },
    h('thead', {}, h('tr', {}, h('th', { scope: 'col' }, 'What matters'), state.options.map((o) => h('th', { scope: 'col' }, o.name)))),
    h('tbody', {}, state.values.map((v) => h('tr', {},
      h('th', { scope: 'row' }, h('span', { class: 'row-name' }, v.name), v.dealbreaker ? h('span', { class: 'badge' }, 'Dealbreaker') : null),
      state.options.map((o) => {
        const c = cellOf(o.id, v.id);
        const td = h('td', { 'data-label': o.name });
        if (!c) return td;
        const key = `${o.id}:${v.id}`;
        const scoreBtn = h('button', { type: 'button', class: 'score-btn', title: 'Change this score' });
        const note = h('p', { class: 'cell-note muted small' });
        const range = h('input', { type: 'range', min: 0, max: 10, step: 1, value: c.score ?? 5, 'aria-label': `Score for ${o.name}, ${v.name}` });
        const editor = h('div', { class: 'cell-editor' }, range);
        editor.hidden = !ui.editing.has(key);
        scoreBtn.addEventListener('click', () => {
          if (ui.editing.has(key)) ui.editing.delete(key); else ui.editing.add(key);
          editor.hidden = !ui.editing.has(key);
          if (!editor.hidden && c.score == null) { applyScore(c, Number(range.value)); }
        });
        range.addEventListener('input', () => applyScore(c, Number(range.value)));
        td.append(...[scoreBtn,
          c.reason ? h('p', { class: 'reason' }, c.reason) : null,
          c.cites.length ? citeChips(`cell-${key}`, c.cites) : null,
          note, editor].filter(Boolean));
        cellRefs.push({ c, scoreBtn, note });
        return td;
      }),
    ))),
  );

  function applyScore(c, score) {
    c.score = score; c.insufficient = false; c.adjusted = score !== c.suggested;
    save(); update();
  }

  // ----- dynamic patch -----
  let prevLeader = state.lastLeader ?? null;
  function update() {
    const r = compute(state, ui.settings.dealbreakerFail);
    sentence.textContent = r.leader ? r.sentence : NO_LEADER[r.reason](r);
    const conf = confidence(state.options, state.values, state.cells, state.turns.length,
      { failAt: ui.settings.dealbreakerFail, target: ui.settings.targetAnswers });
    clarityFill.style.width = `${conf.score}%`;
    clarityFill.className = `clarity-fill ${conf.label.toLowerCase()}`;
    clarityNum.textContent = `${conf.score}% · ${conf.label}`;
    clarityRaise.textContent = conf.raise;
    tipHint.textContent = r.tipping && r.tipping.valueId
      ? `Drag ${valName(r.tipping.valueId)} below to see it happen.`
      : '';

    for (const card of cards) {
      const f = r.fits.find((x) => x.id === card.o.id);
      const isLead = r.leader === card.o.id;
      card.fit.textContent = f.fit == null ? '—' : f.fit.toFixed(1);
      card.bar.style.width = `${f.fit == null ? 0 : f.fit * 10}%`;
      card.el.classList.toggle('leader', isLead);
      card.el.classList.toggle('ruled-out', f.status === 'ruledOut');
      card.el.classList.toggle('unknown', f.status === 'unknown');
      card.tag.textContent = isLead ? 'Currently leading from your weights' : '';
      card.tag.hidden = !isLead;
      const lines = [];
      if (f.status === 'ruledOut') {
        for (const vid of f.ruledOutBy) {
          const c = cellOf(card.o.id, vid);
          lines.push(h('p', { class: 'status ruled' }, `Ruled out by your dealbreaker: ${valName(vid)}`));
          if (c && c.cites.length) lines.push(citeChips(`rule-${card.o.id}-${vid}`, c.cites));
          else if (c && c.adjusted) lines.push(h('p', { class: 'muted small' }, 'You set this score.'));
        }
      } else if (f.status === 'unknown') {
        lines.push(h('p', { class: 'status' }, 'Not enough from you yet to score this option.'));
      }
      for (const vid of f.status === 'ruledOut' ? [] : f.unresolved) {
        lines.push(h('p', { class: 'status unresolved' }, `Dealbreaker unresolved: ${valName(vid)} — not enough from you yet`));
      }
      card.status.replaceChildren(...lines);
      if (isLead && prevLeader && prevLeader !== r.leader) {
        card.el.classList.remove('flipped'); void card.el.offsetWidth; card.el.classList.add('flipped');
      }
    }
    if (r.leader) { prevLeader = r.leader; state.lastLeader = r.leader; }

    for (const { c, scoreBtn, note } of cellRefs) {
      scoreBtn.textContent = c.score == null ? 'Not enough from you yet' : String(c.score);
      scoreBtn.classList.toggle('empty', c.score == null);
      if (c.score == null) note.textContent = 'Tap to set a score yourself.';
      else if (c.adjusted) note.textContent = c.suggested == null ? 'You set this' : `You set this (suggested ${c.suggested})`;
      else note.textContent = '';
    }
  }

  const main = h('main', { class: 'page board' },
    h('header', { class: 'board-head' },
      h('p', { class: 'muted' }, 'Your decision board'),
      h('h1', { class: 'decision' }, state.decision)),
    h('section', { class: 'tipping', 'aria-live': 'polite' }, sentence, tipHint),
    h('section', { class: 'option-cards' }, cards.map((c) => c.el)),
    h('div', { class: 'board-grid' },
      h('div', { class: 'side-col' },
        clarityBox,
        h('section', { class: 'panel weights' }, h('h2', {}, 'How much each matters'), h('ul', { class: 'weight-list' }, sliders))),
      h('section', { class: 'panel scores' },
        h('h2', {}, 'How each option serves it'),
        h('p', { class: 'muted small' }, 'Scores are suggested from your own words — open a tag to check the source, or tap a score to change it.'),
        h('div', { class: 'grid-scroll' }, table)),
    ),
  );
  main.append(h('section', { class: 'futures' },
    h('h2', {}, 'A Tuesday, one year from now'),
    h('p', { class: 'muted small' }, 'Each picture is built only from what you said — open a tag to see which thought it rests on.'),
    futuresView(go)));
  update();
  return main;
}
