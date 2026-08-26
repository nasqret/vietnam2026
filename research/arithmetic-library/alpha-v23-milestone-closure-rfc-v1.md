# Alpha v23: three complete constructive campaign milestones

Status: reviewed additive original-kernel admission with independently
compiled Lean verification; the Stable release remains unchanged.

## Immutable checked parent

Alpha v22 contains exactly **1,890 checked-use theorems**, including exactly
**432 unchanged Stable theorems**. Its ordered enrollment identity is
`431f7300f9190f6fdc35ef84212e93701f2bb565b7e32c1624b7ae0c89cfc5ea`, its edition
identity is
`2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db`, and its
sealed catalog SHA-256 is
`fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22`.

Every historical theorem, source, proof certificate, Stable pointer, logical
signature, intuitionistic rule, and independent kernel remains unchanged.
Historical proof bodies are included only where an actual dependency needs
them; a hash authenticates their bytes but never replaces a proof check.

## Exactly three additive closed campaigns

1. **G101, Euclidean logarithmic complexity:** 17 independently checked
   constructive theorems with 48 direct dependencies. Ordinary induction over
   witnessed powers of two, exact two-step halving, and an actual beta-coded
   Euclidean history construct the terminal gcd and prove the exact blueprint
   inequality `steps <= 2*BitLen(b)+1`. A stronger theorem proves
   `steps <= 2*BitLen(b)`.
2. **G102, arbitrary-exponent binary modular execution:** 24 independently
   checked constructive theorems with 63 direct dependencies. Every natural
   exponent receives actual beta-coded canonical binary digits; its complete
   square-and-multiply trace computes the unique correct modular residue. An
   actual beta-coded population count proves the exact operation identity
   `steps = 2+2*BitLen(e)+BitCount(digits)` and therefore the blueprint bound
   `steps <= 3*BitLen(e)+2`.
3. **G025, infinitely many primes congruent to three modulo four:** 18
   independently checked constructive theorems with 46 direct dependencies.
   Decidable bounded search extracts an actual prime divisor in the residue
   class `4*k+3`; the subtraction-free Euclid witness `4*(c-1)+3` then produces
   a genuine prime strictly above every supplied bound.

Thus the immutable release contains **59 new theorems**, **1,949 total
checked-use theorems**, **1,517 Alpha-only theorems**, **432 Stable theorems**,
**6,285 direct theorem dependencies**, and **53 dependency-first layers**.
The additive ordered-name SHA-256 is
`7d24a436a735a83e20faf2a1378193560f9ea4fb4ae5c7f03e5fc812b39d69db`.
The new enrollment identity is
`f5d94af7a11c642d7076a195e2e795e7b84c61a6de1a6b074708669b2dac1648`; the
edition identity is
`02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85`.

## Self-contained independently checked certificate

The actual dependency cone contains **616 theorem proof bodies**, **nine
maximal checked theorem endpoints**, and one unenrolled synthetic packaging
root. The complete proof artifact contains **617 kernel-checked proof nodes**,
**1,871 dependency edges**, **39,161 structural body-proof nodes**, and exactly
**2,518,315 bytes**. Its SHA-256 is
`cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11`.

Its exact sources are 59 new proofs, 24 genuinely required reconstructed
historical proofs, and frozen original proof bodies from Alpha v19 frontier
(305), Alpha v19 residual closure (10), Alpha v20 (2), Alpha v21 (161), and
Alpha v22 (55). Reconstruction uses bounded one-theorem microbatches. Both the
unchanged original intuitionistic arithmetic kernel and a separately compiled
Lean verifier must accept the whole dependency-closed artifact before any
release manifest is written.

## Conservative reviewed definition DAG

Exactly eight additive reviewed definitions receive stable identities
`ND0038`–`ND0045`: `EuclideanBoundedTrace`,
`EuclideanLogarithmicExecution`, `BinaryExponentDigitCode`,
`BinaryCanonicalExponentDigitCode`, `BinaryCompleteModularExecution`,
`BinaryExecutionOperationCount`, `PrimeThreeModFourDivisor`, and
`EuclidThreeNumber`.

The older Quadratic Reciprocity definitions `Mod4Three` (`PD0012`), `AllBits`
(`PD0016`), and `BitCount` (`PD0017`) are reused by exact hygienic identity;
no duplicate residue-class or bit-count predicate is introduced. The full
global graph has **152 blueprint definitions**, **97 independently reviewed
conservative definitions**, **159 reviewed-definition dependency edges**, and
**61 signature-compatible reviewed blueprint identities**. Definition edges
never claim theorem-proof dependencies or new logical primitives.

No classical principle, general excluded middle, Markov principle, unbounded
choice, reflection axiom, external calculation, complexity oracle, or new sort
enters the unchanged first-order Heyting-arithmetic system.
