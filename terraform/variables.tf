# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model_uuid" {
  description = "UUID of the Juju model to deploy to"
  type        = string
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "ldap-integrator"
}

variable "base" {
  description = "The charm base"
  type        = string
  default     = "ubuntu@22.04"
}

variable "channel" {
  description = "Channel to use for the charm"
  type        = string
  default     = "latest/stable"
}

variable "config" {
  description = "The charm config"
  type        = map(string)
  default     = {}
}

variable "constraints" {
  description = "The constraints to be applied"
  type        = string
  default     = ""
}

variable "revision" {
  description = "Revision of the charm to deploy"
  type        = number
  default     = null
}

variable "units" {
  description = "Number of units to deploy"
  type        = number
  default     = 1
}
