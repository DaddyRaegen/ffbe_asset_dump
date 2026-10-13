// Execute the real publisher and narrow GitHub helper in a network-free VM.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import vm from 'node:vm';
import {ROOT,DIR,FROZEN,qualifiedInputs,hash,assert,pin,read} from './publication_inputs.mjs';
assert(process.argv.length===2,'No remote mode or configurable destinations');
const inputs=qualifiedInputs(),plan=read(DIR+'/plan.json'),pagePlan=read(DIR+'/site/page-plan.json');
const page=fs.readFileSync(DIR+'/site/index.html'),release=read(DIR+'/site/release.json');
assert(hash(page)===pagePlan.new_sha256&&page.includes(plan.apk_url),'Prepared207 page differs');
assert(pagePlan.previous_APK_downloads.length===8&&pagePlan.previous_APK_downloads.every(u=>page.includes('href="'+u+'"')),'An older APK link is missing');
assert(release.apk.url===plan.apk_url&&release.apk.sha256===inputs.build.sha256&&release.apk.bytes===inputs.build.bytes&&release.phone_test.status==='pending'&&release.phone_test.runtime_verified===false&&release.phone_test.save_migration_verified===false,'Release/phone metadata differs');
assert(release.delivery.event_data_version===206&&release.delivery.new_asset_uploads===0&&release.delivery.new_packs===0&&release.delivery.event_catalog_sha256===inputs.download.content_catalog_sha256,'207 data scope differs');
assert(!/S:[\\/]|T:[\\/]|C:[\\/]|API_TOKEN|auth_key|password|Bearer /.test(JSON.stringify(release)),'Public metadata contains a local path or secret');
const frozen=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json');
const stable=fs.readFileSync(frozen.pointers.find(p=>p.path==='channels/beta/manifest.json').local_path);assert(hash(stable)===plan.stable203assetPointerSHA,'Frozen stable203 pointer differs');
const norm=p=>String(p).replaceAll('\\','/'),API='https://api.github.com/repos/luminest-llc/ffbe-memorial-downloads';
const rawBase='https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/',updaterURL=rawBase+'patch_version.json',betaURL='https://ffbe.luminest.io/downloads/beta/';
const helperPath=DIR+'/scripts/github_existing_auth.mjs',helperPin=pin(helperPath);

