"""Copy bounded frozen206 release evidence only after qualified publication."""
from pathlib import Path
import json,hashlib,datetime,shutil,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
CANON=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\event_cleanup_v206')
RELEASE=CANON/'release206'
HANDOFF=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-event-cleanup-v206')
BASELINE='e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'
PUBLIC_REVIEW_SHA='1c71f5b2c58740bc0c1f2cec35dc5881fceceff0c0b875e380830b771d42697a'
def sha(p):
 with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
def require(value,msg):
 if not value:raise RuntimeError(msg)
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def copy_exact(source,target):
 source=source.resolve();target=target.resolve()
 require(target.is_relative_to(CANON.resolve()) or target.is_relative_to(HANDOFF.resolve()),'Copy outside exact new206 destinations')
 require(source.is_file(),'Missing frozen input: '+str(source))
 before=pin(source)
 if target.exists():require(target.is_file() and sha(target)==before['sha256'] and target.stat().st_size==before['bytes'],'Existing different handoff bytes: '+str(target))
 else:target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
 require(sha(source)==before['sha256'] and target.stat().st_size==before['bytes'] and sha(target)==before['sha256'],'Copy/source changed: '+str(source))
 return {'source':str(source),'destination':str(target),'bytes':before['bytes'],'sha256':before['sha256']}
def write_owned(path,blob):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob)
 return pin(path)

