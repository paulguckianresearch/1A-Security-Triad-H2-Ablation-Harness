"""Source S: supplies the operation's payload to the receiver's /push."""
import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get("H2_RECEIVER_URL", "http://receiver:8080/push")

req = urllib.request.Request(
    URL,
    data=json.dumps({"test_value": 42}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)
try:
    with urllib.request.urlopen(req, timeout=5) as r:
        body = json.loads(r.read().decode("utf-8"))
        print(json.dumps({"status": r.status, "body": body}))
except urllib.error.HTTPError as e:
    body = json.loads(e.read().decode("utf-8"))
    print(json.dumps({"status": e.code, "body": body}))
    sys.exit(0)
