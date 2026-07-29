"""Independent admission audit for congruence and Gödel-beta values."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib

import driver

from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, parse_formula_with_names
from peano_lab.kernel.proofs import Axiom, Cut, DNE, EqRefl, Hyp, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import _specs_by_name, get, replay


EXPECTED = {
    "mod_eq_trans": {
        "dependencies": ("add_assoc", "add_comm", "mul_add"),
        "statement": "07009140b6d6d7f4e1e34d6c33bf1b007ea29c26a14eeafa9b2fa3d377abe7a9",
        "script": (42, "5c6a6bf4b3f23de8a7e5eb7bf40cd16d426d00c345fb5e9f834ecba808da2e9f"),
        "certificate": ((252, 29), 6, "052be6f7213b8697002669ec4b938db550329a8573d520d03cb51af28630bd61"),
    },
    "mod_eq_add": {
        "dependencies": ("mul_add", "add_comm", "add_permute_outer"),
        "statement": "6e8c1e97ea5c4221a993e587d4475550418981e5fbef1b4c65e149dee0713ddd",
        "script": (42, "7789df1fd37be5a3be0d6d6cbf4e6c0867bf135e3508ca852e99ec0386c5394f"),
        "certificate": ((370, 30), 10, "49e4d310fb281152161969987650ed529899ec2db8d310000cbe9c0aebb8b986"),
    },
    "mod_eq_mul_right": {
        "dependencies": ("add_mul", "mul_assoc"),
        "statement": "8733e14f0e281c8da5e450d12fe21b7d5929d4b5e9953d867333be510677d636",
        "script": (26, "cf7e391dc56ca71ba86f22be7ecc663e8af5872ccb0a7e21f88fb32496540a2e"),
        "certificate": ((484, 26), 13, "4994212781f9a86bb60622ca1fe8ad409d0bb500791af6a24b5a825098729e27"),
    },
    "mod_eq_mul_left": {
        "dependencies": ("mod_eq_mul_right", "mul_comm"),
        "statement": "dbadf46b1b0bf5a186fbdd59491a88885e0649b62e28e8465f6dee8bdb9e21fe",
        "script": (25, "950e4ebdc52eae84f677b237f20983484305d5af68f3da71457c99287a889dcf"),
        "certificate": ((738, 27), 21, "84e29f574f4ebbcb3993c2746183e370648a84346c8cf4e46f50a28581bf9dc6"),
    },
    "mod_eq_mul": {
        "dependencies": ("mod_eq_mul_right", "mod_eq_mul_left", "mod_eq_trans"),
        "statement": "a3983a74ea581e76450a400c1ed5b4e06e6feac6ff9a6ebb90d8f82f3c316d2b",
        "script": (28, "7e6cb0f149bca7982d666e9b5365ca4dda9449c28943be656d98ff4a94fdc87e"),
        "certificate": ((1_505, 32), 43, "660f19930d52443997b878d9fbc824d96e6070e8e7304d08159dcb591af5cc56"),
    },
    "remainder_decomposition_to_mod_eq": {
        "dependencies": ("add_comm", "mul_comm"),
        "statement": "5329024af13cfcbc0e4662ef24110fcbe2ece3d384ffca5c07cf3f6b7a49b55b",
        "script": (16, "2992d90f135d6b779fc3d926e9fce7e53496c3301dedcc2a55b10eef23b55ad2"),
        "certificate": ((323, 26), 10, "acea3f60f7fa7dfcd1745c5cb1dd1d20436c173affa5518ebcb4f981b6893b19"),
    },
    "mod_eq_bounded_unique": {
        "dependencies": ("add_comm", "division_remainder_unique"),
        "statement": "8e73abc172b556b5fb557c527977e6f07c1e366080b207163dd58b7931643c0d",
        "script": (28, "5a41e200eef2c09137f70c22f1e0bfb69ac5559741c198834c63d8495fa2917c"),
        "certificate": ((961, 59), 26, "9bdbf756db7d40a03088e05e9f311290d4ce31c6304913bcc5a3a12d5a0c2f89"),
    },
    "mod_eq_to_remainder_decomposition": {
        "dependencies": (
            "division_remainder_exists",
            "add_comm",
            "mul_comm",
            "mod_eq_trans",
            "mod_eq_bounded_unique",
        ),
        "statement": "03d36e6993b3691311ccb9e9e75006895f186ff659f1042d9b69fe4811db2360",
        "script": (51, "142583f023f91df0300654d0b53de0ff14549d484ad3e927a1e548758ba20862"),
        "certificate": ((1_793, 64), 50, "a92fbaccbecc0472384e7c424f6b72dda864ce0922174b87828afea85ba5320a"),
    },
    "beta_modulus_nonzero": {
        "dependencies": ("succ_ne_zero",),
        "statement": "6701007cb46c44334c05d9bd894078b9b002f9624b4057b9203dd83087294526",
        "script": (4, "a257b75ac056a1cb2f3caa2c4e5839e1e6bd054244563bcb6993fcb8f7a4c20b"),
        "certificate": ((9, 6), 1, "e8ce620074f6ed37285a3dc034e72bc8f267c4442673ed7dc77c9db067d2f314"),
    },
    "beta_at_self_of_bound": {
        "dependencies": ("mul_zero_left", "zero_add"),
        "statement": "2d7d05bc900916fb1c5e23a402436d7e460ee6ad7ac1de57ba9cc1db76a9c095",
        "script": (12, "b7d6bf2e801f275c7bd097dc7903391161a1b43d9c78d6aa7ec0cf67ad0955b9"),
        "certificate": ((62, 16), 2, "b563c1208a1c868c1c93ba1f03ddef49f5acdcf564dc44edfd0d3ea4e3f5aef4"),
    },
    "beta_at_exists": {
        "dependencies": (
            "beta_modulus_nonzero",
            "mul_comm",
            "division_remainder_exists",
        ),
        "statement": "acd7a937d6ec7c3c4d6214357bdfcdf3a975ccd71f7e14a540a1690d5e9b1773",
        "script": (24, "26c9e7b0a2a682552cbf79df3d6826b613851a3900507ef7298223cade742bf8"),
        "certificate": ((479, 31), 15, "967de23f5a2e16ad6917ba20073cb2b63a1ab562945069360c57b040c48078d4"),
    },
    "beta_at_unique": {
        "dependencies": ("mul_comm", "division_remainder_unique"),
        "statement": "eac0700b7c24aa059073c61ffdf1541dc02d23400571b003fe964b9df65f5afd",
        "script": (37, "4283a8c482f83a0cbea6bdcb718123ac1f20c922b12ea1862d672ca4752ba4af"),
        "certificate": ((1_121, 59), 30, "891320ec08736c26f18d9ac34c38da3df2b764b63794d0a33c8820ce51caf2ae"),
    },
    "beta_at_exists_unique": {
        "dependencies": ("beta_at_exists", "beta_at_unique"),
        "statement": "e113675254fcdd4275f8c427c704dc1eb9816fb5cc2e251d0995ece07f983228",
        "script": (22, "2bc0efab1270e45491a7d3e22ee0a4002c200f646c78152645b925c48d45fd62"),
        "certificate": ((1_625, 61), 47, "37ae2a410d200b75cd68831454765e500dc8dafcc77b8a51ed60f9a79f971d8c"),
    },
    "beta_at_to_mod_eq": {
        "dependencies": ("remainder_decomposition_to_mod_eq",),
        "statement": "c748a4a17fd48703d134abcd46e96aa5ef082fc1f9aa69ce089d1421446d565d",
        "script": (13, "ab6a199f73fef6b1309d2690f5f9546a534bbc7b37f6e007b271d5fbab2d7b12"),
        "certificate": ((358, 27), 11, "dd174002d4701711239c5958acc580ca4ff11c1788aff4936b9a8d9ad65562e6"),
    },
    "beta_at_of_mod_eq_bound": {
        "dependencies": ("beta_modulus_nonzero", "mod_eq_to_remainder_decomposition"),
        "statement": "9934b7b533260bf9c2c53f4a06d653873048b3ccb1b78fba0bd897fe6a604536",
        "script": (17, "9793a6989e45a6b331c687f4a0f7e057fcc20a966e269f5dc646a9770da8ac14"),
        "certificate": ((1_839, 66), 53, "e4a2ead06ca651304be645d679f5e7e81da4ede0afd9997f2f59864f7b01074f"),
    },
    "bezout_mod_left": {
        "dependencies": ("add_assoc", "add_comm"),
        "statement": "7c933e89b5e783e0fe57654937ee8202b8b0a917184b23463fccbda85de308b0",
        "script": (19, "f3828f2a187f21e71e99b16eac7dd26300a29c468da8cc40071fad3fb12a97dd"),
        "certificate": ((134, 19), 4, "0ba24c738b192b0a35c82006181468cc99f2d1cea106cfdaf43d38e80d5b20e2"),
    },
    "bezout_mod_right": {
        "dependencies": ("add_assoc",),
        "statement": "2b9829ff7d6d6582927a7b85c058b531717e3d91259f9bcc574a76f687eec068",
        "script": (13, "b536b76554c8b03ff31194d28bc162a51636713784307c2d659b3ee5552cb2c0"),
        "certificate": ((50, 16), 1, "2b31fb490cc73a830a30434cc534a5a880ed1d52921a4ec97c3e6cdbd932beb2"),
    },
    "mod_eq_predecessor_cancel": {
        "dependencies": ("add_assoc", "add_comm", "mul_succ_left"),
        "statement": "ff9e6397219fcf402e7a0e46e5d1ce0cee284f43b12ebdd124e21082c0170db4",
        "script": (15, "bb918309a373e8829e44b53205816842834e936c6e644241c3c8f9b4c2339244"),
        "certificate": ((315, 25), 9, "35e5bcc4216481e35319981c1f0536cda87b5ec2a6c2215b49d5b686cea7686f"),
    },
    "binary_crt": {
        "dependencies": (
            "nonzero_is_succ",
            "coprime_balanced_bezout",
            "bezout_mod_left",
            "bezout_mod_right",
            "mod_eq_mul_left",
            "mul_add",
            "mul_one",
            "dvd_to_mod_zero",
            "mul_assoc",
            "mul_comm",
            "mod_eq_add",
            "mod_eq_refl",
            "mod_eq_trans",
            "mod_eq_predecessor_cancel",
            "zero_add",
        ),
        "statement": "25e1f5213a9a5b04f3a20077b936ba8814f6ae8951f4f72e5f5e2135d7c9148f",
        "script": (276, "16a1f89d08a1f88ddffa41e9f5b0c81e2bcf8d8b056cd239ae82d01e80de673e"),
        "certificate": ((5_044, 51), 144, "fd5384ba933f194fe0229c01f97f3261d12dfe8586196f1fdd390349aefad2df"),
    },
    "binary_crt_remainders": {
        "dependencies": ("binary_crt", "mod_eq_to_remainder_decomposition"),
        "statement": "ddcf02df0ca3aa652ebe043c1fd2cf099ff83c77a550d263fb143dcff3147a56",
        "script": (44, "af70451e2aa8c622fb07d64f2990919364781717c493adebb465164a946363af"),
        "certificate": ((6_890, 66), 196, "f3432e4bdae49a7b4c832eb34d5c1550436a146e36a4321130d2045f4637bd2f"),
    },
    "binary_crt_beta_pair": {
        "dependencies": ("beta_modulus_nonzero", "binary_crt", "beta_at_of_mod_eq_bound"),
        "statement": "38fc1d7a370130b0342285a0d06f441aea33cfe4881d6215a86f86fdbb3ecb7e",
        "script": (47, "c922363bdbcc3cc43560fbbb358d5f408fcdd77e17092fa73a70e1549e612d71"),
        "certificate": ((6_941, 69), 201, "d0c6658e1cbb304cd57f39f2a60f1695aeac5bd52587d87d8d22ecdf29067776"),
    },
    "beta_modulus_coprime_base": {
        "dependencies": ("divides_remainder", "divisor_one", "mul_comm"),
        "statement": "e3888d0932249958689f3ec9e8d191cf866212c101dabfe5b62c198c39c4d373",
        "script": (20, "5a184438ec47cbcaefa77c2cfec764f5fab1c64509eb9ec832609392037fa545"),
        "certificate": ((874, 30), 24, "f7e3c800ecbe062e709ee0d115860418d316389e361f5b26c5e460340ed6ce42"),
    },
    "common_divisor_beta_moduli_divides_gap_times_c": {
        "dependencies": (
            "divides_remainder",
            "add_succ_left",
            "add_mul",
            "zero_add",
        ),
        "statement": "5e42d3c08bd8cc965eac53bfd7e6abfdf30d1a27ee43f0d38ab3febc24389b0f",
        "script": (27, "bf289ffe19464b806b973dc2271b0ea7218eaa5724d8f42bd0e0fea69b70ed29"),
        "certificate": ((855, 30), 24, "42a60bc7d8feda4822b114ce9a25a29d27d03a2ab6b9cb2e8a078f4942a8862a"),
    },
    "beta_moduli_coprime_of_gap_dvd": {
        "dependencies": (
            "beta_modulus_coprime_base",
            "common_divisor_beta_moduli_divides_gap_times_c",
            "multiple_trans",
            "multiple_refl",
            "gauss_coprime_cancel",
            "mul_comm",
        ),
        "statement": "df6c3daf567bc06a5ca361d2b1cfc976d2ec1bca03f3b8dd5e24dba8b0070602",
        "script": (59, "bee06c03429b6c7f54a1d21e3676efe6002f870c848181331d89c38c90945f97"),
        "certificate": ((6_007, 56), 175, "e31f87a1af34325c3566489d1e3ffe0220e721312a89d0f9a62ea1ea88cf3fe8"),
    },
    "binary_crt_beta_pair_of_gap_dvd": {
        "dependencies": ("beta_moduli_coprime_of_gap_dvd", "binary_crt_beta_pair"),
        "statement": "ca85aea2052028f5d185d8c782cf933f0d06c2c7c40d86f3657aad907f3131e5",
        "script": (27, "beef18023d324c09cc87fa9619a743277d018baa55dea765bc220d51e40aa054"),
        "certificate": ((12_980, 71), 378, "79ec20e402f2b19088c6fb04d4e63229715dbf4e5565e648b4b0f38842fa2a47"),
    },
    "bounded_common_multiple_step": {
        "dependencies": (
            "mul_eq_zero",
            "succ_ne_zero",
            "zero_or_succ",
            "multiple_mul_right",
            "mul_comm",
        ),
        "statement": "7a8fdf6f5a7e1d28efecf7a58005eb7f45d21dccd7aee4cb2cd8acbe7ca792ec",
        "script": (52, "144ec3170f18ec447363382768190823f628a9c5871656c202525ef7d650cc39"),
        "certificate": ((483, 29), 15, "aa455c44508fbe46578348227387b413695af701093b7b5daf55c1a284c9ccd0"),
    },
    "bounded_common_multiple_exists": {
        "dependencies": ("bounded_common_multiple_step", "succ_ne_zero", "add_eq_zero_left"),
        "statement": "ad3921906117ef267f82ff3e9be6d228c7872b98fccb582228c9d4a86866019f",
        "script": (29, "b8222e577fbfc91069929b6a67c9805960a397085ce99fe75c0bfedda4843953"),
        "certificate": ((640, 30), 22, "ccb71e803625625f870e7768b2428a556b41ee1700e549c7f2ddb728865729bd"),
    },
    "beta_moduli_coprime_of_lt_bounded_common_multiple": {
        "dependencies": ("beta_moduli_coprime_of_gap_dvd", "add_comm", "le_trans"),
        "statement": "d63d720fac911184a5163168382a134d76d511a2c6708360a83516556f3568df",
        "script": (49, "2dc67e9f19028d34659f947cbebe999b178d084b2241e0a4b95acdddb08b0869"),
        "certificate": ((6_227, 57), 181, "9d97203f21642818bc2e1d67faa7c2966de4009a0c2f54aacedce2859e59f32b"),
    },
    "beta_moduli_pairwise_coprime_bounded": {
        "dependencies": (
            "lt_trichotomy",
            "beta_moduli_coprime_of_lt_bounded_common_multiple",
        ),
        "statement": "eb5bc880e1349d365cef2c73bd1b3412bac10615d2c14180fddbbb2f54dbcc2c",
        "script": (44, "f8cef8ba6ceb42f302f6764105332adde40c12cf7c2b6b300a20f37bf8df813a"),
        "certificate": ((6_348, 59), 183, "67f94b6555418915f7bddeb843f5a7fd534561870f47f2bbf34d46e198321e50"),
    },
    "bounded_beta_moduli_pairwise_coprime_exists": {
        "dependencies": (
            "bounded_common_multiple_exists",
            "beta_moduli_pairwise_coprime_bounded",
        ),
        "statement": "f499fb8acd42b42caded26f6014a5b4a3ee3ddebe58d1880d2889572a2c82624",
        "script": (11, "b0cab17e9a9125d5c9c19da173d9612e36566ce3e4be7ab8271c7b9d4e21630d"),
        "certificate": ((7_019, 61), 207, "6d8ad65d4fb5f26e141244738ab53b71c3e02eb6fde9cc0f4b4960929099b2b4"),
    },
    "coprime_mul_left": {
        "dependencies": ("multiple_trans", "gauss_coprime_cancel"),
        "statement": "1060b24a0e43b4388c2ac9ecac0e76f60914ccf6cd449d37592e4b4d22461735",
        "script": (34, "5b32c98008b843275b4874f36b3a4499fe6aab9a19f8454923de6e4695149ed8"),
        "certificate": ((3_975, 53), 115, "51b298808927c2b05a997c183519cd9f611b49d94b9e8e067b70cccf4ef65891"),
    },
    "coprime_mul_right": {
        "dependencies": ("coprime_mul_left", "coprime_symm"),
        "statement": "8f9f43f8c2176f47aee5d0fb6063be7cf3a2f75d0116e04f396c4af9315e85f6",
        "script": (26, "de42848f8338801def489375de61afec839f916dfbd2ab188c5108b4c917cf40"),
        "certificate": ((4_017, 54), 117, "8a3a38d99c52a152ee05e9848a8c207d5ad54494e24915ed01edc34d0e575c57"),
    },
    "mod_eq_of_mod_eq_multiple": {
        "dependencies": ("mul_assoc",),
        "statement": "246654070ff9a4577e17991d9189766a93fe7c11629ec2303a8ad111c86451e3",
        "script": (23, "8106127a4ddfb8a0eddfa7aff9714c1445f1a7ef8c5563c2a19ad9a55086119d"),
        "certificate": ((157, 23), 3, "f3d6047561573ffeeeb14c5985c18ababcc42f38cc2784a6f4f5275e68d6bf76"),
    },
    "binary_crt_fold_step": {
        "dependencies": ("binary_crt", "mod_eq_of_mod_eq_multiple", "mod_eq_trans"),
        "statement": "41595b681a738bcfa873935a4aed93b2a865da235cc68d0910aba631cfd4e432",
        "script": (40, "e7b70f504e72e6f465846f1f10ac0ba5d4e3d252cce005281abbc03020784a17"),
        "certificate": ((5_501, 52), 156, "f65c05b0db8af551e664f3194314657c999a9e6528c3dcf71a0ad0f02161f820"),
    },
    "right_factor_divides_product": {
        "dependencies": ("mul_comm",),
        "statement": "4bfe67ec918a0e0f7c189a56fda0d1b256ecaefc78272611b51ec68507987b7d",
        "script": (4, "fc069fee03a0522bf18640f442245e3976773e794ed10e3b7ec69cd86d63ae72"),
        "certificate": ((229, 25), 7, "91ff76024f693baa1003685dc3cd57b2e1ebbf3c51dbf38f26f7bce1c573ba35"),
    },
    "beta_accumulated_product_step": {
        "dependencies": (
            "mul_ne_zero",
            "right_factor_divides_product",
            "beta_modulus_nonzero",
            "le_eq_or_lt",
            "le_of_succ_le_succ",
            "multiple_mul_right",
            "le_succ_self",
            "lt_of_le_of_lt",
            "lt_irrefl_expanded",
            "beta_moduli_pairwise_coprime_bounded",
            "coprime_mul_left",
        ),
        "statement": "caf17d298d156e39ff0ff4e24095d6938d04728114b9395a13f3a415be77d13d",
        "script": (90, "3f0c5cda980d008d014b89957dd92e9ea091a94050df45965211e5e7d3cb373c"),
        "certificate": ((11_174, 69), 330, "6da6cc49d4d9374497ee0572f98c23f835adb41e2432a1557fb0a47d9cc7495f"),
    },
    "beta_crt_prefix_congruence_step": {
        "dependencies": (
            "beta_modulus_nonzero",
            "le_refl",
            "binary_crt_fold_step",
            "beta_at_exists",
            "beta_at_unique",
            "le_eq_or_lt",
            "le_of_succ_le_succ",
        ),
        "statement": "9e2859391ee169231064da3447b9c610f525b6a76b6ace99f827a40fc07c90b0",
        "script": (88, "96aed1f2ac79c6e9fc4ed8406f49dd48818eeab0e799d8bce5b913bfbf4d5f3b"),
        "certificate": ((7_352, 64), 213, "39d62088be96c5368f12cc2426c8468e21c1cea2233409483a95eb2279300038"),
    },
    "beta_crt_prefix_invariant_step": {
        "dependencies": (
            "beta_accumulated_product_step",
            "beta_crt_prefix_congruence_step",
        ),
        "statement": "a420d4f1da24e4d2c44eaa20cdb9d3b190ac93023c24e223a25652b30533c448",
        "script": (47, "ba5be610f34c2a587a80e76a2e915839541bfd78c6d5cd1e353205f1e6b1d859"),
        "certificate": ((18_613, 70), 545, "9cb74ed1e6aa131bab8b5a7775bd80588f8064838fffb78df2f016f26b6de5dd"),
    },
    "bounded_beta_crt_prefix_invariant": {
        "dependencies": (
            "beta_modulus_nonzero",
            "le_zero",
            "multiple_refl",
            "beta_at_to_mod_eq",
            "beta_moduli_coprime_of_lt_bounded_common_multiple",
            "le_succ_self",
            "le_trans",
            "beta_crt_prefix_invariant_step",
        ),
        "statement": "d6b26a8578f6f3ad456060e7d2bdbad9435eadf57e995f5d37ec3e5671d40cdd",
        "script": (81, "a9191946e416077a530d179a26828a5a0eb486a236ce093802958095fe3abecd"),
        "certificate": ((25_496, 78), 752, "ef961db40c76a35a48af0bc94bc2b691844d77fa63efd64520718dcca2cdc072"),
    },
    "bounded_beta_crt_for_existing_code": {
        "dependencies": ("bounded_beta_crt_prefix_invariant", "le_refl"),
        "statement": "bf9bf8445ee1467abf5eb668e9f0e0e73f9bdd5eccd2457c58f4ff7b3ee789f8",
        "script": (22, "aea748f15d03a84e81ac3ec2a51f1f29e760e569cb905240ab0cec7f95b97f39"),
        "certificate": ((25_545, 79), 755, "8d9242fe5e071655fc62172df0a001c9a8389703d1d4c58ade5bacf0a313369c"),
    },
}


EXPECTED.update(
    {'beta_value_le_code': {'dependencies': (),
                            'statement': 'a0b0b9cc668ff0d5345e4b2e41b08ac66b3210e536258d53f95b88337c01876c',
                            'script': (10,
                                       'f897d69a620a878a9922324fdc060adb017430fb0d606a4218cb79a551a6ab7f'),
                            'certificate': ((18, 13),
                                            0,
                                            'f037744e9dd7652f7148d661d88996ad038bf475bb06018383f213f5f268956b')},
     'base_le_beta_modulus': {'dependencies': ('le_add_left', 'mul_succ_left', 'le_succ'),
                              'statement': '850c8372cd6743df77e4354d3cf23d92749917cdda214f1c1ac0dbe0868b32f9',
                              'script': (13,
                                         'f9c14f73174fd55d6ceece6d107af0121e196497641a286f81e2ebb8f1dda7ae'),
                              'certificate': ((233, 24),
                                              8,
                                              'cdc7fe6d2ef27872c6be9917a443e0e6bf77b1c48d3b68e3db87e6a2aaab443b')},
     'le_scaled_nonzero': {'dependencies': ('one_le_of_ne_zero', 'mul_le_mul_right', 'one_mul'),
                           'statement': '3a0c9778138f2ee2ecbab9a5c829a4b1f40f19de61b65eae4765f67ebb1dedaa',
                           'script': (16,
                                      'e56a72093d932f1e0a4cb658c015d7447ee0b9bfbfd7ed39593a42305564bcdc'),
                           'certificate': ((407, 28),
                                           13,
                                           'd68bec41b22273c876385ad01d69025f97c61d815a3fdf54b6c2b7a5045f6652')},
     'scaled_bounded_common_multiple': {'dependencies': ('multiple_mul_right',),
                                        'statement': 'a514ad09db5eae76cb17193a87016a905895f8450a3f9bb35dc77ef00b299945',
                                        'script': (15,
                                                   '044fc9f0fd3b4c5714bd59425202719557fc6a9134519287c16873d14397277b'),
                                        'certificate': ((147, 19),
                                                        4,
                                                        'c4ce3a408de716082d8b9f72c5efcb6a8e52b689ee07ad6d396d06eedec9dbe4')},
     'beta_value_lt_scaled_base': {'dependencies': ('beta_value_le_code',
                                                    'le_add_right',
                                                    'succ_le_succ',
                                                    'le_trans',
                                                    'le_scaled_nonzero',
                                                    'base_le_beta_modulus'),
                                   'statement': '723e34f7303079ad1d5510dcde76756e36f758aed266f6bf8bd225aa8b568268',
                                   'script': (54,
                                              '7b89ce9cb9add05e6078c43bc183035da94ac7b2c528d023fba19b758e7604cb'),
                                   'certificate': ((863, 33),
                                                   31,
                                                   '05aeb5bdd1f80ada1023ab728c03df39a8064475d8bfd5bdcdfff30bf6a8fb27')},
     'new_value_lt_scaled_base': {'dependencies': ('le_add_left',
                                                   'succ_le_succ',
                                                   'le_scaled_nonzero',
                                                   'le_trans',
                                                   'base_le_beta_modulus'),
                                  'statement': '17864693ef24007d91e415865da8a8623b72bb3e2c4aae995e72665c9929fb8c',
                                  'script': (36,
                                             '094590f0d3bdb0ce3a9030341857ca484a0e085691412f8119fc8f2e64aab30a'),
                                  'certificate': ((751, 31),
                                                  27,
                                                  '08fcf3a5d804a316fce0d656a44e4eaeb13cc336a455e351628d2f31ca1387b5')},
     'beta_exclusive_accumulated_product_step': {'dependencies': ('mul_ne_zero',
                                                                  'right_factor_divides_product',
                                                                  'beta_modulus_nonzero',
                                                                  'le_of_succ_le_succ',
                                                                  'le_eq_or_lt',
                                                                  'multiple_mul_right',
                                                                  'le_succ_self',
                                                                  'le_trans',
                                                                  'lt_to_le',
                                                                  'lt_irrefl_expanded',
                                                                  'beta_moduli_pairwise_coprime_bounded',
                                                                  'coprime_mul_left'),
                                                 'statement': '623df71bb00a1df01ed2b113ce65eb8e8c1b5ae56fd4a92a05861cd2b914b2bb',
                                                 'script': (95,
                                                            '5885e1ce2ad76e91ee9787480a1781c37247abd8a5721fbbb61413284d536287'),
                                                 'certificate': ((11222, 70),
                                                                 332,
                                                                 '1833bd103225a199bd1eb410fe3869a3963f49335c33a6b2462f7157f156cd58')},
     'beta_exclusive_recode_congruence_step': {'dependencies': ('beta_modulus_nonzero',
                                                                'le_refl',
                                                                'lt_to_le',
                                                                'binary_crt_fold_step',
                                                                'beta_at_exists',
                                                                'beta_at_unique',
                                                                'le_of_succ_le_succ',
                                                                'le_eq_or_lt'),
                                               'statement': '29947a185cb5bd3e6d5f3addc026b0c148f4e5aca0428989ce28c64955dce949',
                                               'script': (92,
                                                          '22bd35bfd4d21ef60b75fe1078126bc5cca8f0699b110171ef6aa7ac7749c608'),
                                               'certificate': ((7398, 65),
                                                               215,
                                                               '282847b6bbbacfe5a6ff683a06c017ee5e7f1b4d77d8d9ae8b28cb35c9d0abd6')},
     'beta_exclusive_recode_invariant_step': {'dependencies': ('beta_exclusive_accumulated_product_step',
                                                               'beta_exclusive_recode_congruence_step'),
                                              'statement': '9eaa14524e19b2f11771b44c6676033b3e31080ee96371c11bac0f48ca1c51f6',
                                              'script': (49,
                                                         '23c691e57a88affc4036ecd0477e3eacfd414e66d78fe1bd21ede3ac10f8f245'),
                                              'certificate': ((18709, 71),
                                                              549,
                                                              '1057ae7a6b5e5e24ee9976a188920c7a8f12c002c51a4d1db60c7eb932b97ef1')},
     'bounded_beta_exclusive_recode_invariant': {'dependencies': ('succ_ne_zero',
                                                                  'add_eq_zero_right',
                                                                  'coprime_one_left',
                                                                  'le_succ_self',
                                                                  'le_trans',
                                                                  'beta_exclusive_recode_invariant_step'),
                                                 'statement': '29564e9bae7783feeb631c02f82f5e9af720bdfd28c9b4c49aba47a41ff0d6c3',
                                                 'script': (89,
                                                            '2234db2a3820961b2658ed68d633e6dcb4e4e91d9d560de2257b3cb31bf97b9a'),
                                                 'certificate': ((19155, 77),
                                                                 563,
                                                                 '2c9541dd49fb1a6242210f3062931f5313d4632e445135bcad5e9b06fee01295')},
     'beta_prefix_extend': {'dependencies': ('bounded_common_multiple_exists',
                                             'scaled_bounded_common_multiple',
                                             'bounded_beta_exclusive_recode_invariant',
                                             'le_refl',
                                             'beta_modulus_nonzero',
                                             'binary_crt_fold_step',
                                             'new_value_lt_scaled_base',
                                             'beta_value_lt_scaled_base',
                                             'beta_at_of_mod_eq_bound'),
                            'statement': '292c7a2a1abbf591e9a3cfd77ad0533f12761f691460fca7a20f413c6f66a1e0',
                            'script': (105,
                                       'd7218aa3a387b948290f7bfc0f26f11623978d06a5cd0ce4a7b61cc96f688e69'),
                            'certificate': ((29057, 80),
                                            867,
                                            '511d3bde3fc45d7ab2748c39baacb167b9eb05f71d6c43ad1d1eb03fbb23c7f6')},
     'beta_prefix_product_trace_exists': {'dependencies': ('beta_at_self_of_bound',
                                                           'add_eq_zero_right',
                                                           'succ_ne_zero',
                                                           'beta_at_exists',
                                                           'beta_prefix_extend',
                                                           'zero_le',
                                                           'succ_le_succ',
                                                           'le_refl',
                                                           'le_of_succ_le_succ',
                                                           'le_eq_or_lt',
                                                           'one_mul'),
                                          'statement': '81d12aa55dbd4e5d3fef95cdca2ed566435b28fc9e3406a884c8b76b2f0af5d2',
                                          'script': (133,
                                                     'b0626fe4fcf99759859d8e90458c59dc61c4a3b96d1ba1eb5b1a7e1815e3958a'),
                                          'certificate': ((29981, 85),
                                                          899,
                                                          '0dd19ccc0b06503a99e50627eaed2b9bda46c7a5f2685916bde03e1a17ae1f41')},
     'beta_product_exists': {'dependencies': ('beta_prefix_product_trace_exists', 'beta_at_exists'),
                             'statement': '65955dade14a69f532b45f1541232206f1b80a684b8424f6b7b39f1d24df7bb3',
                             'script': (25,
                                        'dd2383d50814503f133930679d865ff79c3621668d9dd11dd1a66bc4464d943b'),
                             'certificate': ((30487, 86),
                                             916,
                                             '6656c8e6b7f3ea457a7353422f510f6a97b4910fc83b7cbb50bf6a6b5170516f')}}
)

EXPECTED.update(
    {
        "beta_product_functional": {
            "dependencies": ("beta_at_unique", "le_refl", "le_succ", "mul_congr"),
            "statement": "0d622682bc03f814ac15b4a40a55d8a3ef7c98c0b2047884df7c25da6ca1a0d8",
            "script": (
                153,
                "54af853b75c0dd8fedd8197d7e8ac3fc7c398e2713c7fc202d9a647e60baaed0",
            ),
            "certificate": (
                (1_382, 60),
                36,
                "12a5727a4593b04b404e2c26eb8a444f4a705305504076c3759078e7fab116d0",
            ),
        },
        "beta_product_exists_unique": {
            "dependencies": ("beta_product_exists", "beta_product_functional"),
            "statement": "438428ac3b1580108ccd4c694f5138dfe3f8f6006021687e2c1f0874356ff480",
            "script": (
                32,
                "d8ddef944cb5949d7c156758015a276b3aefe9bb63a86d127d08540602a53272",
            ),
            "certificate": (
                (31_908, 87),
                954,
                "7a2e26c9d93074adf5eaaf163a6979bc281a988178f7a14f316ff63a72bc5820",
            ),
        },
    }
)

EXPECTED.update(
    {
        "beta_product_zero": {
            "dependencies": ("beta_at_unique",),
            "statement": "311da073e3b279a1c8a11c70e0c320d5728c686f858c65882f380864943c904f",
            "script": (
                16,
                "f98f0bf4b30a2794fdab7e7d4559e7f5d80b03d8629b4c1aadc2e95d013eff6d",
            ),
            "certificate": (
                (1_171, 60),
                31,
                "63088511aac2ef0c5aa853cedc17a39582c96785bc149a143e3a166732358033",
            ),
        },
        "beta_product_succ_decompose": {
            "dependencies": ("le_refl", "le_succ", "beta_at_unique"),
            "statement": "03469f0a2a01256aebd276b930955e026afe285ea8143da27e5d07d19f70c6a2",
            "script": (
                51,
                "743f4400d3b5b55c28f8afb309d7cb80ea6296d899c481c6e659ad7264d78cde",
            ),
            "certificate": (
                (1_257, 62),
                35,
                "2a5502bdcf7379de0e5682ad43a19c8a55ac4e11adf199ef4675d83f0c848adc",
            ),
        },
        "beta_product_succ_append": {
            "dependencies": (
                "beta_prefix_extend",
                "zero_le",
                "succ_le_succ",
                "le_refl",
                "le_of_succ_le_succ",
                "le_eq_or_lt",
            ),
            "statement": "df3c09efc7da4218e0eb7920aa005585e9d6426b6463525fb5a6cc97fcb7973c",
            "script": (
                101,
                "728ef2f69c39ba07c152322dcedf2ef48b6e30750d6c9056041cafde71c3c9f2",
            ),
            "certificate": (
                (29_360, 81),
                877,
                "ffa7ace29cd7a66b4fc65956c4a277328a3fe88d277c73ddbe3ed5594ced9bde",
            ),
        },
    }
)

EXPECTED.update(
    {
        "beta_product_transport_prefix": {
            "dependencies": (),
            "statement": "db9d6aad8466f739736000f4984e1bb872f63f5ed7481f6ccfbeb90512ae0c52",
            "script": (
                44,
                "5cb1362bf2c5ba8573a2479c0a93f90f4c406fba0b45da49ae4f690c70446d32",
            ),
            "certificate": (
                (59, 29),
                0,
                "4c40f0a22c7a5d071f32faee47106b462be9ba530351493ab9f1a8e5f1a79299",
            ),
        },
        "beta_factor_prefix_product_append": {
            "dependencies": (
                "beta_prefix_extend",
                "beta_product_transport_prefix",
                "zero_le",
                "succ_le_succ",
                "le_refl",
                "le_of_succ_le_succ",
                "le_eq_or_lt",
            ),
            "statement": "239265fa49cb97217f7c4dd13adb568af4010183e89f0d88edc37a1bfb4b320f",
            "script": (
                125,
                "47ed26e49f172b44f1012313dfab0e5b40fa33c2e96019fb8cdd7f3adadccd36",
            ),
            "certificate": (
                (29_447, 81),
                878,
                "ee15cbf3907116ded177678a1531f4ebc09d02c1beb71c77b6d662372aa5d318",
            ),
        },
    }
)

EXPECTED.update(
{'all_prime_empty': {'dependencies': ('add_eq_zero_right', 'succ_ne_zero'),
                     'statement': '0f059125f30e3e7d4e3e0aab6e0e668d8dde309d83980aa2301d19813b335a8d',
                     'script': (14,
                                '3bab06f2dff25324434fa0e63fff0155c48f486ac3993360091878abc1dafb7a'),
                     'certificate': ((37, 13),
                                     2,
                                     '17228ed7fa9b88944d80da4c91f4ab8ce7358d327b9df80175556f5af339f6a2')},
 'all_prime_succ_intro': {'dependencies': ('le_of_succ_le_succ', 'le_eq_or_lt'),
                          'statement': 'd3bdcbb783fd64b1702d5cec4dc1cf9549c8f6a062e7666b9d8018c499eb177b',
                          'script': (29,
                                     '868c93b5dcb370ee52693445e9ec36ae1cf396638d0434b0014d0b324a0f17c8'),
                          'certificate': ((150, 21),
                                          5,
                                          '7905f0e448fd961632ad9a07f2c97f8020a19091636f12f749cbb8683587950d')},
 'all_prime_succ_elim_prefix': {'dependencies': ('le_succ',),
                                'statement': '0c3ec2941e97a9fbb51c2a74441d9a415a2baa9f4a972ef36bd15df7c55bb3ea',
                                'script': (12,
                                           '8a176bbbf93e8c680b8bf466f3560024c1aa4f1600efc42dea5b9872061754e4'),
                                'certificate': ((64, 16),
                                                2,
                                                '0126509667dcf1b2218ca7f774ef70fee931aa71bedaa95490b4249d52faf54f')},
 'all_prime_succ_elim_last': {'dependencies': ('le_refl',),
                              'statement': 'fcaee0371b7bdf927111a11d8f8ccb1030be2ec5cb08278c635605ed74e0351a',
                              'script': (8,
                                         '10a209ec6583208e6d405e6284b9fe0b9f86f9913ca0a907748004c841a5cc96'),
                              'certificate': ((41, 11),
                                              2,
                                              'a36af944a5695e57f217c84aeefe22ed58419a90e61ad3803b18a6f88080622b')},
 'all_prime_transport': {'dependencies': (),
                         'statement': '6f2dc8af6b545e13025c45663e49cd41cf9f9dd58c4b0a1bec9b7382eddc4639',
                         'script': (23,
                                    'bbfe5f7041abd2a36b6aacc35b2865a11b9932aa4108668aab1c6f3815ec6d89'),
                         'certificate': ((26, 17),
                                         0,
                                         '4abed2d820d8c3e1b6c43df9b76beb390e46921981073599ec9ba712b919ebbb')},
 'sorted_empty': {'dependencies': ('le_zero', 'succ_ne_zero'),
                  'statement': '8b29eae60cd20ee4ea1ea4068f8cf4f48b48eff2a4b67cdf380e92c5c9ba0fb3',
                  'script': (12,
                             '8a87cdeadfd7d4efdf8b77e7d5fc9cb267389e81e329cd4a93da855a81440db3'),
                  'certificate': ((44, 14),
                                  3,
                                  'a3dc87fe88e5c5244404c842a1cf9fb9520a1259f42f9ec564a2f86c31f8f787')},
 'sorted_singleton': {'dependencies': ('le_of_succ_le_succ', 'le_zero', 'succ_ne_zero'),
                      'statement': '0c6452adfa86a812cb9e21dcfbdceb9f1173997ebd151856d18c58bc79a1cab5',
                      'script': (17,
                                 '88f88eec2a700d795f1f5f657c441f81ada345b3b5cbd1908def68278db4d080'),
                      'certificate': ((65, 15),
                                      4,
                                      '844e77f2d4bb617722d1a7d044e2423a3a597bc49c68e9095eaf03ba59542685')},
 'sorted_succ_intro': {'dependencies': ('le_of_succ_le_succ', 'le_eq_or_lt', 'succ_le_succ'),
                       'statement': '73fb1c3a586dd89a50de8c3ec1862d3a1f3d230d503b770d23079570e4bef7c6',
                       'script': (44,
                                  '957de8755b00fdcd4fff3556c3fa0a4dbfb4ab194dab2ea05dc54ee5b7577473'),
                       'certificate': ((182, 23),
                                       6,
                                       '8c5d249ae99aa2c761c10b10d8cebbba67efb14d2cccdff151244f57aada1faf')},
 'sorted_succ_elim_prefix': {'dependencies': ('le_succ',),
                             'statement': 'a17111b7acd62c9ef7027f733110e60cb45d242ba373c171f889f59bd5bfc835',
                             'script': (12,
                                        'c17f2901c45257202430a19423831f64b01ff952fe648b560ac3108bf3d948d9'),
                             'certificate': ((64, 16),
                                             2,
                                             '1fe322c40f9f5b3b64403b883ed548a1f05663fe56ba0542f439d32bac490570')},
 'sorted_succ_elim_last': {'dependencies': ('le_refl',),
                           'statement': 'c35472661f34e101ac0037f8c58977dd5c823c5c37b4d8e551c4b37493046588',
                           'script': (8,
                                      '857dab41b26e78a8b780c71c04110234eb6e7cdd68eb44d973971b7d3ea25844'),
                           'certificate': ((41, 11),
                                           2,
                                           '96d1e00a0d95382324cc33d03f3c4453f17529efd75d7aa0f2a633b887795665')},
 'sorted_transport': {'dependencies': ('lt_to_le',),
                      'statement': '50e56fadec7781f5070bd9ad01319c250d833ebad85045202aa14d61ca236e59',
                      'script': (37,
                                 '3a8facd30e805504e38c670dee2877c12a940e0702d8571f89281a2c55e9fb5e'),
                      'certificate': ((89, 21),
                                      2,
                                      'a9cf8c461f4ff4467f065dc3bb802063e738035814ca95cb62821f9daa7b67e4')},
 'beta_prefix_extend_all_prime': {'dependencies': ('beta_prefix_extend',
                                                   'all_prime_transport',
                                                   'all_prime_succ_intro'),
                                  'statement': '2fc472f7cb0a31f53ad8e172d9964815a9ce74b3dd78fa323f32061659dfded7',
                                  'script': (39,
                                             '2171e228ad878b2bdd72fe5ff04863b60dfc4ffbe98413e57880cee9df8280ff'),
                                  'certificate': ((29280, 81),
                                                  875,
                                                  'c99644a6fbf84262572c49be2120960cf7e03735b0378794c5b547a606a8277a')},
 'beta_prefix_extend_sorted_singleton': {'dependencies': ('beta_prefix_extend', 'sorted_singleton'),
                                         'statement': '9a6b37067dd2b9a0f9bc39abfbad9e91cd6e3fc692baebb0e0841961f2cf8239',
                                         'script': (21,
                                                    '3fc4c7e4576359ebcb6e75a2557179e63b7c79ee0135be8492a42213347a51fc'),
                                         'certificate': ((29146, 81),
                                                         873,
                                                         '5750ecab9c2a299e23b9008664cf0f4886f46d1c14d9d8e43cfbfac325b59cce')},
 'beta_prefix_extend_sorted_succ': {'dependencies': ('beta_prefix_extend',
                                                     'sorted_transport',
                                                     'sorted_succ_intro',
                                                     'le_refl'),
                                    'statement': '5007f0cb237dcbf2b6575d2591f2e691ab89604113d88e259ee808227e8993c9',
                                    'script': (49,
                                               '29214504fe0d2a63f89e1f5fb6925a32a8cea8653938f7d3d381bb9a0c87979f'),
                                    'certificate': ((29414, 81),
                                                    880,
                                                    'eb120eb89de0ed2f5be2d37f3f625be6717050ee1da4abc0f5b9ee86b23a80b4')},
 'beta_canonical_append_empty': {'dependencies': ('beta_factor_prefix_product_append',
                                                  'all_prime_empty',
                                                  'all_prime_succ_intro',
                                                  'sorted_singleton',
                                                  'one_mul'),
                                 'statement': '5ee6c61f3577982224da1804521bffd6339889074cd2f85c948e86a51103ac1d',
                                 'script': (47,
                                            '8eb713bc4b2ad0548518a29c3434d410ac09b9da7f62fe0e0f4fa52bc7484769'),
                                 'certificate': ((29783, 82),
                                                 894,
                                                 'e89975bab8dbdd4e9bfc37fb4f2978fb4c380950b86be642921f53703a0e0449')},
 'beta_canonical_append_succ': {'dependencies': ('beta_factor_prefix_product_append',
                                                 'all_prime_transport',
                                                 'all_prime_succ_intro',
                                                 'sorted_transport',
                                                 'sorted_succ_intro',
                                                 'le_refl'),
                                'statement': 'f3610b4e1841d58094d09ade755d4a3c60d3b4cfb71a6334b0f445f50a269057',
                                'script': (81,
                                           '314f5aa93735869882ca834e0a63e47fd5d16aa8e5bc415af5027a318adb67ef'),
                                'certificate': ((30020, 82),
                                                898,
                                                '618288aae5fa540d12b201cca09dfab3f02e631fffac385eb38f631b35d002f6')}}
)


EXPECTED.update(
{'prime_divides_decidable': {'dependencies': ('prime_decidable', 'multiple_decidable'),
                             'statement': '948060bcd202ce2dee345ed78127b2219e4dbf7f1b10ac78c7dbb325b8fb3b5e',
                             'script': (25,
                                        '04c1662115a7bf5fca94a03f4769ff37768a77a23efb0db68818cf6f2da5aec6'),
                             'certificate': ((3573, 74),
                                             101,
                                             '44c96dfc214fa323ad039990374f1cd246c07282216ab167d54c5372c89e11bb')},
 'greatest_prime_divisor_search': {'dependencies': ('prime_nonzero',
                                                    'le_zero',
                                                    'prime_divides_decidable',
                                                    'le_refl',
                                                    'le_eq_or_lt',
                                                    'le_of_succ_le_succ',
                                                    'le_succ'),
                                   'statement': '636d314e015c7bbc028aba8aa0ca6815f9d15c7b145e916a5ca85ce0dd964063',
                                   'script': (92,
                                              'fbc0a05777a64e32e1b9172af95e4b7c30a23e3e99f8ca377e7521355ca451c8'),
                                   'certificate': ((3949, 77),
                                                   116,
                                                   '6ea4e68703508591a9384dfe483a9657359f48efd68930d4ab5b2e4b30bd7de7')},
 'greatest_prime_divisor_exists': {'dependencies': ('prime_divisor_exists',
                                                    'divisor_le_nonzero',
                                                    'greatest_prime_divisor_search'),
                                   'statement': '8f40a677fbc3499ae6613b62788dea88baf9111262a1d30514599e0efaf0804c',
                                   'script': (47,
                                              '08acc24c02975fcbfe5824d9544869755264d6e31e3e29c0c61b1798b4a8bc1e'),
                                   'certificate': ((7052, 81),
                                                   214,
                                                   '4ee7dca9d7ad5fdb5315da2a2900c55728b30b9cc8e9b542a68d927394041ae9')},
 'greatest_prime_divisor_quotient_bound': {'dependencies': ('mul_comm', 'multiple_trans'),
                                           'statement': 'a005c3b7d9194a27cb6457c1f411ca6f1e65da1b331af86c134b44caa0fafee7',
                                           'script': (26,
                                                      '3e117a5a9e70f86f9c55d9fb18b8fa332c177cbda2e42f715b3cda54b748cf8a'),
                                           'certificate': ((388, 25),
                                                           11,
                                                           '3c331ed30837f1823efa22ae60505a660e04c033392dc70466ec1c6f743ccba4')},
 'greatest_prime_divisor_descent': {'dependencies': ('greatest_prime_divisor_exists',
                                                     'mul_comm',
                                                     'factor_nonzero_left',
                                                     'proper_factor_lt',
                                                     'greatest_prime_divisor_quotient_bound'),
                                    'statement': '14b91aab6933531916cc59111bba6a092951ca658270b0e0c10457ceae69d741',
                                    'script': (61,
                                               'e90917b6b2bf194126e54d0c904127d281e07acd331c0f7ecd7c9ff1c91b52cb'),
                                    'certificate': ((8256, 82),
                                                    253,
                                                    '136a861b3f30fdca9822ff3689d79d6bcbc378c9f25bc8d6b5fc09a53cb99400')},
 'beta_factor_divides_product': {'dependencies': ('add_eq_zero_right',
                                                  'succ_ne_zero',
                                                  'beta_product_succ_decompose',
                                                  'le_of_succ_le_succ',
                                                  'le_eq_or_lt',
                                                  'beta_at_unique',
                                                  'mul_comm',
                                                  'multiple_mul_right'),
                                 'statement': 'a97f917023d9ac99269ec43effedd133f268e94f91af4b3a65dd245bc123e635',
                                 'script': (82,
                                            'e951484e8c0ba146c32f8399d8d9ebed4be5ea629630df59197014876ab6cdbe'),
                                 'certificate': ((2970, 65),
                                                 85,
                                                 '1584e62c8f359db09dcd5672c1dd53112dc894f8faac24fc105eb8e78ecf3429')},
 'beta_canonical_last_factor_bound': {'dependencies': ('all_prime_succ_elim_last',
                                                       'beta_factor_divides_product',
                                                       'le_refl'),
                                      'statement': 'dfd452f54787b740ee82dcc378b19d4ddc67cf598181fa376ea476db24fc5feb',
                                      'script': (37,
                                                 '66df9015b1299ceeb64aa5ae8cbd738fa4d4c7993be38e908679a667644f3887'),
                                      'certificate': ((3079, 67),
                                                      91,
                                                      '0c23f5d9bd89ef74b0d6e23f3919b7683edf7e43fbfaf2d5eaf0ee1d3eef447a')}}
)


EXPECTED.update(
{'beta_canonical_append_general': {'dependencies': ('beta_factor_prefix_product_append',
                                                    'all_prime_transport',
                                                    'all_prime_succ_intro',
                                                    'zero_or_succ',
                                                    'sorted_singleton',
                                                    'sorted_transport',
                                                    'all_prime_succ_elim_last',
                                                    'beta_factor_divides_product',
                                                    'le_refl',
                                                    'sorted_succ_intro'),
                                   'statement': 'd30636a72e38a0c488316c46401b5469b2dc5a10f2e3c5c810e80e401b546a11',
                                   'script': (126,
                                              '703266422e5ff7c90b9edae2b0db727a7a94fae30f412d5fa0566de87c8e458e'),
                                   'certificate': ((33165, 82),
                                                   993,
                                                   '72e9862443acb69a36356cedf98587f23b817c84e38c6cfeeaa751c37ea461e9')},
 'prime_factorization_exists_up_to': {'dependencies': ('le_zero',
                                                       'le_eq_or_lt',
                                                       'le_of_succ_le_succ',
                                                       'eq_decidable',
                                                       'succ_ne_zero',
                                                       'beta_at_exists',
                                                       'beta_at_self_of_bound',
                                                       'beta_at_unique',
                                                       'one_mul',
                                                       'le_refl',
                                                       'add_eq_zero_right',
                                                       'all_prime_empty',
                                                       'sorted_empty',
                                                       'greatest_prime_divisor_descent',
                                                       'beta_canonical_append_general',
                                                       'mul_comm'),
                                      'statement': '2ec4c9d79e4b033d21b5af527114ebe21e874d63fc46cd46e65a08f1b9944c4b',
                                      'script': (153,
                                                 '2a7fe784c86786ace30546ad3f2aaefb3b98dc2da3c735279dd28e3b600feb74'),
                                      'certificate': ((43927, 97),
                                                      1325,
                                                      'ba5730d9fb3ed6ebe42130962563fcb56cd16f806c9d8d0f1ea3fa0e298c5370')},
 'prime_factorization_existence': {'dependencies': ('prime_factorization_exists_up_to', 'le_refl'),
                                   'statement': '8c84cf902e277e4a3ff011bff49183e48d33847d640e199cc462f8fbb9267c6d',
                                   'script': (8,
                                              '5b41405a579147dfec4db6a53c5d291a0a6bf062b369d9d3571501b25b712245'),
                                   'certificate': ((43973, 98),
                                                   1328,
                                                   'f25aa6adb2b3043fd363f25a25972854dd78b3065c96524990efb45321f9126e')}}
)


EXPECTED.update(
{'beta_prime_divisor_product_member': {'dependencies': ('beta_product_zero',
                                                         'divisor_one',
                                                         'beta_product_succ_decompose',
                                                         'all_prime_succ_elim_prefix',
                                                         'all_prime_succ_elim_last',
                                                         'euclid_prime_dvd_product',
                                                         'prime_divisor_eq_one_or_self',
                                                         'beta_at_unique',
                                                         'le_succ',
                                                         'le_refl'),
                                        'statement': '51b452dc951d2892954bdba767ed93a34ed836c7d86c900dd9bffa4a124932db',
                                        'script': (114,
                                                   '9736a63c6d918b06714b6a1f48bce28dab000689029f57028ad3192dc32b99c8'),
                                        'certificate': ((9499, 67),
                                                        277,
                                                        '7723a9186a8afca0b69b239c65b8f9421cf7be5fda34816d0d384d5bbc446df4')},
 'beta_sorted_factor_le_last': {'dependencies': ('le_of_succ_le_succ',
                                                 'le_zero',
                                                 'beta_at_unique',
                                                 'le_refl',
                                                 'le_eq_or_lt',
                                                 'sorted_succ_elim_prefix',
                                                 'sorted_succ_elim_last',
                                                 'le_trans'),
                                'statement': '2e5ce055d82a7ac9eb6fd31a73db9a5811c4e816b545b079b92c0b10101ba4b5',
                                'script': (106,
                                           'd8d66932d95eecc071c72a84483fa5e1b4f0b519101a15c0dce60fa4f9a93a7c'),
                                'certificate': ((1587, 62),
                                                48,
                                                '02ee4e476daec327158f31db69f3a6b3440dd696c32e21a90d52bb229d613a41')},
 'beta_nonempty_all_prime_product_ne_one': {'dependencies': ('all_prime_succ_elim_last',
                                                             'beta_factor_divides_product',
                                                             'le_refl',
                                                             'divisor_one'),
                                            'statement': '61ad581bdf49b186b80800555c6b0a7502dda8b9a77489a323154fbdf48d2717',
                                            'script': (35,
                                                       '61bfc70ae34be81036d3bf54607083d1f5847c16b2bbe27c1a20c037dbf5fd3a'),
                                            'certificate': ((3266, 67),
                                                            96,
                                                            '9cde473a6b8fdb8a1f41f83f2fb3097a4fd9310964caab1693a3ea5592425273')},
 'beta_all_prime_product_one_iff_length_zero': {'dependencies': ('beta_product_zero',
                                                                 'beta_nonempty_all_prime_product_ne_one',
                                                                 'succ_ne_zero'),
                                                'statement': '7fe520e2f06c5439c839d42669bd0d82cfef1abc502a1ef86a7af81c59868ae2',
                                                'script': (34,
                                                           '7c23c713947029011bb26d74a136a249d25cb94457eb88200a260947813ce41e'),
                                                'certificate': ((4506, 69),
                                                                130,
                                                                '6edf708691c668af3b2c719f3c9ae4913f16a3100260ee5372ddaebca7d0495a')},
 'beta_canonical_last_factors_equal': {'dependencies': ('all_prime_succ_elim_last',
                                                        'beta_at_unique',
                                                        'beta_factor_divides_product',
                                                        'le_refl',
                                                        'beta_prime_divisor_product_member',
                                                        'beta_sorted_factor_le_last',
                                                        'le_antisymm'),
                                       'statement': '2e1ba71c3f9cf660318537120de4d416efc1fba2ffa88a32c81bd8fd4466aaf4',
                                       'script': (138,
                                                  '25dffe8aa164086277406e812e93d134ef5d236bc63e65cc9d5745bcc296b89e'),
                                       'certificate': ((15648, 72),
                                                       456,
                                                       '930f4810f83f9333f4f2e5685025a1244d2887d0315442969471aee366aa0dc2')},
 'beta_canonical_product_cancel_last': {'dependencies': ('beta_product_succ_decompose',
                                                         'beta_canonical_last_factors_equal',
                                                         'all_prime_succ_elim_last',
                                                         'beta_at_unique',
                                                         'prime_nonzero',
                                                         'mul_right_cancel_nonzero',
                                                         'all_prime_succ_elim_prefix',
                                                         'sorted_succ_elim_prefix'),
                                        'statement': '80816bdf59bdcd1137b2b0d0658e8267aec272ebb3afce6c795e3ed2aa58a400',
                                        'script': (148,
                                                   '026cd19b767bcd73032c41b1753f9e4bd85db54967624e47a3fb87690b32f650'),
                                        'certificate': ((18993, 74),
                                                        552,
                                                        '7670e0b1e59f1fd3eed1faddee381e267fb259aa9e31c54dc362d7c71517c4d7')}}
)


EXPECTED.update(
{'prime_factorization_uniqueness_by_length': {'dependencies': ('beta_product_zero',
                                                               'beta_all_prime_product_one_iff_length_zero',
                                                               'add_eq_zero_right',
                                                               'succ_ne_zero',
                                                               'beta_nonempty_all_prime_product_ne_one',
                                                               'nonzero_is_succ',
                                                               'beta_canonical_product_cancel_last',
                                                               'succ_congr',
                                                               'le_of_succ_le_succ',
                                                               'le_eq_or_lt',
                                                               'beta_at_unique'),
                                              'statement': '9d9a8619e8dba36d00e4eb7eac65926301fec20b8b76d2e3634adbf80d1d44b0',
                                              'script': (211,
                                                         '11f8a0aa4be89ea562d4bada841854a70e94aec31c025ceb793993410e6ab8df'),
                                              'certificate': ((29739, 81),
                                                              853,
                                                              'c12e77244e859e98e1b09e1e2401e0a3b6652cec9700a189165524c4a70559d3')},
 'prime_factorization_uniqueness': {'dependencies': ('prime_factorization_uniqueness_by_length',),
                                    'statement': 'feaebf08fc1ba3f23ed60db1fbc6d736644fabea457f0ae1a33db2d00064a63c',
                                    'script': (19,
                                               '030d095f81b877505d6766cbe980e2954dffa27a58ff6e5c2ec0cd21f6de72ce'),
                                    'certificate': ((29789, 82),
                                                    854,
                                                    '2d7a7156431d5a3889af82cfb66b9d48c30b01b9ed191372317b3e8ae46ac401')}}
)


EXPECTED.update(
{'fundamental_theorem_of_arithmetic': {'dependencies': ('prime_factorization_existence',
                                                        'prime_factorization_uniqueness'),
                                       'statement': '1091d994a724ada8f1f7343c420606167cdc50470c0c1a14476bc259b5c4b24d',
                                       'script': (3,
                                                  '266cf07f365e7e877198604f5559ea6c572fabc8f4feffb4b3a134fbd2324b07'),
                                       'certificate': ((73767, 99),
                                                       2184,
                                                       'fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958')}}
)


EXPECTED.update(
{'prime_unbounded': {'dependencies': ('bounded_common_multiple_exists',
                                      'prime_divisor_exists',
                                      'prime_nonzero',
                                      'nonzero_is_succ',
                                      'add_succ_left',
                                      'add_comm',
                                      'divides_remainder',
                                      'divisor_one',
                                      'mul_one',
                                      'le_or_lt'),
                     'statement': '70bdce28233e66ad5122d08e151baf867ee306b7ae49fe0faf5ed70f9314ca51',
                     'script': (84,
                                '003ce9702743fc2f81143321a98189e502aaa54d2e952656c1d83a566f5b0105'),
                     'certificate': ((4595, 82),
                                     146,
                                     '8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b')}}
)


EXPECTED.update(
{'prime_three': {'dependencies': ('mul_succ_left',
                                  'mul_eq_one_components',
                                  'add_eq_zero_left',
                                  'mul_eq_zero',
                                  'mul_zero_left',
                                  'zero_or_succ'),
                 'statement': 'eb78195353302d30dad4c218c384fd4a5e81aee71e8ed7b81fbd2e1e187fd067',
                 'script': (94,
                            'eefae85a02458bb8a05799fedf707daa4aff257a49f5ebad5940759967f3133c'),
                 'certificate': ((691, 43),
                                 18,
                                 'e6386e0d41a9ef03996570cc1e545b967ae86e740b582e5dbcb83321e7d4e819')},
 'two_prime_product_uniqueness': {'dependencies': ('euclid_prime_dvd_product',
                                                   'prime_divisor_eq_one_or_self',
                                                   'prime_nonzero',
                                                   'mul_left_cancel_nonzero',
                                                   'mul_comm'),
                                  'statement': '8852feae5d1f85675a2a01d6bbf3a732df8accb1817535fe75b3e7bb892ba5eb',
                                  'script': (77,
                                             '8f231a38756813b81b17986476ba4c83e6819eb3db5a2939849c90c054ed9a64'),
                                  'certificate': ((6035, 56),
                                                  181,
                                                  'bb1cd0a1af5d4c71f9287fe2fcd686c1633c0cda5dd67999486167bfb3b9cf02')}}
)


ZERO = Zero()
TRUE = Eq(ZERO, ZERO)


def _digest(value: object) -> str:
    return hashlib.sha256(repr(value).encode()).hexdigest()


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _cut_spine(proof: Proof) -> tuple[Cut, ...]:
    result: list[Cut] = []
    while type(proof) is Cut:
        result.append(proof)
        proof = proof.body
    return tuple(result)


def _replace_dependency_by_true(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        return replace(proof, proposition=TRUE, lemma=EqRefl(ZERO))
    return replace(
        proof,
        body=_replace_dependency_by_true(proof.body, index - 1),
    )


def _mutate_first(proof: Proof, node_type: type[Proof], replacement):
    if type(proof) is node_type:
        return replacement(proof), True
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            changed_child, changed = _mutate_first(child, node_type, replacement)
            if changed:
                return replace(proof, **{item.name: changed_child}), True
    return proof, False


def _mutate_authored_body(proof: Proof, node_type: type[Proof], replacement):
    if type(proof) is Cut:
        body, changed = _mutate_authored_body(proof.body, node_type, replacement)
        return replace(proof, body=body), changed
    return _mutate_first(proof, node_type, replacement)


def _cold_rows():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for name in EXPECTED:
        theorem = replay(name)
        assert check((), theorem.certificate, theorem.formula)
        rows.append((name, theorem.certificate, _digest(theorem.certificate)))
    return tuple(rows)


def test_exact_contracts_and_deterministic_constructive_replay() -> None:
    first = _cold_rows()
    second = _cold_rows()
    assert second == first

    for name, certificate, certificate_digest in first:
        expected = EXPECTED[name]
        spec = get(name)
        assert spec is not None
        formula, free_names = parse_formula_with_names(spec.statement)
        script_length, script_digest = expected["script"]
        metrics, cut_count, expected_certificate_digest = expected["certificate"]
        nodes = tuple(_walk(certificate))

        assert free_names == ()
        assert hashlib.sha256(spec.statement.encode()).hexdigest() == expected["statement"]
        assert spec.dependencies == expected["dependencies"]
        assert len(spec.script) == script_length
        assert _digest(spec.script) == script_digest
        assert replay(name).formula == formula
        assert certificate_digest == expected_certificate_digest
        assert proof_metrics(certificate) == metrics
        assert sum(type(node) is Cut for node in nodes) == cut_count
        assert not any(type(node) is DNE for node in nodes)
        assert {
            node.name for node in nodes if type(node) is Axiom
        } <= {"PA1", "PA2", "PA3", "PA4", "PA5", "PA6"}
        assert check((), certificate, formula)


def test_every_declared_dependency_slot_is_semantically_necessary() -> None:
    for name, expected in EXPECTED.items():
        theorem = replay(name)
        dependencies = expected["dependencies"]
        spine = _cut_spine(theorem.certificate)
        assert len(spine) == len(dependencies)

        for index, (cut, dependency_name) in enumerate(
            zip(spine, dependencies, strict=True)
        ):
            dependency = replay(dependency_name)
            assert cut.proposition == dependency.formula
            assert cut.lemma == dependency.certificate
            assert cut.conclusion == theorem.formula
            assert not check(
                (),
                _replace_dependency_by_true(theorem.certificate, index),
                theorem.formula,
            )


def test_every_certificate_rejects_pa_and_authored_hypothesis_mutations() -> None:
    for name in EXPECTED:
        theorem = replay(name)
        bad_axiom, changed = _mutate_first(
            theorem.certificate,
            Axiom,
            lambda node: Axiom("PA6" if node.name != "PA6" else "PA5"),
        )
        if changed:
            assert not check((), bad_axiom, theorem.formula)
        else:
            assert not any(type(node) is Axiom for node in _walk(theorem.certificate))

        bad_hypothesis, changed = _mutate_authored_body(
            theorem.certificate,
            Hyp,
            lambda node: Hyp(node.index + 1),
        )
        assert changed and not check((), bad_hypothesis, theorem.formula)


def test_public_live_use_closes_congruence_and_beta_endpoints() -> None:
    for name in (
        "mod_eq_trans",
        "mod_eq_add",
        "mod_eq_mul",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_bounded_unique",
        "mod_eq_to_remainder_decomposition",
        "beta_at_exists_unique",
        "beta_at_to_mod_eq",
        "beta_at_of_mod_eq_bound",
        "binary_crt",
        "binary_crt_remainders",
        "binary_crt_beta_pair",
        "beta_modulus_coprime_base",
        "common_divisor_beta_moduli_divides_gap_times_c",
        "beta_moduli_coprime_of_gap_dvd",
        "binary_crt_beta_pair_of_gap_dvd",
        "bounded_common_multiple_step",
        "bounded_common_multiple_exists",
        "beta_moduli_coprime_of_lt_bounded_common_multiple",
        "beta_moduli_pairwise_coprime_bounded",
        "bounded_beta_moduli_pairwise_coprime_exists",
        "coprime_mul_left",
        "coprime_mul_right",
        "mod_eq_of_mod_eq_multiple",
        "binary_crt_fold_step",
        "right_factor_divides_product",
        "beta_accumulated_product_step",
        "beta_crt_prefix_congruence_step",
        "beta_crt_prefix_invariant_step",
        "bounded_beta_crt_prefix_invariant",
        "bounded_beta_crt_for_existing_code",
        "beta_value_le_code",
        "base_le_beta_modulus",
        "le_scaled_nonzero",
        "scaled_bounded_common_multiple",
        "beta_value_lt_scaled_base",
        "new_value_lt_scaled_base",
        "beta_exclusive_accumulated_product_step",
        "beta_exclusive_recode_congruence_step",
        "beta_exclusive_recode_invariant_step",
        "bounded_beta_exclusive_recode_invariant",
        "beta_prefix_extend",
        "beta_prefix_product_trace_exists",
        "beta_product_exists",
        "beta_product_functional",
        "beta_product_exists_unique",
        "beta_product_zero",
        "beta_product_succ_decompose",
        "beta_product_succ_append",
        "beta_product_transport_prefix",
        "beta_factor_prefix_product_append",
        "all_prime_empty",
        "all_prime_succ_intro",
        "all_prime_succ_elim_prefix",
        "all_prime_succ_elim_last",
        "all_prime_transport",
        "sorted_empty",
        "sorted_singleton",
        "sorted_succ_intro",
        "sorted_succ_elim_prefix",
        "sorted_succ_elim_last",
        "sorted_transport",
        "beta_prefix_extend_all_prime",
        "beta_prefix_extend_sorted_singleton",
        "beta_prefix_extend_sorted_succ",
        "beta_canonical_append_empty",
        "beta_canonical_append_succ",
        "prime_divides_decidable",
        "greatest_prime_divisor_search",
        "greatest_prime_divisor_exists",
        "greatest_prime_divisor_quotient_bound",
        "greatest_prime_divisor_descent",
        "beta_factor_divides_product",
        "beta_canonical_append_general",
        "beta_canonical_last_factor_bound",
        "prime_factorization_exists_up_to",
        "prime_factorization_existence",
        "beta_prime_divisor_product_member",
        "beta_sorted_factor_le_last",
        "beta_nonempty_all_prime_product_ne_one",
        "beta_all_prime_product_one_iff_length_zero",
        "beta_canonical_last_factors_equal",
        "beta_canonical_product_cancel_last",
        "prime_factorization_uniqueness_by_length",
        "prime_factorization_uniqueness",
        "fundamental_theorem_of_arithmetic",
        "prime_unbounded",
        "prime_three",
        "two_prime_product_uniqueness",
    ):
        theorem = get(name)
        assert theorem is not None
        session = driver.LabSession()
        commands = (
            f"pa prove {theorem.statement}",
            f"use {name}",
            f"exact {name}",
            "qed",
        )
        results = tuple(session.run_result(command) for command in commands)

        assert all(result["failed"] is False for result in results)
        assert "QED." in results[-1]["out"]
