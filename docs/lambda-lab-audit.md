> **Status (2026-07-23):** all P0 semantic/correctness findings below were implemented in this
> repo and verified under the real Pyodide runtime + a 17-test regression suite (`lab-lambda/py/tests/`).
> P1 items (Web Worker, self-hosted assets + SRI/CSP, service-worker offline, server HTTPS-redirect/HSTS,
> real assistive-tech testing) remain open. Original audit follows verbatim.

---

# Lambda Lab — Full Functional, Mathematical, UX, Reliability, and Code Audit

**Target:** <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/>  
**Source repository:** <https://github.com/nasqret/vietnam2026>  
**Source revision audited:** `154c6525f0a4b0c424ba90c620d19a773eca8e3a`  
**Observed live page / audit date:** 2026-07-23  
**Prepared artifact:** `lambda-lab-audit-bundle.zip`  

---

## 1. Executive conclusion

Lambda Lab has a strong educational concept and a clean small architecture: a static page boots Pyodide, copies a compact Python lambda-calculus engine into Pyodide's in-memory filesystem, and presents it through xterm.js. The basic Church encodings are mostly correct, the normal-order beta reducer works on ordinary examples, capture-avoiding substitution is implemented thoughtfully, the UI is attractive, and the lab is easy to discover through examples, `help`, `tour`, and quick-action buttons.

The current build is nevertheless **not mathematically reliable enough to be treated as an authoritative checker**. Several defects affect the core semantics, rather than only presentation:

1. Alpha-equivalence is incorrect under variable shadowing.
2. Church numeral/boolean decoding compares binder *names* instead of binder *identity*.
3. The `alpha` command actually beta-normalizes both sides before comparing them, so it is not an alpha-equivalence command.
4. A fuel-exhausted reduction is still presented as a “Normal form.”
5. String-based constant expansion can corrupt valid lambda terms whose binders happen to use names such as `TRUE`.
6. `whnf` is an alias for full normalization even though WHNF and NF are different mathematical notions.
7. The site claims eta reduction, but the engine implements beta reduction only.

There are also important reliability issues: expensive terms execute synchronously on the browser's main thread; intermediate terms have no size bound; hidden decoder normalization can make a display command such as `church Z` unexpectedly expensive; and the claim that the lab works offline after first load is contradicted by `fetch(..., {cache: "no-store"})` and by mandatory external CDN assets.

The supplied fix overlay addresses the semantic bugs, separates strict alpha-equivalence from beta-convertibility, adds checked NF and real WHNF reduction, makes constant expansion scope-aware, adds binder-aware decoders, makes `POW m 0` beta-normalize to canonical Church `1`, imposes input/output/intermediate-AST limits, corrects the public claims, improves keyboard/accessibility behavior, and adds a substantive regression/property suite.

**Release judgment:** the current live build is suitable for curated demonstrations of simple closed terms, but it should not be used to grade arbitrary alpha-equivalence, decoding, or normalization answers until the high-severity findings are fixed.

---

## 2. Scope and method

### 2.1 What was audited

The review covered:

- the live landing page and its navigation;
- terminal startup and frontend control flow;
- command dispatch and every exposed command family;
- parser, AST, pretty-printer, free-variable calculation, substitution, alpha-equivalence, beta reduction, tracing, NF, and the hidden `whnf` alias;
- all named Church boolean, pair, arithmetic, comparison, fixed-point, and divergent constants;
- the decoder and quiz equivalence logic;
- mathematical wording in `help`, `about`, the knowledge base, and visible page copy;
- resource limits, responsiveness, caching/offline behavior, dependency failure behavior, privacy, basic security posture, and accessibility;
- current CI coverage and deployment documentation.

### 2.2 Evidence used

The live page was inspected directly. Source was reviewed at the pinned Git commit. The Python engine was executed locally using the repository implementation, with adversarial shadowing terms, divergent terms, boundary cases, complete boolean truth tables, and finite arithmetic property grids. The proposed replacement was then validated separately.

Key source files:

- [`lab-lambda/index.html`](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/index.html)
- [`lab-lambda/py/driver.py`](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/driver.py)
- [`lab-lambda/py/lambda_lab/lab/lc.py`](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/lambda_lab/lab/lc.py)
- [`lab-lambda/py/lambda_lab/lab/parser.py`](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/lambda_lab/lab/parser.py)
- [`lab-lambda/py/lambda_lab/lab/church.py`](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/lambda_lab/lab/church.py)
- [current CI workflow](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/.github/workflows/ci.yml)
- [deployment notes](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/docs/DEPLOY.md)

### 2.3 Audit limitations

