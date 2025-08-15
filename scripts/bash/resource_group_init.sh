#!/usr/bin/env bash
set -eu

REGION="$1"
HUB_SUBSCRIPTION_ID="$2"
ENABLE_SOFT_DELETE="$3"
ENV_CONFIG="$4"
STORAGE_ACCOUNT_RG="$5"
STORAGE_ACCOUNT_NAME="$6"
APP_SHORT_NAME="$7"
ARM_SUBSCRIPTION_ID="$8"

echo "Deploy to hub subscription $HUB_SUBSCRIPTION_ID..."
az deployment sub create --location "$REGION" --template-file infrastructure/terraform/resource_group_init/main.bicep \
  --subscription "$HUB_SUBSCRIPTION_ID" \
  --parameters enableSoftDelete="$ENABLE_SOFT_DELETE" envConfig="$ENV_CONFIG" region="$REGION" \
    storageAccountRGName="$STORAGE_ACCOUNT_RG" storageAccountName="$STORAGE_ACCOUNT_NAME" appShortName="$APP_SHORT_NAME" --what-if

read -r -p "Are you sure you want to execute the deployment? (y/n): " confirm
[[ "$confirm" != "y" ]] && exit 0

output=$(az deployment sub create --location "$REGION" --template-file infrastructure/terraform/resource_group_init/main.bicep \
  --subscription "$HUB_SUBSCRIPTION_ID" \
  --parameters enableSoftDelete="$ENABLE_SOFT_DELETE" envConfig="$ENV_CONFIG" region="$REGION" \
    storageAccountRGName="$STORAGE_ACCOUNT_RG" storageAccountName="$STORAGE_ACCOUNT_NAME" appShortName="$APP_SHORT_NAME")

echo "$output"

echo Capture the outputs...
miName=$(echo "$output" | jq -r '.properties.outputs.miName.value')
miPrincipalID=$(echo "$output" | jq -r '.properties.outputs.miPrincipalID.value')

echo "Deploy to core subscription $ARM_SUBSCRIPTION_ID..."
az deployment sub create --location "$REGION" --template-file infrastructure/terraform/resource_group_init/core.bicep \
  --subscription "$ARM_SUBSCRIPTION_ID" \
  --parameters miName="$miName" miPrincipalId="$miPrincipalID" --confirm-with-what-if
