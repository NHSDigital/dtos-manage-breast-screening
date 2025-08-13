# Create an environment

This is the initial manual process to create a new environment like review, dev, production...

## Code

- Create the configuration files in `infrastructure/environments/[environment]`
- Add the `[environment]:` target in `scripts/terraform/terraform.mk`
- Add [environment] to the list of environments in `deploy-stage` step of `cicd-2-main-branch.yaml`. For the review enviornment, there is a single item in `cicd-1-pull-request.yaml`.

## Entra ID

- Create postgres Entra ID group in `DTOS Administrative Unit (AU)`: `postgres_manbrs_[environment]_uks_admin`
- Ask CCOE to assign role:
  - [Form for PIM](https://nhsdigitallive.service-now.com/nhs_digital?id=sc_cat_item&sys_id=28f3ab4f1bf3ca1078ac4337b04bcb78&sysparm_category=114fced51bdae1502eee65b9bd4bcbdc)
  - Approver: Add someone from the infrastructure team
  - Role Name: `Group.Read.All`
  - Application Name: `mi-manbrs-[environment]-adotoaz-uks`
  - Application ID: [client.id]
  - Managed identity: `mi-manbrs-[environment]-adotoaz-uks`
  - Description: - Managed identity: `mi-manbrs-[environment]-adotoaz-uks` - Role: permanent on Directory

## Bicep

- Run bicep from AVD: `make [environment] resource-group-init`

<<<<<<< HEAD
## Infra secrets

- Add the infrastructure secrets to the _inf_ key vault `kv-manbrs-[review]-inf`

=======
>>>>>>> e326390 (Document deployment)
## Azure devops

- Create ADO group
  - Name: `Run pipeline - [environment]`
  - Members: `mi-manbrs-[environment]-ghtoado-uks`. There may be more than 1 in the list. Check client id printed below the name.
  - Permissions:
    - View project-level information
- Create new pipeline:
  - Name: `Deploy to Azure - [environment]`
  - Pipeline yaml: `.azuredevops/pipelines/deploy.yml`
- Manage pipeline security:
  - Add group: `Run pipeline - [environment]`
  - Permissions:
    - Edit queue build configuration
    - Queue builds
    - View build pipeline
    - View builds
- Create service connection (ADO)
  - Connection type: `Azure Resource Manager`
  - Identity type: `Managed identity`
  - Subscription for managed identity: `Digital Screening DToS - Devops`
  - Resource group for managed identity: `rg-mi-[environment]-uks`
  - Managed identity: `mi-manbrs-[environment]-adotoaz-uks`
  - Scope level: `Subscription`
  - Subscription: `Digital Screening DToS - Core Services Dev`
  - Resource group for Service connection: leave blank
  - Service Connection Name: `manbrs-[environment]`
  - Do NOT tick: Grant access permission to all pipelines
  - Security: allow `Deploy to Azure - [environment]` pipeline
- Create ADO environment: [environment]
  - Set: exclusive lock (except for review)
  - Add pipeline permission for `Deploy to Azure - [environment]` pipeline

## Github

- Create Github environment [environment]
- Add the protection rule (except in review):
  - Deselect `Allow administrators to bypass configured protection rules`
  - In `Deployment branches and tags` choose `Selected branches and tags` from the drop-down menu
  - Click `Add deployment branch or tag rule` and enter "main"
- Add environment secrets, from `mi-manbrs-[environment]-ghtoado-uks` in github
  - _AZURE_CLIENT_ID_
  - _AZURE_SUBSCRIPTION_ID_

## First run

- Test running terraform manually from the AVD (Optional)
- Raise a pull request, review and merge to trigger the pipeline
- Check ADO pipeline. You may be prompted to authorise:
  - Pipeline: service connection
  - Environment: service connection and agent pool

## App secrets

- Add the application secrets to the _app_ key vault `kv-manbrs-[review]-app`
- Set `fetch_secrets_from_app_key_vault` terraform variable to `true`
- Test running terraform manually from the AVD (Optional)
- Raise a pull request, review and merge to trigger the pipeline
