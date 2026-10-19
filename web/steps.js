// Screens before the board: framing, interview, review, and the support screen.
import { h } from './dom.js';
import { state, save, activeStatements } from './store.js';
import { post, translateText, messageFor, getSettings } from './api.js';
import { liveView, liveClarity } from './live.js';
import { citeChips } from './cites.js';
import { EXAMPLE } from './example.js';

const ui = { busy: false, error: '', open: null, settings: { dealbreakerFail: 3, targetAnswers: 5 } };
getSettings().then((st) => { ui.settings = st; window.dispatchEvent(new Event('tp:render')); });

const optionNames = () => state.options.slice(0, 2).map((o) => o.name.trim());

// ---------- Framing ----------
export function framingView(go) {
  const decision = h('textarea', {
    id: 'decision', rows: 3, maxlength: 500, value: state.decision,
    placeholder: 'Should I take the job in Berlin or the one in San Francisco?',
  });
  const optA = h('input', { id: 'optA', maxlength: 80, value: state.options[0].name, placeholder: 'Berlin', autocomplete: 'off' });
  const optB = h('input', { id: 'optB', maxlength: 80, value: state.options[1].name, placeholder: 'San Francisco', autocomplete: 'off' });
  const start = h('button', { class: 'primary frame-start', type: 'submit' }, 'Let’s find the tipping point');

  const speechLang = h('select', { class: 'voice-language frame-language', 'aria-label': 'Choose the language you will speak' },
    ...[
      ['en-US', 'English'], ['ur-PK', 'Urdu'], ['hi-IN', 'Hindi'],
      ['ar-SA', 'Arabic'], ['es-ES', 'Spanish'], ['fr-FR', 'French'],
      ['de-DE', 'German'], ['zh-CN', 'Chinese'], ['bn-BD', 'Bengali'],
      ['pa-IN', 'Punjabi'], ['tr-TR', 'Turkish'], ['id-ID', 'Indonesian']
    ].map(([value, label]) => h('option', { value }, label))
  );
  const micButton = h('button', { class: 'secondary frame-mic', type: 'button' }, '🎙 Speak your decision');
  const micStatus = h('p', { class: 'voice-status muted small frame-mic-status', role: 'status', 'aria-live': 'polite' },
    'Prefer speaking? Choose a language and tell us what you’re deciding.');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  if (!SpeechRecognition) {
    micButton.disabled = true;
    micStatus.textContent = 'Voice input is not supported by this browser. You can still type your decision.';
  }
  micButton.addEventListener('click', () => {
    if (!SpeechRecognition) return;
    if (recognition) { try { recognition.stop(); } catch {} recognition = null; }
    recognition = new SpeechRecognition();
    recognition.lang = speechLang.value;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    micButton.disabled = true;
    micStatus.textContent = 'Listening… speak now, and allow microphone access if prompted.';
    recognition.onresult = (event) => {
      const spoken = Array.from(event.results).map((r) => r[0]?.transcript || '').join(' ').trim();
      if (spoken) {
        decision.value = spoken;
        decision.dispatchEvent(new Event('input', { bubbles: true }));
        micStatus.textContent = 'Added your spoken decision. Please check the wording and fill in both options below.';
      } else micStatus.textContent = 'No speech was recognized. Try again or type your decision.';
    };
    recognition.onerror = (event) => {
      micStatus.textContent = event.error === 'not-allowed'
        ? 'Microphone permission was denied. Allow it in Chrome site settings, or type your decision.'
        : `Voice input failed (${event.error}). Try again or type your decision.`;
    };
    recognition.onend = () => { micButton.disabled = false; recognition = null; };
    try { recognition.start(); }
    catch { micButton.disabled = false; micStatus.textContent = 'Could not start the microphone. Try again or type your decision.'; }
  });

  const sync = () => {
    state.decision = decision.value;
    state.options[0].name = optA.value;
    state.options[1].name = optB.value;
    save();
    start.disabled = !(decision.value.trim() && optA.value.trim() && optB.value.trim());
  };
  [decision, optA, optB].forEach((el) => el.addEventListener('input', sync));
  sync();

  const form = h('form', {
    class: 'frame',
    onsubmit: (e) => {
      e.preventDefault();
      if (start.disabled) return;
      state.decision = state.decision.trim();
      state.options[0].name = optA.value.trim();
      state.options[1].name = optB.value.trim();
      state.step = 'interview';
      save();
      go();
    },
  },
    h('div', { class: 'frame-eyebrow' }, 'A little clarity starts here'),
    h('h1', { class: 'frame-title' }, 'At a crossroads? Let’s untangle it.'),
    h('p', { class: 'example-link' },
      h('button', {
        class: 'link', type: 'button',
        onclick: () => {
          state.decision = EXAMPLE.decision;
          state.options[0].name = EXAMPLE.options[0];
          state.options[1].name = EXAMPLE.options[1];
          state.exampleMode = true;
          save(); go();
        },
      }, 'Try Ayesha’s example'),
      ' — a career choice you can explore yourself.'),
    h('p', { class: 'lede' }, 'Put the decision into your own words. We’ll help you see what matters most — without choosing for you.'),
    h('label', { for: 'decision', class: 'field-label' }, 'What’s on your mind?'),
    decision,
    h('div', { class: 'frame-voice-row' }, speechLang, micButton),
    micStatus,
    h('div', { class: 'option-heading' }, 'What are the two options?'),
    h('div', { class: 'option-pair' },
      h('div', {}, h('label', { for: 'optA', class: 'field-label' }, 'Option one'), optA),
      h('span', { class: 'or', 'aria-hidden': 'true' }, 'or'),
      h('div', {}, h('label', { for: 'optB', class: 'field-label' }, 'Option two'), optB),
    ),
    h('p', { class: 'hint' }, 'You can always choose “Wait / neither” later.'),
    h('p', { class: 'notice' },
      'Your decision and answers are sent to OpenAI to generate questions and suggestions. Tipping Point doesn\'t store them — they stay in this browser tab and disappear when you close it. If you use the microphone, your browser\'s own speech service (Google, in Chrome) turns your voice into text first. ',
      h('a', { href: 'https://developers.openai.com/api/docs/guides/your-data', target: '_blank', rel: 'noopener' }, 'How OpenAI handles API data'),
    ),
    start,
  );
  return h('main', { class: 'page narrow' }, form);
}

