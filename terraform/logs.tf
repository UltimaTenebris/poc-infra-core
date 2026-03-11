resource "azurerm_log_analytics_workspace" "ai_ws" {
  name                = "managed-bestrong-function-ai-ws${terraform.workspace}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
}

resource "azurerm_application_insights" "func_ai" {
  name                = "bestrong-function-ai${terraform.workspace}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
  
  workspace_id = azurerm_log_analytics_workspace.ai_ws.id
}
  