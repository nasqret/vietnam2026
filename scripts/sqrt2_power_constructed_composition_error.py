"""CV085: construct the finite normalized composition and its rational errors.

Use the actual checked component proofs behind CV080, not its redundant
large intermediate root. The same input, factorial weights, power and
accumulation tables feed the coefficient pattern, full base-three evaluation
and tail bounds. Export the finite weighted sum and both rational errors.
No geometric pattern, tail bound, or computation witness is a premise.
"""
from hashlib import sha256

from sqrt2_power_same_table_composition import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,same_table_composition_source_pins,
    NORMALIZED_OUTPUTS,FULL_OUTPUTS,INVARIANT,conjoin,
    rename,FULL_PARTS,LOW_PATTERN,CUT_AT_N,
    ENDPOINT_SOURCES as SAME_ENDPOINTS,HELPER_SOURCES as SAME_HELPERS,
)
from sqrt2_power_supplied_composition_evaluation import (
    NAMED_SOURCE as EVALUATION_SOURCE,OUTPUTS as ORIGINAL_EVALUATION_OUTPUTS,
    supplied_composition_evaluation_source_pins,
)
from sqrt2_power_supplied_geometric_error import (
    NAMED_SOURCE as ERROR_SOURCE,supplied_geometric_error_source_pins,
)
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-constructed-composition-error-v1"
EVALUATION_OUTPUTS = tuple("e"+name for name in ORIGINAL_EVALUATION_OUTPUTS)
GEO_OUTPUTS = ("ghb","ghc","gr","p3")
TAIL_OUTPUTS = ("delta","tbx","tcx","u0","a2","q3","h3")
BASE_OUTPUTS = ("d","ab","ac","wb","wc","z","fn","pn")
VALUE_OUTPUTS = ("ex","ep","ev","evb","evc","ezb","ezc","es","p3","a2")
OUTPUTS = ("k","N")+BASE_OUTPUTS+VALUE_OUTPUTS
J = "((S N)*N)"
MONOMIALS = "forall j y a b c. Lt(j,S N) -> BetaAt(evb,evc,j,y) -> Pow(ep,j,a) -> Pow(3,j,b) -> Pow(ex,j,c) -> a*y=(ev*b)*c"
PARTS = ("k=S K","N=S k","~d=0","NatAtanhPrefix(d,ab,ac,N)","NatExpWeightTable(d,N,wb,wc)",
    "BetaAt(wb,wc,0,z)","~z=0","Factorial(N,fn)","Pow(d,N,pn)","z=fn*pn",INVARIANT,
    "NatHornerValue(ab,ac,3,N,ex)","Pow(3,N,ep)","Pow(3,"+J+",ev)",
    "NatPointwiseProductPrefix(wb,wc,evb,evc,ezb,ezc,S N)","Sum(ezb,ezc,S N,es)",MONOMIALS,
    "Pow(3,k,p3)","Pow(2,N,a2)","~ep=0","~ev=0","~p3=0","~(z*ev)=0","~((z*ev)*p3)=0",
    "IRatLe(es,0,z*ev,2*ep+9*a2,0,ep)","IRatLe(2,0,1,es*p3+z*ev,0,(z*ev)*p3)")
NAMED_SOURCE = "forall K. exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "390079559204a44746d65722e27b386315e6b9830542df520c3ed5acd50b4d58"
TABLE_OUTPUTS = ("fpb","fpc","fqb","fqc","frb","frc","fsb","fsc","fub","fuc")
COMPUTATION_OUTPUTS = BASE_OUTPUTS+TABLE_OUTPUTS
COMPUTATION_PARTS = tuple(rename(p,{"N":"(S(S K))","k":"(S K)"}) for p in
    PARTS[2:11]+(FULL_PARTS[0],FULL_PARTS[5],FULL_PARTS[22],LOW_PATTERN,CUT_AT_N))
EVALUATION_PARAMETERS = ("k","ab","ac","wb","wc","z")+TABLE_OUTPUTS
EVALUATION_PREMISES = tuple(rename(p,{"N":"(S k)"}) for p in
    ("~z=0",FULL_PARTS[0],FULL_PARTS[5],FULL_PARTS[22],LOW_PATTERN,CUT_AT_N))
