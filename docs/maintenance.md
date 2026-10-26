# Maintain and release

Edit files under `template/` and run `make lint test docs-build`. Tests render all
12 combinations of problem, topology and ingestion; full local checks cover each
problem type. A real Git-based update test preserves a downstream customization while
applying a newer template revision. Add cases when an option changes architecture.

## Reviewed Databricks basis

The root `template-basis.yml` is the single source for the reviewed skill pack version,
each reviewed skill's declared version and `SKILL.md` SHA-256, tested Databricks CLI,
review date and validation results. `template/template-basis.yml` is a committed copy
distributed to generated projects. A null version means that skill declares no version.
The hashes identify skill entrypoints; they do not cover referenced files or the entire
extension package. Keep the package version as additional context and review relevant
references when updating the basis. No machine-specific installation paths are recorded.

Use `make basis-check` to validate the manifest and detect a stale snapshot. It runs
as part of `make test`, `make example` and CI, without needing the extension installed.
It does not certify that recorded checks were actually performed; the reviewer must
record accurate evidence and distinguish local checks from workspace integration.

To compare against an explicitly chosen installed skill pack:

```bash
make basis-compare SKILLS_DIR=/path/to/databricks/skills
```

The command reads the recorded skill entrypoints and runs only `databricks --version`.
Missing/changed skills or a different CLI version produce a nonzero exit status and a
review reminder. It never reads credentials, updates files or launches remote validation.
This optional local comparison is separate from CI: extension updates cannot silently
rewrite provenance or force a repository restructuring.

When reviewing a changed extension or CLI:

1. Compare the updated skills and relevant references with the recorded basis. Decide
   whether each change requires a template change or is only a new recommendation.
2. Apply appropriate changes under `template/`; rerun local checks and authorized DEV
   validation as applicable. Use `not_run` for any validation not performed for the new
   basis, and describe the evidence or limitation in `validation_evidence`.
3. Edit the root manifest deliberately: review date, package/skill versions, file hashes,
   tested CLI and validation results. Hash bytes with `sha256sum <skill>/SKILL.md`;
   obtain the CLI version with `databricks --version`. There is no automatic review stamp.
4. Run `make basis-sync`, then `make lint test docs-build`. Review and commit both manifest
   files with the implementation changes. Publish a template version after the required
   release validation below; downstream projects receive the snapshot via `copier update`.

In generated projects the snapshot describes the upstream template, while
`.copier-answers.yml` records its source and Git revision when available. Record local
project modifications and workspace validation separately in the operations guide.

## Release validation

The root lockfile is committed. Generated lockfiles are created after rendering rather
than copied from a different package identity. Remote dependency overlays are exported
from each generated lockfile before validation/deployment and ignored by Git.

Before tagging a release: inspect generated diffs, run the local suite and strict docs,
choose a DEV profile, obtain authorization, validate/deploy the bundle and run the actual
DEV integration with isolated synthetic input. Record workspace/runtime versions and
results. Do not call a local-only release remotely verified.

For tagged versions use `uvx copier copy --vcs-ref vX.Y.Z <source> <destination>`.
Use a Git URL or absolute local source path. Before updating a generated repository,
commit all intended files, including `.copier-answers.yml` and the generated dotfiles;
Copier requires a clean Git working tree.
Update from a clean generated Git repository using `uvx copier update`; inspect conflicts,
run `uv lock` when dependencies change, and rerun local and authorized DEV checks.
Version tags and publishing are operator actions; this scaffold does not create a release.

If an early copy has a broken relative `_src_path`, correct it to the actual absolute
source path or Git URL. A missing `_commit` is a separate issue: do not invent an old
revision. Compare the existing scaffold with a fresh render of a known source revision
and establish a matching baseline, preserving customizations. `copier recopy` does not
preserve project evolution, so it is not a substitute for this comparison.
