# Databricks ML repository template

A Copier template for modular classification, regression and forecasting projects.
Choose separate DEV/QA/PROD workspaces and catalogs (default), or one workspace with
separate catalogs. Both options share uv, pytest, MkDocs Material, GitHub Actions,
Unity Catalog and serverless Declarative Automation Bundles.

```bash
uv sync --group dev --group docs
make lint test docs-build
make example
cd examples/generated
uv lock
uv sync --locked --group dev --group docs
make test lint security docs-build demo
```

For a new repository, run `uvx copier copy /path/to/repo-template /path/to/new-project`
and answer the questionnaire. No trusted tasks, credentials or remote resources are
used during generation. In a generated Git repository, retain `.copier-answers.yml`
and run `copier update` for future template updates. Prefer tagged template releases.
The template source must be committed to Git before versioned Copier updates are
available; this workspace has not been initialized as a Git repository.

See [architecture](docs/architecture.md), [creation guide](docs/getting-started.md),
and [verification limits](docs/verification.md). Documentation commands are `make docs`
(`PORT=8001` to override), `make docs-build` (strict), and `make docs-clean`.

[template-basis.yml](template-basis.yml) records the reviewed Databricks skill pack,
skill versions and SHA-256 hashes, tested CLI, and validation scope. Generated projects
receive a matching snapshot. Run `make basis-check` to check synchronization, or
`make basis-compare SKILLS_DIR=/path/to/databricks/skills` to detect installed changes.
After a deliberate review, edit the root manifest and run `make basis-sync`.
See the [maintenance workflow](docs/maintenance.md) before updating the record.

The personal creation skill is packaged under `skills/create-ml-databricks-repo/`;
install it outside generated projects using `python scripts/install_personal_skill.py`.
Root `AGENTS.md` maintains the template; generated `AGENTS.md` guides project work.

Local checks are supported now. Authenticated DEV validation and integration must
be authorized and completed before a remotely verified release. QA/PROD deployment,
profiling enablement, GitHub Environment protections and model promotion require
operator setup; no credentials or remote resources have been used to build this template.