EVALUATION_PARTS = tuple(rename(p,{"N":"(S k)"}) for p in PARTS[11:])
HELPER_SOURCES = {
    "computation":"forall K. exists "+" ".join(COMPUTATION_OUTPUTS)+". "+conjoin(COMPUTATION_PARTS),
    "evaluation":"forall "+" ".join(EVALUATION_PARAMETERS)+". "+" -> ".join("("+p+")" for p in EVALUATION_PREMISES)
        +" -> exists "+" ".join(VALUE_OUTPUTS)+". "+conjoin(EVALUATION_PARTS),
}
HELPER_TARGET_SHA256 = {
    "computation":"2527e4511867ae740637c9816241a5cd07751711cf853a9605df7d24e49ac1cc",
    "evaluation":"51fcba6ade65fcf0739ef46cd500f2a758a2c1f0f77a31d09815fdc6e5eb708a",
}
SAME_ARCHIVE = dict(case="CV080",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-same-table-composition-v3/generation-process.json.gz",
    bytes=157492,sha256="800e4508a43c0dfb246f6fafe33b5e2d8dd80eae7dd2684b217f3cfe18e3a002",
    raw_bytes=4212223,raw_sha256="2c9ccb42958bd058486073a66a6fd9bdc6ad2146029db53ac73025b9134c098a",
    bundle_bytes=2583524,bundle_sha256="739a6442d3cf4657fdb256c65867cd7b790f76676c457cd00f167d607a5b759c",
    nodes=426,root=425,target_ast_sha256="e5ce4e46386b9c0aa0cde7db11202d410819547dc4b6b462458184f2871f9611")
EVALUATION_ARCHIVE = dict(case="CV081",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supplied-composition-evaluation-v2/generation-process.json.gz",
    bytes=74264,sha256="f568f77c36be7e9f4757d46c56c4c92964185912c35c190db1e9e81f36ef4714",
    raw_bytes=1973251,raw_sha256="d0b6f7971e7854ec7491a2e3ee4f5ae3dd08daba05423e801e0ae2d86e9fa5b6",
    bundle_bytes=1198253,bundle_sha256="fb723fc358c8247fa1a3bef7a64b5c8c4292429c439b19843823037a8c8e4873",
    nodes=263,root=262,target_ast_sha256="afd8a2cb3249c998e8a875e5136ae8ea7ce51566569fff1a737c3bb58e6fb097")
ERROR_ARCHIVE = dict(case="CV084",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supplied-geometric-error-v1/generation-process.json.gz",
    bytes=37361,sha256="3c54dc20afecc08164b313e9447d694aa9724166cebf93b64225f89e4b56abdb",
    raw_bytes=632330,raw_sha256="1f18b0230db2660d3dad0a4de43c6c8cfc90c6c053ed72a02f1aabdbc10150f0",
    bundle_bytes=354089,bundle_sha256="a503bbe03a5d157fc56e871be761c191ffd3f399c409968b955e31a4e5b6e300",
    nodes=134,root=133,target_ast_sha256="4ee4edb3a27c63810499bc48918c92c504253b783efa6e306acf9c98ba79f558")
ARCHIVES = (SAME_ARCHIVE,EVALUATION_ARCHIVE,ERROR_ARCHIVE)
ENDPOINT_SOURCES = {name:SAME_ENDPOINTS[name] for name in
    ("normalized_exists","full_exists","geometric_exists","transport","zero_le","succ_le_succ","le_refl")}
ENDPOINT_SOURCES.update({name:SAME_HELPERS[name] for name in ("width","pattern_transport")})
ENDPOINT_SOURCES.update(evaluation_exists=EVALUATION_SOURCE,rational_errors=ERROR_SOURCE,
    power_unique="forall a n x y. Pow(a,n,x) -> Pow(a,n,y) -> x=y")