def main():
 build=read(ROOT/'staged_build/EVENT_CLEANUP_APK_BUILD.json');qualified=read(ROOT/'staged_build/SIGNED_EVENT_QUALIFICATION.json')
 activation=read(ROOT/'publication/activation-receipt.json');stage=read(ROOT/'publication/apk-stage-receipt.json')
 download=read(ROOT/'asset_publication/DOWNLOAD_PLAN.json');host=read(ROOT/'audit/ACTUAL206_CATALOG_HOST_ADMISSION.json')
 transport=read(ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json');local=read(ROOT/'audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json')
 public_path=ROOT/'audit/PUBLIC_V206_REVIEW.json';public=read(public_path)
 require(build['versionCode']==206 and build['baseline_apk_sha256']==BASELINE and qualified['passed'] is True and qualified['signed_apk_qualified'] is True,'Exact signed206 qualification missing')
 require(qualified['apk_sha256']==build['sha256'] and qualified['apk_bytes']==build['bytes'],'Signed qualifier/build identity differs')
 require(activation['success'] is True and activation['versionCode']==206 and activation['sha256']==build['sha256'] and activation['bytes']==build['bytes'],'Exact206 publication incomplete')
 require(stage['success'] is True and stage['apk']['sha256']==build['sha256'] and stage['apk']['bytes']==build['bytes'],'Verified stagedAPK differs')
 require(host['passed'] is True and host['apk_sha256']==build['sha256'] and host['catalog_sha256']==download['content_catalog_sha256'],'Actual206 host gate differs')
 require(transport['passed'] is True and transport['content_catalog_sha256']==download['content_catalog_sha256'] and local['passed'] is True,'Transport/local publication review missing')
 require(sha(public_path)==PUBLIC_REVIEW_SHA and public['passed'] is True and public['versionCode']==206 and public['apk_sha256']==build['sha256'] and public['apk_bytes']==build['bytes'] and public['content_catalog_sha256']==download['content_catalog_sha256'] and public['side_manifest_sha256']==download['side_manifest_sha256'],'Exact independent public206 review differs')
 require(public['runtime_verified'] is False and public['remote_mutations'] is False and public['device_actions'] is False,'Public review scope differs')
 require(sha(ROOT/'audit/read_public206.mjs')==public['checker_sha256'],'Published checker source changed')
 require(build['runtime_verified'] is False and activation['runtime_verified'] is False and activation['physical_phone_test']=='pending','Phone state must remain unverified')
 apk=Path(build['apk']);require(apk.stat().st_size==build['bytes'] and sha(apk)==build['sha256'],'Final signedAPK bytes changed')
 cleanup=read(ROOT/'audit/CLEANUP_PLAN.json');banners=read(ROOT/'audit/BANNER_PLAN.json')
 require(cleanup['category_book_counts']['after']['70']==77 and cleanup['category_book_counts']['after']['71']==376,'Frozen menu counts differ')
 require(banners['passed'] is True and len(banners['members'])==12,'Frozen12banner plan incomplete')
 registry=read(ROOT/'audit/DEFERRED_UI_RECORDS.json')
 require(len(registry['excluded_books'])==41 and len(registry['records'])==1760,'Full deferred UI registry incomplete')
 raw_files=download['new_pack_files']
 require(len(raw_files)==5 and {r['path'] for r in raw_files}=={'side_stories/9Zdr5ap0.dat','side_stories/D2zaT7Ru.dat','side_stories/IL78hX09.dat','side_stories/Nm36woZx.dat','side_stories/spdungeon9.cpk'},'Five frozen raw payload identities differ')
 for row in raw_files:
  p=Path(row['local_path']);require(p.is_relative_to(ROOT/'payload') and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],'Raw payload differs: '+row['path'])
 native=read(ROOT/'banner_outputs/NATIVE_BANNERS.json')
 require(native['passed'] is True and len(native['records'])==11,'Native banner encoding evidence incomplete')
 for row in native['records']:
  for field,size,digest in [('source','source_bytes','source_sha256'),('local_path','bytes','sha256')]:
   p=Path(row[field]);require(p.is_relative_to(ROOT/'banner_outputs') and p.stat().st_size==row[size] and sha(p)==row[digest],'Derivative/native artwork differs: '+str(p))
 for name in ['IMAGE_TOOL_PROMPTS.json','IMAGE_TOOL_FOLLOWUPS.json','IMAGE_TOOL_PRESS_TRANSLATIONS.json']:
  prompt=read(ROOT/'banner_outputs'/name);require(prompt['model_version_verified'] is False,'Image model state must stay unverified')
 copies=[]
 def both(source,relative,t_relative=None):
  copies.append(copy_exact(source,RELEASE/relative));copies.append(copy_exact(source,HANDOFF/(t_relative or ('evidence/'+relative))))
 for folder in ('source','guard'):
  for p in sorted((ROOT/folder).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix.lower() in ('.py','.mjs','.json','.md','.java'):
    both(p,folder+'/'+p.relative_to(ROOT/folder).as_posix())
 for p in sorted((ROOT/'audit').iterdir()):
  if p.is_file() and p.suffix.lower() in ('.json','.csv','.md','.txt','.py','.mjs') and p.name!='HANDOFF_COPY_RECEIPT.json':
   both(p,'audit/'+p.name)
 for p in sorted((ROOT/'audit/runtime_host').iterdir()):
  if p.is_file() and p.suffix.lower() in ('.py','.java','.json','.md'):both(p,'audit/runtime_host/'+p.name)
 # Retain the small sealed205 JVM reference snapshot; never copy fixture caches/classes.
 reference=read(ROOT/'audit/runtime_host/REFERENCE205_JVM_SOURCES.json')
 reference_root=Path(r'S:\FFBE JP Data Export\build\v205-patch5-events\audit\original-downloader\actual-catalog\source')
 for rel,digest in reference['java_source_pins'].items():
  p=reference_root/rel;require(sha(p)==digest,'Sealed205 JVM source changed')
  both(p,'audit/runtime_host/reference205/'+rel)
 both(Path(reference['qualified205_host_report']),'audit/runtime_host/reference205/QUALIFIED205_HOST_REPORT.json')
 for folder in ('banner_sources','banner_outputs'):
  for p in sorted((ROOT/folder).rglob('*')):
   if p.is_file() and p.suffix.lower() in ('.png','.jpg','.jpeg','.webp','.json','.csv','.html','.txt','.md'):
    both(p,'artwork/'+folder+'/'+p.relative_to(ROOT/folder).as_posix(),'artwork/'+folder+'/'+p.relative_to(ROOT/folder).as_posix())
 for p in sorted((ROOT/'payload').rglob('*')):
  if p.is_file():both(p,'payload/'+p.relative_to(ROOT/'payload').as_posix(),'delivery_metadata/payload/'+p.relative_to(ROOT/'payload').as_posix())
 for p in sorted((ROOT/'asset_publication').iterdir()):
  if p.is_file() and (p.suffix.lower() in ('.json','.tsv','.bin','.pack','.txt') or p.name.endswith('.deflate')):
   both(p,'asset_publication/'+p.name,'delivery_metadata/'+p.name)
 for p in sorted((ROOT/'publication').rglob('*')):
  if p.is_file() and p.suffix.lower() in ('.mjs','.json','.html','.txt','.md'):
   both(p,'publication/'+p.relative_to(ROOT/'publication').as_posix())
 for p in sorted((ROOT/'staged_build').iterdir()):
  if p.is_file() and p.suffix.lower() in ('.json','.txt','.md'):both(p,'staged_build/'+p.name)
 both(apk,'staged_build/dist/'+apk.name,'dist/'+apk.name)
 checkpoint=read(ROOT/'PHONE_TEST_CHECKPOINT.json')
 require(checkpoint['apk_sha256']==build['sha256'] and checkpoint['physical_phone_test']=='pending' and checkpoint['runtime_verified'] is False,'Phone checkpoint differs from published206')
 copies.append(copy_exact(ROOT/'PHONE_TEST_CHECKPOINT.json',RELEASE/'PHONE_TEST_CHECKPOINT.json'))
 copies.append(copy_exact(ROOT/'PHONE_TEST_CHECKPOINT.json',HANDOFF/'PHONE_TEST_CHECKPOINT.json'))
 # Own skeleton documents now receive the exact publishedidentity; preserve pending snapshot as historical preparation evidence.
 header=f"Published beta APK 206: [{apk.name}]({activation['apk_url']}), {build['bytes']:,} bytes, SHA-256 `{build['sha256']}`. Signed qualification, publication and independent public verification passed. Phone, runtime, gameplay and save results remain pending.\n\n"
 replacements={
  'Release preparation is pending final signed qualification and verified publication. Planned output files and URLs are not live-release evidence. The final publication receipt and phone checkpoint will identify the exact signed APK. Physical phone results remain pending.':header.strip(),
  'Final qualification/publication evidence is pending while this skeleton is prepared. No phone pass is recorded. Keep the exact final checkpoint pending until Kev reports the signed APK hash, device and Android version.':header.strip(),
  'Publication is pending in this skeleton. Use only the final verified URL/version/size/SHA in `PHONE_TEST_CHECKPOINT.json` and immutable `phone-test-checklist.txt`. Test the exact signed APK on Z Fold 8/Android 17; record that identity with results.':header.strip()+'\n\nUse the exact matching checkpoint/checklist. Test on Z Fold8/Android 17 and report the build identity with results.',
  'Final signed qualification, verified publication and exact APK identity are pending while the handoff skeleton is prepared.':'Final signed qualification and verified publication evidence are retained with the exact APK identity.',
 }
 documents=[]
 for base in (CANON,HANDOFF):
  for p in [base/'README.md',*sorted((base/'documents').glob('*.md'))]:
   text=p.read_text(encoding='utf-8')
   for old,new in replacements.items():text=text.replace(old,new)
   if p.name=='README.md':
    text=text.replace('The final handoff receipt will hash every retained file.','The final handoff receipt hashes every retained file.')
    text=text.replace('Final signed qualification and verified publication evidence are retained with the exact APK identity.',header.strip())
   if p.name=='EVENT_CLEANUP_RELEASE_WORKFLOW.md':
    text+='\n## Final qualification and publication evidence\n\nExact signed APK qualification: `staged_build/SIGNED_EVENT_QUALIFICATION.json`. Actual catalog/cache admission: `audit/ACTUAL206_CATALOG_HOST_ADMISSION.json`. Raw-deflate transport admission: `audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json`. Network-free publisher scope: `audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json`. Immutable upload and activation: `publication/asset-receipt.json`, `apk-stage-receipt.json` and `activation-receipt.json`. Independent public readback: `audit/PUBLIC_V206_REVIEW.json`, including the exact APK, metadata/checklist, new assets, retained links, protected production files and stable203 pointer. These reports establish byte, graph, cache-fixture and publication checks; phone results remain pending.\n'
   p.write_text(text,encoding='utf-8');documents.append(pin(p))
  copies.append(copy_exact(ROOT/'publication/site/phone-test-checklist.txt',base/'documents/phone-test-checklist.txt'))
 receipt={'schema':'ffbe-v206-frozen-handoff-copy-v1','passed':True,'final_copy_complete':True,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'work_root':str(ROOT),'canonical_release_root':str(RELEASE),'handoff_root':str(HANDOFF),
  'apk':{'url':activation['apk_url'],**pin(apk)},'versionCode':206,'catalog_sha256':download['content_catalog_sha256'],'side_manifest_sha256':download['side_manifest_sha256'],'source205_apk_sha256':BASELINE,
  'public_review':pin(public_path),'all_five_raw_payloads_verified':True,'complete_deferred_UI_registry_retained':True,'original_generated_native_artwork_and_prompt_provenance_retained':True,
  'menu_counts':{'story_event_books':77,'event_battle_books':376,'JP_memories_books':450,'total_playback_books':1004,'moved_books':20,'hidden_vortex_books':37,'hidden_greeting_books':1,'named_removed_books':3,'deferred_UI_records':1760,'replaced_banner_members':12},
  'copies':copies,'documents':documents,'copy_count':len(copies),'source_and_destination_hashes_verified':True,'historical_release_writes':False,'excluded':'Signing material/credentials, fixturecaches/classes, build/disassembly intermediates and unrelated large source dumps.','runtime_verified':False,'physical_phone_test':'pending','model_version_verified':False}
 blob=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 for p in (ROOT/'audit/HANDOFF_COPY_RECEIPT.json',RELEASE/'HANDOFF_COPY_RECEIPT.json',HANDOFF/'HANDOFF_COPY_RECEIPT.json'):write_owned(p,blob)
 print(json.dumps({'passed':True,'copy_count':len(copies),'receipt':str(ROOT/'audit/HANDOFF_COPY_RECEIPT.json'),'receipt_sha256':hashlib.sha256(blob).hexdigest(),'APK_sha256':build['sha256'],'phone_test':'pending'}))
if __name__=='__main__':main()
