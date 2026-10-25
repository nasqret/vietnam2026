"""Explicit opt-in to the isolated engine and checked certificate catalogue.

The historical model-only provider and its integrity contract are unchanged.
This module neither adds axioms nor treats a manifest as proof authority.
"""
from pathlib import Path
import hashlib
import sys

import model_runtime as pinned

APP = Path(__file__).resolve().parent
NATIVE = APP / "native-v7"
LIBRARY = APP / "lemmas"
RESERVATION = APP / "evaluation-holdout.json"
NATIVE_MANIFEST_SHA256 = "5c2fa7aa6878c7730fe972e095f8e9312d0980de65c31767d385c27caf54046e"
LIBRARY_MANIFEST_SHA256 = "07e82238a2a02313702f360573b2897e4fcbb010b5b6029aee1e662a33e8320c"
RESERVATION_SHA256 = "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e"
RANKER = APP / "branch-rankers/linear-v1.json"
RANKER_SHA256 = "ea35df234ab4b3083d46959b03ac37c6a033cc98e1af717354ef0a2a8bd31661"
PROFILE = "hydra-experimental-certified-v1"


def selection(value, *, mode, search_mode=None):
    if value is None:
        return None
    pinned.require(type(value) is dict and set(value) <= {"engine", "lemmas", "planner", "ranker", "advisers"},
                   "Experimental fields must be engine, lemmas, planner, ranker and advisers.")
    engine, lemmas = value.get("engine", "sharing-v1"), value.get("lemmas", True)
    planner = value.get("planner","off")
    ranker = value.get("ranker","off")
    advisers = value.get("advisers",[])
    pinned.require(engine == "sharing-v1" and type(lemmas) is bool,
                   "Experimental selection requires sharing-v1 and a Boolean lemmas option.")
    pinned.require(type(planner) is str and planner in {"off","deterministic"},
                   "Planner must be off or deterministic; no new learned provider is installed yet.")
    pinned.require(type(ranker) is str and ranker in {"off","linear-v1"},
                   "Ranker must be off or the pinned linear-v1 artifact.")
    pinned.require(type(advisers) is list and len(advisers)<=2
                   and all(type(name) is str and name in {"sympy","cvc5"} for name in advisers)
                   and len(set(advisers))==len(advisers),
                   "Select each installed bounded adviser at most once: sympy, cvc5.")
    pinned.require(mode in {"replay", "search"}, "Unknown experimental endpoint.")
    pinned.require(search_mode not in {"model", "hybrid"},
        "The preserved model provider cannot run on the experimental native engine. Use heuristic/symbolic until a new provider is installed.")
    return {"engine":engine,"lemmas":lemmas,"planner":planner,"ranker":ranker,"advisers":sorted(advisers)}


def selected_ranker(options):
    if options.get("ranker","off")=="off":
        return None
    from branch_ranker import load_ranker
    return load_ranker(RANKER,expected_sha256=RANKER_SHA256)


def native_snapshot():
    pinned.require(type(NATIVE_MANIFEST_SHA256) is str, "The experimental native engine has not passed its source gate.")
    manifest, identity = pinned._small(NATIVE / "manifest.json", maximum=256*1024,
                                       expected=NATIVE_MANIFEST_SHA256)
    pinned.require(manifest.get("schema") == "hydra-native-engine-v7-source-v1"
        and manifest.get("original_kernel_commit") == pinned.SOURCE_COMMIT
        and type(manifest.get("files")) is dict and 1 <= len(manifest["files"]) <= 512,
        "Invalid versioned native source manifest.")
    actual_files = {str(path.relative_to(NATIVE)) for path in (NATIVE / "peano_lab").rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts}
    pinned.require(actual_files == set(manifest["files"]), "The experimental native source inventory changed.")
    for relative, descriptor in manifest["files"].items():
        path = pinned._safe_path(NATIVE, relative)
        pinned.require(pinned._fingerprint(path, descriptor["bytes"]) == descriptor,
                       "Experimental native source changed: " + relative)
    # A compiler change is permitted; a kernel change is not.
    from worker import KERNEL_PINS
    for original, expected in KERNEL_PINS.items():
        if "/kernel/" in original:
            relative = original.removeprefix("peano-lab/py/")
            pinned.require(manifest["files"][relative]["sha256"] == expected,
                           "The experimental engine changed the original kernel.")
    pinned.require(pinned._fingerprint(NATIVE / "manifest.json", identity["bytes"]) == identity,
                   "Experimental source manifest changed while reading.")
    return identity


