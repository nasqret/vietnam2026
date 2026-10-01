"""Source-only chunk tests. No native proof generation or worker is run."""

from hashlib import sha256
import unittest

import sqrt2_power_composition_chunks as chunks
import sqrt2_power_formal_composition as composition


class CompositionChunkSourceTests(unittest.TestCase):
    def test_sixteen_fixed_chunks_cover_all_original_leaf_positions_once(self):
        rows = chunks.chunk_contracts()
        self.assertEqual([row["id"] for row in rows], list(chunks.CHUNK_IDS))
        self.assertEqual(len(rows), 16)
        self.assertEqual([position for row in rows for position in row["original_leaf_positions"]], list(range(107)))
        self.assertEqual(sum(row["leaf_occurrences"] for row in rows), 107)
        self.assertEqual([row["leaf_occurrences"] for row in rows], [6, 7, 6, 7, 6, 7, 7, 7, 6, 7, 7, 7, 6, 7, 7, 7])

    def test_expanded_sources_and_ordinary_AST_hashes_are_independently_pinned(self):
        for row in chunks.chunk_contracts():
            with self.subTest(chunk=row["id"]):
                self.assertEqual(sha256(row["source"].encode()).hexdigest(), chunks.CHUNK_PINS[row["id"]][0])
                self.assertEqual(sha256(composition.canonical(row["statement_ast"])).hexdigest(), chunks.CHUNK_PINS[row["id"]][1])
                self.assertEqual(row["expected_free_names"], [])
                self.assertEqual(row["original_full_statement_ast_sha256"], chunks.FULL_TARGET_AST_SHA256)

    def test_source_recombination_has_exact_original_And_association(self):
        rebuilt = chunks.recombine_source_chunks(chunks.chunk_trees())
        self.assertEqual(rebuilt, composition.trees()["ground_instance"])
        self.assertEqual(sha256(composition.canonical(composition.encode(rebuilt))).hexdigest(), chunks.FULL_TARGET_AST_SHA256)
        receipt = chunks.source_partition_receipt()
        self.assertTrue(receipt["exact_original_AST_reconstructed"])
        self.assertFalse(receipt["original_HA_checked"])
        self.assertFalse(receipt["aggregate_native_composition_performed"])
        self.assertTrue(receipt["full_ground_instance_open"])

    def test_original_projection_paths_and_leaf_identifiers_are_exact(self):
        original = composition.trees()["ground_instance"]
        expected_ids = [identifier for identifier, _ in composition.trace_rows()] + ["conclusion"]
        trees = chunks.chunk_trees()
        for index, row in enumerate(chunks.chunk_contracts()):
            child = original
            bits = [int(bit) for bit in f"{index:04b}"]
            for bit in bits:
                child = child[bit + 1]
            self.assertEqual(child, trees[row["id"]])
            self.assertEqual(row["original_binary_path"], bits)
            self.assertEqual(row["projection_steps"], ["AndElimL" if bit == 0 else "AndElimR" for bit in bits])
            self.assertEqual(row["original_leaf_ids"], [expected_ids[position] for position in row["original_leaf_positions"]])
            for absolute, relative in zip(row["original_leaf_paths"], row["relative_leaf_paths"]):
                self.assertEqual(absolute, row["original_path"] + relative)

    def test_flat_collector_preserves_each_whole_chunk_and_dependency_order(self):
        for identifier, tree in chunks.chunk_trees().items():
            with self.subTest(chunk=identifier):
                layout = composition.flat_collector_layout(tree)
                count = len(layout.leaves)
                references = tuple(("hyp", count - 1 - i) for i in range(count))
                body = composition.materialize_collector(layout.body, references,
                            lambda left, right: ("and_intro", left, right))
                context = tuple(reversed(layout.leaves))
                def interpret(proof):
                    if proof[0] == "hyp":
                        return context[proof[1]]
                    return ("and", interpret(proof[1]), interpret(proof[2]))
                self.assertEqual(interpret(body), tree)
                self.assertIn(layout.leaf_occurrences, (6, 7))
                self.assertLessEqual(count, 7)

    def test_wrong_subtree_positions_and_missing_chunks_are_rejected(self):
        trees = chunks.chunk_trees()
        trees["P04-C00"], trees["P04-C01"] = trees["P04-C01"], trees["P04-C00"]
        with self.assertRaises(ValueError):
            chunks.recombine_source_chunks(trees)
        trees = chunks.chunk_trees()
        del trees["P04-C15"]
        with self.assertRaises(ValueError):
            chunks.recombine_source_chunks(trees)

    def test_source_contracts_have_no_external_references_or_parent_closure(self):
        for row in chunks.chunk_contracts():
            self.assertFalse(row["original_HA_checked"])
            self.assertFalse(row["closes_full_ground_instance"])
            self.assertFalse(row["closes_P04"])
            self.assertFalse(row["closes_IR079"])
            self.assertFalse(row["closes_IR080"])
            self.assertFalse(row["closes_IR081"])
            self.assertEqual(row["external_certificate_references"], [])
            self.assertIsNone(row["native_budget_fit"])
            self.assertEqual(len(row["existing_premise_allowlist"]), 15)

    def test_wrong_ID_and_caller_hash_fail_before_any_native_import_or_proof(self):
        with self.assertRaises(ValueError):
            chunks.prove_chunk("P04-C16", object(), expected_ast_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "caller's exact chunk AST pin"):
            chunks.prove_chunk("P04-C00", object(), expected_ast_sha256="0" * 64)
        self.assertNotIn("sqrt2_power_binary_dag", chunks.__dict__)
        self.assertNotIn("peano_lab", chunks.__dict__)

    def test_frozen_dependencies_and_full_target_pins_are_unchanged(self):
        self.assertEqual(chunks.verify_source_pins(), chunks.SOURCE_PINS)
        self.assertEqual(composition.FROZEN_TARGETS["ground_instance"]["statement_ast_sha256"], chunks.FULL_TARGET_AST_SHA256)
        self.assertEqual(composition.FROZEN_TARGETS["ground_instance"]["source_sha256"], chunks.FULL_TARGET_SOURCE_SHA256)


if __name__ == "__main__":
    unittest.main()
