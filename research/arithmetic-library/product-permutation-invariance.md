# Product invariance under β-coded reindexing

Status: **active native proof gate**. The checked library already proves
bounded-injection-implies-surjection, one-position product balance, and exact
product invariance for an interior/final swap. It does not yet contain the
general theorem described here.

## Conservative statement

For β-coded prefixes, write `At(r,s,i,j)` for the fully expanded decoded-value
relation and `Product(b,c,l,p)` for the existing fully expanded prefix-product
trace. The authoring abbreviation

$$
\operatorname{Aligned}(r,s,b,c,z,d,l)
\;:\!\Longleftrightarrow\;
\forall i,j,x,\; i<l\to
  \operatorname{At}(r,s,i,j)\to
  \operatorname{At}(b,c,j,x)\to
  \operatorname{At}(z,d,i,x)
$$

uses the bound only on the target position $i$; boundedness of the index map
separately supplies $j<l$. `Aligned` is not parser or kernel syntax. Every
public theorem expands it into ordinary first-order PA.

The intended endpoint is

$$
\begin{aligned}
&\operatorname{BoundedPrefix}(r,s,l)\land
  \operatorname{InjectivePrefix}(r,s,l)\land
  \operatorname{Aligned}(r,s,b,c,z,d,l)\\
&\qquad\land\operatorname{Product}(b,c,l,p)\land
  \operatorname{Product}(z,d,l,q)
  \quad\Longrightarrow\quad p=q.
\end{aligned}
$$

This orientation says that target position $i$ contains source position
$f(i)$. Surjectivity need not be a premise: the checked constructive finite
pigeonhole theorem derives it from boundedness and injectivity.

## Successor induction

For length $S n$, surjectivity exposes a position $i$ with $f(i)=n$.

1. If $i=n$, injectivity and the fixed last entry rule out value $n$ at every
   earlier position. Existing prefix lemmas restrict boundedness and
   injectivity to length $n$. Decompose both products, apply the induction
   hypothesis to the prefixes, identify the two last factors through
   alignment and `beta_at_unique`, and reattach the common factor.
2. If $i<n$, decode $f(n)=j$. Swap positions $i$ and $n$ in the index code and
   in the target factor code. The checked swap transports preserve index-map
   boundedness and injectivity, and
   `beta_product_swap_last_invariant` preserves the target product. The new
   index code fixes its last entry, reducing to the first branch.

The simultaneous-swap alignment proof has three constructive cases, obtained
from `beta_prefix_swap_last_reflect`:

- at $i$, both new codes expose their old final entries;
- at $n$, both expose their old entries at $i$;
- away from $i,n$, both reflect to the original codes and the original
  alignment hypothesis applies.

## Reviewed sublemmas

The implementation should expose these reusable rungs before the capstone:

- `finite_fixed_last_prefix_bounded`: a bounded injective successor prefix
  whose last decoded value is $n$ is bounded by $n$ on its old prefix;
- `beta_reindex_alignment_swap_last`: simultaneous interior/final swaps of
  the index and target-factor codes preserve pointwise alignment;
- `beta_product_reindex_fixed_last`: the successor product step when the
  index map already fixes its last position;
- `beta_product_permutation_invariant`: the full induction.

Names may change during proof engineering, but each logical role should remain
separately replayed and mutation-tested.

## Soundness and capacity gates

- No finite function, list, product, quotient, or permutation primitive may be
  added to the PA language.
- No `DNE` may occur in the certificates.
- Every statement must remain below the 8,192-character interactive ceiling.
- Each theorem receives two cold replays, empty-context kernel checking, exact
  statement/dependency hashes, and false-contract plus Cut mutation tests.
- The existing limits remain 500,000 structural occurrences, 100,000 distinct
  objects, and depth 256. They are changed only after a measured certificate,
  not in anticipation of one.

After this endpoint, the next small corollary identifies a reindexed
$1,\ldots,l$ product with relational factorial. That is the direct bridge to
the nonzero residue product used by Fermat; Wilson still additionally needs a
β-coded inverse involution and classification of the fixed points of
$x\mapsto x^{-1}$ modulo a prime.
