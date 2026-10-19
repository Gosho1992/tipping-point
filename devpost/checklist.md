---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [x] **1. You can frame a decision and answer questions, and your answers turn into numbered statements**
  Becomes usable: A running app at localhost:8000. Ayesha sees the data notice, types her decision and two options (`Wait / neither` added), answers the fixed first question, and sees real statements (S1, S2…) appear beside the conversation, each traceable to the exact words of her answer. AI-written next questions follow. Work survives a refresh. Crisis wording in an answer already stops the flow with the support message.
  Why now: Highest technical risk first — proves the OpenAI key can call `gpt-6-luna`, the SDK's structured-output parameters, and statement extraction — and bootstraps the whole project inside a real behavior.
  PRD ref: `prd.md > The Core Journey` (steps 1–5), `prd.md > Framing the Decision`, `prd.md > Guided Interview`, `prd.md > Statements`, `prd.md > Safety Check`
  Spec ref: `spec.md > Stack`, `spec.md > Where It Runs and How Someone Tries It`, `spec.md > Step Flow and Session Store (web/app.js)`, `spec.md > Framing Step`, `spec.md > Interview Step`, `spec.md > AI Calls (server/ai.py, server/prompts.py, server/schemas.py)`, `spec.md > API Endpoints`, `spec.md > Data Model`, `spec.md > File Structure`, `spec.md > Look and Feel`, `spec.md > Safety Check (server/safety.py)`, `spec.md > Privacy and Security`
  Build: Scaffold per the file structure (requirements.txt with pinned versions, .env.example, .gitignore additions, MIT LICENSE, README stub); config.py; FastAPI app serving `web/`; `/api/turn` with strict schema, `store: false`, `max_output_tokens`, quote check; page with theme, framing and interview steps, statement collection, session storage, "Review my thoughts" enabled after one statement; data notice on the framing step; basic `safety.py` phrase check on `/api/turn` with the support screen. Record the verified SDK parameter names and Python version.
  Verify (mechanical): One-off script confirms a `gpt-6-luna` structured call succeeds and prints token usage; pytest for the quote check and for a crisis phrase stopping `/api/turn`; start the server, POST a sample answer to `/api/turn` and confirm statements with verified quotes and a next question come back; load the page and confirm no console errors.
  Learner check: Run the app, read the data notice, enter a decision with two options, answer two questions in your own words, and check whether the statements match what you meant and show where they came from. Refresh the page and confirm nothing is lost.
  Commit: `Frame a decision and turn interview answers into traceable statements`

- [x] **2. You can review statements, confirm cited values, mark dealbreakers, and set importance**
  Becomes usable: After "Review my thoughts", she edits or removes statements, sees 4–6 AI-proposed values each with citation chips, renames/removes/adds values, marks dealbreakers, and sets 0–10 importance.
  Why now: The citation validator is the main promise; it appears here first on real values, before anything is built on top of them.
  PRD ref: `prd.md > Statements`, `prd.md > Values and Dealbreakers`, `prd.md > Importance Weights`
  Spec ref: `spec.md > Statement Review Step`, `spec.md > Values Step`, `spec.md > Importance Step`, `spec.md > Citation Validator (server/citations.py)`
  Build: Review step (edit, remove, "edited by you"); `citations.py` validator for values; `/api/values`; values step with chips, add/rename/remove, dealbreaker toggle; importance sliders.
  Verify (mechanical): pytest — values with no IDs, unknown IDs, or removed IDs are removed; a live `/api/values` call returns only valid-cited values; removed statements are never sent.
  Learner check: Remove one statement, then check that no value cites it. Add a value of your own, mark one dealbreaker, set importances.
  Commit: `Review statements and confirm cited values, dealbreakers, and importance`

