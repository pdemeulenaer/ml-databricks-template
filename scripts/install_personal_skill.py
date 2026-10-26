"""Install the personal creation workflow outside generated projects."""

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path.home() / ".agents" / "skills")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1] / "skills/create-ml-databricks-repo/SKILL.md"
    target = args.destination / "create-ml-databricks-repo/SKILL.md"
    if target.exists() and target.read_bytes() != source.read_bytes() and not args.force:
        parser.error(f"Refusing to replace an existing skill: {target}; use --force deliberately")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(target)


if __name__ == "__main__":
    main()
