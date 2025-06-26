# Repository Management

This section documents how to manage your repository with PyFlowOps.

## Invoke the Repository Command Group

```bash
pfo repo

```

You will be presented with the menu - _subject to change_.

--create --> Creates a new repository.
--delete --> Deletes an existing repository.
--list --> Lists all repositories.
--update --> Updates the repository information.
--info --> Returns info of the current repository.

### Create a New Repository with pfo

The below command will create a new repository, and initialize it with PyFlowOps.

```bash
pfo repo --create
```

You can then add your code to the repository by running `git init` in the project directory.

Example: `git init`
