# G036: full odd-prime lifting of the exponent in constructive HA

Date: 2026-08-27.

This is an additive, non-admitting development over the exact immutable
Alpha-v28 catalogue: 2,764 checked entries and Stable 432; catalogue SHA-256
`897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9`.
No kernel, tactic, codec, resource limit or frozen source is modified.

## Exact endpoint

`odd_prime_lifting_the_exponent` proves the full guarded blueprint statement
with actual relational outputs:

```text
∀ p x y d n a b.
  Prime(p) → 2<p → y<x → y≠0 → n≠0 → x=y+d →
  Dvd(p,d) → ¬Dvd(p,x*y) → Val(p,d,a) → Val(p,n,b) →
  ∃ X Y D.
    Pow(x,n,X) ∧ Pow(y,n,Y) ∧ X=Y+D ∧ D≠0 ∧
    Dvd(p,D) ∧ ¬Dvd(p,Y) ∧ Val(p,D,a+b).
```

Here `Val` denotes the existing bounded maximal valuation graph, not a new
valuation oracle; the displayed prime and nonzero hypotheses supply its
intended domain. The proof constructs both power values and their actual
positive natural difference. It does not assume a geometric sum, binomial
expansion, output valuation, prime-power decomposition of the exponent, or
the desired lifting identity.

The companion `odd_prime_lifting_the_exponent_value` proves the final
valuation for **every** supplied pair of actual power values and a difference
balance. Power functionality and natural cancellation identify any such
difference with the constructed one. Thus the result does not depend on a
chosen beta code or a conveniently selected output witness.

The guards `p>2`, `x>y>0`, `n>0`, `p|(x-y)`, and `p∤xy` are retained exactly.
No binary-prime extension is asserted. For example, at `p=2,x=3,y=1,n=2`,
the difference valuation is 3 rather than `1+1`. Primality also matters:
`p=9,x=28,y=1,n=3` gives a difference valuation of 2 rather than `1+0`.
These numerical examples are regression explanations, not proof evidence.

## Constructive proof route

1. For `x=y+d`, ordinary exponent induction constructs seven witnesses
   `A,B,R,T,Q,C,H` at every exponent `k+2`, satisfying

   ```text
   Pow(x,k+2,A), Pow(y,k+2,B), Pow(y,k+1,R), Pow(y,k,T),
   A=B+d*Q,
   Q=(k+2)*R+d*C,
   2*C=(k+2)*(k+1)*T+d*H.
   ```

   The base case uses the genuine square difference. The successor uses
   `Q'=x*Q+B`, `C'=y*C+Q` and `H'=y*H+2*C`. All expansion steps are ordinary
   checked equality certificates over the original PA axioms. The existing
   polynomial guide is only an untrusted authoring aid; no ring tactic or
   new inference rule is admitted.
2. At exponent `p`, the last balance and `p|d` imply `p|2*C`. Since `p` is
   prime and different from two, constructive coprime cancellation gives
   `C=p*c`. Hence `Q=p*(R+d*c)`. The actual power `R` is not divisible by
   `p`, and adding the actual multiple `d*c` preserves this nondivisibility.
   Thus the quotient is exactly `p` times a genuine nondivisor cofactor.
3. At every exponent `n` not divisible by `p`, the first correction gives
   `Q=n*R+d*C`. Prime nondivisibility of the actual factors proves `p∤Q`.
   Exponent one is separately constructed; exponent zero is excluded by
   the nondivisibility premise itself.
4. The actual valuation at a prime itself is proved to be one by extracting
   its genuine cofactor and cancelling in the natural numbers. The shared
   valuation-of-powers theorem then constructs `Val(p,p^e,e)`, including
   `e=0`. Exact cofactor and product lemmas construct the valuation graphs
   needed by the prime step and the coprime-exponent step.
5. Ordinary induction constructs `q=p^k`, the corresponding actual powers
   of `x,y`, their positive difference, and its exact valuation `a+k`.
   Finally the original valuation cofactor theorem constructs
   `n=p^b*u` with `p∤u`. The prime-power iteration followed by the proved
   coprime-exponent step yields the full result. Relational power composition
   identifies the composed exponent with the actual input `n`.

