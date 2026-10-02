"""Regressions for preserving the lookup while adding regional base identities."""
import copy
import json
from pathlib import Path
import unittest

from build_unit_lookup import build_lookup

ROOT = Path(__file__).resolve().parents[1]


def mini_master(form="100000102", base="100000102", servers=("GL", "JP")):
    identities = [{
        "server": server, "original_id": form, "source_unit_id": base,
        "name": "Rain", "game_id": "11001", "series": "Final Fantasy Brave Exvius",
        "game_title": "FFBE", "series_status": "known",
        "series_provenance": {"unit_source": server, "unit_form_id": form},
    } for server in servers]
    return {"schema_version": 1, "units": [{
        "master_id": form, "original_id": form, "name": "Rain",
        "identity_status": "shared" if len(servers) == 2 else "regional_only",
        "regions": list(servers), "identities": identities,
        "assets": {"scope": "legacy", "sprite_sheet": "unit_animated/unit_anime_" + form + ".png"},
    }]}


class UnitLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy = json.loads((ROOT / "catalog/legacy_unit_lookup.json").read_text(encoding="utf-8-sig"))
        cls.master = json.loads((ROOT / "catalog/unit_master.json").read_text(encoding="utf-8-sig"))
        cls.lookup = build_lookup(cls.legacy, cls.master)

    def test_every_original_row_field_is_preserved(self):
        self.assertEqual(len(self.legacy), 1043)
        for base, prior in self.legacy.items():
            for field, value in prior.items():
                self.assertEqual(self.lookup[base][field], value, (base, field))
        self.assertNotIn("rarity", self.lookup["210002507"])
        self.assertEqual(self.lookup["401012817"]["name"], "Storm Seeker Esther BS")

    def test_base_unit_coverage_uses_numeric_keys(self):
        bases = {identity["source_unit_id"] for unit in self.master["units"] for identity in unit["identities"]}
        self.assertEqual(len(self.lookup), 1895)
        self.assertEqual(set(self.lookup), bases)
        self.assertTrue(all(key.isascii() and key.isdigit() for key in self.lookup))
        self.assertNotIn("401008506", self.lookup)  # Kaito's intermediate form is not another base unit.

    def test_every_regional_form_occurs_once_under_its_source_base(self):
        expected = {(identity["server"], identity["original_id"]): (identity["source_unit_id"], unit["master_id"])
                    for unit in self.master["units"] for identity in unit["identities"]}
        actual = {}
        for base, row in self.lookup.items():
            for identity in row["identities"]:
                self.assertEqual((identity["original_id"], identity["source_unit_id"]), (base, base))
                for form in identity["forms"]:
                    alias = identity["server"], form["original_id"]
                    self.assertNotIn(alias, actual)
                    actual[alias] = base, form["master_id"]
        self.assertEqual(len(actual), 6823)
        self.assertEqual(actual, expected)

    def test_all_collision_forms_have_separate_master_and_asset_paths(self):
        collisions = {unit["master_id"]: unit for unit in self.master["units"] if unit["identity_status"] == "regional_collision"}
        found = {}
        for row in self.lookup.values():
            for identity in row["identities"]:
                for form in identity["forms"]:
                    if form["master_id"] in collisions:
                        self.assertNotIn(form["master_id"], found)
                        found[form["master_id"]] = form
                        self.assertTrue(form["assets"]["sprite_sheet"].startswith("regional_units/" + identity["server"].lower() + "/"))
        self.assertEqual(len(found), 22)
        self.assertEqual(set(found), set(collisions))
        for key, form in found.items():
            self.assertEqual(form["assets"], collisions[key]["assets"])

    def test_earlier_collisions_link_from_correct_gl_base(self):
        for base, form in [("401008505", "401008507"), ("401008605", "401008607"), ("401008705", "401008707")]:
            gl = next(identity for identity in self.lookup[base]["identities"] if identity["server"] == "GL")
            self.assertIn("unit:GL:" + form, [item["master_id"] for item in gl["forms"]])
            self.assertEqual(self.lookup[form]["master_id"], "unit:JP:" + form)
            self.assertEqual([identity["server"] for identity in self.lookup[form]["identities"]], ["JP"])

    def test_later_collision_bases_are_explicitly_ambiguous(self):
        collision_bases = {"401014207", "401014217", "401014307", "401014317", "401014507", "401014517", "401014607", "401014617"}
        self.assertEqual({base for base, row in self.lookup.items() if row["identity_status"] == "regional_collision"}, collision_bases)
        for base in collision_bases:
            row = self.lookup[base]
            self.assertIsNone(row["master_id"])
            self.assertNotIn("assets", row)
            self.assertEqual([identity["server"] for identity in row["identities"]], ["GL", "JP"])
        abigail = self.lookup["401014207"]
        self.assertEqual(abigail["name"], "GL: Master Machinist Abigail / JP: Dark Knight Duane")
        self.assertEqual(abigail["name"], abigail["canonical_name"])

    def test_new_acquisition_and_rarity_values_are_not_inferred(self):
        for base, row in self.lookup.items():
            if base not in self.legacy:
                self.assertEqual((row["type"], row["rarity"]), ("unknown", ""))

    def test_series_and_every_form_provenance_are_retained(self):
        expected = {(identity["server"], identity["original_id"]): identity
                    for unit in self.master["units"] for identity in unit["identities"]}
        for row in self.lookup.values():
            self.assertEqual(row["series_status"], "known")
            self.assertIsInstance(row["series"], str)
            for identity in row["identities"]:
                for form in identity["forms"]:
                    original = expected[identity["server"], form["original_id"]]
                    for field in ("game_id", "series", "game_title", "series_status", "series_provenance"):
                        self.assertEqual(form[field], original[field])

    def test_shared_localizations_keep_one_base_and_native_id(self):
        for base in ("401011607", "401011617", "401012807", "401012817", "401014407", "401014417"):
            self.assertEqual(self.lookup[base]["identity_status"], "shared")
            self.assertEqual(self.lookup[base]["master_id"], base)

    def test_current_custom_fields_and_numeric_custom_rows_survive(self):
        prior = copy.deepcopy(self.legacy)
        prior["100000102"].update(notes={"favorite": True}, series="outdated generated value", name="My Rain label", type="custom collection", rarity="my label")
        prior["999999990"] = {"name": "Private custom unit", "type": "custom", "notes": ["keep"]}
        result = build_lookup(self.legacy, self.master, prior)
        self.assertEqual(result["100000102"]["notes"], {"favorite": True})
        self.assertEqual((result["100000102"]["name"], result["100000102"]["type"], result["100000102"]["rarity"]), ("My Rain label", "custom collection", "my label"))
        self.assertEqual(result["100000102"]["canonical_name"], "Rain")
        self.assertNotEqual(result["100000102"]["series"], "outdated generated value")
        self.assertEqual(result["999999990"], prior["999999990"])
        prior["401014207"] = {"name": "A custom display label", "assets": {"sprite_sheet": "stale/wrong.png"}}
        collision = build_lookup(self.legacy, self.master, prior)["401014207"]
        self.assertEqual(collision["name"], "A custom display label")
        self.assertNotIn("assets", collision)

    def test_missing_and_conflicting_series_are_explicit(self):
        source = mini_master()
        source["units"][0]["identities"][1].update(series=None, game_title=None, series_status="unknown_game_id")
        row = build_lookup({}, source)["100000102"]
        self.assertIsNone(row["series"])
        self.assertEqual(row["series_status"], "unknown")
        source["units"][0]["identities"][1].update(series="Different supported franchise", series_status="known")
        row = build_lookup({}, source)["100000102"]
        self.assertIsNone(row["series"])
        self.assertEqual(row["series_status"], "multiple")
        self.assertEqual(row["series_values"], ["Different supported franchise", "Final Fantasy Brave Exvius"])

    def test_absent_series_metadata_stays_explicitly_unknown(self):
        source = mini_master()
        for identity in source["units"][0]["identities"]:
            for field in ("game_id", "series", "game_title", "series_status", "series_provenance"):
                identity.pop(field)
        row = build_lookup({}, source)["100000102"]
        self.assertIsNone(row["series"])
        self.assertEqual(row["series_status"], "unknown")
        self.assertTrue(all(identity["series_status"] == "no_unit_metadata" for identity in row["identities"]))

    def test_unreviewed_disjoint_groups_are_rejected(self):
        source = mini_master(servers=("GL",))
        other = mini_master(form="100000103", servers=("JP",))["units"][0]
        source["units"].append(other)
        with self.assertRaisesRegex(ValueError, "Disjoint regional base groups"):
            build_lookup({}, source)

    def test_duplicate_alias_and_non_numeric_lookup_keys_are_rejected(self):
        source = mini_master()
        source["units"][0]["identities"].append(copy.deepcopy(source["units"][0]["identities"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate regional form"):
            build_lookup({}, source)
        with self.assertRaisesRegex(ValueError, "numeric string"):
            build_lookup({"_metadata": {}}, mini_master())

    def test_rerun_is_semantically_stable_and_inputs_unchanged(self):
        before = copy.deepcopy((self.legacy, self.master, self.lookup))
        self.assertEqual(build_lookup(self.legacy, self.master, self.lookup), self.lookup)
        self.assertEqual((self.legacy, self.master, self.lookup), before)


if __name__ == "__main__":
    unittest.main()
