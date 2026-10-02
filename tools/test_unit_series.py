"""Series assignment must follow region-specific game codes, not unit names."""
import copy
import json
from pathlib import Path
import unittest

from build_unit_master import build_master, source_snapshot_fingerprint
from unit_series import attach_series

ROOT = Path(__file__).resolve().parents[1]


class SeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(name):
            return json.loads((ROOT / 'catalog' / name).read_text(encoding='utf-8'))
        cls.snapshot = read('unit_identity_sources.json')
        cls.decisions = read('unit_identity_decisions.json')
        cls.series = read('series_sources.json')
        cls.master = build_master(cls.snapshot, cls.decisions, [], series_sources=cls.series)

    def test_complete_source_coverage_and_regional_provenance(self):
        coverage = self.master['coverage']['series']
        self.assertEqual(coverage['known_regional_identities'], 6823)
        self.assertEqual(coverage['unknown_game_id_count'], 0)
        for unit in self.master['units']:
            for identity in unit['identities']:
                self.assertEqual(identity['series_status'], 'known')
                p = identity['series_provenance']
                self.assertEqual(p['game_title_row_id'], identity['game_id'])
                self.assertEqual(p['unit_form_id'], identity['original_id'])
                self.assertEqual(p['game_title_source'], identity['server'] + '_game_master')

    def test_requested_franchises_and_specific_title_are_retained(self):
        examples = {'11001': 'FFBE', '10016': 'FFXVI', '20028': 'Kingdom Hearts',
                    '20033': 'Kingdom Hearts', '20034': 'Kingdom Hearts',
                    '20032': 'Fullmetal Alchemist'}
        for code, expected in examples.items():
            matching = [i for u in self.master['units'] for i in u['identities'] if i['game_id'] == code]
            self.assertTrue(matching)
            self.assertTrue(all(i['series'] == expected for i in matching))
        row = next(i for u in self.master['units'] for i in u['identities'] if i['game_id'] == '20033')
        self.assertEqual(row['game_title'], 'Kingdom Hearts III')

    def test_regional_code_differences_do_not_split_franchise(self):
        row = next(u for u in self.master['units'] if u['original_id'] == '401000104')
        self.assertEqual(row['series'], 'Ariana Grande')
        self.assertEqual({(i['server'], i['game_id']) for i in row['identities']},
                         {('GL', '90001'), ('JP', '20009')})

    def test_unknown_code_does_not_fall_back_to_unit_name_or_id(self):
        snapshot = copy.deepcopy(self.snapshot)
        series = copy.deepcopy(self.series)
        master = copy.deepcopy(self.master)
        native = next(r for r in snapshot['sources']['GL']['rows'] if r['original_id'] == '401014207')
        native['game_id'] = 'not-in-game-master'
        series['unit_snapshot_fingerprint'] = source_snapshot_fingerprint(snapshot)
        row = next(u for u in master['units'] if u['master_id'] == 'unit:GL:401014207')
        row['name'] = 'Kingdom Hearts'
        attach_series(master, snapshot, series)
        self.assertIsNone(row['series'])
        self.assertEqual(row['identities'][0]['series_status'], 'unknown_game_id')

    def test_asset_without_identity_stays_unknown(self):
        result = build_master(self.snapshot, self.decisions, [{'id': '999999999'}], series_sources=self.series)
        row = next(u for u in result['units'] if u['master_id'] == '999999999')
        self.assertIsNone(row['series'])
        self.assertEqual(row['series_status'], 'no_unit_metadata')

    def test_zero_sentinel_is_unknown_and_not_a_verified_master_row(self):
        snapshot = copy.deepcopy(self.snapshot)
        series = copy.deepcopy(self.series)
        master = copy.deepcopy(self.master)
        native = next(r for r in snapshot['sources']['GL']['rows'] if r['original_id'] == '401014207')
        native['game_id'] = '0'
        series['unit_snapshot_fingerprint'] = source_snapshot_fingerprint(snapshot)
        attach_series(master, snapshot, series)
        row = next(u for u in master['units'] if u['master_id'] == 'unit:GL:401014207')
        identity = row['identities'][0]
        self.assertIsNone(identity['series'])
        self.assertEqual(identity['series_status'], 'unknown_game_id')
        self.assertFalse(identity['series_provenance']['game_title_row_verified'])

    def test_stale_series_snapshot_is_rejected(self):
        series = copy.deepcopy(self.series)
        series['unit_snapshot_fingerprint'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'different reviewed unit snapshot'):
            attach_series(copy.deepcopy(self.master), self.snapshot, series)


if __name__ == '__main__':
    unittest.main()
