// Citation chips: each opens the statement it points to. Used on the values step and the board.
import { h } from './dom.js';
import { state } from './store.js';

const open = new Set();

export function citeChips(ownerKey, ids) {
  const wrap = h('div', { class: 'cites' });
  const chips = h('span', { class: 'cite-row' });
  const detail = h('div', { class: 'cite-detail' });
  const draw = () => {
    detail.replaceChildren(...ids.filter((id) => open.has(ownerKey + id)).map((id) => {
      const s = state.statements.find((x) => x.id === id);
      if (!s) return null;
      const turn = state.turns[s.sourceTurn];
      return h('div', { class: 'cite-text' },
        h('p', {}, h('span', { class: 'sid' }, s.id), ' ', h('strong', {}, s.title), ' — ', s.text,
          s.edited ? h('span', { class: 'muted small' }, ' (edited by you)') : null),
        turn ? h('p', { class: 'cite-from' },
          `From your answer to “${turn.question}”: `,
          h('q', {}, s.quoteVerified && s.quote ? s.quote : turn.answer)) : null);
    }));
  };
  for (const id of ids) {
    const key = ownerKey + id;
    const btn = h('button', {
      type: 'button', class: 'sid chip' + (open.has(key) ? ' on' : ''), 'aria-pressed': String(open.has(key)),
      title: 'Show the thought this comes from',
    }, id);
    btn.addEventListener('click', () => {
      if (open.has(key)) open.delete(key); else open.add(key);
      btn.classList.toggle('on'); btn.setAttribute('aria-pressed', String(open.has(key)));
      draw();
    });
    chips.append(btn);
  }
  draw();
  wrap.append(chips, detail);
  return wrap;
}
