# Repository Management

This section documents how to manage your repositories with the `pfo CLI`.

## Invoke the Repo Command Group

**NOTE**: Since this command interacts with Github, you will need a Github Personal Access Token (PAT) set
in your environment as GH_TOKEN. You can still use the CLI but this application will be unavailable until a
valid GITHUB_TOKEN is added to the environment.

Please see

```bash
pfo repo
```

You will be presented with the menu - _subject to change_.

--init --> Creates a new repo, using the PyFlowOps repo template, complete with CI/CD, versioning, etc.
--set-github-environment --> Adds the environments in Github for the current repo, `dev`, `stg`, `prd`

--update --> Updates the Kubernetes _(Kind)_ cluster.
--info --> Returns info of the current cluster - `local`.
