# pfo CLI

![alt text](FullLogo_Transparent.png)

This is the PyFlowOps CLI _(pfo CLI)_. This CLI is designed to work within the PyFlowOps
ecosystem and will act as a liason between you, the developer, and the operations side
of the development lifecycle.

## Installation

```bash
curl -sSf https://raw.githubusercontent.com/PyFlowOps/pfo-cli/refs/heads/main/.install/install.sh | bash -l
```

## Doppler Setup

If you're running the free-tier of the Doppler SaaS Product, you will need to create a new config
in your organization project _(the project created in the Getting Started section of the PyFlowOps Documentation)_.
Since you are the owner of the account, your personal token will be enough to run the CLI.

If you are using the Teams or Enterprise Tier, then you will want to create a service account for connections to the
Doppler projects _(you will need access to create, change, add configs, etc.)_ This will give you another layer of
security through obfuscation as the service account token will only have access to read the config of the cli. The
config will have another Doppler token that has access to make all of the changes.

All third-party services that the CLI will interact with will have their API keys, etc. stored in the 
config for the CLI.

## Development

Please see the `README.md` in the `@pyflowops/pfo-cli` repo.

## Commands

The command documentation for the `pfo CLI`.

### [repo](./commands/repo.md)

### [k8s](./commands/k8s.md)

### [package](./commands/package.md)
