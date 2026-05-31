# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

output "application" {
  description = "The deployed juju_application resource"
  value       = juju_application.ldap_integrator
}

output "provides" {
  description = "Map of provides endpoint names"
  value = {
    ldap = "ldap"
  }
}
