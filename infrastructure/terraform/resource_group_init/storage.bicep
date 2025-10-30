param storageLocation string
param storageName string
param enableSoftDelete bool
param miPrincipalID string
param miName string
param userGroupPrincipalID string
param userGroupName string

// Create storage account without public access
resource storageAccount 'Microsoft.Storage/storageAccounts@2024-01-01' = {
  name: storageName
  location: storageLocation
  sku: {
    name: 'Standard_RAGRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    encryption: {
      requireInfrastructureEncryption: true
    }
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Disabled'
  }
}


// Create the blob service
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2024-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    containerDeleteRetentionPolicy: {
      days: enableSoftDelete ? 15 : null
      enabled: enableSoftDelete
    }
    deleteRetentionPolicy: {
      days: enableSoftDelete ? 15 : null
      enabled: enableSoftDelete
    }
    isVersioningEnabled: true
  }
}

// Create the blob container
resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2024-01-01' = {
  parent: blobService
  name: 'terraform-state'
  properties: {
    publicAccess: 'None'
    defaultEncryptionScope: '$account-encryption-key'
    denyEncryptionScopeOverride: false
  }
}

// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roleID = {
  blobContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
}

// Define role assignments array
var roleAssignments = [
  {
    roleName: 'blobContributor'
    roleId: roleID.blobContributor
    description: 'Blob Contributor access to subscription'
  }
]

// Managed identity RBAC assignments using loop
resource miRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for role in roleAssignments: {
  name: guid(subscription().subscriptionId, miPrincipalID, role.roleName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', role.roleId)
    principalId: miPrincipalID
    description: '${miName} ${role.description}'
  }
}]

// Entra ID Group RBAC assignments using loop
resource groupRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for role in roleAssignments:{
  name: guid(subscription().subscriptionId, userGroupPrincipalID, role.roleName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', role.roleId)
    principalId: userGroupPrincipalID
    principalType: 'Group'
    description: '${userGroupName} ${role.description}'
  }
}]

// Output the storage account ID so it can be used to create the private endpoint
output storageAccountID string = storageAccount.id
