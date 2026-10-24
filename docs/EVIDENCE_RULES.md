# Evidence Rules

These rules implement the four measurement requirements stated in Paper 1A,
Section 9 (Independence), for a single analysed mechanism. They are derived
from the evidence rules of the H4 Ablation Harness
(https://doi.org/10.5281/zenodo.22711457), which apply the same discipline
one level up, to relations between mechanisms.

1. The intervention removes one condition only.
2. Each unaffected condition is verified present by evidence obtained
   independently of the intervention, and not inferred from the intervention
   having been aimed elsewhere.
3. The removed condition is established absent affirmatively, from
   access-control, configuration or route evidence meeting the absence
   criterion of Paper 1A Sections 3.3 to 3.5.
4. Absence is never inferred from the operation failing. O is recorded, and
   O = 0 is consistent with all three conditions being present.

## Presence

**Interface present.** An `interface_admit` event for the tested source at
the nominated Interface (`/push`), and an admitted response to that source.

**Execution Pathway present.** A benign marker (`X_MARKER`) enters the
post-admission path of the nominated Interface through the receiver's
internal socket, follows the same route as admitted work (payload parsing,
route dispatch, queue, worker dispatch, handler entry), and is observed at
entry to the same acting handler (`x_marker_reached_handler`). The marker
branches off before the state write and records in memory, so observing the
route does not depend on write control over the protected state.

**Authority present.** Both legs:

1. access-control state for the acting mechanism, read inside the receiver
   process under its own execution identity (`ACCESS_STATE`), grants write
   on the protected state file and its directory; and
2. the same receiver process, under the same identity, performs a benign
   write to the protected state (`AUTHORITY_PROBE`, logged
   `authority_probe_write`). The probe is submitted to the worker directly
   and does not depend on the admission relation or the route.

## Absence

**Interface absent (H2-I).** All of: configuration evidence of a
source-specific denial at the nominated Interface (policy names the source
address); a logged rejection of an attempt from that source
(`interface_reject`); and a rejected response (HTTP 403) to that attempt.

**Execution Pathway absent (H2-X).** All of: configuration evidence that the
nominated route is absent (`route_admission_to_worker` false); evidence that
input was admitted (`interface_admit` for the source, admitted response); a
`route_absent` event for the source's input and for the marker; the marker
returning unrouted; and non-observation of `handler_reached` and
`x_marker_reached_handler` in the post window, where the baseline window
observed both.

**Authority absent (H2-A).** All of: access-control state read inside the
receiver process showing write withheld on the protected state file and its
directory; a denial record for a same-identity attempt by the probe
(`authority_denied`, attempt `authority_probe`, with the `PermissionError`);
a denial record for the source's admitted and routed operation
(`authority_denied`, attempt `operation_write`); and `handler_reached` for
that operation, showing the route was traversed before the denial.

## Redesign is not ablation

No mechanism, identity, source, route or enforcement point may be created,
split, duplicated or replaced (Paper 1A Section 5.1, prohibited moves). Each
ablation changes the state of something that already exists: an admission
policy entry, a route switch, a permission bit.

## Classification

A value is recorded 0 only on affirmative absence evidence and 1 only on
affirmative presence evidence. A run is PASS when baseline and post-ablation
tuples match the manifest's predictions with every value carrying its own
warrant; FAIL when any value with affirmative evidence contradicts a
prediction; AMBIGUOUS when nothing contradicts the prediction but some
warrant is missing. A PASS supports H2 for the tested mechanism only.

## Harness control

The `--sham` option applies no ablation and tests the post-ablation
prediction regardless. The expected outcome is FAIL on every sub-ablation.
A harness that passed a sham run would be reporting its own predictions
rather than the system under test. Sham results are kept under
`results/H2-*/<mode>-sham/` and are never counted in the reported batch.
