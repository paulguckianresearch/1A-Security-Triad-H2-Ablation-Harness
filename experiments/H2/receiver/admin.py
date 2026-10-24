"""Administrator identity for the Authority ablation.

Runs as root, the owner of the data directory and of the protected state
file. The receiver runs as the unprivileged user `h2`, whose write control
over the protected state comes solely from group write permission on the
directory and on the file. WITHDRAW_WRITE removes that group permission;
RESTORE_WRITE puts it back. Nothing is created, split, duplicated or
replaced: the same files, the same owner, the same group, the same receiver
identity. Only the access-control state changes.

The event log is owned by the receiver identity itself so that logging,
including the denial record, continues to work with the directory read-only.
"""
import json
import os
import sys

DATA = os.environ.get("H2_DATA", "/data")
STATE = os.path.join(DATA, "state.json")
POLICY = os.path.join(DATA, "policy.json")

BASELINE_DIR = 0o2775   # rwxrwsr-x : setgid so new files inherit the group
BASELINE_FILE = 0o664   # rw-rw-r--
WITHHELD_DIR = 0o2755   # rwxr-sr-x : group may not write
WITHHELD_FILE = 0o644   # rw-r--r--


def modes():
    return {
        "data_dir_mode": oct(os.stat(DATA).st_mode & 0o7777),
        "state_mode": oct(os.stat(STATE).st_mode & 0o7777),
        "policy_mode": oct(os.stat(POLICY).st_mode & 0o7777),
        "data_dir_owner_uid": os.stat(DATA).st_uid,
        "state_owner_uid": os.stat(STATE).st_uid,
    }


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("WITHDRAW_WRITE", "RESTORE_WRITE", "MODES"):
        raise SystemExit("usage: admin.py WITHDRAW_WRITE|RESTORE_WRITE|MODES")
    cmd = sys.argv[1]
    if cmd == "WITHDRAW_WRITE":
        os.chmod(STATE, WITHHELD_FILE)
        os.chmod(POLICY, WITHHELD_FILE)
        os.chmod(DATA, WITHHELD_DIR)
    elif cmd == "RESTORE_WRITE":
        os.chmod(DATA, BASELINE_DIR)
        os.chmod(STATE, BASELINE_FILE)
        os.chmod(POLICY, BASELINE_FILE)
    print(json.dumps({"command": cmd, "admin_uid": os.getuid(), **modes()}))


if __name__ == "__main__":
    main()
