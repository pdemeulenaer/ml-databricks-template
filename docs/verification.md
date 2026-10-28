# Verification and boundaries

Verification on 28 October 2026: **33 template tests passed**, including the new
workspace/catalog questionnaire checks, both topology profiles, all three local ML
examples, and the Copier update test. Lint/format checks and strict documentation
builds passed. Temporary generated projects were removed after each test to fit the
available local disk space; no assertions were skipped. Workspace authentication,
permissions and remote execution remain unverified.

Local verification on 26 October 2026: **21 template tests passed**. This includes
the 12-way render matrix, three complete generated-project checks and a Git-based
Copier update. Root lint/format checks and strict MkDocs build also passed. Each
generated-project check runs unit tests, lint/format checks, Bandit, strict docs,
wheel build, runtime dependency export and an MLflow demo that reloads its artifact.
The provenance checks cover stale snapshots, explicit synchronization, invalid records,
changed/missing skill entrypoints and CLI drift without rewriting the reviewed record.
The render matrix and Copier update test also verify distribution of the snapshot.

The first reference was built and exercised locally before being captured under
`template/`. It uses synthetic independent numeric observations and a small random
forest. Regression and direct three-hour multi-series forecasting are generated variants.

The automated suite checks the render matrix, generated unit tests and lint, security
scanning, strict documentation builds, MLflow demos, offline CLI resource schemas, and
a Git-based Copier update. Forecasting tests verify purged chronological boundaries
and that changing future targets cannot change past input features.

No credentials, workspace authentication, catalog writes, deployments or remote job
runs are part of those checks. DEV integration, serverless environment availability,
permissions, data profiling, managed dashboard/alerts and federated GitHub authentication
remain workspace-dependent. YAML alone cannot install GitHub required reviewers.

The generated baseline computes monitoring metrics, standalone HTML dashboards and
breach flags; it can fail the monitoring job. Actual notifications require configured
recipients. Databricks data profiling setup is documented as an optional authorized
follow-up that creates service-managed tables and a dashboard. The remote baseline
has no outcome source and does not claim live model accuracy. The local demo explicitly
shows separate before-label and after-label reports on held-out synthetic data.

Official references were checked on 26 October 2026: [bundle templates](https://docs.databricks.com/aws/en/dev-tools/bundles/templates),
[Unity Catalog models](https://docs.databricks.com/aws/en/machine-learning/manage-model-lifecycle/),
[Python pipelines](https://docs.databricks.com/aws/en/ldp/developer/python-dev),
[data profiling](https://docs.databricks.com/aws/en/data-governance/unity-catalog/data-quality-monitoring/data-profiling/).
