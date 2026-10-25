"""Central-runtime opt-in remains narrow, explicit, and offline-verifiable.

Site directories and scheduled environments are simulated. No module command,
network call, model import, scheduler request, or real central-directory write
is used by these tests.
"""

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import stat
from types import SimpleNamespace

import pytest

from test_peano_hydra_review_runtime import COMMAND, INPUT, LIMITS, _record
from training.peano_hydra import helios_runtime, review_runtime
from training.peano_hydra.helios_runtime import reviewed_runtime_library_paths
from training.peano_hydra.review_runtime import (
    ReviewRuntimeError, run_bounded, runtime_library_record,
    validate_process_record, validate_runtime_library_directories,
    validate_runtime_library_record,
)


CPU_PATHS = (
    "/net/software/x86_64/el9/Python/3.11.5/lib",
    "/net/software/x86_64/el8/OpenSSL/1.1/lib",
    "/net/software/x86_64/el9/libffi/3.4.4/lib64",
    "/net/software/x86_64/el9/XZ/5.4.4/lib",
    "/net/software/x86_64/el9/SQLite/3.43.1/lib",
    "/net/software/x86_64/el8/Tcl/8.6.13/lib",
    "/net/software/x86_64/el8/libreadline/8.2/lib",
    "/net/software/x86_64/el8/ncurses/6.4/lib",
    "/net/software/x86_64/el8/zlib/1.2.13/lib",
    "/net/software/x86_64/el8/bzip2/1.0.8/lib",
    "/net/software/x86_64/el8/binutils/2.40/lib",
)
CPU_MODULES = (
    "binutils/2.40:bzip2/1.0.8:zlib/1.2.13:ncurses/6.4:libreadline/8.2:"
    "Tcl/8.6.13:SQLite/3.43.1:XZ/5.4.4:libffi/3.4.4:OpenSSL/1.1:Python/3.11.5"
)
GPU_PATHS = (
    "/net/software/aarch64/el9/ML-bundle/25.10/lib",
    "/net/software/aarch64/el9/OpenSSL/3.0.16/lib",
)

# Raw central Lua modules inspected on Helios, not inferred suffix rewrites.
HIERARCHICAL_MODULES = (
    ("Python/3.13.5", "PYTHON", "3.13.5", "3.13.5-GCCcore-14.3.0", "lib"),
    ("HDF5/1.14.6", "HDF5", "1.14.6", "1.14.6-gompi-2025b", "lib"),
    ("Clang/21.1.2-CUDA-12.9.1", "CLANG", "21.1.2",
     "21.1.2-GCCcore-14.3.0-CUDA-12.9.1", "lib/aarch64-unknown-linux-gnu"),
)
LIBPNG_ALIAS = ("libpng/1.6.50", "LIBPNG", "1.6.52", "1.6.52", "lib")
LIBPNG_REQUESTED = "/net/software/aarch64/el9modules/all/Compiler/GCCcore/14.3.0/libpng/1.6.50.lua"
LIBPNG_RESOLVED = "/net/software/aarch64/el9modules/all/Core/libpng/1.6.52.lua"
# Exact read-only inspection bytes, including the final blank line. The test
# never sources the file or executes its load()/prepend_path() declarations.
LIBPNG_MODULE = b'''help([==[

Description
===========
libpng is the official PNG reference library


More information
================
 - Homepage: http://www.libpng.org/pub/png/libpng.html
]==])

whatis([==[Description: libpng is the official PNG reference library]==])
whatis([==[Homepage: http://www.libpng.org/pub/png/libpng.html]==])
whatis([==[URL: http://www.libpng.org/pub/png/libpng.html]==])

local root = "/net/software/aarch64/el9/libpng/1.6.52"

conflict("libpng")

if not ( isloaded("zlib/1.2.13") ) then
    load("zlib/1.2.13")
end

prepend_path("CMAKE_PREFIX_PATH", root)
prepend_path("CPATH", pathJoin(root, "include"))
prepend_path("LD_LIBRARY_PATH", pathJoin(root, "lib"))
prepend_path("LIBRARY_PATH", pathJoin(root, "lib"))
prepend_path("MANPATH", pathJoin(root, "share", "man"))
prepend_path("PATH", pathJoin(root, "bin"))
prepend_path("PKG_CONFIG_PATH", pathJoin(root, "lib", "pkgconfig"))
prepend_path("XDG_DATA_DIRS", pathJoin(root, "share"))
setenv("EBROOTLIBPNG", root)
setenv("EBVERSIONLIBPNG", "1.6.52")
setenv("EBDEVELLIBPNG", pathJoin(root, "easybuild", "Core-libpng-1.6.52-easybuild-devel"))

-- Built with EasyBuild version 5.2.0

add_property("arch","arm")

'''


