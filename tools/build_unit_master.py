#!/usr/bin/env python3
"""Build a reproducible, regional FFBE form registry from sanitized source snapshots.

This reads JSON only. It never decrypts archives or discovers encryption keys.
Numeric form IDs stay unchanged except explicit regional keys for reviewed collisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

JP_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
IDENTITY_FIELDS = ("unit_id", "game_id", "sex", "character_reference", "trustmaster", "supertrust", "is_shift_form")
PRIMARY = {"sprite_sheet": "unit_anime_{id}.png", "frame_data": "unit_cgg_{id}.csv", "idle_animation": "unit_idle_cgs_{id}.csv"}
DEFAULT_REPORT = "reports/2026-10-02-unit-identities/asset-manifest.json"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def source_snapshot_fingerprint(snapshot):
    canonical = json.dumps(snapshot["sources"], ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def unique_rows(source):
    rows = {}
    for row in source["rows"]:
        key = str(row["original_id"])
        if key in rows:
            raise ValueError(f"Duplicate source form ID: {key}")
        rows[key] = row
    return rows


def english(name):
    return bool(name and not JP_TEXT.search(name))


def reward(value):
    if not value:
        return None
    if isinstance(value, list):
        return (str(value[0]), str(value[1]))
    parts = value.split(":")
    return ({"21": "EQUIP", "22": "MATERIA"}.get(parts[0], parts[0]), parts[1])


def gl_name(raw, localized, rejected):
    if localized:
        mismatches = [key for key in ("unit_id", "game_id", "sex") if str(raw.get(key)) != str(localized.get(key))]
        mismatches += [key for key in ("trustmaster", "supertrust") if reward(raw.get(key)) != reward(localized.get(key))]
        if raw["original_id"] == "199000102":
            mismatches.append("known_inherited_name_alias")
        if not mismatches:
            return localized["name"].strip(), "GL_datamine"
        rejected.append({"server": "GL", "original_id": raw["original_id"], "source": "GL_datamine", "candidate_name": localized["name"], "mismatched_fields": mismatches})
    return raw["name"].strip(), "GL"


def jp_name(raw, translated, rejected):
    if translated:
        mismatches = [key for key in IDENTITY_FIELDS if raw.get(key) != translated.get(key)]
        if not mismatches and english(translated.get("name")):
            return translated["name"].strip(), "translated"
        if mismatches:
            rejected.append({"server": "JP", "original_id": raw["original_id"], "source": "translated", "candidate_name": translated["name"], "mismatched_fields": mismatches})
    return raw["name"].strip(), "JP"


def regional_assets(files, server, original_id):
    selected = [row for row in files if str(row.get("server", "")).upper() == server and str(row.get("original_id")) == original_id]
    paths = {}
    for row in selected:
        destination = row["destination"].replace("\\", "/")
        if destination.startswith("/") or ":" in destination or ".." in destination.split("/"):
            raise ValueError(f"Unsafe manifest destination: {destination}")
        if destination in paths:
            raise ValueError(f"Duplicate manifest destination: {destination}")
        paths[destination] = row
    assets = {"scope": "regional", "server": server, "asset_files": sorted(paths)}
    for kind, template in PRIMARY.items():
        matches = [p for p in paths if Path(p).name == template.format(id=original_id)]
        if len(matches) != 1:
            raise ValueError(f"{server}:{original_id} requires exactly one {kind}; found {len(matches)}")
        assets[kind] = matches[0]
    assets["files"] = [{"path": p, "sha256": paths[p]["sha256"], "bytes": paths[p]["bytes"]} for p in sorted(paths)]
    return assets


def annotate_legacy(entries, decisions):
    """Copy legacy rows, adding explicit ambiguity metadata only to collisions."""
    collision_ids = {str(row["original_id"]) for row in decisions["collisions"]}
    result = []
    for entry in entries:
        row = dict(entry)
        original_id = str(row["id"])
        if original_id in collision_ids:
            row.update(identity_status="ambiguous_legacy_id", master_ids=[f"unit:GL:{original_id}", f"unit:JP:{original_id}"], master_catalog="catalog/unit_master.json")
        result.append(row)
    return result


def build_master(snapshot, decisions, legacy_rows, manifest=None, repo=None):
    if decisions.get("schema_version") != 1:
        raise ValueError("Unsupported identity decision schema")
    expected_fingerprint = decisions.get("source_snapshot_fingerprint")
    if not expected_fingerprint or expected_fingerprint != source_snapshot_fingerprint(snapshot):
        raise ValueError("Source snapshot fingerprint missing or mismatched; review identity decisions against the current sources")
    maps = {name: unique_rows(source) for name, source in snapshot["sources"].items()}
    gl, jp = maps["GL"], maps["JP"]
    collisions = {str(row["original_id"]) for row in decisions["collisions"]}
    if len(collisions) != len(decisions["collisions"]) or not collisions <= (gl.keys() & jp.keys()):
        raise ValueError("Collisions must be unique forms present in both raw regions")
    shared_decisions = {str(row["original_id"]) for row in decisions["shared_name_variants"]}
    if len(shared_decisions) != len(decisions["shared_name_variants"]) or not shared_decisions <= (gl.keys() & jp.keys()):
        raise ValueError("Shared decisions must be unique forms present in both raw regions")
    if shared_decisions & collisions:
        raise ValueError("A collision cannot also be a shared-name variant")
    for group, classification_field, classification in (("collisions", "classification", "different_unit_same_id"), ("shared_name_variants", "decision", "shared")):
        for decision in decisions[group]:
            original_id = str(decision["original_id"])
            if decision.get(classification_field) != classification:
                raise ValueError(f"Invalid {group} classification for {original_id}")
            for region in ("GL", "JP"):
                field = f"{region.lower()}_raw_name"
                if field in decision and decision[field] != maps[region][original_id]["name"]:
                    raise ValueError(f"Reviewed {region} raw name does not match sources for {original_id}")
    name_differences = {id_ for id_ in gl.keys() & jp.keys() if gl[id_]["name"] != jp[id_]["name"]}
    if name_differences - collisions - shared_decisions:
        raise ValueError("Unreviewed shared raw-name differences: " + ", ".join(sorted(name_differences - collisions - shared_decisions)))
    legacy = {str(row["id"]): row for row in legacy_rows}
    if len(legacy) != len(legacy_rows):
        raise ValueError("Duplicate IDs in legacy catalog")
    rejected, missing_catalog, missing_primary, units = [], [], [], []
    raw_union = gl.keys() | jp.keys()
    for original_id in sorted(raw_union | legacy.keys(), key=lambda value: (not value.isdigit(), int(value) if value.isdigit() else value)):
        present = [region for region in ("GL", "JP") if original_id in maps[region]]
        groups = [[region] for region in present] if original_id in collisions else [present]
        for regions in groups:
            identities = []
            for region in regions:
                raw = maps[region][original_id]
                name, source = gl_name(raw, maps.get("GL_datamine", {}).get(original_id), rejected) if region == "GL" else jp_name(raw, maps.get("translated", {}).get(original_id), rejected)
                identities.append({"server": region, "original_id": original_id, "source_unit_id": raw["unit_id"], "raw_name": raw["name"], "name": name, "name_source": source})
            # Prefer the identity-checked JP translation for shared forms. It also
            # avoids GL datamine base-name inheritance (e.g. Lid and stat pots).
            display = next((row["name"] for row in identities if row["server"] == "JP" and row["name_source"] == "translated"), None)
            display = display or next((row["name"] for row in identities if english(row["name"])), None)
            display = display or (identities[0]["name"] if identities else None)
            split = original_id in collisions
            if split:
                assets = regional_assets(manifest["files"], regions[0], original_id) if manifest is not None else {"scope": "regional", "server": regions[0], "asset_files": [], "status": "manifest_not_supplied"}
            else:
                prior = legacy.get(original_id)
                assets = {"scope": "legacy", "revision_status": "not_validated_by_region", "asset_files": []}
                if prior:
                    for kind in PRIMARY:
                        if prior.get(kind):
                            assets[kind] = prior[kind]
                            assets["asset_files"].append(prior[kind])
                else:
                    missing_catalog.append(original_id)
                missing = [kind for kind in PRIMARY if not assets.get(kind) or (repo is not None and not (Path(repo) / assets[kind]).is_file())]
                if missing:
                    missing_primary.append({"original_id": original_id, "missing": missing})
            unit = {"master_id": f"unit:{regions[0]}:{original_id}" if split else original_id, "original_id": original_id, "name": display,
                    "identity_status": "regional_collision" if split else "shared" if len(regions) == 2 else "regional_only" if regions else "unresolved_asset_only",
                    "regions": regions, "identities": identities, "assets": assets}
            if original_id == "199000102":
                unit["name_note"] = "GL datamine inherits Emma from its grouped base; both raw region rows identify Lid. That alias is rejected and remains uncertain."
            units.append(unit)
    master_ids = [row["master_id"] for row in units]
    if len(master_ids) != len(set(master_ids)):
        raise ValueError("Master IDs are not unique")
    source_metadata = [{"id": name, **{key: value for key, value in source.items() if key != "rows"}} for name, source in snapshot["sources"].items()]
    unresolved = sorted(legacy.keys() - raw_union)
    coverage = {"gl_raw_forms": len(gl), "jp_raw_forms": len(jp), "raw_id_union": len(raw_union), "shared_raw_ids": len(gl.keys() & jp.keys()),
                "gl_only_ids": len(gl.keys() - jp.keys()), "jp_only_ids": len(jp.keys() - gl.keys()), "collision_ids": len(collisions), "collision_identities": 2 * len(collisions),
                "source_identity_rows": len(raw_union) + len(collisions), "master_rows": len(units), "legacy_catalog_rows": len(legacy),
                "missing_source_metadata_count": len(unresolved), "missing_source_metadata_ids": unresolved,
                "missing_legacy_catalog_count": len(missing_catalog), "missing_legacy_catalog_ids": sorted(missing_catalog),
                "missing_legacy_primary_count": len(missing_primary), "missing_legacy_primary_files": missing_primary,
                "missing_english_name_count": sum(not english(row["name"]) for row in units),
                "missing_english_name_ids": [row["master_id"] for row in units if not english(row["name"])],
                "rejected_name_metadata": rejected,
                "translated_rows_excluded_from_jp_membership": len(maps.get("translated", {}).keys() - jp.keys())}
    return {"schema_version": 1, "sources": source_metadata, "coverage": coverage, "units": units}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--legacy-catalog", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--annotate-legacy", action="store_true", help="Add ambiguity metadata to collision rows in the selected legacy catalog")
    args = parser.parse_args()
    manifest_path = args.asset_manifest or args.repo / DEFAULT_REPORT
    if args.asset_manifest and not manifest_path.is_file():
        parser.error(f"Manifest not found: {manifest_path}")
    result = build_master(read_json(args.sources or args.repo / "catalog/unit_identity_sources.json"), read_json(args.decisions or args.repo / "catalog/unit_identity_decisions.json"),
                          read_json(args.legacy_catalog or args.repo / "catalog/units.json"), read_json(manifest_path) if manifest_path.is_file() else None, repo=args.repo)
    output = args.output or args.repo / "catalog/unit_master.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.annotate_legacy:
        legacy_path = args.legacy_catalog or args.repo / "catalog/units.json"
        decisions = read_json(args.decisions or args.repo / "catalog/unit_identity_decisions.json")
        legacy_path.write_text(json.dumps(annotate_legacy(read_json(legacy_path), decisions), ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result["coverage"].items() if isinstance(value, int)}, indent=2))


if __name__ == "__main__":
    main()
