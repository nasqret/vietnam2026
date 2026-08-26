"""Fail-closed audit for Primorial-interval divisibility into Choose."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v10
from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
    make_bertrand_central_binom_candidate_theorems,
)
from peano_lab.library.bertrand_choose_diagonal_candidate import (
    make_bertrand_choose_diagonal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_factorial_bridge_candidate import (
    make_bertrand_choose_factorial_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_choose_factorial_support_candidate import (
    make_bertrand_choose_factorial_support_candidate_theorems,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    make_bertrand_choose_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_choose_laws_candidate import (
    make_bertrand_choose_laws_candidate_theorems,
)
from peano_lab.library.bertrand_choose_pascal_candidate import (
    make_bertrand_choose_pascal_candidate_theorems,
)
from peano_lab.library.bertrand_choose_positive_candidate import (
    make_bertrand_choose_positive_candidate_theorems,
)
from peano_lab.library.bertrand_choose_recurrence_candidate import (
    make_bertrand_choose_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_choose_row_functional_candidate import (
    make_bertrand_choose_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_symmetry_candidate import (
    make_bertrand_choose_symmetry_candidate_theorems,
)
from peano_lab.library.bertrand_choose_table_row_functional_candidate import (
    make_bertrand_choose_table_row_functional_candidate_theorems,
)
from peano_lab.library.bertrand_choose_weighted_vertical_candidate import (
    make_bertrand_choose_weighted_vertical_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_choose_interval_candidate import (
    make_bertrand_primorial_choose_interval_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_duplicate_free_candidate import (
    _coprime_term,
    _divides_term,
    _le_term,
    _pointwise_divides_term,
    _product_term,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _binders,
    _lt_term,
    _prime_term,
    _render_term,
    _validated_context,
    make_bertrand_primorial_foundation_candidate_theorems,
)
from peano_lab.library.bertrand_primorial_interval_candidate import (
    _primorial_interval_factor_prefix_term,
    _primorial_interval_relation_term,
    make_bertrand_primorial_interval_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from peano_lab.library.finite_factorial_theorems import factorial_relation
from peano_lab.library.finite_product_prefix_suffix_candidate import (
    make_finite_product_prefix_suffix_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    _proof_envelope_metrics_bounded,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "factorial_prime_divides_of_le",
    "factorial_prime_le_of_divides",
    "choose_prime_divides_between",
    "beta_pairwise_coprime_product_divides_common_multiple",
    "primorial_interval_pairwise_coprime",
    "primorial_interval_divides_choose_between",
    "primorial_even_interval_divides_central",
    "primorial_odd_interval_divides_middle",
    "primorial_even_interval_le_central",
    "primorial_odd_interval_le_middle",
)

EXPECTED_DEPENDENCIES = {
    EXPECTED_NAMES[0]: (
        "prime_is_succ_succ",
        "beta_factor_divides_product",
        "add_succ_left",
        "zero_add",
    ),
    EXPECTED_NAMES[1]: (
        "divisor_one",
        "le_succ",
        "euclid_prime_dvd_product",
        "divisor_le_nonzero",
        "succ_ne_zero",
        "factorial_zero",
        "factorial_succ_decompose",
    ),
    EXPECTED_NAMES[2]: (
        "factorial_exists",
        "choose_factorial_bridge",
        EXPECTED_NAMES[0],
        "euclid_prime_dvd_product",
        EXPECTED_NAMES[1],
        "lt_not_le",
    ),
    EXPECTED_NAMES[3]: (
        "beta_product_zero",
        "beta_product_succ_decompose",
        "le_succ",
        "le_refl",
        "one_multiple",
        "lt_irrefl_expanded",
        "beta_product_pointwise_coprime",
        "coprime_product_is_lcm",
    ),
    EXPECTED_NAMES[4]: (
        "beta_at_unique",
        "add_left_cancel",
        "distinct_primes_coprime",
        "coprime_one_left",
        "coprime_one_right",
    ),
    EXPECTED_NAMES[5]: (
        "beta_at_unique",
        "one_multiple",
        EXPECTED_NAMES[2],
        EXPECTED_NAMES[4],
        EXPECTED_NAMES[3],
    ),
    EXPECTED_NAMES[6]: (
        "add_comm",
        "add_le_add_left",
        EXPECTED_NAMES[5],
    ),
    EXPECTED_NAMES[7]: (
        "add_comm",
        "add_succ_left",
        "add_le_add_left",
        "le_refl",
        "lt_trans",
        EXPECTED_NAMES[5],
    ),
    EXPECTED_NAMES[8]: (
        EXPECTED_NAMES[6],
        "central_binom_positive",
        "divisor_le_nonzero",
    ),
    EXPECTED_NAMES[9]: (
        EXPECTED_NAMES[7],
        "choose_positive",
        "add_succ_left",
        "divisor_le_nonzero",
    ),
}

EXPECTED_DIRECT_CUTS = dict(
    zip(EXPECTED_NAMES, (4, 7, 6, 8, 5, 5, 3, 6, 3, 4), strict=True)
)
assert sum(map(len, EXPECTED_DEPENDENCIES.values())) == 51

EXPECTED_ARTIFACTS: dict[str, tuple[int, str, str, str] | None] = {
    EXPECTED_NAMES[0]: (
        3069,
        "4b0fe3c50406ba9534ac0302f5695f983e47a757f35ae8528639331d1c2e5ade",
        "bd72e696768c9bb4c0dd7392c85fd868393a9ce7827735fcfacf2537b3c7b1c3",
        "2c571f360365e73ed38246bdcf524726519a160619b5941e43e8f4e68885430c",
    ),
    EXPECTED_NAMES[1]: (
        3073,
        "d331caeeb9bdfcca5c38140666e6178a0ea4c6c7cd9d1264e8d80a1b76feade0",
        "2da9f973b99ebbdad756049c7d3a99f64f9b26850383582ed2abe4605fee4125",
        "f4f49d7f60e5773a6ddfed94f08eafebdb251ebc0000f5052f62794f48f5ee77",
    ),
    EXPECTED_NAMES[2]: (
        7887,
        "e3a2821fd6bfd7cd12bb0832172be7ed394806efa58699b6f5fc0157928352f4",
        "f29f5a89d0dc5e33dc501da153103ac110bbe838da053021fd4c1dd25732fff4",
        "3490af2dcdb0ddb84f4f76bdb57a3cf32279980ccacee0a4b5b256905bf52d08",
    ),
    EXPECTED_NAMES[3]: (
        4205,
        "ef61a960b982af43443f598008192d7662a5b4e2bc34995798062b8ab860d25b",
        "bf3202bb452f279d07bee0455f057421fabc7a4c882bfb5cad8fb15b1fd584a1",
        "6634989c19981b6e03045b0cc09031b04263a7a15376800e854a2c747e90d88b",
    ),
    EXPECTED_NAMES[4]: (
        2730,
        "874a7086fae51ae12104cad8336c7f23f55739e3d2b46b8b519d137866bad03d",
        "bd4c5e6a72726d9efd44c4fc4e8b66f4d2c0b94173557fe0bdd371844190eb37",
        "5c96aa8cfb98ad8d0671403ad4473b4fe0eef1820f014362abcb48942690c49e",
    ),
    EXPECTED_NAMES[5]: (
        12008,
        "5ae23a8e915cab2c91be901ea7f00f7b136b245fb6c85d8fe087dfa0c3878daa",
        "9c1cb4890bb24542a4f6791be72e033145ce76ce3e212470fdbd9687996eb1b9",
        "b01aa00f7611f20d4aa956a5b5c5d4e0180d343d12b14e32563439a9f06d103d",
    ),
    EXPECTED_NAMES[6]: (
        11706,
        "e37526b1f3f274355798ff1746afa7782b86243e02e6870fbc305f2923f3e064",
        "09a347a7aed73a0fedaf93a640cbc371301b971aadfa41c7c4a2c27b09b387ea",
        "e7672b7b01b159d8526f679a17b94ba653525e88e6e8b803827656b4fc0bf805",
    ),
    EXPECTED_NAMES[7]: (
        11591,
        "88afd5524fe8cc7dffbeea43fe38997d3ffe6cb0994351b4bbd5b3a7cbf40431",
        "ef82fb985ffa5343b2941b460edd7b5e6e5d2256b50db6ebf6c526e08e5f8cfc",
        "33af84ef3bd6460344b7dacdf00793ee72e7080c9c1d73f222928ed784e33431",
    ),
    EXPECTED_NAMES[8]: (
        11704,
        "0f9caf8c372c16031074b6574346ae6af03e3dff34e5914a6b83d7f78612a437",
        "dde4259a8857079799cb4ee304182e9e4df82d79a16ed148d0d7f16bc41ad8c4",
        "fadd5c2a42f86f392e4979370ee0a21db1d10a5a469855985f681474a41d106e",
    ),
    EXPECTED_NAMES[9]: (
        11589,
        "3ee71ba682fa24f17fd0332b4af23ce39dafe91866e67b51d62bdfd15ec5b2c8",
        "6e4ee867b0f9b59ee505bbd80253ca9f14af5c45f8bc4d7585962279c974477a",
        "9df840d990f85e3481c60225f1fa10f5f3a3d3f7deff5d2b456fd3f3beeda833",
    ),
}
EXPECTED_BODIES: dict[
    str, tuple[int, int, int, int, int, int, int] | None
] = {
    EXPECTED_NAMES[0]: (4, 44, 62, 24, 62, 61, 0),
    EXPECTED_NAMES[1]: (7, 64, 85, 24, 85, 84, 0),
    EXPECTED_NAMES[2]: (6, 88, 107, 36, 107, 106, 0),
    EXPECTED_NAMES[3]: (8, 130, 163, 45, 163, 162, 0),
    EXPECTED_NAMES[4]: (5, 114, 219, 40, 219, 218, 0),
    EXPECTED_NAMES[5]: (5, 88, 189, 44, 189, 188, 0),
    EXPECTED_NAMES[6]: (3, 40, 55, 20, 54, 54, 1),
    EXPECTED_NAMES[7]: (6, 53, 72, 23, 71, 71, 1),
    EXPECTED_NAMES[8]: (3, 24, 35, 17, 35, 34, 0),
    EXPECTED_NAMES[9]: (4, 29, 42, 20, 42, 41, 0),
}
EXPECTED_ENVELOPES: dict[str, tuple[int, int, int, int, int] | None] = {
    EXPECTED_NAMES[0]: (62, 62, 24, 39, 24),
    EXPECTED_NAMES[1]: (85, 85, 24, 263, 37),
    EXPECTED_NAMES[2]: (107, 107, 36, 37, 36),
    EXPECTED_NAMES[3]: (163, 163, 45, 361, 45),
    EXPECTED_NAMES[4]: (219, 219, 40, 220, 40),
    EXPECTED_NAMES[5]: (189, 189, 44, 126, 44),
    EXPECTED_NAMES[6]: (55, 54, 20, 36, 20),
    EXPECTED_NAMES[7]: (72, 71, 23, 67, 24),
    EXPECTED_NAMES[8]: (35, 35, 17, 13, 17),
    EXPECTED_NAMES[9]: (42, 42, 20, 21, 22),
}
EXPECTED_CLOSURES: dict[
    str, tuple[int, int, int, int, int, int, int, str] | None
] = {
    EXPECTED_NAMES[0]: (
        3174,
        67,
        1158,
        1211,
        54,
        11875,
        67,
        "caaf55e1fa4cef6c52fcc24eba55c2293825d09fbe7b77b0c835a1cca5c0b7c3",
    ),
    EXPECTED_NAMES[1]: (
        9577,
        70,
        2650,
        2788,
        139,
        34533,
        70,
        "40333c1ba3304cb798f9e9a674cb9ba17201d34b80c29d1f4623facce5c5205d",
    ),
    EXPECTED_NAMES[2]: (
        279577,
        112,
        10458,
        10825,
        368,
        991237,
        112,
        "40d4fcc4e7cc320fa65ccbd4c960adf8218837e4f1b1ab27fc6b97289ed2266a",
    ),
    EXPECTED_NAMES[3]: (
        13710,
        71,
        2580,
        2711,
        132,
        45998,
        71,
        "33a577976bea51c8090dfd6663925505bdab0c537dd4890585c7e997d46f5878",
    ),
    EXPECTED_NAMES[4]: (
        3558,
        60,
        1848,
        1941,
        94,
        10470,
        60,
        "bac4394a5b48b022fbbfe53deb44b401844a19f029c57c0d433c8f95d6df5a4f",
    ),
    EXPECTED_NAMES[5]: (
        298187,
        115,
        11268,
        11660,
        393,
        1055274,
        115,
        "6ea3db7692bd0ce9441efb0a0fbd61f27b2e195bf8173837d22726f5731f28c5",
    ),
    EXPECTED_NAMES[6]: (
        298450,
        118,
        11351,
        11747,
        397,
        1058567,
        118,
        "fde840ccb7f2af59b04ec8b8a16e5842157735782a6d0de7c2eec4fea38d5135",
    ),
    EXPECTED_NAMES[7]: (
        298608,
        121,
        11397,
        11797,
        401,
        1061095,
        121,
        "ed83e4a5b76136b4b1676ed993e6ae06a4233c25ff700ad450f5cdf7c262d97c",
    ),
    EXPECTED_NAMES[8]: (
        398278,
        119,
        11495,
        11898,
        404,
        1425892,
        119,
        "c1e5bb2d1a59c49b5ef66a11c378c67e76ae58bad2bf4b1fd82aee3e1cef5bdb",
    ),
    EXPECTED_NAMES[9]: (
        398448,
        122,
        11526,
        11934,
        409,
        1428407,
        122,
        "62fbacf43f704718a868387805a6fb24a1fbeaef8fd5c9f76d39b6d407353b09",
    ),
}

SOURCE_PINS = {
    "peano-lab/py/peano_lab/library/theorems.py":
        "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",
    "peano-lab/py/peano_lab/library/finite_fold_surface.py":
        "95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30",
    "peano-lab/py/peano_lab/library/finite_factorial_theorems.py":
        "a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709",
    "peano-lab/py/peano_lab/library/bertrand_choose_foundation_candidate.py":
        "97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d",
    "peano-lab/py/peano_lab/library/bertrand_choose_factorial_bridge_candidate.py":
        "22c07f0192b7e3cf6e85cb4b71fe70ecd3146c1c23cf6962ce261b369be10e09",
    "peano-lab/py/peano_lab/library/bertrand_choose_positive_candidate.py":
        "6c289d581e218841013b4f321fb39e66cc815c3ecc7be17d04b6f9fb586592cc",
    "peano-lab/py/peano_lab/library/bertrand_central_binom_candidate.py":
        "c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e",
    "peano-lab/py/peano_lab/library/bertrand_primorial_foundation_candidate.py":
        "70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98",
    "peano-lab/py/peano_lab/library/bertrand_primorial_interval_candidate.py":
        "02e59e0f7addcae3bb127271ddeaa6728c5dab1dee096a878fced278065c10a3",
    "peano-lab/py/peano_lab/library/finite_product_prefix_suffix_candidate.py":
        "b0e98632b5668a688067ecdddebe0f906db00ebe84c267b395592d5797d27d9d",
    "peano-lab/py/peano_lab/library/fermat_residue_product_candidate.py":
        "b43a6fa9be64b806d9973abfb0d566533910c8a841fba16777b8a9498b98d59d",
    "peano-lab/py/peano_lab/library/bertrand_primorial_choose_interval_candidate.py":
        "5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09",
}
RFC_SHA256 = "dda6a985f1a05de4a5e655e73dc06ff7682fb3d3a0a76e2025a4ac28d191a722"


def _prime(value: str, tag: str, variables: tuple[str, ...]) -> str:
    context = _validated_context(variables)
    rendered = _render_term(value, label="test prime", context=context)
    return _prime_term(rendered, tag=tag, avoid=context)


def _pairwise(
    code: str,
    scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
    require_distinct: bool = True,
) -> str:
    context = _validated_context(variables)
    b = _render_term(code, label="test pairwise code", context=context)
    c = _render_term(scale, label="test pairwise scale", context=context)
    l = _render_term(length, label="test pairwise length", context=context)
    i, j, p, q = _binders(
        tag,
        context,
        ("left_index", "right_index", "left_value", "right_value"),
    )
    local = context + (i, j, p, q)
    hi = _lt_term(i, l, tag=f"{tag}_left_bound", avoid=local)
    hj = _lt_term(j, l, tag=f"{tag}_right_bound", avoid=local)
    hp = _beta_at_term(b, c, i, p, tag=f"{tag}_left_at", avoid=local)
    hq = _beta_at_term(b, c, j, q, tag=f"{tag}_right_at", avoid=local)
    cop = _coprime_term(
        p,
        q,
        tag=f"{tag}_coprime",
        variables=local,
    )
    distinct = f"~({i} = {j}) -> " if require_distinct else ""
    return (
        f"forall {i} {j} {p} {q}. ({hi}) -> ({hj}) -> "
        f"({hp}) -> ({hq}) -> {distinct}({cop})"
    )


def _expected_statements() -> dict[str, str]:
    fact = ("p", "n", "F")
    fact_prime = _prime("p", "bfpdol_prime", fact)
    fact_bound = _le_term("p", "n", tag="bfpdol_bound", variables=fact)
    fact_rel = factorial_relation("n", "F", tag="bfpdol_source")
    fact_dvd = _divides_term("p", "F", tag="bfpdol_result", variables=fact)
    rev_prime = _prime("p", "bfplod_prime", fact)
    rev_rel = factorial_relation("n", "F", tag="bfplod_source")
    rev_dvd = _divides_term("p", "F", tag="bfplod_divides", variables=fact)
    rev_le = _le_term("p", "n", tag="bfplod_result", variables=fact)

    cv = ("n", "k", "j", "p", "c")
    cprime = _prime("p", "bcpdb_prime", cv)
    ck = _lt_term("k", "p", tag="bcpdb_left_bound", avoid=cv)
    cj = _lt_term("j", "p", tag="bcpdb_right_bound", avoid=cv)
    cpn = _le_term("p", "n", tag="bcpdb_upper_bound", variables=cv)
    choose = _choose_relation_term(
        "n", "k", "c", tag="bcpdb_source", variables=cv
    )
    cdvd = _divides_term("p", "c", tag="bcpdb_result", variables=cv)

    pv = ("b", "c", "l", "n", "z")
    ppair = _pairwise("b", "c", "l", tag="bpcpdcm_pairwise", variables=pv)
    ppw = _pointwise_divides_term(
        "b", "c", "l", "z", tag="bpcpdcm_pointwise", variables=pv
    )
    pprod = _product_term(
        "b", "c", "l", "n", tag="bpcpdcm_source", variables=pv
    )
    pdvd = _divides_term("n", "z", tag="bpcpdcm_result", variables=pv)

    iv = ("a", "b", "c", "l")
    iprefix = _primorial_interval_factor_prefix_term(
        "a", "b", "c", "l", tag="bpipc_source", variables=iv
    )
    ipair = _pairwise("b", "c", "l", tag="bpipc_result", variables=iv)

    gv = ("a", "l", "n", "k", "j", "c", "z")
    gchoose = _choose_relation_term(
        "n", "k", "c", tag="bpidcb_choose", variables=gv
    )
    ginterval = _primorial_interval_relation_term(
        "a", "l", "z", tag="bpidcb_interval", variables=gv
    )
    index = "bpr_index_bpidcb_bounds"
    local = gv + (index,)
    ibound = _lt_term(index, "l", tag="bpidcb_bounds_index", avoid=local)
    candidate = f"S (a + {index})"
    left = _lt_term("k", candidate, tag="bpidcb_bounds_left", avoid=local)
    right = _lt_term("j", candidate, tag="bpidcb_bounds_right", avoid=local)
    upper = _le_term(
        candidate, "n", tag="bpidcb_bounds_upper", variables=local
    )
    bounds = (
        f"forall {index}. ({ibound}) -> "
        f"(({left}) /\\ (({right}) /\\ ({upper})))"
    )
    gdvd = _divides_term("z", "c", tag="bpidcb_result", variables=gv)

    ev = ("n", "z", "c")
    even_interval = _primorial_interval_relation_term(
        "n", "n", "z", tag="bpeidc_interval", variables=ev
    )
    even_central = _central_binom_relation_term(
        "n", "c", tag="bpeidc_central", variables=ev
    )
    even_dvd = _divides_term("z", "c", tag="bpeidc_result", variables=ev)
    odd_interval = _primorial_interval_relation_term(
        "S n", "n", "z", tag="bpoidm_interval", variables=ev
    )
    odd_middle = _choose_relation_term(
        "S (n + n)", "n", "c", tag="bpoidm_middle", variables=ev
    )
    odd_dvd = _divides_term("z", "c", tag="bpoidm_result", variables=ev)
    even_le = _le_term("z", "c", tag="bpeilc_result", variables=ev)
    odd_le = _le_term("z", "c", tag="bpoilm_result", variables=ev)

    return {
        EXPECTED_NAMES[0]: (
            f"forall p n F. ({fact_prime}) -> ({fact_bound}) -> "
            f"({fact_rel}) -> ({fact_dvd})"
        ),
        EXPECTED_NAMES[1]: (
            f"forall p n F. ({rev_prime}) -> ({rev_rel}) -> "
            f"({rev_dvd}) -> ({rev_le})"
        ),
        EXPECTED_NAMES[2]: (
            "forall n k j p c. k + j = n -> "
            f"({cprime}) -> ({ck}) -> ({cj}) -> ({cpn}) -> "
            f"({choose}) -> ({cdvd})"
        ),
        EXPECTED_NAMES[3]: (
            f"forall b c l n z. ({ppair}) -> ({ppw}) -> "
            f"({pprod}) -> ({pdvd})"
        ),
        EXPECTED_NAMES[4]: (
            f"forall a b c l. ({iprefix}) -> ({ipair})"
        ),
        EXPECTED_NAMES[5]: (
            "forall a l n k j c z. k + j = n -> "
            f"({gchoose}) -> ({ginterval}) -> ({bounds}) -> ({gdvd})"
        ),
        EXPECTED_NAMES[6]: (
            f"forall n z c. ({even_interval}) -> "
            f"({even_central}) -> ({even_dvd})"
        ),
        EXPECTED_NAMES[7]: (
            f"forall n z c. ({odd_interval}) -> "
            f"({odd_middle}) -> ({odd_dvd})"
        ),
        EXPECTED_NAMES[8]: (
            f"forall n z c. ({even_interval}) -> "
            f"({even_central}) -> ({even_le})"
        ),
        EXPECTED_NAMES[9]: (
            f"forall n z c. ({odd_interval}) -> "
            f"({odd_middle}) -> ({odd_le})"
        ),
    }


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_primorial_choose_interval_candidate_theorems(
        TheoremSpec
    )


def _table(rows: tuple[TheoremSpec, ...]) -> dict[str, TheoremSpec]:
    result = {item.name: item for item in rows}
    assert len(result) == len(rows)
    return result


@lru_cache(maxsize=1)
def _support_specs() -> tuple[TheoremSpec, ...]:
    symmetry = make_bertrand_choose_symmetry_candidate_theorems(TheoremSpec)
    pointwise = tuple(
        row
        for row in make_fermat_residue_product_candidate_theorems(TheoremSpec)
        if row.name == "beta_product_pointwise_coprime"
    )
    assert len(pointwise) == 1
    return (
        *make_bertrand_choose_foundation_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_row_functional_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_table_row_functional_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_laws_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_diagonal_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_recurrence_candidate_theorems(TheoremSpec),
        *make_bertrand_choose_pascal_candidate_theorems(TheoremSpec),
        *symmetry[:1],
        *make_bertrand_choose_weighted_vertical_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_support_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_factorial_bridge_candidate_theorems(
            TheoremSpec
        ),
        *make_bertrand_choose_positive_candidate_theorems(TheoremSpec),
        *make_bertrand_central_binom_candidate_theorems(TheoremSpec),
        *make_bertrand_primorial_foundation_candidate_theorems(TheoremSpec),
        *make_finite_product_prefix_suffix_candidate_theorems(
            TheoremSpec
        )[:1],
        *make_bertrand_primorial_interval_candidate_theorems(TheoremSpec),
        *pointwise,
    )


@lru_cache(maxsize=1)
def _core() -> dict[str, TheoremSpec]:
    stable = dict(_specs_by_name())
    support = _table(_support_specs())
    assert not (set(stable) & set(support))
    assert not (set(EXPECTED_NAMES) & set(stable))
    assert not (set(EXPECTED_NAMES) & set(support))
    assert "choose_symmetry" not in support
    return stable | support


def _row_core(name: str) -> dict[str, TheoremSpec]:
    return _core() | _table(_specs()[: EXPECTED_NAMES.index(name)])


@lru_cache(maxsize=1)
def _available() -> dict[str, TheoremSpec]:
    return _core() | _table(_specs())


def _body(item: TheoremSpec) -> tuple[Proof, Formula]:
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(_available()[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        assert tactic != "use"
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _close(
    name: str,
    cache: dict[str, tuple[Formula, Proof]] | None = None,
) -> tuple[Formula, Proof]:
    if cache is None:
        cache = {}
    if name in cache:
        return cache[name]
    if name in _specs_by_name():
        checked = replay(name)
        result = (checked.formula, checked.certificate)
        cache[name] = result
        return result
    item = _available()[name]
    certificate, _target = _body(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    formula = _closed_formula(item.statement)
    dependencies = tuple(_close(dep, cache) for dep in item.dependencies)
    for dependency_formula, dependency_proof in reversed(dependencies):
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    result = (formula, body)
    cache[name] = result
    return result


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_proof(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_sha256(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _mutate_direct_cut(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        zero = Zero()
        return replace(proof, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(proof, body=_mutate_direct_cut(proof.body, index - 1))


def test_bertrand_primorial_choose_interval_sources_are_pinned() -> None:
    root = Path(__file__).resolve().parents[3]
    for relative, digest in SOURCE_PINS.items():
        assert sha256((root / relative).read_bytes()).hexdigest() == digest
    rfc = root / "research/arithmetic-library/" \
        "ha-bertrand-primorial-choose-interval-tranche-rfc-v1.md"
    assert sha256(rfc.read_bytes()).hexdigest() == RFC_SHA256


def test_bertrand_primorial_choose_interval_factory_is_exact() -> None:
    rows = _specs()
    expected = _expected_statements()
    assert tuple(item.name for item in rows) == EXPECTED_NAMES
    assert tuple(item.statement for item in rows) == tuple(
        expected[name] for name in EXPECTED_NAMES
    )
    assert {item.name: item.dependencies for item in rows} == (
        EXPECTED_DEPENDENCIES
    )
    assert all(_closed_formula(item.statement) for item in rows)
    assert not set(EXPECTED_NAMES) & set(_specs_by_name())
    assert not set(EXPECTED_NAMES) & {
        entry.spec.name for entry in editions_v10.ALPHA_ENTRIES
    }


def test_bertrand_primorial_choose_interval_topology_is_exact() -> None:
    table = _table(_specs())
    assert table[EXPECTED_NAMES[1]].script.count("induction n") == 1
    assert table[EXPECTED_NAMES[3]].script.count("induction l") == 1
    assert table[EXPECTED_NAMES[2]].script.count(
        "apply euclid_prime_dvd_product"
    ) == 2
    assert table[EXPECTED_NAMES[4]].script.count(
        "apply distinct_primes_coprime"
    ) == 1
    assert table[EXPECTED_NAMES[5]].script.count(
        "apply choose_prime_divides_between"
    ) == 1
    assert all(
        not command.startswith("rewrite hchoose at")
        for row in table.values()
        for command in row.script
    )


def test_bertrand_primorial_choose_interval_receipts_are_shaped() -> None:
    assert tuple(EXPECTED_DEPENDENCIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_DIRECT_CUTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_ARTIFACTS) == EXPECTED_NAMES
    assert tuple(EXPECTED_BODIES) == EXPECTED_NAMES
    assert tuple(EXPECTED_ENVELOPES) == EXPECTED_NAMES
    assert tuple(EXPECTED_CLOSURES) == EXPECTED_NAMES
    assert all(value is not None for value in EXPECTED_ARTIFACTS.values())
    assert all(value is not None for value in EXPECTED_BODIES.values())
    assert all(value is not None for value in EXPECTED_ENVELOPES.values())
    assert all(value is not None for value in EXPECTED_CLOSURES.values())


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_choose_interval_artifacts_are_frozen(
    name: str,
) -> None:
    item = _table(_specs())[name]
    actual = (
        len(item.statement),
        sha256(item.statement.encode()).hexdigest(),
        sha256("\0".join(item.script).encode()).hexdigest(),
        sha256(
            "\0".join((item.statement, *item.dependencies)).encode()
        ).hexdigest(),
    )
    print(f"PRIMORIAL CHOOSE {name} ARTIFACT actual={actual!r}", flush=True)
    assert EXPECTED_ARTIFACTS[name] is not None, (
        f"freeze artifact receipt for {name}: {actual!r}"
    )
    assert actual == EXPECTED_ARTIFACTS[name]


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_choose_interval_bodies_are_frozen(
    name: str,
) -> None:
    item = _table(_specs())[name]
    body, target = _body(item)
    assert check((), body, target)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        body,
        max_proof_occurrences=limits.max_body_occurrences,
        max_proof_objects=limits.max_body_objects,
        max_proof_depth=limits.max_body_depth,
        max_annotation_occurrences=limits.max_body_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_body_envelope_depth,
        label=f"Primorial Choose body {name}",
    )
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    actual = (
        len(item.dependencies),
        len(item.script),
        nodes,
        depth,
        objects,
        edges,
        reused,
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(body))
    print(
        f"PRIMORIAL CHOOSE {name} BODY actual={actual!r} "
        f"envelope={envelope!r}",
        flush=True,
    )
    assert EXPECTED_BODIES[name] is not None, actual
    assert EXPECTED_ENVELOPES[name] is not None, envelope
    assert actual == EXPECTED_BODIES[name]
    assert envelope == EXPECTED_ENVELOPES[name]


LIVE_EDGES = tuple(
    (name, dependency)
    for name in EXPECTED_NAMES
    for dependency in EXPECTED_DEPENDENCIES[name]
)
assert len(LIVE_EDGES) == 51


@pytest.mark.parametrize(("name", "dependency"), LIVE_EDGES)
def test_bertrand_primorial_choose_interval_every_dependency_is_live(
    name: str,
    dependency: str,
) -> None:
    item = _table(_specs())[name]
    shortened = replace(
        item,
        dependencies=tuple(dep for dep in item.dependencies if dep != dependency),
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((shortened,), core=_row_core(name))


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_choose_interval_false_targets_are_rejected(
    name: str,
) -> None:
    item = _table(_specs())[name]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=f"({item.statement}) /\\ false"),),
            core=_row_core(name),
        )


def _mutations() -> tuple[tuple[str, str, str], ...]:
    statements = _expected_statements()
    fact = ("p", "n", "F")
    old0 = _divides_term("p", "F", tag="bfpdol_result", variables=fact)
    new0 = _divides_term("S p", "F", tag="bfpdol_result", variables=fact)
    old1 = _le_term("p", "n", tag="bfplod_result", variables=fact)
    new1 = _le_term("S p", "n", tag="bfplod_result", variables=fact)
    cv = ("n", "k", "j", "p", "c")
    old2 = _divides_term("p", "c", tag="bcpdb_result", variables=cv)
    new2 = _divides_term("S p", "c", tag="bcpdb_result", variables=cv)
    pv = ("b", "c", "l", "n", "z")
    old3 = _divides_term("n", "z", tag="bpcpdcm_result", variables=pv)
    new3 = _divides_term("S n", "z", tag="bpcpdcm_result", variables=pv)
    iv = ("a", "b", "c", "l")
    old4 = _pairwise("b", "c", "l", tag="bpipc_result", variables=iv)
    new4 = _pairwise(
        "b",
        "c",
        "l",
        tag="bpipc_result",
        variables=iv,
        require_distinct=False,
    )
    gv = ("a", "l", "n", "k", "j", "c", "z")
    old5 = _divides_term("z", "c", tag="bpidcb_result", variables=gv)
    new5 = _divides_term("S z", "c", tag="bpidcb_result", variables=gv)
    ev = ("n", "z", "c")
    old6 = _divides_term("z", "c", tag="bpeidc_result", variables=ev)
    new6 = _divides_term("S z", "c", tag="bpeidc_result", variables=ev)
    old7 = _divides_term("z", "c", tag="bpoidm_result", variables=ev)
    new7 = _divides_term("S z", "c", tag="bpoidm_result", variables=ev)
    old8 = _le_term("z", "c", tag="bpeilc_result", variables=ev)
    new8 = _le_term("S z", "c", tag="bpeilc_result", variables=ev)
    old9 = _le_term("z", "c", tag="bpoilm_result", variables=ev)
    new9 = _le_term("S z", "c", tag="bpoilm_result", variables=ev)
    replacements = (
        (old0, new0),
        (old1, new1),
        (old2, new2),
        (old3, new3),
        (old4, new4),
        (old5, new5),
        (old6, new6),
        (old7, new7),
        (old8, new8),
        (old9, new9),
    )
    return tuple(
        (name, statements[name], statements[name].replace(old, new, 1))
        for name, (old, new) in zip(EXPECTED_NAMES, replacements, strict=True)
    )


def test_bertrand_primorial_choose_interval_mutations_have_fixtures() -> None:
    assert 2 == 2 and 3 > 2
    assert 2 > 1
    assert 1 < 2 and 2 == 2


@pytest.mark.parametrize(
    ("name", "old", "new"),
    _mutations(),
    ids=EXPECTED_NAMES,
)
def test_bertrand_primorial_choose_interval_mutations_are_rejected(
    name: str,
    old: str,
    new: str,
) -> None:
    item = _table(_specs())[name]
    assert item.statement == old
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (replace(item, statement=new),),
            core=_row_core(name),
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_bertrand_primorial_choose_interval_closures_are_frozen(
    name: str,
) -> None:
    item = _table(_specs())[name]
    formula, certificate = _close(name)
    assert formula == _closed_formula(item.statement)
    assert check((), certificate, formula)
    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    envelope = _proof_envelope_metrics_bounded(
        certificate,
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=(
            limits.max_candidate_annotation_occurrences
        ),
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_candidate_envelope_depth,
        label=f"Primorial Choose closure {name}",
    )
    nodes, depth = proof_metrics(certificate)
    objects, edges, reused = proof_identity_metrics(certificate)
    actual = (
        nodes,
        depth,
        objects,
        edges,
        reused,
        envelope[3],
        envelope[4],
        _proof_dag_sha256(certificate),
    )
    assert nodes <= MAX_LIVE_PROOF_NODES
    assert depth <= MAX_LIVE_PROOF_DEPTH
    assert objects <= MAX_LIVE_PROOF_OBJECTS
    assert not any(type(node) is DNE for node in _walk_proof(certificate))
    direct_cut_count = 0
    probe = certificate
    while type(probe) is Cut:
        direct_cut_count += 1
        probe = probe.body
    assert direct_cut_count == EXPECTED_DIRECT_CUTS[name]
    for index in range(direct_cut_count):
        assert not check((), _mutate_direct_cut(certificate, index), formula)
    print(f"PRIMORIAL CHOOSE {name} CLOSURE actual={actual!r}", flush=True)
    assert EXPECTED_CLOSURES[name] is not None, actual
    assert actual == EXPECTED_CLOSURES[name]
