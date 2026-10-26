# Create a project

```bash
uvx copier copy /path/to/repo-template /path/to/new-project
cd /path/to/new-project
uv lock
uv sync --locked --group dev --group docs
make test lint security docs-build demo
uv run pre-commit install
```

Commit the generated lockfile and Copier answers when initializing your new Git repository.
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
