"""Audit data.json base IDs, regional forms, series provenance and asset paths."""
import argparse
from collections import Counter
import json
from pathlib import Path

from build_unit_lookup import build_lookup, read_json


def validate_lookup(repo, lookup, master, legacy):
    assert build_lookup(legacy, master, lookup) == lookup, 'Lookup differs from generated identity/series fields'
    expected = {(i['server'], i['original_id']): (u, i)
                for u in master['units'] for i in u['identities']}
    expected_bases = {i['source_unit_id'] for u in master['units'] for i in u['identities']}
    assert expected_bases <= set(lookup), 'Missing sourced base IDs'
    seen, paths = set(), set()
    for base, row in lookup.items():
        assert base.isdigit(), 'Non-numeric legacy lookup key'
        for identity in row.get('identities', []):
            assert identity['original_id'] == base and identity['source_unit_id'] == base
            server = identity['server']
            for form in identity['forms']:
                alias = (server, form['original_id'])
                assert alias in expected and alias not in seen, 'Missing/duplicate regional form'
                seen.add(alias)
                unit, source_identity = expected[alias]
                assert source_identity['source_unit_id'] == base
                assert form['master_id'] == unit['master_id']
                assert form['assets'] == unit['assets']
                for key in ('game_id', 'series', 'game_title', 'series_status', 'series_provenance'):
                    assert form[key] == source_identity[key], f'Series provenance mismatch: {alias}'
                for relative in form['assets']['asset_files']:
                    path = (repo / relative).resolve()
                    assert path.is_relative_to(repo.resolve()), 'Asset escapes repository'
                    paths.add(path)
        if row.get('identity_status') == 'regional_collision':
            assert row['master_id'] is None and len(row['identities']) == 2
    assert seen == set(expected), 'Regional form coverage mismatch'
    missing = [str(p) for p in paths if not p.is_file()]
    assert not missing, f'Missing asset paths: {missing[:5]}'
    legacy_changes = [{'original_id': uid, 'field': key}
                      for uid, original in legacy.items() for key, value in original.items()
                      if lookup.get(uid, {}).get(key) != value]
    sourced = [lookup[i] for i in expected_bases]
    return {
        'status': 'passed', 'lookup_rows': len(lookup), 'sourced_base_ids': len(expected_bases),
        'preserved_legacy_rows': len(legacy), 'legacy_display_field_changes': legacy_changes,
        'custom_rows_without_source': sorted(set(lookup) - expected_bases),
        'regional_form_aliases': len(seen), 'unique_resolved_asset_paths': len(paths),
        'collision_base_ids': [i for i, r in lookup.items() if r.get('identity_status') == 'regional_collision'],
        'known_series_base_rows': sum(r.get('series_status') == 'known' for r in sourced),
        'unknown_series_base_ids': [i for i in sorted(expected_bases) if lookup[i].get('series_status') != 'known'],
        'base_rows_by_series': dict(sorted(Counter(r.get('series') or 'Unknown' for r in sourced).items())),
        'master_series_coverage': master['coverage']['series'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--lookup', type=Path)
    parser.add_argument('--master', type=Path)
    parser.add_argument('--legacy-snapshot', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = validate_lookup(args.repo.resolve(), read_json(args.lookup or args.repo / 'data.json'),
                             read_json(args.master or args.repo / 'catalog/unit_master.json'),
                             read_json(args.legacy_snapshot or args.repo / 'catalog/legacy_unit_lookup.json'))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('base_rows_by_series', 'master_series_coverage')}, indent=2))


if __name__ == '__main__':
    main()