This proves the required lifting formula by small composable certificates,
without adding a large binomial-summation oracle to a definition.

## Conservative definition DAG

The three public builders in `odd_prime_lte_candidate.py` accept checked
natural terms, an explicit distinct-variable context, and a hygienic tag.
All generated binders, including inherited power/valuation binders, are
scanned for capture and the complete expansion is parsed in that context.

| Builder | Arguments | Exact meaning |
| --- | --- | --- |
| `power_difference_quotient_relation` | `a,b,n,A,B,d,q` | Two actual powers and the balances `a=b+d`, `A=B+d*q`. |
| `power_difference_second_order_relation` | `a,b,d,k,A,B,R,T,Q,C,H` | Four actual powers and the three correction balances above. No prime or valuation condition. |
| `lifted_power_difference_relation` | `p,a,b,n,e,A,B,D` | Actual powers, their positive p-divisible difference, nondivisibility of the second power, and its precise output valuation. |

The first two definitions depend on `Pow` only. The last depends on `Pow`,
`Dvd` and the unchanged `PowerValuation`; it is an **output certificate**
whose existence is proved. It is never a premise of the full endpoint.
The shared prime-valuation foundation is independent of LTE, totients and
squarefree kernels, so these campaigns do not depend circularly on one another.

## Frozen source and body evidence

The factory is `make_odd_prime_lte_candidate_theorems`. It contains 38
topologically ordered theorem specifications, 189 direct dependencies and
2,157 tactic commands. The actual original-kernel body receipts total
4,096 proof-node occurrences and 4,030 proof objects; the largest body has
583 nodes and the maximum depth is 63, below the unchanged 256-depth limit.

Source SHA-256:
`bd701478669f7a531fb4c387cf1e0949c57ef475a1675953cd5802cb43f62bdb`.

The only new prerequisite provider is the separately frozen 20-row
`prime_valuation_support_candidate`, SHA-256
`bbd6e661a575f6a39f7a71424611da36a16d34cb6704cbae2b918387cc0f66d2`.
All other premises are exact Alpha-v28 theorem specifications.

| Principal theorem | Statement SHA-256 |
| --- | --- |
| `lte_odd_prime_power_step` | `252a32c2227f7d425e953caa023299cb69bb8c2132b8a629ea7db87e6a342f0f` |
| `lte_coprime_exponent_step` | `91751802033df98e77f88a429be8ca6fd53cf21799214752ea23fbe697d30518` |
| `lte_prime_power_iteration` | `6ab6fe6bd8c9f1fd3d8d4c2d5deacb3295200392fe7544fcafcc78ef26a7192d` |
| `odd_prime_lifting_the_exponent` | `36da85a059e7c726b9b4708cd6d34696d387b13f962fe6148654df3f0c469f6b` |
| `odd_prime_lifting_the_exponent_value` | `703616c3381acc0809aac4629c10006424894b62fceb60c40899b783329eac22` |

Verification command, run from `peano-lab/py`:

```sh
python3 -m pytest -q tests/test_odd_prime_lte_candidate.py
```

Result: **196 passed in 227.40 seconds**, process exit zero. Each positive
body and adversarial replay runs in a fresh process with a 60-second wall
timeout and 45/50-second CPU guard. No kernel or live-proof limit is raised.
The tests cover all 38 bodies, forged/truncated bodies and false conclusions,
principal-root dependency removal/corruption, all generated binder captures,
alpha-equivalence, malformed terms, exact domain guards, the frozen shared
source, and 1,080 small numerical examples.

**Admission remains separate.** These are original-kernel dependency-curried
body receipts, not an empty-context transitive closure or independent Lean
receipt. The release must assemble and verify the actual full dependency DAG,
obtain independent Lean acceptance, and deliberately enroll it in a new Alpha
edition. This RFC does not claim a deployment or change Stable membership.
