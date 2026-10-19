# Tipping Point UI refresh

This refresh applies the image-2-inspired visual direction while keeping the existing plain HTML/CSS/JavaScript frontend, FastAPI backend, API endpoints, browser-session storage, decision engine, and OpenAI integration intact.

## Visual changes
- Deep indigo/blue background with animated, 3D-inspired gradient orbs.
- Translucent glass-like panels, subtle borders, glow, and depth.
- Violet/pink/cyan gradient accents and updated typography.
- Restyled framing, interview, thought list, score grid, option cards, clarity meter, and future cards.
- Responsive layouts for desktop, tablet, and mobile.
- Reduced-motion preference disables ambient animations.

## Important
- This is a CSS-first visual redesign. It does not replace the application's data model or API calls.
- The current app's existing step-by-step flow remains. The image mockup is a visual direction, not a literal static screenshot replacement.
- Scores and status labels still come from the existing application logic. Previously identified decision-logic issues should be fixed separately before public demo.
- Keep `.env` private. Use `.env.example` in public repositories and rotate any API key that has been included in a shared archive.

## Run locally
Follow the existing README setup instructions. No new runtime dependency was added for the visual refresh.
