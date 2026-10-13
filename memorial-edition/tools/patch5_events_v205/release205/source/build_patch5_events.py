"""Literal Patch 5 plus event catalog/asset delivery; no startup/runtime redesign."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,re,shutil,subprocess,zipfile
ROOT=Path(__file__).resolve().parent
BASELINE_SHA='534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'build_config.json');cfg=json.loads(parser.parse_args().config.read_bytes())
 source=Path(cfg['source_apk']);project=Path(cfg['project']);payload=Path(cfg['payload']);out=Path(cfg['output']);plan=json.loads(Path(cfg['event_plan']).read_bytes());version=int(cfg['version_code']);assert version==205
 assert sha(source)==BASELINE_SHA
 build=out/'build'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f');logs=build/'logs';logs.mkdir(parents=True,exist_ok=False)
 def run(args,name,env=None):
  result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600);(logs/name).write_text(result.stdout+result.stderr,encoding='utf-8')
  if result.returncode:raise RuntimeError(name+': '+str(result.returncode))
  return result.stdout+result.stderr
 pins={p.name:sha(p) for p in ROOT.glob('*.py')}
 bt=project/'graphics-localization/2026-09-19/apk-build/tools/android-16'
 manifest=module('manifest_version',ROOT/'manifest_version.py');script=module('script_events',ROOT/'script_events.py');paths=module('patch_event_paths',ROOT/'patch_event_paths.py')
 apkzip=module('literal_apk_zip',project/'story-ports/side-stories/scripts/apk_zip.py')
 with zipfile.ZipFile(source) as z:
  (build/'original.dex').write_bytes(z.read('classes.dex'))
  axml,manifest_edits=manifest.patch(z.read('AndroidManifest.xml'),version)
  js,script_edits=script.patch(z.read('assets/frida_script.js'),plan['party_book_ids'],version)
 (build/'frida_script.js').write_bytes(js);run([cfg.get('node','node'),'--check',build/'frida_script.js'],'javascript.txt')
 base=build/'smali';run(['java','-jar',project/'tools/bin/baksmali.jar','d',build/'original.dex','-o',base],'original-dex.txt')
 before={f.relative_to(base).as_posix():sha(f) for f in base.rglob('*.smali')}
 receipt=paths.patch_smali(base);changed={f.relative_to(base).as_posix() for f in base.rglob('*.smali') if sha(f)!=before[f.relative_to(base).as_posix()]}
 assert changed=={'O1/ExtraContent$Entry.smali','O1/SideStoryTables.smali'},changed
 receipt.update({'all_other_classes_unchanged':True,'class_count':len(before),'untouched_classes':len(before)-len(changed),'baseline_apk_sha256':BASELINE_SHA})
 (out/'SMALI_EVENT_PATHS.json').parent.mkdir(parents=True,exist_ok=True);(out/'SMALI_EVENT_PATHS.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 skeleton=project/'story-ports/side-stories/delivery/decoded';decoded=build/'decoded';decoded.mkdir()
 for name in ('apktool.yml','AndroidManifest.xml','resources.arsc'):shutil.copy2(skeleton/name,decoded/name)
 shutil.copytree(base,decoded/'smali');run(['java','-jar',project/'tools/bin/apktool.jar','b',decoded,'-o',build/'dex-container.apk'],'assemble.txt')
 with zipfile.ZipFile(build/'dex-container.apk') as z:dex=z.read('classes.dex')
 for cls in (b'LO1/GameAssets;',b'LO1/GameAssetsBoot;',b'LO1/BundledAssets;',b'LO1/DeliveryPolicy;',b'LO1/PatchUpdater;',b'LO1/MovieAssets;',b'LO1/BootstrapActivity;'):assert cls not in dex
 replacements={'AndroidManifest.xml':axml,'classes.dex':dex,'assets/frida_script.js':js,'assets/content_delivery.tsv':(payload/'content_delivery.tsv').read_bytes(),'assets/side_stories/manifest.tsv':(payload/'side_stories/manifest.tsv').read_bytes()}
 unsigned=build/'unsigned.apk';apkzip.replace_entries(source,unsigned,replacements)
 aligned=build/'aligned.apk';run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'alignment.txt')
 dist=out/'dist';dist.mkdir(parents=True,exist_ok=True);signed=dist/'FFBE-Memorial-EN-Patch-5-Events-v205.apk';assert not signed.exists()
 note=(project/'tools/keys/KEYSTORE_README.txt').read_text();env=os.environ.copy();env['FFBE_EVENT_STORE']=re.search(r'^Storepass:\s+(\S+)',note,re.M)[1];env['FFBE_EVENT_KEY']=re.search(r'^Keypass:\s+(\S+)',note,re.M)[1]
 signer=['java','-jar',bt/'lib/apksigner.jar'];run(signer+['sign','--ks',project/'tools/keys/ffbe-instrumented.keystore','--ks-key-alias','ffbe','--ks-pass','env:FFBE_EVENT_STORE','--key-pass','env:FFBE_EVENT_KEY','--v4-signing-enabled','false','--out',signed,aligned],'sign.txt',env)
 assert SIGNER in run(signer+['verify','--verbose','--print-certs',signed],'signature.txt');run([bt/'zipalign.exe','-c','-P','16','4',signed],'alignment-check.txt')
 badging=run([bt/'aapt2.exe','dump','badging',signed],'package.txt');assert "name='com.square_enix.ffbejpn'" in badging and "versionCode='205'" in badging and 'application-debuggable' not in badging
 preserved=[]
 with zipfile.ZipFile(source) as src,zipfile.ZipFile(signed) as dst:
  assert dst.testzip() is None
  assert {n for n in src.namelist() if not apkzip.signature(n)}=={n for n in dst.namelist() if not apkzip.signature(n)}
  for n in src.namelist():
   if apkzip.signature(n):continue
   assert dst.read(n)==replacements.get(n,src.read(n)),n
   if n not in replacements:assert src.getinfo(n).compress_type==dst.getinfo(n).compress_type;preserved.append(n)
 for name,pin in pins.items():assert sha(ROOT/name)==pin,'Source changed: '+name
 assert sha(source)==BASELINE_SHA
 report={'schema':'ffbe-patch5-event-only-apk-build-v1','apk':str(signed.resolve()),'bytes':signed.stat().st_size,'sha256':sha(signed),'versionCode':version,'versionName':'11.1.1','package':'com.square_enix.ffbejpn','signer_sha256':SIGNER,'baseline_apk':str(source),'baseline_apk_sha256':BASELINE_SHA,'build':str(build),'source_pins':pins,'changed_members':list(replacements),'unchanged_members':preserved,'asset_file_count':170,'new_apk_members':0,'new_activity_or_startup_gate':False,'native_libraries_unchanged':True,'original_downloader_callbacks_unchanged':True,'original_lifecycle_unchanged':True,'original_movies_unchanged':True,'manifest_edits':manifest_edits,'script_edits':script_edits,'smali_receipt':str(out/'SMALI_EVENT_PATHS.json'),'event_plan_sha256':sha(cfg['event_plan']),'content_delivery_sha256':sha(payload/'content_delivery.tsv'),'side_manifest_sha256':sha(payload/'side_stories/manifest.tsv'),'zip_alignment_16k_verified':True,'native_ELF_16k_compatibility_verified':False,'published':False,'runtime_verified':False,'device_actions':False}
 (out/'EVENT_ONLY_APK_BUILD.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ('apk','bytes','sha256','versionCode','asset_file_count','new_apk_members')}))
if __name__=='__main__':main()
