"""Create append-only206 handoff documents; retain prior release bytes."""
from pathlib import Path
import hashlib,json,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
CANON=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\event_cleanup_v206')
HANDOFF=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-10-04-event-cleanup-v206')
def put_new(path,text):
 data=text.replace('\r\n','\n').encode('utf-8')
 if path.exists():
  if path.read_bytes()!=data:raise RuntimeError('Refusing existing different handoff bytes: '+str(path))
 else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
 return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
workflow='''# Event menu cleanup and original banner recovery: APK 206

Release preparation is pending final signed qualification and verified publication. Planned output files and URLs are not live-release evidence. The final publication receipt and phone checkpoint will identify the exact signed APK. Physical phone results remain pending.

## Foundation and exact scope

Use qualified published APK 205, 145,206,221 bytes, SHA-256 `e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039`. Its executable foundation is literal production Patch 5, SHA-256 `534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208`. Preserve the previous signed releases and evidence.

The latest user authorization permits the exact event-menu cleanup and requested banners. This is a finite exception to the 205 append-only policy for the named records and 12 PNG members; all unrelated preservation requirements continue.

Only four APK members may differ: the existing typed Android versionCode value 205→206, the existing `PATCH_VERSION` constant 205→206 in `assets/frida_script.js`, `assets/content_delivery.tsv`, and `assets/side_stories/manifest.tsv`. Keep the same package and signer so 206 updates over 205/204/203. All 170 asset files and the member set remain. DEX, native libraries, resources, startup files, party maps/hooks, movies, downloader, cache/resume/callbacks, lifecycle, units and unrelated behavior remain exact 205 bytes. No new runtime helper is introduced.

## Menu records and preserved registry

Move exactly 20 source-confirmed archived story-event books from season 91 to Story Events, season 70, including their exact map/entry descendants. Hide 37 proven permanent Vortex/trial/Chronicle families and one separate greeting preview for later placement. Remove the three explicitly named menu books: Party Test (7299), A New Year's Greeting (7077), and Unit Intro Quest (1000099). Excluding 41 books is a menu change; underlying encounter tables, scene/audio/archive assets and source identities remain retained.

Empty menu seasons 91 and 93 are removed. After cleanup there are 77 Story Event books, 376 Event Battle books and 450 JP Memories books, 1,004 playback books total. Books are menu records, not a count of every event ever released. Revival Parts 1/2 retain their IDs and receive numeric sort orders 1507/1508 so they appear last; physical master row order remains preserved. The real native comparator proof is in `NATIVE_EVENT_MENU_ORDER.json`.

`CLEANUP_PLAN.json` specifies exact old/new fields and record identities. `DEFERRED_UI_RECORDS.json` preserves all 1,760 removed UI records verbatim, including their full keys and parent links. `EVENT71_DECISION_LEDGER.json` records classification decisions for current Event Battles. `INHERITED_PLAYBACK_RELATIONSHIPS.json` preserves pre-existing relationship observations separately. These records are the registry for future sections; do not reconstruct them from titles or screenshot order.

## Banner provenance

The 12 replacement members are the exact current205 icon targets for Lost Reflection, Seaside Daydream, Mystery of the Dollhouse, Shield Maiden/Dream Stage, Baton/Future, World/Canvas, Mirror-Image Princesses, Accompanist/My Heart, Gathering Revisited, the two source5160 Genesis wrappers, and Revival Part1. Keep existing authentic English Genesis7032 and Revival Part 2 unchanged. Party Test's image remains an unused archive member after its menu book is hidden.

`REQUESTED_BANNER_SOURCES.json` and its CSV pin all 15 reviewed book→icon→PNG mappings, existing member bytes/dimensions, admitted originals and rejected candidates. Retained local JP packs supply the exact Gathering5155 and Genesis5160 rerun images. Six genuine original event artworks are publisher-hosted FF Portal images. Lost Reflection and Dollhouse use credited contemporary Gamebiz/Dengeki mirrors: publisher origin is an explicit inference from article context/credit, not publisher hosting. Preserve their article/image URLs and original bytes. Some press/announcement sources contain surrounding date panels; they are distinct from exact CPK banner bytes.

Translate the genuine original artwork through the built-in image tool, preserving characters, background and frame. Revival Part 1 is the explicitly authorized newly created companion cover matching Part2. Generated/translated covers are derivative artwork and must not be called original game bytes. `IMAGE_TOOL_PROMPTS.json`, follow-up records, original source files, raw tool outputs and native encoding receipts must be retained. The user requested Image 2.5; the tool exposes no model selector, so `model_version_verified=false` remains the honest evidence state.

The real native layout uses one per-title PNG plus shared `spd_bn_press.png`; there is no per-title selected-border pair in this path. Retained `_last` images mean last day, not selected borders. `NATIVE_BANNER_BUTTON_PROOF.json` records that static distinction. Final PNGs use the native 640×240 canvas. Visual rendering on the phone remains pending.

## Catalog and publication procedure

The original native eight-field catalog contract stays. Preserve all 1,898 catalog rows and 1,857 side-manifest paths in original order. Change exactly four playback master descriptors and `side_stories/spdungeon9.cpk`; keep the other 1,893 descriptor rows verbatim. Retain each changed path's old205 hash in accepted history. Unknown valid original targets, saves and partial downloads remain authoritative under the unchanged downloader behavior.

1. Finish source plans, derivative banner preparation and exact payload/candidate pins.
2. Qualify the exact signed206 APK against205 with `guard/event_cleanup_guard.py`, its focused regressions, actual206 JVM catalog/cache/partial fixtures and independent raw-deflate transport checks. Reports must bind the final APK and current plans. Static checks are not phone results.
3. Review the final publisher source and run the network-free publication scope fixture. Upload only the three new206 immutable event release files: pack, catalog and manifest. Use the existing repository's beta prerelease and `make_latest=false`.
4. Verify the new pack/APK by full public GET size/hash and first/middle/last ranges. Stage the exact APK under `downloads/beta/releases/event-cleanup-v206-<16-SHA>/` before activation.
5. Publish immutable checksum/release/checklist metadata, update only beta `channels/beta/patch_version.json`, wait for its canonical raw URL to serve exact206 bytes, then publish `/downloads/beta/index.html`. Preserve all seven older APK links. Preserve production Patch5, production page/updaters, main/latest, Vortex and the stable203 asset pointer. No source push or production promotion is authorized here.
6. Retain stage/activation/readback receipts and offer Kev the exact live APK, version/size/SHA and matching phone checklist. Keep results pending until Kev supplies them.

## Retained paths and safe reuse

Runnable work root: `S:/FFBE JP Data Export/build/v206-event-cleanup`. Canonical archive: `S:/FFBE JP Data Export/ffbe_asset_dump/tools/event_cleanup_v206/release206`. Official handoff: `T:/Projects/FFBE Patch/localization-rounds/2026-10-04-event-cleanup-v206`. Canonical documents are under `documents`; the handoff mirrors them under `documents`.

After final freeze, retain source/config/guard files, plans and bounded audit evidence; signed APK; small payload masters/CPK and delivery metadata/new pack; original/generated/native artwork and prompt provenance; registry/deferred records; publication receipts; and phone checkpoint. Exclude signing material, credentials, host fixture caches/classes, disassembly/build intermediates and unrelated large source dumps. Source configs retain explicit local paths as provenance. Future builds require a fresh workspace/output directory and new qualification; do not run historical defaults in place or overwrite retained outputs.

## Evidence limits

See `KNOWN_LIMITS.md` and `PHONE_TEST_CHECKLIST.md`. This release repairs menu placement and the requested artwork. It does not establish full archived server mechanics, all-events coverage, GL combat parity, English completeness, CG completeness, runtime banner rendering, save migration or Android 17/native ELF 16 KB compatibility. Existing source gaps and engine limits continue because runtime/native/movie behavior remains unchanged.
'''
limits='''# APK 206 known limits

Final qualification/publication evidence is pending while this skeleton is prepared. No phone pass is recorded. Keep the exact final checkpoint pending until Kev reports the signed APK hash, device and Android version.

Menu counts are 77 Story Event books, 376 Event Battle books, 450 JP Memories books and 1,004 total playback books. They are menu-book counts. The changes move 20 books, exclude 41 (37 deferred Vortex/challenge families +1 greeting preview +3 named removals), and replace 12 exact PNG members. All 1,760 removed UI rows remain in the deferred registry. Existing underlying assets and encounters are retained; a future section is not yet implemented.

The requested original artwork sources are documented. Eight old title-card cases now have genuine event artwork: six publisher-hosted originals and two credited contemporary press mirrors. Exact old standalone native CPK originals remain missing in several cases. Tool-translated covers and the new Revival Part 1 companion are derivative artwork. Original Genesis 7032 and Revival Part 2 remain unchanged. The requested Image 2.5 model label could not be verified because the tool exposes no selector. Native640×240 images, title legibility, frame/alpha and selected rendering require phone review.

Literal Patch 5/205 runtime limitations remain: some GL-only effects have no JP equivalent; morale uses archived ordinary-battle values; limited-use skills retain individual stock rather than shared pools/refill. Archived source gaps can include incomplete phase/monster/AI/parts records, scenes/English keys and original server-response contracts. Some Japanese dialogue/labels remain. Structural route/resource closure does not prove transitive effects, progression, ranking/rewards, battle/scene replay or every event ever released.

Movies and their networking remain unchanged. The historical 203/204 12/123 movie graph count is not a 206 coverage claim. CG availability, Unit Library/movie playback and optional downloads require phone checks; no new CG completeness claim is made.

Exact DEX/native preservation and ZIP alignment do not prove Android 17 phone runtime or native ELF 16 KB memory-page compatibility. Host cache/resume fixtures and public byte/range verification do not prove physical downloads, saves or save migration. Historical203 had a reported startup crash on Z Fold 8/Android 17 without logs; that does not establish the outcome or cause for 206. No agent installation, device-file reads, battles, save/cache changes, uninstall or clear-data workaround is authorized by this checkpoint.
'''
checklist='''# Kev's APK 206 phone checklist

Publication is pending in this skeleton. Use only the final verified URL/version/size/SHA in `PHONE_TEST_CHECKPOINT.json` and immutable `phone-test-checklist.txt`. Test the exact signed APK on Z Fold 8/Android 17; record that identity with results.

1. Install over the existing app and keep app data. Check saves and settings before playing.
2. Launch normally and let the existing downloader fetch changed event assets. Reopen and confirm completed files are reused; try interrupt/resume if convenient.
3. Open Story Events: RevivalParts 1/2 should be last. The20 moved archived story-event books should appear here with their chapters. Open a representative event and battle/scene.
4. Open Event Battles: Party Test, A New Year's Greeting and Unit Intro Quest should be absent. ArchivedEvent Battles/Greetings sections should be absent; deferred Vortex/challenge content has no new section yet. Check JP Memories and main story remain available.
5. Inspect the requested banners for correct title/art, English text, full frame, proportions, transparency and press behavior. Original Genesis 7032 and Revival Part 2 should be unchanged. Check a known available movie and original content if convenient.
6. Reopen and recheck saves/settings. Report pass/fail, exact build/SHA, affectedbook/scene, device/Android version and any error text or optional crash log.

Keep phone/runtime/gameplay/save status pending until these results arrive. Do not uninstall or clear data. Production promotion is a separate decision.
'''
readme='''# Event cleanup206 release archive

This new archive records the exact205-based menu cleanup and requested original-artwork repair. Final signed qualification, verified publication and exact APK identity are pending while the handoff skeleton is prepared. Historical203–205 releases remain untouched.

Read `documents/EVENT_CLEANUP_RELEASE_WORKFLOW.md`, `documents/KNOWN_LIMITS.md` and `documents/PHONE_TEST_CHECKLIST.md`. Final evidence belongs in `release206` in the canonical S archive, and `dist`, `delivery_metadata`, `artwork`, `evidence` and checkpoint in the T handoff. The final handoff receipt will hash every retained file. Phone results and requested Image 2.5 model verification remain pending/unverified.
'''
docs={'EVENT_CLEANUP_RELEASE_WORKFLOW.md':workflow,'KNOWN_LIMITS.md':limits,'PHONE_TEST_CHECKLIST.md':checklist}
receipts=[]
for base in (CANON,HANDOFF):
 receipts.append(put_new(base/'README.md',readme))
 for name,text in docs.items():receipts.append(put_new(base/'documents'/name,text))
