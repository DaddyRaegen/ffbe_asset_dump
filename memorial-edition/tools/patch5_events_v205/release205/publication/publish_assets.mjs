import fs from 'node:fs';
import crypto from 'node:crypto';
import {githubExistingAuth,REPOSITORY} from './scripts/github_existing_auth.mjs';
const ROOT='S:/FFBE JP Data Export/build/v205-patch5-events';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
const assert=(v,m)=>{if(!v)throw Error(m);};
assert(process.argv.length===2,'This script has no configurable remote destinations');
const plan=read(ROOT+'/asset_publication/DOWNLOAD_PLAN.json');
const build=read(ROOT+'/staged_build/EVENT_ONLY_APK_BUILD.json');
const qualified=read(ROOT+'/staged_build/SIGNED_EVENT_QUALIFICATION.json');
const host=read(ROOT+'/audit/ACTUAL205_CATALOG_HOST_ADMISSION.json');
assert(plan.passed&&qualified.passed&&build.versionCode===205&&qualified.apk_sha256===build.sha256&&host.passed&&host.catalog_sha256===plan.content_catalog_sha256,'Exact205 signed qualification and actual catalog fixtures required');
const transport=read(ROOT+'/audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json');
assert(transport.passed&&transport.content_catalog_sha256===plan.content_catalog_sha256&&transport.download_plan_sha256===hash(fs.readFileSync(ROOT+'/asset_publication/DOWNLOAD_PLAN.json'))&&transport.new_pack_sha256===plan.new_pack.sha256,'Independent exact event transport qualification required');
const apk=fs.readFileSync(build.apk);assert(apk.length===build.bytes&&hash(apk)===build.sha256,'Qualified signed APK changed');
assert(/^beta-content-v205-[0-9a-f]{16}$/.test(plan.release_tag)&&plan.files.length===3,'Unexpected event asset release');
for(const file of plan.files){const b=fs.readFileSync(file.local_path);assert(b.length===file.bytes&&hash(b)===file.sha256,'Frozen event publication file differs');}
const protection=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard;
const gh=await githubExistingAuth();
async function production(){
 const main=await gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`),latest=await gh.request(`/repos/${REPOSITORY}/releases/latest`);
 assert(main.object.sha===protection.main_sha&&latest.id===protection.latest_release_id&&latest.tag_name===protection.latest_tag,'Production repository changed');
 const results=await Promise.allSettled(protection.public_files.map(async f=>{const r=await fetch(f.url,{signal:AbortSignal.timeout(60000)});assert(r.ok,'Protected file unavailable');const b=Buffer.from(await r.arrayBuffer());assert(b.length===f.bytes&&hash(b)===f.sha256,'Protected production/legacy bytes differ');return {url:f.url,bytes:b.length,sha256:hash(b),unchanged:true};}));
 return {main_sha:main.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name,files:results.map(r=>{if(r.status==='rejected')throw r.reason;return r.value;})};
}
const before=await production();
let release=await gh.request(`/repos/${REPOSITORY}/releases/tags/${plan.release_tag}`,{allow404:true});
if(!release)release=await gh.request(`/repos/${REPOSITORY}/releases`,{method:'POST',body:{tag_name:plan.release_tag,target_commitish:'beta',name:'Patch 5 additional event assets — build205',body:'Assets required for the event-only Patch 5 beta build205. Existing Patch 5 content is preserved. Physical-phone gameplay testing is pending.',draft:false,prerelease:true,make_latest:'false'}});
assert(release.tag_name===plan.release_tag&&release.prerelease&&release.target_commitish==='beta'&&!release.draft,'Unexpected release target');
const files=[];
for(const file of plan.files){
 const b=fs.readFileSync(file.local_path);const existing=(await gh.request(`/repos/${REPOSITORY}/releases/${release.id}/assets?per_page=100`)).find(a=>a.name===file.name);
 const asset=existing||await gh.uploadAsset(release.id,file.name,b);assert(asset.size===file.bytes,'Server asset size differs');if(asset.digest)assert(asset.digest==='sha256:'+file.sha256,'Server asset digest differs');
 const url=`https://github.com/${REPOSITORY}/releases/download/${plan.release_tag}/${file.name}`;
 const r=await fetch(url,{headers:{'Accept-Encoding':'identity'},signal:AbortSignal.timeout(180000)});assert(r.ok,'Event asset readback failed');const publicBytes=Buffer.from(await r.arrayBuffer());assert(publicBytes.equals(b),'Event asset full-download bytes differ');
 const ranges=[];for(const start of [0,Math.floor(b.length/2),Math.max(0,b.length-65536)]){const end=Math.min(start+65535,b.length-1);const rr=await fetch(url,{headers:{Range:`bytes=${start}-${end}`,'Accept-Encoding':'identity'},signal:AbortSignal.timeout(60000)});assert(rr.status===206&&rr.headers.get('content-range')===`bytes ${start}-${end}/${b.length}`,'Event asset range differs');assert(Buffer.from(await rr.arrayBuffer()).equals(b.subarray(start,end+1)),'Event asset range bytes differ');ranges.push({start,end,verified:true});}
 files.push({name:file.name,id:asset.id,url,bytes:b.length,sha256:file.sha256,full_download_verified:true,ranges});
 console.log(JSON.stringify({published_event_data:file.name,bytes:b.length,verified:true}));
}
save(ROOT+'/publication/asset-receipt.json',{success:true,release_tag:plan.release_tag,release_id:release.id,files,reused_event_file_count:plan.reused_event_files.length,reused_scope:'Exact local packed ranges decoded and matched to retained event hashes. Same immutable already-published203 URLs reused; no new full body hash claim for old packs.',production_before:before,production_after:await production(),stable_203_asset_pointer_modified:false,APK_pointer_modified:false,completed_at:new Date().toISOString()});
console.log(JSON.stringify({success:true,release_tag:plan.release_tag,new_asset_files_verified:3,production_preserved:true}));
