#!/bin/bash

# Replace the values in the variable declarations here:
resourceGroup='rg-mi-review-l1-uks'
sqlGroupName='postgres_manbrs_review-l1_uks_admin'
managedIdentityName='mi-manbrs-review-l1-uks'

# Create the resource group
az group create --name $resourceGroup --location uksouth

managedIdentityId=$(az identity show --name ${managedIdentityName} --resource-group ${resourceGroup} | jq -r .principalId)

# Create the SQL Server AD Security Group:
az ad group create --display-name $sqlGroupName --mail-nickname $sqlGroupName --description "Group to manage Postgres database in the dev environment"
ownerId=$(az ad user show --id c-allo4@HSCIC365.onmicrosoft.com | jq -r .id)
az ad group owner add --group $sqlGroupName --owner-object-id $ownerId
az ad group member add --group $sqlGroupName --member-id $managedIdentityId

# Create the Federated Identity via the portal.
