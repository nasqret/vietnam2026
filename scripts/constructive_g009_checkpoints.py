"""Fail-closed final G009 bundle, compiled-Lean, and ordinary-root gates.

The registered artifact is data, never a stored successful verification.
Proof-data authoring lives in a separate command. A final verifier accepts
only all ninety exact owned rows; neither a prefix nor a stored audit is an
input authority. Current Alpha remains 3796 and Stable remains 432.
"""

from __future__ import annotations

from dataclasses import dataclass
import gc
from hashlib import sha256
from pathlib import Path
import resource
import sys

import constructive_g009_support as support
import constructive_bottom_layer_checkpoints as independent
from peano_lab.kernel.checker import check
from peano_lab.library.proof_bundle import decode_proof_bundle
from peano_lab.library.theorems import _closed_formula


PRINCIPAL_ROOTS = (
    'signed_support_reindex_sum_equal',
    'signed_cartesian_product_sums_exists',
    'coprime_divisor_factor_pair_exists_unique',
    'dirichlet_convolution_multiplicative_values',
    'dirichlet_convolution_multiplicative_table',
    'dirichlet_convolution_multiplicative_exists_unique',
)
SLUG = 'g009-multiplicative-convolution'


@dataclass(frozen=True, slots=True)
class ArtifactPin:
    path: str
    bytes: int
    sha256: str
    nodes: int
    edges: int
    body_nodes: int


# Set only after actual complete original-HA export and source/spec freeze.
# Independent verification still runs on every acceptance; this is a data
# identity, never a successful-check flag. Empty registration is a hard stop.
FINAL_ARTIFACT: ArtifactPin | None = ArtifactPin(
    'research/arithmetic-library/artifacts/g009-multiplicative-convolution-proof-bundle-v1.json',
    7840579,
    '953dc5ef340379b1e34883c2f9ab2181e91c872f5bbb7943c52b2fb70ce76959',
    462,1371,35945,
)


def peak_rss_bytes():
    factor = 1 if sys.platform == 'darwin' else 1024
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)*factor
    if not 0 < peak <= 1536*1024*1024:
        raise support.G009Error('the original 1536MiB observed RSS gate failed')
    return peak