def _environment(stage="prepare"):
    common = {"SLURM_JOB_ID": "21369075",
              "PEANO_JOB_SCRIPT": f"slurm/peano_hydra_authority_scale_{stage}.sbatch"}
    if stage == "prepare":
        return {**common, "PEANO_HELIOS_CPU_MODULE": "Python/3.11.5", "LOADEDMODULES": CPU_MODULES,
                "LD_LIBRARY_PATH": ":".join(CPU_PATHS)}
    return {**common, "PEANO_HELIOS_ML_MODULE": "ML-bundle/25.10",
            "LOADEDMODULES": "GCC/14.2.0:OpenSSL/3.0.16:ML-bundle/25.10",
            "LD_LIBRARY_PATH": ":".join(GPU_PATHS)}


@pytest.fixture
def central_directories(monkeypatch):
    """Simulate central stat/realpath; leave every noncentral path untouched."""
    real_resolve, real_lstat = Path.resolve, Path.lstat
    aliases, unavailable, calls = {}, set(), []

    def resolve(path, strict=False):
        text = str(path)
        if text.startswith("/net/software/"):
            calls.append(("resolve", text, strict))
            if text in unavailable:
                raise FileNotFoundError(text)
            return Path(aliases.get(text, text))
        return real_resolve(path, strict=strict)

    def lstat(path):
        text = str(path)
        if text.startswith("/net/software/"):
            calls.append(("lstat", text))
            if text in unavailable:
                raise FileNotFoundError(text)
            return SimpleNamespace(st_mode=stat.S_IFDIR | 0o755, st_dev=1, st_ino=42)
        return real_lstat(path)

    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(Path, "lstat", lstat)
    return SimpleNamespace(aliases=aliases, unavailable=unavailable, calls=calls)


def test_local_selection_is_empty_without_reading_or_inheriting_loader_state(central_directories):
    assert reviewed_runtime_library_paths({"LD_LIBRARY_PATH": "/unreviewed", "LD_PRELOAD": "bad"}) == ()
    assert central_directories.calls == []


@pytest.mark.parametrize("stage,expected", [("prepare", CPU_PATHS), ("train", GPU_PATHS),
                                          ("evaluate", GPU_PATHS), ("evaluate_recovery", GPU_PATHS)])
def test_only_reviewed_scheduled_job_and_loaded_module_select_exact_order(central_directories, stage, expected):
    environment = _environment(stage)
    before = deepcopy(environment)
    assert reviewed_runtime_library_paths(environment) == expected
    assert environment == before
    assert central_directories.calls


def test_selector_reads_os_environment_only_when_requested(monkeypatch, central_directories):
    monkeypatch.setattr(helios_runtime.os, "environ", _environment())
    assert reviewed_runtime_library_paths() == CPU_PATHS


@pytest.mark.parametrize("stage", ["train", "evaluate"])
def test_frontier_has_its_own_exact_profile_and_preserves_runtime_selection(central_directories, stage):
    environment = _environment("train")
    environment["PEANO_JOB_SCRIPT"] = f"slurm/peano_hydra_frontier_{stage}.sbatch"
    environment["PEANO_HYDRA_PROFILE"] = "peano-hydra-frontier-v1"
    assert reviewed_runtime_library_paths(environment) == GPU_PATHS
    for wrong in (None, "peano-hydra-search-v2", "peano-hydra-corrective-v2", "peano-hydra-frontier-v2"):
        environment["PEANO_HYDRA_PROFILE"] = wrong
        with pytest.raises(ReviewRuntimeError, match="frontier job"):
            reviewed_runtime_library_paths(environment)


def test_frontier_profile_does_not_relabel_a_historical_corrective_job(central_directories):
    environment = _environment("train")
    environment["PEANO_JOB_SCRIPT"] = "slurm/peano_hydra_corrective_train.sbatch"
    environment["PEANO_HYDRA_PROFILE"] = "peano-hydra-frontier-v1"
    with pytest.raises(ReviewRuntimeError, match="corrective job"):
        reviewed_runtime_library_paths(environment)


