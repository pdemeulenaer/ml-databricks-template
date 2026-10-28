---
name: create-ml-databricks-repo
description: Create a modular Databricks ML repository from the reusable Copier template for classification, regression or forecasting.
---

Find the installed template source from the user's repository path or tagged Git URL.
Collect project/package names, problem type, workspace topology (separate workspaces
and catalogs by default; a shared workspace with separate catalogs is supported), and
batch or arriving-file ingestion. Collect the real DEV workspace HTTPS URL and existing
DEV catalog; do not infer either from credentials or use invented defaults. Offer a
project/developer schema prefix (the target suffix is added). QA/PROD host and catalog
answers are optional until release setup. Infer display title from the project name.
Run `uvx copier copy <source> <destination>`; prefer a release tag for reproducibility.
Do not enable trust or run template tasks; this template has none.

In the generated project run `uv lock`, `uv sync --locked --group dev --group docs`,
`make test lint security docs-build`, and `make demo`; commit the lockfile and Copier
answers in the new repository. Inspect the selected split strategy and assumptions
before adapting a notebook. Explain the model promotion and monitoring boundaries.

Configure workspace URLs, catalogs, a unique DEV namespace, run-as identity, GitHub
Environments and OAuth federation when the user requests deployment setup. Ask them
to choose the CLI profile and pass `--profile` explicitly. Credentials and remote
resources need explicit authorization; local creation does not authorize deployment.
Use `copier update` in a clean Git checkout for later template updates and rerun checks.
