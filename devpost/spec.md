---
doc: spec
status: approved
---

# Tipping Point — Technical Spec

## How This Works, In Plain Language

Tipping Point has two pieces.

1. **The page (frontend)** — the six steps Ayesha moves through, written in plain HTML, CSS, and JavaScript with no build step. It keeps her work in the browser's **session storage**: a short-term notepad for one browser tab that survives an accidental refresh and is wiped when she closes the tab. All the board maths — fit scores, dealbreakers, the tipping point, and confidence — runs here, so dragging a slider updates the board instantly.
2. **The server (backend)** — a small Python FastAPI program. It holds the OpenAI key (so nobody can copy it from the page), asks OpenAI for the language work (next question, splitting answers into statements, proposing values, scoring options, writing future cards), and checks every AI answer before it reaches Ayesha. The **citation validator** removes anything that doesn't cite her statements, and every claim shows its sources so she can judge whether they really support it. The **safety check** stops the flow if her words show crisis or serious distress. The server also counts and budgets usage so strangers can't drain your OpenAI credit. It never stores or logs her words — only counts and costs.

The AI interprets her words; code enforces the rules. The AI never calculates the result and never decides anything. These guardrails **reduce** unsupported claims and make them visible; they cannot guarantee the AI never misreads her.

Her decision text and answers are sent to OpenAI to generate questions and suggestions, and the app tells her so before she starts.

Why this shape: one small server is the minimum that keeps the API key secret and the guardrails out of the browser's reach. Everything else stays in the page, so there is no database of personal data, no accounts, and the proof moment — the instant flip — never waits on the network.

## The Core Journey Through the System

PRD ref: `prd.md > The Core Journey`.

1. Ayesha opens the page → it loads from the server → session storage is empty, so she sees the welcome step, including the notice that her text goes to OpenAI.
2. She types her decision and two options → saved in session storage → the page adds `Wait / neither`.
3. The page shows a fixed first question (no AI call) → she answers → the page sends her answer and the conversation so far to `POST /api/turn` → the server checks size, runs the safety check, reserves budget, asks OpenAI for (a) the statements in her answer, each with the exact words it came from, and (b) the next question → records the cost → validates → the page numbers the new statements S1, S2…, links each to the answer it came from, and shows them in her growing collection → saved.
4. Each `/api/turn` reply also carries the live picture — themes grouping all her statements and a light score grid (options × themes, cited) — which `engine.js` turns into the lean bar and clarity bar beside the question. Steps repeat until she clicks **"Show my result"** (enabled once one statement exists). Skip swaps the question locally, with no AI call.
5. She edits or removes statements → only in the page; nothing is sent.
6. Page sends her final statements to `POST /api/values` → same server pipeline → values each citing statements; any value with missing or unknown citations is removed → she renames, removes, adds values and marks dealbreakers (page only).
7. She sets 0–10 importance for each value (page only).
8. Page sends options, values, and statements to `POST /api/scores` and `POST /api/futures` → server returns a complete score grid (cells without valid support come back as explicit "not enough from you yet" cells) and cited future-card sentences → page builds the board.
9. She drags sliders or scores → `engine.js` recalculates fit, leader, tipping point, and confidence instantly in the browser. No server call.

## Stack

- **Python 3.10+** — learner's choice; comfortable with Python and JSON.
- **FastAPI + Uvicorn** — small Python web server; also serves the page files, so only one program runs. Docs: <https://fastapi.tiangolo.com/>, <https://www.uvicorn.org/>
- **OpenAI Python SDK, Responses API with Structured Outputs** — every AI reply must match a fixed JSON shape, which makes citations checkable. Docs: <https://github.com/openai/openai-python>, <https://developers.openai.com/api/docs/guides/structured-outputs>, <https://developers.openai.com/api/docs/guides/migrate-to-responses>
- **python-dotenv** — reads settings from `.env`. Docs: <https://pypi.org/project/python-dotenv/>
- **SQLite (built into Python)** — stores usage counts and costs only. Docs: <https://docs.python.org/3/library/sqlite3.html>
- **Plain HTML / CSS / JavaScript (ES modules), no framework, no build step** — agreed tradeoff: the board maths lives in JavaScript rather than Python so the flip is instant; Streamlit was rejected because it reruns the page on every slider move.
- **Browser session storage** — learner's choice for surviving a refresh without accounts or cloud. Docs: <https://developer.mozilla.org/en-US/docs/Web/API/Window/sessionStorage>
- **Node's built-in test runner** (Node is already installed) for `engine.js` tests; **pytest** for server tests.

