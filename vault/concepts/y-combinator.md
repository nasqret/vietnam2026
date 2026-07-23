---
title: Y-combinator
tags: [l2]
---

`Y = λf.(λx.f (x x))(λx.f (x x))` satisfies `Y f ↠ f (Y f)` — a fixed point of any `f`, giving recursion in the pure calculus. Why it is Turing-complete.

See also: [[church-encoding]], [[normal-form]].
