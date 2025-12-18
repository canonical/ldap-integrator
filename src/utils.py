# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from charm import LdapIntegratorCharm


def missing_config(charm: "LdapIntegratorCharm") -> set[str]:
    """Check whether the required configuration has been provided."""
    required_keys = {"urls", "base_dn", "bind_dn", "bind_password"}
    return {k for k in required_keys if not charm.config.get(k)}


def config_ready(charm: "LdapIntegratorCharm") -> bool:
    """Check whether the required configuration has been provided."""
    return not missing_config(charm)
