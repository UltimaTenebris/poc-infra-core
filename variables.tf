variable "location" {
  default = "germanywestcentral"
}

variable "prefix" {
  default = "bestrong"
}

variable "environment" {
  type        = string
  description = "Environment (dev / stage / prod)"
}
