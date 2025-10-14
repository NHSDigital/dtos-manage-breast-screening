#!/usr/bin/env bash

set -euo pipefail

ENV_CONFIG=$1
EXPECTED_SHA=$2
PR_NUMBER=${3:-}

if [ "$ENV_CONFIG" = "preprod" ] || [ "$ENV_CONFIG" = "prod" ]; then
    # Permanent environments
    ENDPOINT="https://${ENV_CONFIG}.manage-breast-screening.screening.nhs.uk/sha"
elif [ "$ENV_CONFIG" = "dev" ]; then
    # Non-live permanent environment
    ENDPOINT="https://${ENV_CONFIG}.manage-breast-screening.non-live.screening.nhs.uk/sha"
else
    # On a review app, the environment name uses the PR number, i.e. "pr-1234"
    ENDPOINT="https://pr-${PR_NUMBER}.manage-breast-screening.non-live.screening.nhs.uk/sha"
fi

TIMEOUT=300
INTERVAL=5

start_time=$(date +%s)

while true; do
  if ACTUAL_SHA=$(curl -fsSL "$ENDPOINT" 2>/dev/null); then
      echo "Endpoint responded: $ACTUAL_SHA"
      if [ "$ACTUAL_SHA" = "$EXPECTED_SHA" ]; then
        echo "✅ SHA matches expected commit: $EXPECTED_SHA"
        exit 0
      else
        echo "❌ SHA mismatch. Expected $EXPECTED_SHA but got $ACTUAL_SHA"
        exit 1
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