def activate_native():
    identity = native_snapshot()
    for name, module in tuple(sys.modules.items()):
        if name == "peano_lab" or name.startswith("peano_lab."):
            location = getattr(module, "__file__", None)
            pinned.require(location is None or Path(location).resolve().is_relative_to(NATIVE),
                           "Cannot mix the preserved and experimental native engines in one process.")
    sys.path[:0] = [str(NATIVE), str(pinned.SOURCE), str(pinned.SOURCE / "peano-lab/py")]
    return identity


def library_snapshot():
    pinned.require(type(LIBRARY_MANIFEST_SHA256) is str, "The certified library has not passed its producer gate.")
    manifest, identity = pinned._small(LIBRARY / "manifest.json", maximum=8*1024*1024,
                                      expected=LIBRARY_MANIFEST_SHA256)
    total = identity["bytes"]
    for entry in manifest["entries"]:
        descriptor = entry["certificate"]
        total += descriptor["bytes"]
        pinned.require(total <= 8*1024*1024, "The catalogue exceeds 8 MiB.")
        actual = pinned._fingerprint(pinned._safe_path(LIBRARY, descriptor["path"]), 512*1024)
        pinned.require(actual == {key:descriptor[key] for key in ("bytes","sha256")},
                       "A pinned lemma certificate changed.")
    return identity


def reserved_exclusions():
    from lemma_library import make_exclusions
    pinned.require(type(RESERVATION_SHA256) is str, "No evaluation reservation is pinned.")
    reservation, _ = pinned._small(RESERVATION, maximum=128*1024, expected=RESERVATION_SHA256)
    pinned.require(reservation.get("frozen") is True and len(reservation["cases"]) == 16,
                   "The prospective evaluation reservation changed.")
    return make_exclusions(statements=tuple(item["theorem"] for item in reservation["cases"]),
        families=tuple(sorted({item["family"] for item in reservation["cases"]})))


def authority(theorem, options, commands, capabilities_type, *, should_stop=None):
    if not options["lemmas"]:
        return capabilities_type(label="hydra-sharing-native-v1",allowed_commands=commands,
                                 allowed_theorems=frozenset()), None
    from lemma_imports import ImportBudget
    from lemma_library import load_library
    source_identity = library_snapshot()
    library = load_library(LIBRARY, expected_manifest_sha256=LIBRARY_MANIFEST_SHA256,
        exclusions=reserved_exclusions(), target=theorem, should_stop=should_stop)
    caps = capabilities_type(label=library.capability_label,allowed_commands=commands,
        allowed_theorems=frozenset(library.available_names),checked_library=library,import_budget=ImportBudget())
    return caps, {"manifest":source_identity,"preload_verification":dict(library.verification)}


def status():
    try:
        native_snapshot()
        library_snapshot()
        pinned._small(RESERVATION, maximum=128*1024, expected=RESERVATION_SHA256)
        pinned._small(RANKER,maximum=65536,expected=RANKER_SHA256)
        from adviser_runtime import available_advisers
        return {"available":True,"profile":PROFILE,"engine":"sharing-v1",
            "native_source_sha256":NATIVE_MANIFEST_SHA256,
            "library_manifest_sha256":LIBRARY_MANIFEST_SHA256,
            "saved_model_compatible":False,"learned_provider_available":False,
            "planners":["off","deterministic"],"rankers":["off","linear-v1"],
            "ranker_sha256":RANKER_SHA256,"advisers":available_advisers()}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"available":False,"profile":PROFILE,"detail":str(error)[:256]}
