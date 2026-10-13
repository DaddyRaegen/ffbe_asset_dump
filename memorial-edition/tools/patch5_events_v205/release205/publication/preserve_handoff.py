"""Retain the exact qualified beta artifact, sources and readback evidence locally."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(r'S:\FFBE JP Data Export\build\v205-patch5-events')
CANONICAL=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\patch5_events_v205')
OFFICIAL=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-patch5-events-v205')
def sha(p):
 with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def save(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert sha(src)==sha(dst),'Retained destination differs: '+str(dst)
 else:shutil.copy2(src,dst)
 assert sha(src)==sha(dst)
 return {'source':str(src),'destination':str(dst),'bytes':dst.stat().st_size,'sha256':sha(dst)}
def main():
 build=read(ROOT/'staged_build/EVENT_ONLY_APK_BUILD.json');qualified=read(ROOT/'staged_build/SIGNED_EVENT_QUALIFICATION.json');published=read(ROOT/'publication/activation-receipt.json')
 assert qualified['passed'] and published['success'] and qualified['apk_sha256']==build['sha256']==published['sha256']
 assert qualified['guard_sha256']==sha(ROOT/'guard/patch5_event_guard.py')
 apk=Path(build['apk']);assert sha(apk)==build['sha256']
 official=[];canonical=[]
 selected=[]
 for folder in ('source','guard','publication'):
  selected.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.mjs','.json','.md','.html','.txt'))
 selected.extend(p for p in (ROOT/'audit').glob('*') if p.is_file())
 fixture=ROOT/'audit/original-downloader'
 selected.extend(p for p in fixture.rglob('*') if p.is_file() and p.suffix in ('.py','.mjs','.java','.md','.json','.txt','.tsv') and not any(x in p.parts for x in ('host-fixtures','fixtures','host-classes','reference-classes','classes','smali','__pycache__')))
 for filename in ('EVENT_ONLY_APK_BUILD.json','SIGNED_EVENT_QUALIFICATION.json','SIGNED_EVENT_QUALIFICATION_FILENAME_REJECT.json','SMALI_EVENT_PATHS.json'):
  selected.append(ROOT/'staged_build'/filename)
 selected.append(ROOT/'PHONE_TEST_CHECKPOINT.json')
 for parent in (Path(build['build'])/'logs',Path(qualified['work_directory'])):
  selected.extend(p for p in parent.glob('*.txt') if p.is_file())
 for src in sorted(set(selected)):
  relative=src.relative_to(ROOT)
  official.append(copy(src,OFFICIAL/'evidence'/relative))
  canonical.append(copy(src,CANONICAL/'release205'/relative))
 for name in ('content_delivery.tsv','side_stories/manifest.tsv'):
  src=ROOT/'payload'/name
  official.append(copy(src,OFFICIAL/'delivery_metadata'/name))
  canonical.append(copy(src,CANONICAL/'release205/delivery_metadata'/name))
 downloads=read(ROOT/'asset_publication/DOWNLOAD_PLAN.json')
 official.append(copy(ROOT/'asset_publication/DOWNLOAD_PLAN.json',OFFICIAL/'delivery_metadata/DOWNLOAD_PLAN.json'))
 canonical.append(copy(ROOT/'asset_publication/DOWNLOAD_PLAN.json',CANONICAL/'release205/delivery_metadata/DOWNLOAD_PLAN.json'))
 for file in downloads['files']:
  src=Path(file['local_path']);assert sha(src)==file['sha256'] and src.stat().st_size==file['bytes']
  official.append(copy(src,OFFICIAL/'delivery_metadata'/src.name))
  if file['role']!='pack':canonical.append(copy(src,CANONICAL/'release205/delivery_metadata'/src.name))
 official.append(copy(apk,OFFICIAL/'dist'/apk.name))
 payloads=[]
 for asset in read(ROOT/'audit/EVENT_PLAN.json')['assets']:
  src=Path(asset['local_path']);assert sha(src)==asset['sha256'] and src.stat().st_size==asset['bytes']
  payloads.append({'path':asset['path'],'retained_path':str(src),'bytes':asset['bytes'],'sha256':asset['sha256']})
 documentation=[]
 for parent in (CANONICAL/'documents',OFFICIAL/'documents'):
  documentation.extend({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(parent.glob('*.md')))
 report={'schema':'ffbe-patch5-event-handoff-preservation-v1','passed':True,'versionCode':205,'apk_sha256':build['sha256'],'apk_bytes':build['bytes'],'published_apk_url':published['apk_url'],'source_patch5_sha256':build['baseline_apk_sha256'],'official':official,'canonical':canonical,'documentation_pins':documentation,'retained_payload_files':payloads,'all_copied_bytes_verified':True,'payload_scope':'All500 qualified raw event files retained in the original205 workspace; immutable new pack copied into official handoff. Historical203/204 remain untouched.','runtime_verified':False,'physical_phone_test':'pending'}
 for dst in (ROOT/'HANDOFF_PRESERVATION.json',OFFICIAL/'HANDOFF_PRESERVATION.json',CANONICAL/'release205/HANDOFF_PRESERVATION.json'):save(dst,report)
 checkpoint=read(ROOT/'PHONE_TEST_CHECKPOINT.json')
 for dst in (OFFICIAL/'PHONE_TEST_CHECKPOINT.json',CANONICAL/'release205/PHONE_TEST_CHECKPOINT.json'):save(dst,checkpoint)
 print(json.dumps({'passed':True,'official_copies':len(official),'canonical_copies':len(canonical),'retained_event_payloads':len(payloads),'official_apk':str(OFFICIAL/'dist'/apk.name),'apk_sha256':build['sha256']}))
if __name__=='__main__':main()
