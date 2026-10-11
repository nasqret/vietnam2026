"""CV027: convolution with a zero-headed period-two finite prefix.

For A[0]=0, A[1]=h and A[j+2]=A[j], construct the actual coefficients
u=(A*C)[i], v=(A*C)[i+2] and prove v=u+h*C[i+1] below the common width.
The proof shifts actual antidiagonal sum witnesses twice; no formal-series
or analytic algebra is assumed.
"""
from hashlib import sha256

from sqrt2_power_convolution_commutative import (
    ROOT,Scope,introduce,eliminate,witness,field,apply,specialize,conjunction,
    canonical,json_hash,read_archive,definition_registry,
    convolution_commutative_source_pins,CONVOLUTION_ARCHIVE,
    HELPER_SOURCES as COMM_HELPERS,ENDPOINT_SOURCES as COMM_ENDPOINTS,
    FUBINI_HELPERS,coefficient,
)
from sqrt2_power_convolution_unit import assemble_actual_certificate,_subst,_one_plus

SCHEMA = "sqrt2-power-periodic-convolution-v1"
A,B,C = ("ab","ac","N"),("bb","bc","N"),("cb","cc","N")
D,E = ("db","dc"),("eb","ec")
FIXED = ("ab","ac","bb","bc","cb","cc","N","i")
SHIFT = "forall j x y. Le(j,i) -> BetaAt(ab,ac,S j,x) -> BetaAt(bb,bc,j,y) -> x=y"
PERIOD = "forall j x y. Lt(S(S j),N) -> BetaAt(ab,ac,j,x) -> BetaAt(ab,ac,S(S j),y) -> x=y"
SLICE = "NatAffineSlice(ab,ac,1,1,bb,bc,N)"
NAMED_SOURCE = "forall ab ac cb cc N i h c. Lt(S(S i),N) -> BetaAt(ab,ac,0,0) -> BetaAt(ab,ac,1,h) -> ("+PERIOD+") -> BetaAt(cb,cc,S i,c) -> exists u v. "+coefficient(A,C,"i","u")+" /\\ ("+coefficient(A,C,"S(S i)","v")+" /\\ v=u+h*c)"
TARGET_SHA256 = "3850a7a9f34d3796dd4b8e08f3a80925758444d026b1c0ce93c108108af94dec"
HELPER_SOURCES = {
    "below":"forall j i N. Le(j,i) -> Lt(i,N) -> Lt(j,N)",
    "lower":"forall i N. Lt(S i,N) -> Lt(i,N)",
    "unpad":"forall ab ac N i a. Lt(i,N) -> BetaZeroExtend(ab,ac,N,i,a) -> BetaAt(ab,ac,i,a)",
    "one_index":"forall j. 1+1*j=S j",
    "slice_entry":"forall ab ac bb bc N j x y. "+SLICE+" -> Lt(j,N) -> BetaAt(ab,ac,S j,x) -> BetaAt(bb,bc,j,y) -> x=y",
    "head_tail":"forall "+" ".join(FIXED+("a","c","p","q"))+". Lt(S i,N) -> BetaAt(ab,ac,0,a) -> BetaAt(cb,cc,S i,c) -> ("+SHIFT+") -> "+coefficient(A,C,"S i","p")+" -> "+coefficient(B,C,"i","q")+" -> p=a*c+q",
}
HELPER_TARGET_SHA256 = {
    "below":"f88b6a7e7e066f232cb1eb9b65128ab5c3defe8f47f043d00d5718827ad05a2f",
    "lower":"01af287626703f57499bbdbd6e27304d2293e408237a9549bae2957727ead43a",
    "unpad":"260a3f34dd854c3938ee5e51c66e4ea635623880d924847b23b3750b7f1531c6",
    "one_index":"54935e7eb7e195aaaa2ae7485f44199542900cc2dc9f4b568cba17d789cb1e51",
    "slice_entry":"e269e7222d944376dacf6672c46a7c2ee5bbf8af653e1ac30897609f3ec05d1a",
    "head_tail":"d51b40e48ba6710af83971fd06edaf77841edd0809a1a9ca976b02c147f5b948",
}
COMM_ARCHIVE = dict(case="CV010",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-convolution-commutative-v1/generation-process.json.gz",
    bytes=25857,sha256="9692df33332a534be235cede982b6883c569e3357d3a75297bc890ed89bc839b",
    raw_bytes=505662,raw_sha256="95acbc19c77e2daf6efe0d6ec0e5f6af61a082da3b83a0b4ee7cb314ccebcb64",
    bundle_bytes=305383,bundle_sha256="35c67ca650e7222ffedb065f157777f40bd88d06acfb746314dcb8d6c6afb093",
    nodes=133,root=132,target_ast_sha256="3e62febc17b41a970070ca88e057e05ef7888d821a65f9019ac15bfb8fc5a825")
