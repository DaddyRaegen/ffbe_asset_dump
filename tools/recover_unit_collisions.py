"""Restore reviewed GL/JP unit bundles without altering legacy or source assets.

Each reviewed identity pins one CPK archive. All files for that form come from
that archive, including the sheet, frame data, sequences, icons and extra pages.
This matters because GL archives also contain JP units at colliding native IDs.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

from cpk import Cpk
from recover_assets import category, extract_archive, safe_name, save, verify_bytes

REPORT = 'reports/2026-10-02-unit-identities/asset-manifest.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def member_matches(name, original_id):
    return name.startswith('unit_') and bool(re.search(
        r'_' + re.escape(original_id) + r'(?=[_.])', name))


def required_members(original_id):
    return {f'unit_anime_{original_id}.png', f'unit_cgg_{original_id}.csv',
            f'unit_idle_cgs_{original_id}.csv'}


def source_path(dump, source):
    path = (dump / source).resolve()
    if not path.is_relative_to(dump.resolve()):
        raise ValueError('archive source escapes dump')
    return path


def recover(repo, dump, work, extractor, legacy_repo=None):
    decisions = json.loads((repo / 'catalog/unit_identity_decisions.json').read_text(encoding='utf-8'))
    grouped = defaultdict(list)
    for decision in decisions['collisions']:
        uid = decision['original_id']
        if not uid.isdigit():
            raise ValueError(f'invalid native form ID: {uid!r}')
        for server in ('GL', 'JP'):
            source = decision['asset_sources'][server]
            if not source.startswith(f'FFBE_{server}/'):
                raise ValueError(f'source region mismatch: {server} {source}')
            grouped[source].append((server, uid))
    files, bundles, archives = [], [], []
    for source, identities in sorted(grouped.items()):
        original = source_path(dump, source)
        archive_sha = sha(original.read_bytes())
        cpk = Cpk(original)
        try:
            entries = {}
            for entry in cpk.entries:
                name = safe_name(entry['name'])
                if entry.get('dir') or name in entries:
                    raise ValueError(f'unsupported member directory or duplicate name: {name}')
                entries[name] = entry
            selected = {uid: sorted(name for name in entries if member_matches(name, uid))
                        for _, uid in identities}
            for _, uid in identities:
                missing = required_members(uid) - set(selected[uid])
                if missing:
                    raise ValueError(f'incomplete pinned bundle {source}: {sorted(missing)}')
            # Fresh per-source work caches are produced by the original extractor;
            # the immutable archive hash accompanies every published bundle.
            cache = None
            if source.startswith('FFBE_JP/'):
                cache = extract_archive(SimpleNamespace(work=work / archive_sha, dump=dump,
                                        extractor=extractor), source,
                                        [n for names in selected.values() for n in names])
            if sha(original.read_bytes()) != archive_sha:
                raise ValueError(f'source archive changed during extraction: {source}')
            archives.append({'source': source, 'sha256': archive_sha,
                             'bytes': original.stat().st_size})
            for server, uid in identities:
                paths = []
                for name in selected[uid]:
                    data = (cache / name).read_bytes() if cache else cpk.read(entries[name])
                    extraction = 'DataExtractor' if cache else 'CPK member'
                    try:
                        verify_bytes(name, data)
                    except Exception:
                        data = cpk.read(entries[name])
                        verify_bytes(name, data)
                        extraction = 'plaintext member in encrypted CPK'
                    folder = category(name, source, {})
                    dest = f'regional_units/{server.lower()}/{uid}/{folder}/{name}'
                    target = (repo / dest).resolve()
                    if not target.is_relative_to(repo.resolve()):
                        raise ValueError(f'destination escapes repository: {dest}')
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        if target.read_bytes() != data:
                            raise ValueError(f'existing regional asset differs: {dest}')
                    else:
                        with target.open('xb') as output:
                            output.write(data)
                    record = {'destination': dest, 'server': server, 'original_id': uid,
                              'source': source, 'source_sha256': archive_sha,
                              'member': name, 'bytes': len(data), 'sha256': sha(data),
                              'extraction': extraction}
                    if legacy_repo:
                        legacy = legacy_repo / folder / name
                        if legacy.exists():
                            record['legacy_sha256'] = sha(legacy.read_bytes())
                            record['matches_legacy'] = record['legacy_sha256'] == record['sha256']
                    files.append(record)
                    paths.append(dest)
                bundles.append({'server': server, 'original_id': uid, 'source': source,
                                'source_sha256': archive_sha, 'asset_files': sorted(paths)})
                print(f'Restored {server}:{uid}: {len(paths)} original files', flush=True)
        finally:
            cpk.f.close()
    manifest = {'schema_version': 1, 'archives': archives,
                'files': sorted(files, key=lambda x: x['destination']),
                'bundles': sorted(bundles, key=lambda x: (x['original_id'], x['server']))}
    save(repo / REPORT, manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--dump', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--extractor', type=Path, required=True)
    parser.add_argument('--legacy-repo', type=Path)
    args = parser.parse_args()
    report = recover(args.repo.resolve(), args.dump.resolve(), args.work.resolve(),
                     args.extractor.resolve(), args.legacy_repo)
    print(json.dumps({'bundles': len(report['bundles']), 'files': len(report['files']),
                      'bytes': sum(x['bytes'] for x in report['files'])}))


if __name__ == '__main__':
    main()
