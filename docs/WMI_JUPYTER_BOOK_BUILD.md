# WMI Jupyter Book build

Status on **2026-07-30**: the harness has completed an independent static
security and reproducibility audit, and the findings below have been
remediated. Default `--test-only` scheduler validation previously succeeded
for the 125-file frozen snapshot
`6feb5ebcdb9f59e6d94b71acd3fb2bce06d45b3a3885ad95aa8e9c02d61a3bcb`,
whose content-manifest SHA-256 is
`c09064eb67906761c357626df4ee9e0cf387a89b7593654c8c5bf74baf836c24`.
Real job `173024` was last observed `PENDING (Priority)` with zero CPU. It has
not produced a Book-build or integrity receipt, so neither result is claimed.
That snapshot predates the PA Proof Explorer and cannot validate it. A new
content-addressed snapshot and scheduler/build receipts are required before
the explorer is published. The current local manifest-only preflight selects
1,359 files and 42,263,297 bytes at content-manifest SHA-256
`8a6378db352a567a6d35734ba2ef9a684ef715f2cf8227a6fc3c5e5cc970fe8b`.
No archive was created or uploaded from that observation.

This harness moves the strict Jupyter Book build off the workstation while
preserving the exact dirty-worktree inputs that were requested.  It is
independent of the quadratic-reciprocity proof runner and has no theorem
admission authority.

## Safety and submission

The default mode is scheduler validation only:

```bash
scripts/submit_wmi_book_build.sh
# equivalently
scripts/submit_wmi_book_build.sh --test-only
```

This creates and transfers the content-addressed snapshot, verifies it on
WMI, and calls `sbatch --test-only`.  It does **not** allocate a compute node,
create a virtual environment, install packages, or build the book.

A real allocation requires the exact confirmation token:

```bash
scripts/submit_wmi_book_build.sh \
  --submit --confirm PEANO-WMI-BOOK-BUILD
```

The fixed resource profile is `cpu_idle`, one node, one task, one CPU,
8192 MiB, and one hour.  The job creates a unique run directory named by the
Slurm job ID; repeated submissions never reuse a virtual environment or an
incremental Sphinx build.

## Content-addressed input boundary

[`package_wmi_book_snapshot.py`](../scripts/package_wmi_book_snapshot.py)
sorts every input path and creates a canonical uncompressed GNU tar with
normalized ownership, timestamps, and modes.  Both the archive SHA-256 and a
path/size/mode/content manifest SHA-256 are checked after transfer.
The packager rejects an output path inside the repository, every pre-existing
output, and in particular an output hardlinked to an input.  It reads each
selected file and executable-mode bit once into an immutable in-memory table;
the archive and manifest are derived from that same table.

Immediately before and after packaging, the wrapper captures and hashes both
`git rev-parse --verify HEAD` and the exact NUL-delimited output of `git status
--porcelain=v1 -z --untracked-files=all`.  Any byte of drift aborts before
network transfer.  The HEAD-capture and worktree-status hashes are retained in
the WMI provenance receipt.

The archive contains exactly:

- all files below `book/`, except `_build`, notebook checkpoints, host
  metadata, and bytecode caches;
- `requirements.txt`;
- `artifacts/peano-library/` and `research/arithmetic-library/`, needed by the
  generated theorem-atlas drift check;
- the complete `peano-lab/py/peano_lab/` package: the explorer generator reads
  the theorem stack together with the native term/formula grammar, PA axioms,
  proof constructors, and tactic registry;
- the persistent `pa-proof-tags.json` and `pa-proof-informal.json` registries
  below `research/arithmetic-library/`;
- both deterministic generators and the WMI package, build, integrity,
  submission, and Slurm scripts.

The archive does not include an existing `book/_build`, a local virtual
environment, proof-replay tests, Lambda/Peano interactive drivers, the QR
runner, Git metadata, or unrelated repository artifacts.  Notebook execution
is disabled by `book/_config.yml`, so no notebook runtime is required.

## Job environment boundary

Both SSH control scripts and the Slurm script use non-login Bash.  Before any
Python invocation on WMI they remove inherited `PYTHONPATH`, `PYTHONHOME`,
`VIRTUAL_ENV`, and every `CONDA_*` variable.  The job then invokes the absolute
interpreter
`/projects/wmi_conda/anaconda/2025.12-1/envs/pytorch-gpu/bin/python`.  This is
an **absolute interpreter in the reviewed WMI Conda environment; no activation
command is run**.  Its interpreter and base runtime still come from that
environment.  Inside a fresh per-job copied snapshot it creates
`.wmi-book-venv` with `python -m venv`, sets `PYTHONNOUSERSITE=1`, and installs
only:

```bash
python -m pip install --disable-pip-version-check --no-input \
  -r requirements.txt
```

No workstation package or inherited Python/virtual-environment search path is
visible.  The current `requirements.txt` uses bounded package ranges rather than hashes,
so package resolution is not bit-reproducible across time.  This is an honest
external boundary: the WMI pip configuration/index and the packages available
when the job runs determine the selected wheels.  The receipt therefore pins
the requirements hash, base interpreter, complete `pip freeze --all` output
hash, Jupyter Book version log, command logs, and all input/output manifests.

## Build and integrity gates

The required build command is exactly:

```bash
jupyter-book build book/ --warningiserror --keep-going
```

Before Sphinx is allowed to run, the job executes two non-mutating source
checks:

1. `python scripts/build_arithmetic_book_atlas.py --check` verifies that the
   committed theorem atlas is byte-current with its catalogs and theorem
   sources.
2. `python scripts/build_pa_proof_explorer.py --check` regenerates the complete
   557-page explorer in memory and rejects any drift in its persistent tags,
   corpus, graph, manifest, foundations, theorem pages, or aliases. The
   separately authored local CSS and JavaScript are pinned by the snapshot
   manifest and checked as required, byte-identical built-copy assets by the
   post-build integrity gate.

Only after both checks pass does the job run the strict Jupyter Book build.
Then [`check_wmi_book_build.py`](../scripts/check_wmi_book_build.py) checks
every TOC source has a nonempty HTML page and required Sphinx indexes/assets
exist. It additionally requires the explorer index, foundations, manifest,
corpus, graph, local CSS/JavaScript, and all 557 tag pages to have been copied
byte-for-byte. Every explorer relative `href`, `src`, and HTML fragment must
resolve; remote runtime assets, active-script links, HTML-injection sinks, and
targets escaping `book/_build/html` fail.
The checker emits deterministic source, explorer, and HTML tree manifests.

These checks intentionally do not replay embedded proof commands.  That is a
separate semantic CI/proof workload, not a lightweight book-build integrity
test.

Each run writes command stdout/stderr logs, `book-integrity.json`, and
`peano-book-build-JOBID.json` below the unique run's `logs/` directory.  The
Slurm scheduler stdout/stderr live only in `snapshot_root/logs`; staging and
scheduling never add a log directory or any other file to the immutable
`snapshot_root/source`.  The Slurm log prints the SHA-256 of both
machine-readable receipts.
