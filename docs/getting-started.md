# Create a project

For updatable projects, use a template source that already has a Git commit. Prefer
a release tag when available. For a local template use an **absolute path**: Copier
stores the source as supplied, and a relative path can stop resolving when you later
run `copier update` from the generated project's directory. A Git repository URL also
provides a stable source reference.

```bash
uvx copier copy /path/to/repo-template /path/to/new-project
cd /path/to/new-project
uv lock
uv sync --locked --group dev --group docs
make test lint security docs-build demo
uv run pre-commit install
```

The questionnaire requires the DEV workspace URL and catalog name. For each
environment choose whether to create the catalog on deployment or use an existing
catalog. For existing catalogs, choose whether to create the four `lz`, `bronze`,
`silver` and `gold` schemas or use ones that already exist. QA/PROD settings can be
left blank until release setup; their catalogs never default to DEV. Generation does
not contact a workspace or provision resources.

The generated `databricks.yml` contains concrete DEV host/catalog values. In VS Code
select target **dev** and choose authentication separately in the Databricks extension.
There is no need to export workspace/catalog variables before launching the IDE.
`--defaults` / noninteractive creation must supply the required connection answers:

```bash
uvx copier copy --defaults \
  --data dev_workspace_host=https://your-workspace.example.com \
  --data dev_catalog=your_existing_dev_catalog \
  /path/to/repo-template /path/to/new-project
```

These URLs and catalog names are public configuration, not credentials. Do not provide
PATs, passwords or OAuth tokens to Copier. Local checks work without workspace access.
The `examples/*.yml` URLs/catalogs are documentation-only examples for local rendering.

Commit the generated lockfile and Copier answers when initializing your new Git repository.
The answers file should contain `_src_path` and `_commit`. If `_commit` is missing,
the project was generated from an unversioned source and needs a verified baseline
before normal updates can work.
No Copier tasks execute automatically. `examples/*.yml` contain reproducible answer sets;
`make example` creates a local reference under `examples/generated` without deployment.

Use `make docs` to serve at `http://127.0.0.1:8000`, `make docs PORT=8001` for another
port, `make docs-build` for strict validation and `make docs-clean` to remove `site/`.
The theme follows the supplied electricity forecasting repository: Material light/dark
palettes, teal/amber colors, copy buttons, Mermaid, tables of contents and code reference.

Install the personal creation skill once using `python scripts/install_personal_skill.py`.
It defaults to `~/.agents/skills/create-ml-databricks-repo/SKILL.md`, outside generated
repositories, and refuses to replace a different existing skill without `--force`.

Remote setup starts with the generated operations guide. Catalogs, workspace URLs,
service principals and profile choices are supplied by the operator. Do not infer them
from an existing credential file. `make bundle-validate PROFILE=<chosen> TARGET=dev`
is an authenticated follow-up, not part of credential-free generation.