- [x] **3. The decision board shows the leader and the tipping point, and moving a weight flips it instantly**
  Becomes usable: The board shows three options with fit scores, the leader, a complete score grid with cited reasons and explicit "Not enough from you yet" cells, adjustable scores, weight sliders, dealbreaker status, and the tipping-point sentence. Dragging the tipping-point value past its threshold flips the leader instantly.
  Why now: This is the unique kernel — the visible flip traced to her words. It must exist before polish.
  PRD ref: `prd.md > The Decision Board`, `prd.md > Citation Guardrail`
  Spec ref: `spec.md > Decision Board (web/board.js)`, `spec.md > Decision Engine (web/engine.js)`, `spec.md > Citation Validator (server/citations.py)`, `spec.md > API Endpoints`
  Build: `/api/scores` with complete-grid validation (bad cites → insufficient, `score: null`); `engine.js` fit, dealbreakers (≤3 ruled out, unknown = unresolved), leader, tie, all edge-case messages, tipping point; board panels for fit, weights, grid, tipping point.
  Verify (mechanical): `node --test` covering Ayesha's 6→9 flip, every fit/dealbreaker/leader edge case, and tipping point more/less/no-flip; pytest for grid completeness and conversion to insufficient; full journey run in the browser.
  Learner check: Go through to the board, read the tipping-point sentence, drag that value's slider past the threshold, and watch the leader change. Change one score yourself.
  Commit: `Add decision board with instant tipping-point flip`

- [x] **4. The interview shapes a live picture as you answer**
  Becomes usable: Questions come from the whole picture, not the last answer; every answer updates themes, a lean bar, and a clarity bar beside the question; Skip swaps the question; "Show my result" is always available, with a gentle "more answers would help" line when clarity is Low; the values step is pre-filled from the live themes.
  Why now: Checkpoint feedback after slice 3 — the interview felt like follow-up after follow-up with nothing visible. This changes how the core loop feels, so it comes before the remaining polish.
  PRD ref: `prd.md > Guided Interview`, `prd.md > Live Picture`, `prd.md > The Core Journey`
  Spec ref: `spec.md > Interview Step`, `spec.md > Live Picture (web/live.js)`, `spec.md > Decision Engine (web/engine.js)`, `spec.md > Values Step`, `spec.md > API Endpoints`, `spec.md > Data Model`
  Build: New `/api/turn` schema and prompt (statements with N-IDs renumbered by the server, themes, light cited grid, whole-picture next question); theme and grid validation; `engine.confidence` with raise-line templates; `web/live.js`; interview layout with Skip, live picture, and "Show my result"; values pre-filled from themes.
  Verify (mechanical): pytest for ID renumbering, theme and grid validation, and invalid citations; `node --test` for each confidence part, the no-leader rule, and raise-line choice; a live 3-answer run in which no question repeats or quotes the previous answer; browser run with no console errors.
  Learner check: Run your friendship decision again and say whether the questions now feel like they shape your thinking, and whether the lean and clarity bars help.
  Commit: `Shape a live picture during the interview`

- [x] **5. The board explains itself: confidence, future cards, and sources for every claim**
  Becomes usable: Confidence badge (clarity heuristic, with its note and "what would raise it" line), one future card per option with cited sentences, and clicking any citation chip shows the statement and the answer it came from.
  Why now: Completes every element of `scope.md > What "Working" Looks Like` once the kernel works.
  PRD ref: `prd.md > The Decision Board`
  Spec ref: `spec.md > Decision Engine (web/engine.js)`, `spec.md > Decision Board (web/board.js)`, `spec.md > Citation Validator (server/citations.py)`
  Build: Confidence badge on the board (engine part built in slice 4); `/api/futures` with sentence-level validation; future cards; citation drill-down to statement and source answer.
  Verify (mechanical): board confidence matches `engine.confidence` for the board weights; pytest — uncited future sentences removed, empty card placeholder; browser check that every chip opens its source.
  Learner check: Look at the confidence line and say whether it makes sense; open three citation chips and judge whether each really supports its claim.
  Commit: `Add confidence, future cards, and source drill-down`

