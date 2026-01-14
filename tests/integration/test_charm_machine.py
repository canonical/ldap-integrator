#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Test `ldap-integrator` on machine clouds."""

from pathlib import Path

import jubilant
import pytest

from constants import (
    APP_NAME,
    BIND_PASSWORD_SECRET,
    LDAP_SERVER_CLOUD_INIT,
    OPENLDAP_APP,
    SSSD_APP,
    UBUNTU_APP,
)

pytestmark = pytest.mark.machine


def test_build_and_deploy(
    integrator_model: jubilant.Juju,
    server_model: jubilant.Juju,
    local_charm: Path,
    bind_password_secret: jubilant.SecretURI,
) -> None:
    # Deploy dependencies.
    integrator_model.deploy(
        UBUNTU_APP,
        base="ubuntu@24.04",
    )
    integrator_model.deploy(
        SSSD_APP,
        base="ubuntu@24.04",
        channel="latest/edge",
    )
    integrator_model.integrate(f"{SSSD_APP}:juju-info", f"{UBUNTU_APP}:juju-info")

    # Deploy "external" OpenLDAP server.
    # cloud-init plan seeds a minimal OpenLDAP server with a single user named `nucci`.
    server_model.model_config({"cloudinit-userdata": LDAP_SERVER_CLOUD_INIT})
    server_model.deploy(
        UBUNTU_APP,
        OPENLDAP_APP,
        base="ubuntu@24.04",
    )

    # Wait for "external" LDAP server to become active.
    server_model.wait(lambda status: jubilant.all_active(status, OPENLDAP_APP))
    # Ensure that cloud-init has finished initializing the LDAP server.
    try:
        server_model.exec("cloud-init status --wait", unit=f"{OPENLDAP_APP}/0")
    except jubilant.TaskError as e:
        # cloud-init does not like the `apt_mirror` option added by Juju to new instances,
        # but it does not cause cloud-init to fail, so `cloud-init status --wait` returns
        # exit code 2 "Recoverable error - Cloud-init completed but experienced errors".
        assert e.task.return_code == 2

    # Deploy ldap-integrator.
    server_address = (
        server_model.status().apps[OPENLDAP_APP].units[f"{OPENLDAP_APP}/0"].public_address
    )
    integrator_model.deploy(
        local_charm,
        APP_NAME,
        config={
            "urls": f"ldap://{server_address},ldaps://{server_address}",
            "base_dn": "dc=test,dc=ubuntu,dc=com",
            "starttls": False,
            "bind_dn": "cn=admin,dc=test,dc=ubuntu,dc=com",
            "bind_password": bind_password_secret,
        },
    )
    integrator_model.grant_secret(BIND_PASSWORD_SECRET, APP_NAME)
    integrator_model.integrate(f"{APP_NAME}:ldap", f"{SSSD_APP}:ldap")

    # Ensure ldap-integrator and sssd are active.
    integrator_model.wait(jubilant.all_active, error=jubilant.any_error)


def test_sssd_connection(integrator_model: jubilant.Juju) -> None:
    result = integrator_model.exec("getent passwd nucci", unit=f"{UBUNTU_APP}/0")
    assert result.return_code == 0


def test_multi_sssd_connection(integrator_model: jubilant.Juju) -> None:
    # Deploy second SSSD application.
    ubuntu_secondary = f"{UBUNTU_APP}-secondary"
    sssd_secondary = f"{SSSD_APP}-secondary"
    integrator_model.deploy(
        UBUNTU_APP,
        ubuntu_secondary,
        base="ubuntu@24.04",
    )
    integrator_model.deploy(
        SSSD_APP,
        sssd_secondary,
        base="ubuntu@24.04",
        channel="latest/edge",
    )
    integrator_model.integrate(f"{sssd_secondary}:juju-info", f"{ubuntu_secondary}:juju-info")
    integrator_model.integrate(f"{APP_NAME}:ldap", f"{sssd_secondary}:ldap")

    # Ensure ldap-integrator and sssd-secondary are active.
    integrator_model.wait(jubilant.all_active, error=jubilant.any_error)

    # Test that secondary ubuntu application can query the remote user.
    result = integrator_model.exec("getent passwd nucci", unit=f"{ubuntu_secondary}/0")
    assert result.return_code == 0