The available browser inspection interface does not execute the live Pyodide/xterm application as an interactive human browser session. Core behavior was therefore exercised from the exact Python source under local CPython, and the replacement JavaScript was syntax-checked with Node. The audit did not complete a real-device matrix across Safari, Firefox, Chromium, mobile virtual keyboards, VoiceOver, NVDA, or JAWS. HTTP response headers were not captured, so CSP/HSTS/header recommendations are recommendations rather than confirmed header omissions.

---

## 3. Architecture review

### 3.1 Runtime flow

1. Static HTML, CSS, Google Fonts, xterm.js, the xterm fit add-on, and Pyodide are loaded.
2. The page constructs an xterm terminal on the main browser thread.
3. `boot()` loads Pyodide.
4. Seven same-origin Python source files are fetched and written into `/lab` in Pyodide's in-memory filesystem.
5. `driver.py` is imported, and terminal lines are synchronously passed to `driver.run_line`.
6. ANSI-formatted Python output is written back to xterm.

### 3.2 What is good

- No application backend is required.
- Ordinary terminal-entered expressions are evaluated locally.
- The Python source is small and auditable.
- Normal-order reduction is an appropriate teaching strategy because it reaches a normal form whenever one exists.
- The AST is immutable, making transformations easier to reason about.
- Substitution attempts to avoid capture and passes a direct capture test.
- The page provides visible boot status, command examples, history, and deep-link execution.
- External links use `rel="noopener"`.
- The visual contrast is strong and the mobile layout is simple.

### 3.3 Structural risks

- Python execution is synchronous on the UI thread. Official Pyodide guidance recommends a Web Worker for long-running synchronous work because main-thread execution can make the interface unresponsive: <https://pyodide.org/en/stable/usage/webworker.html>.
- The full startup path depends on multiple external origins.
- There is no cancellation protocol for a running reduction.
- The reducer is untyped and intentionally permits divergent terms; resource limits are therefore part of correctness, not merely optimization.
- The source preprocessor operates on text before parsing, which loses lexical scope information.

---

## 4. Functional inventory

| Area | Current behavior | Audit result |
|---|---|---|
| Boot/status | Loads Pyodide, fetches Python files, imports driver | Works in normal conditions; dependency failure and offline claims need correction |
| Quick buttons | Inject and immediately execute commands | Useful; silently ignored while booting |
| History | Up/down navigation in JS; duplicate unused Python history | Basic behavior is sound |
| Bare-term alias | Intended to run any term without `reduce` | Broken for ordinary applications such as `x y` |
| `help` / `commands` | Lists command surface | Clear, but mathematically inaccurate around alpha/WHNF/eta |
| `about` | Describes runtime and capabilities | Overstates compilation, eta support, and offline guarantees |
| `constants` | Lists Church constants | Good; omits usable `ZERO` alias |
| `church` / `numeral` | Displays definitions and decoded notes | Works for normal constants; hidden decoding is expensive for reducible/divergent constants |
| `peano` | Displays `SUCC (... ZERO)` | Presentation is good; displayed `ZERO` is not recognized by the evaluator |
| `expand` | Replaces named constants | Incorrectly text-based and not scope-aware |
| `lam` | Parses, prints, and reports free variables | Core parsing works; preprocessing can alter valid identifiers/binders |
| `reduce` | Up to 60 normal-order beta steps | Generally correct; exact-limit completion is mislabeled and output can explode |
| `nf` | Up to 1,000 beta steps | High-severity status bug: exhaustion is called “Normal form” |
| `whnf` | Alias to `nf` | Mathematically wrong |
| `decode` | Tries numeral then boolean | Binder-shadowing bug; hides the inherent `0 ≡ FALSE` overlap |
| `alpha` / `eq` | Normalizes both sides then alpha-compares | This is beta-convertibility for normalizing terms, not alpha-equivalence |
| `lean` | Shows read-only snippets | Useful and appropriately says the kernel is not running |
| `kb` | Small concept lookup | Good teaching feature; several formulations need nuance |
| `quiz` | Normalizes answers and alpha-compares | Can be affected by alpha and fuel-status bugs |
| `tour` | Runs curated examples | Curated examples are mathematically correct |
| `clear` | Clears terminal and reprints banner | Works in frontend only |
| `?cmd=` deep link | Executes URL command after boot | Useful, but query contents can be logged and can trigger expensive work |

---

## 5. Findings summary

Severity meanings:

- **High:** can return a mathematically wrong answer, misgrade a learner, or make a documented core operation seriously unreliable.
- **Medium:** significant functional, reliability, accessibility, privacy, or mathematical-description defect.
- **Low:** maintainability, polish, or limited edge-case concern.

