# Local Jordan definition adapter

`jordan_definition_extension.extend_registry(previous)` returns a new immutable
map. It retains every caller-supplied definition object and adds only eleven
conservative definitions, ND0371–ND0381. `definitions()` returns those eleven
objects, and `definition_edges()` returns only `definition_uses_definition`
arrows. No theorem-use or proof-dependency arrow is invented here.

ND0370 is intentionally unallocated. The initial proposed `JordanTupleEqual`
expansion was found to be exactly the existing ND0121 `IntegerVectorZero` AST.
Its historical name describes the zero difference of two integer vectors:
every pair of decoded coordinates is equal. The ordered argument mapping is
`(ab,ac,db,dc,l) = (b,c,d,e,k)`—left code/scale, right code/scale, common length.
There is no code equality, subtraction primitive, sign reinterpretation or
extra premise in this reuse. The adapter checks the exact five-parameter
template and retains the original object. The theorem sources are unchanged.

Enumeration, listing, scanning and common representatives therefore point
directly to `IntegerVectorZero`. The existing `BetaPrefixInto` and
`BetaPrefixEqual` identities also remain unchanged. All new expansions come
from the exact frozen Jordan75 builders and pass independent argument-renaming
AST comparisons. They are syntax only, not proof authority or Alpha admission.
