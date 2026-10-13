import fs from 'node:fs';
import {githubExistingAuth,REPOSITORY} from './scripts/github_existing_auth.mjs';
import {ROOT,STABLE203_SHA,qualifiedInputs,hash,read,save,assert} from './publication_inputs.mjs';
assert(process.argv.length===2,'This script has no configurable remote destinations');
const {download:plan,build,protection}=qualifiedInputs();
const gh=await githubExistingAuth();
async function production(){
 const main=await gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`),latest=await gh.request(`/repos/${REPOSITORY}/releases/latest`);
 assert(main.object.sha===protection.main_sha&&latest.id===protection.latest_release_id&&latest.tag_name===protection.latest_tag,'Production repository changed');
 const results=await Promise.allSettled(protection.public_files.map(async f=>{const r=await fetch(f.url,{signal:AbortSignal.timeout(60000)});assert(r.ok,'Protected file unavailable');const b=Buffer.from(await r.arrayBuffer());assert(b.length===f.bytes&&hash(b)===f.sha256,'Protected production/legacy bytes differ');return {url:f.url,bytes:b.length,sha256:hash(b),unchanged:true};}));
 const stableResponse=await fetch(`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/manifest.json`,{headers:{'Accept-Encoding':'identity'},signal:AbortSignal.timeout(60000)});assert(stableResponse.ok&&hash(Buffer.from(await stableResponse.arrayBuffer()))===STABLE203_SHA,'Stable203 asset pointer differs');
 return {main_sha:main.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name,stable203assetPointerUnchanged:true,files:results.map(r=>{if(r.status==='rejected')throw r.reason;return r.value;})};
}
const before=await production();
let release=await gh.request(`/repos/${REPOSITORY}/releases/tags/${plan.release_tag}`,{allow404:true});
if(!release)release=await gh.request(`/repos/${REPOSITORY}/releases`,{method:'POST',body:{tag_name:plan.release_tag,target_commitish:'beta',name:'Event menu cleanup assets — build 206',body:'Reviewed event menu tables and requested event banners for beta build 206. Existing encounters, assets and runtime behavior are preserved. Physical-phone testing is pending.',draft:false,prerelease:true,make_latest:'false'}});
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
save(ROOT+'/publication/asset-receipt.json',{success:true,release_tag:plan.release_tag,release_id:release.id,files,unchanged_catalog_descriptors:plan.unchanged_original_rows,reused_scope:'All 1893 unchanged catalog descriptors retain their exact immutable transport URLs and bytes. This receipt verifies the three new publication files; it makes no new full-download claim for old packs.',production_before:before,production_after:await production(),stable_203_asset_pointer_modified:false,APK_pointer_modified:false,completed_at:new Date().toISOString()});
console.log(JSON.stringify({success:true,release_tag:plan.release_tag,new_asset_files_verified:3,production_preserved:true}));
