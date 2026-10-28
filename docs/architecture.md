# Architecture and options

The template renders only `template/`. Maintenance docs, tests and the personal skill
remain outside generated repositories. `.copier-answers.yml` records generation options
and the source needed for deliberate updates.

| Question | Options | Architectural effect |
| --- | --- | --- |
| Name, package, title | Validated identifiers; display title | Imports, wheel, docs and bundle names |
| Problem | Classification / regression / forecasting | Example, feature contract, metrics and split |
| Topology | Separate workspaces / shared workspace | Per-target literal workspace URLs or one shared workspace URL |
| DEV connection | Required HTTPS workspace URL and existing catalog | DEV bundle resolves without shell setup |
| Schema prefix | Editable default from the package name | Environment suffixes separate DEV/QA/PROD schemas |
| QA/PROD connection | Optional URLs/catalogs | Configure release targets now or defer them |
| Ingestion | Batch / arriving files | Bronze materialized view or Auto Loader streaming table |

Separate workspaces and catalogs are the enterprise default. Bind catalogs to intended
workspaces and configure grants. A shared workspace with separate catalogs is supported
for smaller teams, with its weaker isolation documented in the generated architecture.
Neither target names nor development mode enforce Unity Catalog isolation.

Batch inference is the proven example path. Online serving, REST APIs, large-scale
training, automatic cross-metastore promotion and a managed profiling service are
extensions rather than questionnaire choices for unfinished implementations.

Each environment has namespaced landing, Bronze, Silver, Gold, models, predictions and
monitoring schemas. Remote training updates only `candidate`; approved immutable artifacts
are copied/imported into destination registries and numeric versions are deployed to
QA/PROD. Deployment never retrains a model as a substitute for promotion.

Data and monitoring jobs use serverless STANDARD for scheduled batch work without a
tight startup SLA. Documentation, dependencies and the offline CLI schema checks follow
[official bundle examples](https://docs.databricks.com/aws/en/dev-tools/bundles/examples).
