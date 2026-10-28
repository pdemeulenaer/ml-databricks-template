"""Generated DEV bundles must resolve public connection settings without shell variables."""

from pathlib import Path

import copier
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def copy_project(destination, **answers):
    return copier.run_copy(str(ROOT), destination, defaults=True, quiet=True, data=answers)


@pytest.mark.parametrize("topology", ["single_workspace", "separate_workspaces"])
def test_minimal_dev_configuration_is_ready_for_ide(tmp_path, topology):
    destination = tmp_path / "project"
    copy_project(
        destination,
        workspace_topology=topology,
        dev_workspace_host="https://my-workspace.example.com/",
        dev_catalog="real_dev",
    )
    text = (destination / "databricks.yml").read_text()
    bundle = yaml.safe_load(text)
    dev = bundle["targets"]["dev"]
    assert dev["workspace"]["host"] == "https://my-workspace.example.com"
    assert dev["variables"]["catalog"] == "real_dev"
    assert "namespace" not in bundle["variables"]
    assert "${env." not in text
    required = {key for key, variable in bundle["variables"].items() if "default" not in variable}
    assert required <= dev["variables"].keys()
    # Unconfigured release targets must not inherit the DEV data catalog.
    assert "default" not in bundle["variables"]["catalog"]
    for name in ("qa", "prod"):
        release = bundle["targets"][name]
        assert "catalog" not in release["variables"]
        if topology == "single_workspace":
            assert release["workspace"]["host"] == dev["workspace"]["host"]
        else:
            assert "host" not in release["workspace"]
    answers = yaml.safe_load((destination / ".copier-answers.yml").read_text())
    assert answers["dev_catalog"] == "real_dev"
    assert answers["dev_workspace_host"] == "https://my-workspace.example.com/"


@pytest.mark.parametrize(
    "answer,value",
    [
        ("dev_workspace_host", "http://insecure.example.com"),
        ("dev_workspace_host", "https://user:password@workspace.example.com"),
        ("dev_workspace_host", "https://workspace.example.com/path"),
        ("dev_catalog", ""),
        ("dev_catalog", "invalid catalog"),
        ("qa_catalog", "real_dev"),
        ("prod_catalog", "real_dev"),
    ],
)
def test_invalid_connection_answers_are_rejected(tmp_path, answer, value):
    answers = {"dev_workspace_host": "https://workspace.example.com", "dev_catalog": "real_dev"}
    answers[answer] = value
    with pytest.raises(ValueError):
        copy_project(tmp_path / "project", **answers)


@pytest.mark.parametrize("missing", ["dev_workspace_host", "dev_catalog"])
def test_required_dev_answers_cannot_be_silently_omitted(tmp_path, missing):
    answers = {"dev_workspace_host": "https://workspace.example.com", "dev_catalog": "real_dev"}
    del answers[missing]
    with pytest.raises(ValueError):
        copy_project(tmp_path / "project", **answers)


@pytest.mark.parametrize("topology", ["single_workspace", "separate_workspaces"])
@pytest.mark.parametrize(
    "catalog_action,schemas_action",
    [("create", None), ("use_existing", "create"), ("use_existing", "use_existing")],
)
def test_catalog_and_schema_choices(tmp_path, topology, catalog_action, schemas_action):
    answers = {
        "workspace_topology": topology,
        "dev_workspace_host": "https://dev.example.com",
        "dev_catalog": "test_dev",
        "dev_catalog_action": catalog_action,
        "qa_catalog": "test_qa",
        "qa_catalog_action": "use_existing",
        "qa_schemas_action": "use_existing",
        "prod_catalog": "test_prod",
        "prod_catalog_action": "use_existing",
        "prod_schemas_action": "use_existing",
    }
    if schemas_action:
        answers["dev_schemas_action"] = schemas_action
    if catalog_action == "create":
        answers["dev_catalog_storage_root"] = "s3://example-managed/dev"
    project = tmp_path / "project"
    copy_project(project, **answers)
    bundle = yaml.safe_load((project / "databricks.yml").read_text())
    assert bundle["bundle"]["engine"] == "direct"
    assert bundle["experimental"]["skip_name_prefix_for_schema"] is True
    storage = yaml.safe_load((project / "resources/storage.schemas.yml").read_text())
    resources = storage.get("targets", {}).get("dev", {}).get("resources", {})
    assert ("catalogs" in resources) == (catalog_action == "create")
    create_schemas = catalog_action == "create" or schemas_action == "create"
    assert set(resources.get("schemas", {})) == (
        set(["lz", "bronze", "silver", "gold"]) if create_schemas else set()
    )
    for schema, definition in resources.get("schemas", {}).items():
        assert definition["name"] == schema
        assert definition["catalog_name"] == (
            "${resources.catalogs.environment_catalog.name}"
            if catalog_action == "create"
            else "${var.catalog}"
        )
        assert definition["lifecycle"]["prevent_destroy"]
    if catalog_action == "create":
        assert (
            resources["catalogs"]["environment_catalog"]["storage_root"]
            == "s3://example-managed/dev"
        )
    assert "qa" not in storage.get("targets", {}) and "prod" not in storage.get("targets", {})
    pipeline = (project / "pipelines/transformations.py").read_text()
    assert "namespace" not in pipeline
    assert ".bronze.my_ml_project_raw" in pipeline
    assert ".silver.my_ml_project_curated" in pipeline
    assert ".gold.my_ml_project_features" in pipeline
    assert "/lz/my_ml_project_files/input" in pipeline