| ID | Severity | Finding | Fix overlay |
|---|---:|---|---|
| LL-MATH-001 | High | Alpha-equivalence loses binder identity under shadowing | Fixed |
| LL-MATH-002 | High | Boolean/numeral decoders compare names, not binders | Fixed |
| LL-MATH-003 | Medium | `FALSE` and Church `0` are the same untyped term, but UI emits only one misleading label | Fixed in display |
| LL-MATH-004 | High | `alpha` performs beta normalization, so its name/result are mathematically false | Split into `alpha` and `equiv` |
| LL-MATH-005 | Medium | `POW m 0` produces eta-short identity, which the beta-only decoder cannot recognize as `1` | Fixed with eta-long definition |
| LL-MATH-006 | Medium | `whnf` is aliased to full NF | Fixed with head-only reducer |
| LL-MATH-007 | Medium | Site/about/docstrings claim eta reduction, but no eta reducer exists | Claims corrected; eta remains explicit future work |
| LL-FUNC-001 | High | Fuel-exhausted output is labeled “Normal form” | Fixed with checked reduction status |
| LL-FUNC-002 | Medium | A term normalizing on exactly step 60 is reported as unfinished | Fixed with one-step look-ahead |
| LL-FUNC-003 | Medium | Bare application alias rejects `x y`, `PLUS 2 3`, etc. | Fixed |
| LL-FUNC-004 | High | Text substitution expands bound names such as `TRUE` and corrupts valid syntax | Fixed by AST/scope-aware expansion |
| LL-FUNC-005 | Medium | Numeral regex rewrites digits inside valid apostrophe identifiers, e.g. `x'2` | Fixed with token-safe boundaries |
| LL-FUNC-006 | Low | `peano` teaches `ZERO`, but only `0` is defined | Fixed |
| LL-PERF-001 | High | Display-time decoders silently normalize again; `church Z` can freeze | Fixed; no hidden reduction of reducible constants |
| LL-PERF-002 | High | Main-thread execution and unbounded intermediate AST growth allow freezes | Mitigated with caps; Worker remains recommended |
| LL-PERF-003 | Medium | `normalize()` retains every intermediate AST in a list | Fixed with iterative checked normalizer |
| LL-REL-001 | Medium | “Works offline after first load” conflicts with `cache: "no-store"` and external assets | False claim removed; deterministic offline still future work |
| LL-REL-002 | Medium | Missing xterm script throws before `boot()` error handling | Fixed with dependency guard |
| LL-NAV-001 | Medium | Slashless course links were observed redirecting HTTPS to HTTP | Source links fixed; server redirect should also be corrected |
| LL-A11Y-001 | Medium | Terminal/status lack sufficient accessible metadata and screen-reader mode | Improved; real assistive-technology test still required |
| LL-UX-001 | Low | Quick buttons silently do nothing during boot | Fixed by visibly disabling them |
| LL-UX-002 | Medium | Unknown multi-byte escape sequences can be inserted and rendered as terminal controls | Fixed by rejecting escape/control sequences |
| LL-SEC-001 | Medium | CDN assets have no SRI/CSP/self-hosted fallback | Not fully fixed; roadmap item |
| LL-SEC-002 | Low | Error status is assembled with `innerHTML` | Fixed with DOM nodes and `textContent` |
| LL-PRIV-001 | Low | `?cmd=` values are in the URL and may be stored in logs/history | Explicitly documented |
| LL-TEST-001 | High | CI only checks for non-empty output; expected values are unused | Regression/property suite supplied |
| LL-MAINT-001 | Low | Dead parser `constants` argument, duplicate history, and inconsistent APIs | Documented; cleanup recommended |

---

## 6. Detailed mathematical and core-engine findings

### LL-MATH-001 — alpha-equivalence is wrong under shadowing

