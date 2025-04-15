# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Dict, Tuple
from unittest.mock import MagicMock

import pytest
from charms.glauth_k8s.v0.ldap import LdapProviderData
from ops import ActiveStatus, BlockedStatus, StatusBase
from ops.testing import Harness
from pytest_mock import MockerFixture

from constants import LDAP_INTEGRATION_NAME


class TestHolisticHandler:
    def test_when_no_ldap_integration_exists(
        self,
        harness: Harness,
        mocker: MockerFixture,
        mocked_event: MagicMock,
    ) -> None:
        mocked_provider = mocker.patch("charm.LdapProvider.update_relations_app_data")

        harness.charm._holistic_handler(mocked_event)

        mocked_provider.assert_not_called()

    def test_when_ldap_integration_exists_with_no_config(
        self,
        harness: Harness,
        mocker: MockerFixture,
        mocked_event: MagicMock,
        all_satisfied_conditions: MagicMock,
        ldap_integration: int,
    ) -> None:
        mocked_provider = mocker.patch("charm.LdapProvider.update_relations_app_data")

        harness.charm._holistic_handler(mocked_event)

        mocked_provider.assert_not_called()

    def test_when_ready(
        self,
        harness: Harness,
        mocker: MockerFixture,
        mocked_event: MagicMock,
        all_satisfied_conditions: MagicMock,
        ldap_integration: int,
        charm_configuration: Dict,
        password_secret: Tuple[str, str],
    ) -> None:
        mocked_provider = mocker.patch("charm.LdapProvider.update_relations_app_data")

        harness.charm._holistic_handler(mocked_event)

        expected = LdapProviderData(
            urls=charm_configuration["urls"].split(","),
            ldaps_urls=charm_configuration["ldaps_urls"].split(","),
            base_dn=charm_configuration["base_dn"],
            starttls=charm_configuration["starttls"],
            bind_dn=charm_configuration["bind_dn"],
            bind_password=password_secret[0],
            auth_method=charm_configuration["auth_method"],
        )
        mocked_provider.assert_called_once_with(expected, relation_id=ldap_integration)


class TestCollectStatusEvent:
    def test_when_all_condition_satisfied(
        self,
        harness: Harness,
        all_satisfied_conditions: MagicMock,
        charm_configuration: Dict,
    ) -> None:
        harness.evaluate_status()

        assert isinstance(harness.model.unit.status, ActiveStatus)

    @pytest.mark.parametrize(
        "condition, status, message",
        [
            (
                "ldap_integration_exists",
                BlockedStatus,
                f"Missing integration {LDAP_INTEGRATION_NAME}",
            ),
        ],
    )
    def test_when_a_condition_failed(
        self,
        harness: Harness,
        mocker: MockerFixture,
        condition: str,
        status: StatusBase,
        message: str,
    ) -> None:
        mocker.patch(f"charm.{condition}", return_value=False)
        harness.evaluate_status()

        assert isinstance(harness.model.unit.status, status)
        assert harness.model.unit.status.message == message

    def test_when_ldap_integration_exists_with_no_config(
        self,
        harness: Harness,
        mocked_event: MagicMock,
        all_satisfied_conditions: MagicMock,
    ) -> None:
        harness.evaluate_status()

        assert isinstance(harness.model.unit.status, BlockedStatus)
