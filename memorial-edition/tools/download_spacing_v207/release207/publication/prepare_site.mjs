import fs from 'node:fs';
import path from 'node:path';
import {ROOT,DIR,FROZEN,BASELINE206_SHA,STABLE203_SHA,qualifiedInputs,read,hash,save,assert,pin} from './publication_inputs.mjs';
assert(process.argv.length===2,'No configurable destination');
const inputs=qualifiedInputs(),{build,signed,download,previousReceipt,previousPlan,protection}=inputs;
const previous=fs.readFileSync(FROZEN+'/index.html'),oldRelease=read(FROZEN+'/release.json');
const filename=path.basename(build.apk);assert(/^[A-Za-z0-9._-]+v207\.apk$/.test(filename),'Unexpected207 APK filename');
const prefix=`downloads/beta/releases/download-spacing-v207-${build.sha256.slice(0,16)}/`,url='https://ffbe.luminest.io/'+prefix+filename,checklistURL='https://ffbe.luminest.io/'+prefix+'phone-test-checklist.txt';
const assetURL=previousReceipt.event_manifest_url;
assert(assetURL===previousPlan.event_manifest_url&&oldRelease.delivery.event_manifest_url===assetURL,'Existing206 event manifest URL differs');
fs.mkdirSync(DIR+'/site',{recursive:true});
let page=previous.toString('utf8');
page=page.replace(/<meta name="description" content="[^"]*">/,'<meta name="description" content="FFBE Memorial Android beta build 207: removes the extra space after the wide comma on the download screen. Build 206 event content and assets are unchanged. Phone testing is pending.">');
assert(page.includes('<h1>Try build 206</h1>'),'Published206 heading absent');
page=page.replace('<h1>Try build 206</h1>','<h1>Try build 207</h1>');
const start=page.indexOf('<section class="card" aria-labelledby="events206">');assert(start>=0,'Published206 download card absent');
const mb=(build.bytes/1000000).toFixed(1);
const card=`<section class="card" aria-labelledby="spacing207"><h2 id="spacing207">Build 207 &mdash; Download screen spacing</h2>
<div class="meta">Android &middot; October 4, 2026 &middot; ${mb} MB APK &middot; Experimental &middot; Version 207</div>
<a class="button" href="${url}" download>Download Build 207 APK &mdash; ${mb} MB</a>
<p class="details">Removes the extra space after the wide comma on the game&rsquo;s download screen. The event menus, banners, assets and downloader behavior remain as in build 206.</p>
<p class="details"><strong>Phone testing is pending.</strong> This signed APK passed the spacing-only APK check. Install over your existing app, keep app data, and check the download text and saves.</p>
<p class="details"><a href="https://ffbe.luminest.io/${prefix}checksums.txt">APK checksum</a> &middot; <a href="https://ffbe.luminest.io/${prefix}release.json">Release details</a> &middot; <a href="${assetURL}">Existing event assets manifest</a> &middot; <a href="${checklistURL}">Phone-test checklist</a></p>
<p class="checksum">SHA-256: ${build.sha256}</p></section>
<h2>Previous build 206</h2>
`;
page=page.slice(0,start)+card+page.slice(start);
const links=[...previous.toString('utf8').matchAll(/href="([^"]+\.apk)"/g)].map(m=>m[1]);
assert(links.length===8&&links.every(link=>page.includes('href="'+link+'"'))&&links.includes(previousReceipt.apk_url),'A previous beta APK link was removed');
fs.writeFileSync(DIR+'/site/previous-index.html',previous);fs.writeFileSync(DIR+'/site/index.html',page);
const known_limits=oldRelease.known_limits;
const release={schema:'ffbe-download-spacing-release-v1',channel:'beta',versionCode:207,versionName:build.versionName,package:build.package,signer_sha256:build.signer_sha256,source_APK:'Published build 206',source_APK_sha256:BASELINE206_SHA,foundation_patch5_sha256:oldRelease.foundation_patch5_sha256,apk:{filename,url,bytes:build.bytes,sha256:build.sha256},scope:'Remove the extra space after the wide comma on the game download screen only.',changed_APK_members:['AndroidManifest.xml','assets/frida_script.js'],signing_metadata_regenerated:true,spacing_fix:{native_download_screen_only:true,exact_finite_script_delta_verified:true,patch_version:207},preserved:{...oldRelease.preserved,event_menus:true,event_banners:true,all_206_game_content_assets:true,non_script_assets_unchanged:true,non_script_asset_file_count:169,all_206_download_descriptors:true},delivery:{...oldRelease.delivery,event_data_version:206,event_assets_reused_from206:true,new_packs:0,new_asset_uploads:0,changed_asset_files:0,unchanged_catalog_descriptors:1898,new_download_paths:0},inherited_event_menu_cleanup:oldRelease.event_menu_cleanup,inherited_banner_changes:oldRelease.banner_changes,local_qualification:{signed_apk_diff:true,expected_script_delta:true,unchanged_members:true,qualification_apk_sha256:signed.apk_sha256},phone_test:{tester:'Kev',status:'pending',device:'Z Fold 8',Android_version:'17',tied_apk_sha256:build.sha256,checklist_url:checklistURL,runtime_verified:false,save_migration_verified:false},known_limits,previous_APK_downloads:links};
save(DIR+'/site/release.json',release);fs.writeFileSync(DIR+'/site/checksums.txt',build.sha256+'  '+filename+'\n');
fs.writeFileSync(DIR+'/site/phone-test-checklist.txt',`FFBE Memorial build207 — Download screen spacing\n\nVersion: Android versionCode207 / versionName ${build.versionName}\nPackage: ${build.package}\nAPK: ${url}\nSize: ${build.bytes.toLocaleString('en-US')} bytes\nSHA-256: ${build.sha256}\n\nPhone target: Z Fold 8, Android17. Runtime and saves remain unverified for this exact APK.\n\n1. Install over the existing app and keep app data. Check saves and settings.\n2. Observe the native download screen while a download is pending: the extra space immediately after the wide comma should be gone. Other text, progress and download behavior should remain unchanged. Report the exact affected line if the spacing persists.\n3. Reopen and confirm saves, settings and event menus remain as in build206. Existing event assets should be reused. This release adds no asset packs.\n4. Report pass/fail, device/Android version and any error text.\n\nInherited limits:\n${known_limits.map(v=>'- '+v).join('\n')}\n`);
save(ROOT+'/PHONE_TEST_CHECKPOINT.json',{schema:'ffbe-phone-test-checkpoint-v1',target_versionCode:207,versionCode:207,apk_url:url,apk_bytes:build.bytes,apk_sha256:build.sha256,package:build.package,physical_phone_test:'pending',runtime_verified:false,save_migration_verified:false,device:'Z Fold 8',Android_version:'17',known_limits,checklist_url:checklistURL,phone_results:null});
const files={};for(const name of ['checksums.txt','release.json','phone-test-checklist.txt'])files[name]=pin(DIR+'/site/'+name);
save(DIR+'/site/page-plan.json',{previous_sha256:hash(previous),previous_versionCode:206,new_sha256:hash(Buffer.from(page)),previous_APK_downloads:links,files});
save(DIR+'/plan.json',{versionCode:207,asset_version:206,apk:build.apk,filename,bytes:build.bytes,sha256:build.sha256,prefix,apk_url:url,spacing_plan_sha256:signed.spacing_plan_sha256,previous_updater_blob_sha:previousReceipt.pointer.blob_sha,previous_updater_sha256:previousReceipt.pointer.sha256,production_guard:protection,asset_release:download.release_tag,event_catalog_sha256:download.content_catalog_sha256,side_manifest_sha256:download.side_manifest_sha256,event_manifest_url:assetURL,stable203assetPointerSHA:STABLE203_SHA,new_asset_uploads:0});
console.log(JSON.stringify({ready:true,apk_url:url,bytes:build.bytes,sha256:build.sha256,previous_APK_links_preserved:links.length,event_assets_reused_from206:true,phone_test:'pending'}));
