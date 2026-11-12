# Metabase Export, Backup, and Restore

Metabase keeps all questions, dashboards, collections, users, and settings in
its **application database**. That database is the source of truth. This
reference covers three persistence layers:

1. **JSON definition export** — Git-friendly, no users or secrets, for review
   and version control.
2. **Full application-database dump** — exact restore point, private, contains
   users and settings.
3. **Native serialization** — YAML export/import, Pro/Enterprise only.

They solve different problems. Do not use one as a substitute for another.

## Choose the artifact

| Need | Artifact | Commit to Git? | Restores Metabase? |
| --- | --- | --- | --- |
| Review dashboard changes in a diff | JSON definition export | Yes | No (needs an importer) |
| Publish dashboard definitions to GitHub | JSON definition export | Yes | No |
| Recover after a bad upgrade or deletion | `pg_dump` of the app DB | **No** | Yes |
| Move to another instance | App DB dump (same version) or Pro serialization | **No** for dump | Yes |
| Native Git workflow with import | Pro/Enterprise serialization YAML | Yes | Yes |

The JSON export is readable and safe. The dump contains `core_user` rows
(emails, password hashes), `setting` values, API keys, and sessions. Keep dumps
private.

## JSON definition export

Use the bundled `scripts/export_metabase.py` or implement the same shape.

```powershell
uv run python scripts\export_metabase.py --collection-name "Airbnb Analytics"
```

The script:

1. Reads `METABASE_URL` and `METABASE_API_KEY` from `.env` or the environment.
2. Walks the root collection and every subcollection.
3. Fetches every card/model and dashboard through the API.
4. Removes volatile fields: timestamps, view counts, last-editor identity,
   public-sharing tokens, permission flags, and `result_metadata`.
5. Writes one JSON file per entity plus a `manifest.json`.

Output:

```text
metabase/export/
├── manifest.json
├── collections/
├── cards/
└── dashboards/
```

Manifest:

```json
{
  "exported_at": "2026-11-06T07:26:23+00:00",
  "metabase_version": "v0.64.3.5",
  "root_collection_id": 7,
  "root_collection_name": "Airbnb Analytics",
  "counts": {"collections": 6, "cards": 66, "dashboards": 5},
  "files": { "...": [] }
}
```

### What the JSON contains

- Collection names, descriptions, and locations.
- Card names, descriptions, `dataset_query` (native SQL or MBQL), display type,
  visualization settings, parameters, and parameter mappings.
- Dashboard parameters, tabs, dashcard layout, card IDs, and filter mappings.
- `entity_id` for stable identity.

### What it excludes

- Users, groups, permissions, sessions, API keys.
- Public-sharing tokens and embedding secrets.
- Query result metadata and timestamps.
- Alerts and subscriptions.

### Limits

- The JSON is **not** a native Metabase import format. Metabase OSS has no
  built-in import for it.
- IDs are instance-local. Importing into a different instance requires
  ID/field remapping.
- It is for versioning, review, and documentation. Use the app DB dump for an
  exact restore.
- Do not edit generated JSON by hand; re-run the exporter.

## Full application-database backup

Use this for an exact restore. It works while Metabase is running when the app
DB is PostgreSQL or MySQL. The warehouse may be PostgreSQL or BigQuery; the
application-database backup/restore workflow is identical because Metabase
stores its own metadata locally.

### Docker Compose example

```powershell
.\scripts\backup_metabase.ps1
```

The script writes a custom-format dump:

```powershell
docker compose exec -T postgres pg_dump -U postgres -d metabase -Fc -f /tmp/metabase.dump
docker compose cp postgres:/tmp/metabase.dump .\metabase\backups\
```

### Plain PostgreSQL

```bash
pg_dump -Fc -d metabase -f metabase_$(date +%Y%m%d_%H%M%S).dump
```

### Restore

Stop Metabase, recreate the app DB, restore, then start Metabase:

```powershell
.\scripts\restore_metabase.ps1 -DumpFile .\metabase\backups\metabase_20261106_142757.dump
```

The script:

1. Stops the Metabase container.
2. Drops and recreates the `metabase` database.
3. `pg_restore --no-owner --no-privileges --exit-on-error`.
4. Starts Metabase and waits for `/api/health`.

The analytics database is not touched. A restore is destructive: it replaces
the current users, settings, questions, and dashboards with the dump's state.

### Restore drill

Test the dump without touching the live app DB:

