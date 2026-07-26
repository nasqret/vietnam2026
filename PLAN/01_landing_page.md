# Module 01 — Landing page (`/vietnam2026`)

**Goal:** a self-contained, polished `index.html` that is the hub of the whole course — hero, the
six-lecture plan, per-lecture descriptions, status badges, and cross-links to book / lab / slides /
artifacts / GitHub. Style mirrors `classical-foundations-ann/index.html` (Inter, CSS variables, dark
hero, card grid) and is theme- and mobile-friendly.

## Subtasks
- [x] Hero: title, subtitle, author + affiliations, VIASM link, call-to-action buttons.
- [x] "The arc" section: the single narrative from λ-calculus → autoformalization.
- [x] Six lecture cards: number, title, abstract, sub-topics, status pill, "notes / slides / lab" links.
- [x] Resources strip: knowledge book, Lambda Lab, Obsidian vault, artifacts (4 provers), GitHub.
- [x] "Why now" panel: the 2024–2026 AI-for-proof landscape (fed by research).
- [x] Enrich abstracts from the research synthesis (the reading list lives in the book's references/appendix).
- [x] Language toggle: decided EN-only — the optional 中文/Tiếng-Việt stub was dropped by choice.

## Acceptance criteria
- Loads with no external JS beyond fonts; no console errors; passes a link check.
- Every card links somewhere real (even if the target is a "coming soon" anchor).
- Deployed to `~/public_html/vietnam2026/index.html`.
