# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

import logging
import os
import subprocess
from collections.abc import Iterable, Iterator
from itertools import product
from pathlib import Path

import jubilant
import pytest

# isort: off
from constants import BIND_PASSWORD_SECRET, BIND_PASSWORD
from helpers import build_charm, create_temp_juju_model

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


@pytest.fixture(scope="session")
def server_model(request: pytest.FixtureRequest) -> Iterator[jubilant.Juju]:
    yield from create_temp_juju_model(request)


@pytest.fixture
def bind_password_secret(integrator_model: jubilant.Juju) -> jubilant.SecretURI:
    secrets = [s for s in integrator_model.secrets() if s.name == BIND_PASSWORD_SECRET]
    if not secrets:
        password = integrator_model.add_secret(
            BIND_PASSWORD_SECRET, content={"password": BIND_PASSWORD}
        )
    else:
        password = secrets[0].uri

    return password


@pytest.fixture
def integrator_config(bind_password_secret: jubilant.SecretURI) -> dict:
    return {
        "urls": "ldap://ldap.com/path/to/somewhere,ldaps://ldap.com/path/to/somewhere",
        "base_dn": "dc=glauth,dc=com",
        "starttls": "True",
        "bind_dn": "cn=user,ou=group,dc=glauth,dc=com",
        "bind_password": bind_password_secret,
        "auth_method": "simple",
    }


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "k8s: integration tests to run on a k8s cloud")
    config.addinivalue_line("markers", "machine: integration tests to run on a machine cloud")


def pytest_collection_modifyitems(config: pytest.Config, items: Iterable[pytest.Item]) -> None:
    enable = set()
    run_k8s = config.getoption("--run-k8s")
    run_machine = config.getoption("--run-machine")

    if run_k8s and run_machine:
        pytest.exit(
            "Cannot run both k8s and machine cloud integration tests at the same time. "
            + "Choose only one set of tests to run with either `--run-k8s` or `--run-machine`"
        )
    elif run_k8s:
        enable.add("k8s")
    elif run_machine:
        enable.add("machine")
    else:
        # Run k8s cloud integration tests by default.
        enable.add("k8s")

    for enabled, item in product(enable, items):
        if enabled not in item.keywords:
            item.add_marker(pytest.mark.skip)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--keep-models",
        action="store_true",
        default=False,
        help="keep temporarily created models",
    )
    parser.addoption(
        "--model",
        action="store",
        default="",
        help="Juju model to use; if not provided, a new model "
        "will be created for each test which requires one",
    )
    parser.addoption(
        "--run-k8s",
        action="store_true",
        default=False,
        help="run k8s cloud tests for ldap-integrator",
    )
    parser.addoption(
        "--run-machine",
        action="store_true",
        default=False,
        help="run machine cloud tests for ldap-integrator",
    )
