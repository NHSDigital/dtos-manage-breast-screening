DOCKER_IMAGE=ghcr.io/nhsdigital/dtos-manage-breast-screening
REGION=UK South
APP_SHORT_NAME=manbrs
STORAGE_ACCOUNT_RG=rg-dtos-state-files

ahl: # Target the dev environment - make dev <action>
	$(eval include infrastructure/environments/ahl/variables.sh)

dev: # Target the dev environment - make dev <action>
	$(eval include infrastructure/environments/dev/variables.sh)

ci: # Skip manual approvals when running in CI - make ci <env> <action>
	$(eval AUTO_APPROVE=-auto-approve)
	$(eval SKIP_AZURE_LOGIN=true)

set-azure-account: # Set the Azure account for the environment - make <env> set-azure-account
	[ "${SKIP_AZURE_LOGIN}" != "true" ] && az account set -s ${AZURE_SUBSCRIPTION} || true

resource-group-init: set-azure-account get-subscription-ids # Initialise the resource group - make <env> resource-group-init
	$(eval STORAGE_ACCOUNT_NAME=sa${APP_SHORT_NAME}${ENV_CONFIG}tfstate)



	$(eval output='$(shell az deployment sub create --location "${REGION}" --template-file infrastructure/terraform/resource_group_init/main.bicep \
		--subscription ${HUB_SUBSCRIPTION_ID} \
		--parameters enableSoftDelete=${ENABLE_SOFT_DELETE} envConfig=${ENV_CONFIG} region="${REGION}" \
			storageAccountRGName=${STORAGE_ACCOUNT_RG}  storageAccountName=${STORAGE_ACCOUNT_NAME} appShortName=${APP_SHORT_NAME})')

	$(eval miName=$(shell echo ${output}| jq -r '.properties.outputs.miName.value'))
	$(eval miPrincipalID=$(shell echo ${output}| jq -r '.properties.outputs.miPrincipalID.value'))

	az deployment sub create --location "${REGION}" --template-file infrastructure/terraform/resource_group_init/core.bicep \
		--subscription ${ARM_SUBSCRIPTION_ID} \
		--parameters  miName=${miName} miPrincipalId=${miPrincipalID} --confirm-with-what-if

get-subscription-ids: # Retrieve the hub subscription ID based on the subscription name in ${HUB_SUBSCRIPTION} - make <env> get-subscription-ids
	$(eval HUB_SUBSCRIPTION_ID=$(shell az account show --query id --output tsv --name ${HUB_SUBSCRIPTION}))
	$(if ${ARM_SUBSCRIPTION_ID},,$(eval export ARM_SUBSCRIPTION_ID=$(shell az account show --query id --output tsv)))

terraform-init-no-backend: # Initialise terraform modules only and update terraform lock file - make terraform-init-no-backend
	rm -rf infrastructure/modules/dtos-devops-templates
	git -c advice.detachedHead=false clone --depth=1 --single-branch --branch main \
		https://github.com/NHSDigital/dtos-devops-templates.git infrastructure/modules/dtos-devops-templates
	terraform -chdir=infrastructure/terraform init -upgrade -backend=false

terraform-init: set-azure-account get-subscription-ids # Initialise Terraform - make <env> terraform-init
	$(eval STORAGE_ACCOUNT_NAME=samanbrs${ENV_CONFIG}tfstate)
	$(eval export ARM_USE_AZUREAD=true)

	rm -rf infrastructure/modules/dtos-devops-templates
	git -c advice.detachedHead=false clone --depth=1 --single-branch --branch ${TERRAFORM_MODULES_REF} \
		https://github.com/NHSDigital/dtos-devops-templates.git infrastructure/modules/dtos-devops-templates

	terraform -chdir=infrastructure/terraform init -upgrade -reconfigure \
		-backend-config=subscription_id=${HUB_SUBSCRIPTION_ID} \
		-backend-config=resource_group_name=${STORAGE_ACCOUNT_RG} \
		-backend-config=storage_account_name=${STORAGE_ACCOUNT_NAME} \
		-backend-config=key=${ENVIRONMENT}.tfstate

	$(eval export TF_VAR_app_short_name=${APP_SHORT_NAME})
	$(eval export TF_VAR_docker_image=${DOCKER_IMAGE}:${DOCKER_IMAGE_TAG})
	$(eval export TF_VAR_environment=${ENVIRONMENT})
	$(eval export TF_VAR_hub=${HUB})
	$(eval export TF_VAR_hub_subscription_id=${HUB_SUBSCRIPTION_ID})

terraform-plan: terraform-init # Plan Terraform changes - make <env> terraform-plan DOCKER_IMAGE_TAG=abcd123
	terraform -chdir=infrastructure/terraform plan -var-file ../environments/${ENV_CONFIG}/variables.tfvars

terraform-apply: terraform-init # Apply Terraform changes - make <env> terraform-apply DOCKER_IMAGE_TAG=abcd123
	terraform -chdir=infrastructure/terraform apply -var-file ../environments/${ENV_CONFIG}/variables.tfvars ${AUTO_APPROVE}

terraform-destroy: terraform-init # Destroy Terraform resources - make <env> terraform-destroy
	terraform -chdir=infrastructure/terraform destroy -var-file ../environments/${ENV_CONFIG}/variables.tfvars ${AUTO_APPROVE}
