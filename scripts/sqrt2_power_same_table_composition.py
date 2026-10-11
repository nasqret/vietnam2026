"""CV080: coefficient identity and rational tails on one full composition.

Keep CV031's actual atanh and factorial-weight tables. Construct their full
composition using CV077, transport the low coefficients using CV079, and
evaluate that very full table's low prefix using CV033. Code equality is
neither needed nor asserted. All statements are finite HA assertions.
"""
from hashlib import sha256
from types import MappingProxyType
import re

from sqrt2_power_supplied_composition_bound import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,conjoin,definition_registry as full_registry,
    supplied_composition_bound_source_pins,NAMED_SOURCE as FULL_SOURCE,
    OUTPUTS as ORIGINAL_FULL_OUTPUTS,PARTS as ORIGINAL_FULL_PARTS,
)
from sqrt2_power_normalized_composition import (
    NAMED_SOURCE as NORMALIZED_SOURCE,OUTPUTS as NORMALIZED_OUTPUTS,
    COEFFICIENT_DATA,INVARIANT,definition_registry as normalized_registry,
    normalized_composition_source_pins,
)
from sqrt2_power_composition_evaluation import NORMALIZED_ARCHIVE,GEOMETRIC_ARCHIVE
from sqrt2_power_geometric_horner import NAMED_SOURCE as GEOMETRIC_SOURCE,pattern
from sqrt2_power_successor_composition_transport import (
    NAMED_SOURCE as TRANSPORT_SOURCE,successor_composition_transport_source_pins,
)
from sqrt2_power_composition_tail_bound import TAIL_PARTS,CUT_OUTPUTS
from sqrt2_power_convolution_unit import _subst
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-same-table-composition-v1"
FULL_NAMES = {name:"f"+name for name in ORIGINAL_FULL_OUTPUTS}


def rename(source,mapping):
    """Simultaneous token renaming, never textual replacement inside a name."""
    return re.sub(r"\b(?:"+"|".join(map(re.escape,mapping))+r")\b",lambda m:mapping[m.group()],source)


FULL_OUTPUTS = tuple(FULL_NAMES[name] for name in ORIGINAL_FULL_OUTPUTS)
FULL_PARTS = tuple(rename(p,{**FULL_NAMES,"w0":"z"}) for p in ORIGINAL_FULL_PARTS)
NORMALIZED_DATA = conjoin((COEFFICIENT_DATA,"Factorial(N,fn)","Pow(d,N,pn)","z=fn*pn",INVARIANT))
FULL_DATA = conjoin(FULL_PARTS)
J = "((S N)*(S k))"
H = ("hb","hc")
EXPORTED_OUTPUTS = ("d","ab","ac","wb","wc","z","fn","pn",
    "fpb","fpc","fqb","fqc","frb","frc","fsb","fsc","fs","fv","fub","fuc")+H+("r","p3")
OUTPUTS = ("k","N")+EXPORTED_OUTPUTS
LOW_PATTERN = rename(pattern(),{"ab":"fub","ac":"fuc"})
CUT_AT_N = "exists "+" ".join(CUT_OUTPUTS)+". "+conjoin(tuple(rename(p,{"J":J,"M":"N","ub":"fub","uc":"fuc","w0":"z"}) for p in TAIL_PARTS))
PARTS = ("k=S K","N=S k","~d=0","NatAtanhPrefix(d,ab,ac,N)","NatExpWeightTable(d,N,wb,wc)",
    "BetaAt(wb,wc,0,z)","~z=0","Factorial(N,fn)","Pow(d,N,pn)","z=fn*pn",INVARIANT,
    FULL_PARTS[0],FULL_PARTS[5],FULL_PARTS[22],FULL_PARTS[4],FULL_PARTS[23],FULL_PARTS[21],
    "Le(N,"+J+")","Le(N,S "+J+")",LOW_PATTERN,
    "NatScaledHornerTrace(fub,fuc,3,N,hb,hc)","BetaAt(hb,hc,N,r)","Pow(3,k,p3)",
    "~p3=0","r+z=(2*z)*p3","~(z*p3)=0",FULL_PARTS[24],CUT_AT_N)
