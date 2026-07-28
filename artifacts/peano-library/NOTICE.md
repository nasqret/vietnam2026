# Public theorem-catalog provenance

## General-arithmetic extension

The 14 entries from `eq_symm` through `prime_two` originate at commit
`bb90b0b89ac5b408049bcc5370c0d2a1411e24e1`. Their compatibility audit and
reviewed merge are identified by
`90bd8dcd99b2765c8175df1ecdf60dc7f400d1d7`. The normalized audit added
exactly those 14 entries to the existing 49, preserved all earlier entries in
the same relative order, and found no change in any earlier certificate hash,
node count, or depth. These revisions establish source provenance only: the
current snapshot still replays every script and checks every closed
certificate independently.

## Modular-arithmetic extension

The 26 theorem specifications published in Peano Lab as `MOD5_THEOREMS` were
imported from `nasqret/peano-private-mathlib` at commit
`d2ba05dca952e2e33479923433f8d2fcd3409493`. The source catalog SHA-256 is
`91c88c1f3311cc0dc540671b169c270758ff6211e77716ed07bd3dd4f55c8380`.
The adjacent `mod5-source-validation-report.json` is the source repository's
unaltered pre-integration validation report. Its `current_live_use` fields
describe the old 4,096-node import limit. Peano Lab raises that untrusted
resource limit to 32,768 nodes, so all 26 public entries can now be imported;
the kernel and its rules are unchanged.

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