// ---------- Interview ----------
function sourceView(s) {
  const turn = state.turns[s.sourceTurn];
  if (!turn) return h('p', { class: 'source muted' }, 'Source answer not available.');
  const answer = turn.answer;
  let body;
  const i = s.quoteVerified && s.quote ? answer.toLowerCase().indexOf(s.quote.toLowerCase()) : -1;
  if (i >= 0) {
    body = h('p', { class: 'source-answer' },
      answer.slice(0, i), h('mark', {}, answer.slice(i, i + s.quote.length)), answer.slice(i + s.quote.length));
  } else {
    body = h('p', { class: 'source-answer' }, answer);
  }
  return h('div', { class: 'source' },
    h('p', { class: 'source-q' }, 'From your answer to “', turn.question, '”'),
    body,
    s.edited ? h('p', { class: 'muted small' }, 'You edited this thought.') : null,
  );
}

export function thoughtItem(s) {
  const open = ui.open === s.id;
  return h('li', { class: 'thought' + (open ? ' open' : '') },
    h('button', {
      class: 'thought-head', type: 'button', 'aria-expanded': String(open),
      onclick: () => { ui.open = open ? null : s.id; window.dispatchEvent(new Event('tp:render')); },
    },
      h('span', { class: 'sid' }, s.id),
      h('span', { class: 'thought-body' }, h('strong', {}, s.title), h('span', {}, s.text)),
    ),
    open ? sourceView(s) : null,
  );
}

function skipQuestions() {
  const [a, b] = optionNames();
  return [
    `What would you gain if you chose ${a}?`,
    `What would you lose if you chose ${b}?`,
    `What worries you most about ${a}?`,
    `What would you gain if you chose ${b}?`,
    'What would waiting a while longer give you, or cost you?',
    'What might you regret not doing, a year from now?',
    `What would you lose if you chose ${a}?`,
    `What worries you most about ${b}?`,
  ];
}

function skip(go) {
  const pool = skipQuestions();
  const asked = new Set([...state.askedQuestions, state.currentQuestion]);
  let next = null;
  for (let k = 0; k < pool.length; k++) {
    const q = pool[(state.skipIndex + k) % pool.length];
    if (!asked.has(q)) { next = q; state.skipIndex = (state.skipIndex + k + 1) % pool.length; break; }
  }
  if (!next) { next = pool[state.skipIndex % pool.length]; state.skipIndex += 1; }
  state.askedQuestions.push(state.currentQuestion);
  state.currentQuestion = next;
  ui.error = '';
  save(); go();
}

