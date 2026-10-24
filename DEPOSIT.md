# Depositing this harness (step by step)

## 1. GitHub

```
cd paper1a-h2-ablation
git init
git add .
git commit -m "Paper 1A H2 ablation harness v0.1.0 (pre-registration release)"
git tag -a v0.1.0 -m "Pre-registration release: frozen manifests and harness, local calibration runs only"
# create an empty public repo on GitHub, e.g. paulguckian7/Paper1A-H2-Ablation-Harness, then:
git remote add origin https://github.com/paulguckian7/Paper1A-H2-Ablation-Harness.git
git push -u origin main --tags
```

## 2. Zenodo

Either enable the Zenodo GitHub integration for the repository and create
a GitHub Release from tag `v0.1.0` (Zenodo archives it automatically), or
upload the release zip manually as a new upload. Set:

- Resource type: Software
- Title: Paper 1A H2 Ablation Harness
- Version: 0.1.0
- Licence: MIT
- Related identifiers: *is derived from* 10.5281/zenodo.22711457 (H4 Ablation Harness); *is supplement to* the Paper 1A manuscript (add the DOI once published)
- Description: paste the README's first two sections and state that this release precedes the confirmatory batch.

Record the version DOI and the concept DOI in `CITATION.cff` (field `doi`)
on the next commit.

## 3. Run, then release v1.0.0

Follow `docs/PUBLICATION_CHECKLIST.md` Stages 2 and 3. The results release
is a new Zenodo version under the same concept DOI.

## 4. What goes in the paper

- Section 6.6: "[DOI HARNESS]" becomes the v1.0.0 version DOI.
- The sentence "the harness and its predictions were deposited before the confirmatory batch" cites the v0.1.0 version DOI.
- `\newcommand{\HtwoRuns}` and `\newcommand{\HtwoSham}` are set from `RESULTS.md`.
