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
    namespace = bundle["variables"]["namespace"]["default"]
    assert namespace.replace("${bundle.target}", "dev") == "my_ml_project_dev"
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
        ("schema_prefix", "invalid-prefix"),
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
