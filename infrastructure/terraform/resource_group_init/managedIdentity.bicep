param name string
param region string
param fedCredProperties object = {}

resource mi 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  location: region
  name: name
}

resource managedIdentiyGHtoADOFedCred 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = if (!empty(fedCredProperties)) {
  parent: mi
  name: 'github-actions'
  properties: fedCredProperties
}

output miPrincipalID string = mi.properties.principalId
