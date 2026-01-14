#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import json
from pathlib import Path

import jubilant
import pytest
from tenacity import Retrying, stop_after_attempt, wait_exponential

# isort: off
from constants import APP_NAME, BIND_PASSWORD_SECRET, CERTIFICATE_PROVIDER_APP, GLAUTH_APP
from helpers import get_integration_data, remove_integration

pytestmark = pytest.mark.k8s


def test_build_and_deploy(
    integrator_model: jubilant.Juju,
    local_charm: Path,
    integrator_config: dict,
) -> None:
    # Deploy dependencies
    integrator_model.deploy(
        GLAUTH_APP,
        app=GLAUTH_APP,
        channel="latest/edge",
        trust=True,
    )
    integrator_model.deploy(
        CERTIFICATE_PROVIDER_APP,
        channel="latest/stable",
        trust=True,
    )
    integrator_model.integrate(GLAUTH_APP, CERTIFICATE_PROVIDER_APP)
    integrator_model.wait(lambda status: jubilant.all_blocked(status, GLAUTH_APP))

    # Deploy ldap-integrator
    integrator_model.deploy(
        local_charm,
        app=APP_NAME,
        config=integrator_config,
        trust=True,
    )
    integrator_model.grant_secret(BIND_PASSWORD_SECRET, APP_NAME)
    integrator_model.integrate(APP_NAME, GLAUTH_APP)
    integrator_model.wait(jubilant.all_active, error=jubilant.any_error)


def test_ldap_integration(
    integrator_model: jubilant.Juju,
    integrator_config: dict,
) -> None:
    ldap_integration_data = get_integration_data(
        integrator_model, app=GLAUTH_APP, endpoint="ldap-client"
    )
    assert ldap_integration_data

    secret = ldap_integration_data.pop("bind_password_secret", None)
    assert secret, "Bind password in integration databag should not be None"
    bind_password_databag = integrator_model.show_secret(secret, reveal=True)
    bind_password_integrator_config = integrator_model.show_secret(
        integrator_config["bind_password"], reveal=True
    )
    assert (
        bind_password_databag.content["password"]
        == bind_password_integrator_config.content["password"]
    )

    urls = integrator_config["urls"].split(",")
    assert ldap_integration_data == {
        "auth_method": "simple",
        "base_dn": integrator_config["base_dn"],
        "bind_dn": integrator_config["bind_dn"],
        "starttls": integrator_config["starttls"],
        "urls": json.dumps([url for url in urls if url.startswith("ldap://")]),
        "ldaps_urls": json.dumps([url for url in urls if url.startswith("ldaps://")]),
    }


def test_remove_ldap_integration(integrator_model: jubilant.Juju) -> None:
    with remove_integration(integrator_model, GLAUTH_APP, "ldap"):
        for attempt in Retrying(
            wait=wait_exponential(multiplier=2, min=1, max=30),
            stop=stop_after_attempt(10),
            reraise=True,
        ):
            with attempt:
                assert (
                    get_integration_data(integrator_model, app=GLAUTH_APP, endpoint="ldap-client")
                    is None
                )
