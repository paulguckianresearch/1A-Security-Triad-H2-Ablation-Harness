# Publication Checklist (two-stage deposit)

The confirmatory evidence is pre-registered only if the frozen harness and
predictions are publicly deposited before the confirmatory batch is run.
Hence two releases.

## Stage 1: v0.2.0, pre-registration release (before the confirmatory Docker run)

- [ ] `python run_h2.py --dry-run` validates and prints hashes matching `FROZEN_SHA256SUMS.txt`.
- [ ] `results/` contains only `local/` and `local-sham/` calibration runs (development, Linux); the 0.1.0 Docker pilot sits in `results-pilot-v0.1.0/`.
- [ ] Push to a public GitHub repository; create release tag `v0.2.0`.
- [ ] Zenodo: archive the release (GitHub integration or manual upload). Record the **version DOI** for v0.2.0 and the **concept DOI**.
- [ ] Do not edit any file listed in `FROZEN_SHA256SUMS.txt` after this point without declaring a harness revision in `CHANGELOG.md`.

## Stage 2: run the confirmatory batch

- [ ] Windows: `.\Run-All-H2.ps1` (dry run, 5 reported runs per test, 2 sham per test, `RESULTS.md`).
- [ ] Confirm every `results/H2-*/docker/run-NN/record.json` has `source_sha256` matching `FROZEN_SHA256SUMS.txt`.
- [ ] Preserve every PASS, FAIL and AMBIGUOUS outcome. A FAIL is a result, not a reason to rerun.
- [ ] Record Docker Desktop and Compose versions (already written to `versions.txt` per run).

## Stage 3: v1.0.0, results release

- [ ] Commit `results/` and `RESULTS.md`; update `CHANGELOG.md` (results section only; frozen files untouched).
- [ ] Tag `v1.0.0`; Zenodo archives it as a new version under the same concept DOI.
- [ ] In the paper: cite the v1.0.0 **version DOI** as [DOI HARNESS]; cite the v0.2.0 version DOI in the sentence stating that the harness and predictions were deposited before the confirmatory batch; set `\HtwoRuns` and `\HtwoSham` from `RESULTS.md`.
- [ ] Describe the result as pre-registered only if Stage 1 preceded Stage 2.

## Never

- Reword a manifest prediction after a run.
- Count local or sham runs in the reported batch.
- Describe H2 as proved; report support or falsification for the tested mechanism.
