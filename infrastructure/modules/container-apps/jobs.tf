# Reads and acknowledges messages (DAT files) in MESH
# Stores the files in Azure Blob Storage
module "store_mesh_data" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-not-smd-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py store_mesh_messages"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.azure_blob_storage_identity.id]

  environment_variables = {
    BLOB_CONTAINER_NAME = "nbss-appointment-data"
    MESH_BASE_URL       = var.mesh_base_url
    AZURE_CLIENT_ID     = module.azure_blob_storage_identity.client_id
    DJANGO_ENV          = var.env_config
  }

  schedule_trigger_config {
    cron_expression          = "*/15 * * * *" # Every 15 minutes
    parallelism              = 1
    replica_completion_count = 1
  }
}

# Reads file data from Azure Blob Storage
# Inserts or updates records in Postgresql
module "create_appointments" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-not-cap-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py create_appointments"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.azure_blob_storage_identity.id, module.db_connect_identity.id]

  environment_variables = {
    BLOB_CONTAINER_NAME = "nbss-appointment-data"
    DATABASE_HOST       = module.postgres.host
    DATABASE_NAME       = module.postgres.database_names[0]
    DATABASE_USER       = module.db_connect_identity.name
    SSL_MODE            = "require"
    AZURE_CLIENT_ID     = module.db_connect_identity.client_id
    DJANGO_ENV          = var.env_config
  }

  schedule_trigger_config {
    cron_expression          = "*/30 * * * *" # Every 30 minutes
    parallelism              = 1
    replica_completion_count = 1
  }
}

# Reads appointment data from Postgresql
# Makes a message batch request to NHS Notify
module "send_message_batch" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-not-smb-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py send_message_batch"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.db_connect_identity.id]

  environment_variables = {
    API_MESSAGE_BATCH_URL = var.api_message_batch_url
    DATABASE_HOST         = module.postgres.host
    DATABASE_NAME         = module.postgres.database_names[0]
    DATABASE_USER         = module.db_connect_identity.name
    SSL_MODE              = "require"
    RETRY_QUEUE_NAME      = "retry-message-batches"
    AZURE_CLIENT_ID       = module.db_connect_identity.client_id
    DJANGO_ENV            = var.env_config
  }

  schedule_trigger_config {
    cron_expression          = "0 11,13,15 * * *" # 1100, 1300 and 1500
    parallelism              = 1
    replica_completion_count = 1
  }
}

# Fetches failed message batches from Azure Storage Queue
# Retries a message batch request to NHS Notify
module "retry_failed_message_batch" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-not-rmb-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py retry_failed_message_batch"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.azure_queue_storage_identity.id]

  environment_variables = {
    API_MESSAGE_BATCH_URL = var.api_message_batch_url
    RETRY_QUEUE_NAME      = "retry-message-batches"
    AZURE_CLIENT_ID       = module.azure_queue_storage_identity.client_id
    DJANGO_ENV            = var.env_config
  }
}

# Fetches message statuses from Azure Storage Queue
# Inserts message statuses into Postgresql
module "save_message_status" {
  source = "../dtos-devops-templates/infrastructure/modules/container-app-job"

  name                         = "${var.app_short_name}-not-sms-${var.environment}"
  container_app_environment_id = var.container_app_environment_id
  resource_group_name          = azurerm_resource_group.main.name

  fetch_secrets_from_app_key_vault = var.fetch_secrets_from_app_key_vault
  app_key_vault_id                 = var.app_key_vault_id

  # Run everything through /bin/sh
  container_command = ["/bin/sh", "-c"]
  container_args = [
    "python manage.py save_message_status"
  ]

  docker_image               = var.docker_image
  user_assigned_identity_ids = [module.azure_queue_storage_identity.id, module.db_connect_identity.id]

  environment_variables = {
    DATABASE_HOST             = module.postgres.host
    DATABASE_NAME             = module.postgres.database_names[0]
    DATABASE_USER             = module.db_connect_identity.name
    SSL_MODE                  = "require"
    STATUS_UPDATES_QUEUE_NAME = "message-status-updates"
    AZURE_CLIENT_ID           = module.db_connect_identity.client_id
    DJANGO_ENV                = var.env_config
  }
}
