#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import logging

import ops
from charms.glauth_k8s.v0.ldap import LdapProvider, LdapProviderData

from constants import LDAP_INTEGRATION_NAME
from utils import config_ready, ldap_integration_exists, missing_config

logger = logging.getLogger(__name__)


class LdapIntegratorCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)

        self.ldap = LdapProvider(self)

        framework.observe(self.on.collect_unit_status, self._on_collect_status)
        framework.observe(self.on.start, self._holistic_handler)
        framework.observe(self.on.update_status, self._holistic_handler)
        framework.observe(self.ldap.on.ldap_requested, self._holistic_handler)

    def _holistic_handler(self, event: ops.EventBase) -> None:
        if not ldap_integration_exists(self):
            return

        if not config_ready(self):
            return

        ldap_integration = self.model.relations[LDAP_INTEGRATION_NAME][0].id

        data = LdapProviderData(
            urls=self.config.get("urls").split(","),
            base_dn=self.config.get("base_dn"),
            starttls=self.config.get("starttls"),
            bind_dn=self.config.get("bind_dn"),
            bind_password=self.config.get("bind_password"),
            auth_method=self.config.get("auth_method"),
        )

        self.ldap.update_relations_app_data(
            data,
            relation_id=ldap_integration,
        )

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        """The central management of the charm operator's status."""
        if not ldap_integration_exists(self):
            event.add_status(ops.BlockedStatus(f"Missing integration {LDAP_INTEGRATION_NAME}"))

        if missing := missing_config(self):
            event.add_status(ops.BlockedStatus(f"Missing required config: {(', ').join(missing)}"))

        event.add_status(ops.ActiveStatus())


if __name__ == "__main__":  # pragma: nocover
    ops.main(LdapIntegratorCharm)  # type: ignore
