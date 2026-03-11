resource "azurerm_service_plan" "example" {
  name                = "example-app-service-plan-${terraform.workspace}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "az-linux-fa" {
  name                = "function-app-bestring${terraform.workspace}"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  service_plan_id            = azurerm_service_plan.example.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    application_stack {
      python_version = "3.10"
    }

    app_service_logs {
      disk_quota_mb         = 35
      retention_period_days = 3
    }
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME = "python"

    DOC_INTEL_ENDPOINT = "https://${azurerm_cognitive_account.doc_intelligence.custom_subdomain_name}.cognitiveservices.azure.com/"
    
    AZURE_OPENAI_ENDPOINT = "https://${azurerm_cognitive_account.openai.custom_subdomain_name}.openai.azure.com"
    AZURE_OPENAI_DEPLOYMENT = "o3-mini"

    STORAGE_ACCOUNT_NAME = azurerm_storage_account.storage.name

    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.func_ai.connection_string

    SUFFIX = terraform.workspace

    #SECRETS
    DISCORD_WEBHOOK_URL = var.discord_webhook

    TELEGRAM_BOT_TOKEN = var.telegram_bot_token

    TELEGRAM_CHAT_ID = var.telegram_chat_id

  }
}