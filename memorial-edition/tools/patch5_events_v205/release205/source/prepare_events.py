"""Prepare only appended event data against literal production Patch5.

No APK assembly, runtime changes, device access, network or publication.
Original records and original banner members remain authoritative.
"""
from pathlib import Path
from collections import Counter, defaultdict
import copy
import hashlib
import json
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / 'audit'
PAYLOAD = ROOT / 'payload'
PATCH = Path(r'T:\Projects\FFBE Patch')
PRODUCTION = PATCH / 'localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk'
CONTENT = PATCH / 'localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Content-Source.apk'
CURRENT = Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction\payload')
GRAPH = PATCH / 'localization-rounds/2026-10-03-native-delivery-v203/delivery_metadata/game_asset_manifest.json'
BASE = PATCH / 'localization-rounds/2026-09-25-download-recovery/base-source'
sys.path.insert(0, str(PATCH / 'story-ports/side-stories/scripts'))
from common import K, FIELDS, rows_bytes, encode, crilayla
from cpk_convert import extend_cpk, read_cpk

PRODUCTION_SHA = '534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
MANIFEST_SHA = 'b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8'
TABLES = ['D2zaT7Ru', 'Nm36woZx', '9Zdr5ap0', 'IL78hX09', 'YW9MUm2H', '91vNbdxg', 'B7LnP2TH', '24Eka6wL', '1Bj4oy5Q', 'Fvix6V0n', 'LM1APs6u', 'YW9MUm2H-legacy', 'bqR4p8SN', 'Wg1a5VJR', '9mS1TPFJ']
KEYS = {'91vNbdxg': ['Lxj5u3WB', '6uIYE15X', 'XFh30CkV', '4SWuwc0M'], 'Wg1a5VJR': ['qo3PECw6', '6v7y3QcJ'], '9mS1TPFJ': ['6uIYE15X', '89EvGKHx', '0G7J2vfD', 'dX0SkK3j', 'pJ56sAEo']}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError('Refuse to replace different prepared bytes: ' + str(path))
    else:
        path.write_bytes(data)

def parse_manifest(data):
    rows = [line.split('\t') for line in data.decode('utf-8').splitlines() if line]
    assert all(len(row) in (3, 4) for row in rows)
    assert len({row[0] for row in rows}) == len(rows)
    return rows

def field(row, name):
    found = [key for key in row if FIELDS.get(key, key) == name]
    assert len(found) == 1, name
    return found[0]

