"""Provenance must be deliberate, portable and carried through generation."""

import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/template_basis.py"


def invoke(root, command, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), command, "--root", str(root), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.fixture
def basis_root(tmp_path):
    basis = yaml.safe_load((ROOT / "template-basis.yml").read_text())
    (tmp_path / "template-basis.yml").write_text(yaml.safe_dump(basis, sort_keys=False))
    return tmp_path


def test_committed_snapshot_is_current():
    result = invoke(ROOT, "check")
    assert result.returncode == 0, result.stderr


def test_sync_copies_reviewed_bytes_without_changing_source(basis_root):
    source = basis_root / "template-basis.yml"
    original = source.read_bytes()
    stale = invoke(basis_root, "check")
    assert stale.returncode == 1
    assert "make basis-sync" in stale.stderr
    assert invoke(basis_root, "sync").returncode == 0
    assert (basis_root / "template/template-basis.yml").read_bytes() == original
    assert source.read_bytes() == original
    assert invoke(basis_root, "check").returncode == 0
    source.write_bytes(original + b"\n# Reviewed change\n")
    assert invoke(basis_root, "check").returncode == 1


@pytest.mark.parametrize("invalid", ["hash", "validation"])
def test_invalid_record_cannot_replace_snapshot(basis_root, invalid):
    source = basis_root / "template-basis.yml"
    assert invoke(basis_root, "sync").returncode == 0
    snapshot = (basis_root / "template/template-basis.yml").read_bytes()
    basis = yaml.safe_load(source.read_text())
    if invalid == "hash":
        basis["databricks"]["skills_reviewed"]["databricks-core"]["sha256"] = "unknown"
    else:
        basis["validation"]["dev_workspace_integration"] = "assumed"
    source.write_text(yaml.safe_dump(basis))
    assert invoke(basis_root, "sync").returncode == 1
    assert (basis_root / "template/template-basis.yml").read_bytes() == snapshot


def test_installed_drift_is_reported_without_rewriting_record(basis_root):
    skills_dir = basis_root / "installed"
    skill = skills_dir / "databricks-core/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("A reviewed skill entrypoint.\n")
    source = basis_root / "template-basis.yml"
    basis = yaml.safe_load(source.read_text())
    basis["databricks"]["skills_reviewed"] = {
        "databricks-core": {
            "version": None,
            "sha256": hashlib.sha256(skill.read_bytes()).hexdigest(),
        }
    }
    # Compare against the actual locally available CLI; no workspace/profile is involved.
    cli = subprocess.run(
        ["databricks", "--version"], check=True, capture_output=True, text=True, timeout=15
    ).stdout
    basis["databricks"]["cli_version"] = re.search(r"\d+\.\d+\.\d+", cli).group()
    source.write_text(yaml.safe_dump(basis))
    original = source.read_bytes()
    result = invoke(basis_root, "compare", "--skills-dir", str(skills_dir))
    assert result.returncode == 0, result.stderr
    skill.write_text("An extension update, without a metadata version bump.\n")
    result = invoke(basis_root, "compare", "--skills-dir", str(skills_dir))
    assert result.returncode == 1
    assert "Changed: databricks-core/SKILL.md" in result.stderr
    assert source.read_bytes() == original
    skill.unlink()
    result = invoke(basis_root, "compare", "--skills-dir", str(skills_dir))
    assert result.returncode == 1
    assert "Missing: databricks-core/SKILL.md" in result.stderr
    skill.write_text("A reviewed skill entrypoint.\n")
    basis["databricks"]["cli_version"] = "0.0.0"
    source.write_text(yaml.safe_dump(basis))
    original = source.read_bytes()
    result = invoke(basis_root, "compare", "--skills-dir", str(skills_dir))
    assert result.returncode == 1
    assert "CLI differs from reviewed version" in result.stderr
    assert "Changed:" not in result.stderr and "Missing:" not in result.stderr
    assert source.read_bytes() == original
