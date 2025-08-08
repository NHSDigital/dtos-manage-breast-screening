## Import into terraform state file

To import Azure resources into the Terraform state file, you can use the following command. If you're working on an AVD machine, you may need to set the environment variables:
- `ARM_USE_AZUREAD` to use Azure AD instead of a shared key
- `MSYS_NO_PATHCONV` to stop git bash from expanding file paths

Below is an example of how to do it.

```shell
export ARM_USE_AZUREAD=true
export MSYS_NO_PATHCONV=true

terraform -chdir=infrastructure/terraform import  -var-file ../environments/${ENV_CONFIG}/variables.tfvars module.infra[0].module.postgres_subnet.azurerm_subnet.subnet  /subscriptions/xxx/resourceGroups/rg-manbrs-review-uks/providers/Microsoft.Network/virtualNetworks/vnet-review-uks-manbrs/subnets/snet-postgres
```

## Error: Failed to load state
This happens when running terraform commands accessing the state file like [import](#import-into-terraform-state-file), `state list` or `force-unlock`.
```
Failed to load state: blobs.Client#Get: Failure responding to request: StatusCode=403 -- Original Error: autorest/azure: Service returned an error. Status=403 Code="KeyBasedAuthenticationNotPermitted" Message="Key based authentication is not permitted on this storage account.
```

By default terraform tries using a shared key, which is not allowed. To force using Entra ID, use `ARM_USE_AZUREAD`.

```shell
ARM_USE_AZUREAD=true terraform force-unlock xxx-yyy
```
