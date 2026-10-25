"""Focused manifest boundaries and scheduled native certificate checks.

PureLibraryBoundaryTests performs no parser/checker work. NativeLemmaLibraryTests
must run only in the root-coordinated native test window. All certificates are
small constructed objects; no proof search, imported theorem replay or adviser
is involved. Fixtures live only in temporary directories.
"""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
SOURCE = APP / "native-v7"
if not SOURCE.is_dir():
    SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py"
sys.path[:0] = [str(APP), str(SOURCE)]
from peano_lab.kernel import formulas as f, proofs as p, terms as t
with patch("peano_lab.kernel.checker.check", side_effect=AssertionError("No import-time native checks")):
    import certificate_codec as codec
    import lemma_library as library


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def manifest(entries):
    return {"schema": library.SCHEMA, "version": 1, "capability_profile": library.CAPABILITY_PROFILE,
            "kernel_identity_sha256": library.KERNEL_IDENTITY_SHA256, "entries": entries}


class FixtureMixin:
    def setUp(self):
        super().setUp()
        temporary = tempfile.TemporaryDirectory(prefix="hydra-certificate-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()

    def write_manifest(self, value):
        raw = dump(value)
        (self.directory / "manifest.json").write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()


class PureLibraryBoundaryTests(FixtureMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        for attribute in ("check", "check_classical"):
            guard = patch("peano_lab.kernel.checker." + attribute,
                          side_effect=AssertionError("Pure boundary test cannot check proofs"))
            guard.start(); self.addCleanup(guard.stop)
        guard = patch("peano_lab.kernel.formulas.parse_formula_with_names",
                      side_effect=AssertionError("Pure boundary test cannot parse native formulas"))
        guard.start(); self.addCleanup(guard.stop)

    def test_manifest_hash_and_envelope_fail_before_native_work(self):
        for value in ({}, {**manifest([]), "script": "refl"}, {**manifest([]), "version": True},
                      {**manifest([]), "capability_profile": "old-library"},
                      {**manifest([]), "kernel_identity_sha256": "0" * 64}, manifest([])):
            pin = self.write_manifest(value)
            with self.assertRaises(library.LemmaLibraryError):
                library.load_library(self.directory, expected_manifest_sha256=pin)
        self.write_manifest(manifest([]))
        with self.assertRaisesRegex(library.LemmaLibraryError, "hash mismatch"):
            library.load_library(self.directory, expected_manifest_sha256="0" * 64)

    def test_duplicate_keys_and_oversize_manifest_are_rejected(self):
        raw = b'{"entries":[],"entries":[]}'
        (self.directory / "manifest.json").write_bytes(raw)
        with self.assertRaises(library.LemmaLibraryError):
            library.load_library(self.directory, expected_manifest_sha256=hashlib.sha256(raw).hexdigest())
        pin = self.write_manifest(manifest([]))
        with self.assertRaises(library.LemmaLibraryError):
            library.load_library(self.directory, expected_manifest_sha256=pin,
                                 limits=library.LibraryLimits(max_manifest_bytes=10))

    def test_path_syntax_and_symlinks_do_not_escape_the_open_root(self):
        for path in ("../outside.json", "/outside.json", "a/../outside.json", "a//b.json",
                     "./b.json", "a\\b.json", "a/./b.json", "a/", ""):
            with self.subTest(path=path), self.assertRaises(library.LemmaLibraryError):
                library._relative_path(path)
        outside = self.directory / "outside.json"; outside.write_bytes(b"safe")
        (self.directory / "link.json").symlink_to(outside)
        (self.directory / "linkdir").symlink_to(self.directory, target_is_directory=True)
        fd = library._open_root(self.directory)
        try:
            for name in ("link.json", "linkdir/outside.json"):
                with self.assertRaises(OSError):
                    library._read_at(fd, name, 100)
        finally:
            library.os.close(fd)
        with self.assertRaises(OSError):
            library._open_root(self.directory / "linkdir")

    def test_manifest_symlink_and_nonregular_file_are_rejected(self):
        source = self.directory / "other.json"; source.write_bytes(dump(manifest([])))
        (self.directory / "manifest.json").symlink_to(source)
        with self.assertRaises(library.LemmaLibraryError):
            library.load_library(self.directory, expected_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        (self.directory / "manifest.json").unlink()
        (self.directory / "manifest.json").mkdir()
        with self.assertRaises(library.LemmaLibraryError):
            library.load_library(self.directory, expected_manifest_sha256="0" * 64)

    def test_fifo_is_rejected_without_waiting_for_a_writer(self):
        library.os.mkfifo(self.directory / "pipe.json")
        fd = library._open_root(self.directory)
        try:
            with self.assertRaises(library.LemmaLibraryError):
                library._read_at(fd, "pipe.json", 100)
        finally:
            library.os.close(fd)

    def test_limits_and_early_cancellation(self):
        for kwargs in ({"max_entries": 129}, {"max_dependency_depth": 9},
                       {"max_total_bytes": True}, {"max_dependencies": 0}):
            with self.assertRaises(library.LemmaLibraryError):
                library.LibraryLimits(**kwargs)
        with self.assertRaisesRegex(library.LemmaLibraryError, "cancelled"):
            library.load_library(self.directory, expected_manifest_sha256="0" * 64, should_stop=lambda: True)
        with self.assertRaises(library.LemmaLibraryError):
            library.LemmaLibrary({}, {}, "0" * 64, None, None, library.DEFAULT_LIMITS, None, {})


class NativeLemmaLibraryTests(FixtureMixin, unittest.TestCase):
    """Root schedules this class; actual original-kernel judgments occur here."""

    def bundle(self, items=None):
        if items is None:
            items = [("zero_identity", "0 = 0", p.EqRefl(t.Zero()), (), "reflexivity")]
        entries = []
        for name, statement, certificate, dependencies, family in items:
            formula = f.parse_formula_with_names(statement)[0]
            payload = codec.encode_certificate(formula, certificate)
            relative = name + ".json"
            (self.directory / relative).write_bytes(payload)
            entries.append({"name": name, "statement": statement,
                "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
                "family": family, "dependencies": list(dependencies),
                "certificate": {"path": relative, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}})
        document = manifest(entries)
        return document, self.write_manifest(document)

    def load(self, pin, **kwargs):
        return library.load_library(self.directory, expected_manifest_sha256=pin,
                                    **{"target": "0 = 1", **kwargs})

    def test_checks_all_entries_once_and_reports_preload_accounting(self):
        items = [("zero_identity", "0 = 0", p.EqRefl(t.Zero()), (), "reflexivity"),
                 ("add_zero", "forall n. n + 0 = n", p.Axiom("PA3"), ("zero_identity",), "additive_zero")]
        document, pin = self.bundle(items)
        original_check = library.kernel.check
        with patch.object(library.kernel, "check", wraps=original_check) as observed:
            loaded = self.load(pin)
            self.assertEqual(observed.call_count, 2)
            first = loaded.resolve("zero_identity")
            self.assertIs(library.resolve_lemma(loaded, "zero_identity"), first)
            self.assertEqual(observed.call_count, 2)
        self.assertEqual(loaded.verification["certificates_checked"], 2)
        self.assertEqual(loaded.verification["native_kernel_checks"], 2)
        self.assertEqual(loaded.verification["certificate_bytes_read"], sum(e["certificate"]["bytes"] for e in document["entries"]))
        self.assertGreaterEqual(loaded.verification["native_kernel_check_seconds"], 0)
        self.assertTrue(loaded.verification["all_entries_checked_before_return"])
        self.assertEqual(first.proof_cost["distinct_objects"], 1)
        self.assertEqual(loaded.manifest_sha256, pin)

    def test_rejects_false_proofs_and_classical_certificates(self):
        self.bundle([("false_equality", "0 = 1", p.EqRefl(t.Zero()), (), "negative")])
        pin = hashlib.sha256((self.directory / "manifest.json").read_bytes()).hexdigest()
        with self.assertRaisesRegex(library.LemmaLibraryError, "kernel rejected"):
            self.load(pin)
        statement = "((0 = 0 -> bot) -> bot) -> 0 = 0"
        q = f.Eq(t.Zero(), t.Zero())
        _, pin = self.bundle([("classical_node", statement, p.DNE(q), (), "classical")])
        with self.assertRaisesRegex(library.LemmaLibraryError, "kernel rejected"):
            self.load(pin)

    def test_statement_and_payload_hashes_are_both_required(self):
        document, pin = self.bundle()
        path = self.directory / document["entries"][0]["certificate"]["path"]
        path.write_bytes(path.read_bytes().replace(b'"EqRefl"', b'"HypXYZ"'))
        with self.assertRaises(library.LemmaLibraryError):
            self.load(pin)
        document, _ = self.bundle()
        document["entries"][0]["statement_sha256"] = "f" * 64
        with self.assertRaisesRegex(library.LemmaLibraryError, "Statement hash"):
            self.load(self.write_manifest(document))

    def test_certificate_root_must_equal_manifest_original_statement(self):
        document, _ = self.bundle()
        statement = "1 = 1"
        document["entries"][0]["statement"] = statement
        document["entries"][0]["statement_sha256"] = hashlib.sha256(statement.encode()).hexdigest()
        with self.assertRaisesRegex(library.LemmaLibraryError, "exact manifest statement"):
            self.load(self.write_manifest(document))

    def test_free_names_and_unbound_explicit_indices_are_rejected(self):
        for statement in ("a = a", "#0 = #0", "forall n. #1 = #1"):
            with self.subTest(statement=statement):
                _, pin = self.bundle([("open_statement", statement, p.EqRefl(t.Var(0)), (), "invalid")])
                with self.assertRaises(library.LemmaLibraryError):
                    self.load(pin)

    def test_alpha_target_binding_excludes_exact_target_and_is_immutable(self):
        proof = p.ForallIntro(p.EqRefl(t.Var(0)))
        _, pin = self.bundle([("universal_identity", "forall original. original = original", proof, (), "reflexivity")])
        loaded = self.load(pin, target="forall renamed. renamed = renamed")
        self.assertEqual(loaded.available_names, ())
        self.assertTrue(loaded.validate_target(f.parse_formula_with_names("forall x. x = x")[0]))
        self.assertEqual(loaded.target_sha256, library.statement_identity("forall y. y = y"))
        self.assertTrue(loaded.capability_label.startswith(library.CAPABILITY_PROFILE + "-"))
        with self.assertRaises(library.ExcludedLemmaError):
            loaded.resolve("universal_identity")
        with self.assertRaises(library.LemmaLibraryError):
            loaded.validate_target(f.Eq(t.Zero(), t.Zero()))
        with self.assertRaises(FrozenInstanceError):
            loaded.target_sha256 = "f" * 64

    def test_reserved_ast_and_dependency_exclusions_propagate(self):
        proof = p.ForallIntro(p.EqRefl(t.Var(0)))
        _, pin = self.bundle([
            ("universal_identity", "forall x. x = x", proof, (), "reflexivity"),
            ("zero_identity", "0 = 0", p.EqRefl(t.Zero()), ("universal_identity",), "closed_reflexivity")])
        exclusions = library.make_exclusions(statements=["forall another. another = another"])
        loaded = self.load(pin, exclusions=exclusions)
        self.assertEqual(loaded.available_names, ())
        self.assertIn("excluded_declared_dependency", loaded.excluded["zero_identity"])
        with self.assertRaises(library.ExcludedLemmaError):
            loaded.resolve("zero_identity")

    def test_wrapped_target_formula_and_family_and_hook_exclusions(self):
        variable = t.Var(0); identity = f.Forall(f.Eq(variable, variable))
        proof = p.ForallIntro(p.EqRefl(variable))
        _, pin = self.bundle([("wrapped_identity", "(forall x. x = x) /\\ (0 = 0)",
                              p.AndIntro(proof, p.EqRefl(t.Zero())), (), "wrapped")])
        loaded = self.load(pin, target="forall n. n = n")
        self.assertEqual(loaded.names, ())
        _, pin = self.bundle()
        self.assertEqual(self.load(pin, exclusions=library.make_exclusions(families=["reflexivity"])).names, ())
        self.assertEqual(self.load(pin, exclusions=library.make_exclusions(names=["zero_identity"])).names, ())
        self.assertEqual(self.load(pin, exclusion_hook=lambda metadata, formula: True).names, ())
        with self.assertRaises(library.LemmaLibraryError):
            self.load(pin, exclusion_hook=lambda metadata, formula: "yes")

    def test_dependency_order_cycles_duplicates_and_depth_are_rejected(self):
        for dependencies in (["missing"], ["zero_identity"], ["zero_identity", "zero_identity"]):
            document, _ = self.bundle()
            document["entries"][0]["dependencies"] = dependencies
            with self.assertRaises(library.LemmaLibraryError):
                self.load(self.write_manifest(document))
        rows = [("lemma_" + str(i), "0 = 0", p.EqRefl(t.Zero()),
                 () if i == 0 else ("lemma_" + str(i - 1),), "chain") for i in range(9)]
        _, pin = self.bundle(rows)
        with self.assertRaisesRegex(library.LemmaLibraryError, "dependency depth"):
            self.load(pin)

    def test_catalogue_bytes_descriptor_size_and_unsafe_paths(self):
        document, pin = self.bundle()
        with self.assertRaises(library.LemmaLibraryError):
            self.load(pin, limits=library.LibraryLimits(max_total_bytes=len((self.directory / "manifest.json").read_bytes())))
        for field, value in (("bytes", True), ("bytes", 512 * 1024 + 1), ("path", "../bad.json")):
            document, _ = self.bundle(); document["entries"][0]["certificate"][field] = value
            with self.assertRaises(library.LemmaLibraryError):
                self.load(self.write_manifest(document))

    def test_retrieval_is_bounded_deterministic_and_never_exposes_certificates(self):
        items = [("seed_" + letter, "0 = 0", p.EqRefl(t.Zero()), (), "reflexivity") for letter in "abcdef"]
        _, pin = self.bundle(items)
        loaded = self.load(pin, exclusions=library.make_exclusions(names=["seed_a"]))
        goal = f.Eq(t.Zero(), t.Succ(t.Zero()))
        results = loaded.retrieve(goal)
        self.assertEqual(len(results), 4)
        self.assertEqual(results, loaded.retrieve(goal))
        self.assertNotIn("seed_a", [r["name"] for r in results])
        self.assertTrue(all("certificate" not in r and "script" not in r for r in results))
        for value in (0, 5, True):
            with self.assertRaises(library.LemmaLibraryError):
                loaded.retrieve(goal, limit=value)
        with self.assertRaises(library.LemmaLibraryError):
            loaded.resolve("unknown")

    def test_no_original_target_means_validation_only_and_labels_bind_target(self):
        _, pin = self.bundle()
        unbound = self.load(pin, target=None)
        self.assertIsNone(unbound.capability_label)
        self.assertEqual(unbound.names, ())
        with self.assertRaises(library.LemmaLibraryError):
            unbound.resolve("zero_identity")
        with self.assertRaises(library.LemmaLibraryError):
            unbound.retrieve(f.Bot())
        first, second = self.load(pin, target="0 = 1"), self.load(pin, target="1 = 0")
        self.assertNotEqual(first.capability_label, second.capability_label)
        with self.assertRaises(library.LemmaLibraryError):
            library.resolve_lemma(object(), "zero_identity")


if __name__ == "__main__":
    unittest.main()
