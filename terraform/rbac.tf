resource "azurerm_role_assignment" "function_openai_user" {
  scope                = azurerm_cognitive_account.openai.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_linux_function_app.az-linux-fa.identity[0].principal_id

  depends_on = [
    azurerm_linux_function_app.az-linux-fa
  ]
}

resource "azurerm_role_assignment" "function_docintel_user" {
  scope                = azurerm_cognitive_account.doc_intelligence.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_linux_function_app.az-linux-fa.identity[0].principal_id

  depends_on = [
    azurerm_linux_function_app.az-linux-fa
  ]
}

resource "azurerm_role_assignment" "function_fileshare_reader" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage File Data SMB Share Elevated Contributor"
  principal_id         = azurerm_linux_function_app.az-linux-fa.identity[0].principal_id

  depends_on = [
    azurerm_linux_function_app.az-linux-fa
  ]
}

resource "azurerm_role_assignment" "function_fileshare_data_prev" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage File Data Privileged Contributor"
  principal_id         = azurerm_linux_function_app.az-linux-fa.identity[0].principal_id
}