*Verified in slice 1:* versions pinned in `requirements.txt` (openai 3.35.1, fastapi 0.143.3); the SDK accepts `instructions`, `text` (structured output), `reasoning`, `max_output_tokens`, and `store`; the key can call `gpt-6-luna`. *Still unverified:* whether reasoning tokens count inside `max_output_tokens` (the spend reservation assumes they do).

## Where It Runs and How Someone Tries It

**Default: local, for building and recording the demo.**

1. `python -m venv .venv`
2. Windows: `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and put your OpenAI key in it.
5. `uvicorn server.main:app --no-access-log`
6. Open <http://localhost:8000>

**Public hosting: deferred to `6-ship`.** Then we compare two options: Amazon Lightsail (only if the AWS credits are confirmed to cover it) and Zain's existing Hetzner VPS. Nothing in the build depends on which one wins: it is one Python program plus a `.env` file. Behind a reverse proxy, run Uvicorn with `--proxy-headers --forwarded-allow-ips=127.0.0.1` so the per-network cap sees each visitor's real address instead of the proxy's.

**Submission requires** a demo video under 3 minutes on YouTube or Vimeo, and a public GitHub repo with an open-source licence (MIT) and the planning docs. A live URL is extra, never a replacement.

## Look and Feel

*Revised by the learner after the build — see `UI-REDESIGN.md`:* deep indigo/blue background with slow-moving gradient orbs (`body::before/::after`), translucent glass panels, violet/pink/cyan gradients on buttons, bars, and headings. Implemented as an override layer appended to `web/styles.css` (a second `:root` block); the earlier tokens below stay in the file underneath it. Ambient animation is disabled under `prefers-reduced-motion`.

Original direction:

From `prd.md > Look and Feel`: very friendly with a brainy touch; calm, evidence-led, empowering.

- **Colours** (learner's choice):
  - Background, warm cream: `#FBF6EE`. Cards: `#FFFDF8`. Borders: `#EADFD0`.
  - Highlights, soft coral: `#F2766B`, with tint `#FDE3DE` — the leader, active step, slider thumbs, the tipping-point sentence. Coral is never used for body text (too little contrast on cream).
  - Text, deep blue: `#1F2F57`. Secondary text: `#5B6785`. Primary buttons are deep blue with cream text.
- **Type:** friendly serif headings (Fraunces) for the "brainy" feel; rounded, readable sans for body (Nunito); statement IDs (S1, S2) as small monospaced chips (IBM Plex Mono) that read like footnotes. Loaded from Google Fonts with system-font fallbacks.
- **Density:** spacious and calm — one focus per step, generous whitespace, soft 12px corners, light shadows. The board is the only dense screen, organised in clear panels.
- **Copy tone:** warm, second person, plain words. Never "you should". The leader is "currently leading from your weights", never "recommended".
- Works on a laptop screen first (the demo); the board stacks into one column on narrow screens.

## Components

### Step Flow and Session Store (`web/app.js`)

Renders the current step, moves forward when she clicks Next, and saves the whole session object to session storage after every change. On load, it restores from session storage if present. Forward-only between steps (the PRD describes a forward flow); a "Start over" link clears the session.
PRD ref: `prd.md > The Core Journey`, `prd.md > Screens and Layout`, `prd.md > States and Boundaries`.

### Framing Step

Decision text plus two option names; Next is disabled until all three are filled. Adds `Wait / neither` as a third option automatically. Shows the data notice (see **Privacy and Security**).
PRD ref: `prd.md > Framing the Decision`.

### Example Entry Point ("Try Ayesha's example")

A secondary link on the framing step. It fills in Ayesha's decision and options, and on each interview turn offers a "Use Ayesha's answer" button that puts her next scripted answer into the answer box. Everything still goes through the live AI and the same guardrails; it only saves typing. The script lives in `web/example.js`. Because the AI's questions vary, a scripted answer may not match the question exactly; she can edit it before sending.

Scope check: it adds no new capability and changes no data flow — it pre-fills existing inputs. It is built **last**, after the core loop works, and is cut if time runs short.

### Interview Step

One question at a time. The first question is fixed ("Why does this decision matter to you right now?"), so the first screen costs no AI call. Each answer goes to `/api/turn` with all current statements, the questions already asked, and the next free statement number. Each returned statement carries a `quote`: the exact words from her answer it came from.

**IDs:** the AI labels new statements `N1, N2…`; the server renumbers them to `S<next>, S<next+1>…` (never reused, even after removal) and rewrites every citation to match, so the page and the AI always agree.

