"""Check and copy reviewed provenance, or compare it with locally installed skills."""

import argparse
import hashlib
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_basis(root: Path) -> dict:
    """Reject incomplete provenance before distributing a snapshot."""
    basis = yaml.safe_load((root / "template-basis.yml").read_text())
    if basis["schema_version"] != 1:
        raise ValueError("Unsupported template-basis schema_version")
    date.fromisoformat(str(basis["reviewed_on"]))
    databricks = basis["databricks"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", databricks["cli_version"]):
        raise ValueError("Record an exact tested Databricks CLI version")
    if not databricks["skill_pack_version"] or not databricks["skills_reviewed"]:
        raise ValueError("Record the skill pack version and reviewed skills")
    for name, skill in databricks["skills_reviewed"].items():
        if not re.fullmatch(r"databricks-[a-z0-9-]+", name):
            raise ValueError(f"Invalid skill name: {name}")
        if not re.fullmatch(r"[0-9a-f]{64}", skill["sha256"]):
            raise ValueError(f"Record a SHA-256 for {name}/SKILL.md")
        if skill["version"] is not None and not isinstance(skill["version"], str):
            raise ValueError(f"Skill version must be a string or null: {name}")
    for name in ("local_checks", "bundle_schema_check", "dev_workspace_integration"):
        if basis["validation"][name] not in {"passed", "failed", "not_run"}:
            raise ValueError(f"Invalid validation status: {name}")
    return basis


def compare_installed(basis: dict, skills_dir: Path) -> list[str]:
    """Report drift without changing the reviewed record or claiming compatibility."""
    differences = []
    for name, recorded in basis["databricks"]["skills_reviewed"].items():
        path = skills_dir / name / "SKILL.md"
        if not path.is_file():
            differences.append(f"Missing: {name}/SKILL.md")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != recorded["sha256"]:
            differences.append(f"Changed: {name}/SKILL.md")
    cli = subprocess.run(
        ["databricks", "--version"], check=True, capture_output=True, text=True, timeout=15
    ).stdout
    version = re.search(r"\d+\.\d+\.\d+", cli)
    if version is None or version.group() != basis["databricks"]["cli_version"]:
        differences.append(f"CLI differs from reviewed version: {cli.strip()}")
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "sync", "compare"])
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--skills-dir", type=Path)
    args = parser.parse_args()
    try:
        basis = load_basis(args.root)
        source = args.root / "template-basis.yml"
        snapshot = args.root / "template/template-basis.yml"
        if args.command == "sync":
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, snapshot)
            print("Copied reviewed provenance into template/template-basis.yml.")
        elif args.command == "check":
            if not snapshot.is_file() or snapshot.read_bytes() != source.read_bytes():
                parser.exit(1, "Provenance snapshot is stale; run make basis-sync.\n")
            print("Reviewed provenance and generated-project snapshot match.")
        else:
            if args.skills_dir is None:
                parser.error("compare requires --skills-dir; select the installed skill pack")
            differences = compare_installed(basis, args.skills_dir)
            if differences:
                parser.exit(
                    1, "\n".join(differences) + "\nReview changes before updating provenance.\n"
                )
            print("Installed skill entrypoints and CLI match the reviewed basis.")
    except (
        KeyError,
        TypeError,
        ValueError,
        OSError,
        yaml.YAMLError,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(1, f"Provenance check failed: {error}\n")


if __name__ == "__main__":
    main()
