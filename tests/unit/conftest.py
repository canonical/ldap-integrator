# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import MagicMock

import pytest
from ops import testing
from pytest_mock import MockerFixture

from charm import LdapIntegratorCharm
from constants import LDAP_INTEGRATION_NAME


@pytest.fixture
def charm_configuration(password_secret: testing.Secret, starttls: bool) -> dict:
    config = {
        "urls": "ldap://ldap.com/path/to/somewhere",
        "ldaps_urls": "ldaps://ldap.com/path/to/somewhere",
        "base_dn": "dc=glauth,dc=com",
        "starttls": starttls,
        "bind_dn": "cn=user,ou=group,dc=glauth,dc=com",
        "bind_password": password_secret.id,
        "auth_method": "simple",
    }
    return config


@pytest.fixture
def ctx() -> testing.Context[LdapIntegratorCharm]:
    return testing.Context(LdapIntegratorCharm)


@pytest.fixture
def ldap_integration() -> testing.Relation:
    return testing.Relation(endpoint=LDAP_INTEGRATION_NAME, remote_app_name="ldap")


@pytest.fixture
def mock_ldap_provider(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("charm.LdapProvider.update_relations_app_data")


@pytest.fixture
def password_secret() -> testing.Secret:
    return testing.Secret(tracked_content={"password": "bind_password"})


@pytest.fixture(params=[True, False], ids=["starttls enabled", "starttls not enabled"])
def starttls(request: pytest.FixtureRequest) -> bool:
    return request.param