**Next question from the whole picture:** the AI receives all statements, the live themes and grid it just built, and every question already asked. It picks what is most missing — an option or theme with no cited evidence, an untouched fear or regret — and must not follow up on the latest answer's wording or repeat an earlier question.

**Skip:** swaps in the next unused question from a fixed local list built from her option names (gains and losses for each option, fears, regret, waiting). No AI call.

**"Show my result":** enabled once one statement exists; when live clarity is Low it shows "A couple more answers would make this clearer" above the button, never blocking.
PRD ref: `prd.md > Guided Interview`, `prd.md > Live Picture`.

### Live Picture (`web/live.js`)

Renders beside the question after every answer, from `state.themes` and `state.liveCells`:

- **Themes:** each with its statements (citation chips and titles); statements no theme cites are listed under "Other thoughts".
- **Lean bar:** one bar per option, using `engine.findLeader` with every theme at weight 5. Shows the fit as a bar plus a number, or "Not enough yet" for an unknown option. The label reads "How your words lean so far — every theme counted equally. Not advice." On a tie or with no leader, it says so.
- **Clarity bar:** `engine.confidence` with the same weights; shown as a filling bar with its label and its "what would raise it" line.

Bars animate their width when they change (respecting reduced motion). This is the only page motion besides the board flip.
PRD ref: `prd.md > Live Picture`.

**Source traceability:** clicking a statement shows "From your answer to: *[question]*" with the quoted words highlighted. The server checks that the quote really appears in that answer (ignoring case and extra spaces). If it doesn't, the statement is kept but shows her whole answer as its source instead of a quote, and the mismatch is counted for the scenario tests.
PRD ref: `prd.md > Guided Interview`, `prd.md > Statements`.

### Statement Review Step

The list of statements, each with an editable title and text and a remove button. An edited statement keeps its source link and shows "edited by you". Removed statements stay hidden and are excluded from everything sent onward, so nothing can cite them.
PRD ref: `prd.md > Statements`.

### Values Step

Pre-fills values from the live themes: each theme becomes a value (weight 5), keeping only citations to statements that are still active; a theme left with no citations is dropped. Only if that leaves no values does it call `/api/values` as a fallback. Then it shows each value with its citation chips. She can rename, remove, add (a value she adds shows "Added by you" instead of citations — her own words need no citation), and toggle a dealbreaker. Next needs at least one value.
PRD ref: `prd.md > Values and Dealbreakers`.

### Importance Step

A 0–10 integer slider per value, defaulting to 5.
PRD ref: `prd.md > Importance Weights`.

### Decision Board (`web/board.js`)

Calls `/api/scores` and `/api/futures` once on arrival, then renders four panels:

- **Options and fit:** three cards, each with its fit (0–10, one decimal) and a bar; the leader gets the coral outline and "currently leading from your weights". Status lines on a card: "Ruled out by your dealbreaker: Family nearby" (with citations), "Dealbreaker unresolved: Family nearby — not enough from you yet", or "Not enough from you yet to score this option".
- **Weights:** the importance sliders again.
- **Score grid:** every option × value cell, each with score, short reason, and citation chips, or an explicit "Not enough from you yet" cell. Clicking a cell opens a 0–10 control; an adjusted cell shows "You set this (suggested 6)". She can also give a score to a "not enough" cell; it then shows "You set this".
- **Insight strip:** the tipping-point sentence, the confidence badge with its "what would raise it" line and an info note, and the three future cards.

Every change calls `engine.compute()` and re-renders. Clicking a citation chip shows the statement and, through it, the answer it came from.
PRD ref: `prd.md > The Decision Board`, `prd.md > Citation Guardrail`.

### Decision Engine (`web/engine.js`)

Pure functions, no AI, fully unit-tested. Implements the code-calculated results in `scope.md > The POC Boundary`.

**Fit, per option**

- Weighted average of its known scores, using importance as weights. "Not enough" cells (`score: null`) and values with weight 0 are left out.
- If the option has no known score on any value with weight above 0, its fit is **unknown** (shown as "—", never as 0), and it cannot lead.

**Dealbreakers** (threshold `DEALBREAKER_FAIL = 3`)

- Score ≤ 3 on a dealbreaker value → the option is **ruled out**: fit 0, reason recorded.
- Score unknown on a dealbreaker value → the dealbreaker is **unresolved**. The option is not ruled out; its fit is computed from its other scores, and the card shows "Dealbreaker unresolved". If it leads, it is shown as "leading, with an unresolved dealbreaker".
- A dealbreaker applies regardless of its weight, including weight 0.

**Leader**

