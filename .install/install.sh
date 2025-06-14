#!/usr/bin/env bash
# This file should not need to change
# Please use EXTREME CAUTION when modifying this file.
# This script is used to install the CLI tool and its dependencies.

#set -euo pipefail

OS=$(uname)
PFO_BASE=${HOME}/.pfo
K8S_LOCAL=${PFO_BASE}/k8s
PFO_ORG_REPO="PyFlowOps/k8s-installs"
PFO_K8S_SCRIPTS_LOCATION="refs/heads/main/deploy"

# Let's exit out of the installation immediately if the OS is not supported.
[[ "${OS}" != "Darwin" ]] && echo "Current OS is Mac only, your OS is not supported. Our apologies for the inconveinience." && exit 0

function prereqs() {
  [[ ! -d ${PFO_BASE} ]] && mkdir ${PFO_BASE} # We need this directory to install some SHELL completions later.
  [[ ! -d ${K8S_LOCAL} ]] && mkdir -p ${K8S_LOCAL} # We need this directory to install some SHELL completions later.

  [[ -z "$(command -v python3)" ]] && brew install python3
  [[ -z "$(command -v gh)" ]] && brew install gh
  [[ -z "$(command -v jq)" ]] && brew install jq
  [[ -z "$(command -v pipx)" ]] && brew install pipx
  [[ -z "$(command -v git )" ]] && brew install git
  [[ -z "$(command -v kubectl)" ]] && brew install kubernetes-cli
  [[ -z "$(command -v kustomize)" ]] && brew install kustomize
  [[ -z "$(command -v helm)" ]] && brew install helm
  [[ -z "$(command -v kind)" ]] && brew install kind
  [[ -z "$(command -v minikube)" ]] && brew install minikube
  [[ -z "$(command -v argocd)" ]] && brew install argocd
}

function k8s_scripts() {
  [[ ! -d ${K8S_LOCAL} ]] && {
    mkdir -p ${K8S_LOCAL} # We need this directory to install some SHELL completions later.
  } || {
    rm -rf ${K8S_LOCAL}/*
  }
  # We need to download the scripts from the k8s-installs repository.
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/create_cluster.sh -o ${K8S_LOCAL}/create_cluster.sh
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/kind-config.yaml -o ${K8S_LOCAL}/kind-config.yaml
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/delete_all_clusters.sh -o ${K8S_LOCAL}/delete_all_clusters.sh
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/delete_local_cluster.sh -o ${K8S_LOCAL}/delete_local_cluster.sh
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/augment_config_file.sh -o ${K8S_LOCAL}/augment_config_file.sh
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/start_cluster.sh -o ${K8S_LOCAL}/start_cluster.sh
  curl https://raw.githubusercontent.com/${PFO_ORG_REPO}/${PFO_K8S_SCRIPTS_LOCATION}/update_cluster.sh -o ${K8S_LOCAL}/update_cluster.sh
}

function cleanup() {
  unset _PYTHON
  unset OS
  unset PFO_BASE
  unset K8S_LOCAL
  unset PFO_ORG_REPO
  unset PFO_K8S_SCRIPTS_LOCATION
  unset _CLI_LATEST
}

echo "[INFO] - Installing the pfo-cli tool prerequisites..."
prereqs > /dev/null 2>&1 # We don't want to see the output of this function.
echo "[INFO] - All prerequisites have been installed successfully."

echo "[INFO] - Downloading the k8s scripts..."
k8s_scripts > /dev/null 2>&1 # We don't want to see the output of this function.
echo "[INFO] - All k8s scripts have been downloaded successfully."

if [[ $(gh api /repos/PyFlowOps/pfo-cli/releases/latest | jq -r '.message') == *"Not Found"* ]]; then
  echo '[WARNING] - We cannot find a release for the pfo-cli...'
  echo '[ERROR] - Please ensure that the "PyFlowOps/pfo-cli" repository exists and is accessible.'
  exit 1
fi

_CLI_LATEST=$(gh api /repos/PyFlowOps/pfo-cli/releases/latest | jq -r '.tag_name')

pipx install git+https://github.com/PyFlowOps/pfo-cli.git@${_CLI_LATEST} --force

cleanup
echo "[INFO] - The pfo-cli tool has been installed successfully."
