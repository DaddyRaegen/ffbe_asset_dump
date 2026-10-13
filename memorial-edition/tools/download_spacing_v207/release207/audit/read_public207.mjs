// Independent readback after confirmed activation. All remote requests are GET.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {githubExistingAuth,REPOSITORY} from '../publication/scripts/github_existing_auth.mjs';

const ROOT='S:/FFBE JP Data Export/build/v207-download-spacing';
const PREVIOUS='S:/FFBE JP Data Export/build/v206-event-cleanup';
const EXPECTED_APK_SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e';
const BASELINE_APK_SHA='345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d';
const CATALOG_SHA='963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a';
const SIDE_SHA='0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14';
const STABLE203_SHA='b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8';
const PRIOR206_PUBLIC_SHA='1c71f5b2c58740bc0c1f2cec35dc5881fceceff0c0b875e380830b771d42697a';
const REUSED_RELEASE='beta-content-v206-ac96f646eaa91996';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const require=(value,message)=>{if(!value)throw Error(message);};
const report={schema:'ffbe-public207-independent-review-v1',passed:false,network_requested:true,
  remote_mutations:false,device_actions:false,runtime_verified:false,requests:[]};
require(process.argv.length===3&&process.argv[2]==='--verify-published','Explicit --verify-published required after activation.');

async function get(url,range=null){
 const headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'};
 if(range)headers.Range=`bytes=${range.start}-${range.end}`;
 const response=await fetch(url,{method:'GET',headers,cache:'no-store',signal:AbortSignal.timeout(180000)});
 require(response.status===(range?206:200),`Public GET HTTP ${response.status}: ${url}`);
 if(range)require(response.headers.get('content-range')===`bytes ${range.start}-${range.end}/${range.total}`,'Exact range header differs');
 const bytes=Buffer.from(await response.arrayBuffer());
 if(range)require(bytes.length===range.end-range.start+1,'Exact range byte length differs');
 report.requests.push({url,status:response.status,bytes:bytes.length,...(range?{range}:{})});
 return bytes;
}
async function settled(promises){
 const results=await Promise.allSettled(promises);
 const rejected=results.find(result=>result.status==='rejected');
 if(rejected)throw rejected.reason;
 return results.map(result=>result.value);
}

