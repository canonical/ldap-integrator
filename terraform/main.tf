# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

/**
 * # Terraform module for the ldap-integrator charm
 *
 * This is a Terraform module facilitating the deployment of the ldap-integrator
 * charm using the Juju Terraform provider.
 */

resource "juju_application" "ldap_integrator" {
  name        = var.app_name
  model_uuid  = var.model_uuid
  config      = var.config
  constraints = var.constraints
  units       = var.units

  charm {
    name     = "ldap-integrator"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }
}
