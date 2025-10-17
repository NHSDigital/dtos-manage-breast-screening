targetScope = 'subscription'

param groupObjectId string
param appShortName string
param envConfig string

// Construct the expected group name for validation/documentation purposes
var expectedGroupName = 'screening_${appShortName}_${envConfig}'

// Output the group's principal ID for use in role assignments
output groupPrincipalId string = groupObjectId
output expectedGroupName string = expectedGroupName
