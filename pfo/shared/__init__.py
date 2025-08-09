import os
import json
import subprocess

from halo import Halo

BASE = os.path.dirname(os.path.abspath(__file__))
_k8s_config_file = os.path.abspath(os.path.join(BASE, "..", "k8s", "k8s_config.json"))

# We're going to set out globals so that we can access the k8s config file easilys
with open(_k8s_config_file, "r") as f:
    k8s_config = json.load(f)

_tempdir = k8s_config.get("base", {}).get("tempdir", "/tmp/pyops")

if not os.path.exists(_tempdir):
    os.makedirs(_tempdir, exist_ok=True)

from . import etc
