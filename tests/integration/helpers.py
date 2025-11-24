# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

import jubilant
import pytest
import yaml
from tenacity import retry, stop_after_attempt, wait_exponential

from constants import APP_NAME


def build_charm() -> Path:
    """Build the charm located at the repository root.

    Raises:
        subprocess.CalledProcessError: Raised if the charm fails to build.
        FileNotFoundError: Raised if the built `*.charm` file cannot be located.
    """
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        ["charmcraft", "-v", "pack"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    charm = list(root.glob("ldap-integrator*.charm"))[0]
    charm = charm.rename("ldap-integrator.charm")
    return charm.absolute()


def create_temp_juju_model(
    request: pytest.FixtureRequest, *, model: str = ""
) -> Iterator[jubilant.Juju]:
    """Create a temporary Juju model."""
    keep_models = bool(request.config.getoption("--keep-models"))

    with jubilant.temp_model(keep=keep_models) as juju:
        # Hack to get around `jubilant.temp_model` not accepting a custom model name
        if model:
            # Destroy `jubilant-*` model
            juju.destroy_model(juju.model, destroy_storage=True, force=True)

            # `CLIError` will be emitted if `--model` already exists so silently ignore
            # error and set the `model` attribute to the value of model.
            try:
                juju.add_model(model)
            except jubilant.CLIError:
                juju.model = model

        juju.wait_timeout = 10 * 60

        yield juju

        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")


def get_integration_data(
    juju: jubilant.Juju,
    /,
    app: str,
    endpoint: str,
    unit_num: int = 0,
    target: Literal["app", "unit"] = "app",
) -> dict | None:
    """Get integration data using `juju show-unit`."""
    unit = f"{app}/{unit_num}"
    stdout = juju.cli("show-unit", unit)
    result = yaml.safe_load(stdout)
    data = next(
        (
            integration
            for integration in result[unit]["relation-info"]
            if integration["endpoint"] == endpoint
        )
    )

    match target:
        case "app":
            return data["application-data"] if data else None
        case "unit":
            return data["related-units"][unit]["data"] if data else None
        case _:
            raise ValueError(f"Expected 'app' or 'unit', not {target}")


@contextmanager
def remove_integration(
    juju: jubilant.Juju, /, remote_app_name: str, integration_name: str
) -> Iterator[None]:
    """Temporarily remove an integration from the `ldap-integrator` application.

    Integration is restored after the context is exited.
    """

    # The pre-existing integration instance can still be "dying" when the `finally` block
    # is called, so `tenacity.retry` is used here to capture the `jubilant.CLIError`
    # and re-run `juju integrate ...` until the previous integration instance has finished dying.
    @retry(
        wait=wait_exponential(multiplier=2, min=1, max=30),
        stop=stop_after_attempt(10),
        reraise=True,
    )
    def _reintegrate() -> None:
        juju.integrate(f"{APP_NAME}:{integration_name}", remote_app_name)

    juju.remove_relation(f"{APP_NAME}:{integration_name}", remote_app_name)
    juju.wait(lambda status: jubilant.all_active(status, remote_app_name))
    try:
        yield
    finally:
        _reintegrate()
        juju.wait(lambda status: jubilant.all_active(status, APP_NAME, remote_app_name))
