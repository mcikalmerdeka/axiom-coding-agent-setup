#!/usr/bin/env python3
"""Scaffold a project with the Metabase seed/export/backup workflow.

Creates:
    scripts/seed_metabase.py
    scripts/export_metabase.py
    scripts/backup_metabase.ps1
    scripts/restore_metabase.ps1
    metabase/README.md
    metabase/.gitignore
    metabase/definitions.json
    metabase/backups/.gitkeep
    metabase/export/.gitkeep

The starter definitions file uses placeholder IDs. Replace them with the real
root collection ID and database ID before running the seeder.

Usage:
    uv run python scripts/scaffold_metabase.py --target C:/path/to/project
    uv run python scripts/scaffold_metabase.py --target . --force
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPTS = SKILL_ROOT / "scripts"
COPIED_SCRIPTS = (
    "seed_metabase.py",
    "export_metabase.py",
    "backup_metabase.ps1",
    "restore_metabase.ps1",
)

README = """# Metabase content: seed, export, backup, and restore

This folder keeps the Metabase work reproducible outside the running container.

```text
metabase/
|-- README.md
|-- .gitignore
|-- definitions.json          # source of truth for the API seeder
|-- backups/                  # private pg_dump files (gitignored)
|   `-- .gitkeep
`-- export/                   # committed, Git-friendly JSON snapshot
```

## 1. Configure

Create a Metabase API key in **Admin -> Settings -> Authentication -> API Keys**
and assign the **Administrators** group. Add it to the project `.env`:

```dotenv
METABASE_URL=http://127.0.0.1:3000
METABASE_API_KEY=mb_...
```

Use `127.0.0.1`, not `localhost`, in scripts. On Windows, Python resolves
`localhost` to IPv6 first and falls back to IPv4, adding about two seconds per
request.

## 2. Define the content

Edit `definitions.json`:

- Set `root_collection_id` and `database_id` from the Metabase URLs/API.
- Add one dashboard object per dashboard.
- Add one card object per question: name, description, display, SQL, tags,
  aliases, visualization settings, and full-width flag.
- Resolve `schema.table.column` to numeric field IDs with
  `GET /api/database/{id}/metadata`.

The full schema is in the `building-metabase-dashboards` skill reference
`metabase-api-provisioning.md`.

## 3. Seed the collections, questions, and dashboards

```powershell
uv run python scripts\\seed_metabase.py --definitions metabase\\definitions.json --dry-run
uv run python scripts\\seed_metabase.py --definitions metabase\\definitions.json
```

The seeder is idempotent by name, adopts legacy names listed in `aliases`, and
does not delete unrelated content. Dashboard filters are not created; the cards
are filter-ready.

## 4. Export the definitions to Git

```powershell
uv run python scripts\\export_metabase.py --collection-id <root-collection-id>
```

Commit `metabase/export/`. The JSON contains collections, questions/models,
dashboards, SQL, visualization settings, and filter mappings. It excludes users,
passwords, API keys, and public-sharing tokens.

## 5. Back up the application database

```powershell
.\\scripts\\backup_metabase.ps1
```

The dump is an exact restore point for users, settings, questions, and
dashboards. It contains account data and secrets. Keep it private and never
commit it.

Restore (destructive):

```powershell
.\\scripts\\restore_metabase.ps1 -DumpFile .\\metabase\\backups\\metabase_<timestamp>.dump
```

Test a dump by restoring it into a scratch database before relying on it.

## Commit

```text
metabase/definitions.json
metabase/export/
scripts/seed_metabase.py
scripts/export_metabase.py
scripts/backup_metabase.ps1
scripts/restore_metabase.ps1
metabase/README.md
metabase/.gitignore
```

## Never commit

```text
.env
metabase/backups/*.dump
```

Metabase's native YAML serialization is a Pro/Enterprise feature; OSS uses the
JSON export plus the application-database dump.
"""

GITIGNORE = """# Metabase application-database dumps contain account data and secrets.
# Keep them out of Git. The JSON export in ../export/ is safe to commit.
*.dump
*.backup
*.sql
*.tar
*.tgz

!.gitkeep
"""

STARTER_DEFINITIONS = {
    "notes": [
        "Replace root_collection_id and database_id with real values from Metabase.",
        "Add dashboards and cards. See references/metabase-api-provisioning.md.",
        "Resolve field_id values from GET /api/database/{id}/metadata.",
        "Run scripts/seed_metabase.py --dry-run before applying.",
    ],
    "root_collection_id": 1,
    "root_collection_name": "Analytics",
    "database_id": 1,
    "dashboards": [],
}


def write_if_missing(path: Path, content: str, force: bool) -> bool:
    if path.exists() and not force:
        print(f"skip existing: {path}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"wrote: {path}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".", help="Project root (default: current directory)")
    parser.add_argument("--force", action="store_true", help="Overwrite generated files")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"Target does not exist: {target}")
        return 2

    scripts_dir = target / "scripts"
    metabase_dir = target / "metabase"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (metabase_dir / "backups").mkdir(parents=True, exist_ok=True)
    (metabase_dir / "export").mkdir(parents=True, exist_ok=True)

    for name in COPIED_SCRIPTS:
        source = SOURCE_SCRIPTS / name
        destination = scripts_dir / name
        if not source.exists():
            print(f"missing skill script: {source}")
            return 1
        if destination.exists() and not args.force:
            print(f"skip existing: {destination}")
            continue
        shutil.copy2(source, destination)
        print(f"copied: {destination}")

    write_if_missing(metabase_dir / "README.md", README, args.force)
    write_if_missing(metabase_dir / ".gitignore", GITIGNORE, args.force)
    write_if_missing(metabase_dir / "backups" / ".gitkeep", "", args.force)
    write_if_missing(metabase_dir / "export" / ".gitkeep", "", args.force)
    definitions = json.dumps(STARTER_DEFINITIONS, indent=2, ensure_ascii=False) + "\n"
    write_if_missing(metabase_dir / "definitions.json", definitions, args.force)

    print("\nScaffold ready.")
    print("Next: edit metabase/definitions.json, then run:")
    print("  uv run python scripts/seed_metabase.py --definitions metabase/definitions.json --dry-run")
    print("  uv run python scripts/export_metabase.py --collection-id <root-collection-id>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
