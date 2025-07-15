import os
import json
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
_k8s_config_file = os.path.join(BASE, "k8s_config.json")

# We're going to set out globals so that we can access the k8s config file easilys
with open(_k8s_config_file, "r") as f:
    k8s_config = json.load(f)

import k8s.traefik as traefik

from pfo import argocd
