# Changelog

## 0.2.0 - 2026-10-24

Declared harness revision before the pre-registration deposit (nothing had been deposited at 0.1.0).

### Added
- H2-P processing interdiction: a worker content rule refuses the write with admission, route and control unchanged; predicted (1,1,1,0). Puts Eq. (6) at risk and records that the Authority probe succeeds while the filter is active.
- H2-N null intervention: log verbosity changed; predicted (1,1,1,1). Specificity control.
- Restoration phase in every run: baseline re-measured after restore; predicted (1,1,1,1) with O returning; reported as a separate outcome.
- `restored_prediction` field in every manifest; `kind` field in `record.json`.
- Shams run for the three denials only (a sham of H2-N is trivial and a sham of H2-P adds nothing beyond H2-N).

### Pilot
- The 0.1.0 Docker batch (Windows, 2026-10-24: I, X, A each 5/5 PASS; sham 2/2 FAIL per test) is retained under `results-pilot-v0.1.0/` as a pre-specified pilot, not pre-registered, and is not the reported batch.

### Floor case considered and not added
- A receiver with the admission check inside the handler was considered as a test of the decomposition floor. It does not discriminate: either the in-handler check is nominated as the Interface and the conditions separate again, or admission and write are one atomic step and no marker can be injected, giving AMBIGUOUS by construction. Recorded here so the omission is visible.

## 0.1.0 - 2026-10-24

Pre-release fix before deposit: the Unix-only `pwd` import moved inside the local backend so the runner starts on Windows (docker mode never needed it).

Initial harness, derived from H4 Ablation Harness I-1 (10.5281/zenodo.22711457).

### Kept from I-1
- Receiver with `/push` admission relation keyed on client address, worker, protected state file, event log.
- X marker entering the post-admission path through an internal Unix socket and observed at handler entry.
- Two-leg Authority probe: access-control state read inside the receiver process, plus a same-identity write.
- Clean rebuild per run, append-only evidence bundles, SHA-256 of all source files in `record.json`.

### Added
- H2-X: a standing route switch between admission and the worker (`SET_ROUTE off`), with `route_absent` events and the marker returning unrouted.
- H2-A: write control as group permission on files owned by an administrator identity; `admin.py` (root) withdraws and restores it. `entrypoint.sh` establishes the baseline access-control state before dropping to the receiver identity.
- The X marker records in memory, not in the protected state, so the route can be verified present while Authority is withheld.
- `save_json` writes in place so the protected state keeps its owner across writes.
- Local mode (same receiver on the host as an unprivileged user) for development checks.
- Sham control (`--sham`): no ablation applied, prediction tested anyway, expected FAIL.
- Classifier distinguishes contradiction (FAIL) from missing warrant (AMBIGUOUS); a value is 0 only on affirmative absence evidence and 1 only on affirmative presence evidence.

### Development results (not the reported batch)
Local mode on Linux, 2026-10-24: H2-I, H2-X, H2-A each 5/5 PASS; sham 2/2 FAIL per test.
