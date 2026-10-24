# Changelog

## 0.1.0 - 2026-10-24

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
