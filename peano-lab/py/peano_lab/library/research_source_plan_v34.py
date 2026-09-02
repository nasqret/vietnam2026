"""Pinned canonical-only source cones and original v30-order plans for v34.

These are syntax/planning data, never proof receipts. Source DFS order is kept
distinct from artifact node order. Only source_selection opens the immutable
v30 parent through the unchanged original planner. No working controller,
Alpha edition, proof artifact, kernel check or Lean worker is imported here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import MappingProxyType, ModuleType
import re
import sys

from .theorems import THEOREMS, TheoremSpec
from .campaign_lower_layer_closure import _specs_digest

class SourcePlanError(ValueError):
    """A canonical source identity, overlap, dependency or original plan differs."""

HERE = Path(__file__).resolve().parent
MAX_SOURCE_BYTES = 2 * 1024 * 1024
THEOREMS_PIN = (536011, "05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919",)
# Exact original26 polynomial providers, including the singular valuation law.
GCD_CANONICAL_PROVIDERS = (
    ("prime_field_arithmetic_candidate", "make_prime_field_arithmetic_candidate_theorems", 39963, "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90",),
    ("prime_field_polynomial_candidate", "make_prime_field_polynomial_candidate_theorems", 45723, "644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72",),
    ("prime_field_polynomial_convolution_candidate", "make_prime_field_polynomial_convolution_candidate_theorems", 49060, "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24",),
    ("prime_field_polynomial_representation_candidate", "make_prime_field_polynomial_representation_candidate_theorems", 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a",),
    ("finite_division_prefix_candidate", "make_finite_division_prefix_candidate_theorems", 13578, "a6af47a7d918d46cdd4b83f60524d3c7afad42886ebb8e560bda5a1318f0b606",),
    ("finite_pointwise_mul_recode_candidate", "make_finite_pointwise_mul_recode_candidate_theorems", 15489, "390e453959339720836e37ea488f226db3ad0c2fabe9dc53572053801e0c9dd3",),
    ("finite_repeat_sum_candidate", "make_finite_repeat_sum_candidate_theorems", 6860, "7e468d7ddced0220b4c6da6c7417edfa1f1392e793770b0109808ad32d84d182",),
    ("finite_sum_transport_candidate", "make_finite_sum_transport_candidate_theorems", 4087, "5b875f94f987c8f7b77a8ef227d2209dfb209244a38f2b7b03c6197034578023",),
    ("binary_modular_exponentiation_candidate", "make_binary_modular_exponentiation_candidate_theorems", 37701, "e30f2c6c7afced6a25449ab429bbcb04452650eb5dd02b256984e7fe4904ab13",),
    ("hensel_prime_power_candidate", "make_hensel_prime_power_candidate_theorems", 41831, "507e76d5ad70e9244313de145036f64891f39ae40de74fcddde112deb8885bc3",),
    ("prime_field_polynomial_convolution_triangular_candidate", "make_prime_field_polynomial_convolution_triangular_candidate_theorems", 16677, "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f",),
    ("prime_field_polynomial_distributivity_candidate", "make_prime_field_polynomial_distributivity_candidate_theorems", 26118, "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86",),
    ("prime_field_polynomial_convolution_padding_candidate", "make_prime_field_polynomial_convolution_padding_candidate_theorems", 39740, "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007",),
    ("prime_field_polynomial_equivalence_candidate", "make_prime_field_polynomial_equivalence_candidate_theorems", 10469, "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373",),
    ("prime_field_polynomial_convolution_congruence_candidate", "make_prime_field_polynomial_convolution_congruence_candidate_theorems", 8183, "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70",),
    ("matrix_coded_product_candidate", "make_matrix_coded_product_candidate_theorems", 73949, "621d47e1a2d3ba9a55ee4779583b7ac7b0cc7192e91ded4141e6e705e9bb0fc2",),
    ("matrix_rank_finite_coding_candidate", "make_matrix_rank_finite_coding_candidate_theorems", 22758, "9a72aed5aa215816b5e26868c04453e0a3042486580e79a13234431b5f45952d",),
    ("matrix_recursive_determinant_extensional_candidate", "make_matrix_recursive_determinant_extensional_candidate_theorems", 32183, "bb2872950c416964ce6fde1012359526e748f856bc6263e080b8e2da852ca59a",),
    ("bertrand_power_valuation_laws_candidate", "make_bertrand_power_valuation_law_candidate_theorems", 12196, "7b95e4f2a16df3866cb3e01f17d1b455000706454a1a241948957c4548a0a17f",),
    ("prime_field_polynomial_subtraction_candidate", "make_prime_field_polynomial_subtraction_candidate_theorems", 27165, "d08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b",),
    ("prime_field_polynomial_degree_candidate", "make_prime_field_polynomial_degree_candidate_theorems", 12579, "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5",),
    ("prime_field_polynomial_trim_candidate", "make_prime_field_polynomial_trim_candidate_theorems", 26425, "1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c",),
    ("prime_field_polynomial_division_candidate", "make_prime_field_polynomial_division_candidate_theorems", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2",),
    ("prime_field_polynomial_monic_candidate", "make_prime_field_polynomial_monic_candidate_theorems", 25658, "3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef",),
    ("finite_sum_pointwise_mod_candidate", "make_finite_sum_pointwise_mod_candidate_theorems", 16646, "8e6c55bc4700302d57959e3318b595d616b185b3af5329988b17b295a929de8a",),
    ("signed_integer_division_candidate", "make_signed_integer_division_candidate_theorems", 9708, "f9471954bb5e2bd470ae09c08da4b224839c7a29942816f9cf43c8d48cced384",),
)
# Congruence providers are a separate exact family, not a registry scan.
CONGRUENCE_CANONICAL_PROVIDERS = (
    ("linear_congruence_complete_candidate", "make_linear_congruence_complete_candidate_theorems", 26450, "133cab6b63fa7b2341a475ebb4a78ca22882d8176224c3fe4d91c13d7df2589f",),
    ("ha_generalized_crt_congruence_candidate", "make_ha_generalized_crt_congruence_candidate_theorems", 18256, "3f22b381e60a2fb78e5617b0a9ca1a0deee63ee9980dc17dfacc048ce3dbb976",),
    ("finite_modular_set_candidate", "make_finite_modular_set_candidate_theorems", 88019, "e1b4ed6a2e9609d5156457aed0891b378868dbaad4e7a914af29bb211c0d9469",),
    ("generalized_crt_compatibility_candidate", "make_generalized_crt_compatibility_candidate_theorems", 62427, "1f88ba8af0b1169072387419c4bd9732cae20b94008ab476d3bfda3acaa00859",),
    ("fermat_endpoints_candidate", "make_fermat_endpoint_candidate_theorems", 12968, "cfbf54b85c2c64393603e34186f5b34866c6c8062301117443155b617e7a6c9d",),
    ("fermat_product_balance_candidate", "make_fermat_product_balance_candidate_theorems", 9914, "bb559bb91a3a3018badbe075f042c093e39731787150171992faafcdade878f9",),
    ("fermat_residue_product_candidate", "make_fermat_residue_product_candidate_theorems", 14389, "b43a6fa9be64b806d9973abfb0d566533910c8a841fba16777b8a9498b98d59d",),
    ("fermat_residue_reindex_candidate", "make_fermat_residue_reindex_candidate_theorems", 25813, "5f214433ba7528a4f5d016de86623551d1fd9921bf9c74e76db3c4fc6cb7ace0",),
    ("fermat_scale_product_candidate", "make_fermat_scale_product_candidate_theorems", 14556, "cfa834d77d591c3c0385ad64371fdddd06d096f9482d337f7b190a3ae2066395",),
    ("fermat_residue_map_candidate", "make_fermat_residue_map_candidate_theorems", 19111, "2b30505a6f6febe5e55874726855b25ae63ed420afd1c3821ba5a082509833e8",),
    ("finite_product_reindex_candidate", "make_finite_product_reindex_candidate", 30400, "2a838774b7dc3ce0bf1d5b3aad34f20faf5a8e51a43a4d81928ed757cc20dc12",),
)
GCD_OWNED_PROVIDERS = (
    ("prime_field_polynomial_shift_candidate", "make_prime_field_polynomial_shift_candidate_theorems", 29786, "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b", 15, "beac32710e2191f4dc40f6317dc376f6b3307ad8ad48a7ccbac17c8bea990081",),
    ("prime_field_polynomial_scalar_convolution_candidate", "make_prime_field_polynomial_scalar_convolution_candidate_theorems", 23637, "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e", 10, "a8ab3e2660a01dc79520722de6093c534e4184dcdbcb9481317df4d5b6a54a7b",),
    ("prime_field_polynomial_append_candidate", "make_prime_field_polynomial_append_candidate_theorems", 28396, "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042", 6, "6035968b0f11aec5e4bd6cb43b4d4958318b55f600fab914025479f571b75c2a",),
    ("prime_field_polynomial_shift_equivalence_candidate", "make_prime_field_polynomial_shift_equivalence_candidate_theorems", 6021, "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068", 1, "d68b99a4ed9f996bd7e8b23fd0f17e165176b949f07a806a4d2c935d4372529e",),
    ("prime_field_polynomial_associativity_step_candidate", "make_prime_field_polynomial_associativity_step_candidate_theorems", 26607, "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1", 3, "87017c7298a0247444be68f9be34e6b354b89d491ca7ee49ea4bd06effd6b2cd",),
    ("prime_field_polynomial_associativity_induction_candidate", "make_prime_field_polynomial_associativity_induction_candidate_theorems", 9924, "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c", 2, "b6ad06b7925dbb35202bb263ef14c7dc69d18c80771e075497d0a17d42294dc8",),
    ("prime_field_polynomial_divisibility_candidate", "make_prime_field_polynomial_divisibility_candidate_theorems", 15168, "f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8", 7, "2ee9efd3344ef213b2170f080ff541ca0a7a45a018ace9f2f7912cd301bc8bce",),
    ("prime_field_polynomial_left_unit_candidate", "make_prime_field_polynomial_left_unit_candidate_theorems", 16858, "dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6", 8, "d948ceded7269773df58eca0ec6d16f77aa8f207483beed48f85bec30e083f08",),
    ("prime_field_polynomial_alignment_candidate", "make_prime_field_polynomial_alignment_candidate_theorems", 11780, "eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e", 7, "76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec",),
    ("prime_field_polynomial_aligned_add_candidate", "make_prime_field_polynomial_aligned_add_candidate_theorems", 20704, "a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db", 9, "b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339",),
    ("prime_field_polynomial_aligned_algebra_candidate", "make_prime_field_polynomial_aligned_algebra_candidate_theorems", 16013, "a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390", 4, "0db1ddc08762db5e207469343143a7ead24de983e8f9a21473592a8d6c97d6f4",),
    ("prime_field_polynomial_euclidean_identity_candidate", "make_prime_field_polynomial_euclidean_identity_candidate_theorems", 11235, "8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77", 2, "f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27",),
    ("prime_field_polynomial_aligned_distributivity_candidate", "make_prime_field_polynomial_aligned_distributivity_candidate_theorems", 8518, "7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba", 2, "22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719",),
    ("prime_field_polynomial_left_constant_candidate", "make_prime_field_polynomial_left_constant_candidate_theorems", 17620, "9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a", 6, "736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836",),
    ("prime_field_polynomial_euclidean_normalization_candidate", "make_prime_field_polynomial_euclidean_normalization_candidate_theorems", 16401, "d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f", 5, "815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74",),
    ("prime_field_polynomial_euclidean_transport_candidate", "make_prime_field_polynomial_euclidean_transport_candidate_theorems", 18256, "9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30", 5, "aba201eca067048dc65b5a2f7f6affd415c6ebd639c35bc613503227a65059b8",),
    ("prime_field_polynomial_bezout_backward_candidate", "make_prime_field_polynomial_bezout_backward_candidate_theorems", 18747, "c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702", 3, "bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564",),
    ("prime_field_polynomial_gcd_bezout_laws_candidate", "make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems", 15300, "76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c", 4, "cbf875f3e7d13394f062e4f5f4349beba59a2ac363a599e7b02649906ea6d6a2",),
    ("prime_field_polynomial_gcd_existence_candidate", "make_prime_field_polynomial_gcd_existence_candidate_theorems", 26480, "81f2f48dd2e81894c7a267453646eb6f2b6f9bd3ee320386d8c561f6b9f8b8ca", 9, "d0bfe3e77e26b0e97c3b20bdd3f6256064c2b34ff56a48039e04f9dbdfcc5d7e",),
    ("prime_field_polynomial_gcd_uniqueness_candidate", "make_prime_field_polynomial_gcd_uniqueness_candidate_theorems", 31432, "916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b", 11, "4bea19123a71314f8d2bf07019377497f56990b31f71a51de861f2b9339a1db3",),
)
# Literal final canonical source; the original Fermat row is extracted intact.
CONGRUENCE_OWNED_PROVIDERS = (
    ("linear_congruence_classification_candidate", "make_linear_congruence_classification_candidate_theorems",
     18128, "12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47", 12,
     "b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8"),
)

@dataclass(frozen=True, slots=True)
class SourceContract:
    slug: str
    owned_count: int
    owned_specs_sha256: str
    owned_names_sha256: str
    theorem_count: int
    dependency_edges: int
    dfs_names_sha256: str
    dfs_specs_sha256: str
    root_names: tuple[str, ...]
    original_frontier_count: int
    original_frontier_specs_sha256: str
    original_names_sha256: str
    original_specs_sha256: str

GCD_CONTRACT = SourceContract(
    "polynomial-gcd-bezout", 119,
    "72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38",
    "51f959e944c81af1f430aebed63f10934f50f67fdae6934048551ce7bbf81ef5",
    492, 1565,
    "608ac8f64143e60628e49875efd3b3ef3c5389eff2f17ecabe98f96770a9e93f",
    "453f7dc94a9ed2fb6c89730024af97e6aaec9168c30c106450d57d2cea8db0eb",
    ("prime_field_polynomial_convolution_shift_right_exists", "prime_field_polynomial_convolution_right_scale_exists", "prime_field_polynomial_convolution_right_scale_zero", "prime_field_convolution_coefficient_right_append_add", "prime_field_polynomial_convolution_right_append_exists", "prime_field_polynomial_right_divides_dividend_bounded", "prime_field_polynomial_right_divides_reflexive", "prime_field_polynomial_aligned_subtract_from_fixed", "prime_field_polynomial_aligned_subtract_functional", "prime_field_polynomial_left_constant_product_to_scale", "prime_field_polynomial_division_constant_remainder_empty", "prime_field_polynomial_normalized_gcd_bezout_exists", "prime_field_polynomial_normalized_gcd_equivalent_unique",),
    325, "7751feff227a4b298a2c484f83bf85c2a5db730ed9e4e2f62b095b1f5866252a",
    "37f749a11c76fd6d38d4a328dfd450fd8a0ea3e79ffac8f22ad4874239f29e25",
    "ae797cbf373142f63f7dd86af1f5ddad0909f4f1df755af6ad523a9c6c7e1d5d",
)
CONGRUENCE_CONTRACT = SourceContract(
    "congruence-arithmetic", 12,
    "b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8",
    "fa61dfc9de450ee1609d02d7de06cb0292fa5de682e306b444807bb4926d2d8c",
    214, 642,
    "3b10febcef718754d645ba4afd07eea6de441b1b1a2a2a8ca55e0d6ce5ae38de",
    "61c20f122d4281a6177865d1d39cd3a5b3939584c852ca028647e0bcf46cc157",
    ("linear_congruence_exact_bounded_enumeration_exists", "linear_congruence_zero_modulus_nonzero_coefficient_unique", "linear_congruence_zero_modulus_zero_coefficient_iff", "linear_congruence_modulus_one_bounded_iff_zero", "fermat_little_all_inputs",),
    12, "b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8",
    "d8f0f89555c5808404bee144e0372f145b6f696e0a0030399c52dc7e193fae90",
    "8d2b30a02f7103507dba33c635d3f3728e6aedd7451b0ec6a7c78b67111d8094",
)

def _require(condition, message):
    if not condition:
        raise SourcePlanError(message)

def _configuration(slug):
    _require(type(slug) is str, "source family must be an exact string")
    if slug == "polynomial-gcd-bezout":
        value = GCD_CONTRACT, GCD_CANONICAL_PROVIDERS, GCD_OWNED_PROVIDERS
    elif slug == "congruence-arithmetic":
        value = CONGRUENCE_CONTRACT, CONGRUENCE_CANONICAL_PROVIDERS, CONGRUENCE_OWNED_PROVIDERS
    else:
        raise SourcePlanError("unknown v34 source family")
    contract, canonical, owned = value
    _require(type(contract) is SourceContract and contract.slug == slug
             and type(canonical) is tuple and type(owned) is tuple and bool(owned),
             "the exact family source/original-order contract is not registered")
    return value

def _read_source(module, size, digest):
    _require(type(module) is str and re.fullmatch(r"[a-z][a-z0-9_]*", module) is not None,
             "invalid canonical source module")
    _require(type(size) is int and 0 < size <= MAX_SOURCE_BYTES
             and type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
             "invalid exact source byte pin")
    path = HERE / (module + ".py")
    _require(not path.is_symlink() and path.is_file() and path.stat().st_size == size,
             "canonical source type/size changed: " + module)
    with path.open("rb") as stream:
        raw = stream.read(size + 1)
    _require(len(raw) == size and sha256(raw).hexdigest() == digest,
             "canonical source digest changed: " + module)
    return module, size, digest

def _module_factory(record):
    module_name, factory_name, size, digest = record[:4]
    _read_source(module_name, size, digest)
    module = import_module("." + module_name, package=__package__)
    path = HERE / (module_name + ".py")
    factory = getattr(module, factory_name, None)
    _require(type(module) is ModuleType and getattr(module, "__file__", None) == str(path)
             and getattr(getattr(module, "__spec__", None), "origin", None) == str(path),
             "foreign canonical module ownership: " + module_name)
    _require(callable(factory) and getattr(factory, "__module__", None) == module.__name__,
             "foreign canonical factory ownership: " + module_name)
    result = factory(TheoremSpec)
    _require(type(result) is tuple and all(type(row) is TheoremSpec for row in result),
             "canonical factory did not return exact theorem specifications")
    _read_source(module_name, size, digest)
    return result

def _edition_bindings():
    return {name: value for name, value in sys.modules.items()
            if name.startswith("peano_lab.library.editions")}

def _source_inputs(slug):
    contract, canonical, owned = _configuration(slug)
    records = (("theorems", *THEOREMS_PIN), *(
        (r[0], r[2], r[3]) for r in (*canonical, *owned)))
    _require(len({r[0] for r in records}) == len(records),
             "canonical and new source owners overlap")
    return contract, canonical, owned, records

def _merge(table, rows):
    for row in rows:
        _require(type(row) is TheoremSpec and (row.name not in table or table[row.name] == row),
                 "different exact specifications share a canonical name")
        table.setdefault(row.name, row)

def canonical_provider_table(slug="polynomial-gcd-bezout"):
    _contract, canonical, _owned, _records = _source_inputs(slug)
    before = _edition_bindings()
    _read_source("theorems", *THEOREMS_PIN)
    table = {}
    _require(type(THEOREMS) is tuple, "canonical theorem ladder is not an exact tuple")
    _merge(table, THEOREMS)
    _require(len(table) == len(THEOREMS), "canonical theorem ladder repeats a name")
    for record in canonical:
        _merge(table, _module_factory(record))
    _read_source("theorems", *THEOREMS_PIN)
    _require(_edition_bindings() == before, "source planning imported/replaced an Alpha edition")
    return MappingProxyType(table)

@dataclass(frozen=True, slots=True)
class SourceCone:
    specs: tuple[TheoremSpec, ...]
    owned: tuple[TheoremSpec, ...]
    canonical: tuple[TheoremSpec, ...]
    root_names: tuple[str, ...]

def source_cone(slug="polynomial-gcd-bezout"):
    """Exact source DFS inventory; artifact positions are deliberately absent."""
    contract, _canonical, owners, records = _source_inputs(slug)
    before = _edition_bindings()
    for record in records: _read_source(*record)
    # Lazy source metadata reconciliation; no call to research_family(), whose
    # full release registration also needs the still-independent artifact gates.
    from . import campaign_research_v34_closure as research
    declared = tuple(owner for owner in research.FACTORIES if owner.campaign == slug)
    actual_records = tuple((o.module, o.factory, o.source_bytes, o.source_sha256,
                            o.count, o.specs_sha256) for o in declared)
    _require(actual_records == owners, "provider/source-planner owner records differ")
    owned = []
    for record in owners:
        rows = _module_factory(record)
        _require(len(rows) == record[4] and _specs_digest(rows) == record[5],
                 "owned factory exact specification digest changed")
        owned.extend(rows)
    owned = tuple(owned)
    _require(len(owned) == contract.owned_count
             and len({r.name for r in owned}) == len(owned)
             and _specs_digest(owned) == contract.owned_specs_sha256
             and sha256("\n".join(r.name for r in owned).encode()).hexdigest() == contract.owned_names_sha256,
             "the exact family-owned source inventory changed")
    canonical = dict(canonical_provider_table(slug))
    overlaps = canonical.keys() & {r.name for r in owned}
    allowed = {"fermat_little_all_inputs"} if slug == "congruence-arithmetic" else set()
    _require(overlaps == allowed, "new source shadows canonical syntax or loses its literal extraction")
    for row in owned:
        if row.name in overlaps:
            _require(canonical[row.name] == row, "the extracted Fermat specification changed")
            del canonical[row.name]
    table = {**canonical, **{r.name: r for r in owned}}
    ordered, seen, active = [], set(), set()
    def visit(name):
        _require(name in table and name not in active, "missing/cyclic source prerequisite: " + name)
        if name in seen: return
        row = table[name]
        _require(type(row.dependencies) is tuple and len(set(row.dependencies)) == len(row.dependencies)
                 and all(type(n) is str for n in row.dependencies),
                 "malformed exact source prerequisites")
        active.add(name)
        for dependency in row.dependencies: visit(dependency)
        active.remove(name)
        seen.add(name)
        ordered.append(row)
    for row in owned: visit(row.name)
    specs = tuple(ordered)
    used = {name for row in specs for name in row.dependencies}
    roots = tuple(row.name for row in owned if row.name not in used)
    _require(len(specs) == contract.theorem_count
             and sum(len(row.dependencies) for row in specs) == contract.dependency_edges
             and roots == contract.root_names
             and sha256("\n".join(r.name for r in specs).encode()).hexdigest() == contract.dfs_names_sha256
             and _specs_digest(specs) == contract.dfs_specs_sha256,
             "the exact source DFS cone changed")
    for record in records: _read_source(*record)
    _require(_edition_bindings() == before, "source planning imported/replaced an Alpha edition")
    return SourceCone(specs, owned, tuple(row for row in specs if row.name in canonical), roots)

@dataclass(frozen=True, slots=True)
class SourceSelection:
    specs: tuple[TheoremSpec, ...]
    owned: tuple[TheoremSpec, ...]
    frontier: tuple[TheoremSpec, ...]
    plan: object
    root_names: tuple[str, ...]

    @property
    def positions(self):
        return MappingProxyType({row.name: row.node_id for row in self.plan.rows})

def source_selection(slug="polynomial-gcd-bezout"):
    """Use the unchanged original planner; only this API opens the v30 parent."""
    contract, _canonical, _owned, records = _source_inputs(slug)
    selected = source_cone(slug)
    from . import campaign_bottom_layer_closure as original
    parent = {row.name: row for row in original.parent_snapshot().specs}
    for row in selected.specs:
        _require(row.name not in parent or row == parent[row.name], "original v30 overlap differs")
    frontier = tuple(row for row in selected.specs if row.name not in parent)
    _require(len(frontier) == contract.original_frontier_count
             and _specs_digest(frontier) == contract.original_frontier_specs_sha256,
             "the separate original-v30 frontier changed")
    plan = original.bottom_layer_plan(frontier)
    table = {row.name: row for row in selected.specs}
    _require({row.name for row in plan.rows} == table.keys()
             and plan.root_names == selected.root_names,
             "the original plan has a different complete cone/root set")
    for row in plan.rows:
        exact = table[row.name]
        _require(row.dependencies == exact.dependencies
                 and row.statement_sha256 == sha256(exact.statement.encode()).hexdigest(),
                 "original planner target or ordered prerequisites differ")
    specs = tuple(table[row.name] for row in plan.rows)
    _require(plan.ordered_names_sha256 == contract.original_names_sha256
             and _specs_digest(specs) == contract.original_specs_sha256,
             "original artifact order or exact complete specification digest changed")
    from . import campaign_research_v34_closure as research
    if research.REGISTRATION_COMPLETE is True:
        family = research.research_family(slug)
        _require(tuple(row.name for row in specs) == family.ordered_cone_names
                 and family.ordered_cone_names_sha256 == contract.original_names_sha256
                 and family.complete_specs_sha256 == contract.original_specs_sha256,
                 "registered artifact order differs from the actual original source plan")
    for record in records: _read_source(*record)
    return SourceSelection(specs, selected.owned, frontier, plan, selected.root_names)