ARCHIVES = (CONVOLUTION_ARCHIVE,COMM_ARCHIVE)
ENDPOINT_SOURCES = {
    **{name:COMM_ENDPOINTS[name] for name in ("zero_add","add_succ_left","add_comm","one_mul","beta_exists","beta_unique","term_unique","diagonal_entry","coefficient_exists")},
    "mul_zero_left":"forall a. 0*a=0",
    "le_refl":"forall a. Le(a,a)",
    "le_trans":"forall a b c. Le(a,b) -> Le(b,c) -> Le(a,c)",
    "le_succ":"forall a b. Le(a,b) -> Le(a,S b)",
    "succ_le_succ":"forall a b. Le(a,b) -> Le(S a,S b)",
    "zero_le":"forall a. Le(0,a)",
    "lt_not_le":"forall a b. Lt(a,b) -> Le(b,a) -> false",
    "sum_head_tail":COMM_HELPERS["head_tail"],
    "slice_exists":FUBINI_HELPERS["slice_exists"],
}
HELPER_DEPENDENCIES = {
    "below":("succ_le_succ","le_trans"),
    "lower":("le_refl","le_succ","le_trans"),
    "unpad":("lt_not_le",),
    "one_index":("one_mul","zero_add","add_succ_left"),
    "slice_entry":("one_index","beta_unique"),
    "head_tail":("below","lower","unpad","one_index","zero_le","le_refl","succ_le_succ","le_of_succ_le_succ","beta_exists","beta_unique","diagonal_entry","term_unique","add_succ_left","zero_add","sum_head_tail"),
    "CV027":("slice_exists","coefficient_exists","beta_exists","below","lower","zero_le","succ_le_succ","slice_entry","one_index","head_tail","mul_zero_left","zero_add","add_comm"),
}
ENDPOINT_SOURCES["le_of_succ_le_succ"] = "forall a b. Le(S a,S b) -> Le(a,b)"


class PeriodicConvolutionError(ValueError):
    """Changed range, initial data, finite period or actual proof bytes."""


def frozen_periodic_convolution_target():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = parse_named(NAMED_SOURCE,registry=definition_registry())
    binders,premises,conclusion = strip_target(target)
    if binders!=8 or len(premises)!=5 or type(conclusion) is not Exists or json_hash(encode_formula(target))!=TARGET_SHA256:
        raise PeriodicConvolutionError("CV027 exact finite periodic convolution target changed")
    return target


def source_contract():
    return dict(code="CV027",schema=SCHEMA,source=NAMED_SOURCE,statement_ast_sha256=TARGET_SHA256,
        premise_count=5,actual_initial_values_and_period_required=True,actual_coefficients_constructed=True,
        strict_index_bound_required=True,actual_head_tail_antidiagonal_transport=True,
        new_definition_ids=[],definition_admissions=0,original_HA_checked=False,
        authority="source_contract_not_proof_authority",logarithm_identity=False,
        exp_composition_recurrence=False,analytic_limit_claim=False,
        closes_IR079=False,closes_IR080=False,closes_IR081=False,closes_IR072=False,
        IR_parents_closed=0,library_admissions=0)


def periodic_convolution_source_pins():
    result = convolution_commutative_source_pins()
    expected = {
        "scripts/sqrt2_power_convolution_commutative.py":"d1d4ce7c0e78c03ba5961710b048fe11bcb3dd481afd2e79d5cc2b418b0412a3",
        "scripts/sqrt2_power_convolution_unit.py":"d058762fb3641d5bb1e90c764c4581801feeaf0a103901811b3e82dbe3db8f16",
        **{pin["path"]:pin["sha256"] for pin in ARCHIVES},
    }
    for name in (*expected,"scripts/sqrt2_power_periodic_convolution.py"):
        with (ROOT/name).open("rb") as stream:
            raw = stream.read(2*1024**2+1)
        digest = sha256(raw).hexdigest()
        if len(raw)>2*1024**2 or name in expected and digest!=expected[name]:
            raise PeriodicConvolutionError("periodic convolution source or actual archive changed")
        result[name] = dict(bytes=len(raw),sha256=digest)
    return result


