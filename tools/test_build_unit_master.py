"""Registry identity regressions using the sanitized, checked-in source snapshots."""
import copy
import json
import unittest
from pathlib import Path

from build_unit_master import annotate_legacy, build_master, jp_name

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


if __name__ == "__main__":
    unittest.main()
