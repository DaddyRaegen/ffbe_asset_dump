// Execute the real publisher source and GitHub scope helper inside a network-free VM.
// Hosting calls, credentials and remote objects are simulated; no publisher writes hit disk.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {ROOT,DIR,PREVIOUS,qualifiedInputs,hash,assert,pin,read} from './publication_inputs.mjs';
assert(process.argv.length===2,'No remote mode or configurable destinations');
const inputs=qualifiedInputs(),plan=read(DIR+'/plan.json'),pagePlan=read(DIR+'/site/page-plan.json');
const page=fs.readFileSync(DIR+'/site/index.html'),release=read(DIR+'/site/release.json');
assert(hash(page)===pagePlan.new_sha256&&page.includes(plan.apk_url),'Prepared206 page differs');
assert(pagePlan.previous_APK_downloads.length>=7&&pagePlan.previous_APK_downloads.every(u=>page.includes('href="'+u+'"')),'Rollback links absent');
assert(release.apk.url===plan.apk_url&&release.apk.sha256===inputs.build.sha256&&release.apk.bytes===inputs.build.bytes&&release.phone_test.status==='pending'&&release.phone_test.runtime_verified===false&&release.phone_test.save_migration_verified===false,'Release/phone metadata differs');
assert(!/S:[\\/]|T:[\\/]|C:[\\/]|API_TOKEN|auth_key|password|Bearer /.test(JSON.stringify(release)),'Public release metadata contains local paths or secrets');
const frozenPath='S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json';
const frozen=read(frozenPath),stable=frozen.pointers.find(p=>p.path==='channels/beta/manifest.json');
const stableBytes=fs.readFileSync(stable.local_path);assert(hash(stableBytes)===plan.stable203assetPointerSHA,'Frozen stable203 pointer differs');
const helperPath=DIR+'/scripts/github_existing_auth.mjs',helperPin=pin(helperPath);
const norm=p=>String(p).replaceAll('\\','/');
const publicBase=`https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/${inputs.download.release_tag}/`;
const API='https://api.github.com/repos/luminest-llc/ffbe-memorial-downloads';
const rawBase='https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/';
const updaterURL=rawBase+'patch_version.json',betaURL='https://ffbe.luminest.io/downloads/beta/';

