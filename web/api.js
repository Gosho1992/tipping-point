// Calls to the server. Errors carry a code the page turns into a plain message.
export class ApiError extends Error {
  constructor(code, status = 0) { super(code); this.code = code; this.status = status; }
}

function visitorId() {
  try {
    let id = localStorage.getItem('tippingPoint.visitor');
    if (!id) { id = crypto.randomUUID(); localStorage.setItem('tippingPoint.visitor', id); }
    return id;
  } catch { return 'anonymous'; }
}

export async function post(path, body) {
  let res;
  try {
    res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Visitor-Id': visitorId() },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError('network');
  }
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) throw new ApiError((data && data.code) || 'ai_failed', res.status);
  return data;
}

export function messageFor(err) {
  const code = err && err.code;
  if (code && code.startsWith('limit_')) return "You've reached today's limit — come back tomorrow. Everything you've written is still here.";
  if (code === 'too_large') return "That's longer than Tipping Point can take in one go. Please shorten it and send again.";
  if (code === 'network') return "Couldn't reach Tipping Point. Check your connection, then try again.";
  return 'Something went wrong — Try again.';
}

let settingsPromise = null;
export function getSettings() {
  if (!settingsPromise) {
    settingsPromise = fetch('/api/config').then((r) => r.json()).catch(() => ({}))
      .then((s) => ({ dealbreakerFail: 3, targetAnswers: 5, ...s }));
  }
  return settingsPromise;
}


// Translate a reviewed voice transcript through the server; the API key stays server-side.
export async function translateText(text, language) {
  return post('/api/translate', { text, language });
}
