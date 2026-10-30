"""Copy the bundled utils package into another project.

Usage:
    python scripts/install_into_project.py /path/to/project
    python scripts/install_into_project.py /path/to/project --force
    python scripts/install_into_project.py /path/to/project --with-requirements

The helper copies ``scripts/utils`` to ``<project>/utils`` and, when requested,
writes dependency manifests with a ``data-science-utils`` suffix so existing
project files are not overwritten.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = SKILL_ROOT / "scripts" / "utils"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=".", help="Project directory (default: current directory).")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing utils directory.")
    parser.add_argument(
        "--with-requirements",
        action="store_true",
        help="Also copy requirements files with a data-science-utils suffix.",
    )
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        parser.error(f"Target directory does not exist: {target}")

    destination = target / "utils"
    if destination.exists() and not args.force:
        parser.error(
            f"{destination} already exists. Use --force to overwrite it, "
            "or add the skill's scripts directory to sys.path instead."
        )

    shutil.copytree(PACKAGE_DIR, destination, dirs_exist_ok=args.force)
    print(f"Copied utils package to {destination}")

    if args.with_requirements:
        copied = []
        for name in ("requirements.txt", "requirements-optional.txt"):
            source = SKILL_ROOT / name
            destination_file = target / f"{source.stem}-data-science-utils{source.suffix}"
            shutil.copy2(source, destination_file)
            copied.append(destination_file)
            print(f"Copied {source.name} to {destination_file}")

        print("Install dependencies from the target project with:")
        print(f'  uv add -r "{copied[0]}"')

    print("Import with: from utils import ...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
