"""Builds RESULTS.md from results/, listing every run and marking the
reported batch (docker mode, not sham)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT / "results"

rows = []
for rec in sorted(RES.rglob("record.json")):
    r = json.loads(rec.read_text(encoding="utf-8"))
    rows.append(r)

lines = ["# Results", "",
         "Reported batch: docker mode, non-sham runs. Local and sham runs are listed for completeness.", ""]
for test in ("H2-I", "H2-X", "H2-A"):
    lines += [f"## {test}", "",
              "| Mode | Run | Baseline | Post | Predicted post | Outcome | Reported |",
              "|------|-----|----------|------|----------------|---------|----------|"]
    for r in rows:
        if r["test"] != test:
            continue
        mode = r["mode"] + ("-sham" if r.get("sham_control") else "")
        lines.append(f"| {mode} | {r['run']:02d} | {tuple(r['baseline_observed'])} | "
                     f"{tuple(r['post_observed'])} | {tuple(r['post_prediction'])} | "
                     f"{r['outcome']} | {'yes' if r.get('reported_batch_eligible') else 'no'} |")
    lines.append("")
    counts = {}
    for r in rows:
        if r["test"] == test and r.get("reported_batch_eligible"):
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    lines.append(f"Reported batch for {test}: " + ", ".join(
        f"{k} {counts.get(k, 0)}" for k in ("PASS", "FAIL", "AMBIGUOUS")) + ".")
    lines.append("")
(ROOT / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
print((ROOT / "RESULTS.md").read_text(encoding="utf-8"))