async function exercise({entry,args=[],tamper=null,expectFailure=false}){
 const remote=new Map(),virtual=new Map(),journal=[],logs=[];
 const simulatedGuard=JSON.parse(JSON.stringify(inputs.protection));
 for(const file of simulatedGuard.public_files){const b=Buffer.from('Local scoped publication fixture for '+file.url+'\n');file.bytes=b.length;file.sha256=hash(b);remote.set(file.url,b);}
 const fakeFrozen={...frozen,production_guard:simulatedGuard};
 const fakePlan={...plan,production_guard:simulatedGuard};
 if(tamper)tamper(fakePlan);
 virtual.set(norm(frozenPath),Buffer.from(JSON.stringify(fakeFrozen)));
 virtual.set(norm(DIR+'/plan.json'),Buffer.from(JSON.stringify(fakePlan)));
 remote.set(rawBase+'manifest.json',stableBytes);
 remote.set(betaURL,fs.readFileSync(PREVIOUS+'/publication/site/index.html'));
 remote.set(updaterURL,fs.readFileSync(PREVIOUS+'/publication/site/patch_version.json'));
 const mockFS={...fs,readFileSync(p,encoding){const key=norm(p),b=virtual.has(key)?virtual.get(key):fs.readFileSync(p);return encoding?b.toString(encoding):Buffer.from(b);},writeFileSync(p,data){const key=norm(p);assert(key.startsWith(norm(DIR)+'/'),'Publisher attempted a write outside206 publication');virtual.set(key,Buffer.isBuffer(data)?Buffer.from(data):Buffer.from(String(data)));}};
 const releaseId=20600001,assets=[];let created=false;
 const makeResponse=(b,status=200,headers={})=>new Response(b,{status,headers});
 const jsonResponse=(obj,status=200)=>makeResponse(JSON.stringify(obj),status,{'Content-Type':'application/json'});
 const fakeFetch=async(raw,options={})=>{
  const url=String(raw),method=options.method||'GET';journal.push({surface:'fetch',url,method});
  if(url==='https://api.github.com/user')return jsonResponse({login:'luminest-llc'});
  if(url===API)return jsonResponse({full_name:'luminest-llc/ffbe-memorial-downloads',private:false,permissions:{push:true}});
  if(url===API+'/git/ref/heads/main')return jsonResponse({object:{sha:inputs.protection.main_sha}});
  if(url===API+'/releases/latest')return jsonResponse({id:inputs.protection.latest_release_id,tag_name:inputs.protection.latest_tag});
  if(url===API+'/releases/tags/'+inputs.download.release_tag)return created?jsonResponse({id:releaseId,tag_name:inputs.download.release_tag,target_commitish:'beta',prerelease:true,draft:false}):makeResponse(null,404);
  if(url===API+'/releases'&&method==='POST'){
   const b=JSON.parse(options.body);assert(b.tag_name===inputs.download.release_tag&&b.target_commitish==='beta'&&b.prerelease===true&&b.draft===false&&b.make_latest==='false','Unexpected release mutation');created=true;
   return jsonResponse({id:releaseId,...b},201);
  }
  if(url===API+`/releases/${releaseId}`)return jsonResponse({id:releaseId,tag_name:inputs.download.release_tag,target_commitish:'beta',prerelease:true,draft:false});
  if(url===API+`/releases/${releaseId}/assets?per_page=100`)return jsonResponse(assets);
  const uploadPrefix='https://uploads.github.com/repos/luminest-llc/ffbe-memorial-downloads/releases/'+releaseId+'/assets?name=';
  if(url.startsWith(uploadPrefix)&&method==='POST'){
   const name=decodeURIComponent(url.slice(uploadPrefix.length)),descriptor=inputs.download.files.find(f=>f.name===name),b=Buffer.from(options.body);
   assert(descriptor&&b.length===descriptor.bytes&&hash(b)===descriptor.sha256,'Unexpected asset upload');remote.set(publicBase+name,b);
   const asset={id:20610000+assets.length,name,size:b.length,digest:'sha256:'+hash(b)};assets.push(asset);return jsonResponse(asset,201);
  }
  if(url===API+'/contents/channels/beta/patch_version.json?ref=beta'&&method==='GET')return jsonResponse({sha:plan.previous_updater_blob_sha,content:remote.get(updaterURL).toString('base64')});
  if(url===API+'/contents/channels/beta/patch_version.json'&&method==='PUT'){
   const body=JSON.parse(options.body),b=Buffer.from(body.content,'base64'),updater=JSON.parse(b);
   assert(body.branch==='beta'&&body.sha===plan.previous_updater_blob_sha&&updater.versionCode===206&&updater.version===206&&updater.apk_url===plan.apk_url&&updater.url===plan.apk_url&&updater.sha256===plan.sha256&&updater.bytes===plan.bytes&&Array.isArray(updater.changelog)&&updater.changelog.length===0,'Unexpected updater mutation');
   remote.set(updaterURL,b);return jsonResponse({content:{sha:'2062062062062062062062062062062062062062'},commit:{sha:'2062062062062062062062062062062062062063'}});
  }
  assert(method==='GET'||method==='HEAD','Unexpected HTTP mutation');
  assert(remote.has(url)||url===plan.apk_url||url.startsWith('https://ffbe.luminest.io/'+plan.prefix),'Unexpected remote read');
  const b=remote.get(url);if(!b)return makeResponse(null,404);
  if(method==='HEAD')return makeResponse(null,200,{'Content-Length':String(b.length)});
  const range=options.headers?.Range;if(range){const m=/^bytes=(\d+)-(\d+)$/.exec(range);assert(m,'Unexpected range');const [start,end]=m.slice(1).map(Number);return makeResponse(b.subarray(start,end+1),206,{'content-range':`bytes ${start}-${end}/${b.length}`});}
  return makeResponse(b);
 };
 const scopedGet=async url=>{const r=await fakeFetch(url);assert(r.ok,'Simulated remote file absent');return Buffer.from(await r.arrayBuffer());};
 const hosting={sha:hash,get:scopedGet,verify:async(url,b,{range=false}={})=>{const got=await scopedGet(url);assert(got.equals(b),'Hosted verification differs');return {url,sha256:hash(b),bytes:b.length,download_verified:true,range_verified:range};},put:async(domain,relative,b,options={})=>{
  assert(domain==='ffbe.luminest.io','Unexpected hosting domain');
  const allowed=[plan.prefix+plan.filename,...['checksums.txt','release.json','phone-test-checklist.txt'].map(n=>plan.prefix+n),'downloads/beta/index.html'];
  assert(allowed.includes(relative),'Unexpected hosting path');
  if(relative==='downloads/beta/index.html')assert(options.overwrite===true&&options.expectedPrevious===pagePlan.previous_sha256,'Unpinned page overwrite');
  else assert(!options.overwrite,'Immutable release overwrite');
  const url=relative==='downloads/beta/index.html'?betaURL:'https://'+domain+'/'+relative;
  journal.push({surface:'hosting-put',url,method:'PUT',overwrite:!!options.overwrite});remote.set(url,Buffer.from(b));
  return {url,sha256:hash(b),bytes:b.length,download_verified:true,range_verified:!!options.range};
 }};
 const context=vm.createContext({Buffer,URL,Response,AbortSignal,Date,Map,Set,console:{log:v=>logs.push(String(v))},fetch:fakeFetch,setTimeout:callback=>{callback();return 0;},process:{argv:['node',entry,...args],env:{},exit:n=>{throw Object.assign(Error('Local dryrun exit'),{dryrunExit:true,code:n});}}});
 const cache=new Map();
 const synthetic=(id,obj)=>new vm.SyntheticModule(Object.keys(obj),function(){for(const [name,value] of Object.entries(obj))this.setExport(name,value);},{context,identifier:id});
 async function load(id){
  if(cache.has(id))return cache.get(id);
  let module;
  if(id==='node:fs')module=synthetic(id,{default:mockFS});
  else if(id==='node:crypto')module=synthetic(id,{default:crypto});
  else if(id==='node:child_process')module=synthetic(id,{execFileSync:()=> 'username=luminest-llc\npassword=LOCAL_SIMULATION_ONLY\n'});
  else if(id.startsWith('file:///T:/'))module=synthetic(id,hosting);
  else module=new vm.SourceTextModule(fs.readFileSync(id,'utf8'),{context,identifier:id});
  cache.set(id,module);
  await module.link(async(spec,importer)=>load(spec.startsWith('node:')||spec.startsWith('file:')?spec:norm(path.resolve(path.dirname(importer.identifier),spec))));
  return module;
 }
 let failure=null;
 try{
  // Exercise creation/upload, then stage/activate in one isolated virtual publisher state.
  const first=await load(norm(DIR+'/publish_assets.mjs'));context.process.argv=['node',norm(DIR+'/publish_assets.mjs')];await first.evaluate();
  const stage=await load(norm(DIR+'/publish_site.mjs'));context.process.argv=['node',norm(DIR+'/publish_site.mjs'),'--stage'];
  try{await stage.evaluate();}catch(error){if(!error.dryrunExit||error.code!==0)throw error;}
  // A new module identifier is needed because the real stage exits its process.
  const activate=new vm.SourceTextModule(fs.readFileSync(DIR+'/publish_site.mjs','utf8'),{context,identifier:norm(DIR+'/activate-vm.mjs')});
  await activate.link(async(spec,importer)=>load(spec.startsWith('node:')||spec.startsWith('file:')?spec:norm(path.resolve(path.dirname(importer.identifier),spec))));
  context.process.argv=['node',norm(DIR+'/publish_site.mjs'),'--activate'];await activate.evaluate();
 }catch(error){failure=error.message;}
 const mutations=journal.filter(r=>r.method!=='GET'&&r.method!=='HEAD');
 if(expectFailure){assert(failure,'Unsafe target fixture was accepted');assert(!mutations.some(r=>r.surface==='hosting-put'||r.method==='PUT'),'Unsafe hosting/updater mutation proceeded');}
 else{
  assert(!failure,failure||'Unexpected dryrun failure');
  assert(assets.length===3&&created,'New206 asset creation not exercised');
  const updater=JSON.parse(remote.get(updaterURL));assert(updater.changelog.length===0,'Updater changelog not empty');
  const receipt=JSON.parse(virtual.get(norm(DIR+'/activation-receipt.json')));assert(receipt.success&&receipt.versionCode===206&&receipt.sha256===plan.sha256&&receipt.runtime_verified===false,'Simulated activation receipt differs');
  assert(remote.get(betaURL).equals(page),'Prepared page not activated in fixture');
 }
 return {passed:true,expect_failure:expectFailure,failure,mutation_targets:mutations.map(({surface,url,method,overwrite})=>({surface,url,method,...(overwrite===undefined?{}:{overwrite})})),request_count:journal.length};
}
const success=await exercise({entry:'publish_assets.mjs'});
const unsafe=await exercise({entry:'publish_site.mjs',tamper:p=>{p.apk_url='https://ffbe.luminest.io/downloads/FFBE-production.apk';},expectFailure:true});
assert(pin(helperPath).sha256===helperPin.sha256,'Existing206 GitHub helper changed during review');
const report={schema:'ffbe-local206-publication-scope-review-v1',passed:true,network_requests_made:0,remote_mutations_made:0,credentials_read:false,simulation:'Real publisher/helper source executed in isolated VM. Production public bodies and credentials are simulated; actual206 local APK/catalog/qualification/page pins are used. This does not verify public network availability.',apk:{bytes:plan.bytes,sha256:plan.sha256,url:plan.apk_url},qualified_catalog_sha256:inputs.download.content_catalog_sha256,qualified_download_plan:pin(ROOT+'/asset_publication/DOWNLOAD_PLAN.json'),previous_page_sha256:pagePlan.previous_sha256,rollback_APK_links:pagePlan.previous_APK_downloads,updater:{channel:'beta',version:206,versionCode:206,apk_url:plan.apk_url,url:plan.apk_url,changelog:[]},stable203_pointer_sha256:plan.stable203assetPointerSHA,existing_GitHub_helper:helperPin,script_pins:Object.fromEntries(['publication_inputs.mjs','prepare_site.mjs','publish_assets.mjs','publish_site.mjs','review_publication_local.mjs'].map(n=>[n,pin(DIR+'/'+n)])),positive:success,negative_wrong_APK_target:unsafe,phone_runtime_verified:false};
fs.writeFileSync(ROOT+'/audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,network_requests_made:0,remote_mutations_made:0,report:ROOT+'/audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json'}));