- [x] **6. We know whether the AI's citations really support its claims**
  Becomes usable: `run_scenarios.py` runs the 5 scenarios and writes a review sheet you mark supported / partly / not supported, plus validator counts. The model per task is confirmed or upgraded.
  Why now: Citation quality is the biggest product risk and it needs the full pipeline. Doing it before guardrail and polish slices leaves room to switch models.
  PRD ref: `prd.md > Citation Guardrail`
  Spec ref: `spec.md > How We Verify`, `spec.md > Decisions and Open Issues`
  Build: Five scenario files (Ayesha demo, ambiguous, contradictory, thin evidence, crisis); runner that calls all four endpoints and writes the sheet; apply the pass bar and switch weak tasks to `gpt-6.1-sol` in `.env` if needed.
  Verify (mechanical): Runner completes all scenarios and writes the sheet; validator counts reported; Ayesha scenario meets ≥90% supported with no unsupported item on the board (after any model change and re-run).
  Learner check: Mark the review sheet yourself and decide whether the results are good enough to demo.
  Commit: `Add citation support scenarios and confirm models`

- [x] **7. Crisis handling covers every step, and her data is handled safely**
  Becomes usable: Crisis wording anywhere in her text (statements, value names, any endpoint) or flagged by the model replaces the flow with the support message; no request bodies are logged; all text renders safely; oversized input is refused.
  Why now: Required guardrails before anyone else touches the app; built on the finished pipeline so every endpoint is covered at once.
  PRD ref: `prd.md > Safety Check`, `prd.md > States and Boundaries`
  Spec ref: `spec.md > Safety Check (server/safety.py)`, `spec.md > Privacy and Security`, `spec.md > Server App (server/main.py)`
  Build: extend the phrase check to every endpoint, add the model `crisis` flag to every schema; `security.py` size limits and CSP; logging config with no bodies; audit that all rendering uses `textContent`.
  Verify (mechanical): pytest for crisis detection on every endpoint and 413 on oversized input; crisis scenario stops on its first crisis answer; grep confirms no `innerHTML` with user or AI text; server log contains no answer text after a full run.
  Learner check: Put distressing wording into an edited statement or a value name and confirm the support message appears and the decision output stops.
  Commit: `Add safety check and privacy hardening`

- [x] **8. Usage caps and spend protection hold, even under simultaneous requests**
  Becomes usable: Per-visitor, per-network, global and daily-spend caps are enforced on the server with atomic reservation; hitting a cap shows the friendly limit message and keeps her work.
  Why now: Only matters once the app is shared; built after everything that makes AI calls so every call path is covered.
  PRD ref: `prd.md > States and Boundaries`
  Spec ref: `spec.md > Usage Limits and Spend Protection (server/limits.py)`, `spec.md > Data Model`
  Build: `limits.py` with SQLite `BEGIN IMMEDIATE` reservation, immediate cost recording, reservation keep/release on failure, daily reset; visitor ID; 429 handling in the page.
  Verify (mechanical): pytest — concurrent requests near the cap, usage recorded when validation later fails, keep on timeout / release on refused connection, daily reset, each 429 code.
  Learner check: Set a tiny cap in `.env`, use the app until it triggers, and confirm the limit message appears and your work is still on screen.
  Commit: `Add usage caps and atomic spend protection`

- [x] **9. Judges can try Ayesha's example in seconds, and the repo explains itself**
  Becomes usable: "Try Ayesha's example" pre-fills the decision and offers her scripted answers turn by turn (still live AI); README covers what it is, how to run it, how it was built (Codex then Claude Code with the Devpost Learn Skill Pack), and the data notice.
  Why now: Pure convenience on top of a finished core; cut first if time runs short.
  PRD ref: `prd.md > The Core Journey`
  Spec ref: `spec.md > Example Entry Point ("Try Ayesha's example")`, `spec.md > Where It Runs and How Someone Tries It`
  Build: `web/example.js` and its entry link; README.
  Verify (mechanical): Example run from start to board in the browser with no console errors; README run steps followed from a clean clone start the app.
  Learner check: Click "Try Ayesha's example" and go all the way to the flip using only the example answers.
  Commit: `Add Ayesha example and README`

