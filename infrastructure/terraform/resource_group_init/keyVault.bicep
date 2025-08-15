
param enableSoftDelete bool
param keyVaultName string
param miPrincipalId string
param miName string
param region string

// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roleID = {
  kvSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
}

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: keyVaultName
  location: region
  properties: {
    tenantId: subscription().tenantId
    sku: {
      name: 'standard'
      family: 'A'
    }
    enableRbacAuthorization: true
    enabledForDeployment: true
    enabledForTemplateDeployment: true
    enabledForDiskEncryption: true
    enableSoftDelete: enableSoftDelete
    publicNetworkAccess: 'disabled'
  }
}

// Let the managed identity read key vault secrets during terraform plan
resource kvSecretsUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().subscriptionId, miPrincipalId, 'kvSecretsUser')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleID.kvSecretsUser)
    principalId: miPrincipalId
    description: '${miName} kvSecretsUser access to resource group'
  }
}

// Output the key vault ID so it can be used to create the private endpoint
output keyVaultID string = keyVault.id
