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
- [ ] Vendor the pure-Python subset of `lambda_lab`; audit imports for Pyodide-safety.
- [ ] Wire `tour`, `quiz`, `kb`, `peano`, `curry_howard`; graceful stubs for the rest.
- [ ] Persist history in `localStorage`; deep-link `?cmd=church%20true`.
- [ ] Deploy to `~/public_html/lab-lambda/`; embed via iframe in the book + landing page.

## Acceptance criteria
- Page loads Pyodide, prints a banner, and `help` + `church true` + `reduce (\x.x) y` all work.
- No network calls after asset load; runs offline once cached.
