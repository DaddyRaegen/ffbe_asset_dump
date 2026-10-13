"""Read-only APK member and sealed Frida delta validation for publication."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(r"S:\FFBE JP Data Export\build\v207-download-spacing")
BASELINE = Path(r"S:\FFBE JP Data Export\build\v206-event-cleanup")
EXPECTED_BASELINE = "345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d"
EXPECTED_SCRIPT = "54072bcb90afcde6a7a3b16b60ebd55a51162b1ed267d126ae94460b6a8bfac5"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    build = json.loads((ROOT / "staged_build/DOWNLOAD_SPACING_APK_BUILD.json").read_text(encoding="utf8"))
    plan = json.loads((ROOT / "audit/DOWNLOAD_SPACING_PLAN.json").read_text(encoding="utf8"))
    old_build = json.loads((BASELINE / "staged_build/EVENT_CLEANUP_APK_BUILD.json").read_text(encoding="utf8"))
    old_apk, new_apk = Path(old_build["apk"]), Path(build["apk"])
    assert sha(old_apk.read_bytes()) == EXPECTED_BASELINE, "Published206 APK differs"
    candidate = new_apk.read_bytes()
    assert len(candidate) == build["bytes"] and sha(candidate) == build["sha256"], "207 APK pin differs"
    assert plan["schema"] == "ffbe-download-spacing-plan-v1"
    assert plan["scope"] == "native-download-screen-comma-spacing-only"
    assert plan["baseline_apk_sha256"] == EXPECTED_BASELINE
    assert plan["baseline_script_sha256"] == EXPECTED_SCRIPT
    with zipfile.ZipFile(old_apk) as old, zipfile.ZipFile(new_apk) as new:
        names = old.namelist()
        assert len(names) == len(set(names)) and len(new.namelist()) == len(set(new.namelist())), "Duplicate APK member"
        assert names == new.namelist(), "APK member membership/order changed"
        changed, preserved, signing_changes = [], [], []
        signing_members = {"META-INF/FFBE.SF", "META-INF/FFBE.RSA", "META-INF/MANIFEST.MF"}
        for name in names:
            before, after = old.read(name), new.read(name)
            if before != after:
                (signing_changes if name in signing_members else changed).append(name)
            else:
                preserved.append(name)
        assert sorted(changed) == ["AndroidManifest.xml", "assets/frida_script.js"], "207 exceeds two-member scope"
        assert set(signing_changes) == signing_members, "Unexpected signing metadata changes"
        baseline_script = old.read("assets/frida_script.js")
        candidate_script = new.read("assets/frida_script.js")
        assert sha(baseline_script) == EXPECTED_SCRIPT
        assert sha(candidate_script) == plan["candidate_script_sha256"]
        expected = baseline_script.decode("utf8")
        version_before, version_after = "const PATCH_VERSION = 206;", "const PATCH_VERSION = 207;"
        assert expected.count(version_before) == 1, "Unexpected baseline patch version"
        expected = expected.replace(version_before, version_after)
        operations = plan["operations"]
        assert isinstance(operations, list) and 1 <= len(operations) <= 4, "Finite spacing operations required"
        for operation in operations:
            before, after, count = operation["before"], operation["after"], operation["count"]
            assert isinstance(before, str) and isinstance(after, str) and before != after and before
            assert isinstance(count, int) and 1 <= count <= 4
            assert "PATCH_VERSION" not in before and "PATCH_VERSION" not in after, "Version delta must be separate"
            assert expected.count(before) == count, "Spacing operation match count differs"
            expected = expected.replace(before, after)
        assert expected.encode("utf8") == candidate_script, "Unexpected Frida delta beyond sealed spacing operations"
        catalog = new.read("assets/content_delivery.tsv")
        side = new.read("assets/side_stories/manifest.tsv")
        return {"passed": True, "apk_sha256": build["sha256"], "apk_bytes": build["bytes"],
                "baseline_apk_sha256": EXPECTED_BASELINE, "changed_members": changed,
                "unchanged_member_count": len(preserved), "signing_metadata_changes": signing_changes,
                "expected_js_delta_passed": True,
                "baseline_script_sha256": sha(baseline_script), "candidate_script_sha256": sha(candidate_script),
                "content_catalog_sha256": sha(catalog), "side_manifest_sha256": sha(side),
                "spacing_plan_sha256": sha((ROOT / "audit/DOWNLOAD_SPACING_PLAN.json").read_bytes()),
                "network_requests_made": 0, "remote_mutations_made": 0}

if __name__ == "__main__":
    print(json.dumps(main()))
