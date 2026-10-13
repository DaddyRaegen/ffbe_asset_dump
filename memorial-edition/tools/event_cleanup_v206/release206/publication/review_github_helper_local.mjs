// Scope tests for the existing206 helper; Git credentials and HTTP are simulated.
import fs from 'node:fs';
import crypto from 'node:crypto';
import vm from 'node:vm';
const ROOT='S:/FFBE JP Data Export/build/v206-event-cleanup';
const helper=ROOT+'/publication/scripts/github_existing_auth.mjs';
const bytes=fs.readFileSync(helper),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const calls=[],results=[];
const repository='luminest-llc/ffbe-memorial-downloads',tag='beta-content-v206-'+'a'.repeat(16);
const context=vm.createContext({Buffer,URL,AbortSignal,process:{env:{}},fetch:async(url,options={})=>{
 calls.push({url:String(url),method:options.method||'GET'});
 let value={};if(String(url).endsWith('/user'))value={login:'luminest-llc'};
 else if(String(url).endsWith('/repos/'+repository))value={full_name:repository,private:false,permissions:{push:true}};
 else if(String(url).includes('/releases/'))value={tag_name:tag,target_commitish:'beta',prerelease:true,draft:false};
 return {ok:true,status:200,json:async()=>value};
}});
const child=new vm.SyntheticModule(['execFileSync'],function(){this.setExport('execFileSync',()=> 'username=luminest-llc\npassword=LOCAL_SCOPE_FIXTURE\n');},{context});
const module=new vm.SourceTextModule(bytes.toString('utf8'),{context});
await module.link(spec=>{if(spec!=='node:child_process')throw Error('Unexpected helper import');return child;});
await module.evaluate();
const gh=await module.namespace.githubExistingAuth();
async function reject(label,action){const n=calls.length;try{await action();throw Error('Unsafe scope accepted: '+label);}catch(e){if(e.message.startsWith('Unsafe scope accepted'))throw e;results.push({label,rejected:true,http_calls:calls.length-n,reason:e.message});}}
const good={tag_name:tag,target_commitish:'beta',prerelease:true,draft:false,make_latest:'false'};
await gh.request('/repos/'+repository+'/releases',{method:'POST',body:good});
await reject('production release branch',()=>gh.request('/repos/'+repository+'/releases',{method:'POST',body:{...good,target_commitish:'main'}}));
await reject('latest release flag',()=>gh.request('/repos/'+repository+'/releases',{method:'POST',body:{...good,make_latest:'true'}}));
await reject('other build release',()=>gh.request('/repos/'+repository+'/releases',{method:'POST',body:{...good,tag_name:'beta-content-v205-'+'a'.repeat(16)}}));
await reject('other repository',()=>gh.request('/repos/other/repository/releases'));
await reject('arbitrary POST',()=>gh.request('/repos/'+repository+'/issues',{method:'POST',body:{}}));
await reject('generic PUT',()=>gh.request('/repos/'+repository+'/contents/x',{method:'PUT',body:{}}));
await reject('APK asset upload',()=>gh.uploadAsset(1,'example.apk',Buffer.from('fixture')));
await reject('production metadata path',()=>gh.putBetaMetadata('patch_version.json',Buffer.from('{"channel":"beta"}'),'a'.repeat(40)));
await reject('non-beta metadata body',()=>gh.putBetaMetadata('channels/beta/patch_version.json',Buffer.from('{"channel":"production"}'),'a'.repeat(40)));
if(results.some(r=>r.http_calls!==0))throw Error('Rejected scope attempted HTTP');
if(hash(fs.readFileSync(helper))!==hash(bytes))throw Error('Existing helper modified');
const report={schema:'ffbe-206-existing-github-helper-local-scope-review-v1',passed:true,network_requests_made:0,remote_mutations_made:0,credentials_read:false,simulation:'Actual unchanged helper evaluated with synthetic credentials and HTTP responses.',helper:{bytes:bytes.length,sha256:hash(bytes)},allowed206prerelease_creation_exercised:true,negative_scope_checks:results,beta_metadata_capability_note:'Existing helper supports three beta metadata paths.206 publisher uses only channels/beta/patch_version.json; publication VM checks the actual call targets.'};
fs.writeFileSync(ROOT+'/audit/GITHUB_HELPER_LOCAL_SCOPE_REVIEW.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,rejected_unsafe_scopes:results.length,network_requests_made:0,credentials_read:false}));
