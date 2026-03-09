terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  # backend "azurerm" {
  #   resource_group_name  = "BeStrongTeam1"
  #   storage_account_name = "team1storageac"
  #   container_name       = "tfstate"
  #   key                  = "terraform.tfstate"
  # }
}

provider "azurerm" {
  features {}
}
