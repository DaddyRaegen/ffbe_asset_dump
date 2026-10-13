"""Independent readback and regressions for the proposed event menu correction.

Optional --payload validates a later integrated directory. Banner edits may change
only icon IDs when --allow-banner-icons is explicitly supplied; source/native
launch fields, identities, archive eligibility and greeting routing remain strict.
"""
from pathlib import Path
import argparse, collections, copy, hashlib, json, sys, zipfile
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
HERE = Path('C:\\Users\\Raegen\\Documents\\Codex\\2026-10-02\\task-2\\integration_work\\native_delivery_correction\\event_audit')
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import build_event_correction as builder
ec = builder.ec

def read(p):
    return json.loads(Path(p).read_text('utf-8-sig'))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--payload', type=Path, default=HERE / 'proposed_payload')
    parser.add_argument('--allow-banner-icons', action='store_true')
    args = parser.parse_args()
    payload = args.payload.resolve()
    ledger = read(HERE / 'EVENT_CORRECTION_LEDGER.json')
    source = Path(ledger['input_archive'])
    assert builder.sha(source) == ledger['input_archive_sha256']
    with zipfile.ZipFile(source) as z:
        before = {s: ec.rows_bytes(z.read('assets/side_stories/' + s + '.dat'), s) for s in builder.TABLE_KEYS}
        old_manifest_blob = z.read('assets/side_stories/manifest.tsv')
        protected_quest_hashes = {n: builder.blob_sha(z.read('assets/side_stories/' + n))
                                 for n in ['24Eka6wL.dat', 'Fvix6V0n.dat', '1Bj4oy5Q.dat', 'Wg1a5VJR.dat']
                                 if 'assets/side_stories/' + n in z.namelist()}
    after = {s: ec.rows_bytes((payload / (s + '.dat')).read_bytes(), s) for s in builder.TABLE_KEYS}
    moves = {r['book_id']: r for r in ledger['moves']}
    cats = {r['catalog_id']: r for r in read(ROOT / 'catalog_output/event_catalog.json')['events']}
    checks = []
    def check(name, value):
        assert value, name
        checks.append({'name': name, 'passed': True})
    def validate_rows(candidate):
        for stem, key in builder.TABLE_KEYS.items():
            a = {r[key]: r for r in before[stem]}
            b = {r[key]: r for r in candidate[stem]}
            assert len(b) == len(candidate[stem]), ('duplicate ID', stem)
            assert a.keys() - b.keys() == ({'1550000'} if stem == 'Nm36woZx' else set()), ('missing IDs', stem)
            assert not b.keys() - a.keys(), ('new IDs', stem)
            for rid, row in b.items():
                differences = {f for f in a[rid].keys() | row.keys() if a[rid].get(f) != row.get(f)}
                allowed = {'2ShgIRU8', 'Z0EN6jSh'} if stem == 'Nm36woZx' else {'2ShgIRU8'}
                if args.allow_banner_icons:
                    allowed |= {'0HUPxDf1'}
                assert differences <= allowed, ('native field changed', stem, rid, differences)
                bid = rid if stem == 'Nm36woZx' else row.get('M9mwe2cu')
                expected = moves[bid]['proposed_season_id'] if bid in moves else a[rid].get('2ShgIRU8')
                assert row.get('2ShgIRU8') == expected, ('wrong category', stem, rid)
                if row.get('2ShgIRU8'):
                    assert 0 <= int(row['2ShgIRU8']) < 2 ** 31
        if args.allow_banner_icons:
            assert [{k: v for k, v in r.items() if k != '0HUPxDf1'} for r in candidate['D2zaT7Ru']] == [{k: v for k, v in r.items() if k != '0HUPxDf1'} for r in before['D2zaT7Ru']], 'category headers changed'
        else:
            assert candidate['D2zaT7Ru'] == before['D2zaT7Ru'], 'category headers changed'
    validate_rows(after)
    check('All IDs, native contracts, fields, categories and int32 values independently preserved or match declared moves', True)
    check('Only the duplicate menu aggregation book is retired', len(before['Nm36woZx']) - len(after['Nm36woZx']) == 1)
    archive_moves = [r for r in moves.values() if r['current_season_id'] == '91']
    check('Exactly 389 source-normal archive books move into normal events', len(archive_moves) == 389)
    for row in archive_moves:
        check('Archive eligibility ' + row['book_id'], all(cats[c]['world_id'] == '2' and '3' not in cats[c]['mission_subtypes'] for c in row['catalog_ids']))
    archive_after = [r for r in after['Nm36woZx'] if r['2ShgIRU8'] == '91']
    check('Twenty story battle books remain archived', len(archive_after) == 20)
    for b in archive_after:
        audit = next(r for r in ledger['book_audit'] if r['book_id'] == b['M9mwe2cu'])
        check('Retained story source ' + b['M9mwe2cu'], all(cats[c]['world_id'] == '10' or '3' in cats[c]['mission_subtypes'] for c in audit['catalog_ids']))
    books = {r['M9mwe2cu']: r for r in after['Nm36woZx']}
    check('Source-proven greeting 7077 belongs to Greetings / Intros', books['7077']['2ShgIRU8'] == '93')
    check('Christmas Unit Introductions has a battle and remains in normal events', books['7067']['2ShgIRU8'] == '71')
    phase_proof = read(HERE / 'GREETING_PHASE_PROOF.json')
    phase_blob = Path(phase_proof['source_path']).read_bytes()
    check('Original JP phase evidence file identity reverified', builder.blob_sha(phase_blob) == phase_proof['source_sha256'])
    source_phases = ec.rows_bytes(phase_blob, 'Wg1a5VJR')
    greeting = [r for r in source_phases if r['qo3PECw6'] == phase_proof['greeting_mission_id']]
    promotion = [r for r in source_phases if r['qo3PECw6'] == phase_proof['Christmas_intro_battle_mission_id']]
    check('Greeting has only authored story phases; promotion has authored battle', bool(greeting) and all(r['gou39JeI'] == '1' for r in greeting) and any(r['gou39JeI'] == '2' for r in promotion))
    for bid in ['7029', '7047', '7070', '7079']:
        check('Raw-normal narrative special ' + bid, books[bid]['2ShgIRU8'] == '71')
    old_slots = {r['VMkv7S9R']: r for r in before['IL78hX09']}
    new_slots = {r['VMkv7S9R']: r for r in after['IL78hX09']}
    for alias in ledger['preserved_aliases']:
        aid, oid = alias['retained_alias_playback_id'], alias['preserved_original_playback_id']
        check('Alias data preserved ' + aid, new_slots[aid] == old_slots[aid])
        check('Alias launch contract equals retained source ' + aid,
              builder.presentation_equivalent(new_slots[aid], new_slots[oid], alias['source_stage_ids'], alias['source_stage_ids']))
        check('Alias has no reachable duplicate aggregation menu ' + aid, new_slots[aid]['M9mwe2cu'] not in books)
    # Concrete mutation tests exercise the preservation rule, not a mirror of edits.
    corrupted = copy.deepcopy(after)
    battle = next(r for r in corrupted['IL78hX09'] if r['89EvGKHx'] == '0' and r.get('6uIYE15X'))
    battle['6uIYE15X'] = str(int(battle['6uIYE15X']) + 1)
    rejected = False
    try:
        validate_rows(corrupted)
    except AssertionError:
        rejected = True
    check('Regression rejects changed native mission target', rejected)
    corrupted = copy.deepcopy(after)
    corrupted['IL78hX09'].pop()
    rejected = False
    try:
        validate_rows(corrupted)
    except AssertionError:
        rejected = True
    check('Regression rejects dropped playback or quest presentation', rejected)
    relations = read(ROOT / 'catalog_output/regional_relationships.json')
    collisions = [r for r in relations if r['status'] == 'same_id_different_title_unresolved_or_collision']
    for r in collisions:
        gl = cats[r['gl_catalog_id']]; jp = cats[r['jp_catalog_id']]
        a = {'server': 'GL', 'catalog_id': gl['catalog_id'], 'stage_id': 'mission:GL:123'}
        b = {'server': 'JP', 'catalog_id': jp['catalog_id'], 'stage_id': 'mission:JP:123'}
        check('Numeric cross-region ID cannot deduplicate ' + r['relationship_id'], builder.source_identity(a, 'battle') != builder.source_identity(b, 'battle'))
    sample = next(iter(new_slots.values()))
    check('Same native contract with different regional sources cannot deduplicate', not builder.presentation_equivalent(sample, sample, ['mission:GL:123'], ['mission:JP:123']))
    check('Same source stage with different native contract cannot deduplicate', not builder.presentation_equivalent(sample, dict(sample, V2mCH5UR='999999'), ['mission:JP:123'], ['mission:JP:123']))
    old_manifest = {r[0]: r for line in old_manifest_blob.decode().splitlines() if (r := line.split('\t'))}
    new_manifest_blob = (payload / 'manifest.tsv').read_bytes()
    new_manifest = {r[0]: r for line in new_manifest_blob.decode().splitlines() if (r := line.split('\t'))}
    for stem in builder.TABLE_KEYS:
        name = stem + '.dat'
        check('Manifest current hash ' + stem, new_manifest[name][1] == builder.sha(payload / name))
        check('Manifest tail fields preserved ' + stem, new_manifest[name][3:] == old_manifest[name][3:])
        accepted = set(filter(None, new_manifest[name][2].split(','))) | {new_manifest[name][1]}
        old_accepted = set(filter(None, old_manifest[name][2].split(','))) | {old_manifest[name][1]}
        check('Manifest retains all prior accepted hashes ' + stem, old_accepted <= accepted)
    if not args.allow_banner_icons:
        changed_names = {r['filename'] for r in read(HERE / 'MANIFEST_ROW_REVISIONS.json')['revisions']}
        check('Other manifest rows byte values unchanged', all(r == old_manifest[name] for name, r in new_manifest.items() if name not in changed_names))
    # No native content table was emitted by this proposal.
    forbidden = ['24Eka6wL.dat', 'Fvix6V0n.dat', '1Bj4oy5Q.dat', 'Wg1a5VJR.dat']
    if payload == (HERE / 'proposed_payload').resolve():
        check('No underlying native quest/header/phase outputs', not any((payload / n).exists() for n in forbidden))
    else:
        for name, expected_hash in protected_quest_hashes.items():
            if (payload / name).exists():
                check('Integrated underlying quest table byte preservation ' + name, builder.sha(payload / name) == expected_hash)
    receipt = {'passed': True, 'checks_count': len(checks), 'checks': checks,
               'payload': str(payload), 'banner_icon_edit_mode': args.allow_banner_icons,
               'frozen_source_sha256': ledger['input_archive_sha256'],
               'tables': [{'stem': s, 'path': str(payload / (s + '.dat')), 'sha256': builder.sha(payload / (s + '.dat')), 'rows': len(after[s])} for s in builder.TABLE_KEYS],
               'manifest_sha256': builder.blob_sha(new_manifest_blob), 'runtime_tested': False,
               'APK_or_runtime_cache_written': False, 'remote_mutations': False}
    Path('S:\\FFBE JP Data Export\\build\\v204-startup-fix\\audit\\content_checks\\EVENT_STATIC_REGRESSION_CHECKS.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ['passed', 'checks_count', 'payload', 'runtime_tested']}))

if __name__ == '__main__':
    main()
