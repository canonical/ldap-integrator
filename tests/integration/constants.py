# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import os
from pathlib import Path

import yaml

# in GitHub CI, charms are built with charmcraftcache and uploaded to $CHARM_PATH
CHARM_PATH = Path(charm) if (charm := os.getenv("CHARM_PATH")) else None
METADATA = yaml.safe_load(Path("./charmcraft.yaml").read_text())
APP_NAME = METADATA["name"]
GLAUTH_APP = "glauth-k8s"
CERTIFICATE_PROVIDER_APP = "self-signed-certificates"
BIND_PASSWORD_SECRET = "password"
