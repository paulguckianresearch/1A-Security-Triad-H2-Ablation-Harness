"""Runner for the Paper 1A H2 single-mechanism ablation (H2-I, H2-X, H2-A).

Derived from run_i1.py of the H4 Ablation Harness
(https://doi.org/10.5281/zenodo.22711457).

Two backends:
  docker  the reported mode: a clean rebuild of the receiver and source
          containers for every run, as in the parent harness.
  local   a development check: the same receiver.py run as an unprivileged
          user on this host, with the runner as root acting as the
          administrator identity. Results are written under results/local/
          and are never the reported batch.

Every run measures all four quantities independently in a baseline phase,
applies exactly one ablation, measures all four again, restores, and writes
an evidence bundle. Failure of the operation is recorded as O and is never
used as evidence that a condition is absent (docs/EVIDENCE_RULES.md).
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "experiments" / "H2"
HARNESS_VERSION = "0.2.0"

ABLATIONS = {
    # Structural denials (H2): one condition removed, two verified present.
    "I": {"manifest": "H2-I.yaml", "post": [0, 1, 1, 0], "kind": "denial"},
    "X": {"manifest": "H2-X.yaml", "post": [1, 0, 1, 0], "kind": "denial"},
    "A": {"manifest": "H2-A.yaml", "post": [1, 1, 0, 0], "kind": "denial"},
    # Processing interdiction: all three present, operation does not occur.
    "P": {"manifest": "H2-P.yaml", "post": [1, 1, 1, 0], "kind": "interdiction"},
    # Null intervention: a change touching none of the three.
    "N": {"manifest": "H2-N.yaml", "post": [1, 1, 1, 1], "kind": "null"},
}
BASELINE = [1, 1, 1, 1]
RESTORED = [1, 1, 1, 1]

SOURCE_FILES = [
    ROOT / "run_h2.py",
    EXP / "docker-compose.yml",
    EXP / "receiver" / "Dockerfile",
    EXP / "receiver" / "entrypoint.sh",
    EXP / "receiver" / "receiver.py",
    EXP / "receiver" / "internal_probe.py",
    EXP / "receiver" / "admin.py",
    EXP / "source" / "Dockerfile",
    EXP / "source" / "send.py",
] + [ROOT / "manifests" / v["manifest"] for v in ABLATIONS.values()]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def last_json_line(out):
    for line in reversed(out.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except Exception:
                pass
    return {"raw": out}


# ---------------------------------------------------------------- backends

class DockerBackend:
    name = "docker"
    base = "http://127.0.0.1:18082"

    def sh(self, *args, check=True, cwd=None):
        p = subprocess.run(args, cwd=cwd or EXP, text=True, capture_output=True)
        if check and p.returncode != 0:
            raise RuntimeError("Command failed: " + " ".join(args) +
                               "\nSTDOUT:\n" + p.stdout + "\nSTDERR:\n" + p.stderr)
        return p

    def up(self):
        self.sh("docker", "compose", "down", "-v", check=False)
        self.sh("docker", "compose", "up", "-d", "--build")

    def down(self):
        self.sh("docker", "compose", "down", "-v", check=False)

    def http_get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    def probe(self, cmd):
        out = self.sh("docker", "compose", "exec", "-T", "receiver",
                      "python", "/app/internal_probe.py", cmd).stdout
        return last_json_line(out)

    def admin(self, cmd):
        out = self.sh("docker", "compose", "exec", "-T", "-u", "root", "receiver",
                      "python", "/app/admin.py", cmd).stdout
        return last_json_line(out)

    def send(self):
        out = self.sh("docker", "compose", "exec", "-T", "source",
                      "python", "/app/send.py").stdout
        return last_json_line(out)

    def source_ip(self):
        return self.sh("docker", "compose", "exec", "-T", "source", "python", "-c",
                       "import socket; print(socket.gethostbyname(socket.gethostname()))"
                       ).stdout.strip()

    def snapshot(self, run_dir):
        (run_dir / "docker-compose.resolved.yaml").write_text(
            self.sh("docker", "compose", "config").stdout, encoding="utf-8")
        (run_dir / "docker.images.txt").write_text(
            self.sh("docker", "images", "--digests", "--format",
                    "{{.Repository}}\t{{.Tag}}\t{{.Digest}}\t{{.ID}}").stdout,
            encoding="utf-8")

    def versions(self):
        rows = []
        for cmd in [("docker", "--version"), ("docker", "compose", "version")]:
            p = subprocess.run(cmd, text=True, capture_output=True)
            rows.append((p.stdout or p.stderr).strip())
        return rows


class LocalBackend:
    """Same receiver, run on this host as an unprivileged user. The runner
    must be root so that it can act as the administrator identity."""
    name = "local"

    def __init__(self, user, port, workdir):
        import pwd  # Unix only; local mode is Linux/macOS
        if os.geteuid() != 0:
            raise RuntimeError("local mode must run as root (it acts as the administrator identity)")
        try:
            self.pw = pwd.getpwnam(user)
        except KeyError:
            subprocess.run(["useradd", "--create-home", user], check=True)
            self.pw = pwd.getpwnam(user)
        self.user = user
        self.port = port
        self.base = f"http://127.0.0.1:{port}"
        self.work = Path(workdir)
        self.data = self.work / "data"
        self.run = self.work / "run"
        self.proc = None
        self.env = dict(os.environ, H2_DATA=str(self.data), H2_RUN=str(self.run),
                        H2_PORT=str(port), H2_RECEIVER_URL=self.base + "/push")

    def _baseline_perms(self):
        gid = self.pw.pw_gid
        self.data.mkdir(parents=True, exist_ok=True)
        self.run.mkdir(parents=True, exist_ok=True)
        os.chown(self.data, 0, gid)
        os.chmod(self.data, 0o2775)
        for name in ("state.json", "policy.json"):
            p = self.data / name
            if not p.exists():
                p.write_text("{}", encoding="utf-8")
            os.chown(p, 0, gid)
            os.chmod(p, 0o664)
        os.chown(self.run, self.pw.pw_uid, gid)
        os.chmod(self.run, 0o2775)

    def up(self):
        self.down()
        if self.work.exists():
            shutil.rmtree(self.work)
        self._baseline_perms()
        env_assign = " ".join(f"{k}={v}" for k, v in self.env.items() if k.startswith("H2_"))
        self.proc = subprocess.Popen(
            ["su", self.user, "-s", "/bin/sh", "-c",
             f"exec env {env_assign} {sys.executable} {EXP / 'receiver' / 'receiver.py'}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)

    def down(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None

    def http_get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))

    def _py(self, script, *args, as_user=None):
        cmd = [sys.executable, "-I", str(script), *args]
        if as_user:
            cmd = ["su", as_user, "-s", "/bin/sh", "-c",
                   "exec env " + " ".join(f"{k}={v}" for k, v in self.env.items() if k.startswith("H2_"))
                   + " " + " ".join(f"'{c}'" for c in cmd)]
        p = subprocess.run(cmd, text=True, capture_output=True, env=self.env)
        if p.returncode != 0:
            raise RuntimeError("Command failed: " + " ".join(cmd) + "\n" + p.stdout + p.stderr)
        return last_json_line(p.stdout)

    def probe(self, cmd):
        return self._py(EXP / "receiver" / "internal_probe.py", cmd, as_user=self.user)

    def admin(self, cmd):
        return self._py(EXP / "receiver" / "admin.py", cmd)

    def send(self):
        return self._py(EXP / "source" / "send.py")

    def source_ip(self):
        return "127.0.0.1"

    def snapshot(self, run_dir):
        (run_dir / "local-environment.json").write_text(json.dumps({
            "receiver_user": self.user, "receiver_uid": self.pw.pw_uid,
            "runner_uid": os.geteuid(), "data_dir": str(self.data)}, indent=2),
            encoding="utf-8")

    def versions(self):
        return []


# ------------------------------------------------------------ measurement

def wait_ready(b):
    deadline = time.time() + 60
    last = None
    while time.time() < deadline:
        try:
            if b.http_get("/health").get("ok"):
                return
        except Exception as e:
            last = e
            time.sleep(0.3)
    raise RuntimeError(f"receiver did not become ready: {last!r}")


def ev_has(ev, name, **match):
    return any(e.get("event") == name and all(e.get(k) == v for k, v in match.items())
               for e in ev)


def measure_present(b, ip, src):
    """Independent presence measurements, used in the baseline phase and for
    the two conditions each ablation leaves untouched."""
    x_result = b.probe("X_MARKER")
    access = b.probe("ACCESS_STATE")
    a_result = b.probe("AUTHORITY_PROBE")
    st = b.http_get("/state")
    ev = b.http_get("/events")
    out = {"x_probe": x_result, "access_state": access, "authority_probe": a_result,
           "state": st, "events": ev}
    present = {
        "I": ev_has(ev, "interface_admit", client_ip=ip) and src.get("status") in (200, 202),
        "X": (x_result.get("status") == 200 and x_result.get("marker_seen") is True
              and ev_has(ev, "handler_reached", marker=True)
              and ev_has(ev, "x_marker_reached_handler")
              and st["mem"].get("marker_seen") is True),
        "A": (access.get("state_writable_by_process") is True
              and access.get("data_dir_writable_by_process") is True
              and a_result.get("authority_probe") == "ok"
              and ev_has(ev, "authority_probe_write")
              and st["state"].get("authority_probe") == "ok"),
    }
    return present, out


def baseline_phase(b, ip):
    b.probe("RESET")
    before = b.http_get("/state")["state"].get("test_value")
    src = b.send()
    present, out = measure_present(b, ip, src)
    O = int(before == 0 and out["state"]["state"].get("test_value") == 42)
    observed = [int(present["I"]), int(present["X"]), int(present["A"]), O]
    evidence_ok = all(present.values()) and O == 1 and src.get("status") == 200 \
        and ev_has(out["events"], "handler_reached", client_ip=ip) \
        and ev_has(out["events"], "state_write", client_ip=ip)
    out["source_result"] = src
    return observed, evidence_ok, out


def post_phase(b, ip, ablation, sham=False):
    b.probe("RESET")
    if sham:
        # Control for the harness itself: no ablation is applied and the
        # post-ablation prediction is still tested. The expected outcome is
        # FAIL on the ablated condition. A harness that passed here would
        # be reporting its own predictions rather than the system.
        applied = {"sham": True, "note": "no ablation applied"}
    elif ablation == "I":
        applied = b.probe(f"SET_DENY_IP {ip}")
    elif ablation == "X":
        applied = b.probe("SET_ROUTE off")
    elif ablation == "A":
        applied = b.admin("WITHDRAW_WRITE")
    elif ablation == "P":
        applied = b.probe("SET_INTERDICT 42")
    elif ablation == "N":
        applied = b.probe("SET_LOG_VERBOSITY verbose")

    src = b.send()
    present, out = measure_present(b, ip, src)
    st, ev = out["state"], out["events"]
    access, x_result, a_result = out["access_state"], out["x_probe"], out["authority_probe"]
    out["source_result"] = src
    out["ablation_applied"] = applied

    absent = {"I": False, "X": False, "A": False}
    if ablation == "I":
        absent["I"] = (st["policy"].get("deny_ip") == ip
                       and ev_has(ev, "interface_reject", client_ip=ip)
                       and src.get("status") == 403)
    elif ablation == "X":
        absent["X"] = (st["policy"].get("route_admission_to_worker") is False
                       and ev_has(ev, "interface_admit", client_ip=ip)
                       and ev_has(ev, "route_absent", client_ip=ip)
                       and ev_has(ev, "route_absent", client_ip="internal-x-marker")
                       and x_result.get("status") == 202
                       and x_result.get("routed") is False
                       and st["mem"].get("marker_seen") is False
                       and not ev_has(ev, "handler_reached")
                       and not ev_has(ev, "x_marker_reached_handler"))
    elif ablation == "A":
        absent["A"] = (access.get("state_writable_by_process") is False
                       and access.get("data_dir_writable_by_process") is False
                       and a_result.get("authority_probe") == "denied"
                       and ev_has(ev, "authority_denied", attempt="authority_probe")
                       and ev_has(ev, "authority_denied", attempt="operation_write", client_ip=ip)
                       and ev_has(ev, "handler_reached", client_ip=ip))

    # Each value carries its own warrant. A condition is recorded 0 only on
    # affirmative absence evidence, 1 only on affirmative presence evidence;
    # anything else leaves the evidence incomplete and the run AMBIGUOUS.
    observed, complete = [], True
    for c in ("I", "X", "A"):
        if absent.get(c) and not present[c]:
            observed.append(0)          # affirmative absence evidence
        elif present[c] and not absent.get(c):
            observed.append(1)          # affirmative presence evidence
        else:
            observed.append(None)       # neither, or both: evidence incomplete
            complete = False
    O = int(st["state"].get("test_value") == 42)
    observed.append(O)
    out["presence_evidence"] = present
    out["absence_evidence"] = absent

    if ablation == "P" and not sham:
        # The interdiction itself must be evidenced, and the misclassification
        # of a processing filter as an Authority denial must be contradicted
        # by the Authority probe (which is part of present["A"] above).
        interdicted = (st["policy"].get("interdict_value") == 42
                       and ev_has(ev, "processing_interdicted", client_ip=ip)
                       and ev_has(ev, "handler_reached", client_ip=ip)
                       and src.get("status") == 200
                       and src.get("body", {}).get("interdicted") is True
                       and not ev_has(ev, "state_write", client_ip=ip))
        complete = complete and interdicted
        out["interdiction_evidence"] = interdicted
        out["misclassification_check"] = {
            "reading_filter_as_authority_denial_contradicted_by": "AUTHORITY_PROBE wrote the protected state",
            "authority_present": present["A"]}
    if ablation == "N" and not sham:
        null_applied = (st["policy"].get("log_verbosity") == "verbose"
                        and ev_has(ev, "state_write", client_ip=ip))
        complete = complete and null_applied
        out["null_intervention_evidence"] = null_applied

    # Restore before the next phase. RESET needs write control, so the
    # Authority restore comes first.
    if ablation == "A" and not sham:
        out["restore"] = b.admin("RESTORE_WRITE")
    b.probe("RESET")
    return observed, complete, out


def restoration_phase(b, ip):
    """After restore and RESET the configuration is the baseline again. The
    prediction is (1,1,1,1) with the operation returning, which shows the
    ablated condition was the cause of O = 0 in the post phase."""
    observed, ok, out = baseline_phase(b, ip)
    return observed, ok, out


def classify(baseline, post, expected_post, evidence_ok):
    """PASS only on complete evidence matching the prediction. A value with
    affirmative evidence that contradicts the prediction is FAIL even when
    some other value is incomplete; AMBIGUOUS is reserved for runs in which
    nothing contradicts the prediction but some warrant is missing."""
    contradiction = any(o is not None and o != e for o, e in zip(post, expected_post)) \
        or any(o is not None and o != e for o, e in zip(baseline, BASELINE))
    if contradiction:
        return "FAIL"
    if not evidence_ok:
        return "AMBIGUOUS"
    return "PASS" if (baseline == BASELINE and post == expected_post) else "FAIL"


def save_checksums(run_dir):
    rows = [f"{sha256_file(p)}  {p.relative_to(run_dir).as_posix()}"
            for p in sorted(run_dir.rglob("*")) if p.is_file() and p.name != "checksums.sha256"]
    (run_dir / "checksums.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def one_run(b, ablation, run_number, results_root, sham=False):
    spec = ABLATIONS[ablation]
    manifest = ROOT / "manifests" / spec["manifest"]
    sub = f"{b.name}-sham" if sham else b.name
    run_dir = results_root / f"H2-{ablation}" / sub / f"run-{run_number:02d}"
    if run_dir.exists():
        raise RuntimeError(f"{run_dir} exists; results are append-only")
    run_dir.mkdir(parents=True)

    b.up()
    wait_ready(b)
    shutil.copy2(manifest, run_dir / "manifest.snapshot.yaml")
    b.snapshot(run_dir)
    versions = [f"Host platform: {platform.platform()}",
                f"Runner interpreter: {sys.executable} {platform.python_version()}"] + b.versions()
    (run_dir / "versions.txt").write_text("\n".join(versions), encoding="utf-8")
    ip = b.source_ip()

    baseline, base_ok, base_ev = baseline_phase(b, ip)
    write_json(run_dir / "baseline.events.json", base_ev["events"])
    write_json(run_dir / "baseline.state.json", base_ev["state"])
    write_json(run_dir / "baseline.access_state.json", base_ev["access_state"])

    post, post_ok, post_ev = post_phase(b, ip, ablation, sham=sham)
    write_json(run_dir / "post.events.json", post_ev["events"])
    write_json(run_dir / "post.state.json", post_ev["state"])
    write_json(run_dir / "post.access_state.json", post_ev["access_state"])

    restored, rest_ok, rest_ev = restoration_phase(b, ip)
    write_json(run_dir / "restored.events.json", rest_ev["events"])
    write_json(run_dir / "restored.state.json", rest_ev["state"])

    outcome = classify(baseline, post, spec["post"], base_ok and post_ok)
    restoration_outcome = "PASS" if (restored == RESTORED and rest_ok) else \
        ("FAIL" if any(o is not None and o != e for o, e in zip(restored, RESTORED)) else "AMBIGUOUS")
    record = {
        "test": f"H2-{ablation}",
        "mode": b.name,
        "sham_control": sham,
        "expected_outcome": "FAIL or AMBIGUOUS (sham control)" if sham else "PASS",
        "reported_batch_eligible": b.name == "docker" and not sham,
        "harness_version": HARNESS_VERSION,
        "parent_harness": "H4 Ablation Harness, https://doi.org/10.5281/zenodo.22711457",
        "source_sha256": {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in SOURCE_FILES},
        "run": run_number,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_ip": ip,
        "baseline_prediction": BASELINE,
        "baseline_observed": baseline,
        "baseline_evidence_complete": base_ok,
        "kind": spec["kind"],
        "post_prediction": spec["post"],
        "post_observed": post,
        "post_evidence_complete": post_ok,
        "outcome": outcome,
        "restored_prediction": RESTORED,
        "restored_observed": restored,
        "restored_evidence_complete": rest_ok,
        "restoration_outcome": restoration_outcome,
        "interdiction_evidence": post_ev.get("interdiction_evidence"),
        "misclassification_check": post_ev.get("misclassification_check"),
        "null_intervention_evidence": post_ev.get("null_intervention_evidence"),
        "baseline_evidence_summary": {"source_result": base_ev["source_result"],
                                      "x_probe": base_ev["x_probe"],
                                      "authority_probe": base_ev["authority_probe"]},
        "post_evidence_summary": {"ablation_applied": post_ev["ablation_applied"],
                                  "source_result": post_ev["source_result"],
                                  "x_probe": post_ev["x_probe"],
                                  "authority_probe": post_ev["authority_probe"],
                                  "access_state": post_ev["access_state"],
                                  "restore": post_ev.get("restore")},
    }
    write_json(run_dir / "record.json", record)
    save_checksums(run_dir)
    print(f"H2-{ablation} [{sub}] run {run_number}: baseline={tuple(baseline)} "
          f"post={tuple(post)} expected={tuple(spec['post'])} => {outcome}; "
          f"restored={tuple(restored)} => {restoration_outcome}")
    return record


def next_run_number(results_root, ablation, mode, sham=False):
    d = results_root / f"H2-{ablation}" / (f"{mode}-sham" if sham else mode)
    nums = []
    if d.exists():
        for p in d.glob("run-*"):
            try:
                nums.append(int(p.name.split("-")[1]))
            except Exception:
                pass
    return (max(nums) + 1) if nums else 1


def dry_run(mode):
    print("Dry run only: nothing is executed.\n")
    for p in SOURCE_FILES:
        print(f"SHA256 {p.relative_to(ROOT).as_posix()}: {sha256_file(p)}")
    if mode == "docker":
        p = subprocess.run(["docker", "compose", "config"], cwd=EXP, text=True, capture_output=True)
        print("\nDocker Compose configuration validates." if p.returncode == 0
              else "\nDocker Compose configuration FAILED:\n" + p.stderr)
    print("\nHarness is ready. Freeze and deposit the manifests before confirmatory execution.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--execute", action="store_true")
    ap.add_argument("--mode", choices=["docker", "local"], default="docker")
    ap.add_argument("--ablation", choices=["I", "X", "A", "P", "N", "all"], default="all")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--yes", action="store_true", help="skip the EXECUTE confirmation")
    ap.add_argument("--sham", action="store_true",
                    help="harness control: apply no ablation and test the post prediction anyway (expected FAIL)")
    ap.add_argument("--local-user", default="h2")
    ap.add_argument("--local-port", type=int, default=18083)
    ap.add_argument("--local-workdir", default=str(ROOT / ".local-env"))
    ap.add_argument("--results", default=str(ROOT / "results"))
    args = ap.parse_args()

    if args.dry_run:
        dry_run(args.mode)
        return

    ablations = ["I", "X", "A", "P", "N"] if args.ablation == "all" else [args.ablation]
    print(f"Mode: {args.mode}   Ablations: {ablations}   Runs each: {args.runs}"
          + ("   SHAM CONTROL (no ablation applied; expected FAIL)" if args.sham else ""))
    if args.mode == "local":
        print("Local mode results are development checks and are not the reported batch.")
    if not args.yes:
        if input("Type EXECUTE to continue: ") != "EXECUTE":
            print("Cancelled.")
            return

    if args.sham:
        ablations = [a for a in ablations if ABLATIONS[a]["kind"] == "denial"]
        # A sham of H2-N would trivially pass (prediction equals the untouched
        # system) and a sham of H2-P tests nothing beyond H2-N, so shams are
        # run for the three denials only.
    b = DockerBackend() if args.mode == "docker" else \
        LocalBackend(args.local_user, args.local_port, args.local_workdir)
    results_root = Path(args.results)
    records = []
    try:
        for abl in ablations:
            start = next_run_number(results_root, abl, b.name, args.sham)
            for n in range(start, start + args.runs):
                records.append(one_run(b, abl, n, results_root, sham=args.sham))
    finally:
        b.down()

    print("\nSummary")
    for abl in ablations:
        counts = {}
        for r in records:
            if r["test"] == f"H2-{abl}":
                counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
        print(f"  H2-{abl}: " + ", ".join(f"{k} {counts.get(k, 0)}" for k in ("PASS", "FAIL", "AMBIGUOUS")))
    print(f"Evidence: {results_root}")


if __name__ == "__main__":
    main()
