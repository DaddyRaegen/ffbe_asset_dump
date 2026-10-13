"""Prepare only the reviewed 206 playback-menu delta against frozen 205.

No APK/runtime/native edits, encounter deletion, asset import, network or publish.
The explicit deferred Vortex families are enabled only by --defer-vortex.
"""
from pathlib import Path
from collections import Counter
import argparse
import copy
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / 'audit'
PAYLOAD = ROOT / 'payload' / 'side_stories'
BASE_ROOT = Path(r'S:\FFBE JP Data Export\build\v205-patch5-events')
BASE = BASE_ROOT / 'payload' / 'side_stories'
APK = BASE_ROOT / 'staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk'
APK_SHA = 'e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'
SOURCE_ROOT = Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2')
LEDGER = SOURCE_ROOT / 'integration_work/native_delivery_correction/event_audit/EVENT_CORRECTION_LEDGER.json'
CATALOG = SOURCE_ROOT / 'catalog_output/event_catalog.json'
REVERIFICATION = SOURCE_ROOT / 'integration_work/native_delivery_correction/event_audit/SOURCE_RECORD_REVERIFICATION.json'
sys.path.insert(0, r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import rows_bytes, encode, readable, FIELDS

TABLE_KEYS = {'D2zaT7Ru': '2ShgIRU8', 'Nm36woZx': 'M9mwe2cu',
              '9Zdr5ap0': 'vG1hSm79', 'IL78hX09': 'VMkv7S9R'}
SEASON = '2ShgIRU8'
BOOK = 'M9mwe2cu'
MAP = 'vG1hSm79'
ENTRY = 'VMkv7S9R'
ORDER = 'Z0EN6jSh'
NAMED_REMOVALS = {'7077', '7299', '1000099'}
GREETING_REMOVALS = {'1700001'}
RESOURCE_PRACTICE = {'1000002', '1000004', '1000005', '1000010', '1000012',
                     '1000013', '1000014', '1000015', '1000035', '1000036'}
TRIAL_CHALLENGE = {'1000237', '1000238', '1000240', '1000241', '1000242',
                   '1000243', '1000246', '1000347'}
CHRONICLE = {'1001215', '1001216', '1001217', '1001218', '1001220', '1001221',
             '1001222', '1001223', '1001226', '1001227', '1001228', '1001229',
             '1001231', '1001234', '1001235', '1001238', '1001239', '1001242', '1001243'}
VORTEX_REMOVALS = RESOURCE_PRACTICE | TRIAL_CHALLENGE | CHRONICLE
RETAINED_AMBIGUOUS = {'1000018', '1000019', '1000025', '1001240', '1001241', '1001244', '1001245'}
EXPECTED_MOVES = {'1000072', '1000089', '1000093', '1000098', '1000103', '1000108',
                  '1000113', '1000118', '1000123', '1000133', '1000138', '1000143',
                  '1000148', '1000154', '1000159', '1000165', '1000170', '1000191',
                  '1000220', '1000986'}
REFERENCES = [
 {'id': 'official_chronicle_definition', 'url': 'https://www.jp.square-enix.com/FFBE/blog/2020/12/update20201228.html',
  'title': 'FFBE development communication 2020-12-28', 'publisher': 'Square Enix', 'accessed': '2026-10-04',
  'supports': 'Defines Chronicle Battles as permanent content, explicitly distinct from limited-time events; developer article section Chronicle Battles.'},
 {'id': 'official_chronicle_ff7', 'url': 'https://www.jp.square-enix.com/FFBE/FFVIIR/',
  'title': 'FFBE x FFVII REMAKE 2021 announcement', 'publisher': 'Square Enix', 'accessed': '2026-10-04',
  'supports': 'FFVII Chronicle release dates end in permanent availability, contrasted with the bounded series event and raid dates.'},
 {'id': 'official_cryst_utility', 'url': 'https://www.jp.square-enix.com/FFBE/blog/2020/12/update20201207.html',
  'title': 'FFBE development communication 2020-12-07', 'publisher': 'Square Enix', 'accessed': '2026-10-04',
  'supports': 'Ability awakening materials are obtained from Vortex > Enhance > Chamber of Crysts.'},
 {'id': 'official_experience_utility', 'url': 'https://www.jp.square-enix.com/FFBE/blog/2020/11/unit-5to6.html',
  'title': 'Awakening a five-star unit to six stars', 'publisher': 'Square Enix', 'accessed': '2026-10-04',
  'supports': 'Chamber of Experience is an ordinary unit leveling route under Vortex > Enhance.'},
 {'id': 'official_practice_categories', 'url': 'https://www.jp.square-enix.com/FFBE/blog/2022/07/questrepeat.html',
  'title': 'Quest repeat farming function', 'publisher': 'Square Enix', 'accessed': '2026-10-04',
  'supports': 'Identifies Training the Soul, Chamber of Blue Magic and Chamber of Arms as distinct quest categories; does not alone establish dates.'},
 {'id': 'official_arms_party', 'url': 'https://www.jp.square-enix.com/FFBE/blog/2021/03/update20210305.html',
  'title': 'Version 6.3.2 update content', 'publisher': 'Square Enix', 'accessed': '2026-10-04',
  'supports': 'Identifies Chamber of Arms as a separate content system with special party formation and temporary suspension.'},
 {'id': 'secondary_vortex_taxonomy', 'url': 'https://altema.jp/ffbe/jigennnohazama-91',
  'title': 'Vortex content overview', 'publisher': 'Altema (secondary)', 'accessed': '2026-10-04',
  'supports': 'Distinguishes utility, special and nemesis routes from limited-time events; Chronicle and weekly challenge containers still occupied the live Event tab. This is secondary corroboration, not an executable field rule.'},
 {'id': 'secondary_weekly_challenges', 'url': 'https://exvius.fandom.com/wiki/Chamber_of_Challenges',
  'title': 'Chamber of Challenges', 'publisher': 'FFBE Wiki (secondary)', 'accessed': '2026-10-04',
  'supports': 'Weekly rotating challenge family, not a particular marketed story or collaboration event. Raw mission subtype8 independently distinguishes this challenge type.'},
 {'id': 'secondary_resource_utilities', 'url': 'https://exvius.fandom.com/wiki/Beginner%27s_guide',
  'title': 'FFBE beginner guide', 'publisher': 'FFBE Wiki (secondary)', 'accessed': '2026-10-04',
  'supports': 'Creation, Experience and Riches are ordinary Enhance farming routes. Reusable utility-family identity is inferred from official raw area/mission identities and corroborating gameplay taxonomy.'},
]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def pin(path):
    blob = path.read_bytes()
    return {'local_path': str(path), 'bytes': len(blob), 'sha256': sha(blob)}

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def numeric(values):
    return sorted(values, key=int)

def reason(book_id):
    if book_id in NAMED_REMOVALS:
        return 'named_user_removal'
    if book_id in GREETING_REMOVALS:
        return 'deferred_greeting_promotion'
    if book_id in RESOURCE_PRACTICE:
        return 'deferred_vortex_utility_practice'
    if book_id in TRIAL_CHALLENGE:
        return 'deferred_vortex_trial_challenge_family'
    if book_id in CHRONICLE:
        return 'deferred_permanent_chronicle_family'
    raise ValueError(book_id)

def evidence_for(book_id, book, review, catalog_by_id):
    data = {'book_id': book_id, 'name': readable(book)['name'], 'baseline_season_id': book[SEASON],
            'source_review': copy.deepcopy(review.get(book_id)), 'source_records': []}
    if book_id not in review:
        assert book_id == '7299'
        data['criterion'] = 'Explicit local Party Test book requested by user; no original regional event source.'
        return data
    for catalog_id in review[book_id]['catalog_ids']:
        source = catalog_by_id[catalog_id]
        data['source_records'].append({key: copy.deepcopy(source.get(key)) for key in [
            'catalog_id', 'server', 'original_id', 'display_name', 'name_original', 'world_id',
            'type', 'subtype', 'mission_subtypes', 'mission_ids', 'dungeon_ids', 'classification_evidence',
            'source_record_refs', 'source_paths', 'name_provenance', 'raw_record']})
    if book_id in EXPECTED_MOVES:
        assert all(e['type'] == 'story_event' for e in data['source_records']), book_id
        data['criterion'] = 'Raw dedicated world10 or legacy mission subtype3; all regional source records qualify as story_event.'
    elif book_id in CHRONICLE:
        assert all('クロニクル' in e['name_original'] for e in data['source_records']), book_id
        data['criterion'] = 'Exact raw Chronicle family IDs plus official permanent-content definition. The exclusion is an editorial event-menu boundary, not a live-game field rewrite.'
        data['reference_ids'] = ['official_chronicle_definition', 'official_chronicle_ff7']
    elif book_id in RESOURCE_PRACTICE:
        data['criterion'] = 'Exact ordinary utility/practice area and mission family; inferred non-event menu boundary using source identity and official/secondary Vortex category corroboration. World2 alone is insufficient.'
        data['reference_ids'] = ['official_cryst_utility', 'official_experience_utility', 'official_practice_categories', 'secondary_resource_utilities', 'secondary_vortex_taxonomy']
    elif book_id in TRIAL_CHALLENGE:
        data['criterion'] = 'Exact reusable trial/challenge family; explicit source area identity. Weekly challenges are recurring Vortex-system content, not claimed never scheduled.'
        data['reference_ids'] = ['official_arms_party', 'secondary_weekly_challenges', 'secondary_vortex_taxonomy']
    elif book_id == '1700001':
        data['criterion'] = 'Distinct sourcearea700 preview / fifth-anniversary greeting puppet show; separate non-event greeting menu deferred by root scope instruction.'
    elif book_id in RETAINED_AMBIGUOUS:
        data['criterion'] = 'Retained: source data does not prove this particular treasure, anniversary or strong-foe route is a permanent/non-event system. Do not infer exclusion from world2 or title similarity.'
    else:
        data['criterion'] = 'Exact named book and regional source ID requested by user; do not remove other title substring matches.'
    return data

def relationship_observations(tables):
    """Record inherited native-table aliases/orphans without repairing them."""
    seasons = {r[SEASON] for r in tables['D2zaT7Ru']}
    books = {r[BOOK]: r for r in tables['Nm36woZx']}
    maps = {r[MAP]: r for r in tables['9Zdr5ap0']}
    observations = []
    for row in tables['Nm36woZx']:
        if row[SEASON] not in seasons:
            observations.append({'stem': 'Nm36woZx', 'id': row[BOOK], 'type': 'book_missing_season', 'season_id': row[SEASON]})
    for row in tables['9Zdr5ap0']:
        book = books.get(row[BOOK])
        if not book:
            observations.append({'stem': '9Zdr5ap0', 'id': row[MAP], 'type': 'map_missing_book', 'book_id': row[BOOK]})
        elif row[SEASON] != book[SEASON]:
            observations.append({'stem': '9Zdr5ap0', 'id': row[MAP], 'type': 'map_season_alias', 'book_id': row[BOOK], 'map_season_id': row[SEASON], 'book_season_id': book[SEASON]})
    for row in tables['IL78hX09']:
        book, map_row = books.get(row[BOOK]), maps.get(row[MAP])
        if not book:
            observations.append({'stem': 'IL78hX09', 'id': row[ENTRY], 'type': 'entry_missing_book', 'book_id': row[BOOK]})
        elif row[SEASON] != book[SEASON]:
            observations.append({'stem': 'IL78hX09', 'id': row[ENTRY], 'type': 'entry_book_season_alias', 'book_id': row[BOOK], 'entry_season_id': row[SEASON], 'book_season_id': book[SEASON]})
        if not map_row:
            observations.append({'stem': 'IL78hX09', 'id': row[ENTRY], 'type': 'entry_missing_map', 'map_id': row[MAP]})
        else:
            if row[BOOK] != map_row[BOOK]:
                observations.append({'stem': 'IL78hX09', 'id': row[ENTRY], 'type': 'entry_map_book_alias', 'map_id': row[MAP], 'entry_book_id': row[BOOK], 'map_book_id': map_row[BOOK]})
            if row[SEASON] != map_row[SEASON]:
                observations.append({'stem': 'IL78hX09', 'id': row[ENTRY], 'type': 'entry_map_season_alias', 'map_id': row[MAP], 'entry_season_id': row[SEASON], 'map_season_id': map_row[SEASON]})
    return observations

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--defer-vortex', action='store_true', help='Apply the exact reviewed37 family IDs; never classify by title automatically.')
    args = parser.parse_args()
    AUDIT.mkdir(parents=True, exist_ok=True)
    assert sha(APK.read_bytes()) == APK_SHA
    with zipfile.ZipFile(APK) as apk:
        manifest_blob = apk.read('assets/side_stories/manifest.tsv')
        catalog_blob = apk.read('assets/content_delivery.tsv')
    manifest = [line.split('\t') for line in manifest_blob.decode('utf-8').splitlines() if line]
    descriptors = {row[0]: row for row in manifest}
    assert len(manifest) == 1857
    catalog_lines = [line for line in catalog_blob.decode('utf-8').splitlines() if line]
    assert catalog_lines[0] == 'ffbe-content-v1' and len(catalog_lines[1:]) == 1898
    catalog_descriptors = {line.split('\t')[0]: line.split('\t') for line in catalog_lines[1:]}
    source_blobs = {stem: (BASE / (stem + '.dat')).read_bytes() for stem in TABLE_KEYS}
    originals = {stem: rows_bytes(blob, stem) for stem, blob in source_blobs.items()}
    assert [len(originals[s]) for s in TABLE_KEYS] == [11, 1045, 3585, 14988]
    for stem, blob in source_blobs.items():
        assert sha(blob) == descriptors[stem + '.dat'][1]
        assert len(blob) == int(catalog_descriptors['side_stories/' + stem + '.dat'][2])
        key = TABLE_KEYS[stem]
        assert len({row[key] for row in originals[stem]}) == len(originals[stem])
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    review = {row['book_id']: row for row in ledger['book_audit']}
    catalog_by_id = {row['catalog_id']: row for row in catalog['events']}
    books = {row[BOOK]: row for row in originals['Nm36woZx']}
    moved = {row[BOOK] for row in originals['Nm36woZx'] if row[SEASON] == '91'}
    assert moved == EXPECTED_MOVES
    assert len(VORTEX_REMOVALS) == 37
    assert all(books[id][SEASON] == '71' for id in VORTEX_REMOVALS)
    excluded = NAMED_REMOVALS | GREETING_REMOVALS | (VORTEX_REMOVALS if args.defer_vortex else set())
    assert not moved & excluded
    involved = moved | excluded | VORTEX_REMOVALS | RETAINED_AMBIGUOUS
    source_book_reviews = [evidence_for(id, books[id], review, catalog_by_id) for id in numeric(involved)]
    event71_decisions = []
    for book_id in numeric({row[BOOK] for row in originals['Nm36woZx'] if row[SEASON] == '71'}):
        source_review = review.get(book_id)
        event71_decisions.append({'book_id': book_id, 'name': readable(books[book_id])['name'],
            'decision': 'exclude_UI' if book_id in excluded else 'retain',
            'reason': reason(book_id) if book_id in excluded else 'No reviewed proof that this exact regional event route belongs to an excluded utility/trial family; no world2-only or name-only deletion.',
            'catalog_ids': source_review.get('catalog_ids', []) if source_review else [],
            'source_areas': source_review.get('source_areas', []) if source_review else [],
            'regional_stage_ids': source_review.get('regional_stage_ids', []) if source_review else [],
            'permanence_independently_established': book_id in CHRONICLE,
            'actual_event_dates_or_server_mechanics_claimed': False})
    event71_path = AUDIT / 'EVENT71_DECISION_LEDGER.json'
    save(event71_path, {'source_catalog': pin(CATALOG), 'source_book_ledger': pin(LEDGER), 'before_book_count': 415,
                       'excluded_book_count': sum(row['decision'] == 'exclude_UI' for row in event71_decisions),
                       'retained_book_count': sum(row['decision'] == 'retain' for row in event71_decisions),
                       'policy': 'Explicit approved source families only; raw normal_event/world2 is a broad Vortex container and does not establish a timed event or a permanent system by itself. Retention preserves baseline content where no exact exclusion is source-qualified.',
                       'books': event71_decisions})
    candidate = copy.deepcopy(originals)
    operations = {stem: [] for stem in TABLE_KEYS}
    deferred = []
    for stem in ['Nm36woZx', '9Zdr5ap0', 'IL78hX09']:
        key = TABLE_KEYS[stem]
        output = []
        for row in candidate[stem]:
            book_id = row[BOOK]
            if book_id in excluded:
                op = {'op': 'remove', 'id': row[key], 'book_id': book_id, 'reason': reason(book_id), 'before': copy.deepcopy(row)}
                operations[stem].append(op)
                deferred.append({'stem': stem, 'primary_key': key, **copy.deepcopy(op)})
                continue
            if book_id in moved:
                assert row[SEASON] == '91', (stem, row[key])
                operations[stem].append({'op': 'update', 'id': row[key], 'book_id': book_id, 'reason': 'archive_story_route',
                                         'fields': {SEASON: {'before': '91', 'after': '70'}}})
                row[SEASON] = '70'
            output.append(row)
        candidate[stem] = output
    retained_story = [row for row in candidate['Nm36woZx'] if row[SEASON] == '70' and row[BOOK] not in {'7074', '7075'}]
    max_order = max(int(row[ORDER]) for row in retained_story)
    assert max_order == 1506
    new_orders = {'7074': str(max_order + 1), '7075': str(max_order + 2)}
    for row in candidate['Nm36woZx']:
        if row[BOOK] in new_orders:
            before = row[ORDER]
            assert before == {'7074': '2', '7075': '3'}[row[BOOK]]
            row[ORDER] = new_orders[row[BOOK]]
            operations['Nm36woZx'].append({'op': 'update', 'id': row[BOOK], 'book_id': row[BOOK], 'reason': 'revival_after_all_story_books',
                                         'fields': {ORDER: {'before': before, 'after': row[ORDER]}}})
    empty_seasons = {'91', '93'}
    output_seasons = []
    for row in candidate['D2zaT7Ru']:
        if row[SEASON] in empty_seasons:
            assert not any(book[SEASON] == row[SEASON] for book in candidate['Nm36woZx'])
            op = {'op': 'remove', 'id': row[SEASON], 'reason': 'empty_menu_section', 'before': copy.deepcopy(row)}
            operations['D2zaT7Ru'].append(op)
            deferred.append({'stem': 'D2zaT7Ru', 'primary_key': SEASON, **copy.deepcopy(op)})
        else:
            output_seasons.append(row)
    candidate['D2zaT7Ru'] = output_seasons
    # Exact delta replay; no row insertion, physical reorder, or unlisted field mutation.
    for stem, key in TABLE_KEYS.items():
        expected = copy.deepcopy(originals[stem])
        by_id = {row[key]: row for row in expected}
        removed = set()
        for op in operations[stem]:
            if op['op'] == 'remove':
                assert by_id[op['id']] == op['before']
                removed.add(op['id'])
            else:
                for field, diff in op['fields'].items():
                    assert by_id[op['id']][field] == diff['before']
                    by_id[op['id']][field] = diff['after']
        expected = [row for row in expected if row[key] not in removed]
        assert candidate[stem] == expected
    books_after = {r[BOOK]: r for r in candidate['Nm36woZx']}
    maps_after = {r[MAP]: r for r in candidate['9Zdr5ap0']}
    for row in candidate['9Zdr5ap0']:
        if row[BOOK] in moved:
            assert row[SEASON] == books_after[row[BOOK]][SEASON] == '70'
    for row in candidate['IL78hX09']:
        if row[BOOK] in moved:
            assert row[BOOK] == maps_after[row[MAP]][BOOK]
            assert row[SEASON] == books_after[row[BOOK]][SEASON] == maps_after[row[MAP]][SEASON] == '70'
    inherited_relationships = relationship_observations(originals)
    after_relationships = relationship_observations(candidate)
    before_signatures = {json.dumps(row, sort_keys=True) for row in inherited_relationships}
    assert all(json.dumps(row, sort_keys=True) in before_signatures for row in after_relationships), 'New relationship observation introduced'
    table_changes = []
    for stem, rows in candidate.items():
        blob = encode(rows, stem)
        assert rows_bytes(blob, stem) == rows
        file = PAYLOAD / (stem + '.dat')
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(blob)
        before_descriptor = descriptors[stem + '.dat']
        after_descriptor = copy.deepcopy(before_descriptor)
        after_descriptor[1] = sha(blob)
        table_changes.append({'stem': stem, 'path': 'side_stories/' + stem + '.dat', 'local_path': str(file),
                              'bytes': len(blob), 'sha256': sha(blob),
                              'baseline': {'local_path': str(BASE / (stem + '.dat')), 'bytes': len(source_blobs[stem]),
                                           'sha256': sha(source_blobs[stem]), 'primary_key': TABLE_KEYS[stem]},
                              'before_rows': len(originals[stem]), 'after_rows': len(rows),
                              'operations': operations[stem], 'manifest_before': before_descriptor, 'manifest_after': after_descriptor})
    excluded_books = []
    for id in numeric(excluded):
        book = books[id]
        excluded_books.append({'book_id': id, 'name': readable(book)['name'], 'season_id': book[SEASON], 'reason': reason(id),
                               'map_ids': numeric({r[MAP] for r in originals['9Zdr5ap0'] if r[BOOK] == id}),
                               'entry_ids': numeric({r[ENTRY] for r in originals['IL78hX09'] if r[BOOK] == id})})
    count = {stem: {'before': len(originals[stem]), 'after': len(candidate[stem]),
                    'removed': sum(op['op'] == 'remove' for op in operations[stem]),
                    'updated': sum(op['op'] == 'update' for op in operations[stem])} for stem in TABLE_KEYS}
    before_sections = dict(Counter(row[SEASON] for row in originals['Nm36woZx']))
    after_sections = dict(Counter(row[SEASON] for row in candidate['Nm36woZx']))
    baseline = {'version': 205, 'APK': {**pin(APK), 'sha256': APK_SHA},
                'side_manifest': {'APK_member': 'assets/side_stories/manifest.tsv', 'bytes': len(manifest_blob), 'sha256': sha(manifest_blob), 'rows': len(manifest)},
                'content_delivery': {'APK_member': 'assets/content_delivery.tsv', 'bytes': len(catalog_blob), 'sha256': sha(catalog_blob), 'rows': 1898}}
    ledger_path = AUDIT / 'DEFERRED_UI_RECORDS.json'
    save(ledger_path, {'schema_version': 1, 'baseline': baseline, 'excluded_books': excluded_books, 'records': deferred,
                      'restore_policy': 'Full exact205 UI records retained for later separately authorized Vortex/non-event section. Underlying mission/dungeon/battle/story/resource tables, catalog paths and assets remain present. No restore is activated in206.'})
    relationship_path = AUDIT / 'INHERITED_PLAYBACK_RELATIONSHIPS.json'
    save(relationship_path, {'baseline': baseline, 'before_count': len(inherited_relationships), 'after_count': len(after_relationships),
                            'new_observations': [], 'observations': after_relationships,
                            'interpretation': 'Preserved205/P5 native playback relationships include season aliases and unused/orphaned UI rows. This audit does not infer those are runtime failures. No unrelated repair or normalization is authorized; moved20 hierarchies are all explicitly consistent.'})
    plan = {'schema_version': 1, 'version': 206, 'ready_for_catalog': bool(args.defer_vortex),
            'scope': 'Only authorized event-menu redistribution, exact named removals, deferred proven non-event families and Revival numeric display-order changes against205. Banners are a separate root BANNER_PLAN.',
            'baseline': baseline, 'source_provenance': {'regional_catalog': pin(CATALOG), 'corrected203_book_ledger': pin(LEDGER), 'raw_record_reverification': pin(REVERIFICATION)},
            'moved_book_ids': numeric(moved), 'moved_from_season_id': '91', 'moved_to_season_id': '70',
            'named_removed_book_ids': numeric(NAMED_REMOVALS), 'deferred_greeting_book_ids': numeric(GREETING_REMOVALS),
            'deferred_vortex_book_ids': numeric(VORTEX_REMOVALS if args.defer_vortex else set()),
            'excluded_book_ids': numeric(excluded), 'excluded_books': excluded_books,
            'removed_season_ids': numeric(empty_seasons), 'revival_orders': new_orders,
            'order_proof': pin(AUDIT / 'NATIVE_EVENT_MENU_ORDER.json'),
            'table_changes': table_changes, 'counts': count,
            'category_book_counts': {'before': before_sections, 'after': after_sections},
            'source_book_reviews': source_book_reviews, 'references': REFERENCES,
            'deferred_ui_records': pin(ledger_path),
            'inherited_playback_relationships': pin(relationship_path),
            'event71_decision_ledger': pin(event71_path),
            'retained_ambiguous_book_ids': numeric(RETAINED_AMBIGUOUS),
            'retained_ambiguity_reason': 'Do not hide possible dated treasure/anniversary events or later strong-foe/Chronicle-adjacent battles from broad world2, title similarity or unsupported permanence assumptions.',
            'protected_title_variant': {'book_id': '7067', 'name': 'Christmas Unit Introductions', 'reason': 'Different sourcearea310; outside exact named UnitIntroQuest area756 removal. Mixed scene/battle route retained.'},
            'guarantees': {'new_UI_IDs': 0, 'physical_retained_row_order_preserved': True, 'encounter_tables_changed': False,
                           'catalog_path_removals': 0, 'asset_deletions': 0, 'runtime_hook_edits': False,
                           'native_library_edits': False, 'banner_edits_by_this_script': False},
            'remaining_limits': ['Host table and source checks do not prove phone navigation, rendering, battles, saves or server-dependent mechanics.',
                                 'Non-event family boundary is a reviewed source-based editorial decision; broad live Vortex world2 classification is not a deletion rule.',
                                 'Main story and JP Memories preserved. No new Vortex section or additional content imported.']}
    save(AUDIT / 'CLEANUP_PLAN.json', plan)
    save(AUDIT / 'CLEANUP_PREPARATION_REPORT.json', {'passed': True, 'ready_for_catalog': plan['ready_for_catalog'],
         'counts': count, 'category_book_counts': plan['category_book_counts'], 'table_changes': [{k:v for k,v in t.items() if k != 'operations'} for t in table_changes],
         'plan': pin(AUDIT / 'CLEANUP_PLAN.json'), 'source': pin(Path(__file__))})
    print(json.dumps({'passed': True, 'ready_for_catalog': plan['ready_for_catalog'], 'counts': count,
                      'category_book_counts': plan['category_book_counts'], 'plan': str(AUDIT / 'CLEANUP_PLAN.json')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
