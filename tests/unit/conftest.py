# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Dict, Generator
from unittest.mock import MagicMock, create_autospec

import pytest
from ops import EventBase
from ops.testing import Harness
from pytest_mock import MockerFixture

from charm import LdapIntegratorCharm
from constants import LDAP_INTEGRATION_NAME


@pytest.fixture
def harness() -> Generator[Harness, None, None]:
    harness = Harness(LdapIntegratorCharm)
    harness.set_model_name("unit-test")
    harness.set_leader(True)

    harness.begin_with_initial_hooks()
    yield harness
    harness.cleanup()


@pytest.fixture
def mocked_event() -> MagicMock:
    return create_autospec(EventBase)


@pytest.fixture
def charm_configuration(harness: Harness) -> Dict:
    config = {
        "urls": "ldap://ldap.com/path/to/somewhere",
        "base_dn": "dc=glauth,dc=com",
        "starttls": True,
        "bind_dn": "cn=user,ou=group,dc=glauth,dc=com",
        "bind_password": "password",
        "auth_method": "simple",
    }
    harness.update_config(config)
    return config


@pytest.fixture
def ldap_integration(harness: Harness) -> int:
    return harness.add_relation(LDAP_INTEGRATION_NAME, "ldap")


@pytest.fixture
def ldap_integration_data(harness: Harness, ldap_integration: int) -> None:
    harness.update_relation_data(
        ldap_integration,
        "ldap",
        {
            "user": "user",
            "group": "group",
        },
    )


@pytest.fixture
def all_satisfied_conditions(mocker: MockerFixture) -> None:
    mocker.patch("charm.ldap_integration_exists", return_value=True)
