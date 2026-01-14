#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm the application."""

import logging
from typing import Optional

import ops
from charms.glauth_k8s.v0.ldap import LdapProvider, LdapProviderData

from constants import CONFIG_PASSWORD_SECRET_KEY, LDAP_INTEGRATION_NAME
from utils import config_ready, missing_config

logger = logging.getLogger(__name__)


class LdapIntegratorCharm(ops.CharmBase):
    """Charm the application."""

    def __init__(self, framework: ops.Framework) -> None:
        super().__init__(framework)

        self.ldap = LdapProvider(self, LDAP_INTEGRATION_NAME)

        framework.observe(self.on.collect_unit_status, self._on_collect_status)
        framework.observe(self.on.start, self._holistic_handler)
        framework.observe(self.on.update_status, self._holistic_handler)
        framework.observe(self.ldap.on.ldap_requested, self._holistic_handler)

    def _holistic_handler(self, _: ops.EventBase) -> None:
        if not config_ready(self):
            return

        bind_password = self._get_bind_password()
        urls = self.config.get("urls").split(",")
        data = LdapProviderData(
            urls=[url for url in urls if url.startswith("ldap://")],
            ldaps_urls=[url for url in urls if url.startswith("ldaps://")],
            base_dn=self.config.get("base_dn"),
            starttls=self.config.get("starttls"),
            bind_dn=self.config.get("bind_dn"),
            bind_password=bind_password,
            auth_method="simple",
        )

        for integration in self.ldap.relations:
            self.ldap.update_relations_app_data(data, relation_id=integration.id)

    def _on_collect_status(self, event: ops.CollectStatusEvent) -> None:
        """The central management of the charm operator's status."""
        if missing := missing_config(self):
            event.add_status(ops.BlockedStatus(f"Missing required config: {', '.join(missing)}"))

        event.add_status(ops.ActiveStatus())

    def _get_bind_password(self) -> Optional[str]:
        secret_id = self.config["bind_password"]
        secret = self.model.get_secret(id=secret_id)
        return secret.get_content()[CONFIG_PASSWORD_SECRET_KEY]


if __name__ == "__main__":  # pragma: nocover
    ops.main(LdapIntegratorCharm)  # type: ignore
