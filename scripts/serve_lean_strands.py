#!/usr/bin/env python3
"""Serve bounded, independently verified Lean proof jobs and theorem explorers.

The server is loopback-only unless an operator explicitly supplies
``--public-host``.  A separately hosted static theorem explorer may use the
service only when its exact HTTPS origin is explicitly approved with
``--public-origin`` and ``--allowed-origin``.  Exactly one proof-generation
subprocess may be active; the subprocess invokes the existing sealed-edition
exporter and its real one-worker Lean verification.  Existing theorem-explorer
HTML gains the shared selector assets only while it is served: frozen source
pages are never rewritten.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
import ipaddress
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable
from urllib.parse import parse_qs, quote, unquote, unquote_to_bytes, urlsplit
import zipfile


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "scripts" / "export_peano_lean.py"
API_PREFIX = "/api/lean-strands"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_LIVE_URL_BYTES = 512 * 1024
MAX_LIVE_URL_BYTES = 1024 * 1024
DEFAULT_LIVE_SOURCE_BYTES = 1024 * 1024
MAX_LIVE_SOURCE_BYTES = 4 * 1024 * 1024
DEFAULT_STRAND_NODES = 1024
MAX_ALLOWED_ORIGINS = 16
MAX_FORWARDED_HOPS = 16
JOB_SCHEMA = "peano-lean-strand-service-v1"
LIVE_SCHEMA = "peano-lab-lean-live-v1"
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
THEOREM_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z")
SAFE_MODULE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
LIVE_CODEZ = re.compile(r"(?:[A-Za-z0-9]|%2B|%2F)+\Z")
STAGES = frozenset({"plan", "translate", "certificate", "package", "compile", "repair", "complete"})
TERMINAL = frozenset({"completed", "failed", "cancelled"})
SENSITIVE_SUFFIXES = frozenset(
    {
        ".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db", ".token",
        ".py", ".pyc", ".pyo", ".env", ".toml", ".ini", ".cfg", ".conf",
        ".yaml", ".yml", ".sh", ".zsh", ".bash", ".lock",
    }
)
SENSITIVE_NAMES = frozenset(
    {
        "id_rsa", "id_ed25519", "credentials", "credentials.json", "secrets.json",
        "config.json", "settings.json", "service-account.json", "package.json",
    }
)
LEGACY_EXPLORER_SEGMENTS = frozenset(
    {"pa-proof-explorer", "bertrand-proof-explorer", "constructive-grand-campaign",
     "constructive-priority-campaign", "constructive-gaussian-campaign",
     "constructive-completed-lower-campaign-v31", "constructive-research-campaign-v32",
     "constructive-research-campaign-v33"}
)
CONSTRUCTIVE_CAMPAIGN_SUCCESSORS = (
    "constructive-completed-lower-campaign-v31",
    "constructive-gaussian-campaign", "constructive-priority-campaign",
    "constructive-grand-campaign",
)
# Keep the older isolated-deployment order literal.  The explicitly reviewed
# current successors precede it; a present invalid one can never fall through.
CONSTRUCTIVE_RESEARCH_CAMPAIGNS = {
    "constructive-research-campaign-v33": "v33",
    "constructive-research-campaign-v32": "v32",
}
CONSTRUCTIVE_CATALOG_CODECS = {
    "v31": "peano_catalog_shards",
    "v32": "peano_catalog_shards_v32",
    "v33": "peano_catalog_shards_v33",
}
CONSTRUCTIVE_EXPLORER_SEGMENT = re.compile(r"constructive-[a-z][a-z0-9-]*-explorer\Z")
CONSTRUCTIVE_FAMILY_SLUG = re.compile(r"[a-z][a-z0-9-]{0,127}\Z")
CONSTRUCTIVE_RELEASE_VERSION = re.compile(r"v[1-9][0-9]{0,3}\Z")
MAX_EXPLORER_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_EXPLORER_CAMPAIGN_BYTES = 8 * 1024 * 1024
MAX_EXPLORER_CATALOG_BYTES = 64 * 1024 * 1024
MAX_EXPLORER_FAMILIES = 512

COMPLETED_LOWER_V31_FAMILIES = {
    "euler-units": 32, "prime-fields": 87, "mobius-values": 21, "signed-sums": 30,
    "divisor-sums": 37, "signed-weighted-sums": 40, "prime-field-polynomials": 49,
    "divisor-involutions": 12, "mobius-divisor-cancellation": 28, "rectangular-sums": 32,
    "polynomial-products": 53, "finite-support": 8, "dirichlet-convolution": 40,
    "dirichlet-fubini": 32, "dirichlet-units": 25, "mobius-inversion": 8,
    "dirichlet-signed-units": 9, "dirichlet-triangular": 10, "dirichlet-inverses": 21,
}

# Literal metadata identities from the forty-four byte-pinned historical
# readers. Mixed/unrecorded first admissions and non-admitted display aliases
# are retained; these descriptors authorize navigation, never theorem proof.
HISTORICAL_V31_FIRST_ADMISSIONS = {
    "arithmetic-foundations": "cfdffcc16315c05a275144d61ae40fe9f58c6ea8bc7834b851154e00d52b099d",
    "bertrand-postulate": "254577900ce3022e7c6930fc3f062a81ae05566601c9e54a14d894a5214c7fd2",
    "bertrand-prime-chains": "423370113995b149fe8121ab28fd0aa7f62bd47d62754e42ac272709d62a2f10",
    "best-approximation": "8b6330c4c2ba8577459b1cd36aea77d02ca27f4b1206cf1780ce282bf354e4a3",
    "binary-digit-extraction": "282c40c3215fc59ad46516482c6e860db32c982d92cf66fd2feb58753ea3cfe2",
    "binary-length": "2713cb1125c849c966e35a870280db49637e153600c740cac9083b238ee3507c",
    "binary-modular-execution": "c8569bf3fa1c3d5bc3efeb8579b17669ec3b9aee844570178afb3fadb51d1ea8",
    "binary-modular-exponentiation": "9f2c23240c97514228b9ca159c77ef0416ef0c2c7a8aad4ff603f37ce71ea0ee",
    "cauchy-davenport": "f733207080b339ee8507579e0e84b3989f1c2c6c2589d31c3d04721aa82c671b",
    "continued-fractions": "bbdbd4c47a9aae1ccbf06ed74e914e460b264d0b13f5d622add7f5f6e133c7b8",
    "cornacchia": "b9e8ccca7ee3d58cebb1e9a81dfdfbd18723fed529bdebe746260f76f50af76d",
    "eisenstein-integers": "945d9b6bce5ff9650d1992383ded3c9d66d6998f1a633b8e26417f3a6c8b0f71",
    "euclidean-complexity": "d3a7c04f53469fd3ef4198c1f0ff1e3d9d8c280dba1bafefbd77703a06fa10f3",
    "euclidean-gcd-transport": "693590c5284a7c1df4f0f36a8d54adbb823973a9e8ad7199c948e524f2e6ee37",
    "euclidean-logarithmic-bound": "99de192c6bd3c338815235282e7b5596273f1b1aa92a500353c1ebd27380b816",
    "exponent-lifting": "1f4efde4320edb946ec777c929dd18dc2c87e72cbc6eedd53b6894d1ecee3b26",
    "four-squares": "1e59942892966dfcea70f29a1be44c4d4fd0fd56a707aafd65f70d046e06e242",
    "gaussian-factorization": "724c4d0e91b54c354a5158a395a1ecb7e8519c48ac18a0357900ceabe4ae90ce",
    "gaussian-integers": "3ad385415c5639baa62adbb1352a272d84f85b787d507be0d46cf00f18cf0411",
    "generalized-crt": "4af026b4c1658811650c4138d38ea6f064f003ab5bc610199904a6dc99d6d44c",
    "generalized-crt-compatibility": "709337ff759f1392ccdd305aa3f73e8e7382e6820deaff90e2ca7f818f22c5ec",
    "generalized-crt-fold": "d81d62b444f8b9ba3a5913de09be3309638633ff00022bb6872561f2dd1d3aef",
    "hensel-lifting": "4080ec0c58faeabac8bc24c393cf108a3b51c195aba6125e08f2039720b1f4e4",
    "integer-linear-algebra": "a3fe5c696aee11e33a48b474b63aa14dd6f50d7150999f85f3a2039b1c6d2fcb",
    "kummer": "50a5634551a5e8bdd631ba03dc24f55d63cf5c5d97dd676eb80f1fcd28ca61e7",
    "lucas": "723649d33b1d7ca32a12fe01f4d95f072547bc6e31bc5756b4122544bb7ad53a",
    "matrix-coded-products": "a08af99b0160d6c7c72efb14c53b273fe80c475fa970896168f6e6fde107dae5",
    "matrix-cofactor-expansion": "7b7c5cf2a1eb18c1aa53d3a11dbacf242016b1f075108c251f9cde67831c8ceb",
    "matrix-determinant-minors": "ee3df980d0c70f10fdd284820a89de9c68e3c66f2b68cdc03b72f022c853e3e7",
    "matrix-dot-product": "c2384c2a8914c1fe4eec0335f0dc73971cf173151fdc1f39eac159582ca70a36",
    "multinomial-kummer": "23c74fc9c92c28b3f67f3d251f9d369fe6be0bba8ca39503f05e48f71336d53c",
    "polynomial-hensel": "1fb5bb73d3262afa2246c7b08ceaf658f42fde035665e6f1b9f70e025c81cb35",
    "polynomial-horner": "50899ce24a7060e49212b81e463e1406a671058688472ce1c858daf336df6bb8",
    "polynomial-taylor-hensel": "387617ea6f729fb7f34851959786b47ff468408e1dcaab2cd6607c37e2a13b3b",
    "prime-count-chebyshev": "8c853603b4289101d2861eb2ee5ee4cd85407262af0b8d3d7f252eae0b52bdce",
    "prime-enumeration": "4f143b049846e1b02fe3fa087c65e500ba7a42dbdfabbdd8791332d0ec55226e",
    "prime-valuation-support": "ba66c595076a9708393151277cf398555d36fb9cf115f9f13f384358940cc28e",
    "primes-three-mod-four": "2b8dfac78f8c4d3b6b571328b89679bb78c1799a822f9cb47e212f030eaeabb7",
    "pythagorean-fermat-four": "4611ca49f9d6d19336e2049d21ad4246f7841c1fe7e20dc53f15848a97dbdd27",
    "quadratic-reciprocity": "4b07f41f1331eddef05ac148c476157e0ec5cd7111a9d57bfc39b62768ba2c8d",
    "squarefree-kernels": "5a1c259dfb2ec468adfd256a6756fc2c78d720a3a3e3136bd2a51e7eb351105a",
    "supplementary-laws": "b5825f0d2d77359296dbb5f9080a58b51f1450809c921d8448c85a3761e26010",
    "totient-products": "a916830eb4236a84cef9e96dc9b77aa7d2370965fdca2ee2fb4b6073165716d0",
    "two-squares": "a70f74c7e962dccb1a5a13772c6ad5215199f21fe05311186d6c21209023ccfd"
}


@dataclass(frozen=True, slots=True)
class ConstructivePublication:
    """Exact presentation schema and admission history, not proof authority."""

    schema: str
    current_version: str
    first_enrolled_version: str
    first_catalog_sha256: str | None = None


CONSTRUCTIVE_PUBLICATIONS = {
    "constructive-polynomial-euclidean-explorer-v33": ConstructivePublication(
        "peano-lab-alpha-v33-canonical-publication-v1-manifest", "v33", "v33"
    ),
    "constructive-research-explorer-v33": ConstructivePublication(
        "peano-lab-alpha-v33-canonical-publication-v1-manifest", "v33", "v32"
    ),
    "constructive-completed-lower-explorer-v33": ConstructivePublication(
        "peano-lab-alpha-v33-canonical-publication-v1-manifest", "v33", "v31"
    ),
    "constructive-historical-explorers-v33": ConstructivePublication(
        "peano-lab-alpha-v33-canonical-publication-v1-manifest", "v33", "mixed_preserved"
    ),
    "constructive-research-explorer-v32": ConstructivePublication(
        "peano-lab-alpha-v32-canonical-publication-v1-manifest", "v32", "v32"
    ),
    "constructive-completed-lower-explorer-v32": ConstructivePublication(
        "peano-lab-alpha-v32-canonical-publication-v1-manifest", "v32", "v31"
    ),
    "constructive-historical-explorers-v32": ConstructivePublication(
        "peano-lab-alpha-v32-canonical-publication-v1-manifest", "v32", "mixed_preserved"
    ),
    "constructive-historical-explorers-v31": ConstructivePublication(
        "peano-lab-constructive-historical-publication-v31-manifest", "v31", "mixed_preserved"
    ),
    "constructive-completed-lower-explorer-v31": ConstructivePublication(
        "peano-lab-constructive-completed-lower-explorer-v31-manifest", "v31", "v31"
    ),
    "constructive-gaussian-factorization-explorer": ConstructivePublication(
        "peano-lab-constructive-gaussian-factorization-explorer-v1-manifest", "v30", "v30"
    ),
    "constructive-priority-layer-explorer-v30": ConstructivePublication(
        "peano-lab-constructive-historical-publication-v30-first-v29-manifest",
        "v30", "v29",
        "2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0",
    ),
    "constructive-lower-layer-explorer-v30": ConstructivePublication(
        "peano-lab-constructive-historical-publication-v30-first-v28-manifest",
        "v30", "v28",
        "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9",
    ),
    "constructive-second-wave-explorer-v30": ConstructivePublication(
        "peano-lab-constructive-historical-publication-v30-first-v27-manifest",
        "v30", "v27",
        "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6",
    ),
    "constructive-lower-layer-explorer": ConstructivePublication(
        "peano-lab-constructive-lower-layer-explorer-v1-manifest", "v28", "v28"
    ),
    "constructive-second-wave-explorer-v28": ConstructivePublication(
        "peano-lab-constructive-second-wave-explorer-v1-manifest",
        "v28",
        "v27",
        "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6",
    ),
    # The original directory remains the immutable v27 publication. Relabeling
    # its manifest does not make it the current v28 successor.
    "constructive-second-wave-explorer": ConstructivePublication(
        "peano-lab-constructive-second-wave-explorer-v1-manifest",
        "v27",
        "v27",
        "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6",
    ),
}

CONSTRUCTIVE_MODERN_PHASES = {
    "constructive-polynomial-euclidean-explorer-v33": "polynomial",
    **{f"constructive-{component}-v{version}": phase
       for version in (32, 33)
       for component, phase in (("research-explorer", "research"),
                                ("completed-lower-explorer", "completed"),
                                ("historical-explorers", "historical"))},
}
CONSTRUCTIVE_MODERN_COUNTS = {
    "polynomial": (121, 121, 0), "research": (175, 175, 0),
    "completed": (574, 574, 0), "historical": (3096, 3007, 443),
}
CONSTRUCTIVE_MODERN_NEW_FAMILIES = {
    "multiplicative-convolution": (90, "MX", "v32", "2013935a09dcd2d7fefdae65ad31f63815e73e5e45da37cd71a880fdb2f5031f"),
    "polynomial-division-prerequisites": (85, "PQ", "v32", "c7fe5ba9e5b0cbfbdde4f0bea7ef321355661f2408ca31e5a78e3041cfb19ce0"),
    "polynomial-euclidean-division": (121, "PX", "v33", "80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc"),
}
# Literal presentation parents, never proof receipts.  Current successors copy
# these exact manifests; historical first-admission records remain separate.
CONSTRUCTIVE_MODERN_PARENTS = {
    "constructive-completed-lower-explorer-v32": ("constructive-completed-lower-explorer-v31", 368715,
        "3fd1e3ceac74d898800030bb0429198c3ec873a3c67ee41d3c06b07b8dc3f1f8"),
    "constructive-historical-explorers-v32": ("constructive-historical-explorers-v31", 1496113,
        "e6805a7a4a09754c4cbaec214b4de6720e6226f609ac4f1a9ad6514cae524372"),
    "constructive-research-explorer-v33": ("constructive-research-explorer-v32", 100223,
        "d69e3793319a6eb97e4224fe5c44f6d374a3f16b5b151e75e79af310121df02f"),
    "constructive-completed-lower-explorer-v33": ("constructive-completed-lower-explorer-v32", 368650,
        "9c0a8703425c7c65dc147af798eb6f5bbed8765ab42dc84e5f10be7b80a1037d"),
    "constructive-historical-explorers-v33": ("constructive-historical-explorers-v32", 1780753,
        "f92a442588e30476be619b01552115e0cd7cc818becde21beb316c12be0cc610"),
}


def _constructive_explorer_segment(segment: str) -> bool:
    return (
        segment in CONSTRUCTIVE_PUBLICATIONS
        or CONSTRUCTIVE_EXPLORER_SEGMENT.fullmatch(segment) is not None
    )


def _constructive_explorer_candidate(segment: str) -> bool:
    # Classification includes malformed/versioned spellings so they cannot
    # bypass manifest review through the generic legacy graph fallback.
    # Authorization still requires the original exact grammar or the explicit
    # publication mapping above; no arbitrary version suffix is approved.
    folded = segment.lower()
    return folded.startswith("constructive-") and "-explorer" in folded


class ServiceError(ValueError):
    """An unsafe request, job transition, or generated artifact was rejected."""


class JobBusyError(ServiceError):
    """The one independently verified proof worker is already occupied."""


class JobNotFoundError(ServiceError):
    """The requested bounded, opaque job identifier is unavailable."""


class JobRateLimitError(ServiceError):
    """One client exceeded the bounded mutation window."""


@dataclass(frozen=True, slots=True)
class ServiceLimits:
    request_bytes: int = 16 * 1024
    response_bytes: int = 3 * 1024 * 1024
    diagnostic_bytes: int = 64 * 1024
    event_line_bytes: int = 16 * 1024
    live_metadata_bytes: int = 2 * 1024 * 1024
    html_bytes: int = 4 * 1024 * 1024
    static_bytes: int = 128 * 1024 * 1024
    package_bytes: int = 64 * 1024 * 1024
    package_files: int = 4_096
    retained_jobs: int = 32
    ttl_seconds: int = 900
    memory_mib: int = 1_024
    verify_seconds: int = 180
    job_seconds: int = 240
    strand_nodes: int = DEFAULT_STRAND_NODES
    strand_edges: int = 8_192
    strand_depth: int = 128
    proof_steps: int = 4_096
    proof_repairs: int = 16
    chunk_kib: int = 192
    live_url_bytes: int = DEFAULT_LIVE_URL_BYTES
    live_source_bytes: int = DEFAULT_LIVE_SOURCE_BYTES
    concurrent_requests: int = 16
    mutations_per_minute: int = 30


@dataclass(frozen=True, slots=True)
class JobRequest:
    theorem: str
    edition: str
    memory_mib: int
    verify_seconds: int
    strand_nodes: int
    strand_edges: int
    strand_depth: int
    proof_steps: int
    proof_repairs: int
    chunk_kib: int
    strict_readable: bool


@dataclass(slots=True)
class JobRecord:
    identifier: str
    request: JobRequest
    directory: Path
    created_at: float
    updated_at: float
    status: str = "queued"
    stage: str = "queued"
    completed: int = 0
    total: int = 0
    diagnostics: deque[str] = field(default_factory=lambda: deque(maxlen=80))
    diagnostic_bytes: int = 0
    error: str | None = None
    manifest: dict[str, Any] | None = None
    lean_verified: bool = False
    verification_marker: bool = False
    live_url: str | None = None
    live_status: str = "fallback_required"
    live_encoding: str | None = None
    live_source_sha256: str | None = None
    live_source_bytes: int = 0
    process: subprocess.Popen[str] | None = None
    cancel_requested: bool = False
    revision: int = 0


def _safe_text(value: object, *, maximum: int = 512) -> str:
    if type(value) is not str:
        raise ServiceError("diagnostics and progress messages must be text")
    compact = " ".join(value.replace("\x00", "").split())
    return compact.encode("utf-8")[:maximum].decode("utf-8", errors="ignore")


def _bounded_json(payload: object, *, maximum: int) -> bytes:
    try:
        encoded = (
            json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ServiceError("service response is not finite strict JSON") from error
    if len(encoded) > maximum:
        raise ServiceError("service response exceeds its reviewed byte limit")
    return encoded


def _validate_job_id(identifier: object) -> str:
    if type(identifier) is not str or JOB_ID.fullmatch(identifier) is None:
        raise JobNotFoundError("job identifier is not a valid opaque token")
    return identifier


def _bounded_integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ServiceError(f"{name} must be an integer between {minimum} and {maximum}")
    return value


def _loopback_hostname(hostname: str) -> bool:
    if hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _safe_origin(value: object, *, label: str) -> str:
    """Canonicalize one exact HTTP(S) origin without paths or credentials."""

    if (
        type(value) is not str
        or not value
        or len(value) > 512
        or any(character.isspace() for character in value)
        or "," in value
        or "\\" in value
    ):
        raise ServiceError(f"{label} must be one exact HTTP(S) origin")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ServiceError(f"{label} must be one exact HTTP(S) origin") from error
    if (
        parsed.scheme not in {"http", "https"}
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or port == 0
    ):
        raise ServiceError(f"{label} must be one exact HTTP(S) origin")
    if parsed.scheme != "https" and not _loopback_hostname(hostname):
        raise ServiceError(f"{label} must use HTTPS outside loopback")
    return parsed.scheme + "://" + parsed.netloc.lower()


def _safe_host_header(value: str) -> str | None:
    if (
        not value
        or len(value) > 256
        or any(character.isspace() for character in value)
        or any(character in value for character in ",/\\@?#")
    ):
        return None
    try:
        parsed = urlsplit("//" + value)
        if not parsed.hostname or parsed.port == 0 or parsed.username or parsed.password:
            return None
    except ValueError:
        return None
    return parsed.netloc.lower()


def validate_request(payload: object, limits: ServiceLimits) -> JobRequest:
    """Accept only a bounded theorem request; never forward arbitrary CLI flags."""

    if type(payload) is not dict:
        raise ServiceError("proof-job request must be a JSON object")
    allowed = {
        "theorem",
        "edition",
        "max_memory_mib",
        "max_verify_seconds",
        "max_strand_nodes",
        "max_strand_edges",
        "max_strand_depth",
        "max_proof_steps",
        "max_proof_repairs",
        "max_chunk_kib",
        "strict_readable",
    }
    unexpected = set(payload).difference(allowed)
    if unexpected:
        raise ServiceError("unsupported proof-job option(s): " + ", ".join(sorted(unexpected)))
    name = payload.get("theorem")
    if type(name) is not str or name == "_" or THEOREM_NAME.fullmatch(name) is None:
        raise ServiceError("theorem must be one bounded safe Lean identifier")
    edition = payload.get("edition", "stable")
    if type(edition) is not str or edition not in {"stable", "alpha"}:
        raise ServiceError("edition must be exactly 'stable' or 'alpha'")
    strict = payload.get("strict_readable", False)
    if type(strict) is not bool:
        raise ServiceError("strict_readable must be an exact JSON boolean")
    return JobRequest(
        theorem=name,
        edition=edition,
        memory_mib=_bounded_integer(
            payload.get("max_memory_mib", limits.memory_mib),
            "max_memory_mib",
            64,
            limits.memory_mib,
        ),
        verify_seconds=_bounded_integer(
            payload.get("max_verify_seconds", limits.verify_seconds),
            "max_verify_seconds",
            1,
            limits.verify_seconds,
        ),
        strand_nodes=_bounded_integer(
            payload.get("max_strand_nodes", limits.strand_nodes),
            "max_strand_nodes",
            1,
            limits.strand_nodes,
        ),
        strand_edges=_bounded_integer(
            payload.get("max_strand_edges", limits.strand_edges),
            "max_strand_edges",
            1,
            limits.strand_edges,
        ),
        strand_depth=_bounded_integer(
            payload.get("max_strand_depth", limits.strand_depth),
            "max_strand_depth",
            1,
            limits.strand_depth,
        ),
        proof_steps=_bounded_integer(
            payload.get("max_proof_steps", limits.proof_steps),
            "max_proof_steps",
            1,
            limits.proof_steps,
        ),
        proof_repairs=_bounded_integer(
            payload.get("max_proof_repairs", limits.proof_repairs),
            "max_proof_repairs",
            0,
            limits.proof_repairs,
        ),
        chunk_kib=_bounded_integer(
            payload.get("max_chunk_kib", limits.chunk_kib),
            "max_chunk_kib",
            8,
            limits.chunk_kib,
        ),
        strict_readable=strict,
    )


def validate_live_url(value: object, *, maximum: int = DEFAULT_LIVE_URL_BYTES) -> str | None:
    """Permit only exact bounded official inline Lean Live code/codez links."""

    if value is None:
        return None
    if type(value) is not str or len(value.encode("utf-8")) > maximum:
        return None
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "live.lean-lang.org"
        or parsed.netloc != "live.lean-lang.org"
        or parsed.path != "/"
        or parsed.query
        or parsed.username is not None
        or parsed.password is not None
    ):
        return None
    if parsed.fragment.startswith("code="):
        if not parsed.fragment[5:]:
            return None
    elif parsed.fragment.startswith("codez="):
        if LIVE_CODEZ.fullmatch(parsed.fragment[6:]) is None:
            return None
    else:
        return None
    return value


def _decoded_live_source(url: str, *, maximum: int) -> tuple[bytes, str]:
    """Decode bounded inline proof source; never fetch hosted/private content."""

    fragment = urlsplit(url).fragment
    if fragment.startswith("code="):
        try:
            decoded = unquote_to_bytes(fragment[5:])
            decoded.decode("utf-8", errors="strict")
        except (UnicodeError, ValueError) as error:
            raise ServiceError("Lean Live code does not contain exact UTF-8 proof source") from error
        encoding = "code"
    elif fragment.startswith("codez="):
        package_root = str(ROOT / "peano-lab" / "py")
        if package_root not in sys.path:
            sys.path.insert(0, package_root)
        try:
            from peano_lab.library.lean_proof_strand import decompress_lean_live_codez

            encoded = fragment[6:]
            if LIVE_CODEZ.fullmatch(encoded) is None:
                raise ValueError("compressed proof does not use canonical escaped Base64")
            compressed = unquote(encoded, errors="strict")
            if quote(compressed, safe="") != encoded:
                raise ValueError("compressed proof does not use canonical escaped Base64")
            decoded = decompress_lean_live_codez(
                compressed,
                max_output_bytes=maximum,
            ).encode("utf-8")
        except (ImportError, UnicodeError, ValueError) as error:
            raise ServiceError("Lean Live compressed code is not one bounded exact proof") from error
        encoding = "codez"
    else:
        raise ServiceError("Lean Live source must be one approved inline proof fragment")
    if len(decoded) > maximum:
        raise ServiceError("Lean Live source exceeds its exact checked proof byte budget")
    return decoded, encoding


def _core_standalone_source(payload: bytes) -> None:
    """Require literally zero imports, no added axioms, and no placeholders."""

    try:
        source = payload.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise ServiceError("standalone Lean proof is not exact UTF-8 source") from error
    if re.search(r"(?m)^\s*import\b", source):
        raise ServiceError("standalone Lean proof declares an explicit import; only import-free proofs are shareable")
    if re.search(r"\b(?:sorry|sorryAx|native_decide)\b", source):
        raise ServiceError("standalone Lean proof contains an unsafe unchecked placeholder")
    if re.search(r"(?m)^\s*axiom\b", source):
        raise ServiceError("standalone Lean proof declares an unaudited external axiom")


class JobManager:
    """One isolated, cancellable, independently verified Lean worker."""

    def __init__(
        self,
        storage: Path,
        *,
        limits: ServiceLimits | None = None,
        popen: Callable[..., subprocess.Popen[str]] = subprocess.Popen,
    ) -> None:
        self.limits = limits or ServiceLimits()
        selected_storage = Path(storage).expanduser()
        if selected_storage.is_symlink():
            raise ServiceError("proof-job storage cannot be a symlink")
        self.storage = selected_storage.resolve()
        self.storage.mkdir(mode=0o700, parents=True, exist_ok=True)
        if not self.storage.is_dir():
            raise ServiceError("proof-job storage must be a directory")
        self._popen = popen
        self._lock = threading.RLock()
        self._changed = threading.Condition(self._lock)
        self._jobs: dict[str, JobRecord] = {}
        self._active: str | None = None
        self._mutation_windows: dict[str, deque[float]] = {}

    def check_mutation_rate(self, client: str) -> None:
        """Bound expensive mutations per client without retaining unbounded keys."""

        if type(client) is not str or not client or len(client) > 128:
            raise JobRateLimitError("proof-job client identity is unavailable")
        now = time.monotonic()
        with self._lock:
            if client not in self._mutation_windows:
                if len(self._mutation_windows) >= 1_024:
                    expired = [
                        key
                        for key, values in self._mutation_windows.items()
                        if not values or now - values[-1] >= 60.0
                    ]
                    for key in expired:
                        self._mutation_windows.pop(key, None)
                    if len(self._mutation_windows) >= 1_024:
                        raise JobRateLimitError("proof-job client capacity is temporarily full")
                self._mutation_windows[client] = deque()
            window = self._mutation_windows[client]
            while window and now - window[0] >= 60.0:
                window.popleft()
            if len(window) >= self.limits.mutations_per_minute:
                raise JobRateLimitError("proof-job mutation rate exceeded; retry within a minute")
            window.append(now)

    def _touch(self, job: JobRecord) -> None:
        job.updated_at = time.time()
        job.revision += 1
        self._changed.notify_all()

    def _remove_job_directory(self, job: JobRecord) -> None:
        target = job.directory.resolve()
        if (
            target.parent != self.storage
            or target.name != job.identifier
            or JOB_ID.fullmatch(target.name) is None
            or target.is_symlink()
        ):
            raise ServiceError("refusing to remove an unsafe proof-job directory")
        if target.is_dir():
            shutil.rmtree(target)

    def _cleanup_locked(self) -> None:
        deadline = time.time() - self.limits.ttl_seconds
        expired = [
            key
            for key, job in self._jobs.items()
            if job.status in TERMINAL and job.updated_at < deadline
        ]
        for key in expired:
            job = self._jobs.pop(key)
            self._remove_job_directory(job)

    def _snapshot_locked(self, job: JobRecord) -> dict[str, Any]:
        base = f"{API_PREFIX}/jobs/{job.identifier}"
        percent = (
            min(100, round(100 * job.completed / job.total))
            if job.total
            else (100 if job.status == "completed" else 0)
        )
        downloads = {
            "lean": base + "/download?format=lean",
            "zip": base + "/download?format=zip",
        }
        return {
            "schema": JOB_SCHEMA,
            "job_id": job.identifier,
            "theorem": job.request.theorem,
            "edition": job.request.edition,
            "status": job.status,
            "state": job.status,
            "stage": job.stage,
            "completed": job.completed,
            "total": job.total,
            "percent": percent,
            "progress": {
                "current": job.completed,
                "completed": job.completed,
                "total": job.total,
                "percent": percent,
            },
            "created_at": datetime.fromtimestamp(
                job.created_at,
                timezone.utc,
            ).isoformat(),
            "updated_at": datetime.fromtimestamp(
                job.updated_at,
                timezone.utc,
            ).isoformat(),
            "status_url": base,
            "events_url": base + "/events",
            "downloads": downloads,
            "download_urls": downloads,
            "live_url": job.live_url,
            "live_status": job.live_status,
            "live_encoding": job.live_encoding,
            "live_compatible": job.live_status in {"ready", "oversized"},
            "standalone_lean": job.live_status in {"ready", "oversized"},
            "companion_required": job.live_status not in {"ready", "oversized"},
            "lean_live": {
                "compatible": job.live_status in {"ready", "oversized"},
                "url": job.live_url,
                "status": job.live_status,
                "share_encoding": job.live_encoding,
                "source_sha256": job.live_source_sha256,
                "source_bytes": job.live_source_bytes,
                "local_source_verified": job.live_status in {"ready", "oversized"},
                "self_contained": job.live_status in {"ready", "oversized"},
                "core_imports": [],
                "external_import_count": 0,
                "remote_compilation": "not_run",
            },
            "lean_verified": job.lean_verified,
            "manifest": job.manifest,
            "diagnostics": list(job.diagnostics),
            "error": job.error,
        }

    def submit(self, payload: object) -> dict[str, Any]:
        request = validate_request(payload, self.limits)
        with self._changed:
            self._cleanup_locked()
            if self._active is not None:
                raise JobBusyError("one Lean proof job is already active; cancel it first")
            if len(self._jobs) >= self.limits.retained_jobs:
                raise JobBusyError("the bounded proof-job history is full")
            identifier = secrets.token_hex(16)
            if identifier in self._jobs:
                raise ServiceError("generated job identifier unexpectedly collided")
            directory = self.storage / identifier
            directory.mkdir(mode=0o700)
            now = time.time()
            job = JobRecord(identifier, request, directory, now, now)
            self._jobs[identifier] = job
            self._active = identifier
            thread = threading.Thread(
                target=self._execute,
                args=(identifier,),
                name=f"lean-proof-{identifier[:8]}",
                daemon=True,
            )
            thread.start()
            return self._snapshot_locked(job)

    def snapshot(self, identifier: str) -> dict[str, Any]:
        valid = _validate_job_id(identifier)
        with self._changed:
            self._cleanup_locked()
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            return self._snapshot_locked(job)

    def _diagnostic(self, job: JobRecord, message: object) -> None:
        try:
            text = _safe_text(message, maximum=1_024)
        except ServiceError:
            return
        if not text:
            return
        text = text.replace(str(ROOT), "<repository>").replace(
            str(job.directory),
            "<proof-job>",
        )
        encoded = len(text.encode("utf-8"))
        if job.diagnostic_bytes + encoded > self.limits.diagnostic_bytes:
            return
        job.diagnostic_bytes += encoded
        job.diagnostics.append(text)

    def _progress(self, job: JobRecord, payload: object) -> bool:
        if (
            type(payload) is not dict
            or payload.get("kind") != "lean_strand_progress"
            or type(payload.get("stage")) is not str
            or payload["stage"] not in STAGES
            or type(payload.get("completed")) is not int
            or type(payload.get("total")) is not int
            or not 0 <= payload["completed"] <= 10_000_000
            or not 0 <= payload["total"] <= 10_000_000
        ):
            return False
        theorem = payload.get("theorem")
        if theorem is not None and (
            type(theorem) is not str or THEOREM_NAME.fullmatch(theorem) is None
        ):
            return False
        module = payload.get("module")
        if module is not None and (
            type(module) is not str or SAFE_MODULE.fullmatch(module) is None
        ):
            return False
        job.stage = payload["stage"]
        job.completed = payload["completed"]
        job.total = payload["total"]
        message = payload.get("message")
        if message is not None:
            self._diagnostic(job, message)
        # Progress is not a proof receipt; publish URLs only after local checks.
        return True

    def _consume_stderr(self, identifier: str, stream: Any) -> None:
        while True:
            try:
                line = stream.readline(self.limits.event_line_bytes + 1)
            except (OSError, ValueError):
                return
            if not line:
                return
            with self._changed:
                job = self._jobs.get(identifier)
                if job is None:
                    return
                if len(line.encode("utf-8")) <= self.limits.event_line_bytes:
                    try:
                        event = json.loads(line)
                    except (TypeError, ValueError):
                        event = None
                    if not self._progress(job, event):
                        if line.strip() == "Independent Lean compilation: PASSED.":
                            job.verification_marker = True
                        self._diagnostic(job, line)
                else:
                    self._diagnostic(job, "exporter diagnostic exceeded its line limit")
                self._touch(job)

    def _command(self, job: JobRecord) -> list[str]:
        item = job.request
        command = [
            sys.executable,
            "-B",
            str(EXPORTER),
            item.theorem,
            "--edition",
            item.edition,
            "--format",
            "strand",
            "--package-dir",
            str(job.directory / "package"),
            "--verify",
            "--max-memory-mib",
            str(item.memory_mib),
            "--max-verify-seconds",
            str(item.verify_seconds),
            "--max-strand-nodes",
            str(item.strand_nodes),
            "--max-strand-edges",
            str(item.strand_edges),
            "--max-strand-depth",
            str(item.strand_depth),
            "--max-proof-steps",
            str(item.proof_steps),
            "--max-proof-repairs",
            str(item.proof_repairs),
            "--max-chunk-kib",
            str(item.chunk_kib),
            "--progress-json",
            "--live-lean-output",
            str(job.directory / "live.lean"),
            "--max-live-url-bytes",
            str(self.limits.live_url_bytes),
            "--max-live-source-kib",
            str(self.limits.live_source_bytes // 1024),
        ]
        if item.strict_readable:
            command.append("--strict-readable")
        return command

    def _load_manifest(self, job: JobRecord) -> dict[str, Any]:
        source = job.directory / "package" / "manifest.json"
        if source.is_symlink() or not source.is_file():
            raise ServiceError("verified Lean job did not publish its proof-strand catalog")
        if source.stat().st_size > min(self.limits.package_bytes, 8 * 1024 * 1024):
            raise ServiceError("verified Lean job produced an oversized proof manifest")
        try:
            catalog = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as error:
            raise ServiceError("verified Lean job produced a malformed proof manifest") from error
        if (
            type(catalog) is not dict
            or catalog.get("schema") != "peano-lean-proof-strand-package-v1"
            or type(catalog.get("strands")) is not dict
            or len(catalog["strands"]) != 1
        ):
            raise ServiceError("verified Lean job produced an unauthenticated proof catalog")
        entry = next(iter(catalog["strands"].values()))
        if (
            type(entry) is not dict
            or entry.get("schema") != "peano-lab-lean-proof-strand-v1"
            or entry.get("name") != job.request.theorem
            or entry.get("edition") != job.request.edition
            or type(entry.get("node_count")) is not int
            or type(entry.get("translated_node_count")) is not int
            or type(entry.get("fallback_node_count")) is not int
            or type(entry.get("relative_path")) is not str
        ):
            raise ServiceError("verified Lean job manifest changed its selected theorem")
        return {
            "name": entry["name"],
            "edition": entry["edition"],
            "edition_version": entry.get("edition_version"),
            "node_count": entry["node_count"],
            "edge_count": entry.get("edge_count"),
            "translated_node_count": entry["translated_node_count"],
            "fallback_node_count": entry["fallback_node_count"],
            "chunk_count": entry.get("chunk_count"),
            "identity_sha256": entry.get("identity_sha256"),
            "relative_path": entry["relative_path"],
        }

    def _load_live(self, job: JobRecord) -> None:
        lean = job.directory / "live.lean"
        sidecar = job.directory / "live.json"
        if lean.is_symlink() or sidecar.is_symlink():
            raise ServiceError("Lean Live artifacts must not be symbolic links")
        if not lean.is_file() or not sidecar.is_file():
            job.live_status = "fallback_required"
            job.live_url = None
            job.live_encoding = None
            job.live_source_sha256 = None
            return
        if sidecar.stat().st_size > self.limits.live_metadata_bytes:
            raise ServiceError("Lean Live metadata exceeds its reviewed size limit")
        if lean.stat().st_size > min(self.limits.package_bytes, self.limits.live_source_bytes):
            raise ServiceError("Lean Live source exceeds its reviewed size limit")
        try:
            metadata = json.loads(sidecar.read_text(encoding="utf-8"))
        except (OSError, TypeError, ValueError) as error:
            raise ServiceError("Lean Live metadata is not canonical JSON") from error
        actual = lean.read_bytes()
        actual_digest = sha256(actual).hexdigest()
        if (
            type(metadata) is not dict
            or metadata.get("schema") != LIVE_SCHEMA
            or metadata.get("theorem") != job.request.theorem
            or metadata.get("edition") != job.request.edition
            or type(metadata.get("source_sha256")) is not str
            or not secrets.compare_digest(metadata["source_sha256"], actual_digest)
            or metadata.get("source_bytes") != len(actual)
            or metadata.get("local_source_verified") is not True
            or metadata.get("remote_compilation") != "not_run"
            or metadata.get("self_contained") is not True
            or metadata.get("core_imports") != []
            or type(metadata.get("external_import_count")) is not int
            or metadata.get("external_import_count") != 0
        ):
            raise ServiceError("Lean Live metadata does not authenticate its locally checked source")
        if job.manifest is None or job.manifest.get("fallback_node_count") != 0:
            raise ServiceError("Lean Live standalone source cannot contain companion-backed certificates")
        _core_standalone_source(actual)
        recorded_fallback = metadata.get("fallback_node_count", 0)
        if type(recorded_fallback) is not int or recorded_fallback != 0:
            raise ServiceError("Lean Live metadata includes a non-standalone certificate fallback")
        job.live_source_bytes = len(actual)
        job.live_source_sha256 = actual_digest
        declared = metadata.get("share_encoding")
        if declared is not None and declared not in {"code", "codez"}:
            raise ServiceError("Lean Live metadata has an unsupported inline proof encoding")
        shared = validate_live_url(
            metadata.get("share_url"),
            maximum=self.limits.live_url_bytes,
        )
        if metadata.get("share_url") is not None and shared is None:
            raise ServiceError("Lean Live metadata contains an unsafe or oversized official URL")
        if shared is not None:
            decoded, actual_encoding = _decoded_live_source(
                shared,
                maximum=len(actual),
            )
            if not secrets.compare_digest(sha256(decoded).hexdigest(), actual_digest):
                raise ServiceError("Lean Live URL does not contain the exact locally compiled proof")
            if declared is not None and declared != actual_encoding:
                raise ServiceError("Lean Live metadata changed its exact inline source encoding")
            if metadata.get("share_status") != "ready":
                raise ServiceError("Lean Live ready URL contradicts its checked metadata status")
            job.live_encoding = actual_encoding
        else:
            if metadata.get("share_status") != "oversized":
                raise ServiceError("missing Lean Live URL contradicts its checked metadata status")
            job.live_encoding = None
        job.live_url = shared
        job.live_status = "ready" if shared is not None else "oversized"

    @staticmethod
    def _terminate_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except (OSError, ProcessLookupError):
            return
        try:
            process.wait(timeout=4.0)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except (OSError, ProcessLookupError):
                return

    def _execute(self, identifier: str) -> None:
        with self._changed:
            job = self._jobs.get(identifier)
            if job is None:
                return
            if job.cancel_requested:
                self._active = None
                return
            job.status = "running"
            job.stage = "plan"
            self._touch(job)
        reader: threading.Thread | None = None
        try:
            environment = dict(os.environ)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PYTHONUNBUFFERED"] = "1"
            process = self._popen(
                self._command(job),
                cwd=str(ROOT),
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=(os.name == "posix"),
            )
            with self._changed:
                job.process = process
                cancelled = job.cancel_requested
            if cancelled:
                self._terminate_process(process)
            elif process.stderr is not None:
                reader = threading.Thread(
                    target=self._consume_stderr,
                    args=(identifier, process.stderr),
                    name=f"lean-events-{identifier[:8]}",
                    daemon=True,
                )
                reader.start()
            try:
                result = process.wait(timeout=self.limits.job_seconds)
            except subprocess.TimeoutExpired:
                self._terminate_process(process)
                raise ServiceError(
                    f"proof job exceeded its {self.limits.job_seconds}-second global limit"
                ) from None
            if reader is not None:
                reader.join(timeout=2.0)
            with self._changed:
                if job.cancel_requested:
                    job.status = "cancelled"
                    job.stage = "cancelled"
                elif result != 0:
                    detail = job.diagnostics[-1] if job.diagnostics else f"exit code {result}"
                    job.status = "failed"
                    job.stage = "failed"
                    job.error = _safe_text(detail)
                else:
                    if not job.verification_marker:
                        raise ServiceError(
                            "proof exporter exited without an independent Lean compilation receipt"
                        )
                    job.manifest = self._load_manifest(job)
                    self._load_live(job)
                    job.status = "completed"
                    job.stage = "complete"
                    job.lean_verified = True
                    if job.total:
                        job.completed = job.total
                job.process = None
                self._active = None
                self._touch(job)
        except (OSError, ServiceError, ValueError) as error:
            with self._changed:
                if job.cancel_requested:
                    job.status = "cancelled"
                    job.stage = "cancelled"
                else:
                    job.status = "failed"
                    job.stage = "failed"
                    job.error = _safe_text(str(error))
                    self._diagnostic(job, str(error))
                job.process = None
                self._active = None
                self._touch(job)

    def cancel(self, identifier: str) -> dict[str, Any]:
        valid = _validate_job_id(identifier)
        with self._changed:
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            if job.status in TERMINAL:
                return self._snapshot_locked(job)
            job.cancel_requested = True
            job.status = "cancelled"
            job.stage = "cancelled"
            process = job.process
            self._touch(job)
        if process is not None:
            self._terminate_process(process)
        with self._changed:
            return self._snapshot_locked(job)

    def wait_for_update(
        self,
        identifier: str,
        revision: int,
        timeout: float,
    ) -> tuple[dict[str, Any], int]:
        valid = _validate_job_id(identifier)
        with self._changed:
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            if job.revision == revision and job.status not in TERMINAL:
                self._changed.wait(timeout=max(0.0, min(timeout, 5.0)))
            return self._snapshot_locked(job), job.revision

    def _checked_job(self, identifier: str) -> JobRecord:
        valid = _validate_job_id(identifier)
        with self._changed:
            job = self._jobs.get(valid)
            if job is None:
                raise JobNotFoundError("proof job was not found or has expired")
            if job.status != "completed" or not job.lean_verified or job.manifest is None:
                raise ServiceError("only a completed independently verified proof can be downloaded")
            return job

    def lean_download(self, identifier: str) -> tuple[Path, bool]:
        job = self._checked_job(identifier)
        standalone = job.directory / "live.lean"
        if job.live_status in {"ready", "oversized"} and standalone.is_file():
            selected = standalone
            independent = True
        else:
            relative = job.manifest["relative_path"]  # type: ignore[index]
            if type(relative) is not str:
                raise ServiceError("verified proof manifest has no safe Lean module")
            selected = (job.directory / "package" / relative).resolve()
            independent = False
        root = job.directory.resolve()
        if (
            selected.is_symlink()
            or not selected.is_file()
            or not selected.is_relative_to(root)
            or selected.stat().st_size > self.limits.package_bytes
        ):
            raise ServiceError("requested Lean source escaped its bounded proof job")
        return selected, independent

    def zip_download(self, identifier: str) -> Path:
        job = self._checked_job(identifier)
        target = job.directory / "proof.zip"
        if target.is_symlink():
            raise ServiceError("proof ZIP output must not be a symbolic link")
        if target.is_file():
            if target.stat().st_size > self.limits.package_bytes:
                raise ServiceError("existing proof ZIP exceeds its reviewed size limit")
            return target
        package = (job.directory / "package").resolve()
        files: list[tuple[str, Path]] = []
        for item in package.rglob("*"):
            if item.is_symlink():
                raise ServiceError("generated Lean proof package must not contain symbolic links")
            if item.is_file() and item.suffix in {".lean", ".json"}:
                files.append((item.relative_to(package).as_posix(), item))
        live = job.directory / "live.lean"
        sidecar = job.directory / "live.json"
        if job.live_status in {"ready", "oversized"} and live.is_file() and sidecar.is_file():
            files.extend((("standalone.lean", live), ("lean-live.json", sidecar)))
        if len(files) > self.limits.package_files:
            raise ServiceError("proof ZIP exceeds its reviewed file-count limit")
        total = 0
        entries: list[tuple[str, Path]] = []
        names: set[str] = set()
        for name, source in files:
            if source.is_symlink():
                raise ServiceError("proof ZIP source must not be a symbolic link")
            resolved = source.resolve()
            if not resolved.is_relative_to(job.directory.resolve()):
                raise ServiceError("proof ZIP source escaped its bounded job")
            if not name or name.startswith("/") or "\\" in name or any(
                part in {"", ".", ".."} for part in name.split("/")
            ):
                raise ServiceError("proof ZIP contains an unsafe archive path")
            if name in names or name == "README.txt":
                raise ServiceError("proof ZIP contains colliding generated modules")
            names.add(name)
            total += resolved.stat().st_size
            if total > self.limits.package_bytes:
                raise ServiceError("proof ZIP exceeds its reviewed source-size limit")
            entries.append((name, resolved))
        manifest = job.manifest
        if manifest is None:
            raise ServiceError("verified proof archive is missing its checked manifest")
        standalone_status = (
            "PASSED; see standalone.lean"
            if job.live_status in {"ready", "oversized"}
            else "unavailable; separately installed checked Lean companion is required"
        )
        readme = (
            "HYDRA INDEPENDENTLY VERIFIED GENERATED LEAN PACKAGE\n"
            "==================================================\n\n"
            f"Theorem: {job.request.theorem}\n"
            f"Edition: {job.request.edition}\n"
            "Independent local package compilation: PASSED\n"
            f"Readable theorem nodes: {manifest['translated_node_count']}\n"
            f"Checked local certificate nodes: {manifest['fallback_node_count']}\n"
            f"Standalone core Lean verification: {standalone_status}\n"
            "Remote Lean Live compilation: NOT RUN\n\n"
            "This archive contains generated proof artifacts only. It intentionally "
            "does not publish the separately maintained private Lean companion. "
            "To recompile presentation or certificate-backed package modules, install "
            "that checked companion separately, overlay the generated PeanoLab/ tree, "
            "and review manifest.json and the final #print axioms command. "
            "When included, standalone.lean requires only the pinned core Lean toolchain.\n"
        ).encode("utf-8")
        total += len(readme)
        if total > self.limits.package_bytes:
            raise ServiceError("proof ZIP README exceeds its reviewed source-size limit")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".proof-", suffix=".zip.tmp", dir=job.directory
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, source in sorted(entries):
                    information = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    information.compress_type = zipfile.ZIP_DEFLATED
                    information.external_attr = 0o644 << 16
                    archive.writestr(information, source.read_bytes())
                information = zipfile.ZipInfo("README.txt", date_time=(1980, 1, 1, 0, 0, 0))
                information.compress_type = zipfile.ZIP_DEFLATED
                information.external_attr = 0o644 << 16
                archive.writestr(information, readme)
            if temporary.stat().st_size > self.limits.package_bytes:
                raise ServiceError("compressed proof ZIP exceeds its reviewed size limit")
            os.replace(temporary, target)
        finally:
            if temporary.is_file() and not temporary.is_symlink():
                temporary.unlink()
        return target


class LeanStrandServer(ThreadingHTTPServer):
    """Bounded proof service with optional exact-origin HTTPS proxy access."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        address: tuple[str, int],
        manager: JobManager,
        directory: Path,
        *,
        public_host: bool = False,
        public_origin: str | None = None,
        allowed_origins: tuple[str, ...] = (),
        trust_proxy: bool = False,
        api_only: bool = False,
    ) -> None:
        self.job_manager = manager
        self.static_directory = Path(directory).expanduser().resolve()
        if not self.static_directory.is_dir():
            raise ServiceError("static root must be an existing directory")
        if manager.storage.is_relative_to(self.static_directory):
            raise ServiceError("private proof-job storage must not lie beneath the public static root")
        self.public_host = public_host
        self.public_origin = (
            None if public_origin is None else _safe_origin(public_origin, label="public origin")
        )
        if allowed_origins and self.public_origin is None:
            raise ServiceError("allowed origins require an explicitly configured public origin")
        if len(allowed_origins) > MAX_ALLOWED_ORIGINS:
            raise ServiceError("too many explicitly approved proof-browser origins")
        selected = tuple(
            dict.fromkeys(
                _safe_origin(origin, label="allowed origin") for origin in allowed_origins
            )
        )
        self.allowed_origins = selected
        self.trust_proxy = trust_proxy
        self.api_only = api_only
        if trust_proxy and self.public_origin is None:
            raise ServiceError("trusted reverse proxy requires an explicitly configured public origin")
        if trust_proxy and not _loopback_hostname(address[0]):
            raise ServiceError("trusted reverse proxy requires a loopback-only service listener")
        self._request_slots = threading.BoundedSemaphore(manager.limits.concurrent_requests)
        self._constructive_authority_lock = threading.RLock()
        self._constructive_release_cache: dict[tuple[object, ...], tuple[str, str, str]] = {}
        self._constructive_manifest_cache: dict[tuple[object, ...], frozenset[str]] = {}
        super().__init__(address, LeanStrandHandler)

    @staticmethod
    def _reviewed_json(path: Path, *, maximum: int, owner: int) -> tuple[dict[str, Any], os.stat_result]:
        if path.is_symlink() or not path.is_file():
            raise ServiceError("reviewed constructive explorer artifact is unavailable")
        information = path.stat()
        if information.st_uid != owner or information.st_size > maximum:
            raise ServiceError("reviewed constructive explorer artifact has unsafe owner or size")
        payload = path.read_bytes()
        if len(payload) > maximum:
            raise ServiceError("reviewed constructive explorer artifact exceeds its bounded size")

        def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ServiceError("reviewed constructive explorer artifact repeats a JSON field")
                result[key] = value
            return result

        def reject_constant(value: str) -> None:
            raise ServiceError(f"reviewed constructive explorer artifact contains {value!r}")

        document = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=strict_object,
            parse_constant=reject_constant,
        )
        if type(document) is not dict:
            raise ServiceError("reviewed constructive explorer artifact is not a JSON object")
        return document, information

    @staticmethod
    def _fingerprint(path: Path, information: os.stat_result) -> tuple[object, ...]:
        return (
            str(path),
            information.st_dev,
            information.st_ino,
            information.st_size,
            information.st_mtime_ns,
            information.st_ctime_ns,
            information.st_mode,
            information.st_uid,
        )

    def _current_constructive_release(self, static_root: Path, *, owner: int) -> tuple[str, str, str]:
        # A present successor is authoritative even when broken: never turn an
        # invalid current release into a silently accepted historical fallback.
        # Older isolated deployments retain their original atlas and policies.
        for segment in (*CONSTRUCTIVE_RESEARCH_CAMPAIGNS, *CONSTRUCTIVE_CAMPAIGN_SUCCESSORS):
            directory = static_root / segment
            if directory.exists() or directory.is_symlink():
                if directory.is_symlink() or not directory.is_dir() or directory.stat().st_uid != owner:
                    raise ServiceError("constructive campaign directory has unsafe owner or type")
                campaign_path = directory / "campaign.json"
                break
        else:
            raise ServiceError("constructive proof browser has no reviewed campaign directory")
        campaign, campaign_info = self._reviewed_json(
            campaign_path,
            maximum=MAX_EXPLORER_CAMPAIGN_BYTES,
            owner=owner,
        )
        if campaign.get("schema") != "constructive-grand-campaign-v1":
            raise ServiceError("constructive proof browser has no reviewed campaign schema")
        metadata = campaign.get("meta")
        if type(metadata) is not dict:
            raise ServiceError("constructive proof browser has no reviewed release metadata")
        version = metadata.get("current_alpha_version")
        if type(version) is not str or CONSTRUCTIVE_RELEASE_VERSION.fullmatch(version) is None:
            raise ServiceError("constructive proof browser has no safe current Alpha release")
        if (directory.name in CONSTRUCTIVE_RESEARCH_CAMPAIGNS
                and version != CONSTRUCTIVE_RESEARCH_CAMPAIGNS[directory.name]):
            raise ServiceError("the present research campaign cannot downgrade to a historical release")
        if directory.name == "constructive-completed-lower-campaign-v31" and version != "v31":
            raise ServiceError("the present v31 campaign cannot downgrade to a historical release")
        boundaries = campaign.get("ambitious_boundaries")
        release = boundaries.get(f"alpha_{version}_edition") if type(boundaries) is dict else None
        if type(release) is not dict or release.get("role") != "current_immutable_release":
            raise ServiceError("constructive proof browser has no current immutable Alpha release")
        digest = release.get("catalog_sha256")
        identity = release.get("identity_sha256")
        count = release.get("theorem_count")
        if (
            type(digest) is not str
            or SHA256.fullmatch(digest) is None
            or type(identity) is not str
            or SHA256.fullmatch(identity) is None
            or type(count) is not int
            or count < 1
            or release.get("checked_use_count") != count
            or metadata.get("current_alpha_checked_use_count") != count
        ):
            raise ServiceError("constructive proof browser has no complete checked-use release")

        roots = tuple(dict.fromkeys((self.static_directory, ROOT)))
        for repository in roots:
            channel_path = repository / "artifacts" / "peano-library" / f"channels-{version}.json"
            catalog_path = repository / "artifacts" / "peano-library" / "alpha" / f"catalog-{version}.json"
            if channel_path.is_file() and catalog_path.is_file():
                break
        else:
            raise ServiceError("constructive proof browser cannot find its sealed release channel")
        if catalog_path.is_symlink() or not catalog_path.is_file():
            raise ServiceError("constructive proof browser catalog is not an ordinary sealed artifact")
        catalog_info = catalog_path.stat()
        if catalog_info.st_uid != owner or catalog_info.st_size > MAX_EXPLORER_CATALOG_BYTES:
            raise ServiceError("constructive proof browser catalog has unsafe owner or size")
        channels, channel_info = self._reviewed_json(
            channel_path,
            maximum=MAX_EXPLORER_CAMPAIGN_BYTES,
            owner=owner,
        )
        if version in {"v32", "v33"} and channels.get("default_channel") != "stable":
            raise ServiceError("the current research release changed the default Stable channel")
        shard_fingerprint = ()
        codec = None
        if version in CONSTRUCTIVE_CATALOG_CODECS:
            # A manifest digest does not authenticate its referenced rows.
            # All three immutable files participate in cache invalidation;
            # the codec does no proof loading and retains the 64 MiB/file cap.
            try:
                codec = import_module(CONSTRUCTIVE_CATALOG_CODECS[version])
                shard_fingerprint = codec.catalog_input_fingerprint(
                    catalog_path, expected_sha256=digest, owner_uid=owner,
                )
            except (ImportError, OSError, ValueError) as error:
                raise ServiceError("constructive sharded catalogue binding is invalid") from error
        key = (
            self._fingerprint(campaign_path, campaign_info),
            self._fingerprint(channel_path, channel_info),
            self._fingerprint(catalog_path, catalog_info),
            shard_fingerprint,
        )
        with self._constructive_authority_lock:
            cached = self._constructive_release_cache.get(key)
            if cached is not None:
                return cached
            if channels.get("schema") != f"peano-library-channels-{version}":
                raise ServiceError("constructive proof browser has a stale release channel")
            channel_map = channels.get("channels")
            channel = channel_map.get("alpha") if type(channel_map) is dict else None
            expected_path = f"artifacts/peano-library/alpha/catalog-{version}.json"
            if (
                type(channel) is not dict
                or channel.get("artifact_path") != expected_path
                or channel.get("artifact_sha256") != digest
                or channel.get("edition_identity_sha256") != identity
                or channel.get("theorem_count") != count
                or channel.get("checked_use_count") != count
            ):
                raise ServiceError("constructive proof browser channel disagrees with its current release")
            if codec is not None:
                try:
                    bindings = codec.verify_catalog_bindings(catalog_path, expected_sha256=digest, owner_uid=owner)
                    if bindings.fingerprint != shard_fingerprint:
                        raise ValueError("catalogue inputs changed during authorization")
                    manifest, _ = self._reviewed_json(catalog_path, maximum=MAX_EXPLORER_CATALOG_BYTES, owner=owner)
                    header = manifest.get("metadata", {})
                    if (header.get("edition_identity_sha256") != identity
                            or type(header.get("theorem_count")) is not int or header["theorem_count"] != count
                            or type(header.get("checked_use_count")) is not int or header["checked_use_count"] != count):
                        raise ValueError("catalogue manifest disagrees with the actual current release")
                except (OSError, ValueError) as error:
                    raise ServiceError("constructive sharded catalogue differs from its sealed data") from error
            else:
                actual = sha256()
                observed = 0
                with catalog_path.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        observed += len(chunk)
                        if observed > MAX_EXPLORER_CATALOG_BYTES:
                            raise ServiceError("constructive proof browser catalog exceeds its safe size")
                        actual.update(chunk)
                if actual.hexdigest() != digest:
                    raise ServiceError("constructive proof browser catalog differs from its sealed digest")
            result = (version, digest, identity)
            if len(self._constructive_release_cache) >= 16:
                self._constructive_release_cache.clear()
            self._constructive_release_cache[key] = result
            return result

    def _historical_v31_provenance(self, directory: Path, manifest: dict, *, owner: int) -> None:
        """Authenticate exact mixed first admissions, including their full rows.

        The small manifest carries literal per-family descriptors; their
        complete historical per-theorem records live in bounded sidecars.
        Recheck these bytes even on a warm family cache. They establish honest
        provenance, not permission to bypass an actual theorem proof.
        """
        entries = manifest.get("families")
        if type(entries) is not list or len(entries) != 44:
            raise ServiceError("historical v31 publication has an incomplete family inventory")
        names = set()
        for family in entries:
            if type(family) is not dict:
                raise ServiceError("malformed historical first-admission family")
            name = family.get("slug")
            descriptor = family.get("first_admission")
            if (type(name) is not str or name not in HISTORICAL_V31_FIRST_ADMISSIONS
                    or name in names or type(descriptor) is not dict):
                raise ServiceError("unreviewed or duplicate historical first admission")
            names.add(name)
            encoded = json.dumps(descriptor, ensure_ascii=False, allow_nan=False,
                                 sort_keys=True, separators=(",", ":")).encode("utf-8")
            if sha256(encoded).hexdigest() != HISTORICAL_V31_FIRST_ADMISSIONS[name]:
                raise ServiceError("literal historical first-admission descriptor changed")
            records = descriptor.get("per_theorem_records")
            if (type(records) is not dict or set(records) != {"path", "bytes", "sha256"}
                    or records["path"] != name + "/api/first-admission.json"
                    or type(records["bytes"]) is not int
                    or not 0 < records["bytes"] <= MAX_EXPLORER_MANIFEST_BYTES):
                raise ServiceError("unsafe historical first-admission sidecar binding")
            parent = directory
            for component in (name, "api"):
                parent /= component
                if parent.is_symlink() or not parent.is_dir() or parent.stat().st_uid != owner:
                    raise ServiceError("unsafe historical first-admission directory")
            path = parent / "first-admission.json"
            if path.is_symlink() or not path.is_file():
                raise ServiceError("historical first-admission rows are unavailable")
            information = path.stat()
            if information.st_uid != owner or information.st_size != records["bytes"]:
                raise ServiceError("historical first-admission rows have unsafe owner or size")
            with path.open("rb") as stream:
                raw = stream.read(records["bytes"] + 1)
            if len(raw) != records["bytes"] or sha256(raw).hexdigest() != records["sha256"]:
                raise ServiceError("literal historical first-admission rows changed")

    def _modern_constructive_provenance(self, directory: Path, manifest: dict, *, owner: int) -> None:
        """Review current labels and literal history, never theorem authority."""
        phase = CONSTRUCTIVE_MODERN_PHASES[directory.name]
        policy = CONSTRUCTIVE_PUBLICATIONS[directory.name]
        expected_counts = CONSTRUCTIVE_MODERN_COUNTS[phase]
        if (manifest.get("phase") != phase
                or manifest.get("publication_scope") != "alpha_checked_use_publication"
                or manifest.get("alpha_first_enrolled_version") != policy.first_enrolled_version
                or "first_enrollment_catalog_sha256" in manifest
                or type(manifest.get("alpha_edition_checked_use_count")) is not int
                or manifest["alpha_edition_checked_use_count"] != {"v32": 3971, "v33": 4092}[policy.current_version]
                or type(manifest.get("stable_edition_count")) is not int or manifest["stable_edition_count"] != 432
                or manifest.get("current_G009_multiplicative_closure_proved") is not True
                or manifest.get("current_G091_prime_power_fields_proved") is not False
                or any(type(manifest.get(key)) is not int or manifest[key] != count
                       for key, count in zip(("theorem_count", "checked_use_count", "stable_count"), expected_counts, strict=True))):
            raise ServiceError("modern reader changed its exact phase, counts or first admission")
        entries = manifest.get("families")
        expected_names = (set(COMPLETED_LOWER_V31_FAMILIES) if phase == "completed"
                          else set(HISTORICAL_V31_FIRST_ADMISSIONS) if phase == "historical"
                          else {"multiplicative-convolution", "polynomial-division-prerequisites"} if phase == "research"
                          else {"polynomial-euclidean-division"})
        if (type(entries) is not list or len(entries) != len(expected_names)
                or any(type(row) is not dict for row in entries)
                or any(type(row.get("slug")) is not str for row in entries)
                or {row.get("slug") for row in entries} != expected_names):
            raise ServiceError("modern reader has a missing, repeated or foreign family")
        for row in entries:
            if row.get("package") != directory.name:
                raise ServiceError("modern family claims a foreign reader package")
            if phase != "historical":
                name = row["slug"]
                count = (COMPLETED_LOWER_V31_FAMILIES[name] if phase == "completed"
                         else CONSTRUCTIVE_MODERN_NEW_FAMILIES[name][0])
                if (row.get("first_admitted_version") != policy.first_enrolled_version
                        or any(type(row.get(key)) is not int or row[key] != expected
                               for key, expected in (("theorem_count", count), ("checked_use_count", count), ("stable_count", 0)))):
                    raise ServiceError("modern family changed its checked count or admission history")
                tags = row.get("tags")
                if (type(tags) is not dict or len(tags) != count
                        or any(type(name) is not str or THEOREM_NAME.fullmatch(name) is None
                               or type(tag) is not str for name, tag in tags.items())
                        or len(set(tags.values())) != count):
                    raise ServiceError("modern family has missing or ambiguous theorem tags")
                if phase in {"research", "polynomial"}:
                    _count, prefix, first, expected = CONSTRUCTIVE_MODERN_NEW_FAMILIES[name]
                    ordered = "\n".join(name for name, _tag in sorted(tags.items(), key=lambda item: item[1]))
                    if (first != policy.first_enrolled_version
                            or set(tags.values()) != {f"{prefix}{index:04X}" for index in range(1, count + 1)}
                            or sha256(ordered.encode()).hexdigest() != expected):
                        raise ServiceError("the exact research theorem names or stable tags changed")
        predecessor = CONSTRUCTIVE_MODERN_PARENTS.get(directory.name)
        if predecessor is None:
            if "historical_parent" in manifest:
                raise ServiceError("first admission invented a historical reader parent")
            return
        name, size, expected = predecessor
        record = {"directory": name, "bytes": size, "sha256": expected}
        relative = "historical/" + name + "/manifest.json"
        if (manifest.get("historical_parent") != record
                or type(manifest.get("files")) is not dict
                or manifest["files"].get(relative) != {"bytes": size, "sha256": expected}):
            raise ServiceError("modern reader lost its exact historical manifest binding")
        path = directory
        ancestors = []
        for part in ("historical", name):
            path /= part
            info = path.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != owner:
                raise ServiceError("unsafe historical manifest directory")
            ancestors.append((path, (info.st_dev, info.st_ino, info.st_mode, info.st_uid)))
        path /= "manifest.json"
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_uid != owner or before.st_size != size or size > MAX_EXPLORER_MANIFEST_BYTES:
            raise ServiceError("historical manifest is not its exact bounded ordinary file")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            if self._fingerprint(path, os.fstat(stream.fileno())) != self._fingerprint(path, before):
                raise ServiceError("historical manifest changed while opening")
            raw = stream.read(size + 1)
            after = os.fstat(stream.fileno())
        if (self._fingerprint(path, before) != self._fingerprint(path, after)
                or self._fingerprint(path, after) != self._fingerprint(path, path.lstat())
                or len(raw) != size or sha256(raw).hexdigest() != expected):
            raise ServiceError("literal historical manifest bytes changed")
        for parent, identity in ancestors:
            info = parent.lstat()
            if (info.st_dev, info.st_ino, info.st_mode, info.st_uid) != identity:
                raise ServiceError("historical manifest ancestor changed")
        # These bytes are a literal registered JSON document, not a supplied
        # proof report.  Only the current package route is changed in its rows.
        old = json.loads(raw.decode("utf-8"))
        inherited = []
        for row in old["families"]:
            item = {**row, "package": directory.name}
            if directory.name == "constructive-completed-lower-explorer-v32":
                item.update(checked_use_count=row["theorem_count"], stable_count=0, first_admitted_version="v31")
            inherited.append(item)
        if entries != inherited:
            raise ServiceError("current reader rewrote a literal historical family identity")

    def reviewed_constructive_family(self, directory: Path, slug: str) -> bool:
        """Authorize one real family only under the current sealed checked release."""

        try:
            if (
                not isinstance(directory, Path)
                or directory.is_symlink()
                or not directory.is_dir()
                or not directory.resolve().is_relative_to(self.static_directory)
                or not _constructive_explorer_segment(directory.name)
                or type(slug) is not str
                or CONSTRUCTIVE_FAMILY_SLUG.fullmatch(slug) is None
            ):
                return False
            owner = directory.stat().st_uid
            static_root = directory.parent
            if static_root.name != "_static" or static_root.stat().st_uid != owner:
                return False
            version, digest, identity = self._current_constructive_release(static_root, owner=owner)
            manifest_path = directory / "manifest.json"
            manifest, information = self._reviewed_json(
                manifest_path,
                maximum=MAX_EXPLORER_MANIFEST_BYTES,
                owner=owner,
            )
            modern_phase = CONSTRUCTIVE_MODERN_PHASES.get(directory.name)
            if directory.name == "constructive-historical-explorers-v31" or modern_phase == "historical":
                self._historical_v31_provenance(directory, manifest, owner=owner)
            if modern_phase is not None:
                self._modern_constructive_provenance(directory, manifest, owner=owner)
            key = (self._fingerprint(manifest_path, information), version, digest, identity)
            with self._constructive_authority_lock:
                families = self._constructive_manifest_cache.get(key)
                if families is None:
                    expected_schema = f"peano-lab-{directory.name}-v1"
                    publication = CONSTRUCTIVE_PUBLICATIONS.get(directory.name)
                    schemas = (
                        {publication.schema}
                        if publication is not None
                        else {expected_schema, expected_schema + "-manifest"}
                    )
                    if (
                        manifest.get("schema") not in schemas
                        or manifest.get("alpha_edition_version") != version
                        or (manifest.get("catalog_sha256") or manifest.get("alpha_catalog_sha256"))
                        != digest
                        or (
                            manifest.get("edition_identity_sha256")
                            or manifest.get("alpha_edition_identity_sha256")
                        )
                        != identity
                    ):
                        return False
                    if publication is not None:
                        if (version != publication.current_version
                                or manifest.get("alpha_first_enrolled_version") != publication.first_enrolled_version):
                            return False
                        if modern_phase is not None:
                            # The canonical schema binds heterogeneous literal
                            # first admissions above, not a fictitious scalar
                            # first-catalog field copied from the current one.
                            pass
                        elif publication.first_enrolled_version == "mixed_preserved":
                            # This one reviewed aggregate has heterogeneous
                            # literal history; a scalar first-catalog claim
                            # would be false even when the current digest fits.
                            if "first_enrollment_catalog_sha256" in manifest:
                                return False
                        elif manifest.get("first_enrollment_catalog_sha256") != (publication.first_catalog_sha256 or digest):
                            return False
                    entries = manifest.get("families")
                    if type(entries) is not list or not 1 <= len(entries) <= MAX_EXPLORER_FAMILIES:
                        return False
                    names: set[str] = set()
                    for family in entries:
                        if type(family) is not dict:
                            return False
                        name = family.get("slug")
                        if (
                            type(name) is not str
                            or CONSTRUCTIVE_FAMILY_SLUG.fullmatch(name) is None
                            or name in names
                        ):
                            return False
                        checked = family.get("alpha_checked_use_node_count", family.get("theorem_count"))
                        if type(checked) is not int or checked < 1:
                            return False
                        if ((directory.name == "constructive-completed-lower-explorer-v31" or modern_phase == "completed")
                                and checked != COMPLETED_LOWER_V31_FAMILIES.get(name)):
                            return False
                        family_version = family.get("alpha_edition_version")
                        if family_version is not None and family_version != version:
                            return False
                        if directory.name == "constructive-historical-explorers-v31" or modern_phase == "historical":
                            descriptor = family.get("first_admission")
                            if type(descriptor) is not dict or name not in HISTORICAL_V31_FIRST_ADMISSIONS:
                                return False
                            encoded = json.dumps(descriptor, ensure_ascii=False, allow_nan=False,
                                                 sort_keys=True, separators=(",", ":")).encode("utf-8")
                            if sha256(encoded).hexdigest() != HISTORICAL_V31_FIRST_ADMISSIONS[name]:
                                return False
                        names.add(name)
                    if ((directory.name == "constructive-historical-explorers-v31" or modern_phase == "historical")
                            and names != set(HISTORICAL_V31_FIRST_ADMISSIONS)):
                        return False
                    if ((directory.name == "constructive-completed-lower-explorer-v31" or modern_phase == "completed")
                            and names != set(COMPLETED_LOWER_V31_FAMILIES)):
                        return False
                    families = frozenset(names)
                    if len(self._constructive_manifest_cache) >= 64:
                        self._constructive_manifest_cache.clear()
                    self._constructive_manifest_cache[key] = families
                return slug in families
        except (OSError, UnicodeError, ValueError, ServiceError, RecursionError):
            return False

    def process_request(self, request: Any, client_address: Any) -> None:
        if not self._request_slots.acquire(blocking=False):
            try:
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"Connection: close\r\nContent-Length: 0\r\n\r\n"
                )
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._request_slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._request_slots.release()