NAMED_SOURCE = "forall K. exists "+" ".join(OUTPUTS)+". "+conjoin(PARTS)
TARGET_SHA256 = "e5ce4e46386b9c0aa0cde7db11202d410819547dc4b6b462458184f2871f9611"
TRANSFER = "forall i a. Lt(i,N) -> BetaAt(cb,cc,i,a) -> BetaAt(ub,uc,i,a)"
PATTERN_C = rename(pattern(),{"ab":"cb","ac":"cc"})
PATTERN_U = rename(pattern(),{"ab":"ub","ac":"uc"})
HELPER_SOURCES = {
    "width":"forall N. Le(N,(S N)*N) /\\ Le(N,S((S N)*N))",
    "pattern_transport":"forall cb cc ub uc N z. ("+TRANSFER+") -> ("+PATTERN_C+") -> ("+PATTERN_U+")",
}
HELPER_TARGET_SHA256 = {"width":"68ebd50b81a16e2d12eae47d9a367494f341b4e5b43aaa134020d884c18602ac",
    "pattern_transport":"f6848ef780d7bc43821041376d0926ddde52269a28535f0a09a297ef6408d166"}
FULL_ARCHIVE = dict(case="CV077",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supplied-composition-bound-v1/generation-process.json.gz",
    bytes=99881,sha256="34ac810fa77d2751628940bcd8a6b2ae123fbee1c5e87d0f2c17f4631c96b902",
    raw_bytes=2729665,raw_sha256="537663b03f156dab01b8bb1a9670de3059b9b8f1686e554a78bb5d8c3b97b5ed",
    bundle_bytes=1661719,bundle_sha256="8b53d2ca3cedcb2b91b3752eb9b01fea4860ef11429582dc25a3b8a9efd78a41",
    nodes=317,root=316,target_ast_sha256="e21e4c6b538bc01cb88d592709a53809b0e7e69f1048918f9661e0965cd5e421")
TRANSPORT_ARCHIVE = dict(case="CV079",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-successor-composition-transport-v1/generation-process.json.gz",
    bytes=31595,sha256="6ee536a1e867412e0547f6db9628a978f71b40346a36f0b91c8ed1583d2c332e",
    raw_bytes=493153,raw_sha256="ec362389decd9dd25ab9038bdc313467b4c51185c05f3b4b4cebf79bf435cb14",
    bundle_bytes=262829,bundle_sha256="84fb9a7149a02574f575743f16e812568cf10e8c19c03e451a785ffeac535d55",
    nodes=55,root=54,target_ast_sha256="f7c56ab23847715134689855bfe86d7d7162eddbd0c52f9112dda1a9a5a89e2b")
