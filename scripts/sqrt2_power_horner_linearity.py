"""CV035: weighted linearity of constructed integer Horner evaluations.

The coefficient relation is a separate premise. All three actual traces and
endpoint values are constructed. Zero scalars, zero multiplier and empty
prefixes are allowed; no polynomial multiplication or limit assertion is made.
"""
from hashlib import sha256

from sqrt2_power_horner_trace import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,definition_registry,horner_trace_source_pins,
    NAMED_SOURCE as HORNER_SOURCE,HELPER_SOURCES as HORNER_HELPERS,
)
from sqrt2_power_geometric_horner import HORNER_ARCHIVE
from sqrt2_power_series_power_trace import CONVOLUTION_ARCHIVE
from sqrt2_power_mixed_assembly import assemble_mixed_certificate,read_mixed_archive

SCHEMA = "sqrt2-power-horner-linearity-v1"
A,B,C = ("ab","ac"),("bb","bc"),("cb","cc")
U,V,W = ("ub","uc"),("vb","vc"),("wb","wc")
PARAMETERS = ("alpha","beta","gamma")+A+B+C+("t","N")
OUTPUTS = U+V+W+("u","v","w")
GRAPH = "NatLinearTriple("+",".join(PARAMETERS[:9]+("N",))+")"


def trace(inputs,codes):
    return "NatScaledHornerTrace("+",".join(inputs+("t","N")+codes)+")"


TRACE_U,TRACE_V,TRACE_W = trace(A,U),trace(B,V),trace(C,W)
NAMED_SOURCE = "forall "+" ".join(PARAMETERS)+". "+GRAPH+" -> exists "+" ".join(OUTPUTS)+". "+TRACE_U+" /\\ ("+TRACE_V+" /\\ ("+TRACE_W+" /\\ (BetaAt(ub,uc,N,u) /\\ (BetaAt(vb,vc,N,v) /\\ (BetaAt(wb,wc,N,w) /\\ gamma*w=alpha*u+beta*v)))))"
TARGET_SHA256 = "ad3d9e7f204d9e713be5a888404827c60c7a6e4a2ceca04adb2deb516e9682df"
HELPER_SOURCES = {
    "mul_swap":"forall s t a. s*(t*a)=t*(s*a)",
    "shuffle":"forall alpha beta gamma t x y z a b c. gamma*z=alpha*x+beta*y -> gamma*c=alpha*a+beta*b -> gamma*(t*z+c)=alpha*(t*x+a)+beta*(t*y+b)",
    "all_rows":"forall "+" ".join(PARAMETERS+U+V+W)+". "+GRAPH+" -> "+TRACE_U+" -> "+TRACE_V+" -> "+TRACE_W+" -> forall k u v w. Le(k,N) -> BetaAt(ub,uc,k,u) -> BetaAt(vb,vc,k,v) -> BetaAt(wb,wc,k,w) -> gamma*w=alpha*u+beta*v",
}
HELPER_TARGET_SHA256 = {
    "mul_swap":"dacbf2e7ff423b37cf847a3b1ce181d4e71a0b0a580472b4b098a3d89c5c742f",
    "shuffle":"c9be7494476444cc8afe447d152d6e32d597c1a9ae8c19d6cfedcaaf581387e2",
    "all_rows":"c5d72895c48ad2118f2e6985435dbb5c79497ec9fb4a2f7bb0d419ef295085b7",
}
ARCHIVES = (HORNER_ARCHIVE,CONVOLUTION_ARCHIVE)
ENDPOINT_SOURCES = {
    "beta_exists":"forall b c i. exists a. BetaAt(b,c,i,a)",
    "beta_unique":"forall b c i a d. BetaAt(b,c,i,a) -> BetaAt(b,c,i,d) -> a=d",
    "zero_add":"forall a. 0+a=a","le_refl":"forall a. Le(a,a)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)","le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "mul_assoc":"forall a b c. (a*b)*c=a*(b*c)","mul_comm":"forall a b. a*b=b*a",
    "mul_add":"forall a b c. a*(b+c)=a*b+a*c", "add_assoc":"forall a b c. (a+b)+c=a+(b+c)",
    "add_comm":"forall a b. a+b=b+a",
    "horner_exists":HORNER_SOURCE,"step_value":HORNER_HELPERS["step_value"],
}
ENDPOINT_OWNERS = {name:"CV003" for name in ENDPOINT_SOURCES}
ENDPOINT_OWNERS.update(horner_exists="CV032",step_value="CV032")
HELPER_DEPENDENCIES = {
    "mul_swap":("mul_assoc","mul_comm"),
    "shuffle":("mul_add","mul_swap","add_assoc","add_comm"),
    "all_rows":("beta_unique","zero_add","beta_exists","le_succ","le_refl","le_trans","step_value","shuffle"),
    "CV035":("horner_exists","beta_exists","all_rows","le_refl"),
}


