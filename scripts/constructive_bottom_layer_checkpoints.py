"""Fresh verification of non-admitting, source-pinned bottom-layer checkpoints.

Hashes identify immutable inputs; only actual original-HA and compiled-Lean
checks supply proof evidence.  These records do not grant library membership.
The presentation layer may consume this module, but never the reverse.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "peano-lab/py") not in sys.path:
    sys.path.insert(0, str(ROOT / "peano-lab/py"))

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.proof_bundle import CheckedProofBundle, ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


SCHEMA = "peano-lab-non-admitting-bottom-layer-checkpoints-v1"
LEAN_BINARY = ROOT.parent / "peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify"
LEAN_BINARY_BYTES = 106_787_344
LEAN_BINARY_SHA256 = "22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
LEAN_TIMEOUT_SECONDS = 30


class CheckpointError(ValueError):
    """An exact source, actual proof check, or authority boundary failed."""


@dataclass(frozen=True, slots=True)
class ModulePin:
    module: str
    sha256: str

    @property
    def path(self) -> str:
        return f"peano-lab/py/peano_lab/library/{self.module}.py"

    @property
    def factory(self) -> str:
        return f"make_{self.module}_theorems"


@dataclass(frozen=True, slots=True)
class Checkpoint:
    slug: str
    modules: tuple[ModulePin, ...]
    artifact: str
    artifact_bytes: int
    artifact_sha256: str
    frontier_count: int
    principal_roots: tuple[str, ...]
    rfc: str
    frontier_specs_sha256: str


CHECKPOINTS: tuple[Checkpoint, ...] = (
    Checkpoint(
        "euler-units",
        (
            ModulePin("euler_units_residue_candidate", "dacb55219a5a5e9856d208a73e39b77156977d1de7d882044d4ed52907a7fdee"),
            ModulePin("euler_units_product_candidate", "dfbbc7dd69672992eb99a4eb99f64fb8273c28838aa6e1e749eb5b8a075ef8b9"),
            ModulePin("euler_units_candidate", "46e69f301a7215929958726a12ee151ad1972b771bcee57250a8fbbf18873458"),
        ),
        "research/arithmetic-library/artifacts/bottom-layer-euler-units-proof-bundle-v2.json",
        571_540, "1edfcb7021a0869c2493383c75dea367d757be0b77f36fc6ad3f5fd18ed38210", 32,
        ("euler_theorem_for_units", "euler_coprime_totient_power"),
        "research/arithmetic-library/euler-units-rfc-v1.md",
        "38ecc1c3c4a6045b7fb301526b09ede9b7927524265909bd59bdbbef1dfaf02e",
    ),
    Checkpoint(
        "prime-fields",
        (
            ModulePin("prime_field_arithmetic_candidate", "d4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90"),
            ModulePin("prime_field_tables_candidate", "2b24ad88c784eb558e36fba39bc181007986a9449194975d4f763723c0580400"),
            ModulePin("prime_field_finiteness_candidate", "a86bc0d8913ebfc1ea84c8dad691db5f90e21029c612ee87ad804657b1971b28"),
        ),
        "research/arithmetic-library/artifacts/bottom-layer-prime-fields-proof-bundle-v1.json",
        594_304, "688e7141106c19adec6fa52a0ae77af3d389b77df512622adc93bd3b0c7ba04e", 87,
        ("prime_field_of_prime_order_exists",),
        "research/arithmetic-library/prime-field-arithmetic-rfc-v1.md",
        "2d007091fb22e1d6c78896feea9363526196ecbcc075d46b0968b372ae39f50b",
    ),
    Checkpoint(
        "mobius-values",
        (
            ModulePin("mobius_value_candidate", "18cc5aef4d4710a09bd8f2eac063ae2ccf54049a68eaab33d6b9ce7df87af9e0"),
            ModulePin("mobius_prime_step_candidate", "f6fe75aa8e5c899baff761edea21dc82a3b76ea52ef165511d20f34a6d332af7"),
        ),
        "research/arithmetic-library/artifacts/bottom-layer-mobius-values-proof-bundle-v1.json",
        813_004, "041f1a3471002ff3cd5fc3da2a6cc751ad2f4a4458a497b3de2a26276fd314b8", 21,
        ("mobius_value_exists_unique", "mobius_fresh_prime_negates"),
        "research/arithmetic-library/mobius-divisor-sum-foundations-rfc-v1.md",
        "547c6e1da76f74f5329b3cc2e5707584bd2534fece4406d7b3493ef11aaa1291",
    ),
    Checkpoint(
        "signed-sums",
        (
            ModulePin("divisor_sum_table_candidate", "011980a3d5857c123e97359e048bb7f5b9e35685fb9d1357d1d543c4ff9d7692"),
            ModulePin("divisor_sum_algebra_candidate", "38cdcf7229cb43001f658bded3434d53b54efee3b28067f634e1f39af61a6c92"),
            ModulePin("divisor_sum_reindex_candidate", "e652ac90350d01c0ec6e4bbb7405950db316f35ff24fba3d019e1bc0c21d1ab4"),
        ),
        "research/arithmetic-library/artifacts/bottom-layer-signed-sums-proof-bundle-v1.json",
        855_381, "35bc01ab3f12cc09a5ed9aa3098225090dcc40ac241f9cbd669f99cef4737e57", 30,
        ("divisor_signed_table_reindex_exists", "divisor_signed_sum_permutation_invariant"),
        "research/arithmetic-library/mobius-divisor-sum-foundations-rfc-v1.md",
        "ddf5801b9e89a639401d1c95ee3745fb44d17e5c255a2dd11d89f38b9de5b37b",
    ),
)


@dataclass(frozen=True, slots=True)
class CheckpointEvidence:
    checkpoint: Checkpoint
    frontier: tuple[TheoremSpec, ...]
    bundle: ProofBundle
    target: Formula
    receipt: CheckedProofBundle
    plan: closure.BottomLayerPlan
    report: dict[str, Any]


def _registered(checkpoint: Checkpoint) -> None:
    if type(checkpoint) is not Checkpoint or checkpoint not in CHECKPOINTS:
        raise CheckpointError("only the literal registered mathematical checkpoints may be verified")


def _source_bytes(pin: ModulePin) -> bytes:
    path = ROOT / pin.path
    if (not path.is_file() or path.is_symlink()
            or not 0 < path.stat().st_size <= MAX_SOURCE_BYTES):
        raise CheckpointError(f"invalid bounded source: {pin.path}")
    with path.open("rb") as handle:
        source = handle.read(MAX_SOURCE_BYTES + 1)
    if len(source) > MAX_SOURCE_BYTES or sha256(source).hexdigest() != pin.sha256:
        raise CheckpointError(f"frozen mathematical source changed: {pin.path}")
    return source


def load_rows(checkpoint: Checkpoint) -> tuple[TheoremSpec, ...]:
    """Authenticate all authoring modules before executing their factories."""
    _registered(checkpoint)
    for pin in checkpoint.modules:
        _source_bytes(pin)
    rows = tuple(
        row for pin in checkpoint.modules
        for row in getattr(import_module(f"peano_lab.library.{pin.module}"), pin.factory)(TheoremSpec)
    )
    if (len(rows) != checkpoint.frontier_count or len({row.name for row in rows}) != len(rows)
            or not set(checkpoint.principal_roots) <= {row.name for row in rows}):
        raise CheckpointError("the actual frontier count, names, or principal roots changed")
    # Source bytes do not alone authenticate an already imported Python
    # factory. Bind the complete ordered authoring output independently too.
    if closure._specs_digest(rows) != checkpoint.frontier_specs_sha256:
        raise CheckpointError("the literal ordered theorem specifications changed")
    return rows


def _check_lean_binary() -> None:
    """Stream the existing binary rather than materializing another 102 MiB."""
    if (not LEAN_BINARY.is_file() or LEAN_BINARY.is_symlink()
            or LEAN_BINARY.stat().st_size != LEAN_BINARY_BYTES):
        raise CheckpointError("the exact independently compiled Lean checker is unavailable")
    digest = sha256()
    read = 0
    with LEAN_BINARY.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            read += len(chunk)
            if read > LEAN_BINARY_BYTES:
                raise CheckpointError("the compiled checker grew during its bounded read")
            digest.update(chunk)
    if read != LEAN_BINARY_BYTES or digest.hexdigest() != LEAN_BINARY_SHA256:
        raise CheckpointError("the independently compiled Lean checker bytes changed")


def _lean_check(checkpoint: Checkpoint, node_count: int, root: int, payload: bytes) -> None:
    if (type(payload) is not bytes or len(payload) != checkpoint.artifact_bytes
            or sha256(payload).hexdigest() != checkpoint.artifact_sha256):
        raise CheckpointError("independent Lean input is not the exact authenticated HA payload")
    _check_lean_binary()
    # Use the already authenticated bytes in a private exclusive snapshot.
    # Passing the original filename would let concurrent regeneration make
    # HA and Lean check different bundles with the same node-count receipt.
    with TemporaryDirectory(prefix="peano-bottom-lean-") as directory:
        artifact = Path(directory) / f"{checkpoint.slug}.proof-bundle.json"
        with artifact.open("xb") as output:
            output.write(payload)
        try:
            completed = subprocess.run(
                [str(LEAN_BINARY), str(artifact)], text=True, capture_output=True,
                timeout=LEAN_TIMEOUT_SECONDS, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise CheckpointError("independent Lean verification could not complete") from error
        expected = f"ACCEPT\t{artifact}\tnodes={node_count}\troot={root}\n"
        if completed.returncode != 0 or completed.stdout != expected or completed.stderr.strip():
            raise CheckpointError("the independent Lean checker did not accept the exact complete bundle")


def verify_checkpoint(checkpoint: Checkpoint, *, ordinary_roots: bool = False) -> CheckpointEvidence:
    """Recheck actual proofs; never consume a stored receipt as authority."""
    if type(ordinary_roots) is not bool:
        raise CheckpointError("ordinary_roots must be an explicit Boolean")
    rows = load_rows(checkpoint)
    payload = closure._read_pinned(ROOT / checkpoint.artifact,
                                   checkpoint.artifact_bytes, checkpoint.artifact_sha256)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    receipt = closure.check_bottom_layer_bundle(rows, bundle, target)
    plan = closure.bottom_layer_plan(rows)
    _lean_check(checkpoint, receipt.node_count, bundle.root, payload)
    positions = {row.name: row.node_id for row in plan.rows}
    by_name = {row.name: row for row in rows}
    roots = []
    for name in checkpoint.principal_roots:
        record: dict[str, Any] = {
            "name": name, "node_id": positions[name],
            "statement_sha256": sha256(by_name[name].statement.encode()).hexdigest(),
            "complete_ordinary_ha_checked": ordinary_roots,
        }
        if ordinary_roots:
            checked = closure.replay_bottom_layer_theorem(rows, name, bundle, target)
            # Deliberately check the returned certificate once more here:
            # neither a compiler receipt nor this wrapper supplies authority.
            exact = _closed_formula(by_name[name].statement)
            if (checked.spec != by_name[name] or checked.formula != exact
                    or not check((), checked.certificate, exact)):
                raise CheckpointError("the returned empty-context certificate failed original HA")
            record["ordinary_certificate_nodes"] = checked.proof_nodes
        roots.append(record)
    report = {
        "slug": checkpoint.slug,
        "membership": "local_non_admitting_checkpoint",
        "admitted_to_alpha": False, "alpha_checked_use": False, "stable_member": False,
        "frontier_count": len(rows),
        "ordered_frontier_names_sha256": sha256("\n".join(row.name for row in rows).encode()).hexdigest(),
        "frontier_specs_sha256": plan.frontier_specs_sha256,
        "frontier_dependency_edges": sum(len(row.dependencies) for row in rows),
        "frontier_tactic_commands": sum(len(row.script) for row in rows),
        "sources": [{"path": pin.path, "sha256": pin.sha256, "factory": pin.factory}
                    for pin in checkpoint.modules],
        "rfc": checkpoint.rfc,
        "bundle": {
            "path": checkpoint.artifact, "bytes": checkpoint.artifact_bytes,
            "sha256": checkpoint.artifact_sha256,
            "nodes_including_packaging_root": receipt.node_count,
            "inherited_theorems": len(plan.rows) - len(rows),
            "dependency_edges_including_packaging": receipt.dependency_edges,
            "body_proof_nodes": receipt.total_body_nodes,
            "packaging_root_id": bundle.root,
            "original_ha_checked": True, "independent_lean_checked": True,
        },
        "all_maximal_frontier_roots": list(plan.root_names),
        "principal_roots": roots,
    }
    return CheckpointEvidence(checkpoint, rows, bundle, target, receipt, plan, report)


def verify_all(*, ordinary_roots: bool = True) -> dict[str, Any]:
    """Return deterministic evidence after fresh checks of every checkpoint."""
    import gc

    reports = []
    for checkpoint in CHECKPOINTS:
        evidence = verify_checkpoint(checkpoint, ordinary_roots=ordinary_roots)
        reports.append(evidence.report)
        del evidence
        gc.collect()
    return {
        "schema": SCHEMA,
        "checkpoint_revision": 2,
        "superseded_audit": "research/arithmetic-library/artifacts/bottom-layer-checkpoints-v1.json",
        "superseded_euler_sources": "research/arithmetic-library/artifacts/bottom-layer-euler-units-v1-sources/manifest.json",
        "revision_reason": "reuse two exact parent Euler lemmas instead of counting duplicate statements",
        "proof_authority": "fresh_original_ha_and_independent_compiled_lean_checks",
        "stored_receipt_is_proof_authority": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "published": False,
        "parent": {
            "version": "v30", "catalog": closure.PARENT_CATALOG,
            "catalog_sha256": closure.PARENT_CATALOG_SHA256,
            "alpha_checked_use_count": closure.PARENT_COUNT, "stable_count": 432,
        },
        "independent_checker": {
            "binary_sha256": LEAN_BINARY_SHA256, "binary_bytes": LEAN_BINARY_BYTES,
            "rebuilt_in_this_tranche": False,
        },
        "new_theorems": sum(row["frontier_count"] for row in reports),
        "checkpoints": reports,
    }


__all__ = (
    "CHECKPOINTS", "Checkpoint", "CheckpointError", "CheckpointEvidence", "ModulePin",
    "LEAN_BINARY", "LEAN_BINARY_BYTES", "LEAN_BINARY_SHA256", "ROOT", "SCHEMA",
    "load_rows", "verify_checkpoint", "verify_all",
)
