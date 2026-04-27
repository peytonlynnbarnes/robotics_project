#!/bin/sh
set -euxo pipefail

# Chown build/install/log volumes once using sentinel files so the ubuntu
# user (UID 1000) inside the ros2 container can write to them. Sentinel
# avoids re-chowning on every compose up, which is slow on large workspaces.
for d in \
  /ros2_build \
  /ros2_install \
  /ros2_log \
; do
  echo "[bootstrap] Ensuring directory exists: $d"
  mkdir -p "$d"
  if [ -f "$d/.owner_set" ]; then
    echo "[bootstrap] Ownership already set for $d; skipping"
  else
    echo "[bootstrap] Chowning recursively to 1000:1000: $d"
    chown -R 1000:1000 "$d"
    echo "owner=1000:1000" > "$d/.owner_set"
  fi
done

echo "[bootstrap] Completed successfully"