export function interviewView(go) {
  const answer = h('textarea', { id: 'answer', rows: 5, maxlength: 1500, value: state.draft, 'aria-label': 'Your answer' });

  const count = h('span', { class: 'count muted small' }, `${state.draft.length} / 1500`);

  // Optional voice entry. Speech recognition runs in the browser; only reviewed text is sent
  // to the server for translation. Typed input remains fully available.
  const speechLang = h('select', { class: 'voice-language', 'aria-label': 'Spoken language' },
    ...[
      ['en-US', 'English'], ['ur-PK', 'Urdu'], ['hi-IN', 'Hindi'],
      ['ar-SA', 'Arabic'], ['es-ES', 'Spanish'], ['fr-FR', 'French'],
      ['de-DE', 'German'], ['zh-CN', 'Chinese'], ['bn-BD', 'Bengali'],
      ['pa-IN', 'Punjabi'], ['tr-TR', 'Turkish'], ['id-ID', 'Indonesian']
    ].map(([value, label]) => h('option', { value }, label))
  );
  const micStatus = h('p', { class: 'voice-status muted small', role: 'status', 'aria-live': 'polite' },
    'Speak in your language, then review the transcript before translating. Browser speech recognition may process audio through your browser provider; only the recognized text is sent to Tipping Point for translation.');
  const micButton = h('button', { class: 'secondary voice-mic', type: 'button' },
    '🎙 Use microphone');
  const transcript = h('textarea', {
    class: 'voice-transcript', rows: 3, maxlength: 1500,
    placeholder: 'Your recognized words will appear here…',
    'aria-label': 'Original speech transcript'
  });
  const translated = h('textarea', {
    class: 'voice-translation', rows: 3, maxlength: 1500,
    placeholder: 'English translation will appear here…',
    'aria-label': 'English translation'
  });
  const translateButton = h('button', { class: 'secondary', type: 'button' }, 'Translate to English');
  const acceptButton = h('button', { class: 'primary', type: 'button' }, 'Use this English answer');
  const voicePanel = h('section', { class: 'voice-panel', 'aria-label': 'Voice input' },
    h('div', { class: 'voice-controls' }, speechLang, micButton),
    micStatus,
    h('label', { class: 'field-label' }, 'Original transcript', transcript),
    h('div', { class: 'voice-actions' }, translateButton),
    h('label', { class: 'field-label' }, 'English translation — review and edit', translated),
    h('div', { class: 'voice-actions' }, acceptButton)
  );
  let recognition = null;
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micButton.disabled = true;
    micStatus.textContent = 'Speech recognition is not available in this browser. You can still type your answer.';
  }
  micButton.addEventListener('click', () => {
    if (!SpeechRecognition) return;
    if (recognition) { try { recognition.stop(); } catch {} recognition = null; }
    recognition = new SpeechRecognition();
    recognition.lang = speechLang.value;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    micButton.disabled = true;
    micStatus.textContent = 'Listening… Allow microphone access if your browser asks.';
    recognition.onresult = (event) => {
      const spoken = Array.from(event.results).map((r) => r[0]?.transcript || '').join(' ').trim();
      transcript.value = spoken;
      translated.value = '';
      micStatus.textContent = spoken ? 'Transcript ready. Review it, then translate to English.' : 'No speech was recognized. Try again or type your answer.';
    };
    recognition.onerror = (event) => {
      micStatus.textContent = event.error === 'not-allowed'
        ? 'Microphone permission was denied. Enable it in Chrome site settings, or type your answer.'
        : `Speech recognition failed (${event.error}). Try again or type your answer.`;
    };
    recognition.onend = () => { micButton.disabled = false; recognition = null; };
    try { recognition.start(); }
    catch { micButton.disabled = false; micStatus.textContent = 'Could not start the microphone. Try again or type your answer.'; }
  });
  translateButton.addEventListener('click', async () => {
    const original = transcript.value.trim();
    if (!original) { micStatus.textContent = 'Record or enter a transcript first.'; return; }
    translateButton.disabled = true;
    micStatus.textContent = 'Translating…';
    try {
      const result = await translateText(original, speechLang.options[speechLang.selectedIndex]?.text || speechLang.value);
      if (result.crisis) {
        state.crisis = true; save();
        window.dispatchEvent(new Event('tp:render'));
        return;
      }
      translated.value = result.translated_text || '';
      micStatus.textContent = translated.value
        ? 'Translation ready. Check that it preserves your meaning, then accept it.'
        : 'No translation returned. Edit the transcript or try again.';
    } catch (err) {
      micStatus.textContent = messageFor(err);
    } finally { translateButton.disabled = false; }
  });
  acceptButton.addEventListener('click', () => {
    const value = translated.value.trim();
    if (!value) { micStatus.textContent = 'Translate or enter the English answer first.'; return; }
    answer.value = value;
    state.draft = value;
    save();
    count.textContent = `${value.length} / 1500`;
    send.disabled = ui.busy || !value;
    micStatus.textContent = 'English answer added. You can edit it in the answer box before sending.';
    answer.focus();
  });

  const send = h('button', { class: 'primary', type: 'submit', disabled: ui.busy || !state.draft.trim() },
    ui.busy ? 'Thinking…' : ui.error ? 'Try again' : 'Send answer');
  answer.addEventListener('input', () => {
    state.draft = answer.value; save();
    count.textContent = `${answer.value.length} / 1500`;
    send.disabled = ui.busy || !answer.value.trim();
  });

  const submit = async (e) => {
    e.preventDefault();
    const text = state.draft.trim();
    if (!text || ui.busy) return;
    ui.busy = true; ui.error = ''; go();
    try {
      const res = await post('/api/turn', {
        decision: state.decision,
        options: state.options.map(({ id, name }) => ({ id, name })),
        asked: state.askedQuestions.slice(-30),
        question: state.currentQuestion,
        answer: text,
        statements: activeStatements().map(({ id, title, text: t }) => ({ id, title, text: t })),
        next_number: state.nextStatementNumber,
      });
      if (res.crisis) { state.crisis = true; save(); ui.busy = false; go(); return; }
      const turnIndex = state.turns.length;
      state.turns.push({ question: state.currentQuestion, answer: text });
      for (const st of res.statements) {
        state.statements.push({
          id: st.id, title: st.title, text: st.text,
          sourceTurn: turnIndex, quote: st.quote, quoteVerified: st.quoteVerified, edited: false, removed: false,
        });
        state.nextStatementNumber = Math.max(state.nextStatementNumber, Number(st.id.slice(1)) + 1);
      }
      state.themes = res.themes;
      state.liveCells = res.cells.map((c) => ({
        option: c.option, value: c.value, score: c.score, cites: c.cites, dependsOnOthers: c.depends_on_others,
      }));
      state.askedQuestions.push(state.currentQuestion);
      state.currentQuestion = res.next_question;
      state.draft = '';
      save();
    } catch (err) {
      ui.error = messageFor(err);
    }
    ui.busy = false;
    go();
    document.getElementById('answer')?.focus();
  };

  const [a, b] = optionNames();
  const stmts = activeStatements();
  const clarity = liveClarity(ui.settings);
  const conversation = h('section', { class: 'conversation' },
    h('h1', { class: 'decision' }, state.decision),
    h('p', { class: 'versus' }, `${a}, ${b}, or wait / neither`),
    h('form', { class: 'current', onsubmit: submit },
      h('label', { for: 'answer', class: 'q current-q' }, state.currentQuestion),
      answer,
      voicePanel,
      state.exampleMode && EXAMPLE.answers[state.turns.length]
        ? h('button', {
          class: 'example-fill', type: 'button',
          onclick: () => { state.draft = EXAMPLE.answers[state.turns.length]; save(); go(); },
        }, 'Use Ayesha\'s answer')
        : null,
      h('div', { class: 'send-row' },
        count,
        h('span', { class: 'send-actions' },
          h('button', { class: 'link', type: 'button', disabled: ui.busy, onclick: () => skip(go) }, 'Skip this question'),
          send)),
      ui.error ? h('p', { class: 'error', role: 'alert' }, ui.error) : null,
    ),
    state.turns.length
      ? h('details', { class: 'past' },
        h('summary', {}, `Your answers so far (${state.turns.length})`),
        h('ol', { class: 'turns' }, state.turns.map((t) => h('li', {}, h('p', { class: 'q' }, t.question), h('p', { class: 'a' }, t.answer)))))
      : null,
  );

  const side = h('aside', { class: 'thoughts', 'aria-label': 'Your live picture' },
    liveView(ui.settings, thoughtItem),
    clarity && clarity.label === 'Low' && stmts.length
      ? h('p', { class: 'nudge' }, 'A couple more answers would make this clearer — but you can see your result any time.')
      : null,
    h('button', {
      class: 'primary wide', type: 'button', disabled: !stmts.length || ui.busy,
      onclick: () => { state.step = 'review'; save(); go(); },
    }, 'Show my result'),
    h('p', { class: 'muted small' }, 'You decide when you\'re done.'),
  );

  return h('main', { class: 'page interview' }, conversation, side);
}

