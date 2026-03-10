resource "azurerm_resource_group" "rg" {
  name     = "BeStrongTeam1"
  location = var.location
}


resource "azurerm_storage_account" "storage" {
  name                     = "team1storageac"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags = {
    environment = var.environment
  }
}

resource "azurerm_storage_container" "container" {
  name                  = "tfstate"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

resource "azurerm_storage_share" "pdf_share" {
  name                 = "team1pdffiles"
  storage_account_name = azurerm_storage_account.storage.name
  quota                = 50
}

resource "azurerm_storage_container" "blob_container" {
  name                  = "team1blobcontainer"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}

resource "azurerm_cognitive_account" "doc_intelligence" {
  name                = "ocr-doc-ai"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "FormRecognizer"
  sku_name            = "S0"

    custom_subdomain_name = "bestrong-doc-ai"

}



resource "azurerm_cognitive_account" "openai" {
  name                = "ocr-openai-01"
  location            = "francecentral"
  resource_group_name = azurerm_resource_group.rg.name
  kind                = "OpenAI"
  sku_name            = "S0"

  custom_subdomain_name = "ocr-openai-01"

}

resource "azurerm_cognitive_deployment" "gpt4o" {
  name                 = "o3-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "o3-mini"
    version = "2025-01-31"
  }

  scale {
    type     = "GlobalStandard"
    capacity = 1
  }
}