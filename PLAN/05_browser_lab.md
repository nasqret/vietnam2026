# Module 05 — Browser Lambda Lab (`/lab-lambda`)

**Goal:** run the `lambda_lab` REPL **directly in the browser**, no install, on static faculty hosting.
Tech: **Pyodide** (CPython → WASM) + **xterm.js** terminal. The `prompt_toolkit` input loop is replaced
by a browser-driven driver; command dispatch and Rich (ANSI) rendering are reused.

## Architecture
```
lab-lambda/
  index.html            (xterm.js terminal + boot UI, self-contained styling)
  js/terminal.js        (xterm wiring, input line editing, history)
  js/pyodide-boot.js    (load Pyodide, install pure-Py deps, mount lambda_lab, wire the driver)
  py/lab_web/driver.py  (web entrypoint: parse a line → dispatch → return ANSI text)
  py/lambda_lab/...      (vendored pure-Python subset of the lab, network/subprocess stubbed)
  vendor/                (pyodide + xterm assets, or CDN-pinned)
```

## Degradation rules (web build)
- `prompt_toolkit` → **removed**; input handled by xterm.js. `rich` → kept (emits ANSI).
- `openai` (LLM judge, `aristotle`) → **stubbed** with a friendly "not available in browser" message.
- `subprocess` / `lake` / `lean` verify → **stubbed**; `lean` command shows read-only pre-baked output.
- `kb`, `church`, `reduce`, `lam`, `peano`, `curry_howard`, `tour`, `quiz`, `help`, `lang` → **work**.

## Subtasks
- [x] Static shell: xterm.js terminal + Pyodide boot with a progress line.
- [x] `driver.py` dispatching a first command set (`help church reduce lam`).
- [x] Vendor the pure-Python subset of `lambda_lab`; audit imports for Pyodide-safety.
- [x] Wire `tour`, `quiz`, `kb`, `peano`, `curry_howard` (+ `prove`, `ch`, tutorials, games); graceful stubs for the rest.
- [x] Persist history in `localStorage` (+ tab completion); `?cmd=` deep links wired book-wide.
- [x] Deploy to `~/public_html/lab-lambda/`; linked from the book + landing page (deep links, no iframe).

## Acceptance criteria
- Page loads Pyodide, prints a banner, and `help` + `church true` + `reduce (\x.x) y` all work.
- No network calls after asset load; runs offline once cached.

## Promotion (2026-07-24)

- [x] Worker + self-hosted build promoted to `/lab-lambda/` (build 2026-07-24a); `-next` = staging.
- [ ] Service-worker precache for guaranteed offline (next).

## Soundness overhaul (2026-07-26, build 2026-07-26a)

- [x] External audit implemented in full: rigid Atom/MetaVar kernel (`stlc_types`), one shared
      sound engine (`proof_builder`) behind both `prove` and `ch build`, checked `qed`,
      proof-wide substitution, free-variable rejection, exact command grammar, single
      interactive-owner routing in the driver, honest hints/`ch type` verdicts.
- [x] `tests/test_prove_soundness.py`: audit oracle + 21 regression groups × both front ends;
      lab suite 359 green; book gate + cookbook transcripts replay byte-identically.