// ---------- Review ----------
export function reviewView(go) {
  const stmts = activeStatements();
  const next = h('button', { class: 'primary', type: 'button', disabled: ui.busy || !stmts.length },
    ui.busy ? 'Thinking…' : ui.error ? 'Try again' : 'Confirm what matters to me');

  next.addEventListener('click', async () => {
    const list = activeStatements().filter((s) => s.text.trim());
    if (!list.length || ui.busy) return;
    if (!state.valuesFetched) {
      const live = new Set(list.map((x) => x.id));
      const fromThemes = state.themes
        .map((t) => ({ name: t.name, cites: t.cites.filter((id) => live.has(id)) }))
        .filter((t) => t.cites.length);
      if (fromThemes.length) {
        state.values = fromThemes.map((v) => ({
          id: `V${state.nextValueNumber++}`, name: v.name, cites: v.cites, addedByUser: false, dealbreaker: false, weight: 5,
        }));
        state.valuesFetched = true; state.step = 'values'; save(); go();
        return;
      }
    } else { state.step = 'values'; save(); go(); return; }
    ui.busy = true; ui.error = ''; go();
    try {
      const res = await post('/api/values', {
        decision: state.decision,
        options: optionNames(),
        statements: list.map((s) => ({ id: s.id, title: s.title.trim() || s.text.slice(0, 40), text: s.text.trim() })),
      });
      if (res.crisis) { state.crisis = true; save(); ui.busy = false; go(); return; }
      state.values = res.values.map((v) => ({
        id: `V${state.nextValueNumber++}`, name: v.name, cites: v.cites, addedByUser: false, dealbreaker: false, weight: 5,
      }));
      state.valuesFetched = true;
      state.step = 'values';
      save();
    } catch (err) {
      ui.error = messageFor(err);
    }
    ui.busy = false;
    go();
  });

  const rows = stmts.map((s) => {
    const title = h('input', { value: s.title, maxlength: 80, 'aria-label': `Title of ${s.id}` });
    const text = h('textarea', { rows: 2, maxlength: 300, value: s.text, 'aria-label': `Text of ${s.id}` });
    const mark = () => { s.title = title.value; s.text = text.value; s.edited = true; save(); };
    title.addEventListener('input', mark);
    text.addEventListener('input', mark);
    return h('li', { class: 'review-row' },
      h('span', { class: 'sid' }, s.id),
      h('div', { class: 'review-fields' }, title, text,
        s.edited ? h('span', { class: 'muted small' }, 'Edited by you') : null),
      h('button', {
        class: 'link', type: 'button',
        onclick: () => { s.removed = true; save(); go(); },
      }, 'Remove'),
    );
  });

  return h('main', { class: 'page narrow' },
    h('h1', { class: 'frame-title' }, 'Is this what you meant?'),
    h('p', { class: 'lede' }, 'Fix any thought that misreads you, and remove any that isn\'t really yours. Everything after this is built only from what stays here.'),
    h('ul', { class: 'review-list' }, rows),
    stmts.length ? null : h('p', { class: 'muted' }, 'You\'ve removed every thought. Go back and answer another question to continue.'),
    h('div', { class: 'action-row' },
      h('button', { class: 'link', type: 'button', onclick: () => { state.step = 'interview'; save(); go(); } }, 'Keep answering'),
      next,
    ),
    ui.error ? h('p', { class: 'error', role: 'alert' }, ui.error) : null,
  );
}

