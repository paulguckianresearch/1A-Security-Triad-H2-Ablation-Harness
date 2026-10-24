# Paper 1A H2 Ablation Harness

A reproducible Docker/Python harness for the controlled single-mechanism
independence experiment specified in Section 9 of:

> *Security Triad: Interface, Execution Pathway and Authority as the
> Structural Conditions of Cyber-Mediated Operation* (Paper 1A)

The experiment tests H2 (Section 4.3): that each of the three structural
conditions can be removed from one fixed mechanism, by an ordinary control,
while the other two are independently verified unchanged.

| Test | Condition removed | Control (Paper 1A Table 3) | Predicted post-ablation (I, X, A, O) |
|------|-------------------|----------------------------|--------------------------------------|
| H2-I | Interface | admission denied for the source (segmentation) | (0, 1, 1, 0) |
| H2-X | Execution Pathway | route from admission to worker disabled (patching, disabling functionality) | (1, 0, 1, 0) |
| H2-A | Authority | write control over the protected state withdrawn (least authority) | (1, 1, 0, 0) |

Baseline prediction for every test is (1, 1, 1, 1).

## Lineage

This harness is derived from experiment I-1 of the H4 Ablation Harness,
which accompanies the companion manuscript on relational extension (Paper 1B):

> H4 Ablation Harness, v1.0.0. https://doi.org/10.5281/zenodo.22711457

I-1's receiver, admission relation, X marker and Authority probe are kept.
Two further ablations are added on the same receiver so that all three
dissociated states of Paper 1A Section 4.3 are produced on one mechanism,
and the X marker now records in memory so that the route can be verified
present while write control is withheld. There is one mechanism, one source
as the input's origin, no relation classification and no governance
assignment: this is the node-level experiment, not the relational one.

## Release status

- **v0.1.0 (this release): pre-registration.** Manifests, predictions and
  harness frozen (`FROZEN_SHA256SUMS.txt`); `results/` holds only local
  calibration runs on Linux (H2-I, H2-X, H2-A each 5/5 PASS; sham 2/2 FAIL
  per test), which are not the reported batch.
- **v1.0.0 (to follow): results.** The Docker batch run after v0.1.0 was
  deposited, with every run's evidence bundle and `RESULTS.md`.

See `docs/PUBLICATION_CHECKLIST.md` and `DEPOSIT.md`.

## Layout

```
paper1a-h2-ablation/
├── README.md
├── LICENSE                 MIT
├── CITATION.cff
├── CHANGELOG.md
├── run_h2.py               runner (docker and local modes, sham control)
├── summarise.py            builds RESULTS.md from results/
├── FROZEN_SHA256SUMS.txt   hashes of every file frozen at v0.1.0
├── DEPOSIT.md              GitHub and Zenodo steps
├── Run-All-H2.ps1          Windows convenience script
├── manifests/              fixed specification and predictions, one per test
├── docs/EVIDENCE_RULES.md  presence and absence warrants, classification
├── experiments/H2/         receiver, source, compose file
└── results/                append-only evidence bundles
    └── H2-<I|X|A>/<docker|local|docker-sham|local-sham>/run-NN/
```

## Modes

**docker** (the reported mode). Every run rebuilds the receiver and source
containers from scratch. The receiver runs as the unprivileged user `h2`;
`admin.py` runs as root inside the receiver container and is the
administrator identity for the Authority ablation.

**local** (development check). The same `receiver.py` runs on the host as an
unprivileged user, with the runner as root acting as the administrator.
Linux or macOS only. Local results are written under `results/H2-*/local/`
and are not the reported batch.

## Running

```
python run_h2.py --dry-run                      # validate, print hashes
python run_h2.py --execute --runs 5             # docker, all three tests, 5 runs each
python run_h2.py --execute --runs 2 --sham      # harness control, expected FAIL
python summarise.py                             # write RESULTS.md
```

On Windows, `Run-All-H2.ps1` runs the dry run, five reported runs per test
and two sham runs per test, then builds `RESULTS.md`.

## Evidence rules

`docs/EVIDENCE_RULES.md` holds the full rules. They implement the four
measurement requirements of Paper 1A Section 9: one condition removed; the
other two verified by evidence independent of the intervention; the removed
condition established absent affirmatively; and the operation's failure
never used as evidence of absence.

## Result interpretation

The runner reports PASS, FAIL or AMBIGUOUS per run. A PASS supports H2 for
this mechanism: the dissociated state was produced and the unaffected
conditions were verified present. It does not establish anything about
other mechanisms, about completeness (H1) or about reproducibility between
analysts (H3). The sham control shows that the classifier returns FAIL when
no ablation is applied.

## Requirements

- Docker Desktop or Docker Engine with Compose v2 (docker mode)
- Python 3.10+, standard library only
- Root on Linux or macOS (local mode only)

## Author

Paul Guckian, Independent Researcher, London, United Kingdom