def test_legitimate_central_lib64_alias_is_resolved_before_executor_validation(central_directories):
    resolved = CPU_PATHS[2].replace("/lib64", "/lib")
    central_directories.aliases[CPU_PATHS[2]] = resolved
    assert reviewed_runtime_library_paths(_environment()) == (*CPU_PATHS[:2], resolved, *CPU_PATHS[3:])


def _hierarchical_environment(module=HIERARCHICAL_MODULES[0], stage="train"):
    loaded, name, version, installed, library = module
    root = f"/net/software/aarch64/el9/{loaded.split('/', 1)[0]}/{installed}"
    path = f"{root}/{library}"
    environment = _environment(stage)
    environment.update({"LOADEDMODULES": environment["LOADEDMODULES"] + ":" + loaded,
                        "LD_LIBRARY_PATH": path + ":" + environment["LD_LIBRARY_PATH"],
                        f"EBROOT{name}": root, f"EBVERSION{name}": version})
    return environment, path


@pytest.mark.parametrize("module", HIERARCHICAL_MODULES)
@pytest.mark.parametrize("stage", ["train", "evaluate", "evaluate_recovery"])
def test_exact_site_metadata_binds_hierarchical_installation_roots(central_directories, module, stage):
    environment, path = _hierarchical_environment(module, stage)
    before = deepcopy(environment)
    assert reviewed_runtime_library_paths(environment) == (path, *GPU_PATHS)
    assert environment == before


@pytest.mark.parametrize("changes", [
    {"EBROOTPYTHON": None}, {"EBROOTPYTHON": True}, {"EBROOTPYTHON": ""},
    {"EBROOTPYTHON": "/private/tmp/Python"},
    {"EBROOTPYTHON": "/net/software/aarch64/el9/Python/3.13.5-GCCcore-14.3.0/"},
    {"EBROOTPYTHON": "/net/software/x86_64/el9/Python/3.13.5-GCCcore-14.3.0"},
    {"EBROOTPYTHON": "/net/software/aarch64/el9/Python/3.13.5-GCCcore-14.3.0-other"},
    {"EBROOTOTHER": "/net/software/aarch64/el9/Python/3.13.5-GCCcore-14.3.0", "EBROOTPYTHON": None},
    {"EBVERSIONPYTHON": None}, {"EBVERSIONPYTHON": True}, {"EBVERSIONPYTHON": ""},
    {"EBVERSIONPYTHON": "3.13"}, {"EBVERSIONPYTHON": "3.13.6"},
    {"EBVERSIONPYTHON": "3.13.5-GCCcore-14.3.0"},
    {"EBVERSIONPYTHON": "3.13.5/../3.13.5"}, {"EBVERSIONPYTHON": "3.13.5\x00"},
    {"EBVERSIONPYTHON": "x" * 97},
])
def test_hierarchical_ownership_requires_exact_valid_metadata(central_directories, changes):
    environment, path = _hierarchical_environment()
    environment.update(changes)
    with pytest.raises(ReviewRuntimeError, match="not owned") as error:
        reviewed_runtime_library_paths(environment)
    assert path in str(error.value)


@pytest.mark.parametrize("additional", ["Python/3.12.13", "PYTHON/3.13.5", "Py.thon/3.13.5"])
def test_hierarchical_owner_and_easybuild_variable_are_unambiguous(central_directories, additional):
    environment, _ = _hierarchical_environment()
    environment["LOADEDMODULES"] += ":" + additional
    with pytest.raises(ReviewRuntimeError, match="not owned"):
        reviewed_runtime_library_paths(environment)


def test_hierarchical_root_is_not_accepted_by_version_prefix_alone(central_directories):
    environment, _ = _hierarchical_environment()
    del environment["EBROOTPYTHON"]
    del environment["EBVERSIONPYTHON"]
    with pytest.raises(ReviewRuntimeError, match="not owned"):
        reviewed_runtime_library_paths(environment)