// ---------- Values ----------
export function valuesView(go) {
  const addInput = h('input', { maxlength: 60, placeholder: 'Something else that matters to you', 'aria-label': 'New value' });
  const add = () => {
    const name = addInput.value.trim();
    if (!name) return;
    state.values.push({ id: `V${state.nextValueNumber++}`, name, cites: [], addedByUser: true, dealbreaker: false, weight: 5 });
    save(); go();
  };
  addInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); add(); } });

  const rows = state.values.map((v) => {
    const name = h('input', { value: v.name, maxlength: 60, class: 'value-name', 'aria-label': 'Value name' });
    name.addEventListener('input', () => { v.name = name.value; save(); });
    const deal = h('input', { type: 'checkbox', id: `deal-${v.id}`, checked: v.dealbreaker });
    deal.addEventListener('change', () => { v.dealbreaker = deal.checked; save(); go(); });
    return h('li', { class: 'value-row' + (v.dealbreaker ? ' is-deal' : '') },
      h('div', { class: 'value-main' },
        name,
        v.addedByUser ? h('p', { class: 'muted small added' }, 'Added by you') : citeChips(v.id, v.cites),
      ),
      h('div', { class: 'value-side' },
        h('label', { class: 'deal', for: `deal-${v.id}` }, deal, ' Dealbreaker'),
        h('button', { class: 'link', type: 'button', onclick: () => { state.values = state.values.filter((x) => x !== v); save(); go(); } }, 'Remove'),
      ),
    );
  });

  const ready = state.values.some((v) => v.name.trim());
  return h('main', { class: 'page narrow' },
    h('h1', { class: 'frame-title' }, 'What matters to you here'),
    h('p', { class: 'lede' }, 'These come from your own thoughts — open a tag to see which. Rename, remove, or add your own. How much each one matters comes next.'),
    state.values.length ? null : h('p', { class: 'notice' }, 'We couldn\'t find values clearly backed by your words — add your own below.'),
    h('ul', { class: 'value-list' }, rows),
    h('div', { class: 'add-row' }, addInput, h('button', { class: 'secondary', type: 'button', onclick: add }, 'Add')),
    h('p', { class: 'hint' }, 'Mark a value as a dealbreaker if any option that fails it would be unacceptable to you, no matter what else it offers.'),
    h('div', { class: 'action-row end' },
      h('button', {
        class: 'primary', type: 'button', disabled: !ready,
        onclick: () => { state.values = state.values.filter((v) => v.name.trim()); state.step = 'importance'; save(); go(); },
      }, 'Set how much each matters'),
    ),
  );
}

