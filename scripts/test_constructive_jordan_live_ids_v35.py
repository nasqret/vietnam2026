"""Literal mandatory same-live UI cases; absence/skip/xfail must fail closed."""
EXPECTED_TEST_NAMES = {
    "jordan": (
        "test_jordan_live_inventory_and_exact_admission_boundary",
        "test_jordan_exact_scripts_alias_provenance_and_paired_pages",
        "test_jordan_canonical_graph_and_definition_dag",
    ),
    "atlas": (
        "test_atlas_live_inventory_and_unchanged_campaign_contracts",
        "test_atlas_conservative_definition_extension_and_real_routes",
    ),
}
