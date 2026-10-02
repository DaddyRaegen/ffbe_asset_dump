"""Regression tests for reviewed archive restoration and immutable source caches."""
from __future__ import annotations

from contextlib import ExitStack, contextmanager, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recover_unit_collisions as repair


UID = '401014207'
GL_SOURCE = 'FFBE_GL/unit/Ver51_unit3_sg_common.cpk'
JP_SOURCE = 'FFBE_JP/unit/unit27.cpk'
MEMBERS = sorted(repair.required_members(UID))


class CollisionRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.dump = self.root / 'dump'
        self.work = self.root / 'work'
        self.extractor = self.root / 'extractor'
        self.entries = {source: [{'name': name} for name in MEMBERS]
                        for source in (GL_SOURCE, JP_SOURCE)}
        for source, data in [(GL_SOURCE, b'GL archive version one'),
                             (JP_SOURCE, b'JP archive version one')]:
            path = self.dump / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.repo = self.make_repo('repo')
        self.cache_work_paths = []
        self.archive_handles = []

    def tearDown(self):
        self.temp.cleanup()

    def make_repo(self, name):
        repo = self.root / name
        (repo / 'catalog').mkdir(parents=True)
        (repo / 'catalog/unit_identity_decisions.json').write_text(json.dumps({
            'schema_version': 1,
            'collisions': [{'original_id': UID,
                            'asset_sources': {'GL': GL_SOURCE, 'JP': JP_SOURCE}}],
        }), encoding='utf-8')
        return repo

    def expected_member(self, source, name, decrypted=False):
        return ((self.dump / source).read_bytes()
                + (b'|decrypted|' if decrypted else b'|member|') + name.encode())

    @contextmanager
    def mocked_tools(self, extractor_hook=None):
        fixtures = self

        class Archive:
            def __init__(self, path):
                self.source = path.relative_to(fixtures.dump).as_posix()
                self.entries = fixtures.entries[self.source]
                self.f = io.BytesIO()
                fixtures.archive_handles.append(self.f)

            def read(self, entry):
                return fixtures.expected_member(self.source, entry['name'])

        def extract(args, source, selected):
            fixtures.cache_work_paths.append(args.work)
            cache = args.work / 'mock-decrypted-cpk'
            cache.mkdir(parents=True, exist_ok=True)
            # Match the production extractor's cache reuse behavior: existing
            # members are not refreshed merely because source bytes changed.
            for name in selected:
                target = cache / name
                if not target.exists():
                    target.write_bytes(fixtures.expected_member(source, name, decrypted=True))
            if extractor_hook:
                extractor_hook(args, source)
            return cache

        with ExitStack() as stack:
            stack.enter_context(patch.object(repair, 'Cpk', Archive))
            stack.enter_context(patch.object(repair, 'extract_archive', side_effect=extract))
            stack.enter_context(patch.object(repair, 'verify_bytes', return_value=None))
            stack.enter_context(redirect_stdout(io.StringIO()))
            yield

    def run_repair(self, repo=None):
        return repair.recover(repo or self.repo, self.dump, self.work, self.extractor)

    def test_changed_jp_archive_uses_new_content_hash_cache(self):
        before = hashlib.sha256((self.dump / JP_SOURCE).read_bytes()).hexdigest()
        with self.mocked_tools():
            first = self.run_repair()
            (self.dump / JP_SOURCE).write_bytes(b'JP archive version two')
            after = hashlib.sha256((self.dump / JP_SOURCE).read_bytes()).hexdigest()
            second_repo = self.make_repo('second-repo')
            second = self.run_repair(second_repo)
        self.assertNotEqual(before, after)
        self.assertEqual(self.cache_work_paths, [self.work / before, self.work / after])
        for record in second['files']:
            if record['server'] == 'JP':
                expected = self.expected_member(JP_SOURCE, record['member'], decrypted=True)
                self.assertEqual((second_repo / record['destination']).read_bytes(), expected)
                self.assertEqual(record['source_sha256'], after)
                old = next(row for row in first['files'] if row['destination'] == record['destination'])
                self.assertNotEqual(old['sha256'], record['sha256'])
        self.assertTrue(all(handle.closed for handle in self.archive_handles))

    def test_unsafe_duplicate_or_directory_members_fail_before_writing(self):
        for bad_entry, expected_error in [({'name': '../escape.png'}, 'unsafe member filename'),
                                          ({'name': MEMBERS[0]}, 'duplicate name'),
                                          ({'name': 'extra.png', 'dir': 'nested'}, 'member directory')]:
            with self.subTest(entry=bad_entry):
                self.entries[GL_SOURCE] = [{'name': name} for name in MEMBERS] + [bad_entry]
                with self.mocked_tools(), self.assertRaisesRegex(ValueError, expected_error):
                    self.run_repair()
                self.assertFalse((self.repo / 'regional_units').exists())
                self.assertFalse((self.repo / repair.REPORT).exists())
                self.assertTrue(all(handle.closed for handle in self.archive_handles))

    def test_each_required_sprite_frame_and_idle_member_is_mandatory(self):
        for omitted in MEMBERS:
            with self.subTest(missing=omitted):
                self.entries[GL_SOURCE] = [{'name': name} for name in MEMBERS if name != omitted]
                with self.mocked_tools(), self.assertRaisesRegex(ValueError, 'incomplete pinned bundle') as error:
                    self.run_repair()
                self.assertIn(omitted, str(error.exception))
                self.assertFalse((self.repo / 'regional_units').exists())
                self.assertFalse((self.repo / repair.REPORT).exists())

    def test_rerun_preserves_same_bytes_and_refuses_replacement(self):
        with self.mocked_tools():
            first = self.run_repair()
            paths = [self.repo / record['destination'] for record in first['files']]
            snapshot = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
            second = self.run_repair()
            self.assertEqual(first, second)
            self.assertEqual(snapshot, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths})
            manifest_before = (self.repo / repair.REPORT).read_bytes()
            victim = self.repo / next(row['destination'] for row in first['files'] if row['server'] == 'GL')
            victim.write_bytes(b'user-owned differing bytes')
            with self.assertRaisesRegex(ValueError, 'existing regional asset differs'):
                self.run_repair()
        self.assertEqual(victim.read_bytes(), b'user-owned differing bytes')
        self.assertEqual((self.repo / repair.REPORT).read_bytes(), manifest_before)
        for path, (data, _) in snapshot.items():
            if path != victim:
                self.assertEqual(path.read_bytes(), data)

    def test_pinned_source_region_mismatch_rejected_before_reading_archives(self):
        decisions_path = self.repo / 'catalog/unit_identity_decisions.json'
        decisions = json.loads(decisions_path.read_text())
        decisions['collisions'][0]['asset_sources']['GL'] = JP_SOURCE
        decisions_path.write_text(json.dumps(decisions), encoding='utf-8')
        with patch.object(repair, 'Cpk', side_effect=AssertionError('Must validate source first')):
            with self.assertRaisesRegex(ValueError, 'source region mismatch'):
                self.run_repair()
        self.assertFalse((self.repo / 'regional_units').exists())
        self.assertFalse((self.repo / repair.REPORT).exists())

    def test_archive_changed_during_extraction_is_not_published(self):
        def mutate_archive(args, source):
            (self.dump / source).write_bytes(b'archive changed while extraction ran')

        with self.mocked_tools(extractor_hook=mutate_archive):
            with self.assertRaisesRegex(ValueError, 'source archive changed during extraction'):
                self.run_repair()
        self.assertFalse((self.repo / repair.REPORT).exists())
        self.assertFalse((self.repo / f'regional_units/jp/{UID}').exists())
        self.assertTrue(all(handle.closed for handle in self.archive_handles))


if __name__ == '__main__':
    unittest.main()
