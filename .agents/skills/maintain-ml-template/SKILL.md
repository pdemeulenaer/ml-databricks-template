---
name: maintain-ml-template
description: Change the Databricks ML Copier template, render representative projects and verify updates across template versions.
---

Locate the generating file under `template/`, rather than patching only an example.
Use `examples/*.yml` for reproducible answers. Run `make lint test docs-build`; the
matrix checks rendering, local checks, bundle resource shapes and a Git-based Copier
update. If questionnaire options change, add the corresponding matrix case and
explain the migration in `docs/maintenance.md`. Keep the personal creation skill
outside `template/`. Check Databricks syntax against official docs and CLI schema,
then report separately whether authenticated DEV validation was actually authorized
and run. Release only after a generated project passes DEV integration.
