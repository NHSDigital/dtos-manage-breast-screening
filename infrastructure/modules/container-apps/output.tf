output "internal_url" {
  value = module.webapp.url
}

output "external_url" {
  value = "https://${module.frontdoor_endpoint.custom_domains["${var.environment}-domain"].host_name}/"
}
