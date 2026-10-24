#!/bin/sh
# Runs as root: establishes the baseline access-control state, then drops to
# the unprivileged receiver identity. The receiver's write control over the
# protected state is group write permission and nothing else.
set -e
mkdir -p /data /run/h2
chown root:h2 /data
chmod 2775 /data
for f in /data/state.json /data/policy.json; do
  [ -f "$f" ] || echo '{}' > "$f"
  chown root:h2 "$f"
  chmod 664 "$f"
done
chown h2:h2 /run/h2
chmod 2775 /run/h2
exec su h2 -s /bin/sh -c 'exec python /app/receiver.py'
