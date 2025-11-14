#!/usr/bin/env bash

set -euo pipefail

ENV_CONFIG=$1
JOB_SHORT_NAME=$2
PR_NUMBER=${3:-}

if [ -z "$PR_NUMBER" ]; then
    # On permanent environments, the environment name is the environment config name, i.e. "production"
    ENV=${ENV_CONFIG}
else
    # On a review app, the environment name uses the PR number, i.e. "pr-1234"
    ENV=pr-${PR_NUMBER}
fi

JOB_NAME=manbrs-${JOB_SHORT_NAME}-${ENV}
RG_NAME=rg-manbrs-${ENV}-container-app-uks
TIMEOUT=300
WAIT=5
count=0

get_job_status() {
    az containerapp job execution show --job-execution-name "$execution_name" -n "$JOB_NAME" -g "$RG_NAME" | jq -r '.properties.status'
}

echo Starting job "$JOB_NAME"...
execution_name=$(az containerapp job start --name "$JOB_NAME" --resource-group "$RG_NAME" | jq -r '.id|split("/")[-1]')

while [[ $(get_job_status) = "Running" ]]; do
    echo The job "$execution_name" is still running...
    ((count*WAIT > TIMEOUT)) && break
    ((count+=1))
    sleep $WAIT
done

if ((count*WAIT > TIMEOUT)); then
    echo "The job \"$execution_name\" timed out (${TIMEOUT}s)"
    exit 1
fi

status=$(get_job_status)
if [[ $status = "Succeeded" ]]; then
    echo The job "$execution_name" completed successfully
else
    echo The job "$execution_name" has not completed successfully. Status: "$status"
    exit 2
fi
