// Live picture beside the interview: themes, how her words lean so far, and clarity.
import { h } from './dom.js';
import { state, activeStatements } from './store.js';
import { findLeader, confidence } from './engine.js';

export const liveValues = () => state.themes.map((t) => ({ id: t.id, name: t.name, weight: 5, dealbreaker: false }));

export function liveClarity(settings) {
  if (!state.themes.length) return null;
  return confidence(state.options, liveValues(), state.liveCells, state.turns.length,
    { failAt: settings.dealbreakerFail, target: settings.targetAnswers });
}

function leanView(settings) {
  const values = liveValues();
  const r = findLeader(state.options, values, state.liveCells, settings.dealbreakerFail);
  const rows = r.fits.map((f) => h('li', { class: 'lean-row' + (r.leader === f.id ? ' leading' : '') },
    h('span', { class: 'lean-name' }, f.name),
    h('span', { class: 'lean-track', 'aria-hidden': 'true' }, h('span', { class: 'lean-fill', style: { width: `${f.fit == null ? 0 : f.fit * 10}%` } })),
    h('span', { class: 'lean-num' }, f.fit == null ? 'Not enough yet' : f.fit.toFixed(1)),
  ));
  let summary;
  if (!values.length || r.reason === 'noKnown' || r.reason === 'allZero') summary = 'Not enough from you yet to see a lean.';
  else if (r.reason === 'tie') summary = 'Your words are evenly balanced so far.';
  else summary = `So far your words lean toward ${state.options.find((o) => o.id === r.leader).name}.`;
  return h('section', { class: 'live-block' },
    h('h3', {}, 'How your words lean so far'),
    h('ul', { class: 'lean-list' }, rows),
    h('p', { class: 'muted small' }, summary, ' Every theme counts equally for now. Not advice.'),
  );
}

function clarityView(c) {
  return h('section', { class: 'live-block' },
    h('h3', {}, 'Clarity'),
    h('div', { class: 'clarity-head' },
      h('span', { class: 'clarity-track', 'aria-hidden': 'true' }, h('span', { class: `clarity-fill ${c.label.toLowerCase()}`, style: { width: `${c.score}%` } })),
      h('span', { class: 'clarity-num' }, `${c.score}% · ${c.label}`)),
    h('p', { class: 'small' }, c.raise),
    h('p', { class: 'muted small' }, 'How complete and steady your picture is — not a prediction of the right choice.'),
  );
}

export function liveView(settings, thoughtItem) {
  const stmts = activeStatements();
  const byId = Object.fromEntries(stmts.map((s) => [s.id, s]));
  const placed = new Set();
  const groups = state.themes.map((t) => {
    const items = t.cites.filter((id) => byId[id] && !placed.has(id)).map((id) => { placed.add(id); return byId[id]; });
    return h('div', { class: 'theme' },
      h('h4', { class: 'theme-name' }, t.name),
      items.length ? h('ul', { class: 'thought-list' }, items.map(thoughtItem)) : null);
  });
  const others = stmts.filter((s) => !placed.has(s.id));
  const c = liveClarity(settings);
  return h('div', { class: 'live' },
    c ? clarityView(c) : null,
    state.themes.length ? leanView(settings) : null,
    h('section', { class: 'live-block' },
      h('h3', {}, 'Your thoughts'),
      stmts.length
        ? h('p', { class: 'muted small' }, 'Grouped by what they\'re about. Open one to see the words it came from.')
        : h('p', { class: 'muted small' }, 'Your first answer will start this picture.'),
      groups,
      others.length ? h('div', { class: 'theme' }, h('h4', { class: 'theme-name muted' }, 'Other thoughts'), h('ul', { class: 'thought-list' }, others.map(thoughtItem))) : null,
    ),
  );
}
