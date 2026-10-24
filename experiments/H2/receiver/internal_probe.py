"""Instrumentation client for the receiver's internal Unix socket.

Runs inside the receiver's environment under an identity permitted to use
the socket. It never touches the protected state itself; every probe is
performed by the receiver process so that the evidence concerns the acting
mechanism's own identity.
"""
import os
import socket
import sys

RUN = os.environ.get("H2_RUN", "/run/h2")
SOCK = os.path.join(RUN, "internal.sock")

if len(sys.argv) != 2:
    raise SystemExit(
        "usage: internal_probe.py "
        "X_MARKER|AUTHORITY_PROBE|ACCESS_STATE|MEM|RESET|"
        "'SET_DENY_IP <ip>'|'SET_ROUTE on|off'|'SET_INTERDICT <value>|off'|"
        "'SET_LOG_VERBOSITY <level>'"
    )

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect(SOCK)
s.sendall((sys.argv[1] + "\n").encode("utf-8"))
s.shutdown(socket.SHUT_WR)
raw = b""
while True:
    part = s.recv(4096)
    if not part:
        break
    raw += part
print(raw.decode("utf-8").strip())
