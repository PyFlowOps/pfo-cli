# Package

This section helps manage the repo utilizing the `pfo CLI`.

## Invoke the Package Command Group

**NOTE**: If this repo is not managed by the `pfo.json`, you will be presented with a warning and the command to register the repo with the `pfo.json`.

```bash
pfo package
```

You will be presented with the menu - _subject to change_.

### Registration
--register --> Creates the `pfo.json` file with pertinent information needed to manage the repo.
--deregister --> Removes the `pfo.json` file, and deregisters the repo from management - versioning, GHA, etc.

### Versioning
--version --> Returns the current version that is in the `pfo.json` file.
--major --> Increments the major version.
--minor --> Increments the minor version.
--patch --> Increments the patch version.
