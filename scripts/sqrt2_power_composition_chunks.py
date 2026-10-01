"""Sixteen exact source-frozen depth-four subtrees of the P04 ground trace.

The full 107-leaf target remains open. Each native producer returns one complete
standalone subconjunction with its own ordinary proof DAG and canonical replay.
No external certificate references, new axioms, larger limits, aggregate proof,
or variable-degree conclusion are introduced. All native imports are lazy.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-composition-chunks-v1"
FULL_TARGET_AST_SHA256 = "67e5493f462533be7b0278c71e26557a606ae3499d32b3fee2ea51e7b4b1ec83"
FULL_TARGET_SOURCE_SHA256 = "17b1baaecceaa5ebfe5d70f23519e6f71c90aec601ead3c03eb4b26472415117"
SOURCE_PINS = {
    "scripts/sqrt2_power_formal_composition.py": "dd234c4db5ae853ce4339b510536cb34b3e1fba231dc4edd87ed58f8b1d846c7",
    "scripts/sqrt2_power_binary_dag.py": "517535807fe06a317fae48c5fc5f47db944b0c32904fb8d02a0a1b102af12227",
}
CHUNK_IDS = tuple(f"P04-C{i:02d}" for i in range(16))
# Each pair pins (expanded source, ordinary lowercase HA AST), independently of
# any proposed proof. Paths are the four binary digits of the chunk index.
CHUNK_PINS = {
    "P04-C00": ("4b74bcb7137adcf728f967ef637559bb528320f58cf6a26c487a9f4ae1d95ecc", "e8fafbb03e9bf8c595485e474d9a258de8b542defdfbb20a3e3aa745dbc68cbb"),
    "P04-C01": ("b2dfface2df8d7c5028f132fc63b30649cc5587138e3c44de790d4711ccf9956", "54843ab8cc85b0a20d691880db62805ab8fa519d9c6ca29dc906df1605e1274a"),
    "P04-C02": ("9bd611e871b3e5a1664b7c2670c650c672e42abb6f02765b046b3ccd1ccb9618", "7e47828bf09996d16a8b6b4df1f9e4294d21df0390eaed4f546bc186ee88a535"),
    "P04-C03": ("70167f403d5e7d921d38dc4628bbe520200890b145e04c8af82d712d60cbbb1c", "c24c821191d3d2a213cbcde4fb0a4a1f98276585434153becb4f9f83844abcd0"),
    "P04-C04": ("08580307055094b5004b63d059d38a74cdef6713d6d404b0fd2ab89bd74f130e", "5a67781f28973fb59401b56a8a3f79fda8ee3aef85c4e6d982b25819cff0263d"),
    "P04-C05": ("d13119ea043aa18b6be684d56e6437ae6dcc295e546afbb059db4122f63b73a1", "d726769334d24cee7d918bed620ab71b89fabcd9e0a14bcd18f47d9399d8595e"),
    "P04-C06": ("785e6736f812c9e2ec3465c034ac28029143620e4e495f300792efbbe2de5d29", "683e5eb3508f136eb0685dbe74f7f00ca7cc9ae3b8ba23f3361a5c7c6c5f5010"),
    "P04-C07": ("4bc29c7e179cbb104ba2743be3fa07a5c026425490c75b3a008a2ba0bc38ae91", "e8276b96a062a8ba544cf2f5f1f411c49ffdd6952a615d5f06d4c323fd48cbf4"),
    "P04-C08": ("ffa0f48dc55e7e395aa3aeaef31d58f4a9bb078f923d3750f01d2f4aba62a678", "4d5502076dff00227dc0f3c6c192d47ac1ca53b1043320c682270059c00803ef"),
    "P04-C09": ("c7468b7f931d674e9436cc5e35d1b7a70ecd399f8a94c8572bf74049f10c7ca5", "d7b8e60537999896b235e6d8e893aec799c0cfde827343add5ea0dfb53353611"),
    "P04-C10": ("00f8341f718279e8d15ff143f6355659723cfcba83764b57b7ecf268ac1135df", "03b53e1693a14342d8e17250af6d1138635633cfa8f4a93403323b2d04f90610"),
    "P04-C11": ("163389e1f1aeb31189d89acf7aa51aa6216ce814d1e1de14f0f295b33398324f", "8ae142a1eb8450325a6e51decbb05c458041dfdb5634d25386cbb702825cde05"),
    "P04-C12": ("8e81e1bda47b24437088654339eb50ba373049ad7ba3818425ea819043645af4", "4a60e8f9088cac962514a8c81c382ce8c690d2c0342b7ef74876dd40d8a15002"),
    "P04-C13": ("f1e1a236654671bee33fdfade2cd433e169db0db60235d052a7b4f49568eb81f", "12ac82dd785aa14b0915924bd287313a7456c0f7ca32358d5370a5cffc74dbef"),
    "P04-C14": ("60df315c2014e46c4d3bc40c779367e90c2b5a9b2821fefee26a1cece22bb72b", "56d3fb73f04aba5883d37caccab1cb0f98b4706ba7b34a9790c8d0640fdeb559"),
    "P04-C15": ("5142f667d2f7b7ab4c1838b303248d1e8d489791ddbcb0327a52481ac373d053", "56aface1bc278ad6cd1c33768cf5e8a95964b96ee802993c3793ca84b8b4293a"),
}


def verify_source_pins():
    actual = {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_PINS}
    if actual != SOURCE_PINS:
        raise ValueError("a source-frozen composition/chunk dependency changed")
    return actual


def _composition():
    verify_source_pins()
    import sqrt2_power_formal_composition as composition
    return composition


def _leaves(tree, path=""):
    if len(tree) == 3 and tree[0] == "and":
        return _leaves(tree[1], path + "L") + _leaves(tree[2], path + "R")
    if len(tree) != 3 or tree[0] != "eq":
        raise ValueError("the original ground trace is not an Eq/And tree")
    return [(tree, path)]


def _source_records():
    composition = _composition()
    original = composition.trees()["ground_instance"]
    if (sha256(composition.canonical(composition.encode(original))).hexdigest() != FULL_TARGET_AST_SHA256
            or sha256(composition.source(original).encode()).hexdigest() != FULL_TARGET_SOURCE_SHA256):
        raise ValueError("the original full ground target changed")
    original_leaves = _leaves(original)
    identifiers = [identifier for identifier, _ in composition.trace_rows()] + ["conclusion"]
    if len(original_leaves) != 107 or len(identifiers) != 107:
        raise ValueError("the original 106 trace rows plus conclusion changed")
    records, cursor = [], 0
    for i, identifier in enumerate(CHUNK_IDS):
        bits = tuple(int(bit) for bit in f"{i:04b}")
        path = "".join("LR"[bit] for bit in bits)
        child = original
        for bit in bits:
            if child[0] != "and":
                raise ValueError("the original depth-four partition changed")
            child = child[bit + 1]
        leaves = _leaves(child, path)
        positions = list(range(cursor, cursor + len(leaves)))
        if len(leaves) not in (6, 7) or leaves != original_leaves[cursor:cursor + len(leaves)]:
            raise ValueError("chunk leaves do not occupy the exact original positions")
        text = composition.source(child)
        encoded = composition.encode(child)
        pins = (sha256(text.encode()).hexdigest(), sha256(composition.canonical(encoded)).hexdigest())
        if pins != CHUNK_PINS[identifier]:
            raise ValueError("an exact source-frozen chunk target changed: " + identifier)
        records.append(dict(id=identifier, tree=child, source=text,
            source_sha256=pins[0], statement_ast=encoded, statement_ast_sha256=pins[1],
            original_path=path, original_binary_path=list(bits),
            projection_steps=["AndElimL" if bit == 0 else "AndElimR" for bit in bits],
            original_leaf_positions=positions, original_leaf_ids=[identifiers[j] for j in positions],
            original_leaf_paths=[leaf_path for _, leaf_path in leaves],
            relative_leaf_paths=[leaf_path[4:] for _, leaf_path in leaves],
            leaf_occurrences=len(leaves)))
        cursor += len(leaves)
    if cursor != 107:
        raise ValueError("chunk coverage omits or duplicates original leaf positions")
    return records


def chunk_trees():
    return {row["id"]: row["tree"] for row in _source_records()}


def recombine_source_chunks(chunks):
    """Exact source reconstruction only: NOT a composition of HA certificates."""
    if set(chunks) != set(CHUNK_IDS):
        raise ValueError("source recombination requires exactly the sixteen fixed chunk IDs")
    composition = _composition()
    for identifier in CHUNK_IDS:
        digest = sha256(composition.canonical(composition.encode(chunks[identifier]))).hexdigest()
        if digest != CHUNK_PINS[identifier][1]:
            raise ValueError("wrong subtree at a fixed original chunk position")
    rebuilt = composition.balanced("and", [chunks[identifier] for identifier in CHUNK_IDS])
    if (rebuilt != composition.trees()["ground_instance"]
            or sha256(composition.canonical(composition.encode(rebuilt))).hexdigest() != FULL_TARGET_AST_SHA256):
        raise ValueError("chunk source reconstruction is not the exact original full AST")
    return rebuilt


def chunk_contracts():
    rows = _source_records()
    composition = _composition()
    allowlist = composition.premise_allowlist()
    result = []
    for row in rows:
        contract = {key: value for key, value in row.items() if key != "tree"}
        contract.update(schema=SCHEMA, pilot="P04", parent="P04-degree7-ground-instance",
            IR_parent="IR079", original_full_statement_ast_sha256=FULL_TARGET_AST_SHA256,
            original_full_source_sha256=FULL_TARGET_SOURCE_SHA256,
            source_dependencies=dict(SOURCE_PINS), existing_premise_allowlist=allowlist,
            expected_free_names=[], coverage="complete_exact_subconjunction_child",
            authority="frozen_source_not_a_certificate", original_HA_checked=False,
            external_certificate_references=[], native_budget_fit=None,
            closes_full_ground_instance=False, closes_P04=False, closes_IR079=False,
            closes_IR080=False, closes_IR081=False, variable_degree_claim=False)
        result.append(contract)
    return result


def chunk_contract(identifier):
    if identifier not in CHUNK_IDS:
        raise ValueError("unknown source-frozen P04 chunk")
    return next(row for row in chunk_contracts() if row["id"] == identifier)


def source_partition_receipt():
    records = _source_records()
    recombine_source_chunks({row["id"]: row["tree"] for row in records})
    return dict(authority="source_only_partition_not_an_aggregate_certificate",
        exact_original_AST_reconstructed=True, original_HA_checked=False,
        original_full_statement_ast_sha256=FULL_TARGET_AST_SHA256,
        chunks=len(records), original_trace_rows=106, original_leaf_occurrences=107,
        exact_coverage_positions=[position for row in records for position in row["original_leaf_positions"]],
        aggregate_native_composition_performed=False, full_ground_instance_open=True,
        closes_IR079=False, closes_IR080=False, closes_IR081=False)


def verify_sources_with_original_parser():
    """Lazy parser/AST agreement only; no proof or theorem generation."""
    from sqrt2_power_native import closed_formula
    from peano_lab.library.proof_bundle import encode_formula
    rows = chunk_contracts()
    for row in rows:
        if encode_formula(closed_formula(row["source"])) != row["statement_ast"]:
            raise ValueError("the original parser disagrees with a frozen chunk AST")
    return [{key: row[key] for key in ("id", "statement_ast_sha256", "source_sha256")} for row in rows]


@dataclass(frozen=True)
class CompositionChunkCertificate:
    formula: object
    bundle_certificate: object
    manifest: dict


def prove_chunk(identifier, basis, *, expected_ast_sha256, limits=None):
    """Root worker only: one whole exact chunk, independently replayed.

    A fresh builder includes every reachable law and arithmetic body in this
    chunk's payload. No sibling receipt is accepted as a premise. Original
    BinaryDAGLimits are retained; any cap failure leaves this chunk open. This
    entry point neither subdivides a chunk automatically nor proves the parent.
    """
    row = chunk_contract(identifier)
    if expected_ast_sha256 != row["statement_ast_sha256"]:
        raise ValueError("the caller's exact chunk AST pin does not match")
    composition = _composition()
    composition._validated_basis(basis)
    from sqrt2_power_native import closed_formula
    from peano_lab.kernel.formulas import And, Eq
    from peano_lab.kernel.proofs import AndIntro, EqRefl
    from peano_lab.library.proof_bundle import encode_formula
    from sqrt2_power_binary_dag import BinaryDAGLimits, _Builder, _basis, _values
    if limits is None:
        limits = BinaryDAGLimits()
    if type(limits) is not BinaryDAGLimits:
        raise ValueError("expected the unchanged bounded binary DAG limits")
    target = closed_formula(row["source"])
    if encode_formula(target) != row["statement_ast"]:
        raise ValueError("the original parser changed the exact chunk AST")
    layout = composition.flat_collector_layout(chunk_trees()[identifier])
    native_leaves, indexes = [], {}
    occurrences = 0
    def collect(formula):
        nonlocal occurrences
        if type(formula) is And:
            collect(formula.left)
            collect(formula.right)
            return
        if type(formula) is not Eq:
            raise ValueError("unexpected leaf in an exact composition chunk")
        occurrences += 1
        if formula not in indexes:
            indexes[formula] = len(native_leaves)
            native_leaves.append(formula)
    collect(target)
    if (occurrences != row["leaf_occurrences"] or occurrences != layout.leaf_occurrences
            or len(native_leaves) != len(layout.leaves)
            or any(encode_formula(actual) != composition.encode(expected)
                   for actual, expected in zip(native_leaves, layout.leaves))):
        raise ValueError("source/native chunk dependency or occurrence mapping changed")
    builder = _Builder(_basis(basis), limits)
    leaf_nodes = []
    for formula in native_leaves:
        if formula.left == formula.right:
            node = builder.emit(formula, (), lambda _, formula=formula: EqRefl(formula.left))
        else:
            node = builder.equality(formula, _values(formula, limits))
        leaf_nodes.append(node)
    root = builder.emit(target, tuple(leaf_nodes), lambda ref:
        composition.materialize_collector(layout.body, tuple(ref(node) for node in leaf_nodes), AndIntro))
    checked = builder.finish(root, target)
    if checked.target_ast_sha256 != row["statement_ast_sha256"]:
        raise ValueError("canonical replay changed the exact chunk target")
    verify_source_pins()
    return CompositionChunkCertificate(target, checked, dict(
        id=identifier, schema=SCHEMA, statement_ast_sha256=row["statement_ast_sha256"],
        source_sha256=row["source_sha256"], original_path=row["original_path"],
        projection_steps=row["projection_steps"], original_leaf_positions=row["original_leaf_positions"],
        original_leaf_ids=row["original_leaf_ids"],
        original_full_statement_ast_sha256=FULL_TARGET_AST_SHA256,
        original_HA_checked=True, canonical_bytes_replayed=True, empty_context=True,
        coverage="complete_exact_subconjunction_child", closes_exact_chunk=True,
        checked_leaf_occurrences=occurrences, unique_execution_dependencies=len(leaf_nodes),
        final_conjunction_collector_nodes=1, external_certificate_references=[],
        requested_existing_laws=list(checked.basis_names),
        closes_full_ground_instance=False, closes_P04=False, closes_IR079=False,
        closes_IR080=False, closes_IR081=False, variable_degree_claim=False,
        aggregate_native_composition_performed=False))


def summary():
    rows = chunk_contracts()
    return dict(schema=SCHEMA, authority="frozen_source_not_a_certificate",
        original_HA_checked=False, native_runs_performed=False,
        source_partition=source_partition_receipt(),
        targets=[{key: row[key] for key in (
            "id", "source_sha256", "statement_ast_sha256", "original_path",
            "original_leaf_positions", "original_leaf_ids", "leaf_occurrences", "coverage")}
            for row in rows])


if __name__ == "__main__":
    print(json.dumps(summary(), sort_keys=True, indent=2))
