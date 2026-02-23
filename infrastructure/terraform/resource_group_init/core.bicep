targetScope='subscription'

@minLength(1)
param miPrincipalId string
@minLength(1)
param miName string
@minLength(1)
param userGroupPrincipalID string
@minLength(1)
param userGroupName string

// See: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles
var roleID = {
  contributor: 'b24988ac-6180-42a0-ab88-20f7382dd24c'
  kvSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  kvSecretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
  rbacAdmin: 'f58310d9-a9f6-439a-9e8d-f62e7b41a168'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  storageQueueDataContributor: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
}

// Define role assignments for managed identity
var miRoleAssignments = [
  {
    roleName: 'contributor'
    roleId: roleID.contributor
    description: 'Contributor access to subscription'
  }
  {
    roleName: 'kvSecretsUser'
    roleId: roleID.kvSecretsUser
    description: 'kvSecretsUser access to subscription'
  }
  {
    roleName: 'rbacAdmin'
    roleId: roleID.rbacAdmin
    description: 'Role Based Access Control Administrator access to subscription. Can assign Key Vault Secrets User, Storage Blob Data Contributor, and Storage Queue Data Contributor roles.'
    // Optional properties - only rbacAdmin has a condition
    condition: '((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/write\'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleID.kvSecretsOfficer}, ${roleID.storageBlobDataContributor}, ${roleID.storageQueueDataContributor}})) AND ((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/delete\'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleID.kvSecretsOfficer}, ${roleID.storageBlobDataContributor}, ${roleID.storageQueueDataContributor}}))'
    conditionVersion: '2.0'
  }
]

// Define role assignments for Entra ID group
var groupRoleAssignments = [
  {
    roleName: 'contributor'
    roleId: roleID.contributor
    description: 'Contributor access to subscription'
  }
  {
    roleName: 'kvSecretsOfficer'
    roleId: roleID.kvSecretsOfficer
    description: 'kvSecretsOfficer access to subscription'
  }
  {
    roleName: 'rbacAdmin'
    roleId: roleID.rbacAdmin
    description: 'Role Based Access Control Administrator access to subscription. Can assign Key Vault Secrets Officer, Storage Blob Data Contributor, and Storage Queue Data Contributor roles.'
    // Optional properties - only rbacAdmin has a condition
    condition: '((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/write\'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleID.kvSecretsOfficer}, ${roleID.storageBlobDataContributor}, ${roleID.storageQueueDataContributor}})) AND ((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/delete\'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleID.kvSecretsOfficer}, ${roleID.storageBlobDataContributor}, ${roleID.storageQueueDataContributor}}))'
    conditionVersion: '2.0'
  }
]

// This creates one resource for each item in the miRoleAssignments array
resource miRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for role in miRoleAssignments: {
  // guid() ensures unique names for each assignment
  name: guid(subscription().subscriptionId, miPrincipalId, role.roleName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', role.roleId)
    principalId: miPrincipalId
    description: '${miName} ${role.description}'
    // Conditionally include the 'condition' property only if it exists in the role object
    condition: role.?condition
    conditionVersion: role.?conditionVersion
  }
}]


// This creates one resource for each item in the groupRoleAssignments array
resource groupRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for role in groupRoleAssignments: {
  name: guid(subscription().subscriptionId, userGroupPrincipalID, role.roleName)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', role.roleId)
    principalId: userGroupPrincipalID
    principalType: 'Group'
    description: '${userGroupName} ${role.description}'
    condition: role.?condition
    conditionVersion: role.?conditionVersion
  }
}]
