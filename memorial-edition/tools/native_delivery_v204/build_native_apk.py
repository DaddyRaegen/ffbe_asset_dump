"""Build only: production Patch 5 baseline plus expanded events and per-file delivery.

Never publishes, installs, touches runtime state, commits, or clears anything.
All outputs go to a fresh local directory. Passwords stay in child environment.
"""
from pathlib import Path
import argparse,copy,datetime,hashlib,importlib.util,json,os,re,shutil,subprocess,zipfile

ROOT=Path(__file__).resolve().parent
BASELINE_SHA='534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
SCRIPT_SHA='31a87e1c3deff7f22d692f5a35d476db76b3d0f6639eb0c487fda9b91fb02b44'
SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
KEEP={'assets/frida_script.js','assets/arm64-v8a/libparser.so','assets/armeabi-v7a/libparser.so','assets/dexopt/baseline.prof','assets/dexopt/baseline.profm'}
META=('base_delivery.tsv','content_delivery.tsv','root_delivery.tsv','delivery_release.tsv','game_asset_manifest.json','bootstrap_inventory.json')

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def scripted(original,adapter,version_code):
    assert hashlib.sha256(original).hexdigest()==SCRIPT_SHA
    event_port=load_module('patch5_event_script',ROOT/'patch5_event_script.py')
    text=event_port.port_events(original).decode('utf-8')
    replacements={
        "const PAYLOAD_DIR = '/data/user/0/com.square_enix.ffbejpn/files/plate_swaps';":"const PAYLOAD_DIR = globalThis.FFBE_GAME_ASSET_ROOT + 'plate_pack';",
        'const PATCH_VERSION = 6;':'const PATCH_VERSION = '+str(version_code)+';',
        'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json':'https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json',
        'const DOWNLOAD_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest";':'const DOWNLOAD_URL   = "https://ffbe.luminest.io/downloads/beta/";',
    }
    for before,after in replacements.items():
        assert text.count(before)==1,before;text=text.replace(before,after)
    pattern=r'jniCallStaticVoid\(JAVA_CLASS,\s*"checkForUpdate",\s*"\(ILjava/lang/String;Ljava/lang/String;\)V",\s*\[PATCH_VERSION,\s*MANIFEST_URL,\s*DOWNLOAD_URL\]\);'
    text,count=re.subn(pattern,'jniCallStaticVoid("O1/PatchUpdater", "check", "()V", []);',text)
    assert count==1,'Exact baseline updater invocation not found'
    # The inherited optional CG hook fetched unmanifested files with curl and a
    # second Java HTTP downloader. Preserve the native movie/sprite path instead.
    # Source coverage for the additional local movie candidates is reported;
    # those bytes must be qualified before entering the native versioned graph.
    start=text.index('    const CDN_BASE = "https://cdn.luminest.io/ffbe/movies/";')
    end=text.index('    // ---- JNI bridge ----',start)
    text=text[:start]+'''    // Movies resolve through the verified native per-file catalog and e.k.
    // Unavailable source movies retain the game's original sprite fallback.
    const SYM_JNIHELPER_GETSMI =
        "_ZN7cocos2d9JniHelper19getStaticMethodInfoERNS_14JniMethodInfo_EPKcS4_S4_";

'''+text[end:]
    start=text.index('    function lbDialogRequest(filename) {')
    end=text.index('    // ---- Version check on app launch ----',start)
    text=text[:start]+'    initJni();\n\n'+text[end:]
    assert 'cdn.luminest.io/ffbe/movies' not in text and 'function fireCurl' not in text
    assert '"requestDownload"' not in text
    return (adapter.read_text(encoding='utf-8')+'\n'+text).encode('utf-8')

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=ROOT/'build_config.json');args=p.parse_args()
    cfg=json.loads(args.config.read_bytes())
    version_code=int(cfg['version_code']);assert version_code==204
    source=Path(cfg['source_apk']);patch=Path(cfg['project']);native=Path(cfg.get('native_source',ROOT/'native_audit'))
    payload=Path(cfg.get('payload',ROOT/'payload'));manifest=Path(cfg.get('asset_manifest',ROOT/'asset_publication/manifest.json'))
    inventory=json.loads((payload/'bootstrap_inventory.json').read_bytes())
    assert inventory['schema']=='ffbe-bootstrap-inventory-v1' and inventory['APK_version']==version_code
    assert inventory['manifest_sha256']==sha(manifest) and inventory['package']=='com.square_enix.ffbejpn' and inventory['signing_certificate_sha256']==SIGNER
    graph=json.loads(manifest.read_bytes());expected_boot={a['path']:a for a in graph['assets'] if a['namespace']=='root' and a['phase']=='boot'}
    assert len(expected_boot)==len(inventory['assets'])==162
    bundled=set()
    for entry in inventory['assets']:
        assert entry['namespace']=='root' and entry['apk_path']=='assets/'+entry['path']
        a=expected_boot[entry['path']];assert entry['sha256']==a['sha256'] and entry['bytes']==a['bytes']
        local=payload/entry['path'];assert sha(local)==entry['sha256'] and local.stat().st_size==entry['bytes']
        assert entry['apk_path'] not in bundled;bundled.add(entry['apk_path'])
    out=Path(cfg.get('output',ROOT/'staged_build'));build=out/'build'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    bt=patch/'graphics-localization/2026-09-19/apk-build/tools/android-16';android=patch/'story-ports/side-stories/delivery/android.jar'
    assert sha(source)==BASELINE_SHA
    for d in ('classes','dex','logs','decoded'): (build/d).mkdir(parents=True,exist_ok=False)
    def run(command,name,env=None):
        r=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600)
        (build/'logs'/name).write_text(r.stdout+r.stderr,encoding='utf-8')
        if r.returncode:raise RuntimeError(name+': '+str(r.returncode)+'; inspect local log')
        return r.stdout+r.stderr
    sources=sorted((native/'java/O1').glob('*.java'));assert sources
    source_pins={str(f.relative_to(native)):sha(f) for f in sources+[native/'patch_smali.py',native/'native_game_assets.js',native/'patch5_event_script.py',native/'manifest_patch.py',native/'build_native_apk.py']}
    run(['javac','-encoding','UTF-8','--release','8','-cp',android,'-d',build/'classes',*sources],'javac.txt')
    classes=sorted((build/'classes').rglob('*.class'));assert classes
    run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','21','--lib',android,'--output',build/'dex',*classes],'d8.txt')
    manifest_patch=load_module('native_manifest_patch',ROOT/'manifest_patch.py')
    with zipfile.ZipFile(source) as z:
        (build/'original.dex').write_bytes(z.read('classes.dex'))
        assert bundled.issubset(z.namelist())
        for entry in inventory['assets']:assert hashlib.sha256(z.read(entry['apk_path'])).hexdigest()==entry['sha256']
        android_manifest,manifest_edits=manifest_patch.patch_manifest(z.read('AndroidManifest.xml'),version_code)
        script=scripted(z.read('assets/frida_script.js'),native/'native_game_assets.js',version_code)
    (build/'frida_script.js').write_bytes(script);run([cfg.get('node','node'),'--check',build/'frida_script.js'],'javascript-check.txt')
    baksmali=patch/'tools/bin/baksmali.jar'
    run(['java','-jar',baksmali,'d',build/'original.dex','-o',build/'base-smali'],'baksmali-original.txt')
    run(['java','-jar',baksmali,'d',build/'dex/classes.dex','-o',build/'new-smali'],'baksmali-overlay.txt')
    overlay=[]
    before_pins={f.relative_to(build/'base-smali').as_posix():sha(f) for f in (build/'base-smali').rglob('*.smali')}
    for f in (build/'new-smali').rglob('*.smali'):
        rel=f.relative_to(build/'new-smali');assert rel.parts[0]=='O1'
        dest=build/'base-smali'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);overlay.append(rel.as_posix())
    patches=load_module('native_smali_patch',native/'patch_smali.py').patch_smali(build/'base-smali')
    expected_changed=set(overlay)|{('com/square_enix/ffbejpn/FridaBootstrap' if x['class']=='FridaBootstrap' else x['class'])+'.smali' for x in patches}
    for name,h in before_pins.items():
        if name not in expected_changed:assert sha(build/'base-smali'/name)==h,name
    preserved_classes=len(set(before_pins)-expected_changed)
    skeleton=patch/'story-ports/side-stories/delivery/decoded'
    for name in ('apktool.yml','AndroidManifest.xml','resources.arsc'):shutil.copy2(skeleton/name,build/'decoded'/name)
    shutil.copytree(build/'base-smali',build/'decoded/smali')
    run(['java','-jar',patch/'tools/bin/apktool.jar','b',build/'decoded','-o',build/'dex-container.apk'],'smali-build.txt')
    with zipfile.ZipFile(build/'dex-container.apk') as z:dex=z.read('classes.dex')
    for s in (b'LO1/AssetBundle;',b'LO1/BundleAssets;',b'LO1/BootstrapActivity;'):assert s not in dex
    sig=lambda n:n.upper()=='META-INF/MANIFEST.MF' or bool(re.fullmatch(r'META-INF/[^/]+\.(SF|RSA|DSA|EC)',n,re.I))
    unsigned=build/'unsigned.apk';changed={'AndroidManifest.xml':android_manifest,'classes.dex':dex,'assets/frida_script.js':script}
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(unsigned,'w',allowZip64=False) as dst:
        for item in src.infolist():
            if sig(item.filename) or (item.filename.startswith('assets/') and item.filename not in KEEP|bundled):continue
            info=copy.copy(item);info.extra=b'';dst.writestr(info,changed.get(item.filename,src.read(item)))
        for name in META:dst.write(manifest if name=='game_asset_manifest.json' else payload/name,'assets/'+name,compress_type=zipfile.ZIP_DEFLATED)
    aligned=build/'aligned.apk';run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'alignment.txt')
    dist=out/'dist';dist.mkdir(parents=True,exist_ok=True);signed=dist/f'FFBE-Memorial-EN-Startup-Fix-v{version_code}.apk'
    assert not signed.exists(),'Preserve staged signed builds; select a fresh output directory'
    note=(patch/'tools/keys/KEYSTORE_README.txt').read_text(encoding='utf-8');env=os.environ.copy()
    env['FFBE_NATIVE_STORE']=re.search(r'^Storepass:\s+(\S+)',note,re.M)[1];env['FFBE_NATIVE_KEY']=re.search(r'^Keypass:\s+(\S+)',note,re.M)[1]
    signer=['java','-jar',bt/'lib/apksigner.jar']
    run(signer+['sign','--ks',patch/'tools/keys/ffbe-instrumented.keystore','--ks-key-alias','ffbe','--ks-pass','env:FFBE_NATIVE_STORE','--key-pass','env:FFBE_NATIVE_KEY','--v4-signing-enabled','false','--out',signed,aligned],'signing.txt',env)
    verify=run(signer+['verify','--verbose','--print-certs',signed],'signature.txt');assert SIGNER in verify
    run([bt/'zipalign.exe','-c','-P','16','4',signed],'alignment-check.txt')
    badging=run([bt/'aapt2.exe','dump','badging',signed],'package.txt')
    assert "name='com.square_enix.ffbejpn'" in badging and f"versionCode='{version_code}'" in badging and 'application-debuggable' not in badging
    run([bt/'aapt2.exe','dump','xmltree',signed,'--file','AndroidManifest.xml'],'manifest-tree.txt')
    untouched=[]
    with zipfile.ZipFile(source) as src,zipfile.ZipFile(signed) as dst:
        assert dst.testzip() is None
        assert {n for n in dst.namelist() if n.startswith('assets/')}==KEEP|bundled|{'assets/'+n for n in META}
        assert dst.read('assets/game_asset_manifest.json')==manifest.read_bytes()
        for n in dst.namelist():
            if n in changed or sig(n) or n in {'assets/'+x for x in META}:continue
            assert dst.read(n)==src.read(n),n;untouched.append(n)
    for name,h in source_pins.items():assert sha(native/name)==h,'Source changed during build: '+name
    assert sha(source)==BASELINE_SHA
    report={'schema':'ffbe-native-delivery-apk-build-v1','apk':str(signed.resolve()),'bytes':signed.stat().st_size,'sha256':sha(signed),'versionCode':version_code,'package':'com.square_enix.ffbejpn','signer_sha256':SIGNER,'source_apk_sha256':BASELINE_SHA,'source_unchanged':True,'build':str(build.resolve()),'native_source_pins':source_pins,'compiled_smali_overlays':overlay,'smali_changes':patches,'unrelated_smali_classes_preserved':preserved_classes,'unchanged_apk_members':untouched,'apk_assets':sorted(KEEP|bundled|{'assets/'+n for n in META}),'all_game_data_external':False,'bootstrap_assets_bundled':len(bundled),'bootstrap_raw_bytes':sum(a['bytes'] for a in inventory['assets']),'bootstrap_inventory_sha256':sha(payload/'bootstrap_inventory.json'),'asset_manifest_sha256':sha(manifest),'asset_version':graph['asset_version'],'remaining_namespace_records_external':len(graph['assets'])-len(bundled),'ABIs_preserved':['arm64-v8a','armeabi-v7a'],'native_libraries_unchanged':True,'zip_alignment_16k_verified':True,'native_ELF_16k_compatibility_verified':False,'installed':False,'runtime_verified':False,'published':False}
    (out/'NATIVE_APK_BUILD.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('apk','bytes','sha256','versionCode','unrelated_smali_classes_preserved','runtime_verified','published')}))
if __name__=='__main__':main()
