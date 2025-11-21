# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import MagicMock

import ops
import pytest
from charms.glauth_k8s.v0.ldap import LdapProviderData
from ops import testing
from pytest_mock import MockerFixture

from charm import LdapIntegratorCharm
from constants import LDAP_INTEGRATION_NAME


class TestHolisticHandler:
    def test_when_no_ldap_integration_exists(
        self, ctx: testing.Context[LdapIntegratorCharm], mock_ldap_provider: MagicMock
    ) -> None:
        ctx.run(ctx.on.start(), state=testing.State(leader=True))

        mock_ldap_provider.assert_not_called()

    def test_when_ldap_integration_exists_with_no_config(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
        mock_ldap_provider: MagicMock,
        all_satisfied_conditions: None,
        ldap_integration: testing.Relation,
    ) -> None:
        state = ctx.run(
            ctx.on.relation_changed(ldap_integration),
            state=testing.State(leader=True, relations={ldap_integration}),
        )

        assert isinstance(state.unit_status, ops.BlockedStatus)
        mock_ldap_provider.assert_not_called()

    def test_when_ready(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
        mocker: MockerFixture,
        mock_ldap_provider: MagicMock,
        all_satisfied_conditions: None,
        ldap_integration: testing.Relation,
        charm_configuration: dict,
        password_secret: testing.Secret,
    ) -> None:
        state = ctx.run(
            ctx.on.relation_changed(ldap_integration),
            state=testing.State(
                leader=True,
                config=charm_configuration,
                relations={ldap_integration},
                secrets={password_secret},
            ),
        )

        expected = LdapProviderData(
            urls=charm_configuration["urls"].split(","),
            ldaps_urls=charm_configuration["ldaps_urls"].split(","),
            base_dn=charm_configuration["base_dn"],
            starttls=charm_configuration["starttls"],
            bind_dn=charm_configuration["bind_dn"],
            bind_password=password_secret.tracked_content["password"],
            auth_method=charm_configuration["auth_method"],
        )
        assert isinstance(state.unit_status, ops.ActiveStatus)
        mock_ldap_provider.assert_called_once_with(expected, relation_id=ldap_integration.id)


class TestCollectStatusEvent:
    def test_when_all_condition_satisfied(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
        all_satisfied_conditions: None,
        charm_configuration: dict,
        password_secret: testing.Secret,
    ) -> None:
        state = ctx.run(
            ctx.on.collect_unit_status(),
            state=testing.State(
                leader=True, config=charm_configuration, secrets={password_secret}
            ),
        )

        assert isinstance(state.unit_status, ops.ActiveStatus)

    @pytest.mark.parametrize(
        "condition, status, message",
        [
            (
                "ldap_integration_exists",
                ops.BlockedStatus,
                f"Missing integration {LDAP_INTEGRATION_NAME}",
            ),
        ],
    )
    def test_when_a_condition_failed(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
        mocker: MockerFixture,
        condition: str,
        status: ops.StatusBase,
        message: str,
    ) -> None:
        mocker.patch(f"charm.{condition}", return_value=False)

        state = ctx.run(ctx.on.collect_unit_status(), state=testing.State(leader=True))

        # Static type checker complains about `ops.StatusBase` being incompatible with the
        # signature of `instance`, so we use tuple[ops.StatusBase] here to make it happy.
        assert isinstance(state.unit_status, (status,))
        assert state.unit_status.message == message

    def test_when_ldap_integration_exists_with_no_config(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
        all_satisfied_conditions: None,
    ) -> None:
        state = ctx.run(ctx.on.collect_unit_status(), state=testing.State(leader=True))

        assert isinstance(state.unit_status, ops.BlockedStatus)
