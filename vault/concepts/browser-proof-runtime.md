---
title: Browser proof runtime
tags: [browser, pyodide, web-worker, caching, performance]
---

A **browser proof runtime** separates static delivery from proof authority. [[peano-lab]] downloads
Pyodide and the prover into a disposable Web Worker; the faculty server serves files but runs no
Python proof process. A second one-shot [[rust-wasm-shadow-checker]] initializes independently and
receives a certificate only after authoritative Python QED.

Cold startup has three costs: transferring the WebAssembly and standard library, instantiating
Python, and importing the prover. Peano Lab compresses source-like responses, places pinned vendor
and application bytes below separate manifest-derived URL namespaces, keeps the HTML page uncached,
and fetches application sources concurrently while Pyodide starts. Complete versioned directories
are uploaded before the HTML pointer and retained after promotion; an unversioned response must
revalidate.

The current local candidate is build `2026-08-09a` with manifest identity
`a-a195e3ab28b3`. These labels identify local built bytes;
they do not assert that anything has been staged or deployed.

This optimization does not weaken the [[trusted-kernel]] boundary. Network completion order never
chooses a logical result: failed files are selected and successful files are mounted in a fixed
declaration order. After startup, every QED still checks the complete [[proof-certificate]] against
the original theorem. Stopping a command terminates the whole worker and its local runtime.

## Related

[[peano-lab-moc|Peano Lab MOC]] · [[peano-lab]] · [[trusted-kernel]] · [[proof-certificate]] ·
[[rust-wasm-shadow-checker]]
