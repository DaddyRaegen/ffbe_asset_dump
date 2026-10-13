"""Append-only208 handoff preparation; local files only, no remote/device actions."""
from pathlib import Path
import hashlib,json,sys,shutil
ROOT=Path(r'S:\FFBE JP Data Export\build\v208-production')
CANON=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\production_v208')
RELEASE=CANON/'release208'
HANDOFF=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-production-v208')
BASELINE='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
FINAL_APK='9d21fc8b61c9900eaacb1c2ddef2cabcad1e97d2dc720be16ac09b06fc0086b4'
MESSAGE='added all the global story events and event battles.'
ISSUES=['Overdrive skills crash the game.','dark visions crash the game']
def require(value,message):
 if not value:raise RuntimeError(message)
def sha(file):
 with Path(file).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def pin(file):
 file=Path(file);return {'path':str(file),'bytes':file.stat().st_size,'sha256':sha(file)}
def blob(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def read(file):return json.loads(Path(file).read_text(encoding='utf-8-sig'))
def create(file,data):
 require(any(file.resolve().is_relative_to(root.resolve()) for root in [CANON,HANDOFF,ROOT/'audit']),'Outside208 handoff roots')
 if file.exists():require(file.read_bytes()==data,'Refusing to overwrite different archive bytes: '+str(file))
 else:file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
 return pin(file)
def copy(source,target):
 source=Path(source);target=Path(target)
 require(any(target.resolve().is_relative_to(root.resolve()) for root in [CANON,HANDOFF]),'Copy outside208 archive roots')
 before=pin(source)
 if target.exists():require(target.stat().st_size==before['bytes'] and sha(target)==before['sha256'],'Refuse different existing archive file: '+str(target))
 else:target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 require(sha(source)==before['sha256'] and target.stat().st_size==before['bytes'] and sha(target)==before['sha256'],'Source or copy changed')
 return {'source':str(source),'destination':str(target),'bytes':before['bytes'],'sha256':before['sha256']}

README='''# Build208 production archive

This archive records the production transition from exact published build207, with finite event/JP Memories banner corrections and ordering changes. Its executable foundation remains production Patch5, with Java classes, native libraries, startup files, downloader, cache and saves unchanged. Android versionCode and the existing updater constants become208; the native content catalog and side manifest pin the finite changed assets.

Final identity, live GitHub link and qualification/publication state belong in `release208/RELEASE.md` and `release208/RELEASE_STATE.json` in the canonical S archive, or `RELEASE.md` and `RELEASE_STATE.json` in the T handoff. Preparation records do not prove a live release. Physical phone results remain pending unless a later exact-build phone receipt records them.

Read `documents/PRODUCTION_WORKFLOW.md`, `documents/KNOWN_LIMITS.md` and `documents/PHONE_TEST_CHECKLIST.md`. The collector retains the signed APK, finite source/plans, changed payload/artwork and exact qualification/publication/BlueStacks evidence. Unchanged historical artwork and packs remain in their prior archives and are referenced by hashes. Signing material, publisher credentials, build temporary files and device/user caches are excluded.
'''
WORKFLOW='''# Build208 production workflow

The user authorized promotion to production once the build is finished and tested. Host this and future APK releases on GitHub. The main Android download page should point directly to the current verified GitHub APK; preserve historical releases and rollback links. Source branch pushes are not required by this release.

The byte baseline is build207 SHA-256 `d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e`, package `com.square_enix.ffbejpn`, signer SHA-256 `21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee`. Only four non-signing APK members may change: `AndroidManifest.xml`, `assets/frida_script.js`, `assets/content_delivery.tsv` and `assets/side_stories/manifest.tsv`. Keep all170 asset members, DEX/native bytes and unrelated compressed member payloads unchanged. New banner CPK members and icon-master remaps are external finite plan operations. Retain all1898 content descriptor paths and1857 side-manifest paths, plus accepted old side hashes; download only changed/missing files with the existing native downloader.

Patch5 compares logical update version5, then reads `url` and `changelog` from the latest GitHub `patch_version.json`. Build208 sets the existing script's logical version208 and production latest updater/download routes. The update manifest must supply208 in `version` and `versionCode`, the exact GitHub APK in both `url` and `apk_url`, asset_version208 and a string-array changelog. Preserve the original legacy base/content manifest references; add current208 event-manifest/catalog aliases. Older APKs retain their embedded immutable native transports. The stable beta203 asset pointer remains unchanged.

Exact update message: `added all the global story events and event battles.` Exact known issues: `Overdrive skills crash the game.` and `dark visions crash the game`.

1. Seal the finite `BANNER_PLAN.json` and `ORDER_PLAN.json`, prepare the modified payloads/catalog/side manifest and immutable `DOWNLOAD_PLAN.json`, and pass independent transport qualification. Preserve actual Dark Visions art/special sizes. Move unmatched missing-banner entries to the bottom without removing their gameplay rows.
2. Stage only the new208 data pack/catalog/manifest files in a GitHub prerelease with `make_latest=false`; verify full public hashes and first/middle/last new-pack ranges. All current production routes still serve Patch5.
3. Build/sign208 and pass the independent exact-APK qualifier. Prepare the production Android card and fixed metadata; preserve all old links, iOS/Windows bytes and historical releases. Stage the APK and aliases as a nonlatest prerelease and verify full APK bytes plus three ranges.
4. Root tests the exact candidate in BlueStacks, retaining existing app data. `device/BLUESTACKS_V208_REVIEW.json` must pass and bind its APK size/SHA/versionCode. A BlueStacks smoke test is distinct from physical-phone or save-migration validation.
5. Promote only the qualified208 APK release to nonprerelease/latest. Verify canonical GitHub latest updater208, synchronize the guarded CDN updater and canonical beta APK updater, then update only the production Android index. Preserve the historical beta207 page, stable203 asset pointer, old Patch5 assets and main source ref.
6. Retain activation and public readback evidence, matching checksum/checklist and pending phone checkpoint. Copy source/report bytes without historical overwrite. Future builds use a fresh work/output directory and current qualification; do not run archival publication defaults against changed files.

Runnable work root: `S:/FFBE JP Data Export/build/v208-production`. Canonical root: `S:/FFBE JP Data Export/ffbe_asset_dump/tools/production_v208/release208`. T handoff: `T:/Projects/FFBE Patch/localization-rounds/2026-10-04-production-v208`. Canonical source snapshots preserve tested bytes and original absolute path pins; they are provenance, not permission to republish a historical default.
'''
LIMITS='''# Build208 known limits

User-provided known issues remain exact: `Overdrive skills crash the game.` and `dark visions crash the game`. Build208 changes banners/order and updater routing, with the original runtime/downloader preserved; it does not claim those gameplay crashes are repaired.

Physical-phone results remain pending. Root's eventual exact-APK BlueStacks report is emulator evidence only. Save migration remains unverified unless that report or a later physical test explicitly proves it. Do not uninstall or clear app data during installation.

Inherited event/server mechanics, original movie networking/CG availability, GL-only effects and native16KB/Android17 compatibility limits remain. Menus with all source-derived Global events do not prove every archived battle, movie or server mechanic works. Historical203 had a reported startup failure on ZFold8/Android17 without logs; do not infer the cause or208 result from it.

Unchanged206 derivative artwork, image-tool prompts and full deferred UI registry remain in the206 archive. The prior requested image-model version was not exposed by the tool and remains unverified. New208 finite banner source/geometry/remap evidence must distinguish authentic originals, retained derivative art and neutral fallback cards. Missing authentic cover art is represented honestly and sorted last; actual Dark Visions artwork is protected.
'''
CHECKLIST='''# Build208 physical phone checklist

Use only the exact live GitHub APK/size/SHA recorded in the final release state and phone checkpoint. Physical testing is pending; emulator screenshots are not a phone pass. Target prior user device: ZFold8, Android17.

1. Install over the current English edition and retain app data, settings and saves.
2. Confirm normal startup, current save/profile and reuse of completed downloads; let only changed/missing assets finish.
3. Check Story Events, Event Battles and JP Memories cover sizes, correct titles and missing-banner bottom ordering. Keep actual Dark Visions artwork distinct.
4. Open representative added Global stories/battles and check dialogue and normal play. Check again after restarting.
5. On an older installation, confirm the update dialog links to the exact208 GitHub APK. Report exact version/hash/device/Android version and any failure text.

Update message: added all the global story events and event battles.
Known issues: Overdrive skills crash the game. / dark visions crash the game
'''

def prepare():
 prior207=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\download_spacing_v207\release207')
 prior206=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\event_cleanup_v206\release206')
 names=[prior207/'HANDOFF_COPY_RECEIPT.json',prior207/'staged_build/SIGNED_SPACING_QUALIFICATION.json',prior207/'audit/PUBLIC_V207_REVIEW.json',prior207/'audit/INHERITED206_REFERENCE_PINS.json',prior207/'github_mirror_2026-10-04/MIRROR_HANDOFF_COPY_RECEIPT.json',prior206/'audit/DEFERRED_UI_RECORDS.json',prior206/'audit/EVENT71_DECISION_LEDGER.json']
 require(all(file.is_file() for file in names),'Prior sealed evidence missing')
 references={'schema':'ffbe-production208-inherited-reference-pins-v1','baseline_apk_sha256':BASELINE,'references':[pin(file) for file in names],'unchanged_historical_artwork_and_packs_copied_again':False,'historical_release_writes':False}
 create(ROOT/'audit/INHERITED_REFERENCE_PINS.json',blob(references))
 documents={'README.md':README,'documents/PRODUCTION_WORKFLOW.md':WORKFLOW,'documents/KNOWN_LIMITS.md':LIMITS,'documents/PHONE_TEST_CHECKLIST.md':CHECKLIST}
 rows=[]
 for base in [CANON,HANDOFF]:
  for name,text in documents.items():rows.append(create(base/name,text.encode('utf-8')))
  create(base/'HANDOFF_PREPARATION.json',blob({'schema':'ffbe-production208-handoff-preparation-v1','versionCode':208,'asset_version':208,'final_copy_complete':False,'APK_hosting_preference':'GitHub current and future releases','production_promotion_explicitly_authorized':True,'physical_phone_test':'pending','historical_release_writes':False}))
 plan={'schema':'ffbe-production208-bounded-handoff-plan-v1','prepared':True,'final_copy_complete':False,'canonical_root':str(CANON),'canonical_release_root':str(RELEASE),'handoff_root':str(HANDOFF),'required_final_gates':['Exact current signed208 APK/package/signer/baseline207','Final banner/order/download plan hashes','Independent signed and transport qualification passed','Verified immutable data/APK staging','Exact passed BlueStacks report','Successful production activation and canonical public routes','Root phone checkpoint physical_phone_test pending'],
 'copy_scope':['Exact signed APK','Frozen source/guard/publisher code and configs without secrets','Finite banner/order/download plans and source/remap/geometry audits','Only changed raw payloads and new immutable data files','Finite changed banner originals/derivatives and their source provenance','Qualification/publication/public-readback receipts and reproducer code','Exact emulator report and bounded screenshot evidence','Current matching phone checklist/checkpoint'],
 'exclude':['Private signing material','Credentials or tokens','User/device caches and saves','Build/classes/disassembly/fixture temporary trees','Duplicate unchanged old APKs/packs/artwork','Superseded unpublished drafts'],
 'copies_must_be_byte_hashed_and_append_only':True,'future_APK_hosting':'GitHub','history_overwrite':False,'physical_phone_test':'pending','documents':rows,'inherited_reference_pins':pin(ROOT/'audit/INHERITED_REFERENCE_PINS.json')}
 create(ROOT/'audit/HANDOFF_PLAN.json',blob(plan));print(json.dumps({'prepared':True,'canonical_root':str(CANON),'handoff_root':str(HANDOFF),'documents':len(rows),'final_copy_complete':False}))

def collect():
 # This collector does not publish, rebuild, query GitHub or operate a device.
 scope=read(ROOT/'audit/RELEASE_SCOPE.json');build=read(ROOT/'staged_build/PRODUCTION_APK_BUILD.json')
 signed=read(ROOT/'staged_build/SIGNED_PRODUCTION_QUALIFICATION.json');transport=read(ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json')
 download=read(ROOT/'asset_publication/DOWNLOAD_PLAN.json');banner=read(ROOT/'audit/BANNER_PLAN.json');order=read(ROOT/'audit/ORDER_PLAN.json')
 assets=read(ROOT/'publication/asset-stage-receipt.json');stage=read(ROOT/'publication/apk-stage-receipt.json')
 activation=read(ROOT/'publication/production-activation-receipt.json');plan=read(ROOT/'publication/plan.json')
 emulator=read(ROOT/'device/BLUESTACKS_V208_REVIEW.json');checkpoint=read(ROOT/'PHONE_TEST_CHECKPOINT.json')
 postpromotion=read(ROOT/'audit/POST_PROMOTION_APP_UPDATER_REVIEW.json')
 apk_sha=build['sha256'];apk=Path(build['apk']);apk_bytes=build['bytes']
 require(scope.get('candidate_revision')==3 and scope['explicit_production_promotion_authorized'] is True,'Final revision3 scope required')
 require(apk_sha not in {'193f8652dd15347f28002928bcb16860de6c958e1e6aa814c4eafcee4c45b893','90bbefdf32c14b6faf2ea635338e62bf3f5570ce6345c4053e4fb9b6b40045f6'},'Superseded208 APK cannot seal final handoff')
 require(apk_sha==FINAL_APK and apk_bytes==145206221,'Exact qualified revision3 APK identity required')
 require(build['versionCode']==208 and build['baseline_apk_sha256']==BASELINE and apk.is_file() and apk.stat().st_size==apk_bytes and sha(apk)==apk_sha,'Exact final208 APK differs')
 require(signed.get('passed') is True and signed['versionCode']==208 and signed['apk_sha256']==apk_sha and signed['apk_bytes']==apk_bytes and signed['baseline_apk_sha256']==BASELINE,'Exact signed final208 qualification required')
 require(download['release_tag']=='content-v208-d76ed937ddeb7ddd' and sha(ROOT/'asset_publication/DOWNLOAD_PLAN.json')=='9a3cf9b88759ef51fb14f482e77399f29ab349893ba71ac34d096edfb41e525e','Final revision3 download plan required')
 require(download['original_content_rows']==download['final_content_rows']==1898 and download['original_side_rows']==download['final_side_rows']==1857,'Final catalog/side membership changed')
 for field,file in [('banner_plan_sha256','audit/BANNER_PLAN.json'),('ordering_plan_sha256','audit/ORDER_PLAN.json'),('download_plan_sha256','asset_publication/DOWNLOAD_PLAN.json')]:require(signed[field]==sha(ROOT/file),'Signed final208 plan changed: '+field)
 require(signed['content_catalog_sha256']==download['content_catalog_sha256'] and signed['side_manifest_sha256']==download['side_manifest_sha256'],'Signed final208 metadata differs')
 require(transport.get('passed') is True and transport['download_plan_sha256']==signed['download_plan_sha256'] and transport['content_catalog_sha256']==signed['content_catalog_sha256'] and transport['side_manifest_sha256']==signed['side_manifest_sha256'],'Final transport qualification differs')
 require(len(banner['members'])==658 and banner['proportional_fit_member_count']==608 and banner['native_canvas_wrapper_member_count']==50 and banner['added_member_count']==470 and banner['replaced_member_count']==188 and banner['unchanged_original_member_count']==373 and len(banner['icon_rows'])==477 and order['fallback_count']==597,'Final revision3 banner/order scope differs')
 require(sum(len(table['operations']) for table in order['table_changes'])==599,'Final order operation count differs')
 require(assets.get('success') is True and assets['release_tag']==download['release_tag'] and assets['download_plan_sha256']==signed['download_plan_sha256'] and assets['content_catalog_sha256']==download['content_catalog_sha256'] and assets['side_manifest_sha256']==download['side_manifest_sha256'],'Final asset-stage receipt differs')
 for expected in download['files']:
  actual=next((f for f in assets['files'] if f['name']==expected['name']),None)
  require(actual and actual['bytes']==expected['bytes'] and actual['sha256']==expected['sha256'] and actual.get('full_download_verified') is True,'New immutable data proof differs')
  if expected['role']=='pack':require(len(actual.get('ranges',[]))==3 and all(r.get('verified') is True for r in actual['ranges']),'Pack range evidence required')
 require(stage.get('success') is True and stage['versionCode']==208 and stage['sha256']==apk_sha and stage['bytes']==apk_bytes and stage['publication_plan_sha256']==sha(ROOT/'publication/plan.json') and stage['asset_stage_receipt_sha256']==sha(ROOT/'publication/asset-stage-receipt.json'),'Final APK stage receipt differs')
 staged_apk=next(f for f in stage['files'] if f['role']=='apk')
 require(staged_apk['full_download_verified'] is True and len(staged_apk['ranges'])==3 and all(r['verified'] is True for r in staged_apk['ranges']),'Public full/ranged final APK proof required')
 require(emulator.get('passed') is True and emulator['versionCode']==208 and emulator['apk_sha256']==apk_sha and emulator['apk_bytes']==apk_bytes,'Passed exact final208 BlueStacks report required')
 require(activation.get('success') is True and activation['versionCode']==208 and activation['asset_version']==208 and activation['sha256']==apk_sha and activation['bytes']==apk_bytes and activation['apk_url']==stage['url'] and activation['prerelease'] is False and activation['make_latest'] is True,'Final production activation required')
 require(activation['publication_plan_sha256']==sha(ROOT/'publication/plan.json') and activation['asset_stage_receipt_sha256']==sha(ROOT/'publication/asset-stage-receipt.json') and activation['apk_stage_receipt_sha256']==sha(ROOT/'publication/apk-stage-receipt.json') and activation['signed_qualification_sha256']==sha(ROOT/'staged_build/SIGNED_PRODUCTION_QUALIFICATION.json'),'Activation receipt pins differ')
 require(activation['BlueStacks']['passed'] is True and activation['BlueStacks']['apk_sha256']==apk_sha and activation['BlueStacks']['report_sha256']==sha(ROOT/'device/BLUESTACKS_V208_REVIEW.json'),'Activated emulator evidence differs')
 require(activation['update_message']==MESSAGE and activation['known_issues']==ISSUES and activation['physical_phone_test']=='pending' and checkpoint['apk_sha256']==apk_sha and checkpoint['physical_phone_test']=='pending','Phone/checkpoint/message state differs')
 for key in ['source_main_unchanged','old_patch5_release_preserved','stable_beta203_asset_pointer_unchanged']:require(activation[key] is True,'Protected production state differs: '+key)
 require(activation['page']['sha256']==plan['page']['sha256'] and all(activation[key]['canonical_public_verified'] is True for key in ['latest_updater','cdn_updater','beta_updater','page']),'Canonical final production routes are not verified')
 require(postpromotion.get('passed') is True and postpromotion['apk_sha256']==apk_sha and postpromotion['apk_bytes']==apk_bytes and postpromotion['observed_updater']=='local=208 remote=208' and postpromotion['home_reached'] is True and postpromotion['app_data_preserved'] is True and postpromotion['production_activation_sha256']==sha(ROOT/'publication/production-activation-receipt.json'),'Exact post-promotion native updater/home evidence required')
 for name,expected in plan['sources'].items():require(sha(ROOT/'publication'/name)==expected,'Sealed publisher source changed: '+name)
 public_path=ROOT/'audit/PUBLIC_V208_REVIEW.json'
 if public_path.exists():
  public=read(public_path);require(public.get('passed') is True and public['apk_sha256']==apk_sha,'Optional independent public report differs')
 for revision in [1,2]:
  previous=read(ROOT/f'audit/SUPERSEDED_CANDIDATE{revision}_REFERENCE.json');require(previous['superseded'] is True and previous['production_activated'] is False,'Supersession record differs')
 selected={}
 def include(file):
  file=Path(file).resolve();require(file.is_file() and file.is_relative_to(ROOT.resolve()),'Final copy source outside frozen208 root: '+str(file))
  require(file.suffix.lower() not in {'.jks','.keystore','.key','.pem','.p12','.pfx'} and not any(word in file.name.lower() for word in ['credential','private_key','secret_token']),'Private file excluded')
  selected[file.relative_to(ROOT.resolve()).as_posix()]=file
 suffixes={'.py','.js','.mjs','.json','.md','.txt','.csv','.html','.tsv'}
 for folder in ['source','guard','publication']:
  for file in sorted((ROOT/folder).rglob('*')):
   if file.is_file() and '__pycache__' not in file.parts and 'unpublished_draft' not in file.parts and file.suffix.lower() in suffixes:include(file)
 for file in sorted((ROOT/'audit').iterdir()):
  if file.is_file() and file.suffix.lower() in suffixes and file.name!='HANDOFF_COPY_RECEIPT.json':include(file)
 for file in sorted((ROOT/'staged_build').iterdir()):
  if file.is_file() and file.suffix.lower() in {'.json','.txt','.md'}:include(file)
 for folder in (ROOT/'audit').iterdir():
  if folder.is_dir() and ('signed' in folder.name or 'qualification' in folder.name):
   for file in folder.glob('*.txt'):include(file)
 for file in download['files']:
  require(pin(Path(file['local_path']))['sha256']==file['sha256'],'Published new data file changed');include(file['local_path'])
 include(ROOT/'asset_publication/DOWNLOAD_PLAN.json')
 for file in download['new_pack_files']:
  require(pin(Path(file['local_path']))['sha256']==file['sha256'],'Prepared raw payload changed');include(file['local_path'])
 for file,expected in [('payload/content_delivery.tsv',download['content_catalog_sha256']),('payload/side_stories/manifest.tsv',download['side_manifest_sha256'])]:require(sha(ROOT/file)==expected,'Prepared builder metadata changed');include(ROOT/file)
 for member in banner['members']:
  candidate=Path(member['candidate']['local_path']);require(sha(candidate)==member['candidate']['sha256'],'Final artwork changed');include(candidate)
  source=member.get('provenance',{}).get('local_path')
  if source and Path(source).resolve().is_relative_to(ROOT.resolve()):include(source)
 # Retain exact referenced208 screenshots/scoped logs, rather than device caches.
 device_evidence=set()
 def screen_refs(value):
  if isinstance(value,dict):
   if isinstance(value.get('path'),str) and value['path'].lower().endswith(('.png','.log','.txt')):
    file=Path(value['path'])
    if file.is_file() and file.resolve().is_relative_to((ROOT/'device').resolve()):
     require(file.stat().st_size==value['bytes'] and sha(file)==value['sha256'],'Referenced device evidence changed')
   for item in value.values():screen_refs(item)
  elif isinstance(value,list):
   for item in value:screen_refs(item)
  elif isinstance(value,str) and not value.startswith(('https://','http://')) and value.lower().endswith(('.png','.log','.txt')):
   for file in [Path(value),ROOT/value,ROOT/'device'/Path(value).name]:
    if file.is_file() and file.resolve().is_relative_to((ROOT/'device').resolve()):device_evidence.add(file.resolve());break
 screen_refs(emulator);screen_refs(postpromotion)
 for file in [ROOT/'audit/RENDERED_207_BANNER_REVIEW.json',ROOT/'audit/NONSTANDARD_GENUINE_BANNER_GEOMETRY.json']:
  if file.is_file():screen_refs(read(file))
 for file in sorted(device_evidence):include(file)
 for name in ['probe_bluestacks.py','seal_final_review.py']:include(ROOT/'device'/name)
 include(ROOT/'device/BLUESTACKS_V208_REVIEW.json');include(ROOT/'PHONE_TEST_CHECKPOINT.json');include(apk)
 copies=[]
 for relative,source in sorted(selected.items()):
  copies.append(copy(source,RELEASE/relative))
  t_relative='dist/'+apk.name if source==apk.resolve() else 'PHONE_TEST_CHECKPOINT.json' if relative=='PHONE_TEST_CHECKPOINT.json' else 'evidence/'+relative
  copies.append(copy(source,HANDOFF/t_relative))
 header=f'''# Published production208 — revision3

GitHub APK: [{apk.name}]({activation['apk_url']})

VersionCode208 / asset_version208. Size: {apk_bytes:,}bytes. SHA-256: `{apk_sha}`.

Signed qualification, exact local transport verification, full public APK/data downloads and three ranges, BlueStacks review and production activation passed for these exact bytes. The canonical latest updater, CDN updater, beta APK updater and production Android page are verified. Physical phone testing remains pending; save migration remains unverified. Overdrive and Dark Visions crashes remain known issues.

Final scope:658 technical banner encodings =608 proportionate fits +50 pixel-preserving native wrappers;470 CPK additions/188 replacements/373 preserved original raw members;477 icon filename rows;597 missing-art books sorted last through599 order-only changes. The50 genuine600×120 artworks retain exact pixels centered at20,60 on640×240 transparent canvases. Protected Dark Visions art/order remains unchanged. All1898 descriptor paths and1857 side-manifest paths remain; old cache/download behavior is preserved.

Update message: {MESSAGE}
Known issues: {ISSUES[0]} / {ISSUES[1]}

Candidates1 and2 were superseded after emulator review and never activated in production. Their immutable prereleases and local full archives remain intact; only revision3 is this release. Early supersession notes record the next candidate planned at that time and do not identify the final APK. Use this full SHA and its matching receipts.

Evidence is retained under `staged_build`, `audit`, `publication` and `device` in the canonical release; under `evidence` in the T handoff. `PHONE_TEST_CHECKPOINT.json` and the immutable phone checklist match this APK. Historical206/207 artwork, full deferred UI records and unchanged packs remain pinned in `INHERITED_REFERENCE_PINS.json`; they are not duplicated here. GitHub remains the APK hosting preference for future releases. No main source push or historical overwrite occurred.
'''
 state={'schema':'ffbe-production208-final-release-state-v1','candidate_revision':3,'versionCode':208,'asset_version':208,'production_active':True,'apk_url':activation['apk_url'],'apk_sha256':apk_sha,'apk_bytes':apk_bytes,'data_release_tag':download['release_tag'],'signed_qualification':pin(ROOT/'staged_build/SIGNED_PRODUCTION_QUALIFICATION.json'),'transport_qualification':pin(ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json'),'BlueStacks_review':pin(ROOT/'device/BLUESTACKS_V208_REVIEW.json'),'activation_receipt':pin(ROOT/'publication/production-activation-receipt.json'),'phone_checkpoint':pin(ROOT/'PHONE_TEST_CHECKPOINT.json'),'physical_phone_test':'pending','save_migration_verified':False,'candidate1_and2_production_activated':False,'GitHub_future_APK_hosting_preference':True}
 for base in [RELEASE,HANDOFF]:create(base/'RELEASE.md',header.encode('utf-8'));create(base/'RELEASE_STATE.json',blob(state))
 receipt={'schema':'ffbe-production208-frozen-handoff-copy-v1','passed':True,'final_copy_complete':True,'candidate_revision':3,'versionCode':208,'asset_version':208,'work_root':str(ROOT),'canonical_release_root':str(RELEASE),'handoff_root':str(HANDOFF),'apk':{'url':activation['apk_url'],**pin(apk)},'copies':copies,'copy_count':len(copies),'source_and_destination_hashes_verified':True,'new_artwork_count':658,'referenced_device_screenshot_count':sum(file.suffix.lower()=='.png' for file in device_evidence),'referenced_device_log_count':sum(file.suffix.lower() in {'.log','.txt'} for file in device_evidence),'postpromotion_native_updater_review':pin(ROOT/'audit/POST_PROMOTION_APP_UPDATER_REVIEW.json'),'historical_release_writes':False,'superseded_APKs_or_packs_copied':False,'unchanged_historical_artwork_and_packs_copied':False,'signing_material_or_credentials_copied':False,'BlueStacks_passed':True,'physical_phone_test':'pending','save_migration_verified':False,'final_release_state':state}
 data=blob(receipt)
 for target in [ROOT/'audit/HANDOFF_COPY_RECEIPT.json',RELEASE/'HANDOFF_COPY_RECEIPT.json',HANDOFF/'HANDOFF_COPY_RECEIPT.json']:create(target,data)
 print(json.dumps({'passed':True,'copy_count':len(copies),'receipt':str(ROOT/'audit/HANDOFF_COPY_RECEIPT.json'),'receipt_sha256':hashlib.sha256(data).hexdigest(),'apk_sha256':apk_sha,'apk_bytes':apk_bytes,'physical_phone_test':'pending'}))
if __name__=='__main__':
 require(len(sys.argv)==2 and sys.argv[1] in ['--prepare','--collect'],'Use --prepare or --collect')
 prepare() if sys.argv[1]=='--prepare' else collect()
