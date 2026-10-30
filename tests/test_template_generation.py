"""Render architecture combinations and exercise actual generated project commands."""

import ast
import itertools
import json
import os
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import copier
import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def run(args, cwd, *, timeout=180):
    result = subprocess.run(
        args,
        cwd=cwd,
        env={**os.environ, "NO_MKDOCS_2_WARNING": "1", "MLFLOW_DISABLE_AGENT_HINT": "1"},
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    assert result.returncode == 0, f"{' '.join(args)}\n{result.stdout}\n{result.stderr}"
    return result.stdout


def render(destination, *, problem="classification", topology="separate_workspaces", mode="batch"):
    copier.run_copy(
        str(ROOT),
        destination,
        data={
            "project_name": f"sample-{problem}",
            "project_title": f"Sample {problem.title()}",
            "package_name": f"sample_{problem}",
            "problem_type": problem,
            "workspace_topology": topology,
            "ingestion_mode": mode,
            "dev_workspace_host": "https://dev.example.databricks.com",
            "dev_catalog": "test_dev",
            "qa_workspace_host": "https://qa.example.databricks.com",
            "qa_catalog": "test_qa",
            "prod_workspace_host": "https://prod.example.databricks.com",
            "prod_catalog": "test_prod",
        },
        defaults=True,
        quiet=True,
    )
    return destination


@pytest.fixture(scope="session")
def bundle_schema():
    schema = json.loads(run(["databricks", "bundle", "schema"], ROOT))

    # The CLI emits Go Unicode regex; normalize only its known ASCII identifier classes.
    def normalize(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "pattern":
                    value[key] = child.replace(r"[\p{L}\p{N}]", "[A-Za-z0-9]").replace(
                        r"\p{L}", "[A-Za-z]"
                    )
                else:
                    normalize(child)
        elif isinstance(value, list):
            for child in value:
                normalize(child)

    normalize(schema)
    return jsonschema.Draft202012Validator(schema)


@pytest.mark.parametrize(
    "problem,topology,mode",
    list(
        itertools.product(
            ["classification", "regression", "forecasting"],
            ["separate_workspaces", "single_workspace"],
            ["batch", "arriving_files"],
        )
    ),
)
def test_architecture_matrix(tmp_path, bundle_schema, problem, topology, mode):
    project = render(tmp_path / "project", problem=problem, topology=topology, mode=mode)
    assert not (project / "copier.yml").exists()
    assert not (project / "skills/create-ml-databricks-repo").exists()
    assert (project / ".copier-answers.yml").is_file()
    assert (project / "template-basis.yml").read_bytes() == (
        ROOT / "template-basis.yml"
    ).read_bytes()
    for path in project.rglob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
    configs = [project / "databricks.yml", *project.glob("resources/*.yml")]
    for config in configs:
        bundle_schema.validate(yaml.safe_load(config.read_text()))
    root = yaml.safe_load((project / "databricks.yml").read_text())
    hosts = {target["workspace"]["host"] for target in root["targets"].values()}
    assert len(hosts) == (1 if topology == "single_workspace" else 3)
    assert "${env." not in (project / "databricks.yml").read_text()
    assert {name: target["variables"]["catalog"] for name, target in root["targets"].items()} == {
        "dev": "test_dev",
        "qa": "test_qa",
        "prod": "test_prod",
    }
    assert "namespace" not in root["variables"]
    assert all("default" not in target for target in root["targets"].values())
    # Shared jobs and DEV-only jobs are separate resource files. The target-scoped
    # definitions must not accidentally deploy integration utilities to QA/PROD.
    assert "resources" not in root
    assert all("resources" not in target for target in root["targets"].values())
    resource_configs = {
        path.name: yaml.safe_load(path.read_text()) for path in project.glob("resources/*.yml")
    }
    jobs = {}
    for config in resource_configs.values():
        jobs.update(config.get("resources", {}).get("jobs", {}))
        if "jobs" in config.get("targets", {}).get("dev", {}).get("resources", {}):
            assert not ({"qa", "prod"} & set(config.get("targets", {})))
    assert set(jobs) == {"data_pipeline", "training", "inference", "monitoring", "smoke"}
    dev_jobs = {}
    for config in resource_configs.values():
        dev_jobs.update(
            config.get("targets", {}).get("dev", {}).get("resources", {}).get("jobs", {})
        )
    assert set(dev_jobs) == {"seed_dev", "integration_dev"}
    tasks = dev_jobs["integration_dev"]["tasks"]
    assert [task["task_key"] for task in tasks] == ["data", "train", "infer", "monitor", "smoke"]
    assert [task.get("depends_on") for task in tasks] == [
        None,
        *[[{"task_key": key}] for key in ("data", "train", "infer", "monitor")],
    ]
    assert dev_jobs["seed_dev"]["environments"][0]["spec"]["dependencies"] == (
        "${var.runtime_dependencies}"
    )
    for workflow in project.glob(".github/workflows/*.yml"):
        # BaseLoader preserves GitHub's YAML 1.2 'on' instead of interpreting it as boolean.
        parsed = yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
        assert isinstance(parsed["on"], dict)
        if workflow.name == "release.yml":
            assert "pull_request" not in parsed["on"]
            assert parsed["jobs"]["deploy"]["environment"] == "${{ inputs.target }}"


@pytest.mark.parametrize("problem", ["classification", "regression", "forecasting"])
def test_generated_project_checks(tmp_path, problem):
    project = render(tmp_path / "project", problem=problem)
    run(["uv", "sync", "--group", "dev", "--group", "docs", "--quiet"], project)
    run(["make", "test", "lint", "security", "docs-build"], project)
    run(["uv", "run", "python", "scripts/check_bundle.py"], project)
    # Simulate ignored v0.2.0 overlays left behind by an update.
    legacy = project / "resources/dev-runtime.generated.yml"
    legacy.write_text(json.dumps({"targets": {"dev": {"resources": {"jobs": {"seed_dev": {}}}}}}))
    (project / "resources/runtime.generated.yml").write_text(
        json.dumps({"resources": {"jobs": {"training": {}}, "pipelines": {"features": {}}}})
    )
    run(["uv", "run", "python", "scripts/export_runtime.py"], project)
    assert yaml.safe_load(legacy.read_text()) == {}
    run(["uv", "build", "--quiet"], project)
    assert list((project / "dist").glob("*.whl"))
    runtime = json.loads((project / "resources/runtime.generated.yml").read_text())
    assert set(runtime) == {"targets"}
    assert set(runtime["targets"]) == {"dev", "qa", "prod"}
    deps = runtime["targets"]["dev"]["variables"]["runtime_dependencies"]
    assert deps[0] == "../dist/*.whl"
    assert all(
        target["variables"]["runtime_dependencies"] == deps
        for target in runtime["targets"].values()
    )
    assert any(dep.startswith("mlflow==") for dep in deps)
    assert not any(dep.startswith("pytest==") for dep in deps)
    run(["make", "demo"], project)
    metrics = json.loads((project / "artifacts/demo/metrics.json").read_text())
    report = json.loads((project / "artifacts/demo/monitoring.json").read_text())
    assert report["observed_label_count"] == 0
    assert "accuracy" not in report and "rmse" not in report
    assert metrics.get("accuracy", 1) > 0.8
    assert (project / "artifacts/demo/monitoring.html").is_file()
    refusal = subprocess.run(
        ["make", "bundle-validate", "PROFILE="], cwd=project, capture_output=True, text=True
    )
    assert refusal.returncode != 0
    assert "Set PROFILE explicitly" in refusal.stderr


def git(cwd, *args):
    return run(
        ["git", "-c", "user.name=Template Test", "-c", "user.email=test@example.test", *args], cwd
    )


def test_copier_update_preserves_project_customization(tmp_path):
    source = tmp_path / "template-source"
    source.mkdir()
    for item in ["copier.yml", "template-basis.yml", "template"]:
        path = ROOT / item
        if path.is_dir():
            shutil.copytree(path, source / item)
        else:
            shutil.copy2(path, source / item)
    git(source, "init", "--initial-branch=main")
    git(source, "add", ".")
    git(source, "commit", "-m", "Initial template")
    git(source, "tag", "v0.1.0")
    destination = tmp_path / "generated"
    run(
        [
            sys.executable,
            "-m",
            "copier",
            "copy",
            "--defaults",
            "--vcs-ref",
            "v0.1.0",
            "--data",
            "dev_workspace_host=https://dev.example.databricks.com",
            "--data",
            "dev_catalog=test_dev",
            str(source.resolve()),
            str(destination),
        ],
        tmp_path,
    )
    answers = yaml.safe_load((destination / ".copier-answers.yml").read_text())
    assert answers["_src_path"] == str(source.resolve())
    assert answers["_commit"] == "v0.1.0"
    git(destination, "init", "--initial-branch=main")
    git(destination, "add", ".")
    git(destination, "commit", "-m", "Generate project")
    customized = destination / "docs/use-case.md"
    customized.write_text(customized.read_text() + "\nProject-specific acceptance criteria.\n")
    git(destination, "add", ".")
    git(destination, "commit", "-m", "Customize use case")
    new_file = source / "template/docs/new-release.md.jinja"
    new_file.write_text("# New release\n\nAn additive template update.\n")
    basis = yaml.safe_load((source / "template-basis.yml").read_text())
    basis["reviewed_on"] = "2026-11-01"
    updated_basis = yaml.safe_dump(basis, sort_keys=False)
    (source / "template-basis.yml").write_text(updated_basis)
    (source / "template/template-basis.yml").write_text(updated_basis)
    git(source, "add", ".")
    git(source, "commit", "-m", "Add release documentation")
    git(source, "tag", "v0.2.0")
    # Run from the generated project's directory, using the source saved at creation.
    # Omitting --vcs-ref should select the newest release tag.
    run([sys.executable, "-m", "copier", "update", "--skip-answered"], destination)
    assert "Project-specific acceptance criteria." in customized.read_text()
    assert (destination / "docs/new-release.md").is_file()
    assert (destination / "template-basis.yml").read_text() == updated_basis
    answers = yaml.safe_load((destination / ".copier-answers.yml").read_text())
    assert answers["_commit"] == "v0.2.0"
    assert not list(destination.rglob("*.rej"))


def test_mixed_catalog_choices_are_valid_bundle_configuration(tmp_path, bundle_schema):
    project = tmp_path / "project"
    copier.run_copy(
        str(ROOT),
        project,
        data={
            "dev_workspace_host": "https://dev.example.com",
            "dev_catalog": "dev_catalog",
            "dev_catalog_action": "create",
            "qa_catalog": "qa_catalog",
            "qa_catalog_action": "use_existing",
            "qa_schemas_action": "create",
            "prod_catalog": "prod_catalog",
            "prod_catalog_action": "use_existing",
            "prod_schemas_action": "use_existing",
        },
        defaults=True,
        quiet=True,
    )
    for path in [project / "databricks.yml", *project.glob("resources/*.yml")]:
        bundle_schema.validate(yaml.safe_load(path.read_text()))
    storage = yaml.safe_load((project / "resources/storage.schemas.yml").read_text())
    dev = storage["targets"]["dev"]["resources"]
    qa = storage["targets"]["qa"]["resources"]
    assert set(dev["schemas"]) == {"lz", "bronze", "silver", "gold"}
    assert set(qa["schemas"]) == {"lz", "bronze", "silver", "gold"}
    assert "catalogs" not in dev and "catalogs" not in qa
    assert dev["job_runs"]["provision_catalog_run"]["job_id"] == (
        "${resources.jobs.provision_catalog.id}"
    )
    assert all(
        definition["comment"].endswith(
            "${resources.job_runs.provision_catalog_run.state.result_state}"
        )
        for definition in dev["schemas"].values()
    )
    assert "prod" not in storage["targets"]
    assert dev["volumes"]["landing_files"]["schema_name"] == "${resources.schemas.lz.name}"
    assert dev["pipelines"]["features"]["schema"] == "${resources.schemas.gold.name}"
    # The CLI requires resource keys to be unique across resource types.
    assert (
        "training_experiment"
        in yaml.safe_load((project / "resources/training.experiment.yml").read_text())["resources"][
            "experiments"
        ]
    )


@pytest.fixture
def fake_databricks_endpoint():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/api/2.0/preview/scim/v2/Me"):
                status = 200
                data = {"id": "1", "userName": "local@example.com", "groups": []}
            elif self.path.startswith("/api/2.0/workspace/get-status"):
                status, data = 200, {"object_type": "DIRECTORY"}
            elif self.path.startswith("/.well-known/databricks-config"):
                status, data = 200, {}
            else:
                status, data = 404, {"error_code": "RESOURCE_DOES_NOT_EXIST"}
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def log_message(self, *_args):
            pass

    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    except PermissionError:
        pytest.skip("The sandbox does not permit a local mock HTTP server")
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def test_runtime_export_removes_duplicate_resources_from_cli_config(
    tmp_path, fake_databricks_endpoint
):
    project = render(tmp_path / "project")
    config = project / "databricks.yml"
    config.write_text(
        config.read_text().replace("https://dev.example.databricks.com", fake_databricks_endpoint)
    )
    old_runtime = project / "resources/runtime.generated.yml"
    old_runtime.write_text(json.dumps({"resources": {"jobs": {"training": {}}}}))
    old_dev = project / "resources/dev-runtime.generated.yml"
    old_dev.write_text(json.dumps({"targets": {"dev": {"resources": {"jobs": {"seed_dev": {}}}}}}))
    fake_config = tmp_path / "databrickscfg"
    fake_config.write_text(f"[offline_test]\nhost = {fake_databricks_endpoint}\ntoken = fake\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DATABRICKS_", "BUNDLE_"))}
    env.update(DATABRICKS_CONFIG_FILE=str(fake_config), DATABRICKS_HOST=fake_databricks_endpoint)
    command = [
        "databricks",
        "bundle",
        "validate",
        "-t",
        "dev",
        "--profile",
        "offline_test",
        "-o",
        "json",
    ]
    before = subprocess.run(
        command, cwd=project, env=env, capture_output=True, text=True, timeout=30
    )
    assert "multiple resources or scripts have been defined with the same key" in before.stderr

    shim = tmp_path / "bin"
    shim.mkdir()
    fake_uv = shim / "uv"
    fake_uv.write_text('#!/bin/sh\nprintf "mlflow==3.17.2\\nnumpy==2.1.0\\n"\n')
    fake_uv.chmod(0o755)
    export_env = {**env, "PATH": str(shim) + os.pathsep + env["PATH"]}
    exported = subprocess.run(
        [sys.executable, "scripts/export_runtime.py"],
        cwd=project,
        env=export_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert exported.returncode == 0, exported.stderr
    after = subprocess.run(
        command, cwd=project, env=env, capture_output=True, text=True, timeout=30
    )
    assert after.returncode == 0, after.stderr
    resources = json.loads(after.stdout)["resources"]
    assert {"training", "inference", "monitoring", "smoke", "seed_dev"} <= set(resources["jobs"])
    for key in ("training", "inference", "monitoring", "smoke", "seed_dev"):
        dependencies = resources["jobs"][key]["environments"][0]["spec"]["dependencies"]
        assert "mlflow==3.17.2" in dependencies
        assert "./dist/*.whl" in dependencies
    assert "mlflow==3.17.2" in resources["pipelines"]["features"]["environment"]["dependencies"]
    assert yaml.safe_load(old_dev.read_text()) == {}
