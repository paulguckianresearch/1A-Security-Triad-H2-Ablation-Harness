"""Receiver R: the single analysed mechanism for the Paper 1A H2 ablation.

Derived from experiment I-1 of the H4 Ablation Harness
(https://doi.org/10.5281/zenodo.22711457). The admission relation, the
post-admission route, the worker and the protected state are the same as
I-1. Three things are added so that all three structural conditions can be
removed on this one mechanism, each by an ordinary control:

  Interface         deny the tested source at the /push admission relation
                    (unchanged from I-1: SET_DENY_IP)
  Execution Pathway disable the standing route from the receiving side of
                    /push to the worker (SET_ROUTE off), which is the
                    structural form of patching or disabling functionality
  Authority         withdraw the receiver identity's write control over the
                    protected state (file-system permissions changed by an
                    administrator identity, see admin.py)

The X marker no longer writes to the protected state (it records in memory),
so observing the route does not depend on Authority. That is what lets the
route be verified present while write control is withheld.
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
import queue
import socket
import threading
import time

DATA = os.environ.get("H2_DATA", "/data")
RUN = os.environ.get("H2_RUN", "/run/h2")
PORT = int(os.environ.get("H2_PORT", "8080"))
STATE = os.path.join(DATA, "state.json")
POLICY = os.path.join(DATA, "policy.json")
EVENTS = os.path.join(DATA, "events.jsonl")
SOCK = os.path.join(RUN, "internal.sock")

workq = queue.Queue()
io_lock = threading.Lock()

# In-memory observations that must not depend on write control over DATA.
mem = {"marker_seen": False, "marker_count": 0}


def save_json(path, obj):
    # Written in place rather than through a temporary file and rename, so
    # that the file keeps its owner (the administrator identity) and the
    # receiver's write control over it remains exactly the group permission
    # that admin.py grants and withdraws.
    with io_lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)


def load_json(path, default):
    with io_lock:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return default


def log(event, **kw):
    rec = {"ts": time.time(), "event": event, **kw}
    with io_lock:
        with open(EVENTS, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")


def reset():
    """Restore the baseline configuration. Requires write control over DATA,
    so it is only called while Authority is present (before an ablation and
    after RESTORE_WRITE)."""
    save_json(STATE, {"test_value": 0, "authority_probe": None})
    save_json(POLICY, {"deny_ip": None, "route_admission_to_worker": True,
                       "interdict_value": None, "log_verbosity": "normal"})
    with io_lock:
        with open(EVENTS, "w", encoding="utf-8") as f:
            f.write("")
    mem["marker_seen"] = False
    mem["marker_count"] = 0
    log("reset")


def worker():
    while True:
        item = workq.get()
        try:
            kind = item["kind"]
            if kind == "operation":
                log("handler_reached",
                    client_ip=item["client_ip"],
                    value=item["value"],
                    marker=item.get("marker", False))
                if item.get("marker"):
                    # The X marker has traversed every step after the
                    # admission decision (payload parsing, route dispatch,
                    # queue, worker dispatch, handler entry) and branches off
                    # here, before the state write, so that it changes
                    # neither O nor the protected state.
                    log("x_marker_reached_handler")
                    mem["marker_seen"] = True
                    mem["marker_count"] += 1
                    item["result"]["marker_seen"] = True
                    continue
                # Processing interdiction (H2-P): a content rule inside the
                # worker refuses the write while admission, route and the
                # worker's control over the state are all unchanged. This is
                # the "interdict with Sigma present" row of the paper's
                # intervention table, not a structural denial.
                pol = load_json(POLICY, {})
                if pol.get("interdict_value") is not None and \
                        item["value"] == pol.get("interdict_value"):
                    log("processing_interdicted",
                        client_ip=item["client_ip"], value=item["value"])
                    item["result"]["written"] = None
                    item["result"]["interdicted"] = True
                    continue
                try:
                    st = load_json(STATE, {})
                    st["test_value"] = item["value"]
                    save_json(STATE, st)
                    log("state_write",
                        client_ip=item["client_ip"],
                        value=item["value"])
                    item["result"]["written"] = item["value"]
                except PermissionError as e:
                    log("authority_denied",
                        client_ip=item["client_ip"],
                        attempt="operation_write",
                        error=repr(e))
                    item["result"]["written"] = None
                    item["result"]["denied"] = True

            elif kind == "authority_probe":
                # Same receiver process and execution identity attempts a
                # benign write to the same protected state the operation
                # changes. Success is the second leg of Authority present;
                # a PermissionError is the denial record for Authority absent.
                try:
                    st = load_json(STATE, {})
                    st["authority_probe"] = "ok"
                    save_json(STATE, st)
                    log("authority_probe_write")
                    item["result"]["authority_probe"] = "ok"
                except PermissionError as e:
                    log("authority_denied",
                        attempt="authority_probe",
                        error=repr(e))
                    item["result"]["authority_probe"] = "denied"
                    item["result"]["error"] = repr(e)
        except Exception as e:
            item["result"]["error"] = repr(e)
        finally:
            item["done"].set()
            workq.task_done()


def submit(item, timeout=5):
    item["done"] = threading.Event()
    item["result"] = {}
    workq.put(item)
    if not item["done"].wait(timeout):
        raise TimeoutError("worker did not complete item")
    return item["result"]


def process_admitted(raw, client_ip, marker=False):
    """Post-admission path of the nominated Interface.

    Everything after the admission decision at /push runs here, for admitted
    work and for the X marker alike: payload parsing, the standing route
    from the receiving side of /push to the worker, and handling by the
    worker. Returns (http_status, body).
    """
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
        value = int(payload["test_value"])
    except Exception:
        return 400, {"error": "bad payload"}

    policy = load_json(POLICY, {})
    if not policy.get("route_admission_to_worker", True):
        # The route is absent: the input was admitted and parsed, and there
        # is no standing route from here to the acting mechanism.
        log("route_absent", client_ip=client_ip, marker=marker)
        return 202, {"admitted": True, "routed": False,
                     "marker_seen": False if marker else None}

    log("route_dispatch", client_ip=client_ip, marker=marker)
    result = submit({
        "kind": "operation",
        "client_ip": client_ip,
        "value": value,
        "marker": marker
    })
    if "error" in result and "written" not in result and not marker:
        return 500, result
    result["routed"] = True
    return 200, result


def access_state():
    """Access-control state for the acting mechanism, read inside the
    receiver process under its own execution identity."""
    stt = os.stat(STATE)
    dst = os.stat(DATA)
    return {
        "process_uid": os.getuid(),
        "process_gid": os.getgid(),
        "process_groups": sorted(os.getgroups()),
        "state_path": STATE,
        "state_owner_uid": stt.st_uid,
        "state_owner_gid": stt.st_gid,
        "state_mode": oct(stt.st_mode & 0o7777),
        "data_dir_owner_uid": dst.st_uid,
        "data_dir_owner_gid": dst.st_gid,
        "data_dir_mode": oct(dst.st_mode & 0o7777),
        "state_writable_by_process": os.access(STATE, os.W_OK),
        "data_dir_writable_by_process": os.access(DATA, os.W_OK),
    }


def internal_server():
    try:
        os.remove(SOCK)
    except FileNotFoundError:
        pass
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(SOCK)
    os.chmod(SOCK, 0o660)
    srv.listen(5)

    while True:
        conn, _ = srv.accept()
        with conn:
            raw = b""
            while True:
                part = conn.recv(4096)
                if not part:
                    break
                raw += part
                if b"\n" in raw:
                    break
            cmd = raw.decode("utf-8").strip()
            try:
                if cmd == "X_MARKER":
                    code, body = process_admitted(
                        json.dumps({"test_value": 0}).encode("utf-8"),
                        client_ip="internal-x-marker",
                        marker=True
                    )
                    result = {"status": code, **body}
                elif cmd == "ACCESS_STATE":
                    result = access_state()
                elif cmd == "AUTHORITY_PROBE":
                    result = submit({"kind": "authority_probe"})
                elif cmd == "MEM":
                    result = dict(mem)
                elif cmd.startswith("SET_DENY_IP "):
                    ip = cmd.split(" ", 1)[1].strip()
                    pol = load_json(POLICY, {})
                    pol["deny_ip"] = ip
                    save_json(POLICY, pol)
                    log("policy_changed", deny_ip=ip)
                    result = {"deny_ip": ip}
                elif cmd.startswith("SET_ROUTE "):
                    val = cmd.split(" ", 1)[1].strip().lower() == "on"
                    pol = load_json(POLICY, {})
                    pol["route_admission_to_worker"] = val
                    save_json(POLICY, pol)
                    log("policy_changed", route_admission_to_worker=val)
                    result = {"route_admission_to_worker": val}
                elif cmd.startswith("SET_INTERDICT "):
                    raw_v = cmd.split(" ", 1)[1].strip()
                    val = None if raw_v.lower() == "off" else int(raw_v)
                    pol = load_json(POLICY, {})
                    pol["interdict_value"] = val
                    save_json(POLICY, pol)
                    log("policy_changed", interdict_value=val)
                    result = {"interdict_value": val}
                elif cmd.startswith("SET_LOG_VERBOSITY "):
                    val = cmd.split(" ", 1)[1].strip()
                    pol = load_json(POLICY, {})
                    pol["log_verbosity"] = val
                    save_json(POLICY, pol)
                    log("policy_changed", log_verbosity=val)
                    result = {"log_verbosity": val}
                elif cmd == "RESET":
                    reset()
                    result = {"ok": True}
                else:
                    result = {"error": "unknown command"}
            except Exception as e:
                result = {"error": repr(e)}
            conn.sendall((json.dumps(result) + "\n").encode("utf-8"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/state":
            self._json(200, {
                "state": load_json(STATE, {}),
                "policy": load_json(POLICY, {}),
                "mem": dict(mem)
            })
            return
        if self.path == "/events":
            with io_lock:
                try:
                    with open(EVENTS, "r", encoding="utf-8") as f:
                        rows = [json.loads(x) for x in f if x.strip()]
                except FileNotFoundError:
                    rows = []
            self._json(200, rows)
            return
        if self.path == "/health":
            self._json(200, {"ok": True})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/push":
            self._json(404, {"error": "not found"})
            return
        n = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(n) if n else b""
        client_ip = self.client_address[0]

        # The nominated Interface: the admission relation at /push.
        policy = load_json(POLICY, {"deny_ip": None})
        if policy.get("deny_ip") == client_ip:
            log("interface_reject", client_ip=client_ip)
            self._json(403, {"admitted": False, "client_ip": client_ip})
            return
        log("interface_admit", client_ip=client_ip)

        code, result = process_admitted(raw, client_ip)
        if code not in (200, 202):
            self._json(code, result)
            return
        self._json(code, {
            "admitted": True,
            "routed": result.get("routed"),
            "written": result.get("written"),
            "denied": result.get("denied", False),
            "interdicted": result.get("interdicted", False),
            "client_ip": client_ip
        })


if __name__ == "__main__":
    os.makedirs(RUN, exist_ok=True)
    if not os.path.exists(STATE):
        reset()
    threading.Thread(target=worker, daemon=True).start()
    threading.Thread(target=internal_server, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
