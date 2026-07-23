# VIASM 2026 — Automatic Theorem Proving in Mathematics
# Build & deploy targets. See docs/BUILD.md and docs/DEPLOY.md.

SERVER    := lts-faculty.wmi.amu.edu.pl
SITE      := ~/public_html/vietnam2026
LAB       := ~/public_html/lab-lambda
LABNEXT   := ~/public_html/lab-lambda-next
STAGE     := _deploy/vietnam2026
STAGENEXT := _deploy/lab-lambda-next

.PHONY: help book lean lab-serve stage deploy-site deploy-lab deploy-lab-next deploy clean

help:
	@echo "Targets:"
	@echo "  make book         build the JupyterBook (book/_build/html)"
	@echo "  make lean         build & axiom-check the Lean artifact"
	@echo "  make lab-serve    serve lab-lambda locally on :8001"
	@echo "  make stage        assemble _deploy/vietnam2026 (landing + book + slides)"
	@echo "  make deploy-site  rsync the site to $(SITE)"
	@echo "  make deploy-lab   rsync the browser lab to $(LAB)"
	@echo "  make deploy-lab-next  deploy the Web Worker preview to $(LABNEXT)"
	@echo "  make deploy       stage + deploy-site + deploy-lab"
	@echo "  make clean        remove build/stage artifacts"

book:
	jupyter-book build book/
	@# ensure a directory index exists (external-toc usually writes one)
	@[ -f book/_build/html/index.html ] || cp book/_build/html/intro.html book/_build/html/index.html

lean:
	cd artifacts/lean && lake build
	cd artifacts/lean && printf 'import Artifacts\nopen Artifacts Artifacts.Sqrt2\n#print axioms s_combinator\n#print axioms add_comm'"'"'\n#print axioms no_sqrt2\n' > /tmp/check.lean && lake env lean /tmp/check.lean | tee /dev/stderr | (! grep -q sorryAx)

lab-serve:
	@echo "→ http://localhost:8001/  (Ctrl-C to stop)"
	cd lab-lambda && python3 -m http.server 8001

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

deploy-lab:
	rsync -avz --delete --exclude '__pycache__' --exclude 'worker' lab-lambda/ $(SERVER):$(LAB)/

# Worker-based preview (Pyodide off the main thread + Stop) → /lab-lambda-next/
deploy-lab-next:
	rm -rf $(STAGENEXT) && mkdir -p $(STAGENEXT)
	cp lab-lambda/worker/index.html $(STAGENEXT)/index.html
	cp lab-lambda/worker/worker.js  $(STAGENEXT)/worker.js
	cp lab-lambda/.htaccess         $(STAGENEXT)/.htaccess
	rsync -a --exclude '__pycache__' --exclude 'tests' lab-lambda/py/ $(STAGENEXT)/py/
	rsync -a lab-lambda/vendor/ $(STAGENEXT)/vendor/
	rsync -avz --delete $(STAGENEXT)/ $(SERVER):$(LABNEXT)/
	@echo "Deployed worker preview → https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda-next/"

deploy: deploy-site deploy-lab
	@echo "Deployed:  https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026  +  /lab-lambda"

clean:
	rm -rf book/_build _deploy
	rm -rf artifacts/lean/.lake
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
