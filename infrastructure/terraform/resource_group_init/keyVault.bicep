
param enableSoftDelete bool
param keyVaultName string
param region string

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

// Output the key vault ID so it can be used to create the private endpoint
output keyVaultID string = keyVault.id
