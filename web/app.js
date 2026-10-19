// Step flow: renders the current step from session state.
import { h } from './dom.js';
import { state, startOver } from './store.js';
import { framingView, interviewView, reviewView, valuesView, importanceView, supportView } from './steps.js';
import { boardView } from './board.js';

const root = document.getElementById('app');

function clearAll() { startOver(); render(); }

function header() {
  return h('header', { class: 'topbar' },
    h('span', { class: 'brand' }, 'Tipping Point'),
    state.step !== 'framing' && !state.crisis
      ? h('button', { class: 'link', type: 'button', onclick: () => { if (confirm('Start over? This clears everything in this tab.')) clearAll(); } }, 'Start over')
      : null,
  );
}

export function render() {
  let view;
  if (state.crisis) view = supportView(clearAll);
  else if (state.step === 'interview') view = interviewView(render);
  else if (state.step === 'review') view = reviewView(render);
  else if (state.step === 'values') view = valuesView(render);
  else if (state.step === 'importance') view = importanceView(render);
  else if (state.step === 'board') view = boardView(render);
  else view = framingView(render);
  root.replaceChildren(header(), view);
}

window.addEventListener('tp:render', render);
render();
