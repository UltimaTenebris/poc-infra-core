resource "azurerm_log_analytics_workspace" "ai_ws" {
  name                = "managed-bestrong-function-ai-ws"
  location            = azurerm_resource_group.rg.location
  resource_group_name = "ai_bestrong-function-ai_dbd34afb-a663-4e0c-9a7b-f3ede38e3dc3_managed"
  sku                 = "PerGB2018"
}

resource "azurerm_application_insights" "func_ai" {
  name                = "bestrong-function-ai"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  
  workspace_id = azurerm_log_analytics_workspace.ai_ws.id
}
