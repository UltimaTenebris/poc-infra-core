resource "azurerm_cognitive_account" "doc_intelligence" {
  name                = "ocr-doc-ai"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "FormRecognizer"
  sku_name            = "S0"
}

resource "azurerm_cognitive_account" "openai" {
  name                = "ocr-openai"
  location            = "East US"
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "OpenAI"
  sku_name            = "S0"
}