class LeanStrandHandler(BaseHTTPRequestHandler):
    """Minimal safe static routes and one authenticated-by-compilation job API."""

    server: LeanStrandServer
    server_version = "HydraLeanStrands/1"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10.0)

    def _headers(self, kind: str, size: int, *, download: str | None = None) -> None:
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        approved = self._cors_origin()
        self.send_header(
            "Cross-Origin-Resource-Policy", "cross-origin" if approved else "same-origin"
        )
        if approved is not None:
            self._cors_headers(approved)
        if download is not None:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')

    def _cors_origin(self) -> str | None:
        """Return only an exact, explicitly approved cross-origin API caller."""

        if self.server.public_origin is None or self._api_parts() is None:
            return None
        origin = self.headers.get("Origin")
        if origin is None:
            return None
        try:
            selected = _safe_origin(origin, label="request origin")
        except ServiceError:
            return None
        if selected not in self.server.allowed_origins:
            return None
        return selected

    def _cors_headers(self, origin: str) -> None:
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Expose-Headers", "Content-Disposition, Content-Length")

    def _json(self, status: HTTPStatus, payload: object, *, head_only: bool = False) -> None:
        try:
            content = _bounded_json(payload, maximum=self.server.job_manager.limits.response_bytes)
        except ServiceError:
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            content = b'{"error":"response exceeded its reviewed size limit"}\n'
        self.send_response(status)
        self._headers("application/json; charset=utf-8", len(content))
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def _failure(self, status: HTTPStatus, message: str) -> None:
        self._json(status, {"schema": JOB_SCHEMA, "error": _safe_text(message)})

    def _same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        try:
            actual = _safe_origin(origin, label="request origin")
        except ServiceError:
            return False
        if self.server.public_origin is not None:
            if actual == self.server.public_origin or actual in self.server.allowed_origins:
                return True
        expected = _safe_host_header(self.headers.get("Host", ""))
        return expected is not None and urlsplit(actual).netloc == expected

    def _host_allowed(self) -> bool:
        host = _safe_host_header(self.headers.get("Host", ""))
        if host is None:
            return False
        expected = {
            f"127.0.0.1:{self.server.server_port}",
            f"localhost:{self.server.server_port}",
            f"[::1]:{self.server.server_port}",
        }
        public_host = (
            None
            if self.server.public_origin is None
            else urlsplit(self.server.public_origin).netloc
        )
        if self.server.public_origin is not None:
            if host not in expected and host != public_host:
                return False
        elif not self.server.public_host:
            return host in expected
        if not self.server.trust_proxy:
            return True
        if not _loopback_hostname(self.client_address[0]):
            return False
        forwarded_host = self.headers.get("X-Forwarded-Host")
        forwarded_scheme = self.headers.get("X-Forwarded-Proto")
        if forwarded_host is None and forwarded_scheme is None and host in expected:
            return True
        if forwarded_scheme != urlsplit(self.server.public_origin).scheme:
            return False
        if forwarded_host is not None and _safe_host_header(forwarded_host) != public_host:
            return False
        return host == public_host or forwarded_host is not None

    def _client_identity(self) -> str:
        """Trust forwarded client identity only on an explicit loopback proxy."""

        direct = self.client_address[0]
        if not self.server.trust_proxy or not _loopback_hostname(direct):
            return direct
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded is None:
            return direct
        if len(forwarded) > 1024:
            raise ServiceError("trusted proxy client chain exceeds its reviewed limit")
        hops = [part.strip() for part in forwarded.split(",")]
        if not hops or len(hops) > MAX_FORWARDED_HOPS or not hops[-1]:
            raise ServiceError("trusted proxy supplied an invalid client address")
        try:
            return str(ipaddress.ip_address(hops[-1]))
        except ValueError as error:
            raise ServiceError("trusted proxy supplied an invalid client address") from error

    def _request_payload(self) -> object:
        if not self._same_origin():
            raise PermissionError("cross-origin proof mutation is forbidden")
        if self.headers.get("Transfer-Encoding") is not None:
            raise ServiceError("chunked proof-job requests are not supported")
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            raise ServiceError("proof-job requests require application/json")
        raw = self.headers.get("Content-Length")
        if raw is None or not raw.isdecimal():
            raise ServiceError("proof-job requests require an exact Content-Length")
        size = int(raw)
        if not 1 <= size <= self.server.job_manager.limits.request_bytes:
            raise ServiceError("proof-job request exceeds its reviewed size limit")
        try:
            return json.loads(self.rfile.read(size).decode("utf-8"))
        except (UnicodeError, TypeError, ValueError) as error:
            raise ServiceError("proof-job body is not valid UTF-8 JSON") from error

    def _api_parts(self) -> tuple[str, ...] | None:
        try:
            parsed = urlsplit(self.path)
        except ValueError:
            return None
        path = parsed.path
        if path == API_PREFIX:
            return ()
        if not path.startswith(API_PREFIX + "/"):
            return None
        tail = path[len(API_PREFIX) + 1:]
        if not tail or any(part in {"", ".", ".."} for part in tail.split("/")):
            return None
        return tuple(tail.split("/"))

    def _static_path(self) -> tuple[Path, tuple[str, ...]]:
        try:
            raw = urlsplit(self.path).path
            decoded = unquote(raw, errors="strict")
        except (UnicodeError, ValueError) as error:
            raise PermissionError("unsafe static path encoding") from error
        if "\x00" in decoded or "\\" in decoded:
            raise PermissionError("unsafe static path characters")
        parts = tuple(part for part in decoded.split("/") if part)
        if any(
            part in {".", ".."}
            or part.startswith(".")
            or part.lower() in SENSITIVE_NAMES
            or Path(part).suffix.lower() in SENSITIVE_SUFFIXES
            for part in parts
        ):
            raise PermissionError("private repository or credential paths are unavailable")
        candidate = self.server.static_directory.joinpath(*parts).resolve()
        if not candidate.is_relative_to(self.server.static_directory):
            raise PermissionError("static path escapes its configured root")
        if candidate.is_dir():
            candidate = (candidate / "index.html").resolve()
            if not candidate.is_file():
                raise PermissionError("directory listings are disabled")
        if not candidate.is_file():
            raise FileNotFoundError("static resource not found")
        if candidate.stat().st_size > self.server.job_manager.limits.static_bytes:
            raise ServiceError("static resource exceeds its reviewed byte limit")
        return candidate, parts

    def _asset_prefix(self) -> str | None:
        base = self.server.static_directory
        for relative in (
            Path("book/_static/lean-selector"),
            Path("_static/lean-selector"),
            Path("lean-selector"),
        ):
            candidate = (base / relative).resolve()
            if (
                candidate.is_relative_to(base)
                and (candidate / "lean-selector.js").is_file()
                and (candidate / "lean-selector.css").is_file()
            ):
                return "/" + relative.as_posix()
        return None

    def _reviewed_constructive_request(self, path: Path, parts: tuple[str, ...]) -> bool:
        candidates = [
            (index, part)
            for index, part in enumerate(parts)
            if _constructive_explorer_candidate(part)
        ]
        if len(candidates) != 1:
            return False
        index, segment = candidates[0]
        if (
            index == 0
            or parts[index - 1] != "_static"
            or not _constructive_explorer_segment(segment)
        ):
            return False
        trailing = parts[index + 1 :]
        if len(trailing) < 3:
            return False
        slug, suffix = trailing[0], trailing[1:]
        reviewed_shapes = {
            ("explorer", "graph.html"),
            ("explorer", "defined", "graph.html"),
            ("explorer", "tag", path.name),
            ("explorer", "defined", "tag", path.name),
        }
        if suffix not in reviewed_shapes:
            return False
        directory = self.server.static_directory.joinpath(*parts[: index + 1])
        return self.server.reviewed_constructive_family(directory, slug)

    def _inject_selector(self, path: Path, parts: tuple[str, ...]) -> bytes | None:
        if (
            path.suffix.lower() != ".html"
            or path.stat().st_size > self.server.job_manager.limits.html_bytes
        ):
            return None
        constructive = any(_constructive_explorer_candidate(part) for part in parts)
        if constructive:
            eligible = self._reviewed_constructive_request(path, parts)
        else:
            eligible = (
                (path.name == "graph.html" and "_static" in parts)
                or bool(LEGACY_EXPLORER_SEGMENTS.intersection(parts))
            )
        if not eligible:
            return None
        prefix = self._asset_prefix()
        if prefix is None:
            return None
        content = path.read_bytes()
        marker = b"lean-selector.js"
        if marker in content:
            return content
        closing = re.search(rb"</head\s*>", content, flags=re.IGNORECASE)
        if closing is None:
            return content
        insertion = (
            f'<link rel="stylesheet" href="{prefix}/lean-selector.css">\n'
            f'<script defer src="{prefix}/lean-selector.js"></script>\n'
        ).encode("utf-8")
        return content[:closing.start()] + insertion + content[closing.start():]

    def _serve_static(self, *, head_only: bool) -> None:
        try:
            source, parts = self._static_path()
            injected = self._inject_selector(source, parts)
        except PermissionError as error:
            self._failure(HTTPStatus.FORBIDDEN, str(error))
            return
        except FileNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        except (OSError, ServiceError) as error:
            self._failure(HTTPStatus.BAD_REQUEST, str(error))
            return
        content_type = mimetypes.guess_type(str(source))[0] or "application/octet-stream"
        if content_type.startswith(("text/", "application/javascript")):
            content_type += "; charset=utf-8"
        length = len(injected) if injected is not None else source.stat().st_size
        self.send_response(HTTPStatus.OK)
        self._headers(content_type, length)
        self.end_headers()
        if head_only:
            return
        if injected is not None:
            self.wfile.write(injected)
            return
        with source.open("rb") as stream:
            shutil.copyfileobj(stream, self.wfile, length=65_536)

    def _download(self, identifier: str, *, head_only: bool) -> None:
        try:
            query = parse_qs(urlsplit(self.path).query, strict_parsing=True)
        except ValueError:
            self._failure(HTTPStatus.BAD_REQUEST, "invalid proof-download query")
            return
        if set(query) != {"format"} or len(query["format"]) != 1:
            self._failure(HTTPStatus.BAD_REQUEST, "proof download needs exactly one format")
            return
        style = query["format"][0]
        try:
            if style == "lean":
                source, standalone = self.server.job_manager.lean_download(identifier)
                filename = (
                    "readable-standalone.lean" if standalone else "verified-proof-strand.lean"
                )
                kind = "text/plain; charset=utf-8"
            elif style == "zip":
                source = self.server.job_manager.zip_download(identifier)
                filename = "verified-lean-proof.zip"
                kind = "application/zip"
            else:
                raise ServiceError("proof download format must be exactly lean or zip")
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        except ServiceError as error:
            self._failure(HTTPStatus.CONFLICT, str(error))
            return
        self.send_response(HTTPStatus.OK)
        self._headers(kind, source.stat().st_size, download=filename)
        self.end_headers()
        if not head_only:
            with source.open("rb") as stream:
                shutil.copyfileobj(stream, self.wfile, length=65_536)

    def _events(self, identifier: str) -> None:
        try:
            snapshot = self.server.job_manager.snapshot(identifier)
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        approved = self._cors_origin()
        if approved is not None:
            self._cors_headers(approved)
        self.end_headers()
        revision = -1
        try:
            while True:
                snapshot, revision = self.server.job_manager.wait_for_update(
                    identifier,
                    revision,
                    2.0,
                )
                encoded = _bounded_json(
                    snapshot,
                    maximum=self.server.job_manager.limits.response_bytes,
                ).rstrip(b"\n")
                self.wfile.write(b"event: status\ndata: " + encoded + b"\n\n")
                self.wfile.flush()
                if snapshot["status"] in TERMINAL:
                    return
        except (BrokenPipeError, ConnectionError, JobNotFoundError, OSError, ServiceError):
            return

    def _get(self, *, head_only: bool) -> None:
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            if self.server.api_only:
                self._failure(HTTPStatus.NOT_FOUND, "static proof-browser hosting is disabled")
                return
            prefix = "/book" if (self.server.static_directory / "book/_static").is_dir() else ""
            location = f"{prefix}/_static/pa-proof-explorer/defined/graph.html?target=PA000F"
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self._headers("text/plain; charset=utf-8", 0)
            self.end_headers()
            return
        if parsed.path in {"/health", "/healthz"}:
            self._json(HTTPStatus.OK, {"status": "ok", "schema": JOB_SCHEMA}, head_only=head_only)
            return
        parts = self._api_parts()
        if parts is None:
            if self.server.api_only:
                self._failure(HTTPStatus.NOT_FOUND, "static proof-browser hosting is disabled")
                return
            self._serve_static(head_only=head_only)
            return
        if not self._same_origin():
            self._failure(HTTPStatus.FORBIDDEN, "unapproved proof-browser origin")
            return
        if parts in {("health",), ("healthz",)}:
            self._json(HTTPStatus.OK, {"status": "ok", "schema": JOB_SCHEMA}, head_only=head_only)
            return
        if parts == ("config",):
            limits = self.server.job_manager.limits
            self._json(
                HTTPStatus.OK,
                {
                    "schema": JOB_SCHEMA,
                    "public_host": self.server.public_host,
                    "public_origin": self.server.public_origin,
                    "allowed_origins": list(self.server.allowed_origins),
                    "trusted_proxy": self.server.trust_proxy,
                    "api_only": self.server.api_only,
                    "api_root": (
                        self.server.public_origin + API_PREFIX
                        if self.server.public_origin is not None
                        else API_PREFIX
                    ),
                    "single_worker": True,
                    "max_concurrent_jobs": 1,
                    "independent_lean_verification": True,
                    "max_memory_mib": limits.memory_mib,
                    "memory_mib": limits.memory_mib,
                    "max_verify_seconds": limits.verify_seconds,
                    "max_strand_nodes": limits.strand_nodes,
                    "max_nodes": limits.strand_nodes,
                    "max_chunk_kib": limits.chunk_kib,
                    "max_live_url_bytes": limits.live_url_bytes,
                    "max_live_source_bytes": limits.live_source_bytes,
                },
                head_only=head_only,
            )
            return
        if len(parts) not in {2, 3} or parts[0] != "jobs":
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        if len(parts) == 3:
            if parts[2] == "download":
                self._download(parts[1], head_only=head_only)
            elif parts[2] == "events" and not head_only:
                self._events(parts[1])
            else:
                self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        try:
            snapshot = self.server.job_manager.snapshot(parts[1])
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        self._json(HTTPStatus.OK, snapshot, head_only=head_only)

    def do_GET(self) -> None:  # noqa: N802
        self._get(head_only=False)

    def do_HEAD(self) -> None:  # noqa: N802
        self._get(head_only=True)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        if self._api_parts() is None:
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        approved = self._cors_origin()
        if approved is None:
            self._failure(HTTPStatus.FORBIDDEN, "unapproved proof-browser origin")
            return
        method = self.headers.get("Access-Control-Request-Method", "").upper()
        if method not in {"GET", "HEAD", "POST", "DELETE"}:
            self._failure(HTTPStatus.FORBIDDEN, "unapproved cross-origin proof method")
            return
        requested = self.headers.get("Access-Control-Request-Headers", "")
        headers = tuple(part.strip().lower() for part in requested.split(",") if part.strip())
        if any(header not in {"accept", "content-type"} for header in headers):
            self._failure(HTTPStatus.FORBIDDEN, "unapproved cross-origin proof header")
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._headers("text/plain; charset=utf-8", 0)
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        if self._api_parts() != ("jobs",):
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        try:
            payload = self._request_payload()
            self.server.job_manager.check_mutation_rate(self._client_identity())
            snapshot = self.server.job_manager.submit(payload)
        except PermissionError as error:
            self._failure(HTTPStatus.FORBIDDEN, str(error))
            return
        except JobRateLimitError as error:
            self._failure(HTTPStatus.TOO_MANY_REQUESTS, str(error))
            return
        except JobBusyError as error:
            self._failure(HTTPStatus.CONFLICT, str(error))
            return
        except ServiceError as error:
            self._failure(HTTPStatus.BAD_REQUEST, str(error))
            return
        self._json(HTTPStatus.ACCEPTED, snapshot)

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._host_allowed():
            self._failure(HTTPStatus.MISDIRECTED_REQUEST, "request Host is not permitted")
            return
        if not self._same_origin():
            self._failure(HTTPStatus.FORBIDDEN, "cross-origin proof cancellation is forbidden")
            return
        parts = self._api_parts()
        if parts is None or len(parts) != 2 or parts[0] != "jobs":
            self._failure(HTTPStatus.NOT_FOUND, "unknown proof-service endpoint")
            return
        try:
            self.server.job_manager.check_mutation_rate(self._client_identity())
            snapshot = self.server.job_manager.cancel(parts[1])
        except JobRateLimitError as error:
            self._failure(HTTPStatus.TOO_MANY_REQUESTS, str(error))
            return
        except JobNotFoundError as error:
            self._failure(HTTPStatus.NOT_FOUND, str(error))
            return
        except ServiceError as error:
            self._failure(HTTPStatus.BAD_REQUEST, str(error))
            return
        self._json(HTTPStatus.OK, snapshot)

    def do_PUT(self) -> None:  # noqa: N802
        self._failure(HTTPStatus.METHOD_NOT_ALLOWED, "proof service does not support PUT")

    def do_PATCH(self) -> None:  # noqa: N802
        self._failure(HTTPStatus.METHOD_NOT_ALLOWED, "proof service does not support PATCH")

    def log_message(self, template: str, *arguments: object) -> None:
        sys.stderr.write("  " + _safe_text(template % arguments, maximum=1_024) + "\n")