ARCHIVES = (NORMALIZED_ARCHIVE,GEOMETRIC_ARCHIVE,FULL_ARCHIVE,TRANSPORT_ARCHIVE)
ENDPOINT_SOURCES = {
    "normalized_exists":NORMALIZED_SOURCE,"full_exists":FULL_SOURCE,
    "geometric_exists":GEOMETRIC_SOURCE,"transport":TRANSPORT_SOURCE,
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "zero_le":"forall a. Le(0,a)","succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "mul_right_mono":"forall a b c. Le(a,b) -> Le(a*c,b*c)",
    "one_mul":"forall a. 1*a=a","le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "le_refl":"forall a. Le(a,a)","mul_ne_zero":"forall a b. ~a=0 -> ~b=0 -> ~(a*b=0)",
}
ENDPOINT_OWNERS = {name:"CV031" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(full_exists="CV077",geometric_exists="CV033",transport="CV079")
HELPER_DEPENDENCIES = {
    "width":("zero_le","succ_le_succ","mul_right_mono","one_mul","le_succ"),
    "pattern_transport":("beta_exists","beta_unique"),
    "CV080":("normalized_exists","full_exists","geometric_exists","transport","width","pattern_transport",
        "zero_le","succ_le_succ","le_refl","mul_ne_zero"),
}


class SameTableCompositionError(ValueError):
    """Changed actual table, factorial normalization or rational tail evidence."""


def definition_registry():
    result = dict(full_registry())
    for name,d in normalized_registry().items():
        if name in result and (result[name].stable_id!=d.stable_id or result[name].template_formula!=d.template_formula):
            raise SameTableCompositionError("same-table conservative definition mismatch")
        result[name] = d
    return MappingProxyType(result)


def frozen_same_table_composition_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=1 or premises or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise SameTableCompositionError("CV080 exact same-table assembly changed")
    return target


def source_contract():
    return dict(code="CV080",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=0,inner_length="N=K+2",outer_terms="N+1",full_degree_bound="J=(N+1)*N",
        supplied_atanh_and_factorial_weight_codes_preserved=True,all_CV031_data_retained=False,
        all_CV077_data_retained=False,downstream_computation_and_normalization_data_retained=True,
        obsolete_small_trace_and_base_two_intermediates_not_exported=True,full_table_low_coefficient_pattern_proved=True,
        same_full_table_low_prefix_geometric_evaluation=True,geometric_identity="r+z=(2*z)*3^(N-1)",
        factorial_normalization="z=N!*d^N",normalization_nonzero=True,
        same_full_table_all_in_range_rational_tails=True,actual_tail_at_low_cutoff_constructed=True,
        tail_bound="tail(1/3)/z <= 9*(2/3)^N",code_number_equality_claimed=False,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",whole_value_at_three_constructed=False,
        analytic_limit_claim=False,closes_IR072=False,closes_IR079=False,closes_IR080=False,
        closes_IR081=False,IR_parents_closed=0,library_admissions=0)


def same_table_composition_source_pins():
    result = supplied_composition_bound_source_pins()
    for source in (normalized_composition_source_pins,successor_composition_transport_source_pins):
        for name,pin in source().items():
            if name in result and result[name]!=pin:
                raise SameTableCompositionError("same-table source pin disagreement")
            result[name] = pin
    expected = {
        "scripts/sqrt2_power_supplied_composition_bound.py":"291e01b84c94ae8482097626133077e987713f4b5e1d0f370e7bd88c3d50121b",
        "scripts/sqrt2_power_normalized_composition.py":"d2444ad39a22c50a6afbeb5f3ec3b67527c25f2c5985877ec4604dad08790d23",
        "scripts/sqrt2_power_successor_composition_transport.py":"dd2cfb71c2905bd7568cd6f05748252cf5a294fb99c7195935e64575699fff0f",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_same_table_composition.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise SameTableCompositionError("same-table source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _width(s,registry):
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        N = t.term("N");one = Succ(Zero());J = Mul(Succ(N),N)
        positive = apply(specialize(t,"succ_le_succ",Zero(),N),specialize(t,"zero_le",N))
        multiplied = apply(specialize(t,"mul_right_mono",one,Succ(N),N),positive)
        bound = _subst(t,registry,"Le(slot,(S N)*N)",specialize(t,"one_mul",N),multiplied)
        return conjunction(bound,apply(specialize(t,"le_succ",N,J),bound))
    return introduce(s,("N",),(),finish)


def _pattern_transport(s,registry):
    def chosen(t):
        transferred = apply(specialize(t,"transfer",*t.terms(("i","b"))),t.hyp("bound"),t.hyp("small_entry"))
        same = apply(specialize(t,"beta_unique",*t.terms(("ub","uc","i","b","a"))),transferred,t.hyp("large_entry"))
        old = apply(specialize(t,"pattern",*t.terms(("i","b"))),t.hyp("bound"),t.hyp("small_entry"))
        return _subst(t,registry,"(i=0 /\\ slot=z) \\/ (exists j. i=S j /\\ slot=2*z)",same,old)
    return introduce(s,("cb","cc","ub","uc","N","z"),("transfer","pattern"),lambda t:
        introduce(t,("i","a"),("bound","large_entry"),lambda u:
            eliminate(u,specialize(u,"beta_exists",*u.terms(("cb","cc","i"))),("b",),"small_entry",chosen)))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL,AndElimR,EqRefl
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def dimensions(t):
        k = Succ(t.term("K"));N = Succ(k)
        return k,N,Mul(Succ(N),N)
    def pattern_proof(t):
        _,N,J = dimensions(t)
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
    def evaluated(t):
        k,N,J = dimensions(t);geo = t.hyp("geometric");widths = specialize(t,"width",N)
        normalized,full = t.hyp("normalized"),t.hyp("full")
        data = field(normalized,0,5);small = field(data,0,5)
        nonzero_z = field(data,2,5)
        denominator = apply(specialize(t,"mul_ne_zero",*t.terms(("z","p3"))),nonzero_z,field(geo,3,5))
        cut = apply(instantiate(field(full,24,25),N),AndElimL(widths))
        return witness((k,N)+t.terms(EXPORTED_OUTPUTS),
            conjunction(EqRefl(k),EqRefl(N),*(field(small,i,10) for i in range(3)),field(data,1,5),nonzero_z,
                *(field(normalized,i,5) for i in range(1,5)),*(field(full,i,25) for i in (0,5,22,4,23,21)),
                AndElimL(widths),AndElimR(widths),pattern_proof(t),*(field(geo,i,5) for i in range(5)),
                denominator,field(full,24,25),cut))
    def full_chosen(t):
        k,_,_ = dimensions(t)
        return eliminate(t,apply(specialize(t,"geometric_exists",*t.terms(("fub","fuc","z")),k),pattern_proof(t)),
            H+("r","p3"),"geometric",evaluated)
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


def prove_same_table_composition(*,limits=None):
    registry = definition_registry()
    return assemble_mixed_certificate(code="CV080",target=frozen_same_table_composition_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,
        factories={"width":lambda s:_width(s,registry),"pattern_transport":lambda s:_pattern_transport(s,registry),"CV080":_root},
        pins=same_table_composition_source_pins,contract=source_contract(),limits=limits,new_induction_count=0)
