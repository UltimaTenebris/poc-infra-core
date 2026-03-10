resource "azurerm_service_plan" "az-sp-ly1" {
  name                = "example-app-service-plan"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1"
}


resource "azurerm_linux_function_app" "az-linux-fa" {
  name                = "function-app-bestring"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location

  storage_account_name       = azurerm_storage_account.storage.name
  storage_account_access_key = azurerm_storage_account.storage.primary_access_key
  service_plan_id            = azurerm_service_plan.az-sp-ly1.id

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
    FILE_SHARE_NAME      = azurerm_storage_share.pdf_share.name

    APPLICATIONINSIGHTS_CONNECTION_STRING = azurerm_application_insights.func_ai.connection_string

  }
}