variable "location" {
  default = "swedencentral"
}

variable "prefix" {
  default = "bestrong"
}

# variable "environment" {
#   type        = string
#   description = "Environment (dev / stage / prod)"
# }

variable "discord_webhook" {
  type      = string
  sensitive = true
}

variable "telegram_bot_token" {
  type      = string
  sensitive = true
}

variable "telegram_chat_id" {
  type      = string
  sensitive = true
}