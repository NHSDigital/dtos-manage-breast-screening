targetScope='subscription'

@minLength(1)
param miPrincipalId string
@minLength(1)
param miName string

// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roleID = {
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  kvSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  rbacAdmin: 'f58310d9-a9f6-439a-9e8d-f62e7b41a168'
}

// Let the managed identity configure resources in the subscription
resource contributorAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().subscriptionId, miPrincipalId, 'contributor')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleID.contributor)
    principalId: miPrincipalId
    description: '${miName} Contributor access to subscription'
  }
}

// Let the managed identity read key vault secrets during terraform plan
resource kvSecretsUserAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().subscriptionId, miPrincipalId, 'kvSecretsUser')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleID.kvSecretsUser)
    principalId: miPrincipalId
    description: '${miName} kvSecretsUser access to subscription'
  }
}

// Let the managed identity assign the Key Vault Secrets User role to the container app managed identity
resource rbacAdminAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().subscriptionId, miPrincipalId, 'rbacAdmin')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleID.rbacAdmin)
    principalId: miPrincipalId
    condition: '((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/write\'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleID.kvSecretsUser}})) AND ((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/delete\'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleID.kvSecretsUser}}))'
    conditionVersion: '2.0'
    description: '${miName} Role Based Access Control Administrator access to subscription. Only allows assigning the Key Vault Secrets User role.'
  }
}
