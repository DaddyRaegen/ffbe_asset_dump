"""Route verified cross-server unit collisions without changing native filenames."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


class PolicyError(ValueError):
    """An identity policy or inventory cannot safely be used for recovery."""


POLICY_FILE = Path('catalog/unit_identity_decisions.json')
INVENTORY_POLICY_FILE = 'inventory-policy.json'
ROUTING_VERSION = 2
PUBLISHED_MANIFEST = Path('reports/2026-10-02-unit-identities/asset-manifest.json')


class UnitRecoveryPolicy:
    def __init__(self, collision_ids=(), asset_sources=None):
        self.collision_ids = frozenset(collision_ids)
        self.asset_sources = asset_sources or {}
        if set(self.asset_sources) != self.collision_ids:
            raise PolicyError('Every collision requires reviewed GL and JP asset_sources')
        for uid, sources in self.asset_sources.items():
            if not isinstance(sources, dict) or set(sources) != {'GL', 'JP'}:
                raise PolicyError(f'Collision {uid} requires exactly GL and JP asset_sources')
            for server, source in sources.items():
                if (not isinstance(source, str) or not source.startswith(f'FFBE_{server}/')
                        or not source.lower().endswith('.cpk') or '\\' in source
                        or any(part in ('', '.', '..') for part in source.split('/'))
                        or ':' in source):
                    raise PolicyError(f'Collision {uid} has an invalid {server} archive source')
        content = {'routing_version': ROUTING_VERSION,
                   'collision_ids': sorted(self.collision_ids),
                   'asset_sources': self.asset_sources}
        self.fingerprint = hashlib.sha256(
            json.dumps(content, sort_keys=True, separators=(',', ':')).encode('utf-8')
        ).hexdigest()

    @classmethod
    def load(cls, repo):
        path = Path(repo) / POLICY_FILE
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ValueError) as error:
            raise PolicyError(f'Cannot read unit identity policy: {path}') from error
        if not isinstance(data, dict) or data.get('schema_version') != 1:
            raise PolicyError('Unit identity policy requires schema_version 1')
        rows = data.get('collisions')
        if not isinstance(rows, list):
            raise PolicyError('Unit identity policy requires a collisions list')
        ids = []
        sources = {}
        for row in rows:
            uid = row.get('original_id') if isinstance(row, dict) else None
            if not isinstance(uid, str) or not re.fullmatch(r'[0-9]+', uid):
                raise PolicyError('Every collision requires a decimal original_id string')
            if uid in ids:
                raise PolicyError(f'Duplicate collision original_id: {uid}')
            ids.append(uid)
            sources[uid] = row.get('asset_sources')
        return cls(ids, sources)

    def destination(self, name, source, category):
        legacy = f'{category}/{name}'
        if not name.lower().startswith('unit_'):
            return legacy
        # Match a complete numeric token, including page-suffixed unit assets.
        matches = set(re.findall(r'(?<![0-9])[0-9]+(?![0-9])', name)) & self.collision_ids
        if not matches:
            return legacy
        if len(matches) != 1:
            raise PolicyError(f'Ambiguous unit ID in collision asset: {name}')
        uid = next(iter(matches))
        region = source.replace('\\', '/').split('/')[0].lower()
        server = {'ffbe_gl': 'gl', 'ffbe_jp': 'jp'}.get(region)
        if server is None:
            raise PolicyError(f'Unknown server for collision asset {name}: {source}')
        # GL archives can carry JP units with the same native ID. Region alone
        # is not identity evidence: keep every member on its reviewed archive.
        if source.replace('\\', '/') != self.asset_sources[uid][server.upper()]:
            return None
        return f'regional_units/{server}/{uid}/{legacy}'

    def inventory_metadata(self, inventory_path):
        return {'schema_version': 1, 'routing_version': ROUTING_VERSION,
                'unit_identity_fingerprint': self.fingerprint,
                'collision_ids': sorted(self.collision_ids),
                'asset_sources': self.asset_sources,
                'inventory_sha256': file_sha256(inventory_path)}

    def verify_existing_recovery(self, repo, assets, baseline, recovered):
        """Refuse source upgrades that would mix old files with new companions."""
        published = None
        # Include old regional members absent from the new archive, otherwise
        # changing sources could leave an old atlas beside newly added CSVs.
        for dest in sorted(set(assets) | set(baseline) | set(recovered)):
            if not dest.startswith('regional_units/'):
                continue
            if dest not in baseline and dest not in recovered:
                continue
            record = recovered.get(dest)
            if record is None and dest in baseline:
                if published is None:
                    published = self.published_records(repo)
                record = published.get(dest)
            if not isinstance(record, dict):
                raise PolicyError(f'Existing regional collision asset has no recovery provenance: {dest}. '
                                  'Use the published manifest, original recovery work directory, or a reviewed migration.')
            parts = dest.split('/')
            source = record.get('source')
            if (len(parts) != 5 or not isinstance(source, str)
                    or record.get('member') != parts[-1]
                    or self.destination(parts[-1], source, parts[-2]) != dest):
                raise PolicyError(f'Existing regional collision asset uses unapproved source provenance: {dest}. '
                                  'Archive source changes require a reviewed migration.')
            try:
                path = Path(repo) / dest
                matches = (path.stat().st_size == record.get('bytes')
                           and file_sha256(path) == record.get('sha256'))
            except OSError:
                matches = False
            if not matches:
                raise PolicyError(f'Existing regional collision asset differs from its recovery provenance: {dest}. '
                                  'Review the asset before resuming recovery.')

    @staticmethod
    def published_records(repo):
        path = Path(repo) / PUBLISHED_MANIFEST
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ValueError) as error:
            raise PolicyError('Cannot read published regional asset provenance') from error
        rows = data.get('files') if isinstance(data, dict) else data
        if not isinstance(rows, list):
            raise PolicyError('Published regional asset provenance requires a files list')
        records = {}
        for row in rows:
            dest = row.get('destination') if isinstance(row, dict) else None
            if not isinstance(dest, str) or dest in records:
                raise PolicyError('Published regional asset provenance has invalid or duplicate destinations')
            records[dest] = row
        return records

    def verify_inventory(self, work):
        work = Path(work)
        marker = work / INVENTORY_POLICY_FILE
        instruction = 'Rerun inventory with the current unit identity policy before recovery.'
        try:
            metadata = json.loads(marker.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ValueError) as error:
            raise PolicyError(f'Missing or invalid inventory policy metadata. {instruction}') from error
        if (not isinstance(metadata, dict) or metadata.get('schema_version') != 1
                or metadata.get('routing_version') != ROUTING_VERSION
                or metadata.get('unit_identity_fingerprint') != self.fingerprint
                or metadata.get('collision_ids') != sorted(self.collision_ids)
                or metadata.get('asset_sources') != self.asset_sources):
            raise PolicyError(f'Inventory uses a different unit identity policy. {instruction}')
        try:
            digest = file_sha256(work / 'inventory.json')
        except OSError as error:
            raise PolicyError(f'Cannot read inventory. {instruction}') from error
        if metadata.get('inventory_sha256') != digest:
            raise PolicyError(f'Inventory does not match its policy metadata. {instruction}')


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