@pytest.mark.parametrize("target", ["/private/tmp/lib", "/net/software/x86_64/el9/Python/3.13.5/lib"])
def test_hierarchical_library_cannot_escape_central_architecture(central_directories, target):
    environment, path = _hierarchical_environment()
    central_directories.aliases[path] = target
    with pytest.raises(ReviewRuntimeError, match="escapes"):
        reviewed_runtime_library_paths(environment)


def test_flat_loaded_module_cannot_have_two_versions(central_directories):
    environment = _environment("train")
    environment["LOADEDMODULES"] += ":OpenSSL/3.0.17"
    with pytest.raises(ReviewRuntimeError, match="not owned"):
        reviewed_runtime_library_paths(environment)


@pytest.fixture
def reviewed_alias_file(tmp_path, monkeypatch, central_directories):
    actual = tmp_path / "libpng.lua"
    actual.write_bytes(LIBPNG_MODULE)
    real_open = Path.open
    calls = []

    def open_module(path, *args, **kwargs):
        if str(path) == LIBPNG_RESOLVED:
            calls.append((str(path), args, kwargs))
            return real_open(actual, *args, **kwargs)
        return real_open(path, *args, **kwargs)

    central_directories.aliases[LIBPNG_REQUESTED] = LIBPNG_RESOLVED
    monkeypatch.setattr(Path, "open", open_module)
    return SimpleNamespace(actual=actual, calls=calls)


@pytest.mark.parametrize("stage", ["train", "evaluate"])
def test_only_exact_reviewed_site_alias_bytes_authorize_a_version_change(reviewed_alias_file, stage):
    assert len(LIBPNG_MODULE) == 1172
    assert hashlib.sha256(LIBPNG_MODULE).hexdigest() == "c9756b9edf3d38edc686263142992360bc709998e29449241278cfe5d888ebc2"
    environment, path = _hierarchical_environment(LIBPNG_ALIAS, stage)
    assert reviewed_runtime_library_paths(environment) == (path, *GPU_PATHS)
    assert reviewed_alias_file.calls == [(LIBPNG_RESOLVED, ("rb",), {})]


@pytest.mark.parametrize("failure", ["same-size-edit", "extra-byte", "missing-file", "world-writable", "different-target"])
def test_reviewed_alias_rejects_changed_modulefile_identity(reviewed_alias_file, central_directories, failure):
    if failure == "same-size-edit":
        reviewed_alias_file.actual.write_bytes(LIBPNG_MODULE.replace(b"1.6.52", b"1.6.53"))
    elif failure == "extra-byte":
        reviewed_alias_file.actual.write_bytes(LIBPNG_MODULE + b"\n")
    elif failure == "missing-file":
        reviewed_alias_file.actual.unlink()
    elif failure == "world-writable":
        reviewed_alias_file.actual.chmod(0o666)
    else:
        central_directories.aliases[LIBPNG_REQUESTED] = LIBPNG_RESOLVED.replace("1.6.52", "1.6.53")
    environment, _ = _hierarchical_environment(LIBPNG_ALIAS)
    with pytest.raises(ReviewRuntimeError, match="not owned"):
        reviewed_runtime_library_paths(environment)


@pytest.mark.parametrize("loaded,version,installed", [
    ("libpng/1.6.49", "1.6.52", "1.6.52"),
    ("libpng/1.6.50", "1.6.53", "1.6.53"),
    ("libpng/1.6.50", "1.6.52", "1.6.52-GCCcore-14.3.0"),
    ("Other/1.6.50", "1.6.52", "1.6.52"),
])
def test_alias_is_not_a_generic_software_version_override(reviewed_alias_file, loaded, version, installed):
    name = loaded.split("/", 1)[0].upper()
    environment, _ = _hierarchical_environment((loaded, name, version, installed, "lib"))
    with pytest.raises(ReviewRuntimeError, match="not owned"):
        reviewed_runtime_library_paths(environment)
    assert reviewed_alias_file.calls == []


def test_normal_hierarchical_module_does_not_read_alias_files(reviewed_alias_file):
    environment, path = _hierarchical_environment()
    assert reviewed_runtime_library_paths(environment) == (path, *GPU_PATHS)
    assert reviewed_alias_file.calls == []


