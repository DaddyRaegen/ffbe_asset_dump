"""Verify the correction against frozen signed v201 and authoritative records."""
from pathlib import Path
import collections, hashlib, io, json, sys, zipfile
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path('C:\\Users\\Raegen\\Documents\\Codex\\2026-10-02\\task-2\\integration_work\\native_delivery_correction\\banner_audit')
WS = ROOT.parents[2]
sys.path.insert(0, str(WS / 'integration_work/events/scripts'))
import event_context as ctx
from cpk_convert import read_cpk

def sha(blob): return hashlib.sha256(blob).hexdigest()
def load(name): return json.loads((ROOT / name).read_text(encoding='utf-8-sig'))

def main():
    count = 0
    def check(condition, message):
        nonlocal count
        count += 1
        if not condition: raise AssertionError(message)
    changes = load('BANNER_CORRECTION_VALIDATION.json')
    catalog = {r['catalog_id']: r for r in json.loads((WS / 'catalog_output/event_catalog.json').read_text())['events']}
    audit = load('book_banner_mapping.json')['books']
    updates = load('banner_owner_updates.json')['updates']
    gaps = load('banner_gap_ledger.json')['gaps']
    frozen = WS / 'integration_work/full_inventory/recovery_round2/build_release/FFBE-Memorial-EN-Patch-6-Full-Inventory-Round2.apk'
    with zipfile.ZipFile(frozen) as archive:
        oldcpk = archive.read('assets/side_stories/spdungeon9.cpk')
        olddat = archive.read('assets/side_stories/LM1APs6u.dat')
        book_blob = archive.read('assets/side_stories/Nm36woZx.dat')
    for item in changes['changed_files']:
        old = oldcpk if item['name'].endswith('.cpk') else olddat
        check(sha(old) == item['source_sha256'], 'Signed-v201 source hash')
        check(Path(item['source_path']).read_bytes() == old, 'Frozen staged input equals signed APK')
        new = Path(item['corrected_path']).read_bytes()
        check(sha(new) == item['corrected_sha256'] and len(new) == item['corrected_bytes'], 'Corrected artifact SHA/size')
    oldicons = ctx.rows_bytes(olddat, 'LM1APs6u')
    newicons = ctx.rows_bytes((ROOT / 'corrected_payload/LM1APs6u.dat').read_bytes(), 'LM1APs6u')
    _, _, _, oldtoc, oldmembers = read_cpk(oldcpk)
    _, _, _, newtoc, newmembers = read_cpk((ROOT / 'corrected_payload/spdungeon9.cpk').read_bytes())
    check(len(oldicons) == len(newicons) == 11004, 'Icon row count preserved')
    check(len(oldmembers) == 1081, 'Frozen old CPK member count')
    check(len(newmembers) == 1237, 'Corrected CPK member count')
    for name, blob in oldmembers.items():
        check(newmembers[name] == blob, 'Old CPK member preserved: ' + name)
    oldbyid = {r['0HUPxDf1']: r for r in oldicons}
    newbyid = {r['0HUPxDf1']: r for r in newicons}
    check(len(newbyid) == len(newicons) and newbyid.keys() == oldbyid.keys(), 'No icon ID collision/add/delete')
    bybook = {r['M9mwe2cu']: r for r in ctx.rows_bytes(book_blob, 'Nm36woZx')}
    changedids = {r['icon_id'] for r in updates}
    for iconid, old in oldbyid.items():
        new = newbyid[iconid]
        changedkeys = {k for k in old if old[k] != new[k]}
        check(changedkeys == ({'qtkvrS60'} if iconid in changedids else set()), 'Only allowed icon filename changed')
    for row in updates:
        check(bybook[row['book_id']]['0HUPxDf1'] == row['icon_id'], 'Native owner-to-icon mapping')
        check(int(row['book_id']) >= 1000000, 'No baseline owner replacement')
        member = newbyid[row['icon_id']]['qtkvrS60']
        check(member == row['target_member'], 'Corrected icon filename')
        blob = newmembers[member]
        check(sha(blob) == row['source_image']['image_sha256'], 'Source image byte identity in CPK')
        with Image.open(io.BytesIO(blob)) as image: image.verify()
        with Image.open(io.BytesIO(blob)) as image:
            image.load(); check(list(image.size) == row['source_image']['image_dimensions'], 'Actual image dimensions')
        event = catalog[row['source_event_id']]
        substitution = row['regional_artwork_substitution']
        if row['source_artwork_server'] != event['server']:
            check(substitution is not None, 'Cross-region art has relationship proof')
            check(event['regional_match_status'] == 'supported_regional_counterpart', 'Cross-region proof not numeric-only')
            check(substitution['artwork_source_event'] in event['regional_match_ids'], 'Approved counterpart event identity')
            check(catalog[substitution['artwork_source_event']]['server'] == row['source_artwork_server'], 'Counterpart region matches image region')
        else:
            check(substitution is None, 'Direct source art provenance')
    added = {r['M9mwe2cu'] for r in bybook.values() if int(r['M9mwe2cu']) >= 1000000}
    restored = {r['book_id'] for r in updates}; missing = {r['book_id'] for r in gaps}
    check(len(restored) == 675 and len(missing) == 189, 'Expected measured restoration scope')
    check(not restored & missing and restored | missing == added, 'Exact disjoint coverage of all added owners')
    for gap in gaps:
        iconid = bybook[gap['book_id']]['0HUPxDf1']
        check(newbyid[iconid] == oldbyid[iconid], 'Documented source gap retains fallback')
        check(oldbyid[iconid]['qtkvrS60'] in newmembers, 'Fallback image physically retained')
    summary = {'passed': True, 'checks': count, 'source_is_frozen_signed_v201_APK': str(frozen), 'source_CPK_SHA256': sha(oldcpk), 'source_icon_table_SHA256': sha(olddat), 'restored_books': 675, 'explicit_source_gap_or_aggregate_fallback_books': 189, 'no_baseline_owner_or_icon_changes': True, 'all_1081_prior_CPK_members_byte_identical': True, 'all_675_restored_icon_source_image_links_checked': True, 'numeric_only_cross_server_substitution_rejected': True, 'image_decode_and_dimensions_verified': True, 'no_runtime_or_remote_action': True}
    Path('S:\\FFBE JP Data Export\\build\\v204-startup-fix\\audit\\content_checks\\INDEPENDENT_BANNER_VERIFICATION.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary))

if __name__ == '__main__': main()
