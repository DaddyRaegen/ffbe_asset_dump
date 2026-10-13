"""Bootstrap tests use synthetic bytes; they do not qualify an Android release."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import release_guard as g
from test_release_guard import build_fixture, fixture_dex, make_apk, OLD_APKS


def make_inventory(manifest_data,apk_version=204):
    manifest=g.load_json(manifest_data)
    return {'schema':g.BOOTSTRAP_SCHEMA,'package':g.PACKAGE,'signing_certificate_sha256':g.SIGNER,'APK_version':apk_version,'asset_version':manifest['asset_version'],'manifest_sha256':g.digest(manifest_data),'assets':[{'namespace':e['namespace'],'path':e['path'],'apk_path':'assets/'+e['path'],'bytes':e['bytes'],'sha256':e['sha256']} for e in manifest['assets'] if e['namespace']=='root' and e['phase']=='boot']}


def fake_tool(args):
    if 'badging' in args:return f"package: name='{g.PACKAGE}' versionCode='204' versionName='11.1.1'\n"
    if '--print-certs' in args:return 'Verifies\nSigner #1 certificate SHA-256 digest: '+g.SIGNER+'\n'
    return 'Verification successful'


class PinnedStartupInventory(unittest.TestCase):
    def setUp(self):
        self.manifest,self.catalogs,self.old_release=build_fixture()
        self.manifest_data=json.dumps(self.manifest).encode()
        self.release=self.old_release.replace(b'beta\t203\t203\t',b'beta\t203\t204\t')
        self.inventory=make_inventory(self.manifest_data)
        self.inventory_data=json.dumps(self.inventory).encode()

    def make_apk(self,path,payloads=None,signed_inventory=None,dex=None):
        script=f'const PATCH_VERSION = 204;\nconst MANIFEST_URL = "{g.BETA_PREFIX}patch_version.json";\nconst DOWNLOAD_URL = "https://ffbe.luminest.io/downloads/beta/";\njniCallStaticVoid("O1/PatchUpdater", "check", "()V", []);\n'
        make_apk(path,self.catalogs,self.release,script=script,dex=dex,manifest_data=self.manifest_data)
        if payloads is None:payloads={row['apk_path']:b'x' for row in self.inventory['assets']}
        with zipfile.ZipFile(path,'a') as apk:
            apk.writestr(g.BOOTSTRAP_MEMBER,self.inventory_data if signed_inventory is None else signed_inventory)
            for member,data in payloads.items():apk.writestr(member,data)

    def verify(self,apk,inventory_data=None):
        return g.qualify(self.manifest_data,self.catalogs,self.release,self.catalogs['base'],apk,previous=self.manifest,expected_version=204,expected_asset_version=203,bootstrap_inventory_data=self.inventory_data if inventory_data is None else inventory_data,runner=fake_tool)

    def mutate_inventory(self,update):
        inventory=copy.deepcopy(self.inventory);update(inventory)
        return json.dumps(inventory).encode()

    def test_exact_signed_startup_inventory_and_independent_versions_pass(self):
        with tempfile.TemporaryDirectory() as td:
            apk=Path(td)/'bootstrap.apk';self.make_apk(apk)
            result=self.verify(apk)
        self.assertEqual(result['version_code'],204)
        self.assertEqual(result['asset_version'],203)
        self.assertEqual(result['APK_min_version'],203)
        self.assertEqual(result['bundled_game_asset_count'],1)
        self.assertEqual(result['bundled_game_asset_bytes'],1)
        self.assertEqual(result['bundled_manifest_asset_rows'],1)
        self.assertEqual(result['external_only_manifest_asset_rows'],4539)
        self.assertEqual(result['bootstrap_inventory_sha256'],g.digest(self.inventory_data))
        self.assertTrue(result['bundled_game_assets_verified'])
        self.assertTrue(result['bootstrap_inventory_signed'])
        self.assertTrue(result['all_manifest_assets_retain_github_transport'])
        self.assertFalse(result['runtime_verified'])

    def test_default_strict_mode_still_rejects_bundled_startup_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            apk=Path(td)/'bootstrap.apk';self.make_apk(apk)
            with self.assertRaisesRegex(ValueError,'bundles game data|bootstrap allowlist'):
                g.qualify(self.manifest_data,self.catalogs,self.release,self.catalogs['base'],apk,expected_version=204,expected_asset_version=203,runner=fake_tool)

    def test_metadata_only_inventory_cannot_claim_signed_or_checked_bytes(self):
        result=g.qualify(self.manifest_data,self.catalogs,self.release,self.catalogs['base'],expected_version=204,expected_asset_version=203,bootstrap_inventory_data=self.inventory_data)
        self.assertEqual(result['bundled_game_asset_count'],1)
        self.assertFalse(result['signed_apk_qualified'])
        self.assertFalse(result['bootstrap_inventory_signed'])
        self.assertFalse(result['bundled_game_assets_verified'])

    def test_changed_same_size_or_wrong_size_startup_bytes_rejected(self):
        for payload,error in [(b'y','asset hash differs'),(b'xx','asset size differs')]:
            with self.subTest(payload=payload),tempfile.TemporaryDirectory() as td:
                apk=Path(td)/'changed.apk';self.make_apk(apk,{'assets/cpk/common.cpk':payload})
                with self.assertRaisesRegex(ValueError,error):self.verify(apk)

    def test_missing_startup_file_and_unlisted_game_asset_rejected(self):
        for payloads in [{},{'assets/cpk/common.cpk':b'x','assets/side_stories/shared.dat':b'x'},{'assets/cpk/common.cpk':b'x','assets/asset_bundle.zip':b'x'}]:
            with self.subTest(paths=list(payloads)),tempfile.TemporaryDirectory() as td:
                apk=Path(td)/'wrong-members.apk';self.make_apk(apk,payloads)
                with self.assertRaisesRegex(ValueError,'bootstrap allowlist'):self.verify(apk)

    def test_signed_inventory_must_equal_exact_supplied_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            apk=Path(td)/'inventory-mismatch.apk';self.make_apk(apk,signed_inventory=self.inventory_data+b'\n')
            with self.assertRaisesRegex(ValueError,'Signed APK bootstrap inventory differs'):self.verify(apk)

    def test_manifest_pin_hash_size_version_and_identity_mismatch_rejected(self):
        changes=[
            (lambda i:i.update(manifest_sha256='a'*64),'manifest pin'),
            (lambda i:i.update(APK_version=203),'APK version'),
            (lambda i:i.update(asset_version=204),'asset version'),
            (lambda i:i.update(package='changed.package'),'app identity'),
            (lambda i:i.update(signing_certificate_sha256='a'*64),'app identity'),
            (lambda i:i['assets'][0].update(sha256='a'*64),'per-file manifest'),
            (lambda i:i['assets'][0].update(bytes=2),'per-file manifest'),
            (lambda i:i['assets'][0].pop('sha256'),'hash/size missing'),
        ]
        for change,error in changes:
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError,error):g.validate_bootstrap_inventory(self.mutate_inventory(change),self.manifest_data,204)

    def test_nonboot_nonroot_unsafe_alias_duplicate_and_bulk_zip_rows_rejected(self):
        shared=next(e for e in self.manifest['assets'] if e['namespace']=='root' and e['phase']=='game')
        shared_row={k:shared[k] for k in ('namespace','path','sha256','bytes')};shared_row['apk_path']='assets/'+shared['path']
        changes=[
            (lambda i:i['assets'].append(shared_row),'non-startup'),
            (lambda i:i['assets'][0].update(namespace='content'),'safe native root'),
            (lambda i:i['assets'][0].update(path='../cpk/common.cpk'),'safe native root'),
            (lambda i:i['assets'][0].update(apk_path='assets/other/common.cpk'),'APK path differs'),
            (lambda i:i['assets'].append(copy.deepcopy(i['assets'][0])),'Duplicate'),
            (lambda i:i['assets'][0].update(path='asset_bundle.zip',apk_path='assets/asset_bundle.zip'),'bulk ZIP'),
        ]
        for change,error in changes:
            with self.subTest(error=error):
                with self.assertRaisesRegex(ValueError,error):g.validate_bootstrap_inventory(self.mutate_inventory(change),self.manifest_data,204)

    def test_every_manifest_startup_asset_is_required_even_if_apk_omits_it(self):
        manifest=copy.deepcopy(self.manifest)
        shared=next(e for e in manifest['assets'] if e['namespace']=='root' and e['phase']=='game');shared['phase']='boot'
        manifest_data=json.dumps(manifest).encode()
        inventory=make_inventory(manifest_data);inventory['assets'].pop()
        with self.assertRaisesRegex(ValueError,'missing a required startup'):
            g.validate_bootstrap_inventory(json.dumps(inventory).encode(),manifest_data,204)

    def test_empty_allowlist_and_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'no exact asset allowlist'):
            g.validate_bootstrap_inventory(self.mutate_inventory(lambda i:i.update(assets=[])),self.manifest_data,204)
        bad=self.inventory_data[:-1]+b',"APK_version":204}'
        with self.assertRaisesRegex(ValueError,'Duplicate JSON'):
            g.validate_bootstrap_inventory(bad,self.manifest_data,204)

    def test_shared_identical_root_content_file_is_counted_as_bundled_once(self):
        manifest=copy.deepcopy(self.manifest)
        for e in manifest['assets']:
            if e['namespace']=='root':e['phase']='boot'
        manifest_data=json.dumps(manifest).encode();inventory_data=json.dumps(make_inventory(manifest_data)).encode()
        selected,result=g.validate_bootstrap_inventory(inventory_data,manifest_data,204)
        self.assertEqual(len(selected),2)
        self.assertEqual(result['bundled_game_asset_count'],2)
        self.assertEqual(result['bundled_game_asset_bytes'],2)
        self.assertEqual(result['bundled_manifest_asset_rows'],3)
        self.assertEqual(result['external_only_manifest_asset_rows'],4537)

    def test_old_counter_cannot_admit_bootstrap_mode(self):
        inventory=make_inventory(self.manifest_data,203)
        with self.assertRaisesRegex(ValueError,'must exceed203'):
            g.validate_bootstrap_inventory(json.dumps(inventory).encode(),self.manifest_data,203)

    def test_historical_bulk_bootstrap_dex_rejected_in_new_inventory_mode(self):
        bad=fixture_dex()+b'LO1/BundleAssets;'
        with tempfile.TemporaryDirectory() as td:
            apk=Path(td)/'legacy-bootstrap.apk';self.make_apk(apk,dex=bad)
            with self.assertRaisesRegex(ValueError,'custom bulk ZIP bootstrap classes'):self.verify(apk)

    def test_frozen_historical_apks_cannot_pass_new_inventory_mode(self):
        for apk in OLD_APKS:
            self.assertTrue(apk.is_file(),'Frozen historical APK unavailable: '+str(apk))
            with self.subTest(apk=apk.name):
                with self.assertRaisesRegex(ValueError,'bundles game data|bootstrap allowlist'):
                    g.verify_apk(apk,self.catalogs,self.release,204,manifest_data=self.manifest_data,bootstrap_inventory_data=self.inventory_data,runner=lambda a:self.fail('Historical APK must fail before tool execution'))


if __name__=='__main__':unittest.main()