for d in ('source','guard','audit','publication','staged_build','payload','artwork'):(CANON/'release206'/d).mkdir(parents=True,exist_ok=True)
for d in ('dist','delivery_metadata','artwork','evidence/source','evidence/guard','evidence/audit','evidence/publication','evidence/staged_build'):(HANDOFF/d).mkdir(parents=True,exist_ok=True)
pending={'schema':'ffbe-v206-handoff-pending-v1','work_root':str(ROOT),'canonical_release_root':str(CANON/'release206'),'handoff_root':str(HANDOFF),'final_copy_complete':False,'signed_qualification_copied':False,'publication_receipts_copied':False,'physical_phone_test':'pending','image_model_version_verified':False,'history_203_204_205_untouched':True,'remaining':'Wait for root final freeze, exact signed qualification and publication receipts; copy bounded immutable evidence then issue full-file copy receipt.'}
blob=json.dumps(pending,indent=2)+'\n'
receipts.append(put_new(CANON/'release206/HANDOFF_PENDING.json',blob));receipts.append(put_new(HANDOFF/'HANDOFF_PENDING.json',blob))
report={'schema':'ffbe-v206-handoff-skeleton-v1','passed':True,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_documents':receipts,'final_copy_complete':False,'no_historical_release_writes':True,'no_remote_or_device_actions':True}
out=ROOT/'audit/HANDOFF_SKELETON.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'documents':len(receipts),'canonical':str(CANON),'handoff':str(HANDOFF),'report':str(out)},ensure_ascii=False))
