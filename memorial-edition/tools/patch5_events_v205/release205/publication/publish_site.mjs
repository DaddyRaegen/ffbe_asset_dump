import fs from 'node:fs';
import {put,get,sha,verify} from 'file:///T:/Projects/FFBE%20Patch/localization-rounds/2026-09-25-download-recovery/scripts/hosting.mjs';
import {githubExistingAuth,REPOSITORY} from './scripts/github_existing_auth.mjs';
const ROOT='S:/FFBE JP Data Export/build/v205-patch5-events',DIR=ROOT+'/publication';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
const assert=(v,m)=>{if(!v)throw Error(m);};
const mode=process.argv[2];assert(['--stage','--activate'].includes(mode)&&process.argv.length===3,'Scoped stage or activate required');
const plan=read(DIR+'/plan.json'),qualified=read(ROOT+'/staged_build/SIGNED_EVENT_QUALIFICATION.json');
const host=read(ROOT+'/audit/ACTUAL205_CATALOG_HOST_ADMISSION.json');
const assets=read(DIR+'/asset-receipt.json'),downloads=read(ROOT+'/asset_publication/DOWNLOAD_PLAN.json');
assert(qualified.passed&&qualified.apk_sha256===plan.sha256&&plan.versionCode===205&&host.passed&&host.catalog_sha256===plan.event_catalog_sha256,'Exact205 qualification and host fixtures required');
const transport=read(ROOT+'/audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json');
assert(transport.passed&&transport.content_catalog_sha256===plan.event_catalog_sha256&&transport.download_plan_sha256===plan.download_plan_sha256,'Exact independent transport qualification required');
assert(assets.success&&assets.release_tag===plan.asset_release&&sha(fs.readFileSync(ROOT+'/asset_publication/DOWNLOAD_PLAN.json'))===plan.download_plan_sha256,'Frozen public event assets required');
const bytes=fs.readFileSync(plan.apk);assert(bytes.length===plan.bytes&&sha(bytes)===plan.sha256,'Qualified APK changed');
async function protectedFiles(){
 const results=await Promise.allSettled(plan.production_guard.public_files.map(async f=>{const b=await get(f.url);assert(b.length===f.bytes&&sha(b)===f.sha256,'Protected public file changed');return {url:f.url,bytes:b.length,sha256:sha(b),unchanged:true};}));
 return results.map(r=>{if(r.status==='rejected')throw r.reason;return r.value;});
}
async function verifyData(){
 const metadata=downloads.files.filter(f=>f.role!=='pack').map(f=>({url:`https://github.com/${REPOSITORY}/releases/download/${downloads.release_tag}/${f.name}`,bytes:f.bytes,sha256:f.sha256}));
 const results=await Promise.allSettled(metadata.map(async f=>{const b=await get(f.url);assert(b.length===f.bytes&&sha(b)===f.sha256,'Event metadata readback differs');return {...f,full_download_verified:true};}));
 const stable=await get(`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/manifest.json`);assert(sha(stable)===plan.stable203assetPointerSHA,'Earlier203/204 data pointer changed');
 return {metadata:results.map(r=>{if(r.status==='rejected')throw r.reason;return r.value;}),stable203assetPointerUnchanged:true};
}
if(mode==='--stage'){
 const before=await protectedFiles(),data=await verifyData();
 const h=await fetch(plan.apk_url,{method:'HEAD',signal:AbortSignal.timeout(30000)});let result;
 if(h.ok)result=await verify(plan.apk_url,bytes,{range:true});
 else {assert(h.status===404,'Unexpected immutable APK destination');result=await put('ffbe.luminest.io',plan.prefix+plan.filename,bytes,{range:true});}
 const ranges=[];for(const start of [0,Math.floor(bytes.length/2),bytes.length-65536]){const end=Math.min(start+65535,bytes.length-1);const r=await fetch(plan.apk_url,{headers:{Range:`bytes=${start}-${end}`,'Accept-Encoding':'identity'},signal:AbortSignal.timeout(60000)});assert(r.status===206&&r.headers.get('content-range')===`bytes ${start}-${end}/${bytes.length}`,'APK range response differs');assert(Buffer.from(await r.arrayBuffer()).equals(bytes.subarray(start,end+1)),'APK range bytes differ');ranges.push({start,end,verified:true});}
 save(DIR+'/apk-stage-receipt.json',{success:true,APK_published:true,versionCode:205,apk:{...result,ranges},data,protected_before:before,protected_after:await protectedFiles(),runtime_verified:false,completed_at:new Date().toISOString()});
 console.log(JSON.stringify({APK_published:true,apk_url:plan.apk_url,bytes:plan.bytes,sha256:plan.sha256}));process.exit(0);
}
const stage=read(DIR+'/apk-stage-receipt.json');assert(stage.success&&stage.apk.sha256===plan.sha256&&stage.apk.bytes===plan.bytes,'Verified immutable APK missing');
const pagePlan=read(DIR+'/site/page-plan.json'),page=fs.readFileSync(DIR+'/site/index.html');assert(sha(page)===pagePlan.new_sha256&&page.includes(plan.apk_url),'Prepared page differs');
const current=await get('https://ffbe.luminest.io/downloads/beta/');assert(sha(current)===pagePlan.previous_sha256||current.equals(page),'Beta page changed concurrently');
const protected_before=await protectedFiles(),data=await verifyData(),gh=await githubExistingAuth();
async function repositoryGuard(){const main=await gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`),latest=await gh.request(`/repos/${REPOSITORY}/releases/latest`);assert(main.object.sha===plan.production_guard.main_sha&&latest.id===plan.production_guard.latest_release_id&&latest.tag_name===plan.production_guard.latest_tag,'Production repository differs');return {main_sha:main.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name};}
await repositoryGuard();
const updater={channel:'beta',package:'com.square_enix.ffbejpn',version:205,versionCode:205,asset_version:205,apk_update_enabled:true,bytes:plan.bytes,sha256:plan.sha256,apk_url:plan.apk_url,url:plan.apk_url,changelog:['Production Patch 5 plus 863 missing event books.','Original startup assets and downloader retained; required event assets download from GitHub.','Phone testing is pending.'],note:'Build205: literal production Patch5 plus missing events and required GitHub event assets. Original startup files and downloader retained. Z Fold8 / Android17 phone test pending.'};
const updaterBytes=Buffer.from(JSON.stringify(updater,null,2)+'\n');fs.writeFileSync(DIR+'/site/patch_version.json',updaterBytes);
const filePath='channels/beta/patch_version.json',previous=await gh.request(`/repos/${REPOSITORY}/contents/${filePath}?ref=beta`);
const same=previous.content&&Buffer.from(previous.content.replace(/\s/g,''),'base64').equals(updaterBytes);
assert(same||previous.sha===plan.previous_updater_blob_sha,'Beta updater changed concurrently');
const releaseFiles=[];for(const name of ['checksums.txt','release.json','phone-test-checklist.txt']){const b=fs.readFileSync(DIR+'/site/'+name);assert(b.length===pagePlan.files[name].bytes&&sha(b)===pagePlan.files[name].sha256,'Release metadata changed');const target=plan.prefix+name,url='https://ffbe.luminest.io/'+target;const h=await fetch(url,{method:'HEAD',signal:AbortSignal.timeout(30000)});if(h.ok)releaseFiles.push(await verify(url,b));else {assert(h.status===404,'Unexpected metadata destination');releaseFiles.push(await put('ffbe.luminest.io',target,b));}}
const pointer=same?{path:filePath,blob_sha:previous.sha,reused:true}:await gh.putBetaMetadata(filePath,updaterBytes,previous.sha),pointerURL=`https://raw.githubusercontent.com/${REPOSITORY}/beta/${filePath}`;
save(DIR+'/activation-progress.json',{pointer:{...pointer,url:pointerURL,sha256:sha(updaterBytes)},release_files:releaseFiles,page_published:false});
let verified=false;for(let i=0;i<60;i++){const r=await fetch(pointerURL,{cache:'no-store',headers:{'Cache-Control':'no-cache','Accept-Encoding':'identity'},signal:AbortSignal.timeout(60000)});if(r.ok&&Buffer.from(await r.arrayBuffer()).equals(updaterBytes)){verified=true;break;}if(i%6===0)console.log(JSON.stringify({waiting_for_public_beta_updater_cache:true,attempt:i+1}));await new Promise(resolve=>setTimeout(resolve,10000));}
assert(verified,'Public updater readback differs');
const publishedPage=current.equals(page)?await verify('https://ffbe.luminest.io/downloads/beta/',page):await put('ffbe.luminest.io','downloads/beta/index.html',page,{overwrite:true,expectedPrevious:pagePlan.previous_sha256});
assert((await get('https://ffbe.luminest.io/downloads/beta/')).equals(page),'Beta directory readback differs');
save(DIR+'/activation-progress.json',{pointer:{...pointer,url:pointerURL,sha256:sha(updaterBytes)},page_published:true,page:publishedPage,release_files:releaseFiles});
save(DIR+'/activation-receipt.json',{success:true,APK_published:true,beta_url:'https://ffbe.luminest.io/downloads/beta/',apk_url:plan.apk_url,versionCode:205,bytes:plan.bytes,sha256:plan.sha256,event_release:assets.release_tag,event_release_id:assets.release_id,event_catalog_sha256:plan.event_catalog_sha256,event_manifest_url:plan.event_manifest_url,stable203assetPointerUnchanged:true,pointer:{...pointer,url:pointerURL,sha256:sha(updaterBytes),full_download_verified:true},release_files:releaseFiles,page:publishedPage,data,protected_before,protected_after:await protectedFiles(),production_after:await repositoryGuard(),runtime_verified:false,physical_phone_test:'pending',save_migration_verified:false,completed_at:new Date().toISOString()});
console.log(JSON.stringify({success:true,apk_url:plan.apk_url,beta_url:'https://ffbe.luminest.io/downloads/beta/',versionCode:205,production_preserved:true,physical_phone_test:'pending'}));