async function exercise({tamper=null,expectFailure=false,helperOnly=false}){
 const remote=new Map(),virtual=new Map(),journal=[],logs=[],fixtureHashes=new Map();
 // Keep real protected metadata pins. Only public bodies are simulated, with
 // hash aliases confined to this VM; real local APK/data hashes remain checked.
 for(const file of inputs.protection.public_files){const b=Buffer.alloc(file.bytes);b.write('Local protected-file fixture '+file.url);fixtureHashes.set(hash(b),file.sha256);remote.set(file.url,b);}
 const fixtureHash=b=>fixtureHashes.get(hash(b))||hash(b);
 const fakeCrypto={...crypto,createHash(algorithm){if(algorithm!=='sha256')return crypto.createHash(algorithm);const chunks=[];return {update(b){chunks.push(Buffer.isBuffer(b)?b:Buffer.from(b));return this;},digest(encoding){const result=fixtureHash(Buffer.concat(chunks));return encoding==='hex'?result:Buffer.from(result,'hex');}};}};
 const fakePlan={...plan};if(tamper)tamper(fakePlan);virtual.set(norm(DIR+'/plan.json'),Buffer.from(JSON.stringify(fakePlan)));
 remote.set(rawBase+'manifest.json',stable);remote.set(betaURL,fs.readFileSync(FROZEN+'/index.html'));remote.set(updaterURL,fs.readFileSync(FROZEN+'/patch_version.json'));
 for(const file of inputs.download.files.filter(f=>f.role!=='pack'))remote.set(`https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/${inputs.download.release_tag}/${file.name}`,fs.readFileSync(file.local_path));
 const mockFS={...fs,readFileSync(p,encoding){const b=virtual.has(norm(p))?virtual.get(norm(p)):fs.readFileSync(p);return encoding?b.toString(encoding):Buffer.from(b);},writeFileSync(p,data){assert(norm(p).startsWith(norm(DIR)+'/'),'Publisher attempted a write outside207 publication');virtual.set(norm(p),Buffer.isBuffer(data)?Buffer.from(data):Buffer.from(String(data)));}};
 const response=(b,status=200,headers={})=>new Response(b,{status,headers}),json=(obj,status=200)=>response(JSON.stringify(obj),status,{'Content-Type':'application/json'});
 const fakeFetch=async(raw,options={})=>{
  const url=String(raw),method=options.method||'GET';journal.push({surface:'fetch',url,method});
  if(url==='https://api.github.com/user'&&method==='GET')return json({login:'luminest-llc'});
  if(url===API&&method==='GET')return json({full_name:'luminest-llc/ffbe-memorial-downloads',private:false,permissions:{push:true}});
  if(url===API+'/git/ref/heads/main'&&method==='GET')return json({object:{sha:inputs.protection.main_sha}});
  if(url===API+'/releases/latest'&&method==='GET')return json({id:inputs.protection.latest_release_id,tag_name:inputs.protection.latest_tag});
  if(url===API+'/contents/channels/beta/patch_version.json?ref=beta'&&method==='GET')return json({sha:plan.previous_updater_blob_sha,content:remote.get(updaterURL).toString('base64')});
  if(url===API+'/contents/channels/beta/patch_version.json'&&method==='PUT'){
   const body=JSON.parse(options.body),b=Buffer.from(body.content,'base64'),updater=JSON.parse(b);
   assert(body.branch==='beta'&&body.sha===plan.previous_updater_blob_sha&&updater.versionCode===207&&updater.version===207&&updater.asset_version===206&&updater.apk_url===plan.apk_url&&updater.url===plan.apk_url&&updater.sha256===plan.sha256&&updater.bytes===plan.bytes&&Array.isArray(updater.changelog)&&updater.changelog.length===0,'Unexpected updater mutation');
   remote.set(updaterURL,b);return json({content:{sha:'2072072072072072072072072072072072072072'},commit:{sha:'2072072072072072072072072072072072072073'}});
  }
  assert(method==='GET'||method==='HEAD','Unexpected HTTP mutation');assert(remote.has(url)||url===plan.apk_url||url.startsWith('https://ffbe.luminest.io/'+plan.prefix),'Unexpected remote read');
  const b=remote.get(url);if(!b)return response(null,404);if(method==='HEAD')return response(null,200,{'Content-Length':String(b.length)});
  const range=options.headers?.Range;if(range){const m=/^bytes=(\d+)-(\d+)$/.exec(range);assert(m,'Unexpected range');const [start,end]=m.slice(1).map(Number);return response(b.subarray(start,end+1),206,{'content-range':`bytes ${start}-${end}/${b.length}`});}return response(b);
 };
 const scopedGet=async url=>{const r=await fakeFetch(url);assert(r.ok,'Simulated remote file absent');return Buffer.from(await r.arrayBuffer());};
 const hosting={sha:fixtureHash,get:scopedGet,verify:async(url,b,{range=false}={})=>{assert((await scopedGet(url)).equals(b),'Hosted verification differs');return {url,sha256:hash(b),bytes:b.length,download_verified:true,range_verified:range};},put:async(domain,relative,b,options={})=>{
  assert(domain==='ffbe.luminest.io','Unexpected hosting domain');const allowed=[plan.prefix+plan.filename,...['checksums.txt','release.json','phone-test-checklist.txt'].map(n=>plan.prefix+n),'downloads/beta/index.html'];assert(allowed.includes(relative),'Unexpected hosting path');
  if(relative==='downloads/beta/index.html')assert(options.overwrite===true&&options.expectedPrevious===pagePlan.previous_sha256,'Unpinned page overwrite');else assert(!options.overwrite,'Immutable release overwrite');
  const url=relative==='downloads/beta/index.html'?betaURL:'https://'+domain+'/'+relative;journal.push({surface:'hosting-put',url,method:'PUT',overwrite:!!options.overwrite});remote.set(url,Buffer.from(b));return {url,sha256:hash(b),bytes:b.length,download_verified:true,range_verified:!!options.range};
 }};
 const child={execFileSync(command,args){if(command==='git'){assert(JSON.stringify(args)===JSON.stringify(['credential','fill']),'Unexpected credential command');return 'username=luminest-llc\npassword=LOCAL_SIMULATION_ONLY\n';}assert(command.endsWith('/python.exe')&&JSON.stringify(args)===JSON.stringify(['-B',DIR+'/verify_apk_delta.py']),'Unexpected subprocess');return JSON.stringify(inputs.local);}};
 const context=vm.createContext({Buffer,URL,Response,AbortSignal,Date,Map,Set,console:{log:v=>logs.push(String(v))},fetch:fakeFetch,setTimeout:callback=>{callback();return 0;},process:{argv:[],env:{},exit:n=>{throw Object.assign(Error('Local dryrun exit'),{dryrunExit:true,code:n});}}});
 const cache=new Map(),synthetic=(id,obj)=>new vm.SyntheticModule(Object.keys(obj),function(){for(const [name,value] of Object.entries(obj))this.setExport(name,value);},{context,identifier:id});
 async function load(id){
  if(cache.has(id))return cache.get(id);let module;
  if(id==='node:fs')module=synthetic(id,{default:mockFS});else if(id==='node:crypto')module=synthetic(id,{default:fakeCrypto});else if(id==='node:child_process')module=synthetic(id,child);else if(id.startsWith('file:///T:/'))module=synthetic(id,hosting);else module=new vm.SourceTextModule(fs.readFileSync(id,'utf8'),{context,identifier:id});
  cache.set(id,module);await module.link(async(spec,importer)=>load(spec.startsWith('node:')||spec.startsWith('file:')?spec:norm(path.resolve(path.dirname(importer.identifier),spec))));return module;
 }
 let failure=null,negativeHelperChecks=0;
 try{
  if(helperOnly){
   const helper=await load(norm(helperPath));await helper.evaluate();const gh=await helper.namespace.githubExistingAuth();
   const valid={channel:'beta',package:'com.square_enix.ffbejpn',version:207,versionCode:207,asset_version:206,apk_update_enabled:true,bytes:plan.bytes,sha256:plan.sha256,apk_url:plan.apk_url,url:plan.apk_url,changelog:[]};
   const cases=[()=>gh.request(API+'/releases',{method:'POST'}),()=>gh.request('/repos/luminest-llc/other/git/ref/heads/main'),()=>gh.request(`/repos/luminest-llc/ffbe-memorial-downloads/git/refs`,{method:'POST'}),()=>gh.putBetaMetadata('channels/beta/manifest.json',Buffer.from(JSON.stringify(valid)),plan.previous_updater_blob_sha),()=>gh.putBetaMetadata('channels/main/patch_version.json',Buffer.from(JSON.stringify(valid)),plan.previous_updater_blob_sha),()=>gh.putBetaMetadata('channels/beta/patch_version.json',Buffer.from(JSON.stringify({...valid,asset_version:207})),plan.previous_updater_blob_sha),()=>gh.putBetaMetadata('channels/beta/patch_version.json',Buffer.from(JSON.stringify({...valid,changelog:['unexpected']})),plan.previous_updater_blob_sha),()=>gh.putBetaMetadata('channels/beta/patch_version.json',Buffer.from(JSON.stringify({...valid,apk_url:'https://ffbe.luminest.io/downloads/production.apk',url:'https://ffbe.luminest.io/downloads/production.apk'})),plan.previous_updater_blob_sha)];
   for(const reject of cases){let rejected=false;try{await reject();}catch{rejected=true;}assert(rejected,'Unsafe GitHub helper case was accepted');negativeHelperChecks++;}
   assert(!journal.some(r=>r.method!=='GET'&&r.method!=='HEAD'),'Unsafe helper case reached HTTP mutation');
  }else{
   const stage=await load(norm(DIR+'/publish_site.mjs'));context.process.argv=['node',norm(DIR+'/publish_site.mjs'),'--stage'];try{await stage.evaluate();}catch(error){if(!error.dryrunExit||error.code!==0)throw error;}
   const activate=new vm.SourceTextModule(fs.readFileSync(DIR+'/publish_site.mjs','utf8'),{context,identifier:norm(DIR+'/activate-vm.mjs')});await activate.link(async(spec,importer)=>load(spec.startsWith('node:')||spec.startsWith('file:')?spec:norm(path.resolve(path.dirname(importer.identifier),spec))));context.process.argv=['node',norm(DIR+'/publish_site.mjs'),'--activate'];await activate.evaluate();
  }
 }catch(error){failure=error.message;}
 const mutations=journal.filter(r=>r.method!=='GET'&&r.method!=='HEAD');
 if(expectFailure){assert(failure,'Unsafe target fixture was accepted');assert(mutations.length===0,'Unsafe target proceeded to a mutation');}
 else{assert(!failure,failure||'Unexpected dryrun failure');if(!helperOnly){assert(mutations.filter(r=>r.surface==='hosting-put').length===5&&mutations.filter(r=>r.surface==='fetch').length===1,'Mutation set differs');const receipt=JSON.parse(virtual.get(norm(DIR+'/activation-receipt.json')));assert(receipt.success&&receipt.versionCode===207&&receipt.asset_version===206&&receipt.sha256===plan.sha256&&receipt.new_asset_uploads===0&&receipt.runtime_verified===false,'Simulated receipt differs');assert(remote.get(betaURL).equals(page),'Prepared page not activated');}}
 return {passed:true,expect_failure:expectFailure,failure,negative_helper_checks:negativeHelperChecks,mutation_targets:mutations.map(({surface,url,method,overwrite})=>({surface,url,method,...(overwrite===undefined?{}:{overwrite})})),request_count:journal.length};
}
const positive=await exercise({}),unsafe=await exercise({tamper:p=>{p.apk_url='https://ffbe.luminest.io/downloads/FFBE-production.apk';},expectFailure:true}),helper=await exercise({helperOnly:true});
assert(pin(helperPath).sha256===helperPin.sha256,'207 GitHub helper changed during review');
const report={schema:'ffbe-local207-publication-scope-review-v1',passed:true,network_requests_made:0,remote_mutations_made:0,credentials_read:false,simulation:'Real publisher/helper source executes in an isolated VM. Public protected-file bodies and credentials are simulated; real207 local APK/script/catalog/qualification/page pins are checked. This does not verify public network availability.',apk:{bytes:plan.bytes,sha256:plan.sha256,url:plan.apk_url},baseline206_apk_sha256:inputs.local.baseline_apk_sha256,expected_script_delta:inputs.local,qualified_catalog_sha256:inputs.download.content_catalog_sha256,qualified_side_manifest_sha256:inputs.download.side_manifest_sha256,event_assets_reused_from206:true,new_asset_uploads:0,previous_page_sha256:pagePlan.previous_sha256,rollback_APK_links:pagePlan.previous_APK_downloads,updater:{channel:'beta',version:207,versionCode:207,asset_version:206,apk_url:plan.apk_url,url:plan.apk_url,changelog:[]},stable203_pointer_sha256:plan.stable203assetPointerSHA,script_pins:Object.fromEntries(['publication_inputs.mjs','verify_apk_delta.py','prepare_site.mjs','publish_site.mjs','review_publication_local.mjs','scripts/github_existing_auth.mjs'].map(n=>[n,pin(DIR+'/'+n)])),positive,negative_wrong_APK_target:unsafe,negative_GitHub_helper:helper,phone_runtime_verified:false};
fs.writeFileSync(ROOT+'/audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,network_requests_made:0,remote_mutations_made:0,report:ROOT+'/audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json'}));
