targetScope='subscription'

param enableSoftDelete bool
param envConfig string
param region string
param storageAccountRGName string
param storageAccountName string
param appShortName string

var hubMap = {
  dev: 'dev'
  int: 'dev'
  nft: 'dev'
  pre: 'prod'
  prd: 'prod'
}
var privateEndpointRGName = 'rg-hub-${envConfig}-uks-hub-private-endpoints'
var privateDNSZoneRGName = 'rg-hub-${hubMap[envConfig]}-uks-private-dns-zones'
var managedIdentityRGName = 'rg-mi-${envConfig}-uks'

// Retrieve existing terraform state resource group
resource storageAccountRG 'Microsoft.Resources/resourceGroups@2024-11-01' existing = {
  name: storageAccountRGName
}
// Retrieve existing private endpoint resource group
resource privateEndpointResourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' existing = {
  name: privateEndpointRGName
}
// Retrieve existing private DNS zone resource group
resource privateDNSZoneRG 'Microsoft.Resources/resourceGroups@2024-11-01' existing = {
  name: privateDNSZoneRGName
}
// Retrieve existing managed identity resource group
resource managedIdentityRG 'Microsoft.Resources/resourceGroups@2024-11-01' existing = {
  name: managedIdentityRGName
}

// Create the managed identity for CD
module managedIdentiy 'managedIdentity.bicep' = {
  scope: managedIdentityRG
  params: {
    region: region
    appShortName: appShortName
    envConfig: envConfig
  }
}

// Create the storage account, blob service and container
module terraformStateStorageAccount 'storage.bicep' = {
  scope: storageAccountRG
  params: {
    storageLocation: region
    storageName: storageAccountName
    enableSoftDelete: enableSoftDelete
    miPrincipalID: managedIdentiy.outputs.miPrincipalID
    miName: managedIdentiy.outputs.miName
  }
}

// Retrieve private DNS zone
module privateDNSZone 'dns.bicep' = {
  scope: privateDNSZoneRG
}

// Create private endpoint and register DNS
module storageAccountPrivateEndpoint 'privateEndpoint.bicep' = {
  scope: privateEndpointResourceGroup
  params: {
    hub: hubMap[envConfig]
    region: region
    storageName: storageAccountName
    storageAccountID: terraformStateStorageAccount.outputs.storageAccountID
    privateDNSZoneID: privateDNSZone.outputs.privateDNSZoneID
  }
}

// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roleID = {
  CDNContributor: 'ec156ff8-a8d1-4d15-830c-5b80698ca432'
  networkContributor: '4d97b98b-1d4f-4787-a291-c67834d212e7'
}

// Let the managed identity configure vnet peering and DNS records
resource networkContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().subscriptionId, envConfig, 'networkContributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleID.networkContributor)
    principalId: managedIdentiy.outputs.miPrincipalID
    description: '${managedIdentiy.outputs.miName} Network Contributor access to subscription'
  }
}

// Let the managed identity configure Front door and its resources
resource CDNContributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().subscriptionId, envConfig, 'CDNContributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleID.CDNContributor)
    principalId: managedIdentiy.outputs.miPrincipalID
    description: '${managedIdentiy.outputs.miName} CDN Contributor access to subscription'
  }
}

output miPrincipalID string = managedIdentiy.outputs.miPrincipalID
output miName string = managedIdentiy.outputs.miName