class HornerLinearityError(ValueError):
    """Changed weighted relation, actual evaluation or proof source."""


def frozen_horner_linearity_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=11 or len(premises)!=1 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise HornerLinearityError("CV035 exact constructed weighted evaluation changed")
    return target


def source_contract():
    return dict(code="CV035",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=1,pointwise_weighted_relation_required=True,three_actual_traces_constructed=True,
        three_actual_endpoint_values_constructed=True,all_row_linearity_proved=True,
        zero_scalars_and_multiplier_allowed=True,empty_prefix_allowed=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",multiplication_evaluation_identity=False,
        analytic_logarithm_identity=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def horner_linearity_source_pins():
    result = horner_trace_source_pins()
    expected = {"scripts/sqrt2_power_horner_trace.py":"32feca5a71d2b82367e6321d7a276c8c7de0f0fbf9b97513e22e816f80ee0328",
        "scripts/sqrt2_power_geometric_horner.py":"6179fa42c4437ed53db78fdc4f806d281d4774b58544150c7007dcfa3b656adc",
        "scripts/sqrt2_power_mixed_assembly.py":"ab949239264b1a7b161aa8203b40eb8c4e1d5d6d56402c05f1858b115865f624",
        **{p["path"]:p["sha256"] for p in ARCHIVES}}
    for name in (*expected,"scripts/sqrt2_power_horner_linearity.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise HornerLinearityError("Horner linearity source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _mul_swap(s):
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongMul,EqRefl,EqSym
    return introduce(s,("s","t","a"),(),lambda u:_chain(
        EqSym(specialize(u,"mul_assoc",*u.terms(("s","t","a")))),
        CongMul(specialize(u,"mul_comm",*u.terms(("s","t"))),EqRefl(u.term("a"))),
        specialize(u,"mul_assoc",*u.terms(("t","s","a")))))


def _shuffle(s):
    from sqrt2_power_quadratic_height import _chain,_additive_equal
    from peano_lab.kernel.proofs import CongAdd,CongMul,EqRefl,EqSym
    from peano_lab.kernel.terms import Add,Mul
    def finish(u):
        alpha,beta,gamma,t,x,y,z,a,b,c = u.terms(("alpha","beta","gamma","t","x","y","z","a","b","c"))
        ax,by,aa,bb = Mul(alpha,Mul(t,x)),Mul(beta,Mul(t,y)),Mul(alpha,a),Mul(beta,b)
        return _chain(specialize(u,"mul_add",gamma,Mul(t,z),c),
            CongAdd(specialize(u,"mul_swap",gamma,t,z),EqRefl(Mul(gamma,c))),
            CongAdd(CongMul(EqRefl(t),u.hyp("old")),u.hyp("input")),
            CongAdd(specialize(u,"mul_add",t,Mul(alpha,x),Mul(beta,y)),EqRefl(Add(aa,bb))),
            CongAdd(CongAdd(specialize(u,"mul_swap",t,alpha,x),specialize(u,"mul_swap",t,beta,y)),EqRefl(Add(aa,bb))),
            _additive_equal(u,Add(Add(ax,by),Add(aa,bb)),Add(Add(ax,aa),Add(by,bb))),
            CongAdd(EqSym(specialize(u,"mul_add",alpha,Mul(t,x),a)),EqSym(specialize(u,"mul_add",beta,Mul(t,y),b))))
    return introduce(s,("alpha","beta","gamma","t","x","y","z","a","b","c"),("old","input"),finish)


def _all_rows(s,target):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import Axiom,AndElimL,AndElimR,CongAdd,CongMul,EqRefl,EqSym,Ind
    from peano_lab.kernel.terms import Succ,Zero
    def base(t):
        def zero(codes,label,value,entry):
            return apply(specialize(t,"beta_unique",*t.terms(codes),Zero(),t.term(value),Zero()),t.hyp(entry),AndElimL(t.hyp(label)))
        uz,vz,wz = zero(U,"traceU","u","valueU"),zero(V,"traceV","v","valueV"),zero(W,"traceW","w","valueW")
        left = _chain(CongMul(EqRefl(t.term("gamma")),wz),instantiate(Axiom("PA5"),t.term("gamma")))
        right = _chain(CongAdd(CongMul(EqRefl(t.term("alpha")),uz),CongMul(EqRefl(t.term("beta")),vz)),
            CongAdd(instantiate(Axiom("PA5"),t.term("alpha")),instantiate(Axiom("PA5"),t.term("beta"))),specialize(t,"zero_add",Zero()))
        return _chain(left,EqSym(right))
    def successor(t):
        def chosen(u):
            k,N = u.terms(("k","N"))
            earlier = apply(specialize(u,"le_trans",k,Succ(k),N),apply(specialize(u,"le_succ",k,k),specialize(u,"le_refl",k)),u.hyp("bound"))
            previous = apply(specialize(u,"IH",*u.terms(("x","y","z"))),earlier,u.hyp("oldU"),u.hyp("oldV"),u.hyp("oldW"))
            coefficient = apply(specialize(u,"graph",*u.terms(("k","a","b","c"))),u.hyp("bound"),u.hyp("inputA"),u.hyp("inputB"),u.hyp("inputC"))
            def value(inputs,codes,label,old,new,a,old_entry,input_entry,new_entry):
                st = apply(instantiate(AndElimR(u.hyp(label)),k),u.hyp("bound"))
                return apply(specialize(u,"step_value",*u.terms(inputs+("t",)+codes+("k",old,a,new))),st,u.hyp(old_entry),u.hyp(input_entry),u.hyp(new_entry))
            ue = value(A,U,"traceU","x","u","a","oldU","inputA","valueU")
            ve = value(B,V,"traceV","y","v","b","oldV","inputB","valueV")
            we = value(C,W,"traceW","z","w","c","oldW","inputC","valueW")
            shuffle = apply(specialize(u,"shuffle",*u.terms(("alpha","beta","gamma","t","x","y","z","a","b","c"))),previous,coefficient)
            return _chain(CongMul(EqRefl(u.term("gamma")),we),shuffle,
                CongAdd(CongMul(EqRefl(u.term("alpha")),EqSym(ue)),CongMul(EqRefl(u.term("beta")),EqSym(ve))))
        def decode(u,remaining):
            if not remaining:
                return chosen(u)
            codes,name,label = remaining[0]
            return eliminate(u,specialize(u,"beta_exists",*u.terms(codes+("k",))),(name,),label,lambda v:decode(v,remaining[1:]))
        return decode(t,((U,"x","oldU"),(V,"y","oldV"),(W,"z","oldW"),(A,"a","inputA"),(B,"b","inputB"),(C,"c","inputC")))
    motive = target
    for _ in PARAMETERS+U+V+W:
        motive = motive.body
    motive = motive.right.right.right.right.body
    return introduce(s,PARAMETERS+U+V+W,("graph","traceU","traceV","traceW"),lambda t:Ind(motive,
        introduce(t,("u","v","w"),("bound","valueU","valueV","valueW"),base),
        introduce(t,("k",),("IH",),lambda u:introduce(u,("u","v","w"),("bound","valueU","valueV","valueW"),successor))))


def _root(s):
    from sqrt2_power_native import instantiate
    from peano_lab.kernel.proofs import AndElimL
    def chosen(t):
        traces = tuple(AndElimL(t.hyp(label)) for label in ("hornerU","hornerV","hornerW"))
        all_rows = apply(specialize(t,"all_rows",*t.terms(PARAMETERS+U+V+W)),t.hyp("graph"),*traces)
        values = tuple(t.hyp(label) for label in ("valueU","valueV","valueW"))
        relation = apply(instantiate(all_rows,*t.terms(("N","u","v","w"))),specialize(t,"le_refl",t.term("N")),*values)
        return witness(t.terms(OUTPUTS),conjunction(*traces,*values,relation))
    def decode(t,remaining):
        if not remaining:
            return chosen(t)
        codes,name,label = remaining[0]
        return eliminate(t,specialize(t,"beta_exists",*t.terms(codes+("N",))),(name,),label,lambda u:decode(u,remaining[1:]))
    def construct(t,remaining):
        if not remaining:
            return decode(t,((U,"u","valueU"),(V,"v","valueV"),(W,"w","valueW")))
        inputs,codes,label = remaining[0]
        return eliminate(t,specialize(t,"horner_exists",*t.terms(inputs+("t","N"))),codes,label,lambda u:construct(u,remaining[1:]))
    return introduce(s,PARAMETERS,("graph",),lambda t:construct(t,((A,U,"hornerU"),(B,V,"hornerV"),(C,W,"hornerW"))))


def prove_horner_linearity(*,limits=None):
    from sqrt2_power_definitions import parse_named
    registry = definition_registry()
    factories = {"mul_swap":_mul_swap,"shuffle":_shuffle,
        "all_rows":lambda s:_all_rows(s,parse_named(HELPER_SOURCES["all_rows"],registry=registry)),"CV035":_root}
    return assemble_mixed_certificate(code="CV035",target=frozen_horner_linearity_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        endpoint_owners=ENDPOINT_OWNERS,archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,
        pins=horner_linearity_source_pins,contract=source_contract(),limits=limits,new_induction_count=1)