def _safe_bind_host(host: str, *, public_host: bool) -> str:
    if type(host) is not str or not host or any(char.isspace() for char in host):
        raise ServiceError("listen host must be nonempty safe text")
    if not _loopback_hostname(host) and not public_host:
        raise ServiceError("non-loopback exposure requires explicit --public-host")
    return host


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--public-host", action="store_true")
    parser.add_argument(
        "--public-origin",
        help="exact external HTTPS service origin behind an approved reverse proxy",
    )
    parser.add_argument(
        "--allowed-origin",
        "--allow-origin",
        dest="allowed_origins",
        action="append",
        default=[],
        help="exact HTTPS theorem-browser origin allowed to call this proof API",
    )
    parser.add_argument(
        "--trust-proxy",
        action="store_true",
        help="trust HTTPS forwarding headers only from an explicit loopback reverse proxy",
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="serve only bounded proof API and health endpoints; expose no static files",
    )
    parser.add_argument("--directory", type=Path, default=ROOT)
    parser.add_argument("--storage", type=Path)
    parser.add_argument("--max-memory-mib", type=int, default=1_024)
    parser.add_argument("--max-verify-seconds", type=int, default=180)
    parser.add_argument("--max-job-seconds", type=int, default=240)
    parser.add_argument("--job-ttl-seconds", type=int, default=900)
    parser.add_argument("--max-jobs", type=int, default=32)
    parser.add_argument("--max-strand-nodes", type=int, default=DEFAULT_STRAND_NODES)
    parser.add_argument("--max-chunk-kib", type=int, default=192)
    parser.add_argument("--max-live-url-bytes", type=int, default=DEFAULT_LIVE_URL_BYTES)
    parser.add_argument("--max-live-source-kib", type=int, default=DEFAULT_LIVE_SOURCE_BYTES // 1024)
    parser.add_argument("--max-mutations-per-minute", type=int, default=30)
    parser.add_argument("--max-concurrent-requests", type=int, default=16)
    return parser


def build_server(argv: list[str] | None = None) -> LeanStrandServer:
    args = _parser().parse_args(argv)
    host = _safe_bind_host(args.host, public_host=args.public_host)
    public_origin = (
        None
        if args.public_origin is None
        else _safe_origin(args.public_origin, label="public origin")
    )
    if args.allowed_origins and public_origin is None:
        raise ServiceError("allowed origins require an explicitly configured public origin")
    if len(args.allowed_origins) > MAX_ALLOWED_ORIGINS:
        raise ServiceError("too many explicitly approved proof-browser origins")
    allowed_origins = tuple(
        dict.fromkeys(
            _safe_origin(origin, label="allowed origin") for origin in args.allowed_origins
        )
    )
    if args.trust_proxy and (
        public_origin is None or not _loopback_hostname(host)
    ):
        raise ServiceError(
            "trusted reverse proxy requires a public origin and loopback-only listener"
        )
    port = _bounded_integer(args.port, "port", 0, 65_535)
    memory = _bounded_integer(args.max_memory_mib, "max_memory_mib", 64, 4_096)
    verification = _bounded_integer(args.max_verify_seconds, "max_verify_seconds", 1, 900)
    runtime = _bounded_integer(args.max_job_seconds, "max_job_seconds", verification, 1_200)
    ttl = _bounded_integer(args.job_ttl_seconds, "job_ttl_seconds", 30, 86_400)
    jobs = _bounded_integer(args.max_jobs, "max_jobs", 1, 256)
    nodes = _bounded_integer(args.max_strand_nodes, "max_strand_nodes", 1, 2_048)
    chunks = _bounded_integer(args.max_chunk_kib, "max_chunk_kib", 8, 1_024)
    live_url = _bounded_integer(
        args.max_live_url_bytes,
        "max_live_url_bytes",
        128,
        MAX_LIVE_URL_BYTES,
    )
    live_source_kib = _bounded_integer(
        args.max_live_source_kib,
        "max_live_source_kib",
        1,
        MAX_LIVE_SOURCE_BYTES // 1024,
    )
    mutations = _bounded_integer(
        args.max_mutations_per_minute, "max_mutations_per_minute", 1, 600
    )
    concurrent_requests = _bounded_integer(
        args.max_concurrent_requests, "max_concurrent_requests", 1, 64
    )
    storage = (
        args.storage
        if args.storage is not None
        else Path(tempfile.mkdtemp(prefix="hydra-lean-proof-jobs-"))
    )
    manager = JobManager(
        storage,
        limits=ServiceLimits(
            memory_mib=memory,
            verify_seconds=verification,
            job_seconds=runtime,
            ttl_seconds=ttl,
            retained_jobs=jobs,
            strand_nodes=nodes,
            chunk_kib=chunks,
            live_url_bytes=live_url,
            live_source_bytes=live_source_kib * 1024,
            mutations_per_minute=mutations,
            concurrent_requests=concurrent_requests,
        ),
    )
    return LeanStrandServer(
        (host, port),
        manager,
        args.directory,
        public_host=args.public_host,
        public_origin=public_origin,
        allowed_origins=allowed_origins,
        trust_proxy=args.trust_proxy,
        api_only=args.api_only,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        server = build_server(argv)
    except (OSError, ServiceError, ValueError) as error:
        print(f"Lean proof service: {error}", file=sys.stderr)
        return 1
    actual_host = server.server_address[0]
    display_host = "127.0.0.1" if actual_host == "0.0.0.0" else actual_host
    base = f"http://{display_host}:{server.server_port}"
    if server.static_directory == ROOT:
        frontier = "/book/_static/constructive-frontier-explorer/index.html"
        proof_graph = "/book/_static/pa-proof-explorer/defined/graph.html?target=PA000F"
    else:
        frontier = "/_static/constructive-frontier-explorer/index.html"
        proof_graph = "/_static/pa-proof-explorer/defined/graph.html?target=PA000F"
    print(f"Hydra Lean proof service: {base}")
    print(f"Frontier theorem explorer: {base}{frontier}")
    print(f"Safe first theorem (add_comm): {base}{proof_graph}")
    print(f"Verified proof-job API: {base}{API_PREFIX}/jobs")
    if server.public_host:
        print("PUBLIC HOST ENABLED: repository explorer and proof API are externally reachable.")
    if server.public_origin is not None:
        print(f"Approved public proof-service origin: {server.public_origin}")
        print(f"Public verified proof-job API: {server.public_origin}{API_PREFIX}/jobs")
    if server.allowed_origins:
        print("Approved cross-origin proof browsers: " + ", ".join(server.allowed_origins))
    if server.trust_proxy:
        print("TRUSTED LOOPBACK HTTPS PROXY ENABLED: forwarding headers are validated.")
    if server.api_only:
        print("API-ONLY MODE: static repository and theorem pages are not exposed.")
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
