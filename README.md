# Tipping Point

**See your decision before you make it — and find the one thing it really depends on.**

Tipping Point is a decision buddy for one personal choice between two options (plus "Wait / neither"). It interviews you, turns your own words into numbered statements, groups them into what matters to you, and builds a decision board that shows which option your own weights favour — and exactly which value would flip the result. Drag that value's importance past the threshold and the leader changes instantly.

It never decides for you, and every claim on screen points back to something you said.

## How it works

- **Live interview.** One question at a time, chosen from the whole picture of what you've said so far — not a follow-up on your last sentence. Every answer updates a live picture: your thoughts grouped into themes, how your words lean across the options, and a clarity bar. Skip any question; click **Show my result** whenever you like.
- **Your words only.** Each thought keeps the exact words it came from. Every value, score reason, and future sentence must cite your statements; a citation validator on the server removes anything that doesn't, and scores without support show as "Not enough from you yet" instead of a guess.
- **Code does the maths.** Fit scores, dealbreakers, the tipping point, and clarity are calculated in the browser by plain JavaScript (`web/engine.js`), never by the AI. Clarity is a heuristic for how complete and steady the picture is — not the chance that a choice is right.
- **Speak in your own language.** Pick a language, use the microphone, and Tipping Point translates what you said into English for you to review, edit, and accept before it's used. Typing always works too.
- **Safety.** Crisis or serious-distress wording stops the flow and shows a support message instead of decision results.

What the guardrails can't do: a valid citation proves the source exists, not that it fully supports the claim. That's why every citation opens the original words so you can judge, and why `tests/run_scenarios.py` produces a review sheet for checking support by hand.

## Run it locally

You need Python 3.10+ ([python.org](https://www.python.org/downloads/); on Windows tick **Add python.exe to PATH**) and an OpenAI API key.

**One click**

1. Click **Code → Download ZIP** on GitHub and unzip it (or `git clone` the repo).
2. Windows: double-click **`start.bat`**. macOS/Linux: run `./start.sh`.
3. The first time, paste your OpenAI API key when asked. It's saved only in `.env` on your computer.
4. Your browser opens Tipping Point. Click **Try Ayesha's example** for a ready-made career decision. Close the black window to stop.

**By hand**

1. `python -m venv .venv`
2. Activate it — Windows: `.venv\Scripts\activate` · macOS/Linux: `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and put your key after `OPENAI_API_KEY=`
5. `uvicorn server.main:app --no-access-log`
6. Open <http://localhost:8000>

## Tests

- Server: `python -m pytest -q tests`
- Decision engine: `node --test tests/engine.test.mjs`
- Citation support (live AI, a few cents at most): `python -m tests.run_scenarios all`, then mark `tests/scenarios/out/review.md`

## Privacy and cost

- If you use the microphone, your browser's own speech service (Google, in Chrome) turns your voice into text; only the text you choose to translate is sent on.
- Your decision and answers are sent to OpenAI to generate questions and suggestions (`store: false`). Tipping Point keeps your work only in your browser tab's session storage — it survives a refresh and disappears when you close the tab. The server never stores or logs what you write; it keeps usage counts and costs only, with IP addresses stored as salted hashes.
- Every setting lives in `.env`: the model per task (default `gpt-6-luna`), output-token caps, and daily caps per visitor, per network, overall, and in dollars. Spend is reserved atomically before each call and replaced by the real cost as soon as OpenAI replies. This local cap is best-effort; use a dedicated OpenAI project with its own budget limit as the hard backstop.
- When hosting behind a reverse proxy, run Uvicorn with `--proxy-headers --forwarded-allow-ips=127.0.0.1` so the per-network cap sees real addresses.

## How it was built

Built for Devpost's **Build With AI: Basics** hackathon with the **Devpost Learn Skill Pack**, plan first: the planning documents are in `devpost/` — `scope.md`, `prd.md`, `spec.md`, and the build `checklist.md` (with every plan revision recorded). Planning started in **Codex** and continued in **Claude Code**, both using the same Skill Pack; the code was written with Claude Code as the coding agent.

Stack: Python (FastAPI) server, plain HTML/CSS/JavaScript page with no build step, OpenAI Responses API with structured outputs, SQLite for usage counts.

## License

MIT — see `LICENSE`.
