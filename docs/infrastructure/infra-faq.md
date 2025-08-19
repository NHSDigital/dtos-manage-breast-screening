# Infrastructure FAQ

- [Terraform](#terraform)
- [Github action triggering Azure devops pipeline](#github-action-triggering-azure-devops-pipeline)
- [Bicep errors](#bicep-errors)


## Terraform
### Import into terraform state file

To import Azure resources into the Terraform state file, you can use the following command. If you're working on an AVD machine, you may need to set the environment variables:
- `ARM_USE_AZUREAD` to use Azure AD instead of a shared key
- `MSYS_NO_PATHCONV` to stop git bash from expanding file paths

Below is an example of how to do it.

```shell
export ARM_USE_AZUREAD=true
export MSYS_NO_PATHCONV=true

terraform -chdir=infrastructure/terraform import  -var-file ../environments/${ENV_CONFIG}/variables.tfvars module.infra[0].module.postgres_subnet.azurerm_subnet.subnet  /subscriptions/xxx/resourceGroups/rg-manbrs-review-uks/providers/Microsoft.Network/virtualNetworks/vnet-review-uks-manbrs/subnets/snet-postgres
```

### Error: Failed to load state
This happens when running terraform commands accessing the state file like [import](#import-into-terraform-state-file), `state list` or `force-unlock`.
```
Failed to load state: blobs.Client#Get: Failure responding to request: StatusCode=403 -- Original Error: autorest/azure: Service returned an error. Status=403 Code="KeyBasedAuthenticationNotPermitted" Message="Key based authentication is not permitted on this storage account.
```

By default terraform tries using a shared key, which is not allowed. To force using Entra ID, use `ARM_USE_AZUREAD`.

```shell
ARM_USE_AZUREAD=true terraform force-unlock xxx-yyy
```

## Github action triggering Azure devops pipeline
### Application with identifier '***' was not found in the directory
Example:
```
Running Azure CLI Login.
...
Attempting Azure CLI login by using OIDC...
Error: AADSTS700016: Application with identifier '***' was not found in the directory 'NHS Strategic Tenant'. This can happen if the application has not been installed by the administrator of the tenant or consented to by any user in the tenant. You may have sent your authentication request to the wrong tenant. Trace ID: xxx Correlation ID: xxx Timestamp: xxx

Error: Interactive authentication is needed. Please run:
az login
```
The managed identity does not exist or Github secrets are not set correctly

### The client '***' has no configured federated identity credentials
Example:
```
Running Azure CLI Login.
...
Attempting Azure CLI login by using OIDC...
Error: AADSTS70025: The client '***'(mi-manbrs-ado-review-temp) has no configured federated identity credentials. Trace ID: xxx Correlation ID: xxx Timestamp: xxx

Error: Interactive authentication is needed. Please run:
az login
```
Federated credentials are not configured.

### No subscriptions found for ***
Example:
```
Running Azure CLI Login.
...
Attempting Azure CLI login by using OIDC...
Error: No subscriptions found for ***.
```
Give the managed identity Reader role on a subscription (normally Devops)

### Pipeline permissions
Examples:
```
ERROR: TF401444: Please sign-in at least once as ***\***\xxx in a web browser to enable access to the service.
Error: Process completed with exit code 1.
```
Or
```
ERROR: TF400813: The user 'xxx' is not authorized to access this resource.
Error: Process completed with exit code 1.
```
Or
```
ERROR: VS800075: The project with id 'vstfs:///Classification/TeamProject/' does not exist, or you do not have permission to access it.
Error: Process completed with exit code 1.
```
The Github secret must reflect the right managed identity, the managed identity must have the following permissions on the pipeline, via its ADO group:
- Edit queue build configuration
- Queue builds
- View build pipeline

The ADO group must have the "View project-level information" permission.

### The service connection does not exist
Example:
```
The pipeline is not valid. Job DeployApp: Step input azureSubscription references service connection manbrs-review which could not be found. The service connection does not exist, has been disabled or has not been authorized for use. For authorization details, refer to https://aka.ms/yamlauthz. Job DeployApp: Step input azureSubscription references service connection manbrs-review which could not be found. The service connection does not exist, has been disabled or has not been authorized for use. For authorization details, refer to https://aka.ms/yamlauthz.
```
The Azure service connection manbrs-[environment] is missing

## Bicep errors
### RoleAssignmentUpdateNotPermitted
Example:
```
ERROR: {"status":"Failed","error":{"code":"DeploymentFailed","target":"/subscriptions/xxx/providers/Microsoft.Resources/deployments/main","message":"At least one reson failed. Please list deployment operations for details. Please see https://aka.ms/arm-deployment-operations for usage details.","details":[{"code":"RoleAssignmentUpdateNotPermitted","message":"Tenprincipal ID, and scope are not allowed to be updated."},{"code":"RoleAssignmentUpdateNotPermitted","message":"Tenant ID, application ID, principal ID, and scope are not allowed to be updated."},{"cteNotPermitted","message":"Tenant ID, application ID, principal ID, and scope are not allowed to be updated."}]}}
```
When deleting a MI, its role assignment is not deleted. When recreating the MI, bicep tries to update the role assignment and is not allowed to. Solution:
- Find the role assignment id. Here: abcd-123
- Navigate to subscriptions and resource group IAM and search for the role assignment id
- Delete the role assignment via the portal

If you can't find the right scope, follow this process:
- Find the role assignment id. Here: abcd-123
```
 ~ Microsoft.Authorization/roleAssignments/abcd-123 [2022-04-01]
    ~ properties.principalId: "xxx" => "[reference('/subscriptions/xxx/resourceGroups/rg-mi-review-uks/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mi-manbrs-ado-review-uks', '2024-11-30').principalId]"
```
- Get the subscription id
- List role assignments: `az role assignment list --scope "/subscriptions/[subscription id]"`
- Look for the role assignment id abcd-123 to retrieve the other details. It may named: Unknown.
- Delete the role assignment via the portal

### PrincipalNotFound
Example:
```
ERROR: {"status":"Failed","error":{"code":"DeploymentFailed","target":"/subscriptions/exxx/providers/Microsoft.Resources/deployments/main","message":"At least one reson failed. Please list deployment operations for details. Please see https://aka.ms/arm-deployment-operations for usage details.","details":[{"code":"PrincipalNotFound","message":"Principal xxx does not exist in the directory xxx. Check that you have the correct principal ID. If you are creating this principal and then immediately assigning a role, this era replication delay. In this case, set the role assignment principalType property to a value, such as ServicePrincipal, User, or Group.  See https://aka.ms/docs-principaltype"}...
```
Race condition: the managed identity is not created in time for the resources that depend on it. Solution: rerun the command.

### The client does not have permission
```
{"code": "InvalidTemplateDeployment", "message": "Deployment failed with multiple errors: 'Authorization failed for template resource 'xxx' of type 'Microsoft.Authorization/roleAssignments'. The client 'xxx' with object id 'xxx' does not have permission to perform action 'Microsoft.Authorization/roleAssignments/write' at scope '/subscriptions/xxx/providers/Microsoft.Authorization/roleAssignments/xxx'...
```
Request Owner role on subscriptions via PIM.
