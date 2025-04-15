#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import pytest
from conftest import (
    APP_NAME,
    BIND_PASSWORD_SECRET,
    CERTIFICATE_PROVIDER_APP,
    GLAUTH_APP,
    remove_integration,
)
from juju.application import Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
@pytest.mark.skip_if_deployed
async def test_build_and_deploy(
    ops_test: OpsTest,
    local_charm: Path,
    ldap_integrator_charm_config: dict,
) -> None:
    # Deploy dependencies
    await ops_test.model.deploy(
        GLAUTH_APP,
        application_name=GLAUTH_APP,
        channel="edge",
        trust=True,
    )
    await ops_test.model.deploy(
        CERTIFICATE_PROVIDER_APP,
        channel="latest/stable",
        trust=True,
    )
    await ops_test.model.integrate(GLAUTH_APP, CERTIFICATE_PROVIDER_APP)
    await ops_test.model.wait_for_idle(
        apps=[GLAUTH_APP],
        status="blocked",
        raise_on_blocked=False,
        timeout=60 * 10,
    )

    # Deploy ldap-integrator
    await ops_test.model.deploy(
        entity_url=str(local_charm),
        application_name=APP_NAME,
        config=ldap_integrator_charm_config,
        trust=True,
    )

    # Integrate with dependencies
    await ops_test.model.grant_secret(BIND_PASSWORD_SECRET, APP_NAME)
    await ops_test.model.integrate(APP_NAME, GLAUTH_APP)

    await asyncio.gather(
        ops_test.model.wait_for_idle(
            apps=[APP_NAME],
            status="active",
            raise_on_blocked=False,
            timeout=60 * 10,
        ),
        ops_test.model.wait_for_idle(
            apps=[GLAUTH_APP, CERTIFICATE_PROVIDER_APP],
            status="active",
            raise_on_blocked=False,
            raise_on_error=False,
            timeout=60 * 10,
        ),
    )


async def test_ldap_integration(
    ops_test: OpsTest,
    ldap_integrator_application: Application,
    ldap_integration_data: Optional[dict],
    ldap_integrator_charm_config: dict,
) -> None:
    assert ldap_integration_data

    secret = ldap_integration_data.pop("bind_password_secret", None)
    assert secret, "Bind password in integration databag should not be None"

    bind_password_databag = (
        await ops_test.model.list_secrets({"uri": secret}, show_secrets=True)
    )[0].value
    bind_password_config = (
        await ops_test.model.list_secrets(
            {"uri": ldap_integrator_charm_config["bind_password"]}, show_secrets=True
        )
    )[0].value
    assert bind_password_databag == bind_password_config

    assert ldap_integration_data == {
        "auth_method": ldap_integrator_charm_config["auth_method"],
        "base_dn": ldap_integrator_charm_config["base_dn"],
        "bind_dn": ldap_integrator_charm_config["bind_dn"],
        "starttls": ldap_integrator_charm_config["starttls"],
        "urls": json.dumps(ldap_integrator_charm_config["urls"].split(", ")),
        "ldaps_urls": json.dumps(ldap_integrator_charm_config["ldaps_urls"].split(", "))
    }


async def test_remove_ldap_integration(
    ops_test: OpsTest, ldap_integrator_application: Application
) -> None:
    async with remove_integration(ops_test, GLAUTH_APP, "ldap"):
        assert ldap_integrator_application.status == "blocked"