**Current implementation:** [`lc.py`, alpha-equivalence](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/lambda_lab/lab/lc.py#L202-L220)

The implementation keeps dictionaries from binder names on the left to binder names on the right. A dictionary cannot represent two simultaneously active binders with the same textual name. An inner binder overwrites the mapping for an outer binder.

Reproduction:

```text
alpha \x. \y. x = \x. \x. x
```

The current engine reports the terms equal. They are not alpha-equivalent:

- `λx. λy. x` returns the **outer** binder, De Bruijn index `1`.
- `λx. λx. x` returns the **inner** binder, De Bruijn index `0`.

This defect affects the public `alpha` command and quiz comparisons.

**Implemented fix:** compare bound occurrences by binder depth using parallel binder stacks. Free variables still compare by literal name.

### LL-MATH-002 — decoders also lose binder identity

**Current implementation:** [`church.py`, decoders](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/lambda_lab/lab/church.py#L172-L208)

Both decoders compare strings such as `body.name == f`. Under shadowing, the same string can identify different binders.

Concrete results from the original engine:

```text
try_decode_bool(λx. λx. x)  -> True     # wrong; this is FALSE
try_decode_numeral(λf. λf. f f) -> 1    # wrong; outer f is shadowed
```

The second error is directly visible:

```text
decode \f. \f. f f
```

is labeled as Church numeral `1` by the current build.

**Implemented fix:** decode beta-normal terms using the nearest enclosing binder's De Bruijn index. A Church numeral body must repeatedly apply binder index `1` and terminate at binder index `0`.

### LL-MATH-003 — `FALSE` and `0` overlap is mathematics, not a decoder tie to hide

The standard encodings are:

```text
FALSE = λt f. f
0     = λf x. x
```

These are alpha-equivalent. In untyped lambda calculus there is no type information with which to distinguish them. The current `_decode_note` checks numerals first, so every false boolean normal form is displayed only as `0`.

This is not a flaw in Church encoding. The flaw is presenting one arbitrary interpretation as though it were unique.

**Implemented fix:** display:

```text
= 0 / FALSE  (the same untyped Church term)
```

A future typed mode could resolve the ambiguity contextually.

### LL-MATH-004 — `alpha` is actually beta-normal-form comparison

**Current implementation:** [`driver.py`, `cmd_alpha`](https://github.com/nasqret/vietnam2026/blob/154c6525f0a4b0c424ba90c620d19a773eca8e3a/lab-lambda/py/driver.py#L371-L385)

Both sides are normalized before `alpha_eq` is called. Therefore:

```text
alpha SUCC 2 = 3
```

returns true, although the original terms are not alpha-equivalent. They are beta-convertible and have alpha-equivalent beta-normal forms.

The message “the same function” is stronger still: equal normal forms establish beta-convertibility for terms whose normal forms were actually reached; they do not decide arbitrary extensional semantic equality, and eta is not considered.

**Implemented fix:**

- `alpha t = u` — strict alpha-equivalence, no beta or eta steps.
- `equiv t = u` — bounded beta-normalization, then alpha-comparison; returns “inconclusive” on exhaustion.
- `eq` aliases `equiv` for convenience.

### LL-MATH-005 — exponent zero is eta-short in a beta-only application

**Current constant:** `POW = λm n. n m`.

For exponent zero:

```text
POW 2 0 ->β λx. x
```

`λx.x` is eta-equivalent to Church numeral `1 = λf x. f x`, but it is not the canonical two-binder numeral under beta reduction alone. The current decoder therefore cannot decode `POW 2 0`.

**Implemented fix:** use the eta-long but extensionally equivalent definition:

```text
POW = λm n f x. n m f x
```

Now `POW m 0` beta-normalizes directly to `λf x. f x` and decodes as `1`, without adding eta reduction to the engine.

### LL-MATH-006 — WHNF and NF are not aliases

Current code sets:

```python
cmd_whnf = cmd_nf
```

Counterexample:

```text
λx. ((λy. y) z)
```

This is already in weak-head normal form because WHNF does not reduce under a lambda. Its full beta-normal form is `λx.z`.

**Implemented fix:** add a head-spine redex finder that reduces neither under lambdas nor inside arguments.

### LL-MATH-007 — eta support is claimed but absent

The live page advertises “alpha/beta/eta-reduction,” and the core docstring/section comments mention eta. The operational code contains only `beta_step`; there is no eta-redex detector, eta step, eta trace, or beta-eta normalizer.

**Implemented fix:** make the UI and help truthful: this is a beta reducer. Eta remains a concept in the knowledge base, explicitly marked as not automatically applied. This is preferable to silently changing equality semantics. A future `eta` or `betaeta` command can be added as a separate, opt-in operation.

---

## 7. Reduction, parsing, and command defects

### LL-FUNC-001 — an exhausted fuel budget is reported as a normal form

`normalize(t, max_steps=1000)` returns the last term even when another beta-redex exists. `cmd_nf` unconditionally labels that term “Normal form.”

Reproduction:

```text
nf OMEGA
```

After 1,000 steps, `OMEGA` still has a beta-redex. The current UI nevertheless calls it a normal form.

This is a correctness defect. A bounded algorithm has three outcomes: completed, exhausted, or failed—not just a term.

**Implemented fix:** `normalize_checked` returns `{term, steps, complete, reason}`. The driver labels an incomplete term as partial and never decodes it as though it were a normal form.

### LL-FUNC-002 — exact trace-bound completion is misclassified

`cmd_reduce` treats `steps >= MAX_TRACE` as unfinished. A term that takes exactly 60 steps to normalize is therefore reported as “no normal form reached.”

**Implemented fix:** after the final allowed step, perform a non-mutating look-ahead with `beta_step(last)`. If no redex remains, the term completed exactly at the boundary.

### LL-FUNC-003 — documented bare-term alias rejects ordinary applications

Dispatch accepts an unknown line as a term only when it contains one of `λ\.()` or is a single identifier. The simplest lambda-calculus application:

```text
x y
```

is rejected as an unknown command. So are `PLUS 2 3` and `AND TRUE FALSE` when entered without `nf`/`reduce`, despite help saying “just type a term.”

**Implemented fix:** after real command and desktop-only checks, attempt every remaining line as a bare term. A misspelled command such as `hlep` was already treated as a variable; this makes the rule consistent.

### LL-FUNC-004 — source-string constant expansion is not scope-aware

The current evaluator performs regex replacement before parsing:

```python
_prepare(src) = expand_named(_expand_numbers(src))
```

This cannot distinguish the free constant `TRUE` from a user binder named `TRUE`.

Reproduction:

```text
lam \TRUE. TRUE
```

This is a valid identity function with a legal identifier. Current expansion rewrites both the binder and occurrence into lambda bodies and causes a parse error.

**Implemented fix:**

1. Expand numeric literals with token-safe boundaries.
2. Parse to an AST.
3. Traverse the AST and expand only **free** variables whose names are constants.
4. Track the expansion stack to detect accidental cyclic definitions.

### LL-FUNC-005 — the numeral regex changes a valid identifier

The parser permits apostrophes after the first identifier character. Thus `x'2` is one identifier. The current number pattern `\b\d+\b` sees the `2` as a standalone number and transforms the term into an application of `x'` to Church `2`.

**Implemented fix:** reject matches adjacent to either word characters or apostrophes:

```regex
(?<![\w'])\d+(?![\w'])
```

Negative literals also receive a direct “Church numerals are non-negative” error instead of a confusing parser error.

### LL-FUNC-006 — displayed `ZERO` cannot be copied back into the lab

`peano 3` displays an expression using `ZERO`, and the explanatory line defines `ZERO`. The constant table contains only key `"0"`, not `"ZERO"`. Copying the displayed expression leaves `ZERO` as a free variable.

**Implemented fix:** add `ZERO` as an alias of the same source as `0` and list both.

---

## 8. Performance and availability

### LL-PERF-001 — decoding performs hidden additional reduction

`_decode_note` calls the numeral decoder and then the boolean decoder. Each decoder normalizes internally. This means:

- `nf` may perform 1,000 steps, display a partial term as a normal form, then silently perform up to 700 more steps while decoding.
- `church <constant>` may normalize a reducible or divergent constant merely to decide whether to attach a value label.
- `church Z` is unexpectedly expensive. In the local original-source harness, the numeral decoder did not finish within a 3-second process timeout; `Y` took about 0.9 seconds on desktop CPython before the boolean decoder was even attempted.

**Implemented fix:** decoding functions for normal forms never reduce. Commands normalize exactly once, inspect the explicit completion flag, and decode only completed beta-normal forms. `church` does not attempt value decoding for a constant that already contains a beta-redex.

### LL-PERF-002 — main-thread and dynamic-size denial of service

The call `runLineFn(line)` is synchronous. Pyodide therefore executes reduction on the UI thread. A shared deep link can trigger an expensive command automatically.

The initial input limit on numerals does not limit result complexity. In a local growth probe, `POW 24 24` grew to approximately:

- 28,758 AST nodes after 5 beta steps;
- 80,171 nodes after 10 steps;
- 265,491 nodes after 30 steps.

The browser can become unresponsive long before the 1,000-step budget is reached.

**Implemented mitigation:**

- 4,000-character input limit;
- 20,000-node expanded-input limit;
- 50,000-node intermediate-reduction limit;
- rendered-term and total trace-output budgets;
- explicit partial/inconclusive status.

**Remaining architectural fix:** move Pyodide and the evaluator into a module Web Worker with request IDs and cancellation/termination. Fuel and node limits should remain even after the Worker migration.

### LL-PERF-003 — `normalize` stores the whole trace

Current `normalize` calls `trace`, which builds a list containing every intermediate AST. Normalization only needs the current term.

In a narrow `tracemalloc` harness for 1,000 `OMEGA` steps:

| Implementation | Peak traced Python allocation |
|---|---:|
| Current list-retaining normalizer | 97,304 bytes |
| Iterative checked normalizer | 784 bytes |

These figures are not total browser memory and should not be interpreted as a production benchmark. They demonstrate the avoidable allocation pattern.

**Implemented fix:** iterative normalization holds only the current term and status.

---

## 9. Reliability, offline behavior, and navigation

### LL-REL-001 — offline claim is contradicted by implementation

The page says “after the first load it works offline.” The deployment documentation repeats the claim. Yet every Python file is fetched with:

```javascript
fetch(rel + "?v=" + BUILD, { cache: "no-store" })
```

`no-store` instructs the browser not to use or update its HTTP cache for the request. See MDN: <https://developer.mozilla.org/en-US/docs/Web/API/Request/cache>.

In addition, startup requires external Google Fonts, xterm.js, its fit add-on, and Pyodide. Ordinary browser caching may make a repeat visit work in some circumstances, but this is not a deterministic offline design.

**Implemented fix:** remove `no-store` from Python source fetches and replace the claim with an accurate local-computation statement.

**Required for a real offline guarantee:** self-host all assets, version them, add a service worker/precache manifest, display offline readiness only after cache installation, and test cold/warm/offline startup.

### LL-REL-002 — xterm CDN failure bypasses boot error handling

`new Terminal(...)` is executed before `boot()` and outside its `try/catch`. If the xterm script fails to load, the inline script throws immediately and can leave the page at “starting…” without a useful explanation.

**Implemented fix:** verify `window.Terminal` and `window.loadPyodide` before terminal construction, and render a safe visible error.

### LL-NAV-001 — slashless links trigger an HTTPS-to-HTTP redirect

The live page uses `/vietnam2026` rather than `/vietnam2026/`. During the audit, following “Course” and “Lecture 2” resulted in a redirect reported as:

```text
https://.../vietnam2026  ->  http://.../vietnam2026/
```

Even if a user's browser later upgrades the request, the canonical redirect should never downgrade HTTPS.

**Implemented source fix:** use `/vietnam2026/` and `/vietnam2026/#l2`, avoiding the directory redirect.

**Server fix still required:** configure the canonical trailing-slash redirect to preserve HTTPS and enable/verify HSTS.

---

## 10. UX and accessibility

### Strengths

- Attractive, focused visual design.
- Good contrast and readable typography.
- Responsive terminal height.
- Useful quick-start examples.
- Clear boot status in the normal path.
- Keyboard history and cursor movement.
- A concise explanation immediately below the terminal.

### Defects and implemented improvements

1. **Boot controls:** quick buttons look active but are silently ignored while `busy`. The overlay disables them visibly until ready and during command execution.
2. **Screen readers:** the current terminal/status lack useful ARIA semantics and xterm screen-reader mode. The overlay adds `role=status`, `aria-live`, a terminal label, screen-reader mode, and a `<noscript>` explanation.
3. **Focus visibility:** explicit `:focus-visible` styling is added.
4. **Reduced motion:** spinner/transition motion now respects `prefers-reduced-motion`.
5. **Decorative dots:** marked `aria-hidden`.
6. **Key handling:** Home, End, and Delete are implemented. Unknown escape sequences are discarded instead of being inserted into the user buffer.
7. **Safe errors:** status text is built with DOM nodes and `textContent`, not string-concatenated `innerHTML`.
8. **Accurate capability text:** beta-only semantics and the deep-link privacy distinction are stated.

### Remaining UX work

- Add completion for commands/constants.
- Add a “Stop” button after the evaluator moves to a Worker.
- Add a copy button and a share-link builder that warns that `?cmd=` is stored in URL/history/logs.
- Add parser diagnostics with a source line and caret, not only a numeric position.
- Test selection/copy behavior versus the current Ctrl-C interrupt shortcut.
- Test mobile composition/input methods and Unicode cursor positions.
- Consider a non-terminal form view for learners who cannot use terminal widgets comfortably.

---

## 11. Security and privacy review

### Positive properties

- Typed terminal expressions are not posted to an application API.
- The Python evaluator has no deliberate network model integration.
- External links use `noopener`.
- User expressions are parsed into a restricted AST, not executed as Python.

### Concerns

#### External dependency integrity

The page executes scripts from jsDelivr and loads fonts from Google without Subresource Integrity. An effective CSP would also be difficult because the page uses inline script/style. This is a supply-chain and availability risk, not evidence that the current dependencies are compromised.

**Recommendation:** self-host pinned xterm/Pyodide/font assets, or add SRI where supported; move script/style to versioned files; set a restrictive CSP; verify `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS, and frame restrictions.

#### Terminal-control injection through input handling

Current fallback logic accepts any multi-character `onData` payload. Escape sequences not covered by the switch can be appended to `buffer`, and `redraw()` writes the buffer back to xterm, which interprets terminal controls.

**Overlay fix:** reject unknown escape-prefixed data and strip C0/DEL controls from pasted input.

#### Deep-link privacy

A typed term stays within the page runtime. A term in `?cmd=...` is different: it is part of the HTTP URL, browser history, copy/paste data, and potentially origin server logs. The overlay explicitly documents this distinction.

#### `innerHTML`

Current `statusFail` concatenates an error message into `innerHTML`. The practical exploit surface is limited because error sources are mostly internal paths/statuses, but safe DOM construction is straightforward and supplied.

---

## 12. Mathematical validation of the named constants

### 12.1 Correct in the tested range

The following were evaluated exhaustively on all boolean inputs and matched their conventional truth tables:

- `AND`, `OR`, `NOT`, `NAND`, `NOR`, `XOR`, `XNOR`, `IFF`, `IMPLIES`.

The pair operations were correct:

- `FST (PAIR a b) -> a`;
- `SND (PAIR a b) -> b`.

The following arithmetic operations were checked for all `m,n` in `0..4` and matched the expected natural-number result:

- `SUCC n = n+1`;
- `PRED n = max(0,n-1)`;
- `PLUS m n = m+n`;
- `MULT m n = m*n`;
- `SUB m n = max(0,m-n)`;
- `ISZERO n`;
- `LEQ m n`;
- `EQ m n`.

`POW m n` was correct for positive tested exponents. The exponent-zero canonical-form issue is addressed separately above.

The Y and Z definitions are recognizable standard fixed-point combinators. Their presence is mathematically appropriate in an untyped lab; the problem was hidden normalization and lack of resource control, not their definitions.

### 12.2 Wording that needs nuance

- **“Mathlib is classical.”** Lean's kernel/type theory is constructive; classical principles are available explicitly and are widely used in Mathlib. The overlay uses that wording.
- **Curry style versus Hindley–Milner.** Principal type inference for unannotated simply typed lambda terms is related to, but should not be equated without qualification to full Hindley–Milner let-polymorphism.
- **“Same function.”** Alpha-equivalence is syntax modulo binder renaming; beta-convertibility is an equational theory; extensional function equality additionally invokes eta or semantics. The UI should name the relation it actually checks.
- **Normal form.** The engine computes beta-normal forms. If eta is not implemented, it should not use “beta/eta normal form” language.
- **Volatile counts.** Hard-coded Mathlib theorem/line counts and project job counts should include a date/source or be removed from the embedded KB.

---

## 13. Testing and CI audit

### Current CI weakness

The existing lab-engine job loops over tuples such as:

```python
("nf PLUS 2 3", "5")
```

but the `expect` value is never asserted. It only checks that output is non-empty. A command can return a parse error, wrong number, or false normal-form claim and still pass CI.

There are no tests for:

- alpha-equivalence shadowing;
- capture avoidance;
- Church decoder shadowing;
- all truth tables;
- arithmetic properties;
- divergence/fuel status;
- exact trace boundary;
- WHNF semantics;
- constant-binding scope;
- numeric-token boundaries;
- deep-link/front-end boot;
- accessibility or offline behavior.

### Supplied suite

The overlay includes `lab-lambda/py/tests/test_regressions.py` and a CI job fragment. It currently has **17 test methods**, including:

- alpha shadowing and positive alpha cases;
- capture-avoiding substitution;
- shadow-safe boolean/numeral decoding;
- explicit `0 / FALSE` display;
- `POW m 0 = 1` for several bases;
- `ZERO` alias;
- bound constant names;
- apostrophe-digit identifiers;
- bare applications;
- divergence status;
- dynamic AST growth limit;
- exact 60-step completion;
- WHNF versus NF;
- strict alpha versus beta-equivalence;
- all boolean truth tables;
- an arithmetic grid over `0..4`.

Validation performed on the supplied overlay:

```text
Python unittest: 17 tests, 0 failures
Python compileall: pass
Inline JavaScript node --check: pass
```

The next CI layer should serve the static directory and run Playwright in Chromium/Firefox/WebKit. A future self-hosted build should include a warm-cache/offline test and a Worker cancellation test.

---

## 14. Implemented fix overlay

The bundle contains a complete file overlay rather than modifying or deploying the public repository.

### `lab-lambda/py/lambda_lab/lab/lc.py`

- shadow-safe alpha-equivalence using binder depth;
- iterative checked normalizer;
- explicit completion/reason status;
- exact-bound look-ahead;
- real weak-head reduction;
- iterative AST size counter;
- optional intermediate node limit.

### `lab-lambda/py/lambda_lab/lab/church.py`

- scope-aware AST constant expansion;
- cycle detection for named definitions;
- binder-aware normal-form decoders;
- no hidden successful decode after fuel exhaustion;
- `ZERO` alias;
- eta-long `POW` definition.

### `lab-lambda/py/driver.py`

- all remaining input is consistently treated as a possible bare term;
- strict `alpha` and separate `equiv`;
- honest NF/WHNF/partial/inconclusive statuses;
- no hidden decoder normalization;
- explicit `0 / FALSE` ambiguity;
- input, AST, intermediate growth, rendered-term, and trace-output limits;
- safer numeral preprocessing;
- corrected KB/about/help wording;
- reduced risk from `church Y/Z/OMEGA` display;
- `ZERO` listed and accepted;
- bounded quiz/tour comparisons.

### `lab-lambda/index.html`

- slash-correct course links;
- accurate beta-only/local-computation/offline wording;
- dependency guard;
- safe status DOM updates;
- disabled boot/busy buttons;
- screen-reader mode and ARIA improvements;
- reduced-motion and focus styles;
- Home/End/Delete handling;
- unknown escape/control filtering;
- normal browser caching for same-origin Python source.

### `lab-lambda/py/tests/test_regressions.py`

Full regression/property suite described above.

### `ci/lab-engine-job.yml`

A semantic test job to replace the current non-empty-output smoke test.

---

## 15. Prioritized roadmap

### P0 — before calling the live lab mathematically authoritative

1. Deploy the alpha-equivalence fix.
2. Deploy checked normalization status; never call an exhausted term a normal form.
3. Deploy scope-aware constant expansion.
4. Deploy binder-aware decoders and explicit `0 / FALSE` output.
5. Separate `alpha` from beta-equivalence.
6. Add the semantic regression suite to CI.
7. Add intermediate AST/output limits.

### P1 — reliability and truthful product behavior

1. Move Pyodide/evaluation to a module Web Worker.
2. Add cancellation and per-request IDs.
3. Self-host versioned xterm/Pyodide assets.
4. Implement a service worker only after assets are self-hosted; then test and truthfully advertise offline readiness.
5. Correct the server's HTTPS canonical redirect and verify HSTS.
6. Add browser integration tests for boot, quick buttons, history, deep links, dependency errors, and term execution.
7. Complete accessibility testing with keyboard-only operation and at least NVDA/Firefox, VoiceOver/Safari, and a mobile screen reader.

### P2 — educational quality and maintainability

1. Add parser caret diagnostics and command completion.
2. Add an explicit eta command, with examples distinguishing alpha, beta, eta, beta-eta, and extensional semantics.
3. Add typed contexts or a typed companion mode so `FALSE` versus `0` can be disambiguated by type.
4. Add sharing UI with a privacy warning for URL commands.
5. Remove the dead parser `constants` argument and duplicate Python history.
6. Add property-based/randomized tests for substitution, alpha-invariance, and confluence diamonds on bounded terms.
7. Version KB factual claims or link to maintained sources instead of embedding volatile counts.

---

## 16. Deployment checklist for the overlay

1. Apply/copy the supplied `lab-lambda/` overlay in a branch.
2. Merge the supplied CI job into `.github/workflows/ci.yml`.
3. Run:

   ```bash
   cd lab-lambda/py
   python -m unittest discover -s tests -v
   ```

4. Serve `lab-lambda/` over local HTTP and perform browser smoke tests.
5. Test these commands manually:

   ```text
   alpha \x. \y. x = \x. \x. x
   alpha \x. x = \y. y
   equiv SUCC 2 = 3
   decode FALSE
   decode \f. \f. f f
   nf POW 2 0
   nf OMEGA
   nf POW 24 24
   whnf \x. (\y. y) z
   lam \TRUE. TRUE
   lam x'2
   x y
   church Z
   peano 3
   ```

6. Verify the quick buttons remain disabled until boot completes.
7. Test a blocked-CDN scenario and confirm a visible startup error.
8. Verify course links remain HTTPS and preserve anchors.
9. Deploy to staging before replacing the live directory.
10. Do not claim deterministic offline operation until a self-hosted precache implementation passes an offline browser test.

---

## 17. Final assessment

The project is compact enough to repair cleanly, and its overall design is well suited to a course lab. Most named Church operations are mathematically sound. The major problems come from a small number of representation and status choices:

- treating binder names as binder identities;
- preprocessing scoped syntax as raw text;
- treating a bounded computation as though it were a decision procedure;
- conflating alpha-equivalence, beta-convertibility, eta, and semantic equality;
- running intentionally divergent/untyped computation without browser-grade resource isolation.

The supplied overlay corrects the first four categories and substantially mitigates the fifth. A Web Worker, self-hosted dependency bundle, service-worker-backed offline design, browser CI, and real assistive-technology testing remain the main production-quality steps.

**No changes were pushed to GitHub and nothing was deployed to the live faculty server.** The bundle is a tested local implementation overlay for review and controlled application.
