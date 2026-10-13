import fs from 'node:fs';
import path from 'node:path';
import {ROOT,DIR,PREVIOUS,STABLE203_SHA,qualifiedInputs,read,hash,save,assert,pin} from './publication_inputs.mjs';
assert(process.argv.length===2,'No configurable destination');
const {build,signed,download,cleanup,banners,protection}=qualifiedInputs();
const previousReceipt=read(PREVIOUS+'/publication/activation-receipt.json');
const previous=fs.readFileSync(PREVIOUS+'/publication/site/index.html');
assert(previousReceipt.success&&previousReceipt.versionCode===205&&previousReceipt.sha256==='e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'&&hash(previous)===previousReceipt.page.sha256,'Previous published205 page pin differs');
const filename=path.basename(build.apk);assert(/^[A-Za-z0-9._-]+v206\.apk$/.test(filename),'Unexpected206 APK filename');
const prefix=`downloads/beta/releases/event-cleanup-v206-${build.sha256.slice(0,16)}/`;
const url='https://ffbe.luminest.io/'+prefix+filename;
const manifest=download.files.find(f=>f.role==='manifest');assert(manifest,'Immutable event manifest missing');
const assetURL=`https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/${download.release_tag}/${manifest.name}`;
const checklistURL='https://ffbe.luminest.io/'+prefix+'phone-test-checklist.txt';
const after=cleanup.category_book_counts.after;
assert(after['70']===77&&after['71']===376&&after['92']===450&&cleanup.excluded_book_ids.length===41&&cleanup.moved_book_ids.length===20,'Reviewed cleanup totals differ');
const artworkCount=new Set(banners.members.map(m=>m.source_key)).size;
assert(artworkCount===11&&banners.members.length===12,'Qualified banner replacement counts differ');
fs.mkdirSync(DIR+'/site',{recursive:true});
let page=previous.toString('utf8');
page=page.replace(/<meta name="description" content="[^"]*">/,'<meta name="description" content="FFBE Memorial Android beta build 206: event menu cleanup and restored event banners. Story Event Revival Parts 1 and 2 appear last. Phone testing is pending.">');
assert(page.includes('<h1>Try build 205</h1>')||page.includes('<h1>Try build 205</h1>'),'Previous205 heading absent');
page=page.replace(/<h1>Try build ?205<\/h1>/,'<h1>Try build 206</h1>');
const start=page.indexOf('<section class="card" aria-labelledby="events205">');assert(start>=0,'Previous205 card absent');
const mb=(build.bytes/1000000).toFixed(1);
const card=`<section class="card" aria-labelledby="events206"><h2 id="events206">Build 206 &mdash; Event menu cleanup</h2>
<div class="meta">Android &middot; October 4, 2026 &middot; ${mb} MB APK &middot; Experimental &middot; Version 206</div>
<a class="button" href="${url}" download>Download Build 206 APK &mdash; ${mb} MB</a>
<p class="details">Story Event Revival Parts 1 and 2 now appear at the bottom. Archived story-event battles move into <strong>Story Events</strong>. Party Test, A New Year&rsquo;s Greeting and Unit Intro Quest are removed from the menus.</p>
<p class="details">Permanent Vortex and challenge families, plus the separate greeting preview, are kept for a later section. Requested event banners are restored or translated. There are ${after['70']} Story Event books and ${after['71']} Event Battle books.</p>
<p class="details">This continues build 205 with its existing startup assets, native downloader, units and movie behavior. Missing event assets download from <strong>GitHub</strong>; existing assets and underlying encounters are retained.</p>
<p class="details"><strong>Phone testing is pending.</strong> This signed APK passed menu-data, APK and downloader checks. Install over your existing app, keep app data, and check menus, saves and representative events on the Z Fold 8 / Android 17.</p>
<p class="details">Archived source gaps and some Japanese dialogue remain. Event gameplay, banner rendering, saves and Android 17 compatibility require phone testing.</p>
<p class="details"><a href="https://ffbe.luminest.io/${prefix}checksums.txt">APK checksum</a> &middot; <a href="https://ffbe.luminest.io/${prefix}release.json">Release details</a> &middot; <a href="${assetURL}">Event assets manifest</a> &middot; <a href="${checklistURL}">Phone-test checklist</a></p>
<p class="checksum">SHA-256: ${build.sha256}</p></section>
<h2>Previous build 205</h2>
`;
page=page.slice(0,start)+card+page.slice(start);
const links=[...previous.toString('utf8').matchAll(/href="([^"]+\.apk)"/g)].map(m=>m[1]);
assert(links.length>=7&&links.every(link=>page.includes('href="'+link+'"'))&&links.includes(previousReceipt.apk_url),'Prior beta APK link removed');
fs.writeFileSync(DIR+'/site/previous-index.html',previous);
fs.writeFileSync(DIR+'/site/index.html',page);
const known_limits=['Phone navigation, banner rendering, gameplay and Android 17 runtime are pending for this exact APK.','Existing saves and settings must be checked on the phone; save migration has not been verified.','Archived source gaps and some Japanese dialogue remain; this does not claim every archived server mechanic has been reconstructed.','Native ELF compatibility with 16 KB memory pages remains unverified; the original native libraries are unchanged.'];
const release={schema:'ffbe-event-menu-cleanup-release-v1',channel:'beta',versionCode:206,versionName:build.versionName,package:build.package,signer_sha256:build.signer_sha256,source_APK:'Published build 205 with literal production Patch 5 foundation',source_APK_sha256:build.baseline_apk_sha256,foundation_patch5_sha256:build.foundation_patch5_sha256,apk:{filename,url,bytes:build.bytes,sha256:build.sha256},scope:'Existing event menu cleanup and requested event banners only; no content imports or unrelated runtime changes.',event_menu_cleanup:{archived_story_books_moved:20,excluded_menu_books:41,named_removed_books:['Party Test',"A New Year's Greeting",'Unit Intro Quest'],deferred_vortex_challenge_books:37,deferred_greeting_books:1,revival_parts_last:true,story_event_books:77,event_battle_books:376,JP_memories_books:450,total_playback_books:1004,underlying_encounters_and_assets_retained:true},preserved:{startup_assets:true,native_libraries:true,lifecycle:true,downloader:true,units_and_movies:true,classes_dex:true,APK_asset_file_count:170,catalog_paths:1898,side_manifest_paths:1857},delivery:{event_assets:'Immutable GitHub releases through the existing native downloader.',event_catalog_sha256:download.content_catalog_sha256,event_catalog_bytes:download.content_catalog_bytes,bundled_side_manifest_sha256:download.side_manifest_sha256,event_manifest_url:assetURL,event_data_release:download.release_tag,changed_asset_files:5,unchanged_catalog_descriptors:1893,new_download_paths:0,stable203assetPointerChanged:false},local_qualification:{signed_apk_diff:true,independent_cleanup_data_checks:true,native_downloader_fixtures:true,independent_transport_checks:true,qualification_apk_sha256:signed.apk_sha256},phone_test:{tester:'Kev',status:'pending',device:'Z Fold 8',Android_version:'17',tied_apk_sha256:build.sha256,checklist_url:checklistURL,runtime_verified:false,save_migration_verified:false},known_limits,previous_APK_downloads:links};
release.banner_changes={unique_artworks:artworkCount,archive_members:banners.members.length,original_Genesis_book7032_preserved:true,Revival_Part1_companion_created:true};
save(DIR+'/site/release.json',release);
fs.writeFileSync(DIR+'/site/checksums.txt',build.sha256+'  '+filename+'\n');
fs.writeFileSync(DIR+'/site/phone-test-checklist.txt',`FFBE Memorial build 206 — Event menu cleanup\n\nVersion: Android versionCode 206 / versionName ${build.versionName}\nPackage: ${build.package}\nAPK: ${url}\nSize: ${build.bytes.toLocaleString('en-US')} bytes\nSHA-256: ${build.sha256}\n\nPhone target: Z Fold 8, Android 17. Testing is pending for this exact signed APK. Startup, native libraries, downloader, units, movies and lifecycle remain as in build 205.\n\n1. Install over your existing app and keep app data. Check saves and settings.\n2. Launch normally. Let the original download screen fetch the updated event assets from GitHub. Reopen and confirm completed files are reused. Interrupt/resume one download if convenient.\n3. Open Story Events: Revival Parts 1/2 should be last; archived story-event battles should appear here. Check their chapters and try a representative battle.\n4. Open Event Battles: Party Test, A New Year's Greeting and Unit Intro Quest should be absent. Archived Event Battles and Greetings/Introductions sections should be absent. Deferred permanent Vortex/challenge content has no new section yet. JP Memories and main story should remain as before.\n5. Inspect the requested event banners and report blank, incorrect, distorted or Japanese text where a translated banner was expected. Check a known available movie and original content if convenient.\n6. Reopen and recheck saves/settings. Report pass/fail, affected event, phone/Android version and any error text.\n\nKnown limits:\n${known_limits.map(v=>'- '+v).join('\n')}\n`);
save(ROOT+'/PHONE_TEST_CHECKPOINT.json',{schema:'ffbe-phone-test-checkpoint-v1',target_versionCode:206,versionCode:206,apk_url:url,apk_bytes:build.bytes,apk_sha256:build.sha256,package:build.package,physical_phone_test:'pending',runtime_verified:false,save_migration_verified:false,device:'Z Fold 8',Android_version:'17',known_limits,checklist_url:checklistURL,phone_results:null});
const files={};for(const name of ['checksums.txt','release.json','phone-test-checklist.txt'])files[name]=pin(DIR+'/site/'+name);
save(DIR+'/site/page-plan.json',{previous_sha256:hash(previous),previous_versionCode:205,new_sha256:hash(Buffer.from(page)),previous_APK_downloads:links,files});
save(DIR+'/plan.json',{versionCode:206,apk:build.apk,filename,bytes:build.bytes,sha256:build.sha256,prefix,apk_url:url,download_plan_sha256:pin(ROOT+'/asset_publication/DOWNLOAD_PLAN.json').sha256,previous_updater_blob_sha:previousReceipt.pointer.blob_sha,previous_updater_sha256:previousReceipt.pointer.sha256,production_guard:protection,asset_release:download.release_tag,event_catalog_sha256:download.content_catalog_sha256,event_manifest_url:assetURL,stable203assetPointerSHA:STABLE203_SHA});
console.log(JSON.stringify({ready:true,apk_url:url,bytes:build.bytes,sha256:build.sha256,previous_APK_links_preserved:links.length,phone_test:'pending'}));
