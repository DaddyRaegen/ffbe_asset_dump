"""Package the finite download-display spacing fix over exact published206."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,re,struct,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT.parent/'v206-event-cleanup'
PROJECT=Path(r'T:\Projects\FFBE Patch')
BASELINE=PREVIOUS/'staged_build/dist/FFBE-Memorial-EN-Event-Cleanup-v206.apk'
BASELINE_SHA='345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d'
SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def main():
 assert sha(BASELINE)==BASELINE_SHA
 qualified=json.loads((PREVIOUS/'staged_build/SIGNED_EVENT_QUALIFICATION.json').read_bytes());assert qualified['passed'] and qualified['apk_sha256']==BASELINE_SHA
 prior=json.loads((PREVIOUS/'staged_build/EVENT_CLEANUP_APK_BUILD.json').read_bytes())
 plan_path=ROOT/'audit/DOWNLOAD_SPACING_PLAN.json';plan_pin=sha(plan_path);plan=json.loads(plan_path.read_bytes());assert plan['schema']=='ffbe-download-spacing-plan-v1' and plan['baseline_apk_sha256']==BASELINE_SHA
 source_pins={p.name:sha(p) for p in (ROOT/'source').glob('*') if p.is_file()}
 out=ROOT/'staged_build';build=out/'build'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f');logs=build/'logs';logs.mkdir(parents=True,exist_ok=False)
 def run(args,name,env=None):
  r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600);(logs/name).write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0,name;return r.stdout+r.stderr
 with zipfile.ZipFile(BASELINE) as z:
  axml=bytearray(z.read('AndroidManifest.xml'));offset=prior['manifest_edits'][0]['offset'];assert axml[offset-1]==16 and struct.unpack_from('<I',axml,offset)[0]==206;struct.pack_into('<I',axml,offset,207)
  original=z.read('assets/frida_script.js');assert digest(original)==plan['baseline_script_sha256'];script=original
  for op in plan['operations']:
   before=op['before'].encode();after=op['after'].encode();assert script.count(before)==op['count']==1;script=script.replace(before,after)
  assert script.count(b'const PATCH_VERSION = 206;')==1;script=script.replace(b'const PATCH_VERSION = 206;',b'const PATCH_VERSION = 207;')
  assert digest(script)==plan['candidate_script_sha256']
  catalog=z.read('assets/content_delivery.tsv');side=z.read('assets/side_stories/manifest.tsv')
 (build/'frida_script.js').write_bytes(script);run(['node','--check',build/'frida_script.js'],'javascript.txt')
 path=PROJECT/'story-ports/side-stories/scripts/apk_zip.py';spec=importlib.util.spec_from_file_location('literal_apkzip',path);apkzip=importlib.util.module_from_spec(spec);spec.loader.exec_module(apkzip)
 replacements={'AndroidManifest.xml':bytes(axml),'assets/frida_script.js':script};unsigned=build/'unsigned.apk';apkzip.replace_entries(BASELINE,unsigned,replacements)
 bt=PROJECT/'graphics-localization/2026-09-19/apk-build/tools/android-16';aligned=build/'aligned.apk';run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'alignment.txt')
 dist=out/'dist';dist.mkdir(parents=True,exist_ok=True);signed=dist/'FFBE-Memorial-EN-Download-Spacing-v207.apk';assert not signed.exists()
 note=(PROJECT/'tools/keys/KEYSTORE_README.txt').read_text();env=os.environ.copy();env['FFBE_SPACING_STORE']=re.search(r'^Storepass:\s+(\S+)',note,re.M)[1];env['FFBE_SPACING_KEY']=re.search(r'^Keypass:\s+(\S+)',note,re.M)[1]
 signer=['java','-jar',bt/'lib/apksigner.jar'];run(signer+['sign','--ks',PROJECT/'tools/keys/ffbe-instrumented.keystore','--ks-key-alias','ffbe','--ks-pass','env:FFBE_SPACING_STORE','--key-pass','env:FFBE_SPACING_KEY','--v4-signing-enabled','false','--out',signed,aligned],'sign.txt',env)
 assert SIGNER in run(signer+['verify','--verbose','--print-certs',signed],'signature.txt');run([bt/'zipalign.exe','-c','-P','16','4',signed],'alignment-check.txt')
 badging=run([bt/'aapt2.exe','dump','badging',signed],'package.txt');assert "name='com.square_enix.ffbejpn'" in badging and "versionCode='207'" in badging and 'application-debuggable' not in badging
 with zipfile.ZipFile(BASELINE) as a,zipfile.ZipFile(signed) as b:
  assert b.testzip() is None and {n for n in a.namelist() if not apkzip.signature(n)}=={n for n in b.namelist() if not apkzip.signature(n)}
  for n in a.namelist():
   if apkzip.signature(n):continue
   assert b.read(n)==replacements.get(n,a.read(n)),n
 for name,pin in source_pins.items():assert sha(ROOT/'source'/name)==pin
 assert sha(plan_path)==plan_pin and sha(BASELINE)==BASELINE_SHA
 report={'schema':'ffbe-download-spacing-apk-v1','apk':str(signed),'bytes':signed.stat().st_size,'sha256':sha(signed),'versionCode':207,'versionName':'11.1.1','package':'com.square_enix.ffbejpn','signer_sha256':SIGNER,'baseline_apk':str(BASELINE),'baseline_apk_sha256':BASELINE_SHA,'changed_members':list(replacements),'spacing_plan_sha256':sha(plan_path),'source_pins':source_pins,'content_catalog_sha256':digest(catalog),'side_manifest_sha256':digest(side),'asset_file_count':170,'new_apk_members':0,'classes_dex_byte_identical_to206':True,'native_libraries_unchanged':True,'event_assets_unchanged':True,'startup_assets_unchanged':True,'downloader_unchanged':True,'movies_unchanged':True,'zip_alignment_16k_verified':True,'runtime_verified':False,'save_migration_verified':False,'device_actions':False,'published':False,'build':str(build),'manifest_edits':[{'offset':offset,'before':206,'after':207}],'script_edit':'Existing punctuation helper finite display-spacing delta plus PATCH_VERSION206 to207 only'}
 (out/'DOWNLOAD_SPACING_APK_BUILD.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ('apk','bytes','sha256','versionCode')}))
if __name__=='__main__':main()