- [x] **10. You can speak your answers in your own language**
  Becomes usable: A language picker and microphone on the framing step and every interview question; the transcript is translated to English via `/api/translate`, reviewed, edited, and accepted before use.
  Why now: Built by the learner after slice 9, together with a visual redesign; recorded here so the plan matches the code.
  PRD ref: `prd.md > Voice Input`, `prd.md > Look and Feel`
  Spec ref: `spec.md > Voice Input (in web/steps.js, endpoint in server/main.py)`, `spec.md > Look and Feel`
  Build: Browser speech recognition, translation endpoint on the existing spend pipeline, review-and-accept panel; indigo glass redesign in `web/styles.css`.
  Verify (mechanical): `tests/test_translate.py` (translation, crisis in original or translation, model flag, empty reply, size limit); all 53 server and 20 engine tests pass; learner confirmed mic, translation, and mapping work in Chrome.
  Learner check: Speak an answer in Urdu, translate it, edit the English, accept, and send.
  Commit: `Add voice input with reviewed translation and visual redesign`

## Hands-on Checkpoints

- [x] Early usable behavior explored — after slice 3 (the flip); feedback led to slice 4 (live interview)
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Zain marks `tests/scenarios/out/review.md` (agent pre-review of the Ayesha run: about 19 of 20 items supported, none unsupported; validator removed nothing; all quotes verified; crisis scenario stopped at answer 2)
- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence:
Route and stops:
Edit outcome:
Reflection:
Activity mode:

## Revisions

- Data notice and a basic crisis phrase check moved into slice 1 — learner asked for them earlier; her text goes to OpenAI from the first answer, so both belong there. Slice 6 now extends them to every endpoint and hardens privacy.
- Verified in slice 1: the OpenAI SDK (openai 3.35.1) accepts `instructions`, `text` structured output, `reasoning`, `max_output_tokens`, and `store`; the key can call `gpt-6-luna`. Python requirement relaxed to 3.10+ because the code runs and is tested on 3.10.
- `.claude/` (Windows symlinks to `.agents/skills`) is gitignored because the links can't be read outside Windows; the skill files themselves are committed under `.agents/` and `agent/`.
- Checkpoint after slice 3: the interview chained questions off the last answer and showed nothing until the end. Added slice 4 (whole-picture questions, live themes, lean and clarity bars, Skip, "Show my result"); the confidence engine moved into it from the board slice; later slices renumbered. Clarity now also shows with no leader (stability counts as 0).
- Clarity showed 69% (Medium) after one answer because a sparsely scored leader looked unflippable. Stability and control are now multiplied by evidence coverage (spec updated).
- Citation support run 1: Luna merged pay into "Career Growth" (2 themes for Ayesha, 86% fully supported) and some reasons used first person. Prompts now keep distinct concerns apart and address the person as "you"; run 2 gave 4 themes and about 19/20 supported. Luna kept for all tasks.
- Usage caps key the network limit on the client address; behind a reverse proxy that would be the proxy's address. Spec now says to run Uvicorn with `--proxy-headers` when hosting (for `6-ship`).
- After slice 9 the learner added voice input and an indigo glass redesign (slice 10). Scope moved voice input from Explicitly Cut into the POC boundary; PRD and spec updated.
- The redesign had removed the framing step's data notice; it was restored (now also explaining that browser speech recognition is used for the microphone) because `spec.md > Privacy and Security` requires it before the first answer.
- The project folder was replaced during the redesign and its `.git` history was lost; the repository was re-initialised from the current files.
- UI polish after the redesign: the board columns were swapped (score table squeezed and the Wait / neither column cut off), empty score cells printed "nullnull" (native `append` writes empty slots as text), the interview panel had no padding, and the background could end in a hard edge on long pages. Fixed in `web/styles.css` and `web/board.js`; every screen re-checked at 1366, 1024, and 390 px with no horizontal scroll.