// ---------- Importance ----------
export function importanceView(go) {
  const rows = state.values.map((v) => {
    const out = h('output', { class: 'weight-num' }, String(v.weight));
    const slider = h('input', { type: 'range', min: 0, max: 10, step: 1, value: v.weight, 'aria-label': `How much ${v.name} matters` });
    slider.addEventListener('input', () => { v.weight = Number(slider.value); out.textContent = slider.value; save(); });
    return h('li', { class: 'weight-row' },
      h('div', { class: 'weight-label' }, h('strong', {}, v.name), v.dealbreaker ? h('span', { class: 'badge' }, 'Dealbreaker') : null),
      h('div', { class: 'weight-control' }, slider, out),
    );
  });
  return h('main', { class: 'page narrow' },
    h('h1', { class: 'frame-title' }, 'How much does each one matter?'),
    h('p', { class: 'lede' }, '0 means it doesn\'t matter for this decision; 10 means it matters more than almost anything. You can change these again on the board.'),
    h('ul', { class: 'weight-list' }, rows),
    h('div', { class: 'action-row end' },
      h('button', { class: 'primary', type: 'button', onclick: () => { state.step = 'board'; save(); go(); } }, 'See my decision board'),
    ),
  );
}

// ---------- Support (crisis) ----------
export function supportView(clear) {
  return h('main', { class: 'page narrow support' },
    h('h1', { class: 'frame-title' }, 'Let\'s pause here.'),
    h('p', { class: 'lede' }, 'It sounds like you may be going through something really hard. That matters more than any decision, and you deserve support from people who care about you.'),
    h('p', {}, 'Please talk to someone you trust — a parent, a friend, or a doctor. If you might be in danger right now, contact your local emergency number.'),
    h('p', { class: 'muted' }, 'Tipping Point has stopped here and won\'t show any decision results.'),
    h('button', { class: 'secondary', type: 'button', onclick: clear }, 'Clear my answers'),
  );
}
