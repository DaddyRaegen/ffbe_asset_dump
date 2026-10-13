from pathlib import Path
import copy, json, tempfile, unittest, zipfile
import download_spacing_guard as guard

class ExactSpacingGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((guard.ROOT/'audit/DOWNLOAD_SPACING_PLAN.json').read_text(encoding='utf-8-sig'))
        with zipfile.ZipFile(guard.DEFAULT_BASELINE) as z:
            cls.original_script = z.read('assets/frida_script.js')
            cls.manifest = z.read('AndroidManifest.xml')
        cls.candidate = (guard.ROOT/'source/frida_script.js').read_bytes()

    def test_exact_finite_script_delta_passes(self):
        self.assertEqual(guard.expected_script(self.original_script, self.plan), self.candidate)
        self.assertTrue(guard.compare_script(self.original_script, self.candidate, self.plan)['expected_js_delta_passed'])

    def test_unrequested_script_change_is_rejected(self):
        for edit in [b'\n// extra hook\n', b' ', b'\n']:
            with self.subTest(edit=edit), self.assertRaises(guard.GuardError):
                guard.compare_script(self.original_script, self.candidate+edit, self.plan)

    def test_loosening_the_plan_does_not_grant_permission(self):
        for key, value in [('after', guard.INSERT_AFTER+'  // anything\r\n'), ('count', 2), ('before', 'function')]:
            plan = copy.deepcopy(self.plan); plan['operations'][0][key] = value
            with self.subTest(key=key), self.assertRaises(guard.GuardError):
                guard.expected_script(self.original_script, plan)
        plan = copy.deepcopy(self.plan); plan['operations'].append(copy.deepcopy(plan['operations'][0]))
        with self.assertRaises(guard.GuardError): guard.expected_script(self.original_script, plan)

    def test_plan_hash_and_versions_are_checked(self):
        for key, value in [('baseline_apk_sha256', '0'*64), ('baseline_script_sha256', '0'*64),
                           ('candidate_script_sha256', '0'*64), ('baseline_version', 205),
                           ('candidate_version', 208), ('schema', 'generic'), ('scope', 'all-labels')]:
            plan = copy.deepcopy(self.plan); plan[key] = value
            with self.subTest(key=key), self.assertRaises(guard.GuardError):
                guard.expected_script(self.original_script, plan)

    def test_manifest_only_typed_version_value_changes(self):
        candidate, receipt = guard.expected_manifest(self.manifest)
        p = receipt['value_offset']
        self.assertEqual(candidate[:p], self.manifest[:p])
        self.assertEqual(candidate[p+4:], self.manifest[p+4:])
        self.assertEqual(int.from_bytes(candidate[p:p+4], 'little'), 207)
        with self.assertRaises(guard.GuardError): guard.expected_manifest(candidate)
        wrong = bytearray(self.manifest); wrong[p-1] = 3
        with self.assertRaises(guard.GuardError): guard.expected_manifest(wrong)
        with self.assertRaises(guard.GuardError): guard.expected_manifest(self.manifest[:-1])

    def archives(self, root, changed=None, method=zipfile.ZIP_DEFLATED, order=None, extra=None, omit=None,
                 candidate_level=6, duplicate=None):
        entries = {'AndroidManifest.xml': b'old manifest', 'assets/frida_script.js': b'old script',
                   'classes.dex': b'old dex'*100, 'assets/content_delivery.tsv': b'old metadata'*100,
                   'assets/side_stories/manifest.tsv': b'old side manifest'*100,
                   'lib/arm64-v8a/libgame.so': b'native'*100,
                   'META-INF/MANIFEST.MF': b'old v1 signature manifest'}
        before, after = Path(root)/'before.apk', Path(root)/'after.apk'
        with zipfile.ZipFile(before, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for n, b in entries.items(): z.writestr(n, b)
        current = dict(entries); current.update({'AndroidManifest.xml': b'new manifest', 'assets/frida_script.js': b'new script'})
        if changed: current.update(changed)
        if extra: current.update(extra)
        if omit: current.pop(omit)
        with zipfile.ZipFile(after, 'w', method, compresslevel=candidate_level) as z:
            for n in order or current:
                z.writestr(n, current[n])
            if duplicate: z.writestr(duplicate, current[duplicate])
        return before, after

    def compare_small(self, paths):
        return guard.compare_members(*paths, asset_count=3, member_count=6)

    def test_only_two_members_pass_and_v1_signature_data_can_change(self):
        with tempfile.TemporaryDirectory(dir=guard.ROOT/'audit') as root:
            paths = self.archives(root, changed={'META-INF/MANIFEST.MF': b'new signed manifest'})
            report = self.compare_small(paths)
            self.assertEqual({r['path'] for r in report['changed_members']}, guard.ALLOWED)
            self.assertEqual(report['unchanged_member_count'], 4)

    def test_unrequested_runtime_catalog_side_and_native_changes_rejected(self):
        for path in ['classes.dex', 'assets/content_delivery.tsv', 'assets/side_stories/manifest.tsv', 'lib/arm64-v8a/libgame.so']:
            with self.subTest(path=path), tempfile.TemporaryDirectory(dir=guard.ROOT/'audit') as root:
                paths = self.archives(root, changed={path: b'changed'})
                with self.assertRaises(guard.GuardError): self.compare_small(paths)

    def test_added_removed_duplicate_reordered_and_signing_names_rejected(self):
        cases = [{'extra': {'assets/extra.dat': b'extra'}}, {'extra': {'META-INF/EXTRA.SF': b'extra'}},
                 {'omit': 'classes.dex'}, {'duplicate': 'classes.dex'},
                 {'order': ['assets/frida_script.js','AndroidManifest.xml','classes.dex','assets/content_delivery.tsv',
                            'assets/side_stories/manifest.tsv','lib/arm64-v8a/libgame.so','META-INF/MANIFEST.MF']}]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory(dir=guard.ROOT/'audit') as root:
                with self.assertRaises(guard.GuardError): self.compare_small(self.archives(root, **case))

    def test_compression_method_and_unchanged_recompression_rejected(self):
        for case in [{'method': zipfile.ZIP_STORED}, {'candidate_level': 0}]:
            with self.subTest(case=case), tempfile.TemporaryDirectory(dir=guard.ROOT/'audit') as root:
                with self.assertRaises(guard.GuardError): self.compare_small(self.archives(root, **case))

    def test_one_change_only_rejected(self):
        with tempfile.TemporaryDirectory(dir=guard.ROOT/'audit') as root:
            paths = self.archives(root, changed={'assets/frida_script.js': b'old script'})
            with self.assertRaises(guard.GuardError): self.compare_small(paths)

if __name__ == '__main__': unittest.main(verbosity=2)