def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    assert sha(PRODUCTION.read_bytes()) == PRODUCTION_SHA
    graph_bytes = GRAPH.read_bytes()
    assert sha(graph_bytes) == MANIFEST_SHA
    graph = json.loads(graph_bytes)
    admitted = {a['path']: a for a in graph['assets'] if a['namespace'] == 'root' and a['path'].startswith('side_stories/')}
    current_manifest = parse_manifest((CURRENT / 'side_stories/manifest.tsv').read_bytes())
    current_by_name = {row[0]: row for row in current_manifest}
    table_provenance = []
    outputs = {}
    logical = {}
    source_blobs = {}
    source_rows = {}
    baselines = {}
    baseline_sources = {}
    primary_fields = {}
    omitted = {'book_id': '1550000', 'map_ids': [], 'entry_ids': [], 'icon_id': '151550000', 'duplicate_scene_proof': []}
    with zipfile.ZipFile(PRODUCTION) as production, zipfile.ZipFile(CONTENT) as content:
        original_manifest_bytes = production.read('assets/side_stories/manifest.tsv')
        original_manifest = parse_manifest(original_manifest_bytes)
        original_by_name = {row[0]: row for row in original_manifest}
        assert len(original_manifest) == 1370
        base_rows = [line.split('\t') for line in production.read('assets/base_delivery.tsv').decode().splitlines() if line.strip()]
        base_by_name = {row[1]: row for row in base_rows if len(row) == 5}
        for stem in TABLES:
            decode_stem = stem.removesuffix('-legacy')
            member = 'assets/side_stories/' + stem + '.dat'
            if member in content.namelist():
                old_blob = content.read(member)
                assert sha(old_blob) == original_by_name[stem + '.dat'][1]
                source = {'archive': str(CONTENT), 'member': member}
            else:
                row = base_by_name[stem + '.dat']
                old_file = BASE / row[0] / '199/199/assets' / row[1]
                old_blob = old_file.read_bytes()
                assert len(old_blob) == int(row[2]) and sha(old_blob) == row[3]
                source = {'file': str(old_file), 'APK_base_descriptor': row}
            new_file = CURRENT / 'side_stories' / (stem + '.dat')
            new_blob = new_file.read_bytes()
            entry = admitted['side_stories/' + stem + '.dat']
            assert sha(new_blob) == entry['sha256'] and len(new_blob) == entry['bytes']
            old_rows = rows_bytes(old_blob, decode_stem)
            new_rows = rows_bytes(new_blob, decode_stem)
            keys = KEYS.get(stem, [next(iter(old_rows[0]))])
            key = lambda row: tuple(str(row[k]) for k in keys)
            assert len({key(row) for row in old_rows}) == len(old_rows), stem
            assert len({key(row) for row in new_rows}) == len(new_rows), stem
            old_ids = {key(row) for row in old_rows}
            appended = [copy.deepcopy(row) for row in new_rows if key(row) not in old_ids]
            if stem == 'Nm36woZx':
                assert not any(row['M9mwe2cu'] == '1550000' for row in appended)
            if stem == '9Zdr5ap0':
                omitted['map_ids'] = [row['vG1hSm79'] for row in appended if row['M9mwe2cu'] == '1550000']
                appended = [row for row in appended if row['M9mwe2cu'] != '1550000']
            if stem == 'IL78hX09':
                type_key, target_key = field(new_rows[0], 'TargetType'), field(new_rows[0], 'TargetId')
                signature = lambda row: (row[type_key], row[target_key], row['tse2kWp6'], row['8aVAUgN5'], row[field(row, 'battle_script_id')])
                existing_signatures = defaultdict(list)
                for row in old_rows:
                    existing_signatures[signature(row)].append(row['VMkv7S9R'])
                duplicates = [row for row in appended if row['M9mwe2cu'] == '1550000']
                assert len(duplicates) == 18
                for row in duplicates:
                    matches = existing_signatures[signature(row)]
                    assert matches, row['VMkv7S9R']
                    omitted['duplicate_scene_proof'].append({'new_entry_id': row['VMkv7S9R'], 'identical_original_entry_ids': matches, 'signature': list(signature(row))})
                omitted['entry_ids'] = [row['VMkv7S9R'] for row in duplicates]
                appended = [row for row in appended if row['M9mwe2cu'] != '1550000']
            if stem == 'LM1APs6u':
                appended = [row for row in appended if row['0HUPxDf1'] != '151550000']
            baselines[stem] = old_rows
            baseline_sources[stem] = {**source, 'sha256': sha(old_blob), 'bytes': len(old_blob)}
            logical[stem] = copy.deepcopy(old_rows) + appended
            source_rows[stem] = new_rows
            source_blobs[stem] = new_blob
            primary_fields[stem] = keys
            new_map = {key(row): row for row in new_rows}
            table_provenance.append({'stem': stem, 'decode_stem': decode_stem, 'table_name': K[decode_stem]['name'], 'candidate_relative_path': 'side_stories/' + stem + '.dat', 'primary_key': keys[0] if len(keys) == 1 else keys, 'primary_key_fields': keys, 'baseline_source': baseline_sources[stem], 'candidate_source': {'file': str(new_file), 'sha256': sha(new_blob), 'bytes': len(new_blob)}, 'baseline_rows': len(old_rows), 'source_rows': len(new_rows), 'ignored_original_row_changes': sum(row != new_map.get(key(row)) for row in old_rows), 'baseline_removed_rows': sum(key(row) not in new_map for row in old_rows), 'original_row_order_preserved': True})

        season = {row['2ShgIRU8']: row for row in logical['D2zaT7Ru']}
        book = {row['M9mwe2cu']: row for row in logical['Nm36woZx']}
        maps = {row['vG1hSm79']: row for row in logical['9Zdr5ap0']}
        parent_repairs = []
        legacy_relation_gaps = {'maps_missing_book': [], 'entries_missing_map': [], 'existing_parent_attribute_mismatches': []}
        original_map_ids = {row['vG1hSm79'] for row in baselines['9Zdr5ap0']}
        original_entry_ids = {row['VMkv7S9R'] for row in baselines['IL78hX09']}
        for row in logical['9Zdr5ap0']:
            if row['vG1hSm79'] in original_map_ids:
                if row['M9mwe2cu'] not in book:
                    legacy_relation_gaps['maps_missing_book'].append({'map_id': row['vG1hSm79'], 'book_id': row['M9mwe2cu']})
                continue
            assert row['M9mwe2cu'] in book
            expected = book[row['M9mwe2cu']]['2ShgIRU8']
            if row['vG1hSm79'] not in original_map_ids and row['2ShgIRU8'] != expected:
                parent_repairs.append({'table': '9Zdr5ap0', 'id': row['vG1hSm79'], 'before': row['2ShgIRU8'], 'after': expected})
                row['2ShgIRU8'] = expected
        for row in logical['IL78hX09']:
            if row['VMkv7S9R'] in original_entry_ids and row['vG1hSm79'] not in maps:
                legacy_relation_gaps['entries_missing_map'].append({'entry_id': row['VMkv7S9R'], 'map_id': row['vG1hSm79']})
                continue
            assert row['vG1hSm79'] in maps
            parent = maps[row['vG1hSm79']]
            if row['VMkv7S9R'] not in original_entry_ids:
                for attr in ('M9mwe2cu', '2ShgIRU8'):
                    if row[attr] != parent[attr]:
                        parent_repairs.append({'table': 'IL78hX09', 'id': row['VMkv7S9R'], 'field': attr, 'before': row[attr], 'after': parent[attr]})
                        row[attr] = parent[attr]
        for row in logical['Nm36woZx']:
            assert row['2ShgIRU8'] in season
        for row in logical['9Zdr5ap0']:
            if row['vG1hSm79'] in original_map_ids:
                continue
            assert row['2ShgIRU8'] == book[row['M9mwe2cu']]['2ShgIRU8']
        for row in logical['IL78hX09']:
            if row['VMkv7S9R'] in original_entry_ids:
                continue
            parent = maps[row['vG1hSm79']]
            assert row['M9mwe2cu'] == parent['M9mwe2cu'] and row['2ShgIRU8'] == parent['2ShgIRU8']

        for info in table_provenance:
            stem = info['stem']
            old_rows = baselines[stem]
            result = logical[stem]
            assert result[:len(old_rows)] == old_rows
            result_blob = source_blobs[stem] if result == source_rows[stem] else encode(result, info['decode_stem'])
            assert rows_bytes(result_blob, info['decode_stem']) == result
            outputs[stem + '.dat'] = result_blob
            added = result[len(old_rows):]
            keys = primary_fields[stem]
            ids = [row[keys[0]] if len(keys) == 1 else [row[k] for k in keys] for row in added]
            info.update({'candidate_bytes': len(result_blob), 'candidate_sha256': sha(result_blob), 'candidate_rows': len(result), 'preserved_original_rows': len(old_rows), 'original_ids': [row[keys[0]] if len(keys) == 1 else [row[k] for k in keys] for row in old_rows], 'added_rows': len(added), 'added_ids': ids, 'reused_corrected203_raw_bytes': result_blob == source_blobs[stem]})

        # Extend literal Patch5 artwork only with new event icon filenames in use.
        old_cpk = content.read('assets/side_stories/spdungeon9.cpk')
        assert sha(old_cpk) == original_by_name['spdungeon9.cpk'][1]
        old_members = read_cpk(old_cpk)[4]
        current_cpk = (CURRENT / 'side_stories/spdungeon9.cpk').read_bytes()
        current_members = read_cpk(current_cpk)[4]
        assert all(current_members.get(name) == data for name, data in old_members.items())
        icon_rows = logical['LM1APs6u'][len(baselines['LM1APs6u']):]
        icon_file_key = field(icon_rows[0], 'file_name')
        needed_names = {row[icon_file_key] for row in icon_rows}
        assert needed_names <= current_members.keys()
        added_members = {name: crilayla(current_members[name]) if current_members[name].startswith(b'CRILAYLA') else current_members[name] for name in needed_names - old_members.keys()}
        new_cpk = extend_cpk(old_cpk, added_members)
        prepared_members = read_cpk(new_cpk)[4]
        assert all(prepared_members[name] == data for name, data in old_members.items())
        assert set(prepared_members) == set(old_members) | set(added_members)
        outputs['spdungeon9.cpk'] = new_cpk
        banner_proof = {'baseline_source': {'archive': str(CONTENT), 'member': 'assets/side_stories/spdungeon9.cpk', 'sha256': sha(old_cpk), 'bytes': len(old_cpk)}, 'corrected_source': {'file': str(CURRENT / 'side_stories/spdungeon9.cpk'), 'sha256': sha(current_cpk), 'bytes': len(current_cpk)}, 'original_member_count': len(old_members), 'original_members_byte_identical': True, 'appended_member_count': len(added_members), 'total_member_count': len(prepared_members), 'omitted_unused_new_members': sorted(set(current_members) - set(prepared_members)), 'appended_members': [{'name': name, 'bytes': len(data), 'sha256': sha(data)} for name, data in sorted(added_members.items())]}

        new_book_ids = [row['M9mwe2cu'] for row in logical['Nm36woZx'][len(baselines['Nm36woZx']):]]
        target_type_key = field(logical['IL78hX09'][0], 'TargetType')
        battle_books = {row['M9mwe2cu'] for row in logical['IL78hX09'] if row[target_type_key] == '0'}
        party_ids = [identifier for identifier in new_book_ids if identifier in battle_books]
        assert len(new_book_ids) == 863 and len(party_ids) == 835
        assert len(logical['9Zdr5ap0']) - len(baselines['9Zdr5ap0']) == 1850
        assert len(logical['IL78hX09']) - len(baselines['IL78hX09']) == 7999

        # Existing retained event resources are admitted by the exact v203 graph.
        # We copy only its 500 event payload files, never its 162 startup assets
        # or other namespaces, and replace only masters/artwork prepared above.
        references = Counter()
        for rows in logical.values():
            for row in rows:
                for value in row.values():
                    if isinstance(value, str):
                        references.update(re.findall(r'[A-Za-z0-9_./-]+\.(?:cpk|acb)', value))
        assets = []
        for source in sorted((CURRENT / 'side_stories').rglob('*')):
            if not source.is_file() or source.name == 'manifest.tsv':
                continue
            name = source.relative_to(CURRENT / 'side_stories').as_posix()
            relative = 'side_stories/' + name
            original_blob = source.read_bytes()
            admission = admitted[relative]
            assert len(original_blob) == admission['bytes'] and sha(original_blob) == admission['sha256']
            blob = outputs.get(name, original_blob)
            destination = PAYLOAD / relative
            put(destination, blob)
            old_row = original_by_name.get(name)
            baseline_sha = old_row[1] if old_row else baseline_sources.get(name.removesuffix('.dat'), {}).get('sha256')
            kind = 'event_table' if name.endswith('.dat') else 'event_banners' if name == 'spdungeon9.cpk' else 'event_audio' if name.endswith('.acb') else 'event_scene_or_resource'
            assets.append({'path': relative, 'relative_path': relative, 'local_path': str(destination), 'bytes': len(blob), 'sha256': sha(blob), 'baseline_sha256': baseline_sha, 'kind': kind, 'source': {'file': str(source), 'bytes': len(original_blob), 'sha256': sha(original_blob)}, 'reused_corrected203_raw_bytes': blob == original_blob, 'direct_table_reference_count': references[name] + (references[relative] if relative != name else 0), 'dependency_reason': 'Retained full-inventory event dependency admitted by exact corrected203 root graph; direct table references recorded, with scene/CRI companion archives indivisible.'})

        asset_by_name = {a['path'].removeprefix('side_stories/'): a for a in assets}
        merged_manifest = copy.deepcopy(original_manifest)
        merged_by_name = {row[0]: row for row in merged_manifest}
        for name, asset in asset_by_name.items():
            if name in merged_by_name:
                row = merged_by_name[name]
                old_hash = row[1]
                accepted = set(filter(None, row[2].split(',')))
                accepted.add(old_hash)
                row[1], row[2] = asset['sha256'], ','.join(sorted(accepted))
            else:
                row = copy.deepcopy(current_by_name[name])
                row[1] = asset['sha256']
                merged_manifest.append(row)
                merged_by_name[name] = row
        manifest_blob = ''.join('\t'.join(row) + '\n' for row in merged_manifest).encode('utf-8')
        put(PAYLOAD / 'side_stories/manifest.tsv', manifest_blob)
        assert set(original_by_name) <= set(merged_by_name)
        for row in original_manifest:
            if row[0] not in asset_by_name:
                assert merged_by_name[row[0]] == row
        for name, asset in asset_by_name.items():
            assert merged_by_name[name][1] == asset['sha256']

    save(AUDIT / 'EVENT_BANNER_PRESERVATION.json', banner_proof)
    report = {'schema': 'ffbe-patch5-events-payload-v1', 'ready': True, 'production_APK': str(PRODUCTION), 'production_APK_sha256': PRODUCTION_SHA, 'production_content_source': str(CONTENT), 'corrected203_manifest_sha256': MANIFEST_SHA, 'assets': assets, 'payload_files': assets, 'table_provenance': table_provenance, 'new_book_ids': new_book_ids, 'added_book_ids': new_book_ids, 'party_book_ids': party_ids, 'scene_only_new_book_ids': [identifier for identifier in new_book_ids if identifier not in battle_books], 'core_added_counts': {'seasons': 3, 'books': 863, 'maps': 1850, 'entries': 7999}, 'original_core_records_changed': 0, 'original_records_preserved': True, 'omitted_duplicate_aggregation': omitted, 'new_child_parent_repairs': parent_repairs, 'parent_child_relationships_verified': True, 'legacy_baseline_relation_gaps_preserved': legacy_relation_gaps, 'side_story_manifest': {'local_path': str(PAYLOAD / 'side_stories/manifest.tsv'), 'path': 'side_stories/manifest.tsv', 'bytes': len(manifest_blob), 'sha256': sha(manifest_blob), 'baseline_sha256': sha(original_manifest_bytes), 'baseline_rows': len(original_manifest), 'rows': len(merged_manifest), 'all_baseline_paths_preserved': True, 'bundled_metadata_excluded_from_assets': True}, 'banner_preservation_report': str(AUDIT / 'EVENT_BANNER_PRESERVATION.json'), 'resource_assets_without_direct_master_filename_reference': [asset['path'] for asset in assets if asset['kind'] in ('event_audio', 'event_scene_or_resource') and asset['direct_table_reference_count'] == 0], 'APK_built': False, 'runtime_changed': False, 'remote_mutations': False}
    save(AUDIT / 'EVENT_PLAN.json', report)
    print(json.dumps({'ready': True, 'payload_files': len(assets), 'payload_bytes': sum(asset['bytes'] for asset in assets), 'new_book_ids': len(new_book_ids), 'party_book_ids': len(party_ids), 'core_added_counts': report['core_added_counts'], 'banner_original_members': banner_proof['original_member_count'], 'banner_appended_members': banner_proof['appended_member_count'], 'banner_unused_new_members_omitted': len(banner_proof['omitted_unused_new_members']), 'resource_assets_without_direct_reference': report['resource_assets_without_direct_master_filename_reference']}, indent=2))

if __name__ == '__main__':
    main()
