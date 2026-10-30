#!/usr/bin/env bash
set -euo pipefail

CONTEXT="kind-student-portal-recovery"
NODE="student-portal-recovery-control-plane"
LOG="/tmp/student-portal-forward.log"

# Prevent two startup tasks from running at the same time.
exec 9>/tmp/student-portal-start.lock
if ! flock -n 9; then
    echo "Another portal startup is already running."
    exit 0
fi

portal_ready() {
    curl --fail --silent --max-time 3 \
        http://127.0.0.1:5002/health >/dev/null
}

echo "Waiting for Docker..."
for attempt in {1..60}; do
    if docker info >/dev/null 2>&1; then
        break
    fi
    sleep 2
done
docker info >/dev/null

echo "Starting the existing Kubernetes cluster..."
docker start "$NODE" >/dev/null

echo "Waiting for Kubernetes..."
for attempt in {1..60}; do
    if kubectl --context "$CONTEXT" --request-timeout=5s \
        get nodes >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

kubectl --context "$CONTEXT" wait \
    --for=condition=Ready nodes --all --timeout=180s

if portal_ready; then
    echo "The portal is already available on port 5002."
    exit 0
fi

for attempt in {1..12}; do
    echo "Connecting to the portal: attempt $attempt of 12..."

    if ! kubectl --context "$CONTEXT" -n student-portal \
        rollout status deployment/student-portal --timeout=30s; then
        sleep 5
        continue
    fi

    # Each attempt selects a pod again.
    nohup kubectl --context "$CONTEXT" -n student-portal \
        port-forward deployment/student-portal 5002:5000 \
        >"$LOG" 2>&1 </dev/null 9>&- &
    FORWARD_PID=$!

    for check in {1..10}; do
        if portal_ready; then
            echo "The portal is ready. Open port 5002 in the Ports tab."
            exit 0
        fi

        if ! kill -0 "$FORWARD_PID" 2>/dev/null; then
            break
        fi
        sleep 2
    done

    # Stop only the forwarding process from this attempt.
    kill "$FORWARD_PID" 2>/dev/null || true
    wait "$FORWARD_PID" 2>/dev/null || true

    echo "Connection not ready yet; retrying in 5 seconds..."
    sleep 5
done

echo "Could not connect to the portal. Latest details:"
cat "$LOG" 2>/dev/null || true
kubectl --context "$CONTEXT" -n student-portal get pods
exit 1