- The highest fit among options that are not ruled out and not unknown.
- If the top two are within 0.1: "Too close to call".
- **Edge cases, each with its own board message, no leader and no tipping point:**
  - **All weights are 0:** "Give at least one value some importance to compare your options."
  - **No option has a known fit:** "Not enough from you yet to compare these options — you can set scores yourself in the grid."
  - **Every option is ruled out:** "Every option breaks at least one of your dealbreakers," listing which dealbreaker each option breaks. Dealbreakers don't depend on weights, so sliders can't change this; editing a score can.

**Tipping point**

- For each value, try every other whole-number weight (0–10) with everything else held fixed. Find the nearest weight at which a **different option becomes the single leader**; a tie doesn't count as a flip.
- The value needing the smallest change is the tipping point. Sentence: "Berlin leads unless Career growth matters more than 8/10" (or "less than").
- If no single weight change flips it: "No single importance change flips this — Berlin leads across the board."
- Ruled-out and unknown options are never candidates.

**Confidence** (0–100)

A **clarity heuristic**: how well supported and how stable this board is. It is **not** the probability that any choice is right, and the badge's info note says so in plain words. Four parts:

- **Evidence coverage (30%):** share of all option × value cells (for values with weight above 0) that have a known score — backed by her statements, or set by her. "Not enough" cells lower it.
- **Completeness (20%):** questions answered ÷ `TARGET_ANSWERS` (default 5), capped at 1. She still decides when to stop; stopping early only lowers this part, never blocks her. When it is the weakest part, the raise line says "Answering a few more questions would raise this". The interview never pressures her to continue.
- **Stability (35%):** steps the tipping-point weight must move — 1 step = 0, 5 or more steps (or no flip possible) = 1, linear in between. With no leader (tie, nothing known), stability is 0. Stability and control are each multiplied by evidence coverage, because a leader that looks stable on thin evidence isn't.
- **Control (15%):** share of the leader's weighted score that doesn't depend on other people. Each cell has a `depends_on_others` flag from the AI, which must be supported by the cell's citations; unknown cells don't count.
- Labels: Low < 50, Medium 50–74, High 75+. Shown during the interview (live, every theme at weight 5) and on the board.
- The "what would raise it" line is a code template chosen from the weakest part — e.g. evidence: "Telling us more about Family nearby for San Francisco would raise this." No AI writes it.

### Server App (`server/main.py`)

FastAPI app: serves `web/` as static files and the four JSON endpoints below. Every endpoint runs, in order:

1. Size check
2. Safety check on her text
3. Budget and limit reservation
4. AI call
5. Record actual usage — **immediately on response, before any parsing or validation**
6. Parse and validate (schema, citations, quotes)
7. Safety flag check on the AI's output
8. Response

It never logs or stores her text.
PRD ref: `prd.md > States and Boundaries`.

### AI Calls (`server/ai.py`, `server/prompts.py`, `server/schemas.py`)

One function per task, each with its own instructions, strict JSON schema, `max_output_tokens`, and model from `.env`. Calls are made with `store: false` (don't keep responses on OpenAI's side for later retrieval; parameter name to verify).

Instructions shared by every task:

- Use only the listed statements, and cite statement IDs for every claim.
- Never describe what another person thinks or feels.
- Never give medical, legal, or financial direction.
- When the statements say nothing relevant, return an "insufficient" cell rather than guessing.

### Citation Validator (`server/citations.py`)

Runs on every parsed AI response. Implements `prd.md > Citation Guardrail`. **What it guarantees:** every citation shown points to a real, current statement of hers. **What it does not guarantee:** that the statement actually supports the claim. That is checked by showing the cited words on screen and by the citation support tests (see **How We Verify**).

1. Builds the set of valid IDs from the statements sent with this request (removed statements are never sent).
2. **Values:** a value with no citations, or with any unknown ID, is removed.
3. **Score cells:**
   - The grid is always complete: every option × value pair gets a cell.
   - A cell with a score but missing or unknown citations is **converted** to an insufficient cell — never silently dropped.
   - Insufficient cells look exactly like this: `{score: null, reason: "", cites: [], insufficient: true}`.
   - Scores must be whole numbers from 0 to 10; anything else becomes insufficient.
   - Cells for unknown option or value IDs are discarded, and the missing pairs are filled as insufficient.
4. **Future cards:** checked sentence by sentence; sentences without valid citations are removed. A card left empty shows "Not enough from you yet to picture this one."
5. **Statements from `/api/turn`:** the quote is checked against the source answer (see **Interview Step**).
6. Returns the cleaned response plus counts of removed, converted, and quote-mismatched items (logged as numbers only; used by the scenario tests).

### Safety Check (`server/safety.py`)

