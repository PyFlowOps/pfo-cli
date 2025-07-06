#!/usr/bin/env bash
# This shell script takes the file path (absolute path) of the Helm values file as an argument.
# It installs the Traefik Helm chart in the specified namespace using the provided values file.
# Usage: ./traefik_install.sh /path/to/values.yaml

set -eou pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 /path/to/values.yaml"
  exit 1
fi

# We need to ensure that our required tools are installed before proceeding.
# Check if Helm and kubectl are installed
[[ -z $(command -v helm || true) ]] && { echo "Helm is not installed. Please install Helm first."; exit 1; }
[[ -z $(command -v kubectl || true) ]] && { echo "kubectl is not installed. Please install kubectl first."; exit 1; }

helm repo add traefik https://traefik.github.io/charts
helm repo update

# Install Traefik with the specified values
kubectl create namespace traefik || true
helm install traefik traefik/traefik \
  --namespace traefik \
  -f "${1}"
