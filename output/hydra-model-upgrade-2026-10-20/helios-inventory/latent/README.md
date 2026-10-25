# Latent Proof Lab

Private research on **recurrent transformer depth for verified Heyting arithmetic proofs**, starting from [Geiping et al., arXiv:2502.05171v2](https://arxiv.org/abs/2502.05171v2).

The programme has three independent obligations: understand the architecture mathematically, establish controlled empirical comparisons, and connect every proof claim to a pinned constructive checker. Extra hidden-state updates are computational work, not proof steps or a correctness guarantee.

**Active Campaign 5:** twelve **Qwen3-1.7B-Base** LoRA runs compare vanilla, fixed recurrence, random depth and learned stopping at three paired seeds. Each targets 2,048 updates on an expanded, independently admitted corpus: 2,580 train, 192 development and 384 test sessions, with a common 6,144-token context. Training uses balanced sampling, proof-based checkpoint selection and staged adaptive-depth supervision. The base weights are frozen; rank-32 LoRA trains about 34.9M parameters, with up to four shared-core passes.

Helios training jobs **24730085 / 24730087 / 24730089** and dependent inference jobs **24730086 / 24730088 / 24730090** were submitted on October 16. Raw 128-development/256-test proof evaluation, assisted development inference and training-only encounter collection are separate phases. WMI **285228** runs a longer old-data control. See the [Campaign 5 account](docs/book/campaign5.md), [protocol](research/campaign5-protocol.md), [execution ledger](status/campaign5.json) and [independent registration review](research/agents/c5_audit/registration-review.md). Expanded-data learning and recurrence advantage remain unestablished.

**Audited early progress:** the longer vanilla control improved from **7/32** development proofs at update 512 to **11/32** at update 1,024, with five gains and one regression on the same roster. Independent native replay **285260** passed. This is within-run development progress; the expanded-data recurrent comparison and final-test improvement remain open. See the [duration review](research/agents/c5_audit/duration-development-review.md).

The preceding harder-task comparison completed all four WMI 512-update arms and 22 development/test policy suites; these saved outputs now passed independent native replay. On 48 test targets, vanilla solved 6 and fixed recurrence solved 6/7/4 at depths 1/2/4. Helios remained partial. This establishes no recurrence advantage. The [independent main audit](research/agents/c5_audit/campaign4-review.md) preserves the completed and incomplete conditions; earlier pilot [results](docs/book/harder-results.md) and [paired outcomes](docs/book/harder-paired-results.md) remain distinct.

**[Open the live training dashboard](http://127.0.0.1:8766/dashboard/training/index.html).** Reconnect with `bash scripts/preview_campaign2.sh` if the SSH tunnels have closed. The servers continue training when the laptop sleeps. See the [Qwen mathematical account](docs/book/qwen-recurrence.md), [frozen protocol](research/campaign3-protocol.md), [independent review](research/agents/qwen_referee/review-report.md) and [operations guide](docs/book/operations.md).

The earlier 2,000-update campaign used WMI 285072 and Helios 24676117. At its 2026-10-14 19:15 UTC snapshot, all four WMI runs and two Helios runs had completed; Helios continued with the remaining conditions. Both GPU environments had passed 116 tests and an exact interrupted/resumed state comparison. The dashboard provides current progress and preserves the earlier campaigns separately.

The preceding small-model campaign completed all 18 runs at 6,000 updates. Its six conditions and three seeds remain available in the dashboard's campaign selector. Final held-out evaluation is still pending; training completion does not establish proof improvement.

## Start here

- [Random-depth recurrence PDF](output/pdf/random-depth-recurrence.pdf), [annotated PDF](output/pdf/random-depth-recurrence-annotated.pdf), and [LaTeX source](docs/latex/random-depth-recurrence.tex): exact Campaign 5 methodology plus a four-page results appendix with five charts and two tables. [Method review](research/agents/random_depth_note_review/REVIEW.md) and [results audit](research/agents/results_appendix_review/REVIEW.md) distinguish source checks, saved-output recount and the remaining native-replay scope.
- [Research memory](MEMORY.md), [journal](JOURNAL.md), [live plan](PLAN.md).
- [Research book source](docs/book/index.md); built HTML is fetched to `artifacts/site/book/index.html`.
- [Interactive labyrinth dashboard](labyrinth/dashboard/index.html), with source and operation notes in [labyrinth/README.md](labyrinth/README.md).
- [Obsidian vault](obsidian-vault/Home.md).
- [Machine status](status/project_status.json), [compute policy](research/COMPUTE.md), [experiment protocol](docs/book/experiments.md).
- [Paper audit](research/agents/paper/paper-analysis.md) and [Peano audit](research/agents/peano/peano-audit.md), with independent review in `research/agents/referee/`.

The initial experiment is a deliberately narrow closed-addition certificate canary. It compares a small recurrent decoder with an approximately parameter-matched finite-depth transformer and a block-depth-matched transformer. Model-selected answers and rule counts are compiled to Peano proof objects and checked in Lean. This is not direct generation of arbitrary proof syntax, a replication of Huginn, or evidence of induction capability.

**First completed result:** WMI 284986 trained six models in an 89-second GPU allocation. Extra recurrence beyond two steps did not improve accepted counts; all models failed the held-out right-operand/longer-certificate split. Validation passed 79 tests and 192 fixture checks. Independent audit 284990 checked all 1,834 predictions and replayed 1,826 well-formed certificates. These are finite empirical results, with full limitations in [the results](docs/book/results.md) and [independent review](research/agents/referee/pilot-review.md).

## Operating the project

All model runs, numerical tests, notebook execution and document builds use Helios or WMI SLURM. The laptop is a control plane. The initial pilot used WMI; a fresh quota probe admitted Helios for campaign 2. Re-probe current state before every new campaign. The training dashboard and its read-only metadata services run on the servers and are viewed through localhost SSH tunnels.

```bash
./scripts/queue_report.sh
./scripts/submit_wmi.sh --test-only slurm/validate-wmi.sbatch
./scripts/submit_wmi.sh --submit slurm/validate-wmi.sbatch
./scripts/submit_wmi.sh --submit slurm/pilot-wmi.sbatch
./scripts/submit_wmi.sh --submit slurm/audit-wmi.sbatch
./scripts/submit_wmi.sh --submit slurm/docs-wmi.sbatch
```

Validation must succeed before pilot submission. Do not submit an already completed job again merely to refresh documentation. Scripts sync without deletion and exclude model weights and unrelated projects.

The audit and documentation jobs default to archived run 284986; set `LATENT_RUN_ID` in the remote submission environment to select a later completed run. The manual GitHub Actions workflow uses an isolated WMI directory and requires a dedicated self-hosted control runner; that runner is not configured yet.

The managed workspace protects `.git`, so local metadata is in `.local-git`. Use `./scripts/git.sh status`, `./scripts/git.sh log`, and other ordinary Git subcommands through that wrapper. The private remote is [nasqret/latent](https://github.com/nasqret/latent). Large raw sources and checkpoints stay outside Git; immutable references and hashes are tracked. No public website has been authorized.

## Evidence vocabulary

The labyrinth distinguishes standard/literature mathematics (T1), new proofs (T2, with review), independently validated exhaustive finite computation (T3), empirical evidence (T4), tested conjectures (T5), and speculative directions (T6). Passing a neural benchmark remains T4 even when every generated certificate is checked. The checked certificates establish their individual formulas; they do not prove a model's general competence.


The harder-task comparison is documented in [the task chapter](docs/book/harder-tasks.md)
and [measured results](docs/book/harder-results.md). Its frozen four-arm protocol
is in [research/campaign4-protocol.md](research/campaign4-protocol.md), with exact
jobs and replay scope in [the ledger](artifacts/campaign4/job-ledger.json) and
[independent review](research/agents/hard_referee/review-report.md). The live
[training observatory](http://127.0.0.1:8766/dashboard/training/index.html) separates
training curves, selected coverage, proof families and recurrence policies.
