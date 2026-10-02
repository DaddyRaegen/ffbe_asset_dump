#!/usr/bin/env python3
"""Expand the legacy numeric base-unit lookup without flattening sprite forms.

The preserved snapshot seeds original display/acquisition fields, and later
customizations survive. Regional form identities, series evidence and explicit
asset paths come from unit_master.json.
No series, acquisition category or rarity is inferred from an ID or name.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile

GENERATED_FIELDS = frozenset({
    "original_id", "identity_status", "canonical_name", "master_id",
    "form_master_ids", "identities", "series", "series_values", "series_status", "assets",
})
SERIES_FIELDS = ("game_id", "series", "game_title", "series_status", "series_provenance")
SERVERS = ("GL", "JP")
NATIVE_ID = re.compile(r"[0-9]+\Z")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def native_id(value, label):
    if not isinstance(value, str) or not NATIVE_ID.fullmatch(value):
        raise ValueError(f"{label} must be a numeric string: {value!r}")
    return value


def id_order(value):
    return int(value), value


def check_lookup(lookup, label):
    if not isinstance(lookup, dict):
        raise ValueError(f"{label} must be a numeric-keyed object")
    for key, value in lookup.items():
        native_id(key, f"{label} key")
        if not isinstance(value, dict):
            raise ValueError(f"{label} row {key} must be an object")


def series_summary(identities):
    """Summarize only supported values; regional/form evidence remains nested."""
    values = sorted({row.get("series") for row in identities if row.get("series")})
    if len(values) > 1:
        return {"series": None, "series_values": values, "series_status": "multiple"}
    if values and all(row.get("series") == values[0] and row.get("series_status") == "known" for row in identities):
        return {"series": values[0], "series_status": "known"}
    return {"series": None, "series_status": "unknown"}


def representative(base, members):
    return next((member for member in members if member[1]["original_id"] == base), members[0])


def series_metadata(identity):
    fields = {key: deepcopy(identity.get(key)) for key in SERIES_FIELDS}
    if not fields["series_status"]:
        fields["series_status"] = "unknown_game_id" if fields["game_id"] else "no_unit_metadata"
    return fields


def build_lookup(legacy_snapshot, master, current=None):
    """Return a new lookup; inputs and original snapshot fields are never mutated.

    Snapshot fields seed existing entries unchanged. Current non-generated
    fields then preserve later user customizations. Unrelated numeric custom
    rows are retained instead of silently lost.
    """
    check_lookup(legacy_snapshot, "legacy snapshot")
    current = {} if current is None else current
    check_lookup(current, "current lookup")
    if master.get("schema_version") != 1 or not isinstance(master.get("units"), list):
        raise ValueError("Unsupported unit master schema")
    groups = defaultdict(lambda: defaultdict(list))
    seen_master_ids, seen_aliases = set(), set()
    for unit in master["units"]:
        master_id = unit.get("master_id")
        if not isinstance(master_id, str) or not master_id or master_id in seen_master_ids:
            raise ValueError(f"Missing or duplicate master ID: {master_id!r}")
        seen_master_ids.add(master_id)
        form = native_id(unit.get("original_id"), "master original_id")
        for identity in unit.get("identities", []):
            server = identity.get("server")
            if server not in SERVERS:
                raise ValueError(f"Unsupported identity server: {server!r}")
            if identity.get("original_id") != form or server not in unit.get("regions", []):
                raise ValueError(f"Alias does not match its master: {server}:{form}")
            alias = (server, form)
            if alias in seen_aliases:
                raise ValueError(f"Duplicate regional form: {server}:{form}")
            seen_aliases.add(alias)
            base = native_id(identity.get("source_unit_id"), "source_unit_id")
            groups[base][server].append((unit, identity))

    result = {}
    for base in sorted(groups.keys() | legacy_snapshot.keys() | current.keys(), key=id_order):
        row = deepcopy(legacy_snapshot.get(base, {}))
        row.update({key: deepcopy(value) for key, value in current.get(base, {}).items() if key not in GENERATED_FIELDS})
        regional = groups.get(base)
        if not regional:
            # Custom/legacy entries with no source metadata stay untouched. They
            # must not gain guessed identities, series, names or asset pointers.
            result[base] = deepcopy(legacy_snapshot.get(base, {}))
            result[base].update(deepcopy(current.get(base, {})))
            continue
        for members in regional.values():
            members.sort(key=lambda pair: (id_order(pair[1]["original_id"]), pair[0]["master_id"]))
        representatives = {server: representative(base, members) for server, members in regional.items()}
        roots = {unit["master_id"] for members in regional.values() for unit, identity in members if identity["original_id"] == base}
        shared_masters = set.intersection(*(set(unit["master_id"] for unit, _ in regional[server]) for server in SERVERS)) if len(regional) == 2 else set()
        collision_roots = len(regional) == 2 and len(roots) == 2 and all(
            identity["original_id"] == base and unit.get("identity_status") == "regional_collision"
            for unit, identity in representatives.values()
        )
        if len(regional) == 1:
            status = "regional_only"
        elif collision_roots:
            if shared_masters:
                raise ValueError(f"Collision base also has shared forms; review required: {base}")
            status = "regional_collision"
        elif shared_masters:
            status = "shared"
        else:
            raise ValueError(f"Disjoint regional base groups need an identity decision: {base}")

        identities = []
        all_source_identities = []
        for server in SERVERS:
            if server not in regional:
                continue
            _, identity = representatives[server]
            regional_row = {
                "server": server, "original_id": base, "source_unit_id": base,
                "name": identity.get("name"),
                **series_metadata(identity),
                "forms": [],
            }
            for unit, form_identity in regional[server]:
                all_source_identities.append(form_identity)
                regional_row["forms"].append({
                    "original_id": form_identity["original_id"], "master_id": unit["master_id"],
                    "name": form_identity.get("name"), "assets": deepcopy(unit["assets"]),
                    **series_metadata(form_identity),
                })
            identities.append(regional_row)

        if status == "regional_collision":
            canonical = " / ".join(f"{identity['server']}: {identity['name']}" for identity in identities)
        elif status == "shared":
            # The master builder already prefers an identity-checked JP English
            # translation, then GL English, without treating a name as identity.
            common = next((unit for members in regional.values() for unit, identity in members
                           if unit["master_id"] in shared_masters and identity["original_id"] == base), None)
            if common is None:
                common = next(unit for members in regional.values() for unit, _ in members if unit["master_id"] in shared_masters)
            canonical = common.get("name")
        else:
            canonical = identities[0]["name"]
        if base not in legacy_snapshot:
            row.setdefault("name", canonical)
            row.setdefault("type", "unknown")
            row.setdefault("rarity", "")
        row.update({
            "original_id": base, "identity_status": status, "canonical_name": canonical,
            "master_id": next(iter(roots)) if len(roots) == 1 else None,
            "form_master_ids": sorted({unit["master_id"] for members in regional.values() for unit, _ in members}),
            "identities": identities,
            **series_summary(all_source_identities),
        })
        result[base] = row
    return result


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--legacy-snapshot", type=Path)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    snapshot = args.legacy_snapshot or args.repo / "catalog/legacy_unit_lookup.json"
    master = args.master or args.repo / "catalog/unit_master.json"
    output = args.output or args.repo / "data.json"
    if output.resolve() in (snapshot.resolve(), master.resolve()):
        parser.error("Output must not overwrite a source snapshot or master registry")
    current = output if output.is_file() else args.repo / "data.json"
    lookup = build_lookup(read_json(snapshot), read_json(master), read_json(current) if current.is_file() else None)
    atomic_json(output, lookup)
    print(json.dumps({
        "lookup_rows": len(lookup),
        "sourced_base_ids": sum(bool(row.get("identities")) for row in lookup.values()),
        "regional_forms": sum(len(identity["forms"]) for row in lookup.values() for identity in row.get("identities", [])),
        "collision_base_ids": sum(row.get("identity_status") == "regional_collision" for row in lookup.values()),
        "preserved_legacy_rows": len(read_json(snapshot)),
    }, indent=2))


if __name__ == "__main__":
    main()
