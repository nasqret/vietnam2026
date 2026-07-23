---
title: Church encoding
tags: [l2, core]
---

Data as pure functions. `true = λt f.t`, `false = λt f.f`; the numeral `n = λf x. fⁿ x`; `succ`, `plus`, `mult`, `pow = λm n. n m`. The predecessor is Kleene's famous trick.

See also: [[church-numeral]], [[y-combinator]], [[lambda-term]]. **Run:** `nf PLUS 2 3` in the [[lambda-lab]].
