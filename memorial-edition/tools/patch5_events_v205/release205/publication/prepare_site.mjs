import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const ROOT='S:/FFBE JP Data Export/build/v205-patch5-events';
const OLD='S:/FFBE JP Data Export/build/v204-startup-fix';
const DIR=ROOT+'/publication';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
const assert=(v,m)=>{if(!v)throw Error(m);};
assert(process.argv.length===2,'No configurable destination');
const build=read(ROOT+'/staged_build/EVENT_ONLY_APK_BUILD.json');
const qualification=read(ROOT+'/staged_build/SIGNED_EVENT_QUALIFICATION.json');
const payload=read(ROOT+'/audit/INDEPENDENT_PAYLOAD_QUALIFICATION.json');
const download=read(ROOT+'/asset_publication/DOWNLOAD_PLAN.json');
const host=read(ROOT+'/audit/ACTUAL205_CATALOG_HOST_ADMISSION.json');
assert(qualification.passed&&qualification.apk_sha256===build.sha256&&build.versionCode===205&&payload.passed&&download.passed&&host.passed&&host.catalog_sha256===download.content_catalog_sha256,'Exact205 qualification required');
const previousReceipt=read(OLD+'/publication/activation-receipt.json');
const previous=fs.readFileSync(OLD+'/publication/site/index.html');
assert(hash(previous)===previousReceipt.page.sha256,'Previous beta page pin differs');
const filename=path.basename(build.apk),prefix=`downloads/beta/releases/patch5-events-v205-${build.sha256.slice(0,16)}/`;
const url='https://ffbe.luminest.io/'+prefix+filename;
const assetURL=`https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/${download.release_tag}/event-assets-${download.catalog_identity_sha256.slice(0,16)}.json`;
const checklistURL='https://ffbe.luminest.io/'+prefix+'phone-test-checklist.txt';
fs.mkdirSync(DIR+'/site',{recursive:true});
let page=previous.toString('utf8');
page=page.replace(/<meta name="description" content="[^"]*">/,'<meta name="description" content="FFBE Memorial Android beta build 205: production Patch 5 plus missing events. Original startup assets are bundled; required additional event assets download from GitHub. Phone testing is pending.">');
page=page.replace('<h1>Try build 204</h1>','<h1>Try build 205</h1>');
const start=page.indexOf('<section class="card" aria-labelledby="startup204">');
assert(start>=0,'Previous204 card absent');
page=page.replace('Build 204 &mdash; Corrected beta download','Build 204 &mdash; Previous beta');
page=page.replace('Use corrected build 204 above.','Use the current beta download above.');
const mb=(build.bytes/1000000).toFixed(1);
const card=`<section class="card" aria-labelledby="events205"><h2 id="events205">Build 205 &mdash; Patch 5 with missing events</h2>
<div class="meta">Android &middot; October 4, 2026 &middot; ${mb} MB APK &middot; Experimental &middot; Version 205</div>
<a class="button" href="${url}" download>Download Build 205 APK &mdash; ${mb} MB</a>
<p class="details">Production <strong>Patch 5</strong> with <strong>863 additional event books</strong> and their required assets. Existing Patch 5 event records, startup files, units and movie behavior are preserved.</p>
<p class="details">The original startup assets remain inside the APK. Missing event assets download from <strong>GitHub through Patch 5&rsquo;s native downloader</strong>, with its existing cache reuse and interrupted-download support.</p>
<p class="details"><strong>Phone testing is pending.</strong> The finished signed APK passed checks against Patch 5, event data checks and downloader fixtures. Please test first launch and the added events on the Z Fold 8 / Android 17.</p>
<p class="details">Same package and signer as Patch 5: <code>com.square_enix.ffbejpn</code>. Version 205 can install over 203 or 204. Keep app data and check existing saves and settings.</p>
<p class="details">Archived source gaps, some Japanese dialogue and fallback banners remain. Event gameplay, saves and Android 17 compatibility require phone testing.</p>
<p class="details"><a href="https://ffbe.luminest.io/${prefix}checksums.txt">APK checksum</a> &middot; <a href="https://ffbe.luminest.io/${prefix}release.json">Release details</a> &middot; <a href="${assetURL}">Event assets manifest</a> &middot; <a href="${checklistURL}">Phone-test checklist</a></p>
<p class="checksum">SHA-256: ${build.sha256}</p></section>
<h2>Previous build 204</h2>
`;
page=page.slice(0,start)+card+page.slice(start);
const links=[...previous.toString('utf8').matchAll(/href="([^"]+\.apk)"/g)].map(m=>m[1]);
assert(links.every(link=>page.includes('href="'+link+'"')),'Prior APK link removed');
fs.writeFileSync(DIR+'/site/index.html',page);
const known_limits=['Physical-phone startup and Android 17 runtime are pending for this exact APK.','Gameplay and save migration have not been tested on a device.','Archived source gaps, fallback event banners and some Japanese dialogue remain; this does not claim every archived server mechanic has been reconstructed.','Native ELF compatibility with 16 KB memory pages remains unverified; original Patch 5 native libraries are unchanged.'];
const release={schema:'ffbe-patch5-event-only-release-v1',channel:'beta',versionCode:205,versionName:build.versionName,package:build.package,signer_sha256:build.signer_sha256,source_APK:'Literal production Patch 5',source_APK_sha256:build.baseline_apk_sha256,apk:{filename,url,bytes:build.bytes,sha256:build.sha256},scope:'Patch 5 plus missing event records and required event assets only.',event_additions:{books:863,maps:1850,entries:7999,seasons:3,required_event_files:500,new_download_paths:487,modified_existing_event_descriptors:13},preserved:{startup_assets:true,all_original_event_records:true,native_libraries:true,original_lifecycle:true,original_downloader:true,units_and_movies:true,APK_asset_file_count:170},delivery:{additional_event_assets:'Immutable GitHub release downloads through original Patch 5 native downloader.',event_catalog_sha256:download.content_catalog_sha256,event_manifest_url:assetURL,event_data_release:download.release_tag,reused_event_file_count:download.reused_event_files.length,new_pack_file_count:download.new_pack_files.length,stable203assetPointerChanged:false},local_qualification:{signed_apk_diff:true,independent_event_source_checks:true,native_downloader_fixtures:true,qualification_apk_sha256:qualification.apk_sha256},phone_test:{tester:'Kev',status:'pending',device:'Z Fold 8',Android_version:'17',tied_apk_sha256:build.sha256,checklist_url:checklistURL,runtime_verified:false,save_migration_verified:false},known_limits,previous_APK_downloads:links};
save(DIR+'/site/release.json',release);
fs.writeFileSync(DIR+'/site/checksums.txt',build.sha256+'  '+filename+'\n');
fs.writeFileSync(DIR+'/site/phone-test-checklist.txt',`FFBE Memorial build 205 — Patch 5 plus missing events\n\nVersion: Android versionCode 205 / versionName ${build.versionName}\nPackage: ${build.package}\nAPK: ${url}\nSize: ${build.bytes.toLocaleString('en-US')} bytes\nSHA-256: ${build.sha256}\n\nPhone target: Z Fold 8, Android 17. Testing is pending for this exact signed APK. Production Patch 5 is the literal baseline. Its startup assets, original event records, native downloader, units and movie behavior are retained. Only missing event data, required event downloads and support for the added scene paths were added.\n\n1. Install over the existing FFBE app. Keep app data; check saves and settings.\n2. Launch and check that the game opens using its packaged startup files. Report any crash, error and last screen shown.\n3. Let the normal download screen fetch missing event assets from GitHub. Close and reopen; check completed files are reused. Interrupt/resume a download once if convenient.\n4. Open JP Memories, Archived Event Battles and Normal Events. Check the added events and try representative quests if desired. Report missing entries, duplicates, blank images or quest-start failures.\n5. Check existing Patch 5 content, units and a known available movie if desired, then reopen and recheck saves/settings.\n6. Report pass/fail, phone/Android version, the affected event and any error text.\n\nKnown limits:\n${known_limits.map(v=>'- '+v).join('\n')}\n`);
save(ROOT+'/PHONE_TEST_CHECKPOINT.json',{schema:'ffbe-phone-test-checkpoint-v1',target_versionCode:205,versionCode:205,apk_url:url,apk_bytes:build.bytes,apk_sha256:build.sha256,package:build.package,physical_phone_test:'pending',runtime_verified:false,save_migration_verified:false,device:'Z Fold 8',Android_version:'17',known_limits,checklist_url:checklistURL,phone_results:null});
const files={};for(const name of ['checksums.txt','release.json','phone-test-checklist.txt']){const b=fs.readFileSync(DIR+'/site/'+name);files[name]={bytes:b.length,sha256:hash(b)};}
save(DIR+'/site/page-plan.json',{previous_sha256:hash(previous),new_sha256:hash(Buffer.from(page)),files});
save(DIR+'/plan.json',{versionCode:205,apk:build.apk,filename,bytes:build.bytes,sha256:build.sha256,prefix,apk_url:url,download_plan_sha256:hash(fs.readFileSync(ROOT+'/asset_publication/DOWNLOAD_PLAN.json')),previous_updater_blob_sha:previousReceipt.pointer.blob_sha,previous_updater_sha256:previousReceipt.pointer.sha256,production_guard:read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard,asset_release:download.release_tag,event_catalog_sha256:download.content_catalog_sha256,event_manifest_url:assetURL,stable203assetPointerSHA:'b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8'});
console.log(JSON.stringify({ready:true,apk_url:url,bytes:build.bytes,sha256:build.sha256}));
