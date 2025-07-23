ENV_CONFIG=dev
REGION="UK South"
APP_SHORT_NAME=andppl
HUB_SUBSCRIPTION="Digital Screening DToS - DevOps"
STORAGE_ACCOUNT_RG=rg-dtos-state-files
STORAGE_ACCOUNT_NAME=sa${APP_SHORT_NAME}${ENV_CONFIG}tfstate
HUB_SUBSCRIPTION_ID=$(az account show --query id --output tsv --name "${HUB_SUBSCRIPTION}")

az deployment sub create --location "${REGION}" --template-file infrastructure/terraform/resource_group_init/main.bicep \
    --subscription ${HUB_SUBSCRIPTION_ID} \
    --parameters enableSoftDelete=${ENABLE_SOFT_DELETE} envConfig=${ENV_CONFIG} region="${REGION}" \
      storageAccountRGName=${STORAGE_ACCOUNT_RG}  storageAccountName=${STORAGE_ACCOUNT_NAME} \
    --confirm-with-what-if