Checks every piece of her text in a request (decision, answers, statements, value names) against a list of crisis and serious-distress phrases. Each AI response schema also includes a `crisis` flag the model must set. If either fires, the server returns `{"crisis": true}` and makes no further AI calls; the page replaces the flow with the support message (talk to a parent, friends, or a doctor) and shows no decision output. Basic by design, per `scope.md > The POC Boundary`; a phrase list will miss some wording.
PRD ref: `prd.md > Safety Check`.

### Usage Limits and Spend Protection (`server/limits.py`)

All caps are set in `.env`:

- Per visitor: 45 AI calls/day (≈3 sessions). Visitor = a random ID the page keeps in local storage (an ID only, never her content).
- Per network: 90 calls/day, keyed by a salted hash of the IP address (the raw IP is never stored) — a backstop if the visitor ID is cleared.
- Global: 1,500 calls/day (≈100 sessions).
- Spend: `DAILY_SPEND_CAP_USD` ($1 public; higher locally while building).

**How spend is protected:**

1. **Bounded requests.** Each task has a `max_output_tokens` cap, and request bodies are size-limited. Together these set a worst-case cost for every call.
2. **Atomic reservation before the call.** In one SQLite `BEGIN IMMEDIATE` transaction, the server works out the worst-case cost (estimated input tokens × input price + `max_output_tokens` × output price) and checks every cap: calls for this visitor, this network and overall, and today's spend plus open reservations plus this estimate. If all pass, it records the call and a reservation in that same transaction. Two simultaneous requests can never both squeeze under the cap.
3. **Record immediately on response.** As soon as OpenAI replies, the reservation is replaced with the actual cost, computed from the response's token usage at full input price (no cached-input discount, so it errs high). This happens before parsing or validation, so a reply that later fails validation is still counted.
4. **Failures:**
   - If the request may have reached OpenAI (timeout, server error, broken connection mid-request), the full reservation stays as spent, the conservative choice.
   - If it clearly never reached OpenAI (connection refused, rejected key), the reservation is released.
5. **Reset:** counts and spend reset at UTC midnight. Stored in `server/usage.db`.
6. **When a cap is hit:** HTTP 429 with a code. The page shows "You've reached today's limit — come back tomorrow" and keeps all her work on screen.

**This cap is best-effort, not a guarantee.**

- It sees only this app's calls.
- Its prices are copies in `.env` that can go stale.
- Token estimates can differ from OpenAI's invoice.

