"""Validate the master identity registry and every restored regional asset."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from PIL import Image
from build_unit_master import build_master
from recover_assets import save, verify_bytes
from recover_unit_collisions import REPORT, member_matches, required_members, source_path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(repo, dump=None):
    manifest = json.loads((repo / REPORT).read_text(encoding='utf-8'))
    decisions = json.loads((repo / 'catalog/unit_identity_decisions.json').read_text(encoding='utf-8'))
    sources = json.loads((repo / 'catalog/unit_identity_sources.json').read_text(encoding='utf-8'))
    master = json.loads((repo / 'catalog/unit_master.json').read_text(encoding='utf-8'))
    legacy = json.loads((repo / 'catalog/units.json').read_text(encoding='utf-8'))
    series_path = repo / 'catalog/series_sources.json'
    series_sources = json.loads(series_path.read_text(encoding='utf-8')) if series_path.exists() else None
    expected_master = build_master(sources, decisions, legacy, manifest, series_sources=series_sources)
    assert master == expected_master, 'master registry differs from its reviewed inputs'
    collisions = {row['original_id']: row for row in decisions['collisions']}
    assert len(collisions) == len(decisions['collisions']), 'duplicate collision decisions'
    ids = [row['master_id'] for row in master['units']]
    assert len(ids) == len(set(ids)), 'duplicate master IDs'
    aliases = [(i['server'], i['original_id']) for u in master['units'] for i in u['identities']]
    expected = {(s, row['original_id']) for s in ('GL', 'JP')
                for row in sources['sources'][s]['rows']}
    assert len(aliases) == len(set(aliases)), 'duplicate regional alias'
    assert set(aliases) == expected, 'master/source coverage mismatch'
    by_master = {row['master_id']: row for row in master['units']}
    for row in master['units']:
        assert row['regions'] == [i['server'] for i in row['identities']]
        assert all(i['original_id'] == row['original_id'] for i in row['identities'])
    for uid, decision in collisions.items():
        for server in ('GL', 'JP'):
            row = by_master[f'unit:{server}:{uid}']
            assert row['original_id'] == uid
            assert row['regions'] == [server]
    paths = [row['destination'] for row in manifest['files']]
    assert len(paths) == len(set(paths)), 'duplicate asset destination'
    archive_hashes = {a['source']: a['sha256'] for a in manifest['archives']}
    assert len(archive_hashes) == len(manifest['archives']), 'duplicate archive provenance'
    bundle_files = defaultdict(dict)
    bundle_paths = defaultdict(set)
    for record in manifest['files']:
        server, uid, name = record['server'], record['original_id'], record['member']
        assert uid in collisions and member_matches(name, uid)
        assert record['source'] == collisions[uid]['asset_sources'][server]
        assert record['source_sha256'] == archive_hashes[record['source']], 'archive provenance mismatch'
        path = (repo / record['destination']).resolve()
        assert path.is_relative_to(repo.resolve()), 'asset path escapes repository'
        assert record['destination'].startswith(f'regional_units/{server.lower()}/{uid}/')
        assert path.name == name, 'native member renamed'
        data = path.read_bytes()
        assert len(data) == record['bytes'] and hashlib.sha256(data).hexdigest() == record['sha256'], record['destination']
        verify_bytes(name, data)
        bundle_files[(server, uid)][name] = path
        bundle_paths[(server, uid)].add(record['destination'])
    assert set(bundle_files) == {(s, i) for i in collisions for s in ('GL', 'JP')}
    assert len(manifest['bundles']) == len(bundle_files), 'bundle coverage mismatch'
    seen_bundles = set()
    for bundle in manifest['bundles']:
        key = (bundle['server'], bundle['original_id'])
        assert key not in seen_bundles and key in bundle_files, 'duplicate or unknown bundle'
        seen_bundles.add(key)
        assert bundle['source'] == collisions[key[1]]['asset_sources'][key[0]]
        assert bundle['source_sha256'] == archive_hashes[bundle['source']]
        assert len(bundle['asset_files']) == len(set(bundle['asset_files']))
        assert set(bundle['asset_files']) == bundle_paths[key], 'bundle member list mismatch'
    frames_checked = sequences_checked = parts_checked = 0
    for (server, uid), files in sorted(bundle_files.items()):
        assert required_members(uid) <= set(files), f'missing core assets: {server}:{uid}'
        listed = by_master[f'unit:{server}:{uid}']['assets']
        for key, name in [('sprite_sheet', f'unit_anime_{uid}.png'),
                          ('frame_data', f'unit_cgg_{uid}.csv'),
                          ('idle_animation', f'unit_idle_cgs_{uid}.csv')]:
            assert (repo / listed[key]).resolve() == files[name]
        atlas = {}
        for name, path in files.items():
            if name.startswith(f'unit_anime_{uid}') and name.endswith('.png'):
                suffix = name[len(f'unit_anime_{uid}'):-4]
                page = int(suffix.lstrip('_')) if suffix else 0
                with Image.open(path) as image:
                    image.load()
                    atlas[page] = image.size
        cgg = files[f'unit_cgg_{uid}.csv'].read_text(encoding='utf-8-sig').splitlines()
        for name, path in files.items():
            if '_cgs_' not in name or not name.endswith('.csv'):
                continue
            sequences_checked += 1
            for line in path.read_text(encoding='utf-8-sig').splitlines():
                if line.strip():
                    frame = int(line.split(',')[0])
                    assert 0 <= frame < len(cgg), f'invalid frame {server}:{uid} {name}:{frame}'
                    frames_checked += 1
        for number, line in enumerate(cgg):
            values = [int(x) for x in line.strip().split(',') if x]
            assert len(values) >= 2, f'invalid CGG row {server}:{uid}:{number}'
            count, values = values[1], values[2:]
            if not count:
                continue
            assert len(values) % count == 0
            stride = len(values) // count
            assert stride >= 10
            for start in range(0, len(values), stride):
                part = values[start:start + stride]
                page = part[10] if stride > 10 else 0
                assert page in atlas, f'missing texture page {server}:{uid}:{page}'
                x, y, w, h = part[6:10]
                width, height = atlas[page]
                assert min(x, y, w, h) >= 0 and x + w <= width and y + h <= height, f'atlas bounds {server}:{uid}:{number}'
                parts_checked += 1
    verified_sources = 0
    if dump:
        for archive in manifest['archives']:
            assert digest(source_path(dump, archive['source'])) == archive['sha256']
            verified_sources += 1
        for source in sources['sources'].values():
            assert digest(Path(source['path'])) == source['sha256'], source['path']
            verified_sources += 1
        if series_sources:
            for source in series_sources['sources'].values():
                assert digest(Path(source['path'])) == source['sha256'], source['path']
                verified_sources += 1
    return {'status': 'passed', 'master_ids': len(ids), 'regional_aliases': len(aliases),
            'collision_form_ids': len(collisions), 'restored_bundles': len(bundle_files),
            'restored_files': len(paths), 'bytes': sum(x['bytes'] for x in manifest['files']),
            'sequences_checked': sequences_checked, 'frame_references_checked': frames_checked,
            'atlas_parts_checked': parts_checked, 'source_files_sha256_verified': verified_sources,
            'legacy_matches': dict(Counter(str(r.get('matches_legacy')) for r in manifest['files'])),
            'errors': []}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--dump', type=Path, help='Also verify original DAT and CPK source hashes')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = validate(args.repo.resolve(), args.dump)
    if args.output:
        save(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
