---
doc: scope
status: approved
---

# Tipping Point

Tipping Point helps one person make sense of one two-option personal decision by turning only their own words into an interactive, traceable decision board.

## The Unique Kernel

It does not give generic advice or decide for someone. It connects every value and reason to the person's stated evidence, then lets them move the values' weights until they can see the exact threshold that would change the result.

## Who It's For

One person caught in a consequential personal choice and looping through the same pros and cons. The proof-of-concept demo follows Ayesha choosing between Berlin and San Francisco, while retaining a `Wait / neither` option.

## The Core Loop

The person enters a decision and two options, answers a short set of open questions, then inspects and edits the cited values, weights, dealbreakers, and option scores. They move a slider on the board to see the winner, confidence, and tipping point recalculate instantly.

## Inspiration & Identity

The experience should feel like a clear, personal decision workspace: evidence-led, calm, and empowering rather than prescriptive. Specific visual direction is intentionally deferred to the PRD.

## Why This Matters to the Learner

The learner wants a tool that is personally useful and can help a wider community make better decisions. They are also using this project to practice the hackathon's plan-first, flipped-interaction process.

## What "Working" Looks Like

At the end of the demo, Ayesha sees Berlin and San Francisco alongside `Wait / neither`, with a leading option and fit score, a code-calculated confidence score and what would raise it, cited values and reasons, a future card for each option, and the key tipping-point sentence. When she moves career growth from 6 to 9, the leading option flips instantly; the board updates and every claim remains traceable to something she said.

## The POC Boundary

- One complete decision session for one person: two primary choices plus `Wait / neither`.
- A short interview whose answers become numbered statements.
- Four to six user-editable values with statement citations, 0–10 weights, and a dealbreaker marker.
- Cited option/value scores that the user can adjust.
- Code-calculated weighted fit, dealbreaker handling, tipping-point sensitivity, and confidence using evidence, completeness, stability, and control.
- One interactive decision board that shows every core result at once, including one short user-input-only future card per option.
- A citation validator that drops any AI-generated line without a valid statement ID before the user sees it.
- A basic crisis-language check that switches to a supportive message.
- Optional voice input in the person's own language, translated to English and accepted by the person before it is used (added by the learner after the build: speaking in your own language makes the flipped interview open to people who don't think in English).

## Later

- Deeper, decision-type-specific interview flows beyond the concise demo questions.
- Richer support for many kinds of decisions beyond the career/relocation demonstration.
- Additional reasoning presentation such as separate labels for fears, comparisons, and other people's opinions.
- Persistent decision history, multiple saved scenarios, and collaboration.
- Three or more primary options (the POC stays at two primary choices plus `Wait / neither`).
- Merging and splitting statements (the POC supports reviewing, editing, and removing them).

## Explicitly Cut

- External factual research or advice inside the score: the proof must rely on the person's own words.
- A final recommendation made by the app: the board shows the calculated leader from the user's own weights, but never tells the person what to choose.
- Accounts, login, and cloud syncing: they do not prove the core loop in this hackathon proof of concept.
- A production-complete decision engine for every life situation: one convincing interactive scenario is the appropriate proof.
- Images, video, and sharing: they add polish but do not prove the core loop.
