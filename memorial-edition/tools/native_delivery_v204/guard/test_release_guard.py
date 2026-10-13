import copy
import hashlib
import json
import os
import struct
from pathlib import Path
import tempfile
import unittest
import zipfile
import release_guard as g

URL=f'https://github.com/{g.REPO}/releases/download/content-v1/data.pack#ffbe-range=0:1:1'
H=hashlib.sha256(b'x').hexdigest()
WORKSPACE=Path(os.environ.get('FFBE_RELEASE_WORKSPACE',r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2'))
OLD_APKS=[Path(os.environ.get('FFBE_FROZEN_V201_APK',str(WORKSPACE/'integration_work/full_inventory/recovery_round2/build_release/FFBE-Memorial-EN-Patch-6-Full-Inventory-Round2.apk'))),Path(os.environ.get('FFBE_FROZEN_V202_APK',str(WORKSPACE/'integration_work/thin_delivery/dist/FFBE-Memorial-EN-Patch-6-Thin-Round2-v202.apk')))]

def build_fixture():
    roots=['cpk/common.cpk','side_stories/shared.dat']
    contents=['side_stories/shared.dat']+[f'battle/{i}.dat' for i in range(1410)]
    row=lambda p:f'{p}\t{H}\t1\t{URL}\t0\t1\t0\t1\n'
    catalogs={'root':('ffbe-content-v1\n'+''.join(row(p) for p in roots)).encode(),'content':('ffbe-content-v1\n'+''.join(row(p) for p in contents)).encode(),'base':('ffbe-base-v1\n'+''.join(f'on_demand_asset\t{i}.dat\t1\t{H}\t{URL}\n' for i in range(3127))).encode()}
    m={'schema':'ffbe-asset-manifest-v1','channel':'beta','package':g.PACKAGE,'signing_certificate_sha256':g.SIGNER,'asset_version':203,'APK_min_version':203,'engine_compat':g.ENGINE,'assets':[]}
    for namespace,data in catalogs.items():
        m[namespace+'_catalog']={'sha256':g.digest(data),'bytes':len(data),'url':f'https://github.com/{g.REPO}/releases/download/beta-content-v203-fixture/{namespace}_delivery.tsv'}
        for e in g.parse_catalog(data,namespace).values():
            e['version']=1
            if namespace=='root':e['phase']='boot' if e['path'].startswith('cpk/') else 'game'
            m['assets'].append(e)
    release=('ffbe-delivery-release-v1\nbeta\t203\t203\t'+g.digest(catalogs['root'])+'\t'+g.digest(catalogs['content'])+'\t'+g.BETA_PREFIX+'patch_version.json\t'+g.BETA_PREFIX+'manifest.json\n').encode()
    return m,catalogs,release

def fixture_dex(class_name='LO1/PatchUpdater;',method_name='check',flags=9):
    def leb(n):
        b=bytearray()
        while True:
            q=n&127;n>>=7;b.append(q|(128 if n else 0))
            if not n:return bytes(b)
    strings=[class_name,'V',method_name];data=bytearray(184);offsets=[]
    for s in strings:
        offsets.append(len(data));data.extend(leb(len(s))+s.encode()+b'\0')
    classdata=len(data);code=(classdata+8+3)&~3
    records=b'\0\0\1\0'+b'\0'+leb(flags)+leb(code)
    if classdata+len(records)>code:code=(classdata+len(records)+3)&~3;records=b'\0\0\1\0'+b'\0'+leb(flags)+leb(code)
    data.extend(records);data.extend(b'\0'*(code-len(data)));data.extend(struct.pack('<HHHHIIH',0,0,0,0,0,1,14))
    data[:8]=b'dex\n035\0';struct.pack_into('<III',data,32,len(data),112,0x12345678)
    for at,n,off in [(56,3,112),(64,2,124),(72,1,132),(88,1,144),(96,1,152),(104,len(data)-184,184)]:struct.pack_into('<II',data,at,n,off)
    for i,off in enumerate(offsets):struct.pack_into('<I',data,112+i*4,off)
    struct.pack_into('<II',data,124,0,1);struct.pack_into('<III',data,132,1,1,0);struct.pack_into('<HHI',data,144,0,0,2)
    struct.pack_into('<IIIIIIII',data,152,0,1,0xffffffff,0,0xffffffff,0,classdata,0)
    return bytes(data)

def make_apk(path,catalogs,release,extra=None,script=None,dex=None,manifest_data=None):
    script=script or f'const PATCH_VERSION = 203;\nconst MANIFEST_URL = "{g.BETA_PREFIX}patch_version.json";\nconst DOWNLOAD_URL = "https://ffbe.luminest.io/downloads/beta/";\njniCallStaticVoid("O1/PatchUpdater", "check", "()V", []);\n'
    manifest_data=manifest_data or json.dumps(build_fixture()[0]).encode()
    with zipfile.ZipFile(path,'w') as z:
        for name in g.ALLOWED_ASSETS:
            if name=='assets/frida_script.js':b=script.encode()
            elif name=='assets/game_asset_manifest.json':b=manifest_data
            elif name=='assets/delivery_release.tsv':b=release
            elif name.endswith('_delivery.tsv'):b=catalogs[name.split('/')[-1].split('_')[0]]
            else:b=b'executable/profile fixture'
            z.writestr(name,b)
        z.writestr('classes.dex',dex or fixture_dex())
        z.writestr('AndroidManifest.xml',b'Synthetic interface fixture, not a real signed Android APK')
        if extra:z.writestr(extra,b'x')

class ActualReleaseRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m,cls.catalogs,cls.release=build_fixture()
    def test_complete_native_graph_and_shared_identical_path_pass(self):
        r=g.qualify(json.dumps(self.m).encode(),self.catalogs,self.release,self.catalogs['base'])
        self.assertEqual(r['namespace_counts'],{'root':2,'content':1411,'base':3127});self.assertEqual(r['root_content_shared_paths'],1)
    def test_actual_schema_requires_every_per_file_version(self):
        m=copy.deepcopy(self.m);del m['assets'][0]['version']
        with self.assertRaisesRegex(ValueError,'Per-file'):g.validate_manifest(m,self.catalogs)
    def test_root_and_content_mismatched_identity_rejected(self):
        catalogs=dict(self.catalogs);catalogs['root']=catalogs['root'].replace(H.encode(),b'a'*64)
        m=copy.deepcopy(self.m);m['root_catalog'].update(sha256=g.digest(catalogs['root']),bytes=len(catalogs['root']))
        for e in m['assets']:
            if e['namespace']=='root':e['sha256']='a'*64
        with self.assertRaisesRegex(ValueError,'conflicting bytes'):g.validate_manifest(m,catalogs)
    def test_descriptor_json_transport_mismatch_rejected(self):
        m=copy.deepcopy(self.m);m['assets'][0]['transport']['url']=URL.replace('data.pack','other.pack')
        with self.assertRaisesRegex(ValueError,'record mismatch'):g.validate_manifest(m,self.catalogs)
    def test_missing_graph_member_and_duplicate_rejected(self):
        for m in [dict(self.m,assets=self.m['assets'][1:]),dict(self.m,assets=self.m['assets']+[self.m['assets'][0]])]:
            with self.assertRaises(ValueError):g.validate_manifest(m,self.catalogs)
    def test_changed_same_size_requires_new_asset_revision(self):
        old=copy.deepcopy(self.m);old['assets'][0]['sha256']='a'*64
        with self.assertRaisesRegex(ValueError,'revision increment'):g.validate_manifest(self.m,self.catalogs,old)
        m=copy.deepcopy(self.m);m['assets'][0]['version']=2
        self.assertEqual(g.validate_manifest(m,self.catalogs,old)['per_file_versions_verified'],4540)
    def test_version_rollback_wrong_channel_or_engine_rejected(self):
        for key,value in [('channel','prod'),('package','wrong.package'),('signing_certificate_sha256','a'*64),('engine_compat','custom-zip'),('APK_min_version',204),('APK_min_version',202),('asset_version',False)]:
            m=copy.deepcopy(self.m);m[key]=value
            with self.assertRaises(ValueError):g.validate_manifest(m,self.catalogs)
        old=copy.deepcopy(self.m);old['asset_version']=204
        with self.assertRaisesRegex(ValueError,'rollback'):g.validate_manifest(self.m,self.catalogs,old)
    def test_wrong_catalog_hash_or_base_bytes_rejected(self):
        m=copy.deepcopy(self.m);m['base_catalog']['sha256']='a'*64
        with self.assertRaisesRegex(ValueError,'pin mismatch'):g.validate_manifest(m,self.catalogs)
        with self.assertRaisesRegex(ValueError,'base descriptor'):g.qualify(json.dumps(self.m).encode(),self.catalogs,self.release,b'wrong')
    def test_transport_rejects_hostinger_other_repo_latest_and_unsafe_paths(self):
        for url in ['https://ffbe.luminest.io/pack.zip',URL.replace(g.REPO,'other/repo'),f'https://github.com/{g.REPO}/releases/latest/download/pack.bin',URL+'?token=bad']:
            t=dict(self.m['assets'][0]['transport'],url=url)
            with self.assertRaises(ValueError):g.validate_transport(t,1)
        for p in ['../save.dat','/save.dat','a\\b.dat','a//b.dat']:
            self.assertFalse(g.safe_path(p))
    def test_fragment_and_inner_bounds_rejected(self):
        for t in [dict(self.m['assets'][0]['transport'],url=URL.replace('0:1:1','1:1:1')),dict(self.m['assets'][0]['transport'],source_bytes=2),dict(self.m['assets'][0]['transport'],offset=1),dict(self.m['assets'][0]['transport'],method=9)]:
            with self.assertRaises(ValueError):g.validate_transport(t,1)
    def test_native_release_metadata_binds_channel_counter_hashes(self):
        for data in [self.release.replace(b'beta\t',b'prod\t'),self.release.replace(b'203\t203',b'203\t202'),self.release.replace(g.BETA_PREFIX.encode(),b'https://example.com/')]:
            with self.assertRaises(ValueError):g.validate_release_metadata(data,self.catalogs,203,203)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError,'Duplicate JSON'):g.load_json(b'{"channel":"beta","channel":"prod"}')
    def test_original_crlf_base_preservation_and_strict_release_lf(self):
        catalogs=dict(self.catalogs);catalogs['base']=catalogs['base'].replace(b'\n',b'\r\n')
        m=copy.deepcopy(self.m);m['base_catalog'].update(sha256=g.digest(catalogs['base']),bytes=len(catalogs['base']))
        self.assertEqual(g.validate_manifest(m,catalogs)['namespace_counts']['base'],3127)
        with self.assertRaisesRegex(ValueError,'LF-only'):g.validate_release_metadata(self.release.replace(b'\n',b'\r\n'),catalogs,203,203)
    def test_synthetic_apk_interface_invokes_real_tool_contract(self):
        calls=[]
        def fake_tool(args):
            calls.append(list(map(str,args)))
            if 'badging' in args:return f"package: name='{g.PACKAGE}' versionCode='203' versionName='11.1.1'\n"
            if '--print-certs' in args:return 'Verifies\nSigner #1 certificate SHA-256 digest: '+g.SIGNER+'\n'
            return 'Verification successful'
        with tempfile.TemporaryDirectory() as td:
            apk=Path(td)/'good.apk';make_apk(apk,self.catalogs,self.release)
            result=g.qualify(json.dumps(self.m).encode(),self.catalogs,self.release,self.catalogs['base'],apk,runner=fake_tool)
            self.assertEqual(result['version_code'],203);self.assertEqual(len(calls),3);self.assertIn('verify',calls[1]);self.assertIn('--print-certs',calls[1]);self.assertIn('16',calls[2])
    def test_actual_tool_package_signer_failure_rejected(self):
        for bad in ('package','signer'):
            def fake_tool(args):
                if 'badging' in args:return f"package: name='{g.PACKAGE if bad!='package' else 'changed.package'}' versionCode='203'\n"
                return 'Signer #1 certificate SHA-256 digest: '+('a'*64 if bad=='signer' else g.SIGNER)
            with tempfile.TemporaryDirectory() as td:
                apk=Path(td)/'bad.apk';make_apk(apk,self.catalogs,self.release)
                with self.assertRaises(ValueError):g.verify_apk(apk,self.catalogs,self.release,runner=fake_tool,manifest_data=json.dumps(self.m).encode())
    def test_synthetic_bundled_data_custom_bootstrap_and_wrong_updater_rejected(self):
        badscript=f'const PATCH_VERSION=203; const MANIFEST_URL="https://github.com/{g.REPO}/releases/latest/download/patch_version.json";'
        badcounter=f'const PATCH_VERSION=202; const MANIFEST_URL="{g.BETA_PREFIX}patch_version.json";'
        for kwargs in [{'extra':'assets/cpk/common.cpk'},{'dex':b'dex\n035\0LO1/BundleAssets;'},{'script':badscript},{'script':badcounter}]:
            with tempfile.TemporaryDirectory() as td:
                apk=Path(td)/'bad.apk';make_apk(apk,self.catalogs,self.release,**kwargs)
                with self.assertRaises(ValueError):g.verify_apk(apk,self.catalogs,self.release,runner=lambda a:'',manifest_data=json.dumps(self.m).encode())
    def test_new_native_adapter_and_actual_dex_class_required(self):
        good=f'const PATCH_VERSION=203; const MANIFEST_URL="{g.BETA_PREFIX}patch_version.json"; const DOWNLOAD_URL="https://ffbe.luminest.io/downloads/beta/";\n'
        new='jniCallStaticVoid("O1/PatchUpdater", "check", "()V", []);'
        legacy='jniCallStaticVoid(JAVA_CLASS, "checkForUpdate", "(ILjava/lang/String;Ljava/lang/String;)V", [PATCH_VERSION, MANIFEST_URL, DOWNLOAD_URL]);'
        for kwargs in [{'script':good+legacy},{'script':good+new+legacy},{'script':good+'// '+new},{'dex':fixture_dex(class_name='LO1/Other;')+b'LO1/PatchUpdater;'}, {'dex':fixture_dex(method_name='wrong')}, {'dex':fixture_dex(flags=1)}, {'manifest_data':b'{"wrong":"baseline"}'}]:
            with tempfile.TemporaryDirectory() as td:
                apk=Path(td)/'bad.apk';make_apk(apk,self.catalogs,self.release,**kwargs)
                with self.assertRaises(ValueError):g.verify_apk(apk,self.catalogs,self.release,runner=lambda a:'',manifest_data=json.dumps(self.m).encode())
    def test_legacy_optional_cg_networking_cannot_return(self):
        good=f'const PATCH_VERSION=203; const MANIFEST_URL="{g.BETA_PREFIX}patch_version.json"; const DOWNLOAD_URL="https://ffbe.luminest.io/downloads/beta/"; jniCallStaticVoid("O1/PatchUpdater", "check", "()V", []);\n'
        bad=['const CDN_BASE="https://cdn.luminest.io/ffbe/movies/";','function fireCurl(name,url) {}','fireCurl(name,url);','jniCallStaticVoid(JAVA_CLASS, "requestDownload", "(Ljava/lang/String;Ljava/lang/String;)V", [name,url]);','requestDownload(name,url);']
        for extra in bad:
            with tempfile.TemporaryDirectory() as td:
                apk=Path(td)/'bad-movie-network.apk';make_apk(apk,self.catalogs,self.release,script=good+extra)
                with self.assertRaisesRegex(ValueError,'Legacy'):g.verify_apk(apk,self.catalogs,self.release,runner=lambda a:'',manifest_data=json.dumps(self.m).encode())
    def test_commented_old_movie_route_is_not_executable_evidence(self):
        text='// const CDN_BASE="https://cdn.luminest.io/ffbe/movies/";\n/* fireCurl(name,url); requestDownload(name,url); */\nconst safe="https://github.com/keep/url";'
        uncommented=g.uncomment_js(text)
        self.assertNotIn('fireCurl',uncommented);self.assertNotIn('requestDownload',uncommented);self.assertNotIn('cdn.luminest.io',uncommented);self.assertIn('https://github.com/keep/url',uncommented)
    def test_actual_v201_and_v202_cannot_regress_into_qualified_release(self):
        for apk in OLD_APKS:
            self.assertTrue(apk.is_file(),'Frozen historical APK unavailable: '+str(apk))
            with self.subTest(apk=apk.name):
                with self.assertRaisesRegex(ValueError,'bundles game data|bootstrap allowlist'):
                    g.verify_apk(apk,self.catalogs,self.release,runner=lambda a: self.fail('Old APK must fail before tool execution'))

if __name__=='__main__':unittest.main()