def _below(s):
    from peano_lab.kernel.terms import Succ
    return introduce(s,("j","i","N"),("small","bound"),lambda t:
        apply(specialize(t,"le_trans",Succ(t.term("j")),Succ(t.term("i")),t.term("N")),
            apply(specialize(t,"succ_le_succ",*t.terms(("j","i"))),t.hyp("small")),t.hyp("bound")))


def _lower(s):
    from peano_lab.kernel.terms import Succ
    def finish(t):
        i,N = t.terms(("i","N"))
        small = apply(specialize(t,"le_succ",Succ(i),Succ(i)),specialize(t,"le_refl",Succ(i)))
        return apply(specialize(t,"le_trans",Succ(i),Succ(Succ(i)),N),small,t.hyp("bound"))
    return introduce(s,("i","N"),("bound",),finish)


def _unpad(s):
    from peano_lab.kernel.proofs import AndElimL,AndElimR,BotElim,OrElim
    return introduce(s,("ab","ac","N","i","a"),("bound","pad"),lambda t:
        OrElim(t.hyp("pad"),AndElimR(t.hypothesis("inside").hyp("inside")),
            BotElim(apply(specialize(t.hypothesis("outside"),"lt_not_le",*t.hypothesis("outside").terms(("i","N"))),
                t.hypothesis("outside").hyp("bound"),AndElimL(t.hypothesis("outside").hyp("outside"))))))


def _one_index(s):
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqTrans
    from peano_lab.kernel.terms import Succ,Zero
    return introduce(s,("j",),(),lambda t:
        EqTrans(CongAdd(EqRefl(Succ(Zero())),specialize(t,"one_mul",t.term("j"))),_one_plus(t,t.term("j"))))


def _slice_entry(s,registry):
    from peano_lab.kernel.terms import Succ
    def finish(t):
        decoded = apply(specialize(t,"slice",*t.terms(("j","y"))),t.hyp("bound"),t.hyp("second"))
        decoded = _subst(t,registry,"BetaAt(ab,ac,slot,y)",specialize(t,"one_index",t.term("j")),decoded)
        return apply(specialize(t,"beta_unique",*t.terms(("ab","ac")),Succ(t.term("j")),*t.terms(("x","y"))),t.hyp("first"),decoded)
    return introduce(s,("ab","ac","bb","bc","N","j","x","y"),("slice","bound","first","second"),finish)


