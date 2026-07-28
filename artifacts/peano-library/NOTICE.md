# Public modular-arithmetic catalog provenance

The 26 theorem specifications published in Peano Lab as `MOD5_THEOREMS` were
imported from `nasqret/peano-private-mathlib` at commit
`d2ba05dca952e2e33479923433f8d2fcd3409493`. The source catalog SHA-256 is
`91c88c1f3311cc0dc540671b169c270758ff6211e77716ed07bd3dd4f55c8380`.
The adjacent `mod5-source-validation-report.json` is the source repository's
unaltered pre-integration validation report. Its `current_live_use` fields
describe the old 4,096-node import limit. Peano Lab raises that untrusted
resource limit to 32,768 nodes, so all 26 public entries can now be imported.
The imported statements add no axioms. The current runtime snapshot may package
their dependency proofs in self-contained, kernel-checked `Cut` nodes; that
later representation does not rewrite this immutable source report.

Source license, preserved verbatim:

```text
MIT License

Copyright (c) 2026 Bartosz Naskrecki

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