def require_final_inventory():
    support.require_final_source_pins()
    pin = FINAL_ARTIFACT
    if (type(pin) is not ArtifactPin or any(type(value) is not int or value <= 0
            for value in (pin.bytes,pin.nodes,pin.edges,pin.body_nodes))):
        raise support.G009Error('no actual complete G009 artifact has been registered')
    support.check_pin(support.FilePin(pin.path,pin.bytes,pin.sha256),support.ROOT,
                      support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
    return pin


def _load_final():
    pin = require_final_inventory()
    state = support.load_candidate_state(final=True)
    names = tuple(row.name for row in state.rows)
    if len(names) != 90 or not set(PRINCIPAL_ROOTS) <= set(names):
        raise support.G009Error('the final ninety-row/principal inventory is incomplete')
    selected = support.select_support(state.rows,names)
    payload = support.bounded_bytes(support.ROOT/pin.path,pin.bytes)
    if len(payload) != pin.bytes or sha256(payload).hexdigest() != pin.sha256:
        raise support.G009Error('the exact final artifact changed before parsing')
    bundle,target = decode_proof_bundle(payload.decode('utf-8'))
    return pin,state,selected,payload,bundle,target


def _shape(pin,selected,bundle,target):
    plan = selected.plan
    if len(selected.owned) != 90 or selected.current_support:
        raise support.G009Error('a partial authoring prefix cannot be a final checkpoint')
    receipt = support.closure.check_bottom_layer_bundle(selected.frontier,bundle,target)
    if (receipt.node_count != pin.nodes or receipt.dependency_edges != pin.edges
            or receipt.total_body_nodes != pin.body_nodes or receipt.kernel_calls != pin.nodes
            or pin.nodes != len(plan.rows)+1):
        raise support.G009Error('the whole original-HA inventory or body accounting changed')
    return receipt


def expected_report(pin,state,selected):
    """Syntax-only worker contract, not a successful verification receipt."""
    return {'slug':SLUG,'new_theorems':90,'new_specs_sha256':state.specs_sha256,
        'alpha_admission_performed':False,'stable_admission_performed':False,
        'parent':{'version':'v31','theorems':3796,'stable':432,'identity_sha256':support.PARENT_IDENTITY_SHA256},
        'owned_names':[row.name for row in selected.owned],
        'inherited_alpha_v31_names':list(selected.parent_support),
        'inherited_rows_counted_as_new':False,
        'execution_frontier_specs_sha256':selected.plan.frontier_specs_sha256,
        'ordered_complete_names_sha256':selected.plan.ordered_names_sha256,
        'bundle':{'path':pin.path,'bytes':pin.bytes,'sha256':pin.sha256,'nodes':pin.nodes,
                  'edges':pin.edges,'body_nodes':pin.body_nodes,'original_ha_checked':True,
                  'independent_lean_checked':True}}


def verify_checkpoint():
    pin,state,selected,payload,bundle,target = _load_final()
    receipt = _shape(pin,selected,bundle,target)
    # Reuse the unchanged adapter: real binary pin, private exclusive copy of
    # exactly the HA bytes, original timeout, exact stdout/root/node match.
    checkpoint = independent.Checkpoint(SLUG,(),pin.path,pin.bytes,pin.sha256,90,
                                       PRINCIPAL_ROOTS,'',state.specs_sha256)
    independent._lean_check(checkpoint,receipt.node_count,bundle.root,payload)
    peak_rss_bytes()
    return expected_report(pin,state,selected)


def expected_root_report(pin,selected,name):
    if type(name) is not str or name not in PRINCIPAL_ROOTS:
        raise support.G009Error('only an exact G009 principal may be replayed')
    row = next(row for row in selected.owned if row.name == name)
    positions = {row.name:row.node_id for row in selected.plan.rows}
    return {'slug':SLUG,'bundle_sha256':pin.sha256,'principal_roots':[{
        'name':name,'node_id':positions[name],'statement_sha256':sha256(row.statement.encode()).hexdigest(),
        'complete_ordinary_ha_checked':True}]}


def verify_principal_root(name):
    if type(name) is not str or name not in PRINCIPAL_ROOTS:
        raise support.G009Error('only an exact G009 principal may be replayed')
    pin,state,selected,payload,bundle,target = _load_final()
    if len(selected.owned) != 90 or selected.current_support or len(bundle.nodes) != pin.nodes:
        raise support.G009Error('a partial bundle cannot supply a final principal')
    # The authenticated source rows remain in selected; inert input bytes
    # and the unused state container need not overlap with ordinary replay.
    del state, payload
    gc.collect()
    # The original replay function itself checks the complete exact bundle
    # and every body before materialization. Do not duplicate that whole HA
    # pass here; the separate same-byte bundle worker also checks all literal
    # receipt metrics. The ordinary worker claims only its exact certificate.
    proof = support.closure.replay_bottom_layer_theorem(selected.frontier,name,bundle,target)
    # The returned ordinary certificate retains everything it actually uses.
    # Drop both independent decoded owners before its separate exact check.
    del bundle, target
    gc.collect()
    exact_spec = next(row for row in selected.owned if row.name == name)
    formula = _closed_formula(exact_spec.statement)
    if proof.spec != exact_spec or proof.formula != formula or not check((),proof.certificate,formula):
        raise support.G009Error('the exact ordinary empty-context principal failed original HA')
    result = expected_root_report(pin,selected,name)
    result['principal_roots'][0]['ordinary_certificate_nodes'] = proof.proof_nodes
    peak_rss_bytes()
    # No Lean claim here; the separate whole-bundle worker establishes it.
    return result
