"""Reject corrupt registry/provenance fields, using the real restored bundles."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from validate_unit_identities import validate

ROOT = Path(__file__).resolve().parents[1]


class IdentityValidationTests(unittest.TestCase):
    def reject_mutation(self, mutate):
        loads = json.loads

        def changed_loads(data, *args, **kwargs):
            document = loads(data, *args, **kwargs)
            mutate(document)
            return document

        with patch('validate_unit_identities.json.loads', side_effect=changed_loads):
            with self.assertRaises(AssertionError):
                validate(ROOT)

    def test_restored_registry_and_assets_pass(self):
        report = validate(ROOT)
        self.assertEqual(report['restored_bundles'], 22)
        self.assertEqual(report['restored_files'], 352)

    def test_corrupt_secondary_catalog_hash_is_rejected(self):
        def mutate(document):
            if isinstance(document, dict) and 'units' in document:
                unit = next(x for x in document['units'] if x['identity_status'] == 'regional_collision')
                unit['assets']['files'][-1]['sha256'] = '0' * 64
        self.reject_mutation(mutate)

    def test_wrong_file_archive_provenance_is_rejected(self):
        def mutate(document):
            if isinstance(document, dict) and 'archives' in document:
                document['files'][0]['source_sha256'] = '0' * 64
        self.reject_mutation(mutate)

    def test_incomplete_bundle_member_list_is_rejected(self):
        def mutate(document):
            if isinstance(document, dict) and 'archives' in document:
                document['bundles'][0]['asset_files'].pop()
        self.reject_mutation(mutate)


if __name__ == '__main__':
    unittest.main()
