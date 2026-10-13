"""Append bounded GitHub mirror evidence; never replace original207 archive files."""
from pathlib import Path
import datetime,hashlib,json,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v207-github-mirror')
BASE=ROOT.parent/'v207-download-spacing'
CANON=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\download_spacing_v207\release207')
HANDOFF=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-download-spacing-v207')
DESTINATIONS=[CANON/'github_mirror_2026-10-04',HANDOFF/'github_mirror_2026-10-04']
SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e';SIZE=145206221
TAG='beta-apk-v207-d9181ffc05fa11e1'
URL='https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/'+TAG+'/FFBE-Memorial-EN-Download-Spacing-v207.apk'
LUMINEST='https://ffbe.luminest.io/downloads/beta/releases/download-spacing-v207-d9181ffc05fa11e1/FFBE-Memorial-EN-Download-Spacing-v207.apk'
PUBLISHER_SHA='06ebfef3df0034da03f7daf79ac0e3173438efa8fd6703ddcc2fd16fd9c0b762'
ORIGINAL_HANDOFF_SHA='3312e725499929c349969b81198ab365755d2fc5b6fc2b3274be7943db2bf63a'
def require(value,message):
 if not value:raise RuntimeError(message)
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def pin(path):return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def blob(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def create(path,data):
 require(any(path.resolve().is_relative_to(destination.resolve()) for destination in DESTINATIONS) or path.resolve().is_relative_to((ROOT/'audit').resolve()),'Outside new mirror evidence roots')
 if path.exists():require(path.read_bytes()==data,'Existing different mirror bytes: '+str(path))
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 return pin(path)
def copy(source,target):
 before=pin(source);create(target,source.read_bytes())
 require(pin(source)==before and sha(target)==before['sha256'],'Source/copy changed')
 return {'source':str(source),'destination':str(target),'bytes':before['bytes'],'sha256':before['sha256']}

def main():
 upload=read(ROOT/'publication/github-apk-receipt.json');updater=read(ROOT/'publication/github-updater-receipt.json');page=read(ROOT/'publication/page-activation-receipt.json')
 review=read(ROOT/'audit/INDEPENDENT_PUBLISHER_SOURCE_REVIEW.json');local=read(ROOT/'audit/LOCAL_PAGE_REVIEW.json')
 require(sha(ROOT/'publication/publish_github.mjs')==PUBLISHER_SHA and review['passed'] is True and review['source']['sha256']==PUBLISHER_SHA,'Reviewed publisher differs')
 require(upload['success'] is True and upload['APK_published'] is True and upload['versionCode']==207 and upload['sha256']==SHA and upload['bytes']==SIZE and upload['url']==URL and upload['release_tag']==TAG and upload['prerelease'] is True and upload['make_latest'] is False and upload['full_download_verified'] is True,'Exact public GitHub mirror not verified')
 starts=[0,SIZE//2,SIZE-65536]
 require(len(upload['ranges'])==3 and all(any(row['start']==start and row['end']==min(start+65535,SIZE-1) and row['verified'] is True for row in upload['ranges']) for start in starts),'Three exact verified mirror ranges required')
 require(upload['original_apk_url']==LUMINEST and upload['APK_modified'] is False and upload['event_assets_modified'] is False and upload['new_asset_uploads']==0,'Mirror scope changed')
 require(updater['success'] is True and updater['versionCode']==207 and updater['asset_version']==206 and updater['apk_url']==updater['url']==URL and updater['sha256']==SHA and updater['bytes']==SIZE and updater['only_apk_urls_changed'] is True and updater['updater']['full_download_verified'] is True,'Canonical GitHub updater not verified')
 require(page['success'] is True and page['versionCode']==207 and page['apk_sha256']==SHA and page['apk_bytes']==SIZE and page['github_primary_url']==URL and page['luminest_mirror_url']==LUMINEST and page['github_verified_upload_receipt_sha256']==sha(ROOT/'publication/github-apk-receipt.json'),'Final mirror page not verified')
 require(page['all_existing_content_and_links_preserved'] is True and page['APK_changed'] is False and page['assets_changed'] is False and page['new_asset_uploads']==0 and page['phone_test_pending'] is True,'Page scope/phone state changed')
 require(local['passed'] is True and local['all_other_page_bytes_preserved'] is True and local['prepared_page']['sha256']==page['page']['sha256'] and sha(ROOT/'publication/site/index.html')==page['page']['sha256'],'Final page does not match exact local delta')
 for name,expected in local['source_pins'].items():require(pin(ROOT/'publication'/name)['sha256']==expected['sha256'],'Page source changed')
 require(upload['runtime_verified'] is False and upload['physical_phone_test']==updater['physical_phone_test']=='pending','Phone results must remain pending')
 original=[CANON/'HANDOFF_COPY_RECEIPT.json',HANDOFF/'HANDOFF_COPY_RECEIPT.json',CANON/'PHONE_TEST_CHECKPOINT.json',HANDOFF/'PHONE_TEST_CHECKPOINT.json']
 for path in original[:2]:require(sha(path)==ORIGINAL_HANDOFF_SHA,'Historical207 receipt changed')
 for path in original[2:]:require(read(path)['apk_sha256']==SHA and read(path)['physical_phone_test']=='pending','Historical207 checkpoint differs')
 # The existing README/workflow/checklists are retained as historical bytes.
 original_docs=[Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\download_spacing_v207')/'README.md',HANDOFF/'README.md']
 original_docs.extend(sorted((Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\download_spacing_v207')/'documents').glob('*')))
 original_docs.extend(sorted((HANDOFF/'documents').glob('*')))
 originals=[pin(path) for path in original+original_docs if path.is_file()]
 copies=[]
 for folder in ['publication','audit']:
  for source in sorted((ROOT/folder).rglob('*')):
   if source.is_file() and '__pycache__' not in source.parts and source.suffix.lower() in {'.mjs','.py','.json','.md','.html','.txt'} and source.name!='MIRROR_HANDOFF_COPY_RECEIPT.json':
    for destination in DESTINATIONS:copies.append(copy(source,destination/(folder+'/'+source.relative_to(ROOT/folder).as_posix())))
 checkpoint=read(BASE/'PHONE_TEST_CHECKPOINT.json')
 require(checkpoint['apk_sha256']==SHA and checkpoint['physical_phone_test']=='pending' and checkpoint['runtime_verified'] is False,'Original phone state differs')
 mirror_checkpoint={**checkpoint,'schema':'ffbe-v207-github-mirror-phone-checkpoint-v1','apk_url':URL,'luminest_mirror_url':LUMINEST,'APK_unchanged':True,'event_assets_unchanged':True,'asset_version':206,'original_checkpoint_sha256':sha(BASE/'PHONE_TEST_CHECKPOINT.json'),'phone_results':None}
 text=f'''# Build 207 GitHub mirror

[Download the exact build 207 APK from GitHub]({URL}). [Luminest mirror]({LUMINEST}) remains available.

VersionCode: 207. Asset version: 206. APK size: {SIZE:,} bytes. SHA-256: `{SHA}`.

This is the same signed APK; there was no rebuild or event asset change. The GitHub release is a beta prerelease and does not become the production latest release. The beta updater now uses the GitHub URL in both download fields, and the beta page offers GitHub first while retaining Luminest and all earlier builds.

The reviewed publisher verified the complete public GitHub APK size/hash and first/middle/last ranges. Its upload/updater receipts and exact source pin are retained here; the page receipt binds the verified upload and canonical updater to the sole button-block change. This handoff performed local receipt and copy validation, without repeating the large APK download.

Phone, runtime and save results remain pending for this exact hash. Use the existing [phone checklist]({checkpoint['checklist_url']}); install over the current app and keep data. Observe download counter spacing, reopen, and check saves/settings. Report the exact APK hash and device/Android version with results. Inherited event/banner/CG/native limits remain as recorded in the original 207 documents. Image 2.5 model verification remains unverified.

Original 207 documents, receipts, checkpoint and exported APK remain untouched. This new folder contains only mirror source/review/publication evidence and a separate pending mirror checkpoint; unchanged art, packs, APK bytes, signing material and credentials are not copied.
'''
 docs=[]
 for destination in DESTINATIONS:
  docs.append(create(destination/'README.md',text.encode('utf-8')))
  docs.append(create(destination/'PHONE_TEST_CHECKPOINT.json',blob(mirror_checkpoint)))
 for before in originals:require(pin(Path(before['path']))==before,'Historical207 bytes changed during append')
 receipt={'schema':'ffbe-v207-github-mirror-handoff-v1','passed':True,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versionCode':207,'asset_version':206,'apk':{'github_url':URL,'luminest_mirror_url':LUMINEST,'bytes':SIZE,'sha256':SHA},'GitHub_release_id':upload['release_id'],'publisher_source_sha256':PUBLISHER_SHA,'root_public_upload_full_hash_and_three_ranges_verified':True,'large_public_download_repeated_by_handoff':False,'copies':copies,'documents':docs,'copy_count':len(copies),'original207_files_preserved':originals,'historical_document_or_receipt_writes':False,'APK_copied_again':False,'event_assets_copied_or_changed':False,'credentials_or_signing_material_copied':False,'physical_phone_test':'pending','runtime_verified':False}
 data=blob(receipt)
 for target in [ROOT/'audit/MIRROR_HANDOFF_COPY_RECEIPT.json',*[destination/'MIRROR_HANDOFF_COPY_RECEIPT.json' for destination in DESTINATIONS]]:create(target,data)
 print(json.dumps({'passed':True,'copies':len(copies),'receipt':str(ROOT/'audit/MIRROR_HANDOFF_COPY_RECEIPT.json'),'receipt_sha256':hashlib.sha256(data).hexdigest(),'APK_sha256':SHA,'physical_phone_test':'pending'}))

if __name__=='__main__':main()