ENDPOINT_OWNERS = {name:"CV080" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(evaluation_exists="CV081",rational_errors="CV084")
HELPER_DEPENDENCIES = {
    "computation":("normalized_exists","full_exists","transport","zero_le","succ_le_succ","le_refl","width","pattern_transport"),
    "evaluation":("geometric_exists","evaluation_exists","rational_errors","power_unique","le_refl"),
    "CV085":("computation","evaluation"),
}


class ConstructedCompositionErrorError(ValueError):
    """Changed constructed finite sum, normalization or exact rational errors."""


def frozen_constructed_composition_error_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise ConstructedCompositionErrorError("CV085 exact unconditional finite error construction changed")
    return target


def source_contract():
    return dict(code="CV085",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,inner_length="N=K+2",outer_terms="N+1",full_degree_bound="J=(N+1)*N",
        same_actual_input_and_factorial_weights_for_all_parts=True,
        actual_input_value_scaling_powers_row_products_and_sum_constructed=True,
        exact_row_monomial_interpretation_retained=True,all_index_factorial_weight_normalization_retained=True,
        normalization="z=N!*d^N; v=3^J",all_rational_denominators_proved_nonzero=True,
        rational_upper="s/(z*v) <= 2+9*(2/3)^N",rational_lower="2 <= s/(z*v)+1/3^(N-1)",
        geometric_pattern_or_tail_bound_assumed=False,intermediate_CV080_root_replayed=False,
        checked_construction_and_evaluation_stages_separated=True,
        actual_reachable_component_bodies_fully_replayed=True,new_definition_ids=[],definition_admissions=0,
        original_HA_checked=False,authority="source_contract_not_proof_authority",analytic_limit_claim=False,
        closes_IR072=False,closes_IR079=False,closes_IR080=False,closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def constructed_composition_error_source_pins():
    result = same_table_composition_source_pins()
    for source in (supplied_composition_evaluation_source_pins,supplied_geometric_error_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:
                raise ConstructedCompositionErrorError("constructed composition source pin disagreement")
            result[name] = pin
    expected = {"scripts/sqrt2_power_same_table_composition.py":"a6d12ca8c148143f752f2bc34f8de57b20a88fa24c6f1476f2f27ae1b88015d8",
        "scripts/sqrt2_power_supplied_composition_evaluation.py":"34a9fe4f8e9f6d40b4ff464302ed339cecf11c7eb9ef3a7ae1f595c2c76d0a42",
        "scripts/sqrt2_power_supplied_geometric_error.py":"f59d0e1521b7ef67857545a7d7fe72d6a027d02b739c4bc7dc74ac0145f8f5d6",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_constructed_composition_error.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise ConstructedCompositionErrorError("constructed composition source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _computation(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def dimensions(t):
        k = Succ(t.term("K"));N = Succ(k)
        return k,N,Mul(Succ(N),N)
    def pattern_proof(t):
        _,N,_ = dimensions(t)
        def entry(u):
            _,NN,JJ = dimensions(u)
            small = field(field(u.hyp("normalized"),0,5),0,5);full = u.hyp("full")
            widths = specialize(u,"width",NN)
            rows = apply(specialize(u,"transport",*u.terms(("ab","ac")),NN,NN,Succ(JJ),
                *u.terms(("wb","wc","pb","pc","qb","qc","fpb","fpc","fqb","fqc",
                    "tb","tc","vb","vc","frb","frc","fsb","fsc")),NN),
                AndElimR(widths),field(small,5,10),field(full,0,25),field(small,6,10),field(full,5,25))
            return apply(instantiate(rows,Succ(NN),*u.terms(("cb","cc","fub","fuc","i","a"))),
                specialize(u,"le_refl",Succ(NN)),field(small,7,10),field(full,22,25),u.hyp("bound"),u.hyp("entry"))
        transfer = introduce(t,("i","a"),("bound","entry"),entry)
        return apply(specialize(t,"pattern_transport",*t.terms(("cb","cc","fub","fuc")),N,t.term("z")),
            transfer,field(field(t.hyp("normalized"),0,5),4,5))
    def full_chosen(t):
        _,N,_ = dimensions(t);norm,full = t.hyp("normalized"),t.hyp("full")
        data = field(norm,0,5);small = field(data,0,5)
        cut = apply(instantiate(field(full,24,25),N),AndElimL(specialize(t,"width",N)))
        return witness(t.terms(COMPUTATION_OUTPUTS),conjunction(
            *(field(small,i,10) for i in range(3)),field(data,1,5),field(data,2,5),
            *(field(norm,i,5) for i in range(1,5)),
            field(full,0,25),field(full,5,25),field(full,22,25),pattern_proof(t),cut))
    def normalized_chosen(t):
        k,N,_ = dimensions(t);data = field(t.hyp("normalized"),0,5);small = field(data,0,5)
        return eliminate(t,apply(specialize(t,"full_exists",*t.terms(("d","ab","ac")),k,N,*t.terms(("wb","wc","z"))),
            field(small,0,10),field(small,1,10),field(small,2,10),field(data,1,5),field(data,2,5)),
            FULL_OUTPUTS,"full",full_chosen)
    def begin(t):
        K = t.term("K");one = apply(specialize(t,"succ_le_succ",Zero(),K),specialize(t,"zero_le",K))
        width = apply(specialize(t,"succ_le_succ",Succ(Zero()),Succ(K)),one)
        return eliminate(t,apply(specialize(t,"normalized_exists",Succ(Succ(K))),width),NORMALIZED_OUTPUTS,"normalized",normalized_chosen)
    return introduce(s,("K",),(),begin)


def _evaluation(s,registry):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.terms import Mul,Succ,Zero
    three = Succ(Succ(Succ(Zero())))
    def dimensions(t):
        k = t.term("k");N = Succ(k)
        return k,N,Mul(Succ(N),N)
    def finished(t):
        k,N,J = dimensions(t);ev,tail,err = (t.hyp(n) for n in ("evaluated","tail","errors"))
        h_equal = apply(specialize(t,"power_unique",three,J,*t.terms(("h3","ev"))),field(tail,5,12),field(ev,3,9))
        q_equal = apply(specialize(t,"power_unique",three,N,*t.terms(("q3","ep"))),field(tail,4,12),field(ev,2,9))
        upper = _subst(t,registry,"IRatLe(es,0,z*slot,2*q3+9*a2,0,q3)",h_equal,field(err,11,13))
        upper = _subst(t,registry,"IRatLe(es,0,z*ev,2*slot+9*a2,0,slot)",q_equal,upper)
        lower = _subst(t,registry,"IRatLe(2,0,1,es*p3+z*slot,0,(z*slot)*p3)",h_equal,field(err,12,13))
        epnz = _subst(t,registry,"~slot=0",q_equal,field(err,4,13))
        evnz = _subst(t,registry,"~slot=0",h_equal,field(err,5,13))
        znz = _subst(t,registry,"~(z*slot)=0",h_equal,field(err,6,13))
        zpnz = _subst(t,registry,"~((z*slot)*p3)=0",h_equal,field(err,7,13))
        input_value = witness(t.terms(("eahb","eahc")),conjunction(field(ev,0,9),field(ev,1,9)))
        return witness(t.terms(VALUE_OUTPUTS),conjunction(input_value,field(ev,2,9),field(ev,3,9),
            field(ev,5,9),field(ev,6,9),field(ev,8,9),field(t.hyp("geometric"),2,5),field(tail,3,12),
            epnz,evnz,field(err,3,13),znz,zpnz,upper,lower))
    def tail_chosen(t):
        k,N,J = dimensions(t);tail,geo,ev = (t.hyp(n) for n in ("tail","geometric","evaluated"))
        prefix = witness(t.terms(("ghb","ghc")),conjunction(field(geo,0,5),field(geo,1,5)))
        full_value = apply(instantiate(field(ev,7,9),*t.terms(("fub","fuc"))),t.hyp("terminal"))
        full_value = _subst(t,registry,"NatHornerValue(fub,fuc,3,S slot,es)",field(tail,0,12),full_value)
        full_power = _subst(t,registry,"Pow(3,slot,h3)",field(tail,0,12),field(tail,5,12))
        premise = apply(specialize(t,"rational_errors",*t.terms(("fub","fuc","tbx","tcx")),k,
            *t.terms(("delta","z","gr","es","u0","p3","h3","q3","a2"))),
            t.hyp("head_nonzero"),prefix,field(geo,4,5),field(geo,2,5),
            field(tail,1,12),field(tail,2,12),full_value,full_power,field(tail,4,12),field(tail,3,12),field(tail,10,12))
        return eliminate(t,premise,("b3",),"errors",finished)
    def evaluated(t):
        return eliminate(t,t.hyp("cut"),TAIL_OUTPUTS,"tail",tail_chosen)
    def geometric_chosen(t):
        _,N,J = dimensions(t)
        evaluation = apply(specialize(t,"evaluation_exists",*t.terms(("ab","ac")),N,three,J,Succ(N),
            *t.terms(("wb","wc","fpb","fpc","fqb","fqc","frb","frc","fsb","fsc"))),
            specialize(t,"le_refl",Succ(J)),t.hyp("powers"),t.hyp("weighted"))
        return eliminate(t,evaluation,EVALUATION_OUTPUTS,"evaluated",evaluated)
    def begin(t):
        return eliminate(t,apply(specialize(t,"geometric_exists",*t.terms(("fub","fuc","z","k"))),t.hyp("pattern")),
            GEO_OUTPUTS,"geometric",geometric_chosen)
    return introduce(s,EVALUATION_PARAMETERS,("head_nonzero","powers","weighted","terminal","pattern","cut"),begin)


def _root(s):
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Succ
    def finished(t):
        k = Succ(t.term("K"));N = Succ(k)
        return witness((k,N)+t.terms(BASE_OUTPUTS+VALUE_OUTPUTS),conjunction(EqRefl(k),EqRefl(N),
            *(field(t.hyp("constructed"),i,14) for i in range(9)),
            *(field(t.hyp("bounds"),i,15) for i in range(15))))
    def constructed(t):
        k = Succ(t.term("K"));data = t.hyp("constructed")
        ev = apply(specialize(t,"evaluation",k,*t.terms(EVALUATION_PARAMETERS[1:])),
            *(field(data,i,14) for i in (4,9,10,11,12,13)))
        return eliminate(t,ev,VALUE_OUTPUTS,"bounds",finished)
    return introduce(s,("K",),(),lambda t:
        eliminate(t,specialize(t,"computation",t.term("K")),COMPUTATION_OUTPUTS,"constructed",constructed))


def prove_constructed_composition_error(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV085",target=frozen_constructed_composition_error_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"computation":lambda s:_computation(s,registry),"evaluation":lambda s:_evaluation(s,registry),"CV085":_root},
        pins=constructed_composition_error_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
