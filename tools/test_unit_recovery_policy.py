"""Regression checks for safe, server-aware recovery of confirmed collisions."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import recover_assets
from unit_recovery_policy import INVENTORY_POLICY_FILE, PUBLISHED_MANIFEST, PolicyError, UnitRecoveryPolicy


COLLISION = '401014207'
GL_SOURCE = 'FFBE_GL/resource/unit/units.cpk'
JP_SOURCE = 'FFBE_JP/resource/unit/units.cpk'


def source_choices(ids):
    return {uid: {'GL': GL_SOURCE, 'JP': JP_SOURCE} for uid in ids}


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.work = self.root / 'work'
        self.work.mkdir()
        self.policy = UnitRecoveryPolicy([COLLISION], source_choices([COLLISION]))

    def tearDown(self):
        self.temporary.cleanup()

    def write_decisions(self, collisions=None):
        recover_assets.save(self.repo / 'catalog/unit_identity_decisions.json', {
            'schema_version': 1,
            'collisions': collisions if collisions is not None else [
                {'original_id': COLLISION, 'asset_sources': source_choices([COLLISION])[COLLISION]}],
        })

    def prepare_inventory(self):
        recover_assets.save(self.work / 'inventory.json', {'example': []})
        recover_assets.save(self.work / INVENTORY_POLICY_FILE,
                            self.policy.inventory_metadata(self.work / 'inventory.json'))

    def test_only_confirmed_units_route_with_native_filename_and_category(self):
        cases = [('unit_anime_', '.png', 'unit_animated'),
                 ('unit_anime_', '_2.png', 'unit_animated'),
                 ('unit_cgg_', '.csv', 'unit_animated_csv'),
                 ('unit_idle_cgs_', '.csv', 'unit_animated_csv'),
                 ('unit_icon_', '.png', 'unit_icons'),
                 ('unit_ills_', '.png', 'unit_illustrations'),
                 ('unit_something_', '.bin', 'unit_assets')]
        for prefix, suffix, folder in cases:
            name = prefix + COLLISION + suffix
            for server in ('gl', 'jp'):
                source = {'gl': GL_SOURCE, 'jp': JP_SOURCE}[server]
                category = recover_assets.category(name, source, {})
                self.assertEqual(category, folder)
                self.assertEqual(self.policy.destination(name, source, category),
                    f'regional_units/{server}/{COLLISION}/{folder}/{name}')
        for name in ('unit_anime_100002503.png', f'unit_anime_1{COLLISION}.png'):
            self.assertEqual(self.policy.destination(name, 'FFBE_GL/example.cpk', 'unit_animated'),
                             f'unit_animated/{name}')
        self.assertEqual(self.policy.destination(f'monster_anime_{COLLISION}.png',
                         'FFBE_JP/example.cpk', 'monster_animated'),
                         f'monster_animated/monster_anime_{COLLISION}.png')

    def test_unknown_server_and_ambiguous_id_fail_closed(self):
        with self.assertRaisesRegex(PolicyError, 'Unknown server'):
            self.policy.destination(f'unit_anime_{COLLISION}.png', 'other/FFBE_JP/a.cpk', 'unit_animated')
        policy = UnitRecoveryPolicy([COLLISION, '401014217'], source_choices([COLLISION, '401014217']))
        with self.assertRaisesRegex(PolicyError, 'Ambiguous unit ID'):
            policy.destination(f'unit_{COLLISION}_401014217.png', 'FFBE_GL/a.cpk', 'unit_assets')

    def test_policy_load_validates_schema_and_preserves_evidence_independence(self):
        self.assertFalse(UnitRecoveryPolicy.load(self.repo).collision_ids)
        self.write_decisions([{'original_id': COLLISION, 'evidence': 'verified separately',
                              'asset_sources': source_choices([COLLISION])[COLLISION]}])
        self.assertEqual(UnitRecoveryPolicy.load(self.repo).fingerprint, self.policy.fingerprint)
        for rows in ([{'original_id': 401014207}], [{'original_id': '../401014207'}],
                     [{'original_id': COLLISION}, {'original_id': COLLISION}], None):
            recover_assets.save(self.repo / 'catalog/unit_identity_decisions.json',
                                {'schema_version': 1, 'collisions': rows})
            with self.assertRaises(PolicyError):
                UnitRecoveryPolicy.load(self.repo)
        recover_assets.save(self.repo / 'catalog/unit_identity_decisions.json',
                            {'schema_version': 2, 'collisions': []})
        with self.assertRaises(PolicyError):
            UnitRecoveryPolicy.load(self.repo)

    def test_policy_fingerprint_tracks_collision_set_and_reviewed_sources(self):
        self.assertEqual(UnitRecoveryPolicy([COLLISION, '123456789'],
                         source_choices([COLLISION, '123456789'])).fingerprint,
                         UnitRecoveryPolicy(['123456789', COLLISION],
                         source_choices(['123456789', COLLISION])).fingerprint)
        self.assertNotEqual(self.policy.fingerprint, UnitRecoveryPolicy().fingerprint)
        changed = source_choices([COLLISION])
        changed[COLLISION]['GL'] = 'FFBE_GL/resource/unit/new-reviewed-version.cpk'
        changed_policy = UnitRecoveryPolicy([COLLISION], changed)
        self.assertNotEqual(self.policy.fingerprint, changed_policy.fingerprint)
        self.prepare_inventory()
        with self.assertRaisesRegex(PolicyError, 'different unit identity policy'):
            changed_policy.verify_inventory(self.work)

    def test_collisions_require_valid_reviewed_archive_choices(self):
        for choices in (None, {}, {COLLISION: None}, {COLLISION: {'GL': GL_SOURCE}},
                        {COLLISION: {'GL': JP_SOURCE, 'JP': JP_SOURCE}},
                        {COLLISION: {'GL': 'FFBE_GL/../outside.cpk', 'JP': JP_SOURCE}},
                        {COLLISION: {'GL': 'FFBE_GL/loose.png', 'JP': JP_SOURCE}}):
            with self.assertRaises(PolicyError):
                UnitRecoveryPolicy([COLLISION], choices)
        self.write_decisions([{'original_id': COLLISION}])
        with self.assertRaises(PolicyError):
            UnitRecoveryPolicy.load(self.repo)

    def test_unreviewed_carried_jp_and_new_versions_are_excluded(self):
        for source in ('FFBE_GL/resource/unit/unit27_common.cpk',
                       'FFBE_GL/resource/unit/new_gl_sg_version.cpk',
                       'FFBE_JP/resource/unit/other.cpk'):
            self.assertIsNone(self.policy.destination(f'unit_anime_{COLLISION}.png',
                                                     source, 'unit_animated'))

    def test_inventory_rejects_prepolicy_changed_policy_and_changed_inventory(self):
        with self.assertRaisesRegex(PolicyError, 'Rerun inventory'):
            self.policy.verify_inventory(self.work)
        self.prepare_inventory()
        self.policy.verify_inventory(self.work)
        with self.assertRaisesRegex(PolicyError, 'different unit identity policy'):
            UnitRecoveryPolicy().verify_inventory(self.work)
        (self.work / 'inventory.json').write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(PolicyError, 'does not match'):
            self.policy.verify_inventory(self.work)

    def test_stale_inventory_aborts_recovery_before_any_output(self):
        self.write_decisions()
        args = SimpleNamespace(repo=self.repo, work=self.work)
        with self.assertRaises(PolicyError):
            recover_assets.recover(args)
        self.assertEqual(list(self.work.iterdir()), [])

    def test_committed_baseline_uses_verified_published_manifest(self):
        self.write_decisions()
        name = f'unit_idle_cgs_{COLLISION}.csv'
        dest = f'regional_units/gl/{COLLISION}/unit_animated_csv/{name}'
        path = self.repo / dest
        path.parent.mkdir(parents=True)
        data = b'0,1\n'
        path.write_bytes(data)
        record = {'destination': dest, 'source': GL_SOURCE, 'member': name,
                  'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
        recover_assets.save(self.repo / PUBLISHED_MANIFEST, {'files': [record]})
        assets = {dest: [{'source': GL_SOURCE, 'kind': 'cpk', 'entry': {'name': name}}]}
        recover_assets.save(self.work / 'inventory.json', assets)
        recover_assets.save(self.work / INVENTORY_POLICY_FILE,
                            self.policy.inventory_metadata(self.work / 'inventory.json'))
        baseline = {dest: len(data)}
        recover_assets.save(self.work / 'baseline.json', baseline)
        args = SimpleNamespace(repo=self.repo, work=self.work, phase='priority',
                               existing_folders_only=True, workers=1)
        with contextlib.redirect_stdout(io.StringIO()), patch.object(
                recover_assets, 'extract_archive', side_effect=AssertionError('Baseline must not extract')):
            recover_assets.recover(args)
        self.assertEqual(json.loads((self.work / 'recovered.json').read_text()), {})
        self.assertEqual(path.read_bytes(), data)
        wrong = {**record, 'source': 'FFBE_GL/resource/unit/unreviewed.cpk'}
        recover_assets.save(self.repo / PUBLISHED_MANIFEST, {'files': [wrong]})
        with self.assertRaisesRegex(PolicyError, 'unapproved source provenance'):
            self.policy.verify_existing_recovery(self.repo, assets, baseline, {})
        recover_assets.save(self.repo / PUBLISHED_MANIFEST, {'files': [record]})
        path.write_bytes(b'9,9\n')
        with self.assertRaisesRegex(PolicyError, 'differs from its recovery provenance'):
            self.policy.verify_existing_recovery(self.repo, assets, baseline, {})

    def test_inventory_and_recovery_keep_both_servers_and_legacy_copy(self):
        self.write_decisions()
        dump = self.root / 'dump'
        name = f'unit_idle_cgs_{COLLISION}.csv'
        shared = 'unit_idle_cgs_100002503.csv'
        legacy = self.repo / 'unit_animated_csv' / name
        legacy.parent.mkdir()
        legacy.write_bytes(b'legacy copy retained')
        recover_assets.save(self.work / 'baseline.json', {f'unit_animated_csv/{name}': 20})
        (self.work / 'baseline-commit.txt').write_text('synthetic-baseline\n')
        for server in ('GL', 'JP'):
            path = dump / f'FFBE_{server}' / 'resource/unit/units.cpk'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'synthetic archive')
        carried_jp = dump / 'FFBE_GL/resource/unit/unit27_common.cpk'
        carried_jp.write_bytes(b'synthetic carried JP archive')
        carried_only = f'unit_magic_cgs_{COLLISION}.csv'

        class Archive:
            def __init__(self, path):
                self.f = io.BytesIO()
                self.entries = ([{'name': name}, {'name': carried_only}]
                                if path.name == 'unit27_common.cpk'
                                else [{'name': name}, {'name': shared}])

        args = SimpleNamespace(repo=self.repo, dump=dump, work=self.work, phase='priority',
                               existing_folders_only=True, workers=1, extractor=None)
        with patch.object(recover_assets, 'Cpk', Archive), contextlib.redirect_stdout(io.StringIO()):
            recover_assets.inventory(args)
        assets = json.loads((self.work / 'inventory.json').read_text())
        self.assertEqual(len(assets), 3)
        self.assertFalse(any(carried_only in dest for dest in assets))
        for server in ('gl', 'jp'):
            dest = f'regional_units/{server}/{COLLISION}/unit_animated_csv/{name}'
            self.assertIn(dest, assets)
            self.assertEqual(len(assets[dest]), 1)
            self.assertEqual(assets[dest][0]['source'], {'gl': GL_SOURCE, 'jp': JP_SOURCE}[server])
        self.assertEqual(len(assets[f'unit_animated_csv/{shared}']), 2)
        self.assertTrue(assets[f'unit_animated_csv/{shared}'][0]['source'].startswith('FFBE_JP/'))

        def extract(args, source, selected):
            server = source.split('/')[0]
            cache = self.work / server
            cache.mkdir(exist_ok=True)
            value = b'0,1\n' if server == 'FFBE_GL' else b'1,2\n'
            for member in selected:
                (cache / member).write_bytes(value)
            return cache

        with patch.object(recover_assets, 'extract_archive', extract), contextlib.redirect_stdout(io.StringIO()):
            recover_assets.recover(args)
            recover_assets.recover(args)  # Resume must add nothing and preserve distinct bytes.
        recovered = json.loads((self.work / 'recovered.json').read_text())
        self.assertEqual(len(recovered), 3)
        self.assertEqual(legacy.read_bytes(), b'legacy copy retained')
        for server, expected in [('gl', b'0,1\n'), ('jp', b'1,2\n')]:
            dest = f'regional_units/{server}/{COLLISION}/unit_animated_csv/{name}'
            self.assertEqual((self.repo / dest).read_bytes(), expected)
            self.assertEqual(recovered[dest]['member'], name)
            self.assertTrue(recovered[dest]['source'].startswith(f'FFBE_{server.upper()}/'))
        changed = source_choices([COLLISION])
        changed[COLLISION]['GL'] = 'FFBE_GL/resource/unit/new-reviewed-version.cpk'
        with self.assertRaisesRegex(PolicyError, 'unapproved source provenance'):
            UnitRecoveryPolicy([COLLISION], changed).verify_existing_recovery(
                self.repo, assets, {}, recovered)
        with self.assertRaisesRegex(PolicyError, 'unapproved source provenance'):
            UnitRecoveryPolicy([COLLISION], changed).verify_existing_recovery(
                self.repo, {}, {}, recovered)  # Old members absent from new inventory still count.
        gl_dest = f'regional_units/gl/{COLLISION}/unit_animated_csv/{name}'
        with self.assertRaisesRegex(PolicyError, 'no recovery provenance'):
            self.policy.verify_existing_recovery(self.repo, assets, {gl_dest: 4}, {})
        (self.repo / gl_dest).write_bytes(b'9,9\n')
        with self.assertRaisesRegex(PolicyError, 'differs from its recovery provenance'):
            self.policy.verify_existing_recovery(self.repo, assets, {}, recovered)

    def test_unknown_region_archive_is_fatal_not_silently_skipped(self):
        self.write_decisions()
        dump = self.root / 'dump'
        dump.mkdir()
        (dump / 'unknown.cpk').write_bytes(b'synthetic archive')
        recover_assets.save(self.work / 'baseline.json', {})

        class Archive:
            def __init__(self, path):
                self.f = io.BytesIO()
                self.entries = [{'name': f'unit_anime_{COLLISION}.png'}]

        args = SimpleNamespace(repo=self.repo, dump=dump, work=self.work)
        with patch.object(recover_assets, 'Cpk', Archive), self.assertRaises(PolicyError):
            recover_assets.inventory(args)
        self.assertFalse((self.work / 'inventory.json').exists())


if __name__ == '__main__':
    unittest.main()
