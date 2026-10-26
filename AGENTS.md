# Maintain the Databricks ML Copier template

Generated project source lives in `template/`. Make reusable changes there, then
render projects to verify them. Root code and documentation maintain the template;
root files do not get copied into generated repositories.

`template-basis.yml` is the reviewed provenance source. Its generated-project snapshot
is maintained with `make basis-sync`; `make basis-check` detects an out-of-date copy.
Update versions, hashes and review date only after reviewing changes and recording
validation evidence. Installing a newer extension does not constitute a review.

Use uv and Python 3.12. Run `make lint test docs-build` before completing changes.
Tests must cover all problem types and both deployment topologies. Keep Copier
question defaults backward compatible; exercise an actual Git-based Copier update
before tagging a template release. Avoid Copier tasks that execute automatically.

Use the Databricks core and matching product skills for Databricks changes; verify
current official documentation and offline CLI schema. Never auto-select a profile.
Remote validation, deployment, credentials and integration are separate from local
checks and require the user's authorization. Never deploy QA/PROD by default.
