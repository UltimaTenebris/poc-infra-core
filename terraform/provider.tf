terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "Backend"
    storage_account_name = "team1storageforbacekfend"
    container_name       = "tfstate"
    key                  = "terraform.tfstateenv:dev"
  }
}


provider "azurerm" {
  features {}
}
