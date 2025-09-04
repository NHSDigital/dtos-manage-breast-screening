# Deployment

## Infrastructure

The code is packaged into a docker image which is deployed to [Azure container apps](https://learn.microsoft.com/en-us/azure/container-apps/). The main app is a web application, with an HTTP ingress. And the second one is an [Azure container app job](https://learn.microsoft.com/en-us/azure/container-apps/jobs?tabs=azure-cli), triggered on demand to run the database migration.

The web application does not have a public endpoint. It is only accessible via [Azure front door](https://learn.microsoft.com/en-us/azure/frontdoor/) which is a CDN providing TLS certificates, firewall, scaling and caching. The internal endpoint is accessible via [Azure Virtual Desktop](https://learn.microsoft.com/en-us/azure/virtual-desktop/).

The data is hosted on [Azure postgres flexible server](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/overview).

## Docker build

The build pipeline builds and pushes a docker image to [Github container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry). The image is tagged with:

- branch name: for docker build caching
- commit SHA: to uniquely identify the image during deployment, prefixed by "git-sha-".
- image digest sha: immutable tag

## Automated deployment

The deployment is split between:

- [Github actions](https://github.com/features/actions) for Continuous Integration (CI)
- [Azure devops](https://azure.microsoft.com/en-us/products/devops) pipelines for Continuous Deployment (CD)

### Github actions

Runs on Github hosted runners on the internet. They run all our tests (unit, functional, security, linting...). They don't have access to our internal network nor any sensitive data.

To deploy an environment, they authenticate to Azure and delegate the work to [Azure devops piplines](#azure-devops-pipelines).

See [all Github actions](https://github.com/NHSDigital/dtos-manage-breast-screening/actions).

### Azure devops pipelines

We use a public repository as required by the [NHS Service standard](https://service-manual.nhs.uk/standards-and-technology/service-standard-points/12-make-new-source-code-open). For security reasons, deployments cannot run from Github actions and run instead on Azure devops private runners inside our internal network. They have access to the network and any Azure resource deployed onto it.

See [all Azure devops pipelines](https://dev.azure.com/nhse-dtos/dtos-manage-breast-screening/_build).

### Review apps

When a pull request is raised, add a "deploy" label to deploy a _review app_ (concept borrowed from [Heroku](https://devcenter.heroku.com/articles/github-integration-review-apps)). It triggers the [CI/CD pull request](https://github.com/NHSDigital/dtos-manage-breast-screening/actions/workflows/cicd-1-pull-request.yaml) Github action workflow, which runs tests then authenticates to Azure and triggers the [Deploy review app](https://dev.azure.com/nhse-dtos/dtos-manage-breast-screening/_build?definitionId=102) Azure devops pipeline. It runs terraform to deploy the application, database and front door configuration.

To make this process faster and less costly, most of the infrastructure is reused for all review apps: networking, key vaults, container app environments... The base infrastructure is only updated by the pipeline on the main branch.

Also, by default a container version of postgres is deployed, as opposed to a full Azure postgres server. This behaviour can be changed by setting `deploy_database_as_container` to false. Note: each postgres container exposes a unique port, based on the PR number.

When the pull request is closed or merged, and if it has the "deploy" label, the [Delete review app](https://github.com/NHSDigital/dtos-manage-breast-screening/actions/workflows/cicd-1-pull-request-closed.yaml) workflow is triggered, followed by the [Delete review app](https://dev.azure.com/nhse-dtos/dtos-manage-breast-screening/_build?definitionId=103) Azure devops pipeline. It runs _terraform destroy_ to delete the resources.

### Main branch

When a pull request is merged to the main branch, the [CI/CD main branch](https://github.com/NHSDigital/dtos-manage-breast-screening/actions/workflows/cicd-2-main-branch.yaml) is triggered. It runs tests then authenticates to Azure and triggers the [Deploy to Azure](https://dev.azure.com/nhse-dtos/dtos-manage-breast-screening/_build?definitionId=93) Azure devops pipeline. It runs terraform to deploy the entire environment, including both infrastructure and applications. Any manual change is overwritten by terraform.

## Application secrets

The application requires secrets provided as environment variables. Terraform creates an _app_ Azure key vault and all its secrets are mapped directly to the app as environment variables. Developers can access the key vault to create and update the secrets manually.

Notes:

- [the process requires multiple steps](https://github.com/NHSDigital/dtos-devops-templates/tree/main/infrastructure/modules/container-app#key-vault-secrets) to set up an environment initially. The process is documented in [create-environment](create-environment.md).
- The secrets names in key vault are uppercase with hyphen separators. They are mapped to environment variables as uppercase with underscore separator. e.g. `SECRET-KEY` is mapped to `SECRET_KEY`.

## Manual deployment

For each environment, e.g. 'dev':

1. Connect to [Azure virtual desktop](https://azure.microsoft.com/en-us/products/virtual-desktop). Ask the platform team for access with Administrator role.
1. If not present, install the following software: terraform (version 1.7.0), git, make, jq.
   - Run a Command prompt as administrator
   - choco install terraform --version 1.7.0
   - choco install terraform git make jq
1. Open git bash
1. Clone the repository: `git clone https://github.com/NHSDigital/dtos-manage-breast-screening.git`
1. Enter the directory and select the branch, tag, commit...
1. Login: `az login`
1. Create the resource group: `make dev resource-group-init`. This is only required when creating the environment from scratch.
1. Deploy:
   ```shell
   make dev terraform-plan DOCKER_IMAGE_TAG=git-sha-af32637e7e6a07e36158dcb8d7ed90be49be1xyz
   ```
1. The web app URL will be displayed as output. Copy it into a browser on the AVD to access the app.

## Manual deployment of the review app environments

[Review app environments](#review-apps) differ slightly from other environments. They are lightweight versions of the application and are designed to share much of the core Azure infrastructure. As a result, there is a one-to-many relationship between the container apps and the container app environment.

### Step 1

If you run the following command _without_ the `PR_NUMBER` parameter, it will apply only the infrastructure module:

```shell
make review terraform-apply
```

This is usually deployed by the pipeline on the main branch.

### Step 2

If you include the `PR_NUMBER` parameter (it can be any number), it will apply the container-apps module instead of the infrastructure module:

```shell
make review terraform-apply DOCKER_IMAGE_TAG=git-sha-01ecb79d561f55be60072a093dd167fe8eb5b42e PR_NUMBER=123
```

### Delete review app

Run terraform-destroy:

```shell
make review terraform-destroy DOCKER_IMAGE_TAG=git-sha-01ecb79d561f55be60072a093dd167fe8eb5b42e PR_NUMBER=123
```
