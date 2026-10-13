"""Package reviewed event-menu data over the exact qualified build 205.

Original startup, native/Java code, downloader, movies and all other assets
remain literal build 205. Event data and banners stay on GitHub.
"""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,subprocess,zipfile
ROOT=Path(__file__).resolve().parent
BASELINE_SHA='e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'
PATCH5_SHA='534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'build_config.json');cfg=json.loads(parser.parse_args().config.read_bytes())
 baseline=Path(cfg['source_apk']);project=Path(cfg['project']);payload=Path(cfg['payload']);out=Path(cfg['output']);assert int(cfg['version_code'])==206
 assert sha(baseline)==BASELINE_SHA
 source_report=json.loads(Path(cfg['source_qualification']).read_bytes());assert source_report['passed'] and source_report['apk_sha256']==BASELINE_SHA
 build=out/'build'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f');logs=build/'logs';logs.mkdir(parents=True,exist_ok=False)
 def run(args,name,env=None):
  result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600);(logs/name).write_text(result.stdout+result.stderr,encoding='utf-8')
  if result.returncode:raise RuntimeError(name+': '+str(result.returncode))
  return result.stdout+result.stderr
 source_pins={p.name:sha(p) for p in ROOT.glob('*.py')}
 bt=project/'graphics-localization/2026-09-19/apk-build/tools/android-16'
 manifest=module('manifest_version',ROOT/'manifest_version.py');apkzip=module('literal_apk_zip',project/'story-ports/side-stories/scripts/apk_zip.py')
 with zipfile.ZipFile(baseline) as archive:
  axml,edits=manifest.patch(archive.read('AndroidManifest.xml'),206)
  original=archive.read('assets/frida_script.js');assert original.count(b'const PATCH_VERSION = 205;')==1
  script=original.replace(b'const PATCH_VERSION = 205;',b'const PATCH_VERSION = 206;')
 (build/'frida_script.js').write_bytes(script);run([cfg.get('node','node'),'--check',build/'frida_script.js'],'javascript.txt')
 replacements={'AndroidManifest.xml':axml,'assets/frida_script.js':script,'assets/content_delivery.tsv':(payload/'content_delivery.tsv').read_bytes(),'assets/side_stories/manifest.tsv':(payload/'side_stories/manifest.tsv').read_bytes()}
 unsigned=build/'unsigned.apk';apkzip.replace_entries(baseline,unsigned,replacements)
 aligned=build/'aligned.apk';run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'alignment.txt')
 dist=out/'dist';dist.mkdir(parents=True,exist_ok=True);signed=dist/'FFBE-Memorial-EN-Event-Cleanup-v206.apk';assert not signed.exists()
 note=(project/'tools/keys/KEYSTORE_README.txt').read_text();env=os.environ.copy();env['FFBE_MENU_STORE']=re.search(r'^Storepass:\s+(\S+)',note,re.M)[1];env['FFBE_MENU_KEY']=re.search(r'^Keypass:\s+(\S+)',note,re.M)[1]
 signer=['java','-jar',bt/'lib/apksigner.jar'];run(signer+['sign','--ks',project/'tools/keys/ffbe-instrumented.keystore','--ks-key-alias','ffbe','--ks-pass','env:FFBE_MENU_STORE','--key-pass','env:FFBE_MENU_KEY','--v4-signing-enabled','false','--out',signed,aligned],'sign.txt',env)
 assert SIGNER in run(signer+['verify','--verbose','--print-certs',signed],'signature.txt');run([bt/'zipalign.exe','-c','-P','16','4',signed],'alignment-check.txt')
 badging=run([bt/'aapt2.exe','dump','badging',signed],'package.txt');assert "name='com.square_enix.ffbejpn'" in badging and "versionCode='206'" in badging and 'application-debuggable' not in badging
 preserved=[]
 with zipfile.ZipFile(baseline) as source,zipfile.ZipFile(signed) as target:
  assert target.testzip() is None
  assert {n for n in source.namelist() if not apkzip.signature(n)}=={n for n in target.namelist() if not apkzip.signature(n)}
  for name in source.namelist():
   if apkzip.signature(name):continue
   assert target.read(name)==replacements.get(name,source.read(name)),name
   if name not in replacements:assert source.getinfo(name).compress_type==target.getinfo(name).compress_type;preserved.append(name)
 for name,pin in source_pins.items():assert sha(ROOT/name)==pin,'Build source changed: '+name
 assert sha(baseline)==BASELINE_SHA
 report={'schema':'ffbe-event-menu-cleanup-apk-v1','apk':str(signed.resolve()),'bytes':signed.stat().st_size,'sha256':sha(signed),'versionCode':206,'versionName':'11.1.1','package':'com.square_enix.ffbejpn','signer_sha256':SIGNER,'baseline_apk':str(baseline),'baseline_apk_sha256':BASELINE_SHA,'foundation_patch5_sha256':PATCH5_SHA,'source_qualification_sha256':sha(cfg['source_qualification']),'build':str(build),'source_pins':source_pins,'changed_members':list(replacements),'unchanged_members':preserved,'asset_file_count':170,'new_apk_members':0,'classes_dex_byte_identical_to205':True,'native_libraries_unchanged':True,'startup_assets_unchanged':True,'downloader_unchanged':True,'movies_unchanged':True,'manifest_edits':edits,'script_edit':'PATCH_VERSION205 to206 only','content_catalog_sha256':sha(payload/'content_delivery.tsv'),'side_manifest_sha256':sha(payload/'side_stories/manifest.tsv'),'zip_alignment_16k_verified':True,'native_ELF_16k_compatibility_verified':False,'runtime_verified':False,'device_actions':False,'published':False}
 (out/'EVENT_CLEANUP_APK_BUILD.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ('apk','bytes','sha256','versionCode','asset_file_count','new_apk_members')}))
if __name__=='__main__':main()