def _head_tail(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import AndElimL,AndElimR,AndIntro,CongS,EqRefl,EqSym,OrIntroL
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        def head(u):
            N,i,a,c,z = u.terms(("N","i","a","c","z"))
            bound0 = apply(specialize(u,"below",Zero(),Succ(i),N),specialize(u,"zero_le",Succ(i)),u.hyp("bound"))
            diagonal0 = apply(specialize(u,"succ_le_succ",Zero(),Succ(i)),specialize(u,"zero_le",Succ(i)))
            term = apply(specialize(u,"diagonal_entry",*u.terms(A+C),Succ(i),*u.terms(D),Succ(Succ(i)),Zero(),z),
                AndElimL(u.hyp("whole")),diagonal0,u.hyp("head_value"))
            expected = witness((Succ(i),a,c),conjunction(specialize(u,"zero_add",Succ(i)),
                OrIntroL(AndIntro(bound0,u.hyp("first_a"))),OrIntroL(AndIntro(u.hyp("bound"),u.hyp("first_c"))),EqRefl(Mul(a,c))))
            equal = apply(specialize(u,"term_unique",*u.terms(A+C),Succ(i),Zero(),z,Mul(a,c)),term,expected)
            actual_head = _subst(u,registry,"BetaAt(db,dc,0,slot)",equal,u.hyp("head_value"))
            def shifted(v):
                def small_term(w):
                    def coefficient_value(x):
                        j = x.term("j")
                        def diagonal_value(y_scope):
                            j,i,N,tvalue,zv = y_scope.terms(("j","i","N","t","zv"))
                            # Rebuild the translated term after the new value binder.
                            def translated_at(z_scope):
                                jj,kk,ii,nn,bv,yv,avv = z_scope.terms(("j","k","i","N","x","y","av"))
                                small0 = apply(specialize(z_scope,"le_of_succ_le_succ",jj,ii),z_scope.hyp("index"))
                                jn = apply(specialize(z_scope,"below",jj,ii,nn),small0,apply(specialize(z_scope,"lower",ii,nn),z_scope.hyp("bound")))
                                sjn = apply(specialize(z_scope,"below",Succ(jj),Succ(ii),nn),apply(specialize(z_scope,"succ_le_succ",jj,ii),small0),z_scope.hyp("bound"))
                                be = apply(specialize(z_scope,"unpad",*z_scope.terms(("bb","bc","N","j","x"))),jn,field(z_scope.hyp("small_term"),1,4))
                                equal0 = apply(specialize(z_scope,"shift",jj,avv,bv),small0,z_scope.hyp("a_value"),be)
                                ae = _subst(z_scope,registry,"BetaAt(ab,ac,S j,slot)",equal0,z_scope.hyp("a_value"))
                                index0 = _chain(specialize(z_scope,"add_succ_left",jj,kk),CongS(field(z_scope.hyp("small_term"),0,4)))
                                return witness((kk,bv,yv),conjunction(index0,OrIntroL(AndIntro(sjn,ae)),field(z_scope.hyp("small_term"),2,4),field(z_scope.hyp("small_term"),3,4)))
                            actual = apply(specialize(y_scope,"diagonal_entry",*y_scope.terms(A+C),Succ(i),*y_scope.terms(D),Succ(Succ(i)),Succ(j),zv),
                                AndElimL(y_scope.hyp("whole")),apply(specialize(y_scope,"succ_le_succ",Succ(j),Succ(i)),y_scope.hyp("index")),y_scope.hyp("diagonal_value"))
                            eq = apply(specialize(y_scope,"term_unique",*y_scope.terms(A+C),Succ(i),Succ(j),zv,tvalue),actual,translated_at(y_scope))
                            entry = _subst(y_scope,registry,"BetaAt(db,dc,S j,slot)",eq,y_scope.hyp("diagonal_value"))
                            return _subst(y_scope,registry,"BetaAt(db,dc,slot,t)",EqSym(specialize(y_scope,"one_index",j)),entry)
                        return eliminate(x,specialize(x,"beta_exists",*x.terms(D),Succ(j)),("zv",),"diagonal_value",diagonal_value)
                    return eliminate(w,specialize(w,"beta_exists",*w.terms(("ab","ac")),Succ(w.term("j"))),("av",),"a_value",coefficient_value)
                term = apply(specialize(v,"diagonal_entry",*v.terms(B+C),v.term("i"),*v.terms(E),Succ(v.term("i")),*v.terms(("j","t"))),
                    AndElimL(v.hyp("tail")),v.hyp("index"),v.hyp("value"))
                return eliminate(v,term,("k","x","y"),"small_term",small_term)
            slice_proof = introduce(u,("j","t"),("index","value"),shifted)
            affine = witness(u.terms(E),AndIntro(slice_proof,AndElimR(u.hyp("tail"))))
            return apply(specialize(u,"sum_head_tail",*u.terms(D),Succ(i),u.term("p"),Mul(a,c),u.term("q")),AndElimR(u.hyp("whole")),actual_head,affine)
        return eliminate(t,specialize(t,"beta_exists",*t.terms(D),Zero()),("z",),"head_value",head)
    return introduce(s,FIXED+("a","c","p","q"),("bound","first_a","first_c","shift","whole_coefficient","tail_coefficient"),lambda t:
        eliminate(t,t.hyp("whole_coefficient"),D,"whole",lambda u:
            eliminate(u,u.hyp("tail_coefficient"),E,"tail",finish)))


def _root(s,registry):
    from sqrt2_power_native import instantiate
    from sqrt2_power_quadratic_height import _chain
    from peano_lab.kernel.proofs import CongAdd,EqRefl,EqSym
    from peano_lab.kernel.terms import Mul,Succ,Zero
    def finish(t):
        N,i,h,c,u,v,q,e,z = t.terms(("N","i","h","c","u","v","q","e","z"))
        bound1 = apply(specialize(t,"lower",Succ(i),N),t.hyp("bound"))
        bound0 = apply(specialize(t,"below",Zero(),Succ(Succ(i)),N),specialize(t,"zero_le",Succ(Succ(i))),t.hyp("bound"))
        hz = apply(specialize(t,"slice_entry",*t.terms(("ab","ac","bb","bc","N")),Zero(),h,z),t.hyp("slice"),bound0,t.hyp("one"),t.hyp("slice_zero"))
        zero_entry = _subst(t,registry,"BetaAt(bb,bc,0,slot)",EqSym(hz),t.hyp("slice_zero"))
        def first_shift(w):
            j,i,N = w.terms(("j","i","N"))
            b1 = apply(specialize(w,"lower",Succ(i),N),w.hyp("bound"))
            jn = apply(specialize(w,"below",j,Succ(i),N),w.hyp("small"),b1)
            return apply(specialize(w,"slice_entry",*w.terms(("ab","ac","bb","bc","N","j","x","y"))),w.hyp("slice"),jn,w.hyp("first"),w.hyp("second"))
        def second_shift(w):
            j,i,N,x,y = w.terms(("j","i","N","x","y"))
            small1 = apply(specialize(w,"succ_le_succ",j,i),w.hyp("small"))
            small2 = apply(specialize(w,"succ_le_succ",Succ(j),Succ(i)),small1)
            b2 = apply(specialize(w,"below",Succ(Succ(j)),Succ(Succ(i)),N),small2,w.hyp("bound"))
            b1 = apply(specialize(w,"lower",Succ(j),N),b2)
            shifted = apply(specialize(w,"slice",Succ(j),x),b1,w.hyp("first"))
            shifted = _subst(w,registry,"BetaAt(ab,ac,slot,x)",specialize(w,"one_index",Succ(j)),shifted)
            return EqSym(apply(specialize(w,"period",j,y,x),b2,w.hyp("second"),shifted))
        rel1 = introduce(t,("j","x","y"),("small","first","second"),first_shift)
        rel2 = introduce(t,("j","x","y"),("small","first","second"),second_shift)
        first = apply(specialize(t,"head_tail",*t.terms(("ab","ac","bb","bc","cb","cc","N")),Succ(i),Zero(),e,v,q),
            t.hyp("bound"),t.hyp("zero"),t.hyp("last_c"),rel1,t.hyp("large_coefficient"),t.hyp("middle_coefficient"))
        second = apply(specialize(t,"head_tail",*t.terms(("bb","bc","ab","ac","cb","cc","N","i")),h,c,q,u),
            bound1,zero_entry,t.hyp("entry_c"),rel2,t.hyp("middle_coefficient"),t.hyp("small_coefficient"))
        equality = _chain(first,CongAdd(specialize(t,"mul_zero_left",e),EqRefl(q)),specialize(t,"zero_add",q),second,specialize(t,"add_comm",Mul(h,c),u))
        return witness((u,v),conjunction(t.hyp("small_coefficient"),t.hyp("large_coefficient"),equality))
    def construct(t,position):
        if position==6:
            return finish(t)
        if position==0:
            proof,names,label = specialize(t,"slice_exists",*t.terms(("ab","ac")),Succ(Zero()),Succ(Zero()),t.term("N")),("bb","bc"),"slice"
        elif position==1:
            proof,names,label = specialize(t,"coefficient_exists",*t.terms(A+C+("i",))),("u",),"small_coefficient"
        elif position==2:
            proof,names,label = specialize(t,"coefficient_exists",*t.terms(A+C),Succ(Succ(t.term("i")))),("v",),"large_coefficient"
        elif position==3:
            proof,names,label = specialize(t,"coefficient_exists",*t.terms(B+C),Succ(t.term("i"))),("q",),"middle_coefficient"
        elif position==4:
            proof,names,label = specialize(t,"beta_exists",*t.terms(("cb","cc")),Succ(Succ(t.term("i")))),("e",),"last_c"
        else:
            proof,names,label = specialize(t,"beta_exists",*t.terms(("bb","bc")),Zero()),("z",),"slice_zero"
        return eliminate(t,proof,names,label,lambda u:construct(u,position+1))
    return introduce(s,("ab","ac","cb","cc","N","i","h","c"),("bound","zero","one","period","entry_c"),lambda t:construct(t,0))


def prove_periodic_convolution(*,limits=None):
    registry = definition_registry()
    factories = {"below":_below,"lower":_lower,"unpad":_unpad,"one_index":_one_index,
        "slice_entry":lambda s:_slice_entry(s,registry),"head_tail":lambda s:_head_tail(s,registry),"CV027":lambda s:_root(s,registry)}
    return assemble_actual_certificate(code="CV027",target=frozen_periodic_convolution_target(),registry=registry,
        helper_sources=HELPER_SOURCES,helper_hashes=HELPER_TARGET_SHA256,endpoint_sources=ENDPOINT_SOURCES,
        archives=ARCHIVES,dependencies=HELPER_DEPENDENCIES,factories=factories,pins=periodic_convolution_source_pins,
        contract=source_contract(),limits=limits,new_induction_count=0)