The hard backstop is outside the code: a **dedicated OpenAI project and key for Tipping Point**, with its own budget limit and alerts in the dashboard (check whether your account's limit is a hard stop). Docs: <https://developers.openai.com/api/docs/guides/spend-limits>

### Voice Input (in `web/steps.js`, endpoint in `server/main.py`)

Added by the learner after the build. Implements `prd.md > Voice Input`.

- Uses the browser's built-in speech recognition (`SpeechRecognition` / `webkitSpeechRecognition`) with the language she picks; in Chrome, audio is processed by the browser's speech service (Google), not by Tipping Point. Unsupported browsers or a refused microphone fall back to typing with a plain message.
- Framing step: the spoken text fills the decision box directly for her to check.
- Interview: transcript (editable) → **Translate to English** calls `POST /api/translate` → English (editable) → **Use this English answer** puts it into the answer box; she still sends it herself.
- `/api/translate` runs the same pipeline as every AI endpoint: size limit, phrase-based crisis check on the transcript, budget reservation and cost recording (using the `turn` model and output cap), the model's crisis flag, and a phrase check on the translation.

### Privacy and Security

- **Data notice** (framing step, always visible before her first answer): "Your decision and answers are sent to OpenAI to generate questions and suggestions. Tipping Point doesn't store them — they stay in this browser tab and disappear when you close it. If you use the microphone, your browser's own speech service (Google, in Chrome) turns your voice into text first." Plus a link to OpenAI's data-use page (<https://developers.openai.com/api/docs/guides/your-data>).
- **No logging of request bodies.** Uvicorn runs with access logs off. App logs contain only the endpoint, status, latency, token counts, cost, and validator counts — never her text, never the AI's text.
- **Safe rendering.** All text from her or from the AI is inserted with `textContent` (never `innerHTML`), so nothing she or the AI writes can run as code. A basic Content-Security-Policy header allows scripts only from the site itself and fonts from Google Fonts.
- **Size limits (kept):**
  - request body 64 KB
  - answer 1,500 characters
  - statement title 80 / text 300 characters
  - value name 60 characters
  - at most 40 statements and 10 values per request

  Anything over a limit gets HTTP 413; the page also enforces the limits on input.
- **Secrets:** the key lives only in the server's `.env`, which is gitignored. `.env.example` has no real values.
- **Same-origin only:** no CORS headers, so other websites can't call the API from a browser.

## API Endpoints

All `POST`, JSON in and out, stateless — the page sends what each call needs.

| Endpoint | Sends | Returns (after validation) |
|---|---|---|
| `/api/turn` | decision, options, questions asked so far, current question, latest answer, current statements, next statement number | `{ statements: [{id, title, text, quote, quoteVerified}], themes: [{id, name, cites}], cells: [{option, value (theme id), score or null, cites, depends_on_others, insufficient}], next_question, crisis }` — the grid is always complete for the themes kept |
| `/api/values` | decision, options, statements | `{ values: [{name, cites}], crisis }` |
| `/api/scores` | options, values, statements | `{ cells: [{option, value, score or null, reason, cites, depends_on_others, insufficient}], crisis }` — always the complete grid |
| `/api/futures` | options, statements | `{ cards: [{option, sentences: [{text, cites}]}], crisis }` |
| `/api/translate` | text (≤1,500 chars), language name | `{ translated_text, crisis }` |

Errors: `429 {code: "limit_visitor" | "limit_network" | "limit_global" | "limit_budget"}`, `502 {code: "ai_failed"}`, `413 {code: "too_large"}`.

## Data Model

**In the page (session storage, key `tippingPoint.session`):**

```json
{
  "step": "framing | interview | review | values | importance | board",
  "decision": "Should I move to Berlin or San Francisco?",
  "options": [{"id": "A", "name": "Berlin"}, {"id": "B", "name": "San Francisco"}, {"id": "W", "name": "Wait / neither"}],
  "turns": [{"question": "...", "answer": "..."}],
  "statements": [{"id": "S1", "title": "Career growth", "text": "...", "sourceTurn": 0, "quote": "...", "quoteVerified": true, "edited": false, "removed": false}],
  "themes": [{"id": "T1", "name": "Career growth", "cites": ["S1"]}],
  "liveCells": [{"option": "A", "value": "T1", "score": 7, "cites": ["S1"], "dependsOnOthers": false}],
  "askedQuestions": ["..."],
  "nextStatementNumber": 3,
  "values": [{"id": "V1", "name": "Family nearby", "cites": ["S2"], "addedByUser": false, "dealbreaker": false, "weight": 5}],
  "cells": [{"option": "A", "value": "V1", "score": 6, "suggested": 6, "reason": "...", "cites": ["S2"], "dependsOnOthers": false, "insufficient": false, "adjusted": false}],
  "futures": [{"option": "A", "sentences": [{"text": "...", "cites": ["S1"]}]}],
  "exampleMode": false
}
```

- **Updated:** after every action. **Refresh:** restored. **Tab closed:** gone (learner's choice: don't keep sensitive personal data longer than needed).
- **Visitor ID:** local storage `tippingPoint.visitor` — a random ID only, used for limits.

**On the server (`usage.db`):** `usage(day, key, calls, cost_usd, reserved_usd)`, where key is `visitor:<id>`, `net:<hash>`, or `global`. No personal text, ever.

**`.env` settings:**

- `OPENAI_API_KEY` — a dedicated Tipping Point project key.
- Models per task: `MODEL_TURN`, `MODEL_VALUES`, `MODEL_SCORES`, `MODEL_FUTURES` (all `gpt-6-luna` by default).
- `REASONING_EFFORT` (default `low`).
- Output caps per task: `MAX_OUT_TURN=2000`, `MAX_OUT_VALUES=800`, `MAX_OUT_SCORES=2000`, `MAX_OUT_FUTURES=1000`.
- Prices per model: `PRICE_IN_PER_M_<model>`, `PRICE_OUT_PER_M_<model>`.
- Limits: `LIMIT_VISITOR_CALLS=45`, `LIMIT_NETWORK_CALLS=90`, `LIMIT_GLOBAL_CALLS=1500`, `DAILY_SPEND_CAP_USD=1.00`.
- `IP_HASH_SALT`, `DEALBREAKER_FAIL=3`, `TARGET_ANSWERS=5`.

## File Structure

```
learn-ai-basics-project/
├── server/
│   ├── main.py          # FastAPI app: routes, static files, request pipeline
│   ├── config.py        # reads .env: models, output caps, prices, limits
│   ├── ai.py            # OpenAI calls (one function per task)
│   ├── prompts.py       # instructions for each task
│   ├── schemas.py       # strict JSON shapes for AI replies
│   ├── citations.py     # citation + quote validator, complete score grid
│   ├── safety.py        # crisis check + support response
│   ├── limits.py        # caps, atomic budget reservation, cost recording
│   ├── security.py      # size limits, CSP header
│   └── usage.db         # created at runtime; counts and costs only (gitignored)
├── web/
│   ├── index.html       # page shell, fonts
│   ├── styles.css       # cream / coral / deep-blue theme
│   ├── app.js           # step flow + session storage
│   ├── steps.js         # framing, interview, review, values, importance screens
│   ├── live.js          # live picture beside the interview (themes, lean, clarity)
│   ├── board.js         # decision board rendering
│   ├── engine.js        # fit, dealbreakers, tipping point, confidence (pure)
│   ├── api.js           # calls to the server, retry, error messages
│   └── example.js       # Ayesha's example script (built last)
├── tests/
│   ├── test_citations.py
│   ├── test_limits.py   # includes concurrent-request and failed-validation cases
│   ├── test_safety.py
│   ├── engine.test.mjs  # node --test, includes all edge cases
│   ├── run_scenarios.py # runs the 5 scenarios, writes a support-review sheet
│   └── scenarios/       # Ayesha demo, ambiguous, contradictory, thin evidence, crisis
├── devpost/             # planning docs (scope, prd, spec, checklist)
├── .agents/ .claude/ agent/   # Devpost Learn Skill Pack (installed)
├── .env.example         # every setting, no real key
├── .gitignore           # .env, usage.db, .venv, learner profile, scenario outputs
├── requirements.txt
├── LICENSE              # MIT — required for submission
└── README.md            # what it is, how to run, how it was built, data notice
```

## External Services and Dependencies

### OpenAI API

- **Call:** Responses API, one call per endpoint request; model, `max_output_tokens`, and reasoning effort from `.env`; strict JSON-schema output; `store: false`.
- **Auth:** dedicated project key in `OPENAI_API_KEY`, server only.
- **Model:** `gpt-6-luna` for all tasks to start ("most efficient model for focused, high-volume tasks"); any task can move to `gpt-6.1-sol` via `.env` if the citation support tests show weak results.
- **Cost (checked 18 Oct 2026):** Luna $0.10 in / $0.50 out per 1M tokens; Sol $2 / $10. A session is roughly 9–15 calls, about $0.007 on Luna.
- **Docs:** <https://developers.openai.com/api/docs/models>, <https://developers.openai.com/api/docs/pricing>, <https://developers.openai.com/api/docs/guides/your-data>

### Google Fonts

Fraunces, Nunito, IBM Plex Mono via a stylesheet link; the page still works with system fonts if they fail to load.

### Hosting (deferred to `6-ship`)

Lightsail (if the credits apply) or the existing Hetzner VPS. No build decision depends on it.

## How We Verify

- **Engine unit tests** (`engine.test.mjs`):
  - Ayesha's flip (career growth 6 → 9 changes the leader).
  - Fit edge cases: all weights 0; an option with all scores unknown; every option unknown; a tie.
  - Dealbreakers: a score of exactly 3 rules the option out; a score of 4 doesn't; an unknown dealbreaker score is unresolved; every option ruled out; a weight-0 dealbreaker still applies.
  - Tipping-point "more than" / "less than" / no flip, and each confidence part at its limits.
- **Validator tests:**
  - Values with no IDs, unknown IDs, or removed IDs are removed.
  - Score cells with bad citations are converted to insufficient.
  - The grid is always complete.
  - Out-of-range scores are rejected.
  - Uncited future sentences are removed.
  - A quote that doesn't appear in the answer is flagged.
- **Spend tests:**
  - Concurrent requests near the cap — only those that fit are reserved.
  - Usage is recorded when validation fails afterwards.
  - Reservations are kept on timeout and released on refused connection.
  - The daily reset.
- **Citation support test** (`run_scenarios.py`):
  - Runs the 5 scenarios on the configured models.
  - Writes a review sheet listing every value, score reason, `depends_on_others` flag, and future-card sentence next to the full text of the statements it cites.
  - Zain marks each one *supported*, *partly*, or *not supported*.
  - Pass bar for the Ayesha demo scenario: at least 90% *supported* and no *not supported* item visible on the board. Otherwise that task moves to `gpt-6.1-sol` and is re-run.
  - The sheet also reports how many items the validator removed or converted, and how many quotes mismatched.
- **Safety test:** the crisis scenario must stop the flow on the first answer that contains crisis wording.
- **Manual:** the full demo journey in a browser; refresh mid-flow restores her work; closing the tab clears it.

## Important Failure Modes

- **OpenAI slow** → a "Thinking…" state on the step; the button is disabled so it can't double-send.
- **OpenAI fails or times out (30s)** → "Something went wrong — Try again." Retrying repeats only that request; everything in session storage stays (`prd.md > States and Boundaries`). The cost of a possibly-billed failure is still counted.
- **Validator removes all values** → "We couldn't find values clearly backed by your words — add your own" (adding values is always possible).
- **Insufficient cells or empty future cards** → explicit "Not enough from you yet" states, and the engine edge-case messages above.
- **Limit or budget reached** → the limit message; work stays.
- **Crisis detected** → the support message; the decision flow stops.

## What Was Simplified and Why

- **A fixed first question, not AI-written** — saves a call and makes the opening instant. Later questions are AI-written.
- **Extraction and next question in one call** (`/api/turn`) instead of two — halves interview cost and waiting.
- **Session storage instead of saved sessions** — survives a refresh, no accounts, no personal data kept. Saving across visits would need storage and consent.
- **Phrase list + model flag for crisis detection** instead of a trained classifier — matches "basic" in scope; a fuller version would use a dedicated safety-classification service.
- **Citation support checked by human review in tests**, not by a second AI judging every live answer — a live judge would double the cost and is itself fallible.
- **Whole-number tipping-point search** — matches the 0–10 sliders and keeps the sentence readable.
- **Forward-only steps** — going back and editing would force regenerating values and scores; "Start over" covers mistakes for the POC.
- **Evidence coverage instead of voice labels** — voice labels are deferred (`scope.md > Later`).

## Decisions and Open Issues

**Learner decisions**

- Python backend + plain web page; the board maths in the browser for an instant flip — accepted tradeoff: the maths is JavaScript, not Python.
- OpenAI, starting with `gpt-6-luna`, model set per task; upgrade only tasks that fail the citation support test.
- Caps: 3 sessions per visitor, 100 sessions per day, $1/day spend, all in `.env`, enforced on the server.
- **Spend protection (review):**
  - Atomic reservation before each call.
  - Usage recorded immediately on response, even if validation fails afterwards.
  - Conservative cost estimates, and output-token caps per task.
  - The local cap is documented as best-effort, with a dedicated OpenAI project budget as the backstop.
- **Citation integrity (review):** a valid ID is not proof of support. Every statement keeps its source answer and quote, and support is tested by human review against a pass bar. No claim that hallucination is impossible.
- **Calculation edge cases (review):**
  - Defined behaviour for all-zero weights, all-unknown scores, unresolved dealbreakers, and every option ruled out.
  - Insufficient cells are kept with `score: null` and empty citations.
- **Privacy and security (review):** data notice before the first answer, no body logging, safe rendering, and size limits.
- **Confidence (review):** a clarity heuristic, not a probability. Completeness counts answered questions against a target of 5 and never blocks her from stopping.
- **Dealbreaker:** a score of 3 or below rules an option out; an unknown score leaves it unresolved.
- **Evidence:** measured as evidence coverage.
- **"Try Ayesha's example":** included because it only pre-fills existing inputs; built last and cut if time runs short.
- **Hosting:** local by default; public hosting compared in `6-ship` (Lightsail if the credits apply, versus the Hetzner VPS).
- Colours: warm cream, soft coral, deep blue. Refresh survival via session storage.

**Derived implementation details (agent, from the decisions above)**

- FastAPI serves the page too; SQLite for counts; IP stored only as a salted hash.
- Fonts and exact shades; output-token defaults per task; the 90% pass bar.
- `store: false`; Content-Security-Policy header.

**The learner's question: how the citation validator works**

Zain wanted to understand the validator, since "the AI never invents a reason" is the main promise. Clarified with Ayesha's example:

- Every AI item must list statement IDs.
- The server removes values, converts score cells, or drops future sentences that have no IDs or unknown/removed IDs, before she sees anything.
- The AI may say "not enough from you" instead of guessing.

Zain's review sharpened this: a valid ID proves only that the source exists, not that it supports the claim. That is now handled by quote traceability on screen and by the citation support test with a pass bar.

**Still to verify in the first build step (not spec decisions)**

- Python version on the laptop.
- That the API key can call `gpt-6-luna`.
- The SDK parameter names (`text.format`, `reasoning`, `max_output_tokens`, `store`), and whether reasoning tokens count toward `max_output_tokens`.
- Whether the OpenAI project budget is a hard stop.

**Carried from `prd.md > Open Questions` (not blocking)**

- Support message: add a helpline, or only the parent / friends / doctor guidance?
