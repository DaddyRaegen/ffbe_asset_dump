"""Registry identity regressions using the sanitized, checked-in source snapshots."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from build_unit_master import annotate_legacy, apply_animation_notes, build_master, bundle_links, discover_unit_files, jp_name, regional_assets

ROOT = Path(__file__).resolve().parents[1]


class UnitMasterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads((ROOT / "catalog/unit_identity_sources.json").read_text(encoding="utf-8"))
        cls.decisions = json.loads((ROOT / "catalog/unit_identity_decisions.json").read_text(encoding="utf-8"))
        cls.result = build_master(cls.snapshot, cls.decisions, [])
        cls.units = {unit["master_id"]: unit for unit in cls.result["units"]}

    def test_coverage_and_unique_mapping(self):
        coverage = self.result["coverage"]
        self.assertEqual((coverage["raw_id_union"], coverage["collision_ids"], coverage["collision_identities"], coverage["master_rows"]), (3932, 11, 22, 3943))
        self.assertEqual(len(self.units), len(self.result["units"]))
        pairs = [(identity["server"], identity["original_id"]) for unit in self.units.values() for identity in unit["identities"]]
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(len(pairs), 3311 + 3512)

    def test_shared_ids_and_different_numeric_forms_stay_unchanged(self):
        for unit in self.units.values():
            if unit["identity_status"] != "regional_collision":
                self.assertEqual(unit["master_id"], unit["original_id"])
        for id_ in ["401011607", "401011617", "401012807", "401012817", "401014407", "401014417", *map(str, range(256000101, 256000107))]:
            self.assertEqual(self.units[id_]["identity_status"], "shared")
        self.assertEqual(len(self.decisions["shared_name_variants"]), 83)

    def test_translated_gl_imports_never_establish_jp_membership(self):
        raw_jp = {row["original_id"] for row in self.snapshot["sources"]["JP"]["rows"]}
        extra = {row["original_id"] for row in self.snapshot["sources"]["translated"]["rows"]} - raw_jp
        self.assertEqual(len(extra), 420)
        for unit in self.units.values():
            if unit["original_id"] in extra:
                self.assertNotIn("JP", unit["regions"])

    def test_verified_abigail_duane_and_lid_names(self):
        self.assertEqual(self.units["unit:GL:401014207"]["name"], "Master Machinist Abigail")
        self.assertEqual(self.units["unit:JP:401014207"]["name"], "Dark Knight Duane")
        self.assertEqual(self.units["unit:GL:401014507"]["name"], "Dark Knight Duane")
        self.assertEqual(self.units["unit:JP:401014507"]["name"], "Hyoh & Panthera Ultimus")
        self.assertEqual(self.units["199000102"]["name"], "Lid")

    def test_translation_identity_mismatch_is_rejected(self):
        snapshot = copy.deepcopy(self.snapshot)
        row = next(row for row in snapshot["sources"]["translated"]["rows"] if row["original_id"] == "401014207")
        row.update(name="Wrong identity", sex="2")
        with self.assertRaisesRegex(ValueError, "snapshot fingerprint"):
            build_master(snapshot, self.decisions, [])
        raw = next(raw for raw in snapshot["sources"]["JP"]["rows"] if raw["original_id"] == "401014207")
        rejected = []
        self.assertEqual(jp_name(raw, row, rejected), (raw["name"], "JP"))
        self.assertEqual(rejected[0]["mismatched_fields"], ["sex"])

    def test_stale_shared_decision_cannot_merge_new_character(self):
        snapshot = copy.deepcopy(self.snapshot)
        row = next(row for row in snapshot["sources"]["JP"]["rows"] if row["original_id"] == "401011607")
        row.update(name="Different character", unit_id="100000102", sex="1")
        with self.assertRaisesRegex(ValueError, "snapshot fingerprint"):
            build_master(snapshot, self.decisions, [])

    def test_missing_fingerprint_is_rejected(self):
        decisions = copy.deepcopy(self.decisions)
        decisions.pop("source_snapshot_fingerprint")
        with self.assertRaisesRegex(ValueError, "snapshot fingerprint"):
            build_master(self.snapshot, decisions, [])

    def test_invalid_decision_classification_or_raw_name_is_rejected(self):
        for group, field, value in (("collisions", "classification", "shared"), ("shared_name_variants", "decision", "different_unit_same_id"), ("shared_name_variants", "jp_raw_name", "stale name")):
            decisions = copy.deepcopy(self.decisions)
            decisions[group][0][field] = value
            with self.assertRaises(ValueError):
                build_master(self.snapshot, decisions, [])

    def test_missing_manifest_primary_assets_fail_without_legacy_fallback(self):
        with self.assertRaisesRegex(ValueError, "requires exactly one sprite_sheet"):
            build_master(self.snapshot, self.decisions, [], {"files": []})

    def test_legacy_annotation_and_unresolved_asset_preserve_paths(self):
        original = [{"id": "401014207", "sprite_sheet": "old/abigail.png"}, {"id": "100000102", "sprite_sheet": "old/rain.png"}, {"id": "999999999", "sprite_sheet": "old/unknown.png"}]
        annotated = annotate_legacy(original, self.decisions)
        self.assertEqual(annotated[0]["sprite_sheet"], original[0]["sprite_sheet"])
        self.assertEqual(annotated[0]["identity_status"], "ambiguous_legacy_id")
        self.assertEqual(annotated[1:], original[1:])
        self.assertNotIn("identity_status", original[0])
        result = build_master(self.snapshot, self.decisions, original)
        unit = next(row for row in result["units"] if row["master_id"] == "999999999")
        self.assertEqual((unit["identity_status"], unit["name"], unit["regions"]), ("unresolved_asset_only", None, []))
        self.assertEqual(unit["assets"]["scope"], "legacy")

    def test_complete_native_bundle_discovery_keeps_variants_and_id_boundaries(self):
        uid = "100000102"
        names = {"unit_animated": [f"unit_anime_{uid}.png", f"unit_anime_{uid}_OD.png", f"unit_anime_{uid}_1.png", "unit_anime_1000001020.png"],
                 "unit_animated_csv": [f"unit_cgg_{uid}.csv", f"unit_cgg_{uid}ef.csv", f"unit_idle_cgs_{uid}.csv", f"unit_limit_move_cgs_{uid} .csv", f"unit_overdrive_cgs_{uid}_OD.csv"],
                 "unit_icons": [f"unit_icon_{uid}.png"],
                 "unit_illustrations": [f"unit_ills_{uid}.png"],
                 "unit_assets": [f"unit_atk_cgs_{uid}_1.png", "unit_animation_HD.png"]}
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            for folder, filenames in names.items():
                (repo / folder).mkdir()
                for name in filenames:
                    (repo / folder / name).touch()
            regional = repo / "regional_units/gl" / uid / "unit_animated"
            regional.mkdir(parents=True)
            (regional / f"unit_anime_{uid}.png").touch()
            discovered = discover_unit_files(repo, [uid])
            self.assertEqual(len(discovered[uid]), 11)
            links = bundle_links(discovered[uid], uid)
            self.assertEqual(len(links["sprite_sheets"]), 3)
            self.assertEqual(len(links["frame_data_files"]), 2)
            self.assertEqual(len(links["animation_csvs"]), 3)
            self.assertEqual(links["illustration"], f"unit_illustrations/unit_ills_{uid}.png")
            self.assertEqual(links["icon"], f"unit_icons/unit_icon_{uid}.png")
            self.assertEqual(links["companion_files"], [f"unit_assets/unit_atk_cgs_{uid}_1.png"])
            self.assertFalse(any("regional_units" in path for path in links["asset_files"]))

    def test_regional_bundle_links_never_import_another_server(self):
        uid = "401014207"
        rows = []
        for server in ("GL", "JP"):
            for folder, name in (("unit_animated", f"unit_anime_{uid}.png"),
                                 ("unit_animated_csv", f"unit_cgg_{uid}.csv"),
                                 ("unit_animated_csv", f"unit_idle_cgs_{uid}.csv"),
                                 ("unit_illustrations", f"unit_ills_{uid}.png")):
                rows.append({"server": server, "original_id": uid,
                             "destination": f"regional_units/{server.lower()}/{uid}/{folder}/{name}",
                             "bytes": 1, "sha256": "0" * 64})
        result = regional_assets(rows, "GL", uid)
        self.assertEqual(len(result["asset_files"]), 4)
        self.assertTrue(all(path.startswith(f"regional_units/gl/{uid}/") for path in result["asset_files"]))
        self.assertIn("/unit_illustrations/", result["illustration"])

    def test_overdrive_and_effect_sequences_use_their_own_frame_tables(self):
        uid = "254000403"
        paths = [f"unit_animated/unit_anime_{uid}.png", f"unit_animated/unit_anime_{uid}_OD.png",
                 *[f"unit_animated_csv/{name}" for name in
                   [f"unit_cgg_{uid}.csv", f"unit_idle_cgs_{uid}.csv", f"unit_cgg_{uid}_OD.csv",
                    f"unit_overdrive_cgs_{uid}_OD.csv", f"unit_cgg_{uid}ef.csv", f"unit_limit_atk_cgs_{uid}ef.csv"]]]
        assets = bundle_links(paths, uid)
        groups = {row['variant']: row for row in assets['animation_sets']}
        self.assertEqual(set(groups), {'main', 'OD', 'effect'})
        self.assertEqual(groups['OD']['sprite_sheets'], [f"unit_animated/unit_anime_{uid}_OD.png"])
        self.assertEqual(groups['effect']['sprite_sheets'], [f"unit_animated/unit_anime_{uid}.png"])
        self.assertEqual(groups['effect']['frame_data'], f"unit_animated_csv/unit_cgg_{uid}ef.csv")
        self.assertEqual(groups['main']['animation_csvs'], [f"unit_animated_csv/unit_idle_cgs_{uid}.csv"])

    def test_source_defect_stays_archived_but_is_not_an_active_sequence(self):
        uid = "100001101"
        paths = [f"unit_animated/unit_anime_{uid}.png", f"unit_animated_csv/unit_cgg_{uid}.csv",
                 f"unit_animated_csv/unit_idle_cgs_{uid}.csv", f"unit_animated_csv/unit_jump_cgs_{uid}.csv"]
        assets = bundle_links(paths, uid)
        notes = {uid: {'input_sha256': {}, 'unusable_sequences':
                      [{'filename': f'unit_jump_cgs_{uid}.csv', 'status': 'unusable_source_frame_reference'}]}}
        apply_animation_notes(assets, uid, notes)
        bad = f"unit_animated_csv/unit_jump_cgs_{uid}.csv"
        self.assertIn(bad, assets['asset_files'])
        self.assertNotIn(bad, assets['animation_csvs'])
        self.assertNotIn(bad, assets['animation_sets'][0]['animation_csvs'])
        self.assertEqual(assets['unusable_source_sequences'][0]['path'], bad)

    def test_changed_source_bytes_require_review_of_defect_notes(self):
        uid = "100001101"
        name = f"unit_cgg_{uid}.csv"
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / "unit_animated_csv").mkdir()
            (repo / "unit_animated_csv" / name).write_text("0,0,\n", encoding="utf-8")
            assets = bundle_links([f"unit_animated_csv/{name}"], uid)
            notes = {uid: {"input_sha256": {name: "0" * 64}}}
            with self.assertRaisesRegex(ValueError, "review source notes"):
                apply_animation_notes(assets, uid, notes, repo)


if __name__ == "__main__":
    unittest.main()
