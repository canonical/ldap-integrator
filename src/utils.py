# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
from typing import TYPE_CHECKING, Callable

from constants import LDAP_INTEGRATION_NAME

if TYPE_CHECKING:
    from charm import LdapIntegratorCharm


logger = logging.getLogger(__name__)

Condition = Callable[["LdapIntegratorCharm"], bool]


def integration_existence(integration_name: str) -> Condition:
    """A factory of integration existence condition."""

    def wrapped(charm: "LdapIntegratorCharm") -> bool:
        return bool(charm.model.relations[integration_name])

    return wrapped


ldap_integration_exists = integration_existence(LDAP_INTEGRATION_NAME)


def missing_config(charm: "LdapIntegratorCharm") -> set[str]:
    """Check whether the required configuration has been provided."""
    required_keys = {"urls", "base_dn", "bind_dn", "bind_password"}
    return {k for k in required_keys if not charm.config.get(k)}


def config_ready(charm: "LdapIntegratorCharm") -> bool:
    """Check whether the required configuration has been provided."""
    return not missing_config(charm)
