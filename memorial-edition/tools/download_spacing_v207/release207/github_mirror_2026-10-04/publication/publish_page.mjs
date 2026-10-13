import fs from 'node:fs';
import {put,get,sha,verify} from 'file:///T:/Projects/FFBE%20Patch/localization-rounds/2026-09-25-download-recovery/scripts/hosting.mjs';
// The established helper is used only for authenticated production reads.
import {githubExistingAuth,REPOSITORY} from 'file:///S:/FFBE%20JP%20Data%20Export/build/v207-download-spacing/publication/scripts/github_existing_auth.mjs';
import {ROOT,DIR,APK_SHA,APK_BYTES,GITHUB_URL,LUMINEST_URL,STABLE203_SHA,preparedPage,verifiedUpload,hash,pin,read,save,assert} from './page_inputs.mjs';
assert(process.argv.length===2,'Only the fixed beta page can be published');
const delta=preparedPage(),upload=verifiedUpload(),review=read(ROOT+'/audit/LOCAL_PAGE_REVIEW.json');
assert(review.passed&&review.apk_sha256===APK_SHA&&review.prepared_page.sha256===hash(delta.page)&&review.all_other_page_bytes_preserved===true,'Exact reviewed mirror page required');
for(const [name,expected] of Object.entries(review.source_pins)){const actual=pin(DIR+'/'+name);assert(actual.bytes===expected.bytes&&actual.sha256===expected.sha256,'Reviewed page publisher source changed');}
async function protectedFiles(){
 const results=await Promise.allSettled(delta.protection.public_files.map(async f=>{const b=await get(f.url);assert(b.length===f.bytes&&sha(b)===f.sha256,'Protected public file changed');return {url:f.url,bytes:b.length,sha256:sha(b),unchanged:true};}));
 return results.map(r=>{if(r.status==='rejected')throw r.reason;return r.value;});
}
async function stablePointer(){const b=await get(`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/manifest.json`);assert(sha(b)===STABLE203_SHA,'Stable203 asset pointer changed');return {sha256:sha(b),unchanged:true};}
async function betaUpdater(){
 const url=`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/patch_version.json`,b=await get(url),value=JSON.parse(b);
 assert(value.channel==='beta'&&value.package==='com.square_enix.ffbejpn'&&value.version===207&&value.versionCode===207&&value.asset_version===206&&value.bytes===APK_BYTES&&value.sha256===APK_SHA&&value.apk_url===GITHUB_URL&&value.url===GITHUB_URL&&value.apk_update_enabled===true&&Array.isArray(value.changelog)&&value.changelog.length===0,'Root must verify and activate both GitHub207 beta updater URLs first');
 return {url,sha256:sha(b),bytes:b.length,versionCode:207,apk_url:value.apk_url,mirrored_exact_apk:true,asset_version:206,changelog:[]};
}
const current=await get('https://ffbe.luminest.io/downloads/beta/');assert(sha(current)===hash(delta.before)||current.equals(delta.page),'Beta page changed concurrently');
const gh=await githubExistingAuth();
async function repositoryGuard(){const main=await gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`),latest=await gh.request(`/repos/${REPOSITORY}/releases/latest`);assert(main.object.sha===delta.protection.main_sha&&latest.id===delta.protection.latest_release_id&&latest.tag_name===delta.protection.latest_tag,'Production main/latest changed');return {main_sha:main.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name};}
const protected_before=await protectedFiles(),stable_before=await stablePointer(),repository_before=await repositoryGuard(),updater_before=await betaUpdater();
const result=current.equals(delta.page)?await verify('https://ffbe.luminest.io/downloads/beta/',delta.page):await put('ffbe.luminest.io','downloads/beta/index.html',delta.page,{overwrite:true,expectedPrevious:hash(delta.before)});
assert((await get('https://ffbe.luminest.io/downloads/beta/')).equals(delta.page),'GitHub primary page readback differs');
save(DIR+'/page-activation-receipt.json',{schema:'ffbe-207-github-primary-page-activation-v1',success:true,versionCode:207,apk_bytes:APK_BYTES,apk_sha256:APK_SHA,github_primary_url:GITHUB_URL,luminest_mirror_url:LUMINEST_URL,github_verified_upload_receipt_sha256:pin(DIR+'/github-apk-receipt.json').sha256,GitHub_release_id:upload.release_id,page:result,local_page_review_sha256:pin(ROOT+'/audit/LOCAL_PAGE_REVIEW.json').sha256,all_existing_content_and_links_preserved:true,protected_before,protected_after:await protectedFiles(),stable_before,stable_after:await stablePointer(),repository_before,production_after:await repositoryGuard(),updater_before,updater_after:await betaUpdater(),APK_changed:false,assets_changed:false,new_asset_uploads:0,phone_test_pending:true,completed_at:new Date().toISOString()});
console.log(JSON.stringify({success:true,github_primary:GITHUB_URL,luminest_mirror:LUMINEST_URL,beta_page:'https://ffbe.luminest.io/downloads/beta/',APK_changed:false,assets_changed:false}));
