# VIASM 2026 — Automatic Theorem Proving in Mathematics
# Build & deploy targets. See docs/BUILD.md and docs/DEPLOY.md.

SERVER    := lts-faculty.wmi.amu.edu.pl
SITE      := ~/public_html/vietnam2026
LAB       := ~/public_html/lab-lambda
LABNEXT   := ~/public_html/lab-lambda-next
# These are `rsync --delete` destinations.  Keep command-line Make variable
# overrides from widening either one to an unrelated remote directory.
override PEANO     := ~/public_html/peano-lab
override PEANONEXT := ~/public_html/peano-lab-next
STAGE     := _deploy/vietnam2026
STAGENEXT := _deploy/lab-lambda-next
PEANO_CORPUS_PYTHON ?= python3
# This path is a deletion target in `stage-peano`; command-line assignments
# must not be able to widen it beyond the repository's dedicated stage tree.
override STAGEPEANO := _deploy/peano-lab
override PEANOAPPID := a-f2054080fdc5

.PHONY: help book lean lab-serve peano-serve peano-corpus peano-corpus-smoke peano-eval stage \
	stage-peano deploy-site deploy-lab deploy-lab-next deploy-peano deploy-peano-next \
	deploy clean

help:
	@echo "Targets:"
	@echo "  make book         build the JupyterBook (book/_build/html)"
	@echo "  make lean         build & axiom-check the Lean artifact"
	@echo "  make lab-serve    serve lab-lambda locally on :8001"
	@echo "  make peano-serve serve the staged Peano Lab locally on :8002"
	@echo "  make peano-corpus reproduce the leakage-safe Peano train/val release"
	@echo "  make peano-corpus-smoke  run the all-ladder M9 generation/export smoke"
	@echo "  make peano-eval   run the deterministic kernel-judged random baseline"
	@echo "  make stage        assemble _deploy/vietnam2026 (landing + book + slides)"
	@echo "  make deploy-site  rsync the site to $(SITE)"
	@echo "  make deploy-lab   rsync the browser lab to $(LAB)"
	@echo "  make deploy-lab-next  deploy the Web Worker preview to $(LABNEXT)"
	@echo "  make deploy-peano  rsync Peano Lab to $(PEANO)"
	@echo "  make deploy-peano-next  deploy Peano Lab staging to $(PEANONEXT)"
	@echo "  make deploy       stage + deploy-site + deploy-lab"
	@echo "  make clean        remove build/stage artifacts"

book:
	rm -rf book/_build   # full rebuild: incremental Sphinx leaves stale sidebars after TOC changes
	jupyter-book build book/
	@# ensure a directory index exists (external-toc usually writes one)
	@[ -f book/_build/html/index.html ] || cp book/_build/html/intro.html book/_build/html/index.html

lean:
	cd artifacts/lean && lake build
	cd artifacts/lean && printf 'import Artifacts\nopen Artifacts Artifacts.Sqrt2\n#print axioms s_combinator\n#print axioms add_comm'"'"'\n#print axioms no_sqrt2\n' > /tmp/check.lean && lake env lean /tmp/check.lean | tee /dev/stderr | (! grep -q sorryAx)

lab-serve:
	@echo "→ http://localhost:8001/  (Ctrl-C to stop)"
	cd lab-lambda && python3 -m http.server 8001

peano-serve: stage-peano
	@echo "→ http://localhost:8002/  (Ctrl-C to stop)"
	cd "$(STAGEPEANO)" && python3 -m http.server 8002

# The committed learning release deliberately omits every ladder session.  Raw
# session JSONL remains a reproducible intermediate in /tmp; the manifest keeps
# its exact byte hash and the released transitions live under peano-lab/corpus/.
peano-corpus:
	@$(PEANO_CORPUS_PYTHON) -c 'import platform, sys; actual = f"{platform.python_implementation()} {platform.python_version()}"; expected = "CPython 3.10.0"; sys.exit(0 if actual == expected else f"byte-identical Peano corpus reproduction needs {expected}, got {actual}; override PEANO_CORPUS_PYTHON with that interpreter")'
	$(PEANO_CORPUS_PYTHON) scripts/generate_peano_traces.py \
		--output /tmp/peano-lab-release-raw.jsonl \
		--manifest peano-lab/corpus/generation-manifest.json \
		--seed 0 --renamed 1500 --commuted 96 --numeric 96 \
		--auto-depth 5 --auto-max-nodes 5000 \
		--no-ladder-auto --no-ladder-scripts
	$(PEANO_CORPUS_PYTHON) scripts/export_traces.py /tmp/peano-lab-release-raw.jsonl \
		--output-dir peano-lab/corpus --val-fraction 0.1 --seed peano-lab-v1

# The acceptance superset includes honest bounded-auto attempts and checked
# authored replays for every theorem-ladder entry.  It is not training input.
peano-corpus-smoke:
	$(PEANO_CORPUS_PYTHON) scripts/generate_peano_traces.py \
		--output /tmp/peano-lab-acceptance-raw.jsonl \
		--manifest /tmp/peano-lab-acceptance-manifest.json
	$(PEANO_CORPUS_PYTHON) scripts/export_traces.py /tmp/peano-lab-acceptance-raw.jsonl \
		--output-dir /tmp/peano-lab-acceptance-export

peano-eval:
	$(PEANO_CORPUS_PYTHON) scripts/eval_peano_policy.py --k 8 --max-steps 16 --seed 20260727

