"""Append-only207 documentation and bounded final release handoff; no network."""
from pathlib import Path
import datetime,hashlib,json,shutil,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v207-download-spacing')
PREVIOUS=ROOT.parent/'v206-event-cleanup'
CANON=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\download_spacing_v207')
RELEASE=CANON/'release207'
HANDOFF=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-download-spacing-v207')
APK_SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
BASELINE_SHA='345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d'
PUBLIC206_SHA='1c71f5b2c58740bc0c1f2cec35dc5881fceceff0c0b875e380830b771d42697a'
def require(value,message):
 if not value:raise RuntimeError(message)
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def pin(path):return {'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}
def blob(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def create(path,data):
 require(path.resolve().is_relative_to(CANON.resolve()) or path.resolve().is_relative_to(HANDOFF.resolve()) or path.resolve().is_relative_to((ROOT/'audit').resolve()),'Outside owned207 roots')
 if path.exists():require(path.read_bytes()==data,'Existing different207 archive file: '+str(path))
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 return pin(path)
def copy(source,target):
 before=pin(source);create(target,source.read_bytes())
 require(pin(source)==before and target.stat().st_size==before['bytes'] and sha(target)==before['sha256'],'Source/copy changed')
 return {'source':str(source),'destination':str(target),'bytes':before['bytes'],'sha256':before['sha256']}

README='''# Build 207 download spacing archive

This release changes the download counter's punctuation spacing over exact published build 206. Final publication is pending during archive preparation. Phone results remain pending.

Read `documents/DOWNLOAD_SPACING_RELEASE_WORKFLOW.md`, `documents/KNOWN_LIMITS.md` and `documents/PHONE_TEST_CHECKLIST.md`. Frozen source, signed APK, exact qualification and publication evidence belong in `release207` in the canonical S archive; the T handoff uses `dist` and `evidence`. The copy receipt hashes all retained bytes. Unchanged 206 artwork, assets and event registries are referenced with source pins instead of copied again.
'''
WORKFLOW='''# Download counter spacing: APK 207

Final publication is pending during archive preparation. Planned URLs are not live-release evidence. Phone results remain pending.

## Exact change

Use published build 206, SHA-256 `345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d`, as the byte baseline. Its executable foundation remains production Patch 5. This user-authorized fix is limited to the existing English punctuation helper: grouped numeric MB/MB counters keep compact ASCII commas rather than wide comma cells. The precise counter grammar is recorded in `DOWNLOAD_SPACING_PLAN.json`; all other display rules retain their existing behavior.

Among non-signing APK members, only `AndroidManifest.xml` (typed versionCode 206 to 207) and `assets/frida_script.js` (the finite punctuation helper edit and existing PATCH_VERSION 206 to 207) may differ. Standard signing metadata is regenerated for the new APK. DEX, native libraries, resources, member set, all 169 non-script assets, startup, menus, banners, party hooks, movies, downloader/cache/resume/callbacks, lifecycle and saves retain their existing bytes and code. Use the same package and signer so 207 updates over the installed app.

All 1,898 content descriptors and 1,857 side-manifest paths remain byte-identical to 206. Reuse the immutable `beta-content-v206-ac96f646eaa91996` asset release. `asset_version` remains 206; there are no new packs, asset paths or data uploads. This release does not rebuild the 206 event data or artwork.

## Qualification and publication

1. Qualify the exact signed APK against 206 with the independent spacing guard, focused native-format/punctuation tests, raw ZIP preservation checks and actual package/signer/alignment tools. An old report does not qualify changed bytes.
2. Run the network-free publisher scope fixture against the final signed reports and sealed 206 inputs. Stage the immutable APK under `downloads/beta/releases/download-spacing-v207-<16-SHA>/` and verify full bytes plus first/middle/last ranges.
3. Publish immutable release/checksum/checklist files, update only beta `channels/beta/patch_version.json` with version/versionCode 207, asset_version 206, matching `url`/`apk_url` and `changelog: []`, wait for canonical raw readback, then activate `/downloads/beta/index.html`. Retain all eight previous APK links. The narrow GitHub helper cannot upload data packs, create releases or push source files.
4. Independently read back the exact APK and ranges, nine APK links, updater and immutable metadata/checklist. Recheck the two small reused 206 catalog/manifest files, production/legacy public files, main/latest and stable203 asset pointer. The unchanged 206 pack is not downloaded again; its prior full/range proof remains pinned.
5. Offer Kev the exact verified live APK, size/SHA and matching checklist. Record physical results only when supplied by Kev. Preserve all historical release bytes and evidence.

## Inherited source and asset evidence

`audit/INHERITED206_REFERENCE_PINS.json` points to the frozen 206 signed qualification, public verification, handoff receipt, cleanup/banner plans, full 1,760-record deferred UI registry, menu decision ledger, original banner source mappings, image-tool prompt/follow-up provenance and native encoding record. The unchanged artwork and raw event files stay in `S:/FFBE JP Data Export/ffbe_asset_dump/tools/event_cleanup_v206/release206` and `T:/Projects/FFBE Patch/localization-rounds/2026-10-04-event-cleanup-v206`. Source pins retain full paths as provenance; future builds require a fresh working/output directory and current qualification, never overwriting historical defaults.

The inherited menu contains 77 Story Event, 376 Event Battle and 450 JP Memories books. The 20 moves, 37 deferred Vortex families, one separate deferred greeting preview, three named removals and 12 derivative banner replacements remain exactly 206. Full records and original/generated/native artwork are retained in the 206 archive, including the honest Image 2.5 model state (`model_version_verified=false`).

## Retained outputs

Runnable work root: `S:/FFBE JP Data Export/build/v207-download-spacing`. Canonical archive: `S:/FFBE JP Data Export/ffbe_asset_dump/tools/download_spacing_v207/release207`. T handoff: `T:/Projects/FFBE Patch/localization-rounds/2026-10-04-download-spacing-v207`. Retain source, guard/tests, finite plan/native proof, small frozen206 publication inputs, signed APK, qualification/publication/readback reports and pending phone checkpoint. Exclude signing material, credentials, fixture caches/classes, build/disassembly intermediates and duplicate unchanged art/packs.
'''
LIMITS='''# Build 207 known limits

Final publication is pending during archive preparation. No phone result is recorded.

The spacing change is supported by the native counter format and isolated punctuation tests. Its actual appearance on the phone remains pending; it does not alter the underlying downloader. Same DEX/native/assets do not prove physical runtime, saves or save migration for a new signed APK.

All build 206 event, regional-source, banner and engine limits remain. The menus contain 77 Story Event books and 376 Event Battle books, not a claim that every historical event is fully playable. Some archived scenes, English text and server mechanics remain incomplete. GL-only effects, morale and limited-use stock behavior retain the Patch 5/205 limitations. Original/movie networking and CG availability are unchanged; there is no new CG completeness claim.

The 206 tool-translated/reconstructed banners and Revival Part 1 companion remain derivative artwork. Actual title/frame/press rendering is still a phone check. The requested Image 2.5 model could not be verified because the tool exposed no selector. Full provenance remains in the 206 archive.

ZIP alignment and exact native preservation do not establish Android 17 or native ELF 16 KB compatibility. Historical 203 had a reported startup failure on Z Fold 8/Android 17 without logs; it does not establish the outcome or cause for 207. No agent installation, device-file reads, battles, save/cache changes, uninstall or clear-data action is part of this release checkpoint.
'''
CHECKLIST='''# Kev's build 207 phone checklist

Final publication is pending during archive preparation. Use the verified link/version/size/SHA in the final `PHONE_TEST_CHECKPOINT.json` and immutable `phone-test-checklist.txt`. Target: Z Fold 8, Android 17.

1. Install over the current app and retain app data. Check saves and settings.
2. During an existing native download, inspect the grouped MB/MB counter. The apparent gap after commas should be removed. Capture the affected line if it remains. Other progress/download behavior should match 206.
3. Reopen and recheck saves/settings and existing event menus. The 206 assets should be reused; 207 adds no packs.
4. Report pass/fail, exact APK hash, device/Android version and any error text. Keep phone/runtime/save results pending until supplied. Do not uninstall or clear data.
'''

def references():
 base=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\event_cleanup_v206\release206')
 names=['HANDOFF_COPY_RECEIPT.json','staged_build/SIGNED_EVENT_QUALIFICATION.json','audit/PUBLIC_V206_REVIEW.json','audit/CLEANUP_PLAN.json','audit/DEFERRED_UI_RECORDS.json','audit/EVENT71_DECISION_LEDGER.json','audit/REQUESTED_BANNER_SOURCES.json','audit/BANNER_PLAN.json','artwork/banner_outputs/IMAGE_TOOL_PROMPTS.json','artwork/banner_outputs/IMAGE_TOOL_FOLLOWUPS.json','artwork/banner_outputs/IMAGE_TOOL_PRESS_TRANSLATIONS.json','artwork/banner_outputs/NATIVE_BANNERS.json','asset_publication/DOWNLOAD_PLAN.json']
 require(sha(base/'audit/PUBLIC_V206_REVIEW.json')==PUBLIC206_SHA,'Frozen206 public proof differs')
 value={'schema':'ffbe-v207-inherited206-reference-pins-v1','asset_version':206,'baseline_APK_sha256':BASELINE_SHA,'immutable_asset_release':'beta-content-v206-ac96f646eaa91996','references':[pin(base/name) for name in names],'unchanged_assets_and_artwork_copied_again':False,'runtime_verified':False,'model_version_verified':False}
 create(ROOT/'audit/INHERITED206_REFERENCE_PINS.json',blob(value))

def prepare():
 references();docs={'README.md':README,'documents/DOWNLOAD_SPACING_RELEASE_WORKFLOW.md':WORKFLOW,'documents/KNOWN_LIMITS.md':LIMITS,'documents/PHONE_TEST_CHECKLIST.md':CHECKLIST}
 rows=[]
 for base in [CANON,HANDOFF]:
  for name,text in docs.items():rows.append(create(base/name,text.encode('utf-8')))
  create(base/'HANDOFF_PREPARATION.json',blob({'schema':'ffbe-v207-handoff-preparation-v1','final_copy_complete':False,'versionCode':207,'asset_version':206,'physical_phone_test':'pending','historical_release_writes':False}))
 report={'passed':True,'schema':'ffbe-v207-handoff-skeleton-v1','final_copy_complete':False,'documents':rows,'runtime_verified':False}
 create(ROOT/'audit/HANDOFF_SKELETON.json',blob(report));print(json.dumps({'prepared':True,'documents':len(rows),'phone':'pending'}))

def collect():
 references();build=read(ROOT/'staged_build/DOWNLOAD_SPACING_APK_BUILD.json');signed=read(ROOT/'staged_build/SIGNED_SPACING_QUALIFICATION.json')
 activation=read(ROOT/'publication/activation-receipt.json');stage=read(ROOT/'publication/apk-stage-receipt.json');public=read(ROOT/'audit/PUBLIC_V207_REVIEW.json');local=read(ROOT/'audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json')
 require(build['sha256']==APK_SHA and build['bytes']==145206221 and build['versionCode']==207 and build['baseline_apk_sha256']==BASELINE_SHA,'Exact207 build differs')
 require(signed['passed'] is True and signed['apk_sha256']==APK_SHA and signed['apk_bytes']==build['bytes'] and signed['expected_js_delta_passed'] is True,'Signed207 qualification differs')
 require(activation['success'] is True and activation['versionCode']==207 and activation['asset_version']==206 and activation['sha256']==APK_SHA and activation['bytes']==build['bytes'] and activation['new_asset_uploads']==0,'207 publication incomplete')
 require(stage['success'] is True and stage['apk']['sha256']==APK_SHA and stage['apk']['bytes']==build['bytes'],'Staged207 APK differs')
 require(public['passed'] is True and public['apk_sha256']==APK_SHA and public['apk_bytes']==build['bytes'] and public['versionCode']==207 and public['asset_version']==206 and public['event_assets']['unchanged_pack_re_downloaded'] is False,'Independent207 public review differs')
 require(local['passed'] is True,'Network-free publication scope review missing')
 require(sha(ROOT/'audit/read_public207.mjs')==public['checker_sha256'],'Public checker bytes changed')
 require(activation['runtime_verified'] is False and activation['physical_phone_test']=='pending' and public['runtime_verified'] is False,'Phone state must remain pending')
 apk=Path(build['apk']);require(sha(apk)==APK_SHA and apk.stat().st_size==build['bytes'],'Signed207 APK changed')
 checkpoint=read(ROOT/'PHONE_TEST_CHECKPOINT.json');require(checkpoint['apk_sha256']==APK_SHA and checkpoint['physical_phone_test']=='pending' and checkpoint['runtime_verified'] is False,'Phone checkpoint differs')
 copies=[]
 def both(source,rel,t_rel=None):
  copies.append(copy(source,RELEASE/rel));copies.append(copy(source,HANDOFF/(t_rel or 'evidence/'+rel)))
 for folder in ['source','guard','publication']:
  for path in sorted((ROOT/folder).rglob('*')):
   if path.is_file() and '__pycache__' not in path.parts and path.suffix.lower() in {'.py','.js','.mjs','.json','.md','.txt','.html'}:both(path,folder+'/'+path.relative_to(ROOT/folder).as_posix())
 for path in sorted((ROOT/'audit').iterdir()):
  if path.is_file() and path.suffix.lower() in {'.py','.js','.mjs','.json','.md','.txt','.csv'} and path.name!='HANDOFF_COPY_RECEIPT.json':both(path,'audit/'+path.name)
 for path in sorted((ROOT/'audit/signed_spacing_tools').glob('*.txt')):
  both(path,'audit/signed_spacing_tools/'+path.name)
 for path in sorted((ROOT/'staged_build').iterdir()):
  if path.is_file() and path.suffix.lower() in {'.json','.txt','.md'}:both(path,'staged_build/'+path.name)
 both(PREVIOUS/'audit/PUBLIC_V206_REVIEW.json','inherited206/PUBLIC_V206_REVIEW.json')
 both(apk,'staged_build/dist/'+apk.name,'dist/'+apk.name)
 copies.append(copy(ROOT/'PHONE_TEST_CHECKPOINT.json',RELEASE/'PHONE_TEST_CHECKPOINT.json'));copies.append(copy(ROOT/'PHONE_TEST_CHECKPOINT.json',HANDOFF/'PHONE_TEST_CHECKPOINT.json'))
 header=f"Published beta APK 207: [{apk.name}]({activation['apk_url']}), {build['bytes']:,} bytes, SHA-256 `{APK_SHA}`. Signed spacing qualification, beta publication and independent public readback passed. Asset version remains 206. Phone, runtime and save results remain pending."
 phrases=['Final publication is pending during archive preparation. Phone results remain pending.','Final publication is pending during archive preparation. Planned URLs are not live-release evidence. Phone results remain pending.','Final publication is pending during archive preparation. No phone result is recorded.','Final publication is pending during archive preparation. Use the verified link/version/size/SHA in the final `PHONE_TEST_CHECKPOINT.json` and immutable `phone-test-checklist.txt`. Target: Z Fold 8, Android 17.']
 docs=[]
 for base in [CANON,HANDOFF]:
  for path in [base/'README.md',*sorted((base/'documents').glob('*.md'))]:
   text=path.read_text(encoding='utf-8')
   for phrase in phrases:text=text.replace(phrase,header)
   if path.name=='DOWNLOAD_SPACING_RELEASE_WORKFLOW.md':
    text+='\n## Final evidence\n\n`staged_build/SIGNED_SPACING_QUALIFICATION.json` binds the exact signed APK and finite script change. `audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json` binds the final publishers to network-free scope verification. `publication/apk-stage-receipt.json` and `activation-receipt.json` record beta publication. `audit/PUBLIC_V207_REVIEW.json` independently verifies the public APK/ranges, nine preserved APK offers, updater, release/checksum/checklist, reused 206 metadata and production protection. `PHONE_TEST_CHECKPOINT.json` and the immutable checklist remain pending for physical results.\n'
   path.write_text(text,encoding='utf-8');docs.append(pin(path))
  copies.append(copy(ROOT/'publication/site/phone-test-checklist.txt',base/'documents/phone-test-checklist.txt'))
 receipt={'schema':'ffbe-v207-frozen-handoff-copy-v1','passed':True,'final_copy_complete':True,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'work_root':str(ROOT),'canonical_release_root':str(RELEASE),'handoff_root':str(HANDOFF),'versionCode':207,'asset_version':206,'apk':{'url':activation['apk_url'],**pin(apk)},'source206_apk_sha256':BASELINE_SHA,'public_review':pin(ROOT/'audit/PUBLIC_V207_REVIEW.json'),'copies':copies,'documents':docs,'copy_count':len(copies),'source_and_destination_hashes_verified':True,'historical_release_writes':False,'unchanged206_artwork_and_pack_copied':False,'signing_material_or_credentials_copied':False,'runtime_verified':False,'physical_phone_test':'pending','model_version_verified':False}
 data=blob(receipt)
 for target in [ROOT/'audit/HANDOFF_COPY_RECEIPT.json',RELEASE/'HANDOFF_COPY_RECEIPT.json',HANDOFF/'HANDOFF_COPY_RECEIPT.json']:create(target,data)
 print(json.dumps({'passed':True,'copies':len(copies),'receipt':str(ROOT/'audit/HANDOFF_COPY_RECEIPT.json'),'receipt_sha256':hashlib.sha256(data).hexdigest(),'phone':'pending'}))

if __name__=='__main__':
 require(len(sys.argv)==2 and sys.argv[1] in ['--prepare','--collect'],'Use --prepare or --collect')
 prepare() if sys.argv[1]=='--prepare' else collect()
