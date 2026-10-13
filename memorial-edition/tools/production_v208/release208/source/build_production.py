"""Package finite banner/order descriptors over the exact published build207."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, os, re, struct, subprocess, zipfile
ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT.parent/'v207-download-spacing'
PROJECT=Path(r'T:\Projects\FFBE Patch')
BASELINE=PREVIOUS/'staged_build/dist/FFBE-Memorial-EN-Download-Spacing-v207.apk'
BASELINE_SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
QUAL_SHA='1368c69047515c6f36a7500144ec2da4c23e430fbbe16e9b22bbb471a6513f17'
SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
OPERATIONS=[
    (b'const PATCH_VERSION = 207;',b'const PATCH_VERSION = 208;'),
    (b'const MANIFEST_URL   = "https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json";',b'const MANIFEST_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json";'),
    (b'const DOWNLOAD_URL   = "https://ffbe.luminest.io/downloads/beta/";',b'const DOWNLOAD_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest";'),
]
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main():
    assert sha(BASELINE)==BASELINE_SHA
    qual_path=PREVIOUS/'staged_build/SIGNED_SPACING_QUALIFICATION.json'
    assert sha(qual_path)==QUAL_SHA
    qualified=json.loads(qual_path.read_bytes());assert qualified['passed'] and qualified['apk_sha256']==BASELINE_SHA
    plan_path=ROOT/'asset_publication/DOWNLOAD_PLAN.json';plan_pin=sha(plan_path);plan=json.loads(plan_path.read_bytes())
    assert plan['passed'] and plan['original_content_rows']==plan['final_content_rows']==1898
    prior=json.loads((PREVIOUS/'staged_build/DOWNLOAD_SPACING_APK_BUILD.json').read_bytes())
    source_pins={p.name:sha(p) for p in (ROOT/'source').glob('*') if p.is_file()}
    out=ROOT/'staged_build';build=out/'build'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f');logs=build/'logs';logs.mkdir(parents=True,exist_ok=False)
    def run(args,name,env=None):
        result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600)
        (logs/name).write_text(result.stdout+result.stderr,encoding='utf-8');assert result.returncode==0,name
        return result.stdout+result.stderr
    with zipfile.ZipFile(BASELINE) as archive:
        manifest=bytearray(archive.read('AndroidManifest.xml'));offset=prior['manifest_edits'][0]['offset']
        assert manifest[offset-1]==16 and struct.unpack_from('<I',manifest,offset)[0]==207
        struct.pack_into('<I',manifest,offset,208)
        original=archive.read('assets/frida_script.js');assert digest(original)=='d766347efe033dbeb2bc358e99c6cf74385da95d19a0528d20f8841bacd0d696'
        script=original
        for before,after in OPERATIONS:
            assert script.count(before)==1
            script=script.replace(before,after)
    catalog=(ROOT/'payload/content_delivery.tsv').read_bytes();side=(ROOT/'payload/side_stories/manifest.tsv').read_bytes()
    assert digest(catalog)==plan['content_catalog_sha256'] and digest(side)==plan['side_manifest_sha256']
    (build/'frida_script.js').write_bytes(script);run(['node','--check',build/'frida_script.js'],'javascript.txt')
    module_path=PROJECT/'story-ports/side-stories/scripts/apk_zip.py';spec=importlib.util.spec_from_file_location('literal_apk_zip',module_path);apkzip=importlib.util.module_from_spec(spec);spec.loader.exec_module(apkzip)
    replacements={'AndroidManifest.xml':bytes(manifest),'assets/frida_script.js':script,'assets/content_delivery.tsv':catalog,'assets/side_stories/manifest.tsv':side}
    unsigned=build/'unsigned.apk';apkzip.replace_entries(BASELINE,unsigned,replacements)
    tools=PROJECT/'graphics-localization/2026-09-19/apk-build/tools/android-16';aligned=build/'aligned.apk'
    run([tools/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'alignment.txt')
    dist=out/'dist';dist.mkdir(parents=True,exist_ok=True);signed=dist/'FFBE-Memorial-EN-Global-Events-v208.apk';assert not signed.exists()
    note=(PROJECT/'tools/keys/KEYSTORE_README.txt').read_text();env=os.environ.copy()
    env['FFBE_PROD_STORE']=re.search(r'^Storepass:\s+(\S+)',note,re.M)[1];env['FFBE_PROD_KEY']=re.search(r'^Keypass:\s+(\S+)',note,re.M)[1]
    signer=['java','-jar',tools/'lib/apksigner.jar']
    run(signer+['sign','--ks',PROJECT/'tools/keys/ffbe-instrumented.keystore','--ks-key-alias','ffbe','--ks-pass','env:FFBE_PROD_STORE','--key-pass','env:FFBE_PROD_KEY','--v4-signing-enabled','false','--out',signed,aligned],'sign.txt',env)
    assert SIGNER in run(signer+['verify','--verbose','--print-certs',signed],'signature.txt')
    run([tools/'zipalign.exe','-c','-P','16','4',signed],'alignment-check.txt')
    badging=run([tools/'aapt2.exe','dump','badging',signed],'package.txt')
    assert "name='com.square_enix.ffbejpn'" in badging and "versionCode='208'" in badging and 'application-debuggable' not in badging
    with zipfile.ZipFile(BASELINE) as before,zipfile.ZipFile(signed) as after:
        assert after.testzip() is None
        assert {n for n in before.namelist() if not apkzip.signature(n)}=={n for n in after.namelist() if not apkzip.signature(n)}
        for name in before.namelist():
            if not apkzip.signature(name):assert after.read(name)==replacements.get(name,before.read(name)),name
    for name,pin in source_pins.items():assert sha(ROOT/'source'/name)==pin
    assert sha(plan_path)==plan_pin and sha(BASELINE)==BASELINE_SHA
    report={'schema':'ffbe-production208-apk-v1','apk':str(signed),'bytes':signed.stat().st_size,'sha256':sha(signed),'versionCode':208,'versionName':'11.1.1','package':'com.square_enix.ffbejpn','signer_sha256':SIGNER,'baseline_apk':str(BASELINE),'baseline_apk_sha256':BASELINE_SHA,'foundation_patch5_sha256':'534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208','source_qualification_sha256':QUAL_SHA,'source_pins':source_pins,'changed_members':list(replacements),'download_plan_sha256':plan_pin,'content_catalog_sha256':digest(catalog),'side_manifest_sha256':digest(side),'asset_file_count':170,'new_apk_members':0,'classes_dex_byte_identical_to207':True,'native_libraries_unchanged':True,'startup_assets_unchanged':True,'downloader_unchanged':True,'movies_unchanged':True,'zip_alignment_16k_verified':True,'native_ELF_16k_compatibility_verified':False,'runtime_verified':False,'physical_phone_test':'pending','save_migration_verified':False,'published':False,'build':str(build),'manifest_edits':[{'offset':offset,'before':207,'after':208}],'script_operations':[{'before':a.decode(),'after':b.decode(),'count':1} for a,b in OPERATIONS]}
    (out/'PRODUCTION_APK_BUILD.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('apk','bytes','sha256','versionCode')}))
if __name__=='__main__':main()