def test_flat_site_module_does_not_depend_on_stale_easybuild_version(central_directories):
    environment = _environment("train")
    path = "/net/software/aarch64/el9/libfabric/2.3.1-SHS-13.1.0/lib"
    environment.update({"LOADEDMODULES": environment["LOADEDMODULES"] + ":libfabric/2.3.1-SHS-13.1.0",
                        "LD_LIBRARY_PATH": path + ":" + environment["LD_LIBRARY_PATH"],
                        "EBROOTLIBFABRIC": path[:-4], "EBVERSIONLIBFABRIC": "2.1.0"})
    assert reviewed_runtime_library_paths(environment) == (path, *GPU_PATHS)


@pytest.mark.parametrize("target", ["/private/tmp/lib", "/net/software/aarch64/el9/libffi/3.4.4/lib"])
def test_central_alias_cannot_escape_to_user_or_other_architecture(central_directories, target):
    central_directories.aliases[CPU_PATHS[2]] = target
    with pytest.raises(ReviewRuntimeError, match="escapes"):
        reviewed_runtime_library_paths(_environment())


@pytest.mark.parametrize("changes", [
    {"SLURM_JOB_ID": ""}, {"SLURM_JOB_ID": "0"}, {"SLURM_JOB_ID": True},
    {"SLURM_JOB_ID": "12;unsafe"}, {"SLURM_JOB_ID": "9" * 100},
    {"PEANO_JOB_SCRIPT": "slurm/peano_hydra_alpha_prepare.sbatch"},
    {"PEANO_JOB_SCRIPT": "slurm/peano_hydra_authority_scale_prepare.sbatch/../other"},
    {"PEANO_HELIOS_CPU_MODULE": "Python/3.12.0"},
    {"PEANO_HELIOS_ML_MODULE": "ML-bundle/25.10"},
    {"LOADEDMODULES": "Python/3.11.4"}, {"LOADEDMODULES": "Python/3.11.5:"},
    {"LOADEDMODULES": CPU_MODULES + ":Python/3.11.5"},
    {"LOADEDMODULES": CPU_MODULES + ":Python/3.12.0"},
    {"LOADEDMODULES": CPU_MODULES + ":arbitrary-module"},
    {"LOADEDMODULES": "x" * 16385}, {"LD_LIBRARY_PATH": ""},
    {"LD_LIBRARY_PATH": ":".join(CPU_PATHS) + ":"},
    {"LD_LIBRARY_PATH": ":" + ":".join(CPU_PATHS)},
    {"LD_LIBRARY_PATH": ":".join((CPU_PATHS[0], CPU_PATHS[0]))},
    {"LD_LIBRARY_PATH": "lib"}, {"LD_LIBRARY_PATH": "/private/tmp/lib"},
    {"LD_LIBRARY_PATH": CPU_PATHS[0] + "/../unreviewed"},
    {"LD_LIBRARY_PATH": CPU_PATHS[0] + "/./nested"},
    {"LD_LIBRARY_PATH": CPU_PATHS[0] + ":/net/software/x86_64/el9/Unknown/1.0/lib"},
    {"LD_LIBRARY_PATH": ":".join(GPU_PATHS)},
    {"LD_LIBRARY_PATH": CPU_PATHS[1]},
    {"LD_PRELOAD": "unreviewed.so"}, {"LD_PRELOAD": ""}, {"LD_AUDIT": "unreviewed.so"},
    {"LD_OTHER_FUTURE_OPTION": "value"}, {"DYLD_LIBRARY_PATH": "/private/tmp/lib"},
    {"DYLD_INSERT_LIBRARIES": "unreviewed.dylib"},
])
def test_unknown_modules_paths_loader_knobs_and_ambiguous_scheduled_inputs_fail_closed(central_directories, changes):
    with pytest.raises(ReviewRuntimeError):
        reviewed_runtime_library_paths({**_environment(), **changes})


def test_unavailable_central_library_is_not_silently_discarded(central_directories):
    central_directories.unavailable.add(CPU_PATHS[0])
    with pytest.raises(ReviewRuntimeError, match="unavailable"):
        reviewed_runtime_library_paths(_environment())