```powershell
docker compose exec -T postgres psql -U postgres -d postgres -c "CREATE DATABASE metabase_restore_test;"
docker compose cp .\metabase\backups\metabase_20261106_142757.dump postgres:/tmp/restore_test.dump
docker compose exec -T postgres pg_restore -U postgres -d metabase_restore_test --no-owner --no-privileges --exit-on-error /tmp/restore_test.dump
docker compose exec -T postgres psql -U postgres -d metabase_restore_test -c "SELECT count(*) FROM core_user; SELECT count(*) FROM report_dashboard; SELECT count(*) FROM report_card;"
docker compose exec -T postgres psql -U postgres -d postgres -c "DROP DATABASE metabase_restore_test WITH (FORCE);"
```

Expected in the worked example: 3 users, 5 dashboards, 66 cards. Counts depend on
the snapshot; use the dump's metadata as the source of truth.

## Native serialization (Pro/Enterprise)

Metabase's native serialization exports collections, questions, and dashboards
as YAML and imports by stable `entity_id`. It is designed for Git and
staging-to-production workflows.

**It is not available in the OSS image.** It requires a Pro or Enterprise
license.

- CLI: `metabase.jar export <dir>` / `metabase.jar import <dir>`
- API: `POST /api/ee/serialization/export` / `POST /api/ee/serialization/import`
- The API expects GZIP-compressed tar files.
- Source and target should use the same Metabase major version.
- Serialization is not a backup mechanism; use the app DB dump for backups.

## Cadence

| Event | Action |
| --- | --- |
| After adding/changing a question or dashboard | Run the JSON export; commit the diff |
| Before a Metabase upgrade | Full app DB dump |
| Before a database reset or `docker compose down -v` | Full app DB dump |
| Before a bulk API seed/update | Full app DB dump |
| Before publishing a public repo | Review the JSON; ensure `.env` and dumps are ignored |

Sizes from the worked example:

- Application database: ~25 MB.
- Custom-format dump: ~1.1–1.2 MB.
- JSON export for 66 cards + 5 dashboards: ~237 KB across 78 files.
- Exported JSON should stay well under a few MB; if it grows unexpectedly,
  check for embedded result metadata or unwanted collections.

## Git hygiene

Commit:

```text
metabase/definitions.json
metabase/export/
scripts/export_metabase.py
scripts/seed_metabase.py
scripts/backup_metabase.ps1
scripts/restore_metabase.ps1
metabase/README.md
```

Ignore:

```text
.env
metabase/backups/*.dump
metabase/backups/*.sql
metabase/backups/*.backup
metabase/backups/*.tar
metabase/backups/*.tgz
```

Use a `metabase/.gitignore` for the dump patterns and keep a `.gitkeep` in the
backup directory.

## Verification checklist

- [ ] JSON files parse.
- [ ] Manifest counts match the collection tree.
- [ ] No email, API key, password, or `public_uuid` in the export.
- [ ] `git check-ignore` confirms `.env` and dumps are ignored.
- [ ] A restore drill succeeds in a scratch database.
- [ ] `/api/health` is `200` after a real restore.
- [ ] The exporter is idempotent: a second run produces the same content, apart
      from `exported_at`.

## Common mistakes

| Mistake | Consequence | Fix |
| --- | --- | --- |
| Committing the app DB dump to a public repo | Leaks users, hashes, settings | Ignore dumps; keep them private |
| Treating JSON export as a restorable backup | Cannot rebuild without remapping | Use the app DB dump for restore |
| Editing generated JSON | Changes disappear on next export | Edit in Metabase and re-export |
| Assuming OSS has serialization | `export` endpoint 404/paid only | Use JSON export + app DB dump |
| Restoring without stopping Metabase | Connection errors / corrupt state | Stop Metabase first |
| Restoring into the wrong database | Data loss | Verify `-d metabase` and the dump path |
| Never testing the dump | Restore fails when needed | Run the scratch restore drill |
| Using `localhost` in Python scripts | ~2s per request on Windows | Use `127.0.0.1` |
| Committing `.env` | Leaks the admin API key | Keep `.env` gitignored |

## Security

- The API key is admin-level. Treat it like a password.
- The dump contains `core_user` emails and password hashes. Treat it like a
  production backup.
- Rotate the API key if it is exposed; rotate the admin password if it was
  shared in chat.
- Review exported SQL and descriptions before publishing a public repository.
