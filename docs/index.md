# Databricks ML repository template

Turn a monolithic ML notebook into a tested repository with pure modules and explicit
Databricks adapters. Generate a small example first, verify its assumptions, then
replace synthetic data and baseline models with the use case's contracts.

Use `uvx copier copy <template-source> <destination>`, then follow the creation guide.
For maintenance, run `uv sync --group dev --group docs` and `make lint test docs-build`.