@pytest.mark.parametrize("paths", [
    (), [], None, "", ("",), (Path(CPU_PATHS[0]),), (True,),
    (CPU_PATHS[0], CPU_PATHS[0]), (CPU_PATHS[0] + ":/tmp",),
    (CPU_PATHS[0] + "/",), (CPU_PATHS[0].replace("/el9/", "//el9/"),),
    ("/net/software/x86_64",), ("/net/software/x86_64-mine/el9/Python/3.11.5/lib",),
    ("/net/software/x86_64/el9/Python/3.11.5/../../lib",),
    ("/net/software/x86_64/el9/Python/3.11.5/lib\x00",),
    ("/net/software/x86_64/el9/Python/3.11.5/λ",),
    (CPU_PATHS[0] + "x" * 1024,),
    tuple(f"/net/software/x86_64/el9/Python/3.11.5/lib{i}" for i in range(65)),
    tuple(f"/net/software/x86_64/el9/Python/3.11.5/lib{i}" + "x" * 600 for i in range(64)),
])
def test_library_descriptors_have_bounded_exact_portable_paths(paths):
    with pytest.raises(ReviewRuntimeError):
        runtime_library_record(paths)


def test_selector_requires_explicit_cpu_marker_and_environment_mapping(central_directories):
    environment = _environment()
    del environment["PEANO_HELIOS_CPU_MODULE"]
    with pytest.raises(ReviewRuntimeError, match="reviewed central module"):
        reviewed_runtime_library_paths(environment)
    with pytest.raises(ReviewRuntimeError, match="environment mapping"):
        reviewed_runtime_library_paths([])


