#!/usr/bin/env python3
"""Create Metabase collections, questions, and dashboards from a definitions file.

The seeder reads a JSON definitions file and uses the Metabase API to create
missing items. Existing cards/dashboards are reused; cards listed with
``aliases`` are adopted and renamed. It is idempotent by name and never deletes
unrelated content.

Dashboard filters are intentionally not created; cards are built with Field
Filter template tags so filters can be added in a later pass.

Usage:
    uv run python scripts/seed_metabase.py --definitions metabase/definitions.json --dry-run
    uv run python scripts/seed_metabase.py --definitions ... --dashboard supply
    uv run python scripts/seed_metabase.py --definitions ...
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEFINITIONS = PROJECT_ROOT / "metabase" / "definitions.json"
PAGE_SIZE = 200


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class MetabaseClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def request(self, method: str, path: str, payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:1000]
            raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"{method} {path} failed: {exc.reason}") from exc

    def get(self, path: str):
        return self.request("GET", path)

    def post(self, path: str, payload: dict):
        return self.request("POST", path, payload)

    def put(self, path: str, payload: dict):
        return self.request("PUT", path, payload)

    def collection_items(self, collection_id: int, model: str) -> list[dict]:
        items: list[dict] = []
        offset = 0
        while True:
            query = urllib.parse.urlencode(
                [("models", model), ("archived", "false"), ("limit", PAGE_SIZE), ("offset", offset)]
            )
            payload = self.get(f"/api/collection/{collection_id}/items?{query}")
            data = payload.get("data", []) if isinstance(payload, dict) else payload
            items.extend(data)
            offset += len(data)
            total = payload.get("total") if isinstance(payload, dict) else None
            if not data or total is None or offset >= total:
                return items


def build_card_payload(card: dict, collection_id: int, database_id: int) -> dict:
    template_tags = []
    parameters = []
    for tag in card.get("tags", []):
        tag_id = str(uuid.uuid4())
        template_tags.append(
            {
                "id": tag_id,
                "type": "dimension",
                "widget-type": tag["widget_type"],
                "name": tag["name"],
                "display-name": tag["display_name"],
                "dimension": ["field", {"lib/uuid": str(uuid.uuid4())}, tag["field_id"]],
            }
        )
        parameters.append(
            {
                "id": tag_id,
                "type": tag["widget_type"],
                "target": ["dimension", ["template-tag", tag["name"]]],
                "name": tag["display_name"],
                "slug": tag["name"],
                "isMultiSelect": tag["widget_type"] != "boolean/=",
            }
        )
    return {
        "name": card["name"],
        "description": card.get("description") or None,
        "collection_id": collection_id,
        "display": card.get("display", "table"),
        "dataset_query": {
            "database": database_id,
            "lib/type": "mbql/query",
            "stages": [
                {
                    "lib/type": "mbql.stage/native",
                    "native": card["sql"],
                    "template-tags": template_tags,
                }
            ],
        },
        "visualization_settings": card.get("visualization_settings", {}),
        "parameters": parameters,
        "type": "question",
        "parameter_mappings": [],
    }


def find_collection(client: MetabaseClient, parent_id: int, name: str) -> dict | None:
    for item in client.collection_items(parent_id, "collection"):
        if item.get("name") == name:
            return item
    return None


def ensure_collection(
    client: MetabaseClient, parent_id: int, name: str, description: str, dry_run: bool
) -> dict:
    existing = find_collection(client, parent_id, name)
    if existing:
        print(f"  collection exists: {name} (id={existing['id']})")
        return existing
    print(f"  collection create: {name}")
    if dry_run:
        return {"id": -1, "name": name}
    return client.post(
        "/api/collection",
        {"name": name, "description": description, "parent_id": parent_id},
    )


def find_card(client: MetabaseClient, collection_id: int, name: str) -> dict | None:
    for item in client.collection_items(collection_id, "card"):
        if item.get("name") == name:
            return item
    return None


def resolve_card(
    client: MetabaseClient,
    collection_id: int,
    card: dict,
    database_id: int,
    dry_run: bool,
) -> dict:
    if collection_id > 0:
        existing = find_card(client, collection_id, card["name"])
        if existing:
            print(f"    card exists: {card['name']} (id={existing['id']})")
            return {**existing, "name": card["name"], "display": card.get("display", "table")}

        for alias in card.get("aliases", []):
            existing = find_card(client, collection_id, alias)
            if existing:
                print(f"    card adopt: {alias!r} -> {card['name']!r} (id={existing['id']})")
                if not dry_run:
                    payload = build_card_payload(card, collection_id, database_id)
                    payload.pop("collection_id", None)
                    client.put(f"/api/card/{existing['id']}", payload)
                return {
                    **existing,
                    "name": card["name"],
                    "display": card.get("display", "table"),
                }

    print(f"    card create: {card['name']}")
    if dry_run:
        return {"id": -1, "name": card["name"], "display": card.get("display", "table")}
    return client.post("/api/card", build_card_payload(card, collection_id, database_id))


def find_dashboard(client: MetabaseClient, collection_id: int, name: str) -> dict | None:
    for item in client.collection_items(collection_id, "dashboard"):
        if item.get("name") == name:
            return item
    return None


def ensure_dashboard(
    client: MetabaseClient, collection_id: int, meta: dict, dry_run: bool
) -> dict:
    if collection_id > 0:
        existing = find_dashboard(client, collection_id, meta["dashboard"])
        if existing:
            print(f"  dashboard exists: {meta['dashboard']} (id={existing['id']})")
            return existing
    print(f"  dashboard create: {meta['dashboard']}")
    if dry_run:
        return {"id": -1, "name": meta["dashboard"], "dashcards": []}
    return client.post(
        "/api/dashboard",
        {
            "name": meta["dashboard"],
            "description": meta.get("description") or None,
            "collection_id": collection_id,
            "parameters": [],
        },
    )


def layout(cards: list[dict]) -> list[tuple[int, int, int, int]]:
    positions = []
    row = 0
    col = 0
    row_height = 0
    kpi_index = 0
    for card in cards:
        if card["name"].startswith("KPI -"):
            width = [5, 5, 5, 5, 4][kpi_index] if kpi_index < 5 else 4
            height = 3
            kpi_index += 1
        elif card.get("display") == "table" or card.get("full_width"):
            width = 24
            height = 7 if card.get("display") == "table" else 6
        else:
            width = 12
            height = 6

        if col + width > 24:
            row += row_height
            col = 0
            row_height = 0
        positions.append((row, col, width, height))
        col += width
        row_height = max(row_height, height)
        if col >= 24:
            row += row_height
            col = 0
            row_height = 0
    return positions


def populate_dashboard(
    client: MetabaseClient,
    dashboard_id: int,
    cards: list[dict],
    dry_run: bool,
    force_layout: bool = False,
) -> None:
    if dry_run or dashboard_id <= 0:
        print(f"    dashboard {dashboard_id}: would ensure {len(cards)} cards")
        return

    dashboard = client.get(f"/api/dashboard/{dashboard_id}")
    existing_dashcards = {dc.get("card_id"): dc for dc in dashboard.get("dashcards", [])}
    target_card_ids = {card["id"] for card in cards if card.get("id", -1) > 0}
    all_present = target_card_ids and target_card_ids.issubset(existing_dashcards)

    if all_present and not force_layout:
        print(f"    dashboard {dashboard_id}: all {len(cards)} cards already present; layout left untouched")
        return

    positions = layout(cards)
    payload_cards = []
    next_negative = -1
    for card, (row, col, size_x, size_y) in zip(cards, positions):
        existing = existing_dashcards.get(card.get("id"))
        if existing:
            payload_cards.append(
                {
                    "id": existing["id"],
                    "card_id": card["id"],
                    "row": row,
                    "col": col,
                    "size_x": size_x,
                    "size_y": size_y,
                    "parameter_mappings": existing.get("parameter_mappings", []),
                    "visualization_settings": existing.get("visualization_settings", {}),
                    "inline_parameters": existing.get("inline_parameters", []),
                }
            )
        else:
            payload_cards.append(
                {
                    "id": next_negative,
                    "card_id": card["id"],
                    "row": row,
                    "col": col,
                    "size_x": size_x,
                    "size_y": size_y,
                    "parameter_mappings": [],
                    "visualization_settings": {},
                    "inline_parameters": [],
                }
            )
            next_negative -= 1

    for card_id, dashcard in existing_dashcards.items():
        if card_id not in target_card_ids:
            payload_cards.append(
                {
                    "id": dashcard["id"],
                    "card_id": card_id,
                    "row": dashcard.get("row", 0),
                    "col": dashcard.get("col", 0),
                    "size_x": dashcard.get("size_x", 12),
                    "size_y": dashcard.get("size_y", 6),
                    "parameter_mappings": dashcard.get("parameter_mappings", []),
                    "visualization_settings": dashcard.get("visualization_settings", {}),
                    "inline_parameters": dashcard.get("inline_parameters", []),
                }
            )

    client.put(
        f"/api/dashboard/{dashboard_id}",
        {
            "dashcards": payload_cards,
            "parameters": dashboard.get("parameters", []),
            "tabs": dashboard.get("tabs", []),
        },
    )
    print(f"    dashboard {dashboard_id}: ensured {len(payload_cards)} cards")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--definitions",
        type=Path,
        default=DEFAULT_DEFINITIONS,
        help=f"Definitions JSON (default: {DEFAULT_DEFINITIONS})",
    )
    parser.add_argument("--dashboard", help="Only seed one dashboard key")
    parser.add_argument("--root-collection-id", type=int, help="Override root_collection_id")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--relayout", action="store_true", help="Reposition all cards even if present")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    base_url = os.environ.get("METABASE_URL", "http://127.0.0.1:3000")
    api_key = os.environ.get("METABASE_API_KEY", "").strip()
    if not api_key:
        print("METABASE_API_KEY is not set in the environment or .env", file=sys.stderr)
        return 2

    definitions_path = args.definitions
    if not definitions_path.is_absolute():
        definitions_path = PROJECT_ROOT / definitions_path
    definitions = json.loads(definitions_path.read_text(encoding="utf-8"))
    root_id = args.root_collection_id or definitions.get("root_collection_id")
    database_id = definitions.get("database_id")
    if not root_id or not database_id:
        print("Definitions must provide root_collection_id and database_id.", file=sys.stderr)
        return 2

    client = MetabaseClient(base_url, api_key)
    selected = [
        dashboard
        for dashboard in definitions["dashboards"]
        if (args.dashboard is None or dashboard["key"] == args.dashboard)
        and not dashboard.get("skip", False)
    ]
    if not selected:
        print(f"No dashboard matched {args.dashboard!r}.", file=sys.stderr)
        return 2

    for dashboard in selected:
        print(f"\n[{dashboard['key']}] {dashboard['dashboard']}")
        collection = ensure_collection(
            client,
            root_id,
            dashboard["collection"],
            f"Questions and dashboard for {dashboard['dashboard']}.",
            args.dry_run,
        )
        collection_id = collection["id"]

        cards = []
        for card in dashboard["cards"]:
            resolved = resolve_card(
                client, collection_id, card, database_id, args.dry_run
            )
            resolved["full_width"] = card.get("full_width", False)
            cards.append(resolved)

        dash = ensure_dashboard(client, collection_id, dashboard, args.dry_run)
        populate_dashboard(client, dash["id"], cards, args.dry_run, args.relayout)

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
