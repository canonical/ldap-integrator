# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path

import jubilant
import pytest
from helpers import build_charm, create_temp_juju_model

from constants import BIND_PASSWORD_SECRET

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def local_charm() -> Path:
    # in GitHub CI, charms are built with charmcraftcache and uploaded to $CHARM_PATH
    charm = Path(charm) if (charm := os.getenv("CHARM_PATH")) else None
    if not charm:
        # fall back to build locally - required when run outside of GitHub CI
        logger.info("building local `ldap-integrator` charm from repository")
        try:
            charm = build_charm()
            logger.info("built local `ldap-integrator` charm at %s", charm)
            return charm
        except subprocess.CalledProcessError as e:
            logger.error("failed to build charm: %s", e.stdout if hasattr(e, "stdout") else e)
            raise
        except FileNotFoundError as e:
            logger.error("failed to move charm: %s", e)
            raise

    logger.info("using local `ldap-integrator` charm located at %s", charm)
    return charm.absolute()


@pytest.fixture(scope="session")
def integrator_model(request: pytest.FixtureRequest) -> Iterator[jubilant.Juju]:
    model = str(request.config.getoption("--model"))
    yield from create_temp_juju_model(request, model=model)


@pytest.fixture
def integrator_config(integrator_model: jubilant.Juju) -> dict:
    secrets = [s for s in integrator_model.secrets() if s.name == BIND_PASSWORD_SECRET]
    if not secrets:
        password = integrator_model.add_secret(
            BIND_PASSWORD_SECRET, content={"password": "secret"}
        )
    else:
        password = secrets[0].uri

    return {
        "urls": "ldap://ldap.com/path/to/somewhere",
        "ldaps_urls": "ldaps://ldap.com/path/to/somewhere",
        "base_dn": "dc=glauth,dc=com",
        "starttls": "True",
        "bind_dn": "cn=user,ou=group,dc=glauth,dc=com",
        "bind_password": password,
        "auth_method": "simple",
    }


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--model",
        action="store",
        default="",
        help="Juju model to use; if not provided, a new model "
        "will be created for each test which requires one",
    )
    parser.addoption(
        "--keep-models",
        action="store_true",
        default=False,
        help="keep temporarily created models",
    )
