# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "The name of the deployed application"
  value       = juju_application.ldap_integrator.name
}

output "provides" {
  description = "The Juju integrations that the charm provides"
  value = {
    ldap = "ldap"
  }
}
