---
doc: prd
status: approved
---

# Tipping Point — Product Requirements

A decision buddy that turns one person's own words about a two-option personal decision into an interactive, traceable decision board showing what the decision hinges on — without deciding for them.
Source: `scope.md > The Unique Kernel`, `scope.md > Who It's For`.

## The Core Journey

Source: `scope.md > The Core Loop`, `scope.md > What "Working" Looks Like`.

1. **Welcome.** Ayesha opens Tipping Point and sees a simple, welcoming space asking what she is trying to decide.
2. **Frame the decision.** She describes the decision in her own words, as she would on paper, and names her two options (Berlin, San Francisco). The app always adds `Wait / neither` as a third option.
3. **Interview.** The app asks one open question at a time, chosen from the whole picture of what she has said so far — what is still missing (an option she hasn't talked about, a fear, a trade-off, a possible regret) — not a follow-up on her last sentence. She answers in her own words, or skips the question.
4. **Live picture.** After each answer, the app extracts her thoughts as numbered, readable statements (e.g. "S1 — Career growth: Moving abroad could improve my career prospects") and groups them under emerging themes. Beside the question she sees a **lean bar** (how her own words lean across the three options so far, every theme counted equally, labelled "not advice") and a **clarity bar** with one line on what would raise it.
5. **She decides when she's done.** **"Show my result"** is always available once she has a thought. If clarity is still low, a gentle line suggests a couple more answers, but it never blocks her. The app never ends the interview on its own.
6. **Review statements.** She reads each statement, edits its wording, or removes ones that misread her.
7. **Choose values.** The values arrive pre-filled from the live themes (e.g. Career growth, Family nearby), each citing the statements it came from. She renames, removes, or adds values, and marks any value as a dealbreaker.
8. **Set importance.** She sets a 0–10 importance weight for each value.
9. **Decision board.** She sees all results at once: each option's fit score and the current leader, option-by-value scores with cited reasons (adjustable here), the tipping-point sentence, a confidence score with what would raise it, and one future card per option.
10. **Play with it.** She drags a weight slider on the board. Fit scores, leader, tipping point, and confidence update instantly. Moving the tipping-point value past its threshold flips the leader.

**Success:** Ayesha drags Career growth from 6 to 9, San Francisco overtakes Berlin instantly, the board updates, and every line still traces back to something she said.

## Screens and Layout

One step-by-step flow; she moves forward through these steps and never sees every control at once.

1. **Welcome / Frame** — decision text and her two options.
2. **Interview** — one question at a time with a Skip action; alongside it, the live picture (lean bar, clarity bar, themes with their statements) and the "Show my result" action.
3. **Review statements** — the full statement list, each editable or removable.
4. **Choose values** — proposed values with their citations; rename, remove, add, mark dealbreaker.
5. **Set importance** — a 0–10 weight for each confirmed value.
6. **Decision board** — all results together (see "The Decision Board").
7. **Support message** — replaces the flow if crisis language is detected (see "Safety Check").

## Look and Feel

*Revised by the learner after the build (`UI-REDESIGN.md`):* a deep indigo/blue background with slow-moving gradient orbs, translucent glass panels, and violet/pink/cyan gradient accents. The tone stays friendly with a brainy touch; ambient motion stops when the person prefers reduced motion. The original direction is kept below for the record.


Source: `scope.md > Inspiration & Identity`.

- **Very friendly, with a brainy touch.** Warm and approachable, never clinical or corporate — but clearly thoughtful and evidence-led.
- Calm and empowering rather than prescriptive; it should feel like her own thinking workspace.
- Statements should read like readable thought cards, not codes.
- Colours: warm cream background, soft coral highlights, deep blue text.

## Features and Behavior

### Framing the Decision

- She types the decision in free text and enters exactly two options.
- `Wait / neither` is always added automatically as a third option.
- [ ] Two named options plus `Wait / neither` appear and carry through to the board.
- [ ] She cannot proceed without a decision description and both options.

### Guided Interview

Source: `scope.md > The POC Boundary`.

- One open question at a time; she answers in her own words or skips it.
- Each question comes from the whole picture so far — what is still missing or unclear across her options and themes — never a drill-down on her last sentence, and never a repeat of an earlier question.
- Questions explore gains and losses for each option, fears, trade-offs, and regret.
- **Skip** gives her a different question without needing an answer.
- **"Show my result"** is available as soon as one statement exists; when clarity is Low it shows "A couple more answers would make this clearer" but never blocks her.
- [ ] Only one question is shown at a time.
- [ ] Consecutive questions explore different angles rather than following up on the previous answer.
- [ ] Skip changes the question without sending an answer.
- [ ] The interview continues until she clicks "Show my result."

### Live Picture

Source: `scope.md > The Core Loop` — made visible during the interview instead of only at the end.

- After every answer, her statements are grouped under 2–6 emerging themes, each citing its statements; thoughts that fit no theme stay listed on their own.
- **Lean bar:** how her own words lean across the three options so far, treating every theme as equally important (she sets real importance later). Labelled as a reading of her words, not advice. When there isn't enough yet, it says so instead of showing a lean.
- **Clarity bar:** the same clarity heuristic the board uses, with Low / Medium / High and one line on what would raise it. It moves as she answers.
- [ ] After each answer, the themes, lean bar, and clarity bar update without leaving the page.
- [ ] Every theme shows the statements it groups; every lean is computed in code from cited scores.
- [ ] The lean bar never names a choice as advice.

### Statements

- Each answer is split into individual thoughts, each shown as `S#` + a short readable title + the meaning of her thought.
- Statements appear live as she answers and accumulate as a visible collection.
- On the review step she can edit wording or remove a statement.
- Statement IDs are the anchors every citation in the app points to.
- [ ] Her example answer about career and family produces two separate statements with readable titles.
- [ ] Edited wording is what later citations show.
- [ ] A removed statement is no longer cited anywhere.

### Values and Dealbreakers

- The app proposes 4–6 values, each citing one or more statements.
- She can rename, remove, or add values, and mark any value as a dealbreaker.
- Choosing values is separate from setting their importance.
- Dealbreaker ≠ importance: importance says how much a value matters; a dealbreaker means an option that fails it is unacceptable (its fit becomes zero).
- [ ] Every proposed value shows at least one valid statement citation.
- [ ] Renamed, added, and removed values are reflected on every later step.

### Importance Weights

- A dedicated step before the board: a 0–10 weight per value.
- The same weights remain adjustable on the board.
- [ ] Each value has a 0–10 control, and the values set here appear on the board.

### The Decision Board

Source: `scope.md > What "Working" Looks Like`.

Shows at once:

- **Options and fit** — Berlin, San Francisco, and `Wait / neither`, each with a fit score (weighted average of option scores by importance); the leader is marked as the calculated leader from her weights, never as the app's recommendation.
- **Option scores** — a 0–10 score per option per value, each with a short reason citing statements. `Wait / neither` is scored exactly like Berlin and San Francisco, using her own statements as evidence. She can adjust any score here.
- **Weight sliders** — for every value.
- **Tipping point** — one sentence naming the most sensitive value and its threshold, e.g. "Berlin leads unless Career growth matters more than 8/10."
- **Confidence** — a percentage with Low (<50) / Medium (50–74) / High (75+), plus one line on what information would raise it. Calculated in code from evidence, completeness, stability, and control — never by asking the AI how sure it is.
- **Future cards** — one short "a Tuesday, one year from now" card per option, built only from her statements.
- [ ] Moving any slider or score updates fit, leader, tipping point, and confidence instantly.
- [ ] Moving the tipping-point value past its threshold flips the leader.
- [ ] A dealbreaker failure sets that option's fit to zero, and the board shows why on that option (which dealbreaker value it fails, with its citation).
- [ ] Every reason, value, and future card shows citations to her statements.

### Citation Guardrail

Source: `scope.md > The POC Boundary`.

- Any AI-generated line without a valid statement ID is dropped before she sees it.
- [ ] No uncited or wrongly cited AI line ever appears on any screen.

### Voice Input

Added by the learner after the build.

- On the framing step she can speak her decision; on each interview question she can speak her answer, choosing the language she speaks from a list (English, Urdu, Hindi, Arabic, and others).
- She sees the recognized words in her language, translates them to English, reviews and edits the English, and only **"Use this English answer"** puts it into the answer box — she still presses Send.
- Typing always remains available; if the browser has no speech recognition or the microphone is refused, she is told so and keeps typing.
- [ ] Spoken words appear as an editable transcript before anything is translated.
- [ ] Nothing spoken reaches the interview until she accepts the English text.
- [ ] Crisis wording in the original or the translation stops the flow with the support message.

### Safety Check

Source: `scope.md > The POC Boundary`.

- If her input contains crisis or serious-distress language, the app stops giving decision answers and shows a supportive message encouraging her to talk to a parent, friends, or a doctor.
- [ ] Crisis language replaces the flow with the support message; no further decision output is shown.

## States and Boundaries

- **First use** — welcome screen with only the decision prompt.
- **Interview in progress** — statements collection grows; "Review my thoughts" is always available once at least one statement exists.
- **No statements** — she cannot move to review until at least one statement exists.
- **Dropped AI lines** — removed silently by the citation guardrail; if a value or reason ends up with nothing valid, it is simply not shown.
- **AI unavailable or fails** — a clear "Try again" message. Everything she has typed, edited, selected, and scored is preserved, and retrying repeats only the failed operation — it never restarts the workflow.
- **Crisis detected** — support message; the decision flow stops.
- **Persistence** — one session only; her work survives an accidental page refresh in the same tab and is cleared when she closes it. No accounts or cloud sync (`scope.md > Explicitly Cut`), and no unnecessary personal data is stored.

## Product Decisions

- Two primary options plus `Wait / neither`; demo stays Berlin vs San Francisco — the core idea is turning messy thoughts into visible trade-offs, not the number of options.
- Edit and remove statements only; merge/split deferred — extra interactions not needed to prove the idea.
- One question at a time with live statement extraction — a guided conversation, not a questionnaire.
- She ends the interview herself via "Show my result" — the app helps her understand her thinking; it doesn't decide when she has finished thinking.
- (Checkpoint feedback after slice 3) Questions come from the whole picture, not her last answer, and every answer updates a live picture with a lean bar and clarity bar — following up on each answer felt like an interrogation with no visible progress.
- Skip and a gentle "more answers would help" line instead of a fixed number of questions.
- Statements show readable titles, with S# only as an identifier — they shouldn't feel like mysterious codes.
- Choosing values is separate from setting importance, and importance has its own step before the board.
- Dealbreakers are marked on the choosing step and are distinct from importance.
- Importance uses a 0–10 scale.
- Option scores are reviewed and adjusted on the board, not in a separate step.
- Crisis language stops the decision flow and points her to a parent, friends, or a doctor.
- When a dealbreaker zeroes an option, the board explains the reason on that option — a silent zero would feel like the app overruling her.
- `Wait / neither` is scored by the AI like the other options, from her own statements — so staying put is judged on the same evidence.
- A failed AI call never costs her work; retry repeats only the failed step.
- Look: very friendly with a brainy touch.
- (After the build) Voice input in her own language with translation she reviews and accepts — so people who don't think in English can still answer in their own words.
- (After the build) Visual redesign to deep indigo glass with gradient accents.

## What We're Building

- Framing (decision + two options + `Wait / neither`).
- One-question-at-a-time interview with live, readable, numbered statements and user-controlled completion.
- Statement review (edit, remove).
- Value choosing (AI-proposed with citations; rename, remove, add; dealbreakers).
- Importance step (0–10).
- Decision board with fit, leader, adjustable cited option scores, sliders, tipping point, confidence, and future cards, all updating instantly.
- Citation guardrail and safety check.
- Optional voice input with reviewed English translation.

## Deferred From the POC

- Three or more primary options — two plus `Wait / neither` proves the core.
- Merging and splitting statements — editing and removing is enough to keep her in control.
- Saved sessions or history — would need storage/accounts, cut in scope.

## Possible Later Enhancements

- Decision-type-specific interview paths beyond career/relocation.
- Labels showing whose voice each reason is (her value, a fear, a comparison, someone else's opinion).
- "Worth checking" outside facts, kept separate from her own evidence.
- Gut check after revealing the leader, and a suggested small next step.

## Non-Goals

- Telling her what to choose — the board shows a calculated leader from her weights only.
- External research or facts inside the scores — everything comes from her words.
- Accounts, login, sync, sharing, images, video — they don't prove the core loop.
- Medical, legal, or financial advice.

## Open Questions

- **Support message details** — include a specific helpline number, or only the parent/friends/doctor guidance? Not blocking.
