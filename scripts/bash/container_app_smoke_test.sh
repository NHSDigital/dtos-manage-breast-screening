#!/usr/bin/env bash

set -euo pipefail

ENV_CONFIG=$1
EXPECTED_SHA=$2
DNS_ZONE_NAME=$3
PR_NUMBER=${4:-}
USE_APEX_DOMAIN=${5:-false}

if [ -z "$PR_NUMBER" ]; then
    # Permanent environments
    if [ "$USE_APEX_DOMAIN" = "true" ]; then
        # For production with apex domain
        ENDPOINT="https://${DNS_ZONE_NAME}/sha"
    else
        # For other environments (dev, test, etc.)
        ENDPOINT="https://${ENV_CONFIG}.${DNS_ZONE_NAME}/sha"
    fi
else
    # On a review app, the environment name uses the PR number, i.e. "pr-1234"
    ENDPOINT="https://pr-${PR_NUMBER}.${DNS_ZONE_NAME}/sha"
fi

# Script timeout and check interval in seconds
TIMEOUT=$((15*60))
INTERVAL=5

start_time=$(date +%s)

while true; do
  # Send request to /sha URL. Only print the sha and fail if required.
  # It should fail initially until front door presents the right certificate.
  if ACTUAL_SHA=$(curl -fsS "$ENDPOINT" 2>/dev/null); then
    echo "Endpoint responded: $ACTUAL_SHA"
    if [ "$ACTUAL_SHA" = "$EXPECTED_SHA" ]; then
      echo "✅ SHA matches expected commit: $EXPECTED_SHA"
      exit 0
    else
      echo "❌ SHA mismatch. Expected $EXPECTED_SHA but got $ACTUAL_SHA"
    fi
  fi

  now=$(date +%s)
  elapsed=$((now - start_time))
  if [ $elapsed -ge $TIMEOUT ]; then
    echo "❌ Timeout: Endpoint did not become ready within ${TIMEOUT}s"
    exit 1
  fi

  echo "Still waiting... ($elapsed/${TIMEOUT}s elapsed)"
  sleep $INTERVAL
done
