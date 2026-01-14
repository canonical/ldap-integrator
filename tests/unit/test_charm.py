# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

from unittest.mock import MagicMock

import ops
from charms.glauth_k8s.v0.ldap import LdapProviderData
from ops import testing

from charm import LdapIntegratorCharm


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
        mock_ldap_provider: MagicMock,
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

        expected_urls = charm_configuration["urls"].split(",")
        expected = LdapProviderData(
            urls=[url for url in expected_urls if url.startswith("ldap://")],
            ldaps_urls=[url for url in expected_urls if url.startswith("ldaps://")],
            base_dn=charm_configuration["base_dn"],
            starttls=charm_configuration["starttls"],
            bind_dn=charm_configuration["bind_dn"],
            bind_password=password_secret.tracked_content["password"],
            auth_method="simple",
        )
        assert isinstance(state.unit_status, ops.ActiveStatus)
        mock_ldap_provider.assert_called_once_with(expected, relation_id=ldap_integration.id)


class TestCollectStatusEvent:
    def test_when_all_condition_satisfied(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
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

    def test_when_ldap_integration_exists_with_no_config(
        self,
        ctx: testing.Context[LdapIntegratorCharm],
    ) -> None:
        state = ctx.run(ctx.on.collect_unit_status(), state=testing.State(leader=True))

        assert isinstance(state.unit_status, ops.BlockedStatus)
