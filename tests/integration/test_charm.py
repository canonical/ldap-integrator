#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import json
import logging
from typing import Dict

import pytest
from conftest import (
    APP_NAME,
    CERTIFICATE_PROVIDER_APP,
    GLAUTH_APP,
    get_app_integration_data,
    remove_integration,
)
from juju.application import Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
@pytest.mark.skip_if_deployed
async def test_build_and_deploy(ops_test: OpsTest) -> None:
    charm = await ops_test.build_charm(".")

    await asyncio.gather(
        ops_test.model.deploy(
            charm,
            application_name=APP_NAME,
            trust=True,
        ),
        ops_test.model.deploy(
            GLAUTH_APP,
            application_name=GLAUTH_APP,
            channel="edge",
            trust=True,
        ),
        ops_test.model.deploy(
            CERTIFICATE_PROVIDER_APP,
            channel="stable",
            trust=True,
        ),
    )
    await ops_test.model.integrate(GLAUTH_APP, CERTIFICATE_PROVIDER_APP)

    await ops_test.model.wait_for_idle(
        apps=[APP_NAME], status="blocked", raise_on_blocked=False, timeout=1000
    )


async def test_ldap_integration(
    ops_test: OpsTest, ldap_integrator_application: Application, ldap_integrator_charm_config: Dict
) -> None:
    await ldap_integrator_application.set_config(ldap_integrator_charm_config)
    await ops_test.model.integrate(GLAUTH_APP, APP_NAME)

    await ops_test.model.wait_for_idle(
        apps=[APP_NAME, GLAUTH_APP], status="active", raise_on_blocked=False, timeout=1000
    )

    data = await get_app_integration_data(ops_test, GLAUTH_APP, "ldap-client")

    secret = data.pop("bind_password_secret", None)
    assert secret
    bind_password_databag = (
        await ops_test.model.list_secrets({"uri": secret}, show_secrets=True)
    )[0].value
    bind_password_config = (
        await ops_test.model.list_secrets(
            {"uri": ldap_integrator_charm_config["bind_password"]}, show_secrets=True
        )
    )[0].value
    assert bind_password_databag == bind_password_config
    assert data == {
        "auth_method": ldap_integrator_charm_config["auth_method"],
        "base_dn": ldap_integrator_charm_config["base_dn"],
        "bind_dn": ldap_integrator_charm_config["bind_dn"],
        "starttls": ldap_integrator_charm_config["starttls"],
        "urls": json.dumps(ldap_integrator_charm_config["urls"].split(", ")),
    }


@pytest.mark.skip_if_deployed
async def test_remove_ldap_integration(
    ops_test: OpsTest, ldap_integrator_application: Application
) -> None:
    async with remove_integration(ops_test, GLAUTH_APP, "ldap"):
        assert ldap_integrator_application.status == "blocked"
