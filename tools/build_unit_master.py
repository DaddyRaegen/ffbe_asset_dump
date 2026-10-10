#!/usr/bin/env python3
"""Build a reproducible, regional FFBE form registry from sanitized source snapshots.

This reads JSON only. It never decrypts archives or discovers encryption keys.
Numeric form IDs stay unchanged except explicit regional keys for reviewed collisions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path

JP_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
IDENTITY_FIELDS = ("unit_id", "game_id", "sex", "character_reference", "trustmaster", "supertrust", "is_shift_form")
PRIMARY = {"sprite_sheet": "unit_anime_{id}.png", "frame_data": "unit_cgg_{id}.csv", "idle_animation": "unit_idle_cgs_{id}.csv"}
DEFAULT_REPORT = "reports/2026-10-02-unit-identities/asset-manifest.json"
UNIT_FOLDERS = ("unit_animated", "unit_animated_csv", "unit_icons", "unit_illustrations", "unit_assets")


def discover_unit_files(repo, original_ids):
    """Index native form tokens once, including OD/effect/page companions.

    Only the established legacy folders are scanned. Regional collision files
    must continue to come exclusively from the reviewed archive manifest.
    """
    known = set(original_ids)
    result = defaultdict(list)
    for folder in UNIT_FOLDERS:
        directory = Path(repo) / folder
        if not directory.is_dir():
            continue
        for entry in os.scandir(directory):
            if not entry.is_file() or not entry.name.startswith("unit_"):
                continue
            matches = set(re.findall(r"(?<![0-9])[0-9]+(?![0-9])", entry.name)) & known
            if len(matches) > 1:
                raise ValueError(f"Ambiguous unit form tokens: {entry.name}")
            if matches:
                result[matches.pop()].append(f"{folder}/{entry.name}")
    return {uid: sorted(paths) for uid, paths in result.items()}


def bundle_links(paths, original_id):
    """Expose every source companion while retaining the primary API paths."""
    paths = sorted(set(paths))
    grouped = {"sprite_sheets": [], "frame_data_files": [], "animation_csvs": [],
               "illustrations": [], "icons": [], "companion_files": []}
    for path in paths:
        name = Path(path).name
        if name.startswith("unit_anime_") and name.endswith(".png"):
            kind = "sprite_sheets"
        elif name.startswith("unit_cgg_") and name.endswith(".csv"):
            kind = "frame_data_files"
        elif name.endswith(".csv"):
            kind = "animation_csvs"
        elif name.startswith("unit_ills_"):
            kind = "illustrations"
        elif name.startswith("unit_icon_"):
            kind = "icons"
        else:
            kind = "companion_files"
        grouped[kind].append(path)
    result = {"asset_files": paths, **grouped}
    for key, filename in (("illustration", f"unit_ills_{original_id}.png"),
                          ("icon", f"unit_icon_{original_id}.png")):
        matches = [path for path in paths if Path(path).name == filename]
        if len(matches) > 1:
            raise ValueError(f"Duplicate {key} for {original_id}")
        result[key] = matches[0] if matches else None
    result["animation_sets"] = animation_sets(paths, original_id)
    return result


def animation_sets(paths, original_id):
    """Keep main, overdrive, and source-verified effect frame tables separate."""
    by_name = {Path(path).name: path for path in paths}
    uid = re.escape(original_id)
    definitions = [("main", f"unit_cgg_{original_id}.csv", rf"unit_anime_{uid}(?:_[0-9]+)?\.png")]
    if f"unit_cgg_{original_id}_OD.csv" in by_name:
        definitions.append(("OD", f"unit_cgg_{original_id}_OD.csv", rf"unit_anime_{uid}_OD(?:_[0-9]+)?\.png"))
    # These effect tables use the ordinary atlas. Their frame indices differ
    # from the main table; the accompanying CGS must not be sent to main CGG.
    if f"unit_cgg_{original_id}ef.csv" in by_name:
        definitions.append(("effect", f"unit_cgg_{original_id}ef.csv", rf"unit_anime_{uid}(?:_[0-9]+)?\.png"))
    if f"unit_cgg_limit_atkeff_{original_id}.csv" in by_name:
        definitions.append(("limit_atkeff", f"unit_cgg_limit_atkeff_{original_id}.csv", rf"unit_anime_{uid}(?:_[0-9]+)?\.png"))
    available = {key for key, _, _ in definitions}
    sequences = defaultdict(list)
    for name, path in by_name.items():
        if not name.endswith(".csv") or name.startswith("unit_cgg_"):
            continue
        if name.endswith(f"_{original_id}_OD.csv"):
            key = "OD"
        elif name.endswith(f"_{original_id}ef.csv"):
            key = "effect"
        elif name == f"unit_limit_atkeff_cgs_{original_id}.csv" and "limit_atkeff" in available:
            key = "limit_atkeff"
        else:
            key = "main"
        sequences[key].append(path)
    result = []
    for key, cgg_name, atlas_pattern in definitions:
        if cgg_name not in by_name and not sequences[key]:
            continue
        atlases = sorted(path for name, path in by_name.items() if re.fullmatch(atlas_pattern, name))
        result.append({"variant": key, "sprite_sheets": atlases, "frame_data": by_name.get(cgg_name),
                       "animation_csvs": sorted(sequences[key]),
                       "status": "complete" if atlases and cgg_name in by_name else "missing_companions"})
    for key in sorted(sequences.keys() - available):
        result.append({"variant": key, "sprite_sheets": [], "frame_data": None,
                       "animation_csvs": sorted(sequences[key]), "status": "missing_companions"})
    return result


def load_animation_notes(repo):
    if repo is None:
        return {}
    path = Path(repo) / "catalog/unit_animation_notes.json"
    if not path.is_file():
        return {}
    notes = read_json(path)
    if notes.get("schema_version") != 1:
        raise ValueError("Unsupported animation notes schema")
    return notes["units"]


def apply_animation_notes(assets, original_id, notes, repo=None):
    note = notes.get(original_id)
    if not note:
        return
    by_name = {Path(path).name: path for path in assets["asset_files"]}
    for name, expected in note["input_sha256"].items():
        if name not in by_name:
            raise ValueError(f"Reviewed animation input is missing: {name}")
        if repo is not None and hashlib.sha256((Path(repo) / by_name[name]).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Animation input changed; review source notes: {name}")
    unusable = [{**row, "path": by_name[row["filename"]]} for row in note.get("unusable_sequences", [])]
    excluded = {row["path"] for row in unusable}
    if unusable:
        assets["unusable_source_sequences"] = unusable
        assets["animation_csvs"] = [path for path in assets["animation_csvs"] if path not in excluded]
    if note.get("source_warnings"):
        assets["source_warnings"] = note["source_warnings"]
    for family in assets["animation_sets"]:
        family["animation_csvs"] = [path for path in family["animation_csvs"] if path not in excluded]
        warnings = [row for row in note.get("source_warnings", []) if row.get("variant") == family["variant"]]
        if warnings:
            family["source_warnings"] = warnings


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
    assets = {"scope": "regional", "server": server, **bundle_links(paths, original_id)}
    for kind, template in PRIMARY.items():
        matches = [p for p in paths if Path(p).name == template.format(id=original_id)]
        if len(matches) != 1:
            raise ValueError(f"{server}:{original_id} requires exactly one {kind}; found {len(matches)}")
        assets[kind] = matches[0]
    assets["files"] = [{"path": p, "sha256": paths[p]["sha256"], "bytes": paths[p]["bytes"]} for p in sorted(paths)]
    return assets


def annotate_legacy(entries, decisions, repo=None):
    """Copy legacy rows, adding explicit ambiguity metadata only to collisions."""
    collision_ids = {str(row["original_id"]) for row in decisions["collisions"]}
    discovered = discover_unit_files(repo, (str(row["id"]) for row in entries)) if repo is not None else None
    notes = load_animation_notes(repo)
    result = []
    for entry in entries:
        row = dict(entry)
        original_id = str(row["id"])
        if discovered is not None:
            row.update(bundle_links(discovered.get(original_id, []), original_id))
            apply_animation_notes(row, original_id, notes, repo)
        if original_id in collision_ids:
            row.update(identity_status="ambiguous_legacy_id", master_ids=[f"unit:GL:{original_id}", f"unit:JP:{original_id}"], master_catalog="catalog/unit_master.json")
        result.append(row)
    return result


def build_master(snapshot, decisions, legacy_rows, manifest=None, repo=None, series_sources=None):
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
    discovered = discover_unit_files(repo, raw_union | legacy.keys()) if repo is not None else None
    animation_notes = load_animation_notes(repo)
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
                    paths = discovered.get(original_id, []) if discovered is not None else prior.get("asset_files", [])
                    paths = sorted(set(paths) | {prior[kind] for kind in PRIMARY if prior.get(kind)})
                    assets.update(bundle_links(paths, original_id))
                    for kind in PRIMARY:
                        if prior.get(kind):
                            assets[kind] = prior[kind]
                else:
                    missing_catalog.append(original_id)
                missing = [kind for kind in PRIMARY if not assets.get(kind) or (repo is not None and not (Path(repo) / assets[kind]).is_file())]
                if missing:
                    missing_primary.append({"original_id": original_id, "missing": missing})
            apply_animation_notes(assets, original_id, animation_notes, repo)
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
    result = {"schema_version": 1, "sources": source_metadata, "coverage": coverage, "units": units}
    if series_sources is not None:
        from unit_series import attach_series
        attach_series(result, snapshot, series_sources)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--sources", type=Path)
    parser.add_argument("--decisions", type=Path)
    parser.add_argument("--legacy-catalog", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--series-sources", type=Path)
    parser.add_argument("--annotate-legacy", action="store_true", help="Add ambiguity metadata to collision rows in the selected legacy catalog")
    args = parser.parse_args()
    manifest_path = args.asset_manifest or args.repo / DEFAULT_REPORT
    if args.asset_manifest and not manifest_path.is_file():
        parser.error(f"Manifest not found: {manifest_path}")
    series_path = args.series_sources or args.repo / "catalog/series_sources.json"
    result = build_master(read_json(args.sources or args.repo / "catalog/unit_identity_sources.json"), read_json(args.decisions or args.repo / "catalog/unit_identity_decisions.json"),
                          read_json(args.legacy_catalog or args.repo / "catalog/units.json"), read_json(manifest_path) if manifest_path.is_file() else None, repo=args.repo,
                          series_sources=read_json(series_path) if series_path.is_file() else None)
    output = args.output or args.repo / "catalog/unit_master.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.annotate_legacy:
        legacy_path = args.legacy_catalog or args.repo / "catalog/units.json"
        decisions = read_json(args.decisions or args.repo / "catalog/unit_identity_decisions.json")
        legacy_path.write_text(json.dumps(annotate_legacy(read_json(legacy_path), decisions, repo=args.repo), ensure_ascii=True, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result["coverage"].items() if isinstance(value, int)}, indent=2))


if __name__ == "__main__":
    main()