stage: book
	rm -rf $(STAGE) && mkdir -p $(STAGE)
	cp index.html $(STAGE)/index.html
	cp deploy/site.htaccess $(STAGE)/.htaccess
	cp -R assets $(STAGE)/assets
	cp -R book/_build/html $(STAGE)/book
	cp -R slides $(STAGE)/slides
	@echo "Staged site in $(STAGE)"

deploy-site: stage
	rsync -avz --delete $(STAGE)/ $(SERVER):$(SITE)/

# The lab IS the worker+self-hosted build (promoted 2026-07-24).
deploy-lab:
	rm -rf $(STAGENEXT) && mkdir -p $(STAGENEXT)
	cp lab-lambda/index.html $(STAGENEXT)/index.html
	cp lab-lambda/worker.js  $(STAGENEXT)/worker.js
	cp lab-lambda/.htaccess  $(STAGENEXT)/.htaccess
	rsync -a --exclude '__pycache__' --exclude 'tests' lab-lambda/py/ $(STAGENEXT)/py/
	rsync -a lab-lambda/vendor/ $(STAGENEXT)/vendor/
	rsync -avz --delete $(STAGENEXT)/ $(SERVER):$(LAB)/
	@echo "Deployed lab → https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/"

# Staging channel: identical assembly, deployed to /lab-lambda-next/
deploy-lab-next:
	rm -rf $(STAGENEXT) && mkdir -p $(STAGENEXT)
	cp lab-lambda/index.html $(STAGENEXT)/index.html
	cp lab-lambda/worker.js  $(STAGENEXT)/worker.js
	cp lab-lambda/.htaccess  $(STAGENEXT)/.htaccess
	rsync -a --exclude '__pycache__' --exclude 'tests' lab-lambda/py/ $(STAGENEXT)/py/
	rsync -a lab-lambda/vendor/ $(STAGENEXT)/vendor/
	rsync -avz --delete $(STAGENEXT)/ $(SERVER):$(LABNEXT)/
	@echo "Deployed staging → https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda-next/"

# Peano Lab uses its own local vendor mirror.  Its staged release namespaces
# are served by `make peano-serve`; scripts/fetch_vendor.sh creates both mirrors.
stage-peano:
	@bash scripts/verify_peano_vendor_manifest.sh >/dev/null || \
		{ echo "Peano Lab vendor verification failed; rerun: bash scripts/fetch_vendor.sh" >&2; exit 1; }
	@bash scripts/update_peano_app_manifest.sh --check >/dev/null || \
		{ echo "Peano Lab application manifest is stale; run scripts/update_peano_app_manifest.sh" >&2; exit 1; }
	@test "$$(shasum -a 256 peano-lab/APP_MANIFEST.sha256 | cut -c1-12)" = "$(patsubst a-%,%,$(PEANOAPPID))" || \
		{ echo "PEANOAPPID does not match APP_MANIFEST.sha256" >&2; exit 1; }
	@grep -Fq 'const APP_ROOT="releases/$(PEANOAPPID)/";' peano-lab/index.html || \
		{ echo "index.html APP_ROOT does not match PEANOAPPID" >&2; exit 1; }
	@grep -Eq 'const BUILD="[^"]+";' peano-lab/index.html || \
		{ echo "index.html has no human-facing BUILD" >&2; exit 1; }
	rm -rf "$(STAGEPEANO)" && mkdir -p "$(STAGEPEANO)/releases/$(PEANOAPPID)"
	cp peano-lab/index.html "$(STAGEPEANO)/index.html"
	cp peano-lab/.htaccess  "$(STAGEPEANO)/.htaccess"
	cp peano-lab/worker.js "$(STAGEPEANO)/releases/$(PEANOAPPID)/worker.js"
	cp peano-lab/APP_MANIFEST.sha256 "$(STAGEPEANO)/releases/$(PEANOAPPID)/APP_MANIFEST.sha256"
	rsync -a --delete --exclude '/tests/***' --exclude '__pycache__/' --exclude '.pytest_cache/' --include '*/' --include '*.py' --exclude '*' peano-lab/py/ "$(STAGEPEANO)/releases/$(PEANOAPPID)/py/"
	rsync -a --delete peano-lab/vendor/ "$(STAGEPEANO)/vendor/"
	@echo "Staged Peano Lab in $(STAGEPEANO)"

# Production channel.  Promotion policy is documented in PLAN/09_peano_lab.md.
deploy-peano: stage-peano
	rsync -avz "$(STAGEPEANO)/.htaccess" "$(STAGEPEANO)/vendor" "$(STAGEPEANO)/releases" $(SERVER):$(PEANO)/
	rsync -avz "$(STAGEPEANO)/index.html" $(SERVER):$(PEANO)/index.html
	@echo "Deployed Peano Lab → https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/"

# Staging channel: byte-for-byte the same assembled tree, under /peano-lab-next/.
deploy-peano-next: stage-peano
	rsync -avz "$(STAGEPEANO)/.htaccess" "$(STAGEPEANO)/vendor" "$(STAGEPEANO)/releases" $(SERVER):$(PEANONEXT)/
	rsync -avz "$(STAGEPEANO)/index.html" $(SERVER):$(PEANONEXT)/index.html
	@echo "Deployed Peano Lab staging → https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/"

deploy: deploy-site deploy-lab
	@echo "Deployed:  https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026  +  /lab-lambda"

clean:
	rm -rf book/_build _deploy
	rm -rf artifacts/lean/.lake
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