async function main(){
 const activation=read(ROOT+'/publication/activation-receipt.json'),plan=read(ROOT+'/publication/plan.json');
 const build=read(ROOT+'/staged_build/DOWNLOAD_SPACING_APK_BUILD.json'),signed=read(ROOT+'/staged_build/SIGNED_SPACING_QUALIFICATION.json');
 require(activation.success&&activation.versionCode===207&&activation.asset_version===206&&activation.sha256===EXPECTED_APK_SHA&&activation.bytes===145206221,'Exact207 activation not confirmed');
 require(plan.versionCode===207&&plan.asset_version===206&&plan.sha256===EXPECTED_APK_SHA&&plan.bytes===145206221&&plan.new_asset_uploads===0,'207 prepared plan differs');
 require(build.versionCode===207&&build.sha256===EXPECTED_APK_SHA&&build.baseline_apk_sha256===BASELINE_APK_SHA&&build.runtime_verified===false,'207 build differs');
 require(signed.passed&&signed.apk_sha256===EXPECTED_APK_SHA&&signed.apk_bytes===145206221&&signed.expected_js_delta_passed===true
   &&signed.baseline_apk_sha256===BASELINE_APK_SHA&&signed.content_catalog_sha256===CATALOG_SHA&&signed.side_manifest_sha256===SIDE_SHA,'207 signed qualification differs');
 const delta=JSON.parse(execFileSync('C:/Users/Raegen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
   ['-B',ROOT+'/publication/verify_apk_delta.py'],{encoding:'utf8',timeout:120000,maxBuffer:1024*1024}));
 require(delta.passed&&delta.apk_sha256===EXPECTED_APK_SHA&&delta.expected_js_delta_passed&&delta.content_catalog_sha256===CATALOG_SHA&&delta.side_manifest_sha256===SIDE_SHA,'Exact local member/script delta differs');
 report.local_APK_delta=delta;
 const apk=fs.readFileSync(plan.apk);require(apk.length===plan.bytes&&sha(apk)===EXPECTED_APK_SHA,'Signed207 local bytes changed');
 const publicAPK=await get(plan.apk_url);require(publicAPK.equals(apk),'Public207 APK differs from signed bytes');
 const ranges=await settled([0,Math.floor(apk.length/2),apk.length-65536].map(async start=>{
   const end=Math.min(start+65535,apk.length-1),bytes=await get(plan.apk_url,{start,end,total:apk.length});
   require(bytes.equals(apk.subarray(start,end+1)),'Public APK range bytes differ');
   return {start,end,bytes:bytes.length,sha256:sha(bytes),verified:true};
 }));
 report.apk={url:plan.apk_url,bytes:apk.length,sha256:sha(publicAPK),full_signed_bytes_identical:true,ranges};
 console.log(JSON.stringify({verified:'signed207 APK and three ranges'}));
 const pageURL='https://ffbe.luminest.io/downloads/beta/',page=await get(pageURL);
 require(page.equals(fs.readFileSync(ROOT+'/publication/site/index.html')),'Public beta page differs');
 const links=[...page.toString('utf8').matchAll(/href="([^"]+\.apk)"/g)].map(match=>match[1]);
 const prior=read(ROOT+'/publication/site/page-plan.json').previous_APK_downloads;
 require(links.length===9&&new Set(links).size===9&&prior.length===8&&prior.every(url=>links.includes(url))&&links.includes(plan.apk_url),'Nine APK links must retain eight prior offers');
 require(page.includes(Buffer.from('<h1>Try build 207</h1>')),'Current207 heading absent');
 report.page={url:pageURL,sha256:sha(page),all_prepared_bytes_identical:true,APK_links:links,prior_eight_downloads_preserved:true};
 const updaterURL=`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/patch_version.json`,updaterBytes=await get(updaterURL),updater=JSON.parse(updaterBytes);
 require(updaterBytes.equals(fs.readFileSync(ROOT+'/publication/site/patch_version.json')),'Canonical public updater bytes differ');
 require(updater.channel==='beta'&&updater.package==='com.square_enix.ffbejpn'&&updater.version===207&&updater.versionCode===207&&updater.asset_version===206&&updater.apk_update_enabled===true,'Updater identity differs');
 require(updater.url===plan.apk_url&&updater.apk_url===plan.apk_url&&updater.sha256===EXPECTED_APK_SHA&&updater.bytes===apk.length&&Array.isArray(updater.changelog)&&updater.changelog.length===0,'Updater URLs/size/hash/changelog differ');
 report.updater={url:updaterURL,sha256:sha(updaterBytes),version:207,versionCode:207,asset_version:206,both_APK_URLs_verified:true,changelog:[]};
 report.release_metadata=await settled(['release.json','checksums.txt','phone-test-checklist.txt'].map(async name=>{
   const url='https://ffbe.luminest.io/'+plan.prefix+name,bytes=await get(url);
   require(bytes.equals(fs.readFileSync(ROOT+'/publication/site/'+name)),'Public release/checksum/checklist differs');
   return {name,url,bytes:bytes.length,sha256:sha(bytes),exact_prepared_bytes:true};
 }));
 const download=read(ROOT+'/publication/frozen206/DOWNLOAD_PLAN.json'),previousPublic=read(PREVIOUS+'/audit/PUBLIC_V206_REVIEW.json');
 require(download.passed&&download.content_catalog_sha256===CATALOG_SHA&&download.side_manifest_sha256===SIDE_SHA&&download.files.length===3,'Frozen206 assets differ');
 require(sha(fs.readFileSync(PREVIOUS+'/audit/PUBLIC_V206_REVIEW.json'))===PRIOR206_PUBLIC_SHA,'Inherited206 public evidence seal differs');
 require(previousPublic.passed&&previousPublic.apk_sha256===BASELINE_APK_SHA&&previousPublic.content_catalog_sha256===CATALOG_SHA&&previousPublic.side_manifest_sha256===SIDE_SHA,'206 public evidence differs');
 require(previousPublic.new_pack_sha256===download.files.find(file=>file.role==='pack')?.sha256,'Inherited206 pack proof belongs to another pack');
 require(download.release_tag===REUSED_RELEASE&&previousPublic.event_assets.release_tag===REUSED_RELEASE&&plan.asset_release===REUSED_RELEASE&&activation.event_release===REUSED_RELEASE&&activation.event_assets_reused_from206===true&&activation.new_asset_uploads===0,'207 must reuse the exact206 asset release');
 const metadata=await settled(download.files.filter(file=>file.role!=='pack').map(async file=>{
   const url=`https://github.com/${REPOSITORY}/releases/download/${download.release_tag}/${file.name}`,bytes=await get(url);
   require(bytes.length===file.bytes&&sha(bytes)===file.sha256&&bytes.equals(fs.readFileSync(file.local_path)),'Reused206 public metadata differs');
   if(file.role==='catalog')require(bytes.toString('utf8').trimEnd().split('\n').length===1899&&sha(bytes)===CATALOG_SHA,'All1898 catalog rows differ');
   if(file.role==='manifest'){
    const manifest=JSON.parse(bytes);require(manifest.assets.length===1898&&manifest.content_catalog.sha256===CATALOG_SHA&&manifest.bundled_side_manifest_sha256===SIDE_SHA,'Reused206 manifest/catalog identity differs');
    require(url===plan.event_manifest_url,'207 advertises another asset manifest');
   }
   return {role:file.role,url,bytes:bytes.length,sha256:sha(bytes),full_GET_byte_identical:true};
 }));
 require(metadata.length===2&&metadata.some(file=>file.role==='catalog')&&metadata.some(file=>file.role==='manifest'),'Exact reused206 catalog and manifest required');
 report.event_assets={release_tag:download.release_tag,asset_version:206,event_assets_reused_from206:true,new_asset_uploads:0,metadata,
   catalog_rows:1898,all_APK_catalog_and_side_bytes_identical_to206:true,
   unchanged_pack_re_downloaded:false,pack_evidence_scope:'Exact prior206 full public pack and five raw-deflate range verification retained;207 does not download or hash the unchanged pack again.',
   prior206_public_report_sha256:sha(fs.readFileSync(PREVIOUS+'/audit/PUBLIC_V206_REVIEW.json')),prior206_pack_sha256:previousPublic.new_pack_sha256};
 console.log(JSON.stringify({verified:'beta207 page/updater/checklist and reused206 metadata; unchanged pack not repeated'}));
 const protectedPlan=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard;
 require(JSON.stringify(protectedPlan)===JSON.stringify(plan.production_guard)&&protectedPlan.public_files.length===6,'Six protected sources differ');
 report.protected_public_files=await settled(protectedPlan.public_files.map(async file=>{
   const bytes=await get(file.url);require(bytes.length===file.bytes&&sha(bytes)===file.sha256,'Protected public production/legacy bytes changed');
   return {url:file.url,bytes:bytes.length,sha256:sha(bytes),unchanged:true};
 }));
 const stableURL=`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/manifest.json`,stable=await get(stableURL);
 require(sha(stable)===STABLE203_SHA,'Stable203 asset pointer changed');
 report.stable203_asset_pointer={url:stableURL,bytes:stable.length,sha256:sha(stable),unchanged:true};
 const gh=await githubExistingAuth(),[mainRef,latest]=await settled([
   gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`),gh.request(`/repos/${REPOSITORY}/releases/latest`)]);
 require(mainRef.object.sha===protectedPlan.main_sha&&latest.id===protectedPlan.latest_release_id&&latest.tag_name===protectedPlan.latest_tag,'Protected main/latest changed');
 report.production_repository={main_sha:mainRef.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name,unchanged:true,method:'GET through existing established-account helper'};
 report.versionCode=207;report.asset_version=206;report.apk_sha256=EXPECTED_APK_SHA;report.apk_bytes=apk.length;
 report.content_catalog_sha256=CATALOG_SHA;report.side_manifest_sha256=SIDE_SHA;
 report.independent_signed_qualification_sha256=sha(fs.readFileSync(ROOT+'/staged_build/SIGNED_SPACING_QUALIFICATION.json'));
 report.passed=true;
}
try{await main();}catch(error){report.failure=error.message;}
report.time_utc=new Date().toISOString();report.checker_sha256=sha(fs.readFileSync(new URL(import.meta.url)));
fs.writeFileSync(ROOT+'/audit/PUBLIC_V207_REVIEW.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,report:ROOT+'/audit/PUBLIC_V207_REVIEW.json',failure:report.failure||null}));
if(!report.passed)process.exitCode=1;