def test_saved_library_receipt_validates_offline_without_filesystem_or_environment(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline receipt validation touched a live library")

    monkeypatch.setattr(Path, "resolve", forbidden)
    monkeypatch.setattr(Path, "lstat", forbidden)
    record = runtime_library_record(CPU_PATHS)
    assert validate_runtime_library_record(record) == CPU_PATHS
    assert validate_runtime_library_record(record, paths=CPU_PATHS) == CPU_PATHS
    assert record["paths"] == list(CPU_PATHS)


@pytest.mark.parametrize("changes", [
    {"schema": "other"}, {"variable": "LD_PRELOAD"}, {"sha256": "b" * 64},
    {"sha256": None}, {"paths": tuple(CPU_PATHS)}, {"paths": []},
    {"paths": list(reversed(CPU_PATHS))}, {"paths": list(CPU_PATHS) + [CPU_PATHS[0]]},
    {"paths": [True]}, {"unknown": "extra"},
])
def test_receipt_shape_order_and_digest_are_checked(changes):
    with pytest.raises(ReviewRuntimeError):
        validate_runtime_library_record({**runtime_library_record(CPU_PATHS), **changes})


def test_resealed_different_paths_do_not_match_the_original_request():
    changed = runtime_library_record(tuple(reversed(CPU_PATHS)))
    with pytest.raises(ReviewRuntimeError, match="requested paths"):
        validate_runtime_library_record(changed, paths=CPU_PATHS)


def test_optional_process_field_requires_explicit_opt_in_and_semantic_validation():
    record = _record()
    record["runtime_libraries"] = runtime_library_record(CPU_PATHS)
    with pytest.raises(ReviewRuntimeError, match="fields"):
        validate_process_record(record, command=COMMAND, limits=LIMITS, input_bytes=INPUT)
    for options in ({"extra_fields": ("runtime_libraries",)}, {"runtime_library_paths": CPU_PATHS},
                    {"extra_fields": ("runtime_libraries",), "runtime_library_paths": CPU_PATHS}):
        validate_process_record(record, command=COMMAND, limits=LIMITS, input_bytes=INPUT, **options)
    record["runtime_libraries"]["sha256"] = "b" * 64
    with pytest.raises(ReviewRuntimeError, match="hash"):
        validate_process_record(record, command=COMMAND, limits=LIMITS, input_bytes=INPUT,
                                extra_fields=("runtime_libraries",))


def test_process_receipt_cannot_drop_or_reseal_its_requested_libraries():
    with pytest.raises(ReviewRuntimeError, match="fields"):
        validate_process_record(_record(), command=COMMAND, limits=LIMITS, input_bytes=INPUT,
                                runtime_library_paths=CPU_PATHS)
    record = {**_record(), "runtime_libraries": runtime_library_record(GPU_PATHS)}
    with pytest.raises(ReviewRuntimeError, match="requested paths"):
        validate_process_record(record, command=COMMAND, limits=LIMITS, input_bytes=INPUT,
                                runtime_library_paths=CPU_PATHS)


@pytest.mark.parametrize("failure", [None, "missing", "file", "symlink", "intermediate-symlink", "world-writable"])
def test_execution_requires_real_canonical_non_world_writable_directories(tmp_path, monkeypatch, failure):
    central = tmp_path.resolve() / "central"
    central.mkdir()
    real = central / "real"
    real.mkdir()
    requested = real
    monkeypatch.setattr(review_runtime, "_RUNTIME_LIBRARY_ROOTS", (str(central),))
    if failure == "missing":
        requested = central / "missing"
    elif failure == "file":
        requested = central / "file"
        requested.write_bytes(b"not a directory")
    elif failure == "symlink":
        requested = central / "link"
        requested.symlink_to(real, target_is_directory=True)
    elif failure == "intermediate-symlink":
        (real / "nested").mkdir()
        link = central / "linked-parent"
        link.symlink_to(real, target_is_directory=True)
        requested = link / "nested"
    elif failure == "world-writable":
        real.chmod(0o777)
    if failure is None:
        validate_runtime_library_directories((str(requested),))
    else:
        with pytest.raises(ReviewRuntimeError):
            validate_runtime_library_directories((str(requested),))


def test_explicit_worker_environment_restores_only_requested_library_path(tmp_path, monkeypatch, central_directories):
    names = ("LD_LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT", "LD_FUTURE_OPTION", "DYLD_LIBRARY_PATH",
             "DYLD_INSERT_LIBRARIES", "DYLD_FUTURE_OPTION")
    for name in names:
        monkeypatch.setenv(name, "unreviewed-parent-value")
    captured = {}

    def launch(*args, **kwargs):
        captured.update(kwargs["env"])
        raise RuntimeError("captured before launch")

    monkeypatch.setattr(review_runtime.subprocess, "Popen", launch)
    with pytest.raises(RuntimeError, match="captured before launch"):
        run_bounded(COMMAND, cwd=tmp_path, limits=LIMITS, runtime_library_paths=CPU_PATHS)
    loader = {name: value for name, value in captured.items() if name.startswith(("LD_", "DYLD_"))}
    assert loader == {"LD_LIBRARY_PATH": ":".join(CPU_PATHS)}
    assert all(os.environ[name] == "unreviewed-parent-value" for name in names)


def test_unreviewed_paths_reject_before_any_launch(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid runtime path reached process launch")

    monkeypatch.setattr(review_runtime.subprocess, "Popen", forbidden)
    with pytest.raises(ReviewRuntimeError):
        run_bounded(COMMAND, cwd=tmp_path, limits=LIMITS, runtime_library_paths=("/private/tmp/lib",))


def test_mocked_worker_adds_exact_field_only_for_explicit_library_tuple(tmp_path, monkeypatch, central_directories):
    captured = []

    def launch(*args, **kwargs):
        captured.append(kwargs["env"])
        kwargs["stdout"].write(b"proof\n")
        kwargs["stdout"].flush()
        return SimpleNamespace(pid=123456, returncode=None)

    monkeypatch.setattr(review_runtime.subprocess, "Popen", launch)
    monkeypatch.setattr(review_runtime.os, "wait4", lambda *args: (
        123456, 0, SimpleNamespace(ru_maxrss=16384, ru_utime=0.1, ru_stime=0.1)))
    monkeypatch.setattr(review_runtime, "_group_members", lambda pid: [])
    monkeypatch.setattr(review_runtime, "_kill_owned_group", lambda pid: None)
    plain = run_bounded(COMMAND, cwd=tmp_path, limits=LIMITS, input_bytes=INPUT)
    explicit = run_bounded(COMMAND, cwd=tmp_path, limits=LIMITS, input_bytes=INPUT,
                           runtime_library_paths=CPU_PATHS)
    assert set(explicit) == set(plain) | {"runtime_libraries"}
    assert explicit["runtime_libraries"] == runtime_library_record(CPU_PATHS)
    assert all(plain[name] == explicit[name] for name in plain if name != "resources")
    assert not any(name.startswith(("LD_", "DYLD_")) for name in captured[0])
    assert captured[1]["LD_LIBRARY_PATH"] == ":".join(CPU_PATHS)
    validate_process_record(explicit, command=COMMAND, limits=LIMITS, input_bytes=INPUT,
                            runtime_library_paths=CPU_PATHS, success_codes=(0,))
