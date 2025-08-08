param resourceServiceType string

var dnsZoneName = {
  storage: 'privatelink.blob.${environment().suffixes.storage}'
  // Cannot read vault URL from environment() because of https://github.com/Azure/bicep/issues/9839
  keyVault: 'privatelink.vaultcore.azure.net'
}

// Retrieve the private DNS zone for storage accounts
resource privateDNSZone 'Microsoft.Network/privateDnsZones@2024-06-01' existing = {
  name: dnsZoneName[resourceServiceType]
}

output privateDNSZoneID string = privateDNSZone.id
