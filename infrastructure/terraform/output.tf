output "internal_url" {
  value = var.deploy_container_apps? module.container-apps[0].internal_url : null
}

output "external_url" {
  value = var.deploy_container_apps? module.container-apps[0].external_url : null
}
