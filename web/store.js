// The whole session lives in sessionStorage: survives a refresh, gone when the tab closes.
const KEY = 'tippingPoint.session';
export const FIRST_QUESTION = 'Why does this decision matter to you right now?';

function fresh() {
  return {
    step: 'framing',
    decision: '',
    options: [
      { id: 'A', name: '' },
      { id: 'B', name: '' },
      { id: 'W', name: 'Wait / neither' },
    ],
    turns: [],
    currentQuestion: FIRST_QUESTION,
    draft: '',
    statements: [],
    themes: [],
    liveCells: [],
    askedQuestions: [],
    skipIndex: 0,
    nextStatementNumber: 1,
    values: [],
    nextValueNumber: 1,
    valuesFetched: false,
    cells: [],
    scoresFetched: false,
    futures: [],
    futuresFetched: false,
    exampleMode: false,
    crisis: false,
  };
}

function load() {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (raw) return Object.assign(fresh(), JSON.parse(raw));
  } catch { /* storage unavailable: start fresh */ }
  return fresh();
}

export let state = load();

export function save() {
  try { sessionStorage.setItem(KEY, JSON.stringify(state)); } catch { /* ignore */ }
}

export function startOver() {
  state = fresh();
  try { sessionStorage.removeItem(KEY); } catch { /* ignore */ }
}

export const activeStatements = () => state.statements.filter((s) => !s.removed);
