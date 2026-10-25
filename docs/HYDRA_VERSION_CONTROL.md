# Hydra source preservation and recovery

Hydra belongs to [nasqret/vietnam2026](https://github.com/nasqret/vietnam2026).
The October 25 preservation separates the accumulated Hydra work from newer
changes already on the remote `peano-lab` branch. It does not reset or overwrite
that branch.

| Branch | Purpose |
| --- | --- |
| `agent/hydra-preservation-2026-10-25` | Source, configuration, tests, proof gallery, selected experiment evidence, and local training changes, based on `ff5333db11cb7be9b1595e9f377c5c1e0b759493` |
| `archive/hydra-native-20260831` | Exact frozen native/training source, ending at `dca88930b59e3147a95d0234d804076ccf757a74` |
| `peano-lab` | Existing development branch; observed remote head was `2b4400ba4f3543369cd52549a85d0f70f92f2b11` during preservation |

These are separate histories. The native archive contains two commits, including
the independent root `4aeae795c8cb5bfc622c9943359b5b38446089b9`. Its pinned source
catalogue covers 896 files and 91,225,189 bytes. Publishing its existing history
preserves the actual source commit rather than substituting a new kernel snapshot.

## What is in source control

The preservation branch includes the playground frontend and server, model and
symbolic integrations, native checking adapters, training tools, tests, the
experimental native source, checked lemma certificates, and the proof gallery.
Selected source and evidence under `output/` are retained too: that directory
contains runtime implementation, not just disposable results. In particular,
the deployed WMI provider, tokenizer-length cache, frozen WMI helpers, and their
manifests must accompany the playground.

The frozen source's three ignored custody files are backed up byte-for-byte in
[`hydra-playground/archive/native-custody`](../hydra-playground/archive/native-custody/).
Its [`restore-manifest.json`](../hydra-playground/archive/native-custody/restore-manifest.json)
records each archive filename, original relative destination, byte count, and
SHA-256. These files are not part of the native archive's Git tree. They are
evidence of historical runs, not instructions to run those jobs again.

Ordinary Git deliberately excludes model tensors, generated environments and
solver binaries, repeated transfer/source bundles, large generated datasets,
private operational notes, credentials, caches, and temporary process records.
[`hydra-external-assets.json`](hydra-external-assets.json) identifies four important
local model files by freshly read byte counts and hashes. It is an inventory,
**not a claim that their bytes have been backed up remotely**. Recovering those
files still requires an existing trusted copy or separately arranged artifact
storage; no download service is implied by a hash.

## Recover the preserved source

After both branches have been published, these commands obtain the source trees
without running training, inference, a server, or any historical launcher:

```sh
git clone --branch agent/hydra-preservation-2026-10-25 https://github.com/nasqret/vietnam2026.git hydra-source
cd hydra-source
git fetch origin refs/heads/archive/hydra-native-20260831:refs/remotes/origin/archive/hydra-native-20260831
git worktree add --detach _deploy/hydra-retention-evaluation-recovery-execution-20260831 dca88930b59e3147a95d0234d804076ccf757a74
```

Use a fresh destination. Do not remove or overwrite an existing `_deploy` checkout
to make these commands succeed. The detached worktree is intentional: it preserves
the exact historical source identity.

Restore the three custody files from the committed manifest only after the native
tree exists. This script verifies archived bytes and refuses to replace a different
existing file. Run it from the repository root; it performs no model work:

```sh
python3 -I -B - <<'PY'
import hashlib
import json
from pathlib import Path

manifest = Path("hydra-playground/archive/native-custody/restore-manifest.json")
native = Path("_deploy/hydra-retention-evaluation-recovery-execution-20260831")
if not (native / "peano-lab/py/peano_lab").is_dir():
    raise SystemExit("Restore the exact native Git worktree first.")
for entry in json.loads(manifest.read_text())["files"]:
    source, target = Path(entry["archive_file"]), Path(entry["restore_path"])
    raw = source.read_bytes()
    if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise SystemExit("Archive integrity failure: " + str(source))
    if target.is_symlink() or any(parent.is_symlink() for parent in target.parents):
        raise SystemExit("Refusing a symlink destination: " + str(target))
    if target.exists():
        if target.read_bytes() != raw:
            raise SystemExit("Refusing to overwrite different bytes: " + str(target))
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(raw)
print("Native custody metadata restored; no inference or training was run.")
PY
```

## Source recovery is not a ready-to-run model installation

The preserved system was authenticated in one local workspace. Some immutable
manifests, setup receipts, and historical artifact locations contain absolute
paths. The current provider also checks a chain of earlier training receipts,
source trees, tokenizer files, dataset identities, and model artifacts. Restoring
the two Git trees and the three custody files does not restore that entire chain.

Actual inference additionally needs the local base-model conversion, pinned
Python/MLX packages, selected adapter tensors, historical custody dependencies,
and compatible Apple Metal hardware. Symbolic modes need their selected solver
installation. The generated `hydra-playground/.runtime/` is not committed.
The previous adapter's metadata and tokenizer are preserved, but its adapter
tensors remain an external asset.

Do not edit sealed manifests, remove hash checks, invent setup-completion receipts,
or change historical source identities to make a new machine appear ready. A
portable installation requires a separately reviewed installation/admission path
that preserves the old evidence and records its own actual checks. This commit
preserves source and selected scientific evidence; it is not a complete machine
backup or a verified fresh-machine deployment.

## Keep future work committed

Use a focused branch and explicitly select reviewed source files. Check for
credentials, machine-local access details, accidental datasets, and large files
before staging. Then inspect the exact staged changes before committing:

```sh
git status --short
git diff
git add -- path/to/reviewed-source.py path/to/reviewed-test.py
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "Describe the concrete Hydra change"
git push origin HEAD
```

The root ignore rules exclude `output/` and private operational directories by
default. Already tracked reviewed files remain tracked. A new source or evidence
file under an ignored directory requires an explicit, narrowly scoped
`git add -f -- exact/path`; never force-add the whole directory. Document why it
belongs in source control and inspect its contents and size first. Model weights
need separate artifact storage, not an exception to this source-review rule.

Do not force-push shared branches. Do not merge this preservation branch wholesale
over later `peano-lab` work: compare the histories and integrate reviewed changes
deliberately. Retained experiment launchers, allocation packets, and receipts must
not be automatically rerun during checkout, testing, or recovery. A historical
approval or completed job receipt is not a fresh job reservation.
