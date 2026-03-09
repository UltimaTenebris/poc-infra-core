resource "azurerm_resource_group" "rg" {
  name     = "BeStrongTeam01"
  location = var.location
}

resource "azurerm_storage_account" "storage" {
  name                     = "${var.prefix}-storage"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = var.environment
  }
}

resource "azurerm_storage_share" "pdf_share" {
  name                 = "${var.prefix}-pdf-files"
  storage_account_name = azurerm_storage_account.storage.name
  quota                = 50
}

resource "azurerm_storage_container" "blob_container" {
  name                  = "${var.prefix}-blob-container"
  storage_account_name  = azurerm_storage_account.storage.name
  container_access_type = "private"
}