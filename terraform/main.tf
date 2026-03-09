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