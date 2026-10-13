// Existing credentials remain in memory. Only exact208 releases and beta updater can change.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {REPO,hash,assert,rangeStarts} from './inputs208.mjs';
export function github208(inputs,mode){
 assert(['assets','stage','promote'].includes(mode),'Explicit208 operation required');
 let raw;
 try{raw=execFileSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\nusername=luminest-llc\n\n',encoding:'utf8',timeout:20000,env:{...process.env,GCM_INTERACTIVE:'Never',GIT_TERMINAL_PROMPT:'0'},stdio:['pipe','pipe','pipe']});}catch{throw Error('Existing publisher credentials unavailable');}
 const credentials=Object.fromEntries(raw.trim().split(/\r?\n/).map(line=>{const n=line.indexOf('=');return [line.slice(0,n),line.slice(n+1)];}));raw=null;
 assert(credentials.username?.toLowerCase()==='luminest-llc'&&credentials.password,'Publisher account differs');
 const headers={Authorization:'Bearer '+credentials.password,'X-GitHub-Api-Version':'2022-11-28',Accept:'application/vnd.github+json','User-Agent':'FFBE-208-Production'};
 const releases=new Map(),prefix='/repos/'+REPO;
 async function request(route,{method='GET',body,allow404=false}={}){
  const tag=mode==='assets'?inputs.download.release_tag:inputs.tag;
  if(method==='GET')assert(body===undefined&&(['/user','', '/git/ref/heads/main','/releases/latest',`/releases/${inputs.protection.latest_release_id}`,'/releases/tags/'+tag,'/contents/channels/beta/patch_version.json?ref=beta'].includes(route)||[...releases.keys()].some(id=>route===`/releases/${id}/assets?per_page=100`||route===`/releases/${id}`)),'Read outside exact208 scope');
  else if(method==='POST')assert(mode!=='promote'&&route==='/releases'&&body?.tag_name===tag&&body?.target_commitish===inputs.protection.main_sha&&body?.draft===false&&body?.prerelease===true&&body?.make_latest==='false'&&body?.generate_release_notes===false,'Only exact nonlatest208 release creation allowed');
  else if(method==='PATCH')assert(mode==='promote'&&releases.get(Number(route.split('/').pop()))===inputs.tag&&route===`/releases/${Number(route.split('/').pop())}`&&JSON.stringify(body)===JSON.stringify({prerelease:false,make_latest:'true'}),'Only qualified208 APK release can become latest');
  else if(method==='PUT'){
   assert(mode==='promote'&&route==='/contents/channels/beta/patch_version.json'&&body?.branch==='beta'&&/^[a-f0-9]{40}$/.test(body.sha||''),'Only canonical beta APK updater may change');
   const value=JSON.parse(Buffer.from(body.content,'base64').toString('utf8'));
   assert(value.channel==='beta'&&value.version===208&&value.versionCode===208&&value.asset_version===208&&value.sha256===inputs.build.sha256&&value.bytes===inputs.build.bytes&&value.url===inputs.url&&value.apk_url===inputs.url,'Beta updater must identify exact208 APK');
  }else throw Error('Unsupported208 remote operation');
  const endpoint=route==='/user'?route:prefix+route;
  const response=await fetch('https://api.github.com'+endpoint,{method,redirect:'error',headers:{...headers,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(60000)});
  if(allow404&&method==='GET'&&response.status===404){await response.body?.cancel();return null;}
  if(!response.ok){await response.body?.cancel();throw Error(`Scoped GitHub ${method}: HTTP ${response.status}`);}return response.json();
 }
 async function authenticate(){const account=await request('/user'),repo=await request('');assert(account.login.toLowerCase()==='luminest-llc'&&repo.full_name.toLowerCase()===REPO&&!repo.private&&repo.permissions?.push,'Established public publisher differs');}
 function register(release,tag){assert(tag===(mode==='assets'?inputs.download.release_tag:inputs.tag)&&release.tag_name===tag&&Number.isSafeInteger(release.id)&&release.draft===false,'Exact release identity differs');releases.set(release.id,tag);}
 async function stageRelease(tag,name,body){
  let release=await request('/releases/tags/'+tag,{allow404:true});
  if(!release)release=await request('/releases',{method:'POST',body:{tag_name:tag,target_commitish:inputs.protection.main_sha,name,body,draft:false,prerelease:true,make_latest:'false',generate_release_notes:false}});
  assert(release.prerelease===true&&release.target_commitish===inputs.protection.main_sha,'Stage release must remain nonlatest prerelease at frozen source');register(release,tag);return release;
 }
 async function upload(release,file,allowedNames){
  assert(releases.get(release.id)===release.tag_name&&allowedNames.includes(file.name)&&/^[A-Za-z0-9._-]+$/.test(file.name),'Upload outside exact208 file allowlist');
  const bytes=fs.readFileSync(file.local_path);assert(bytes.length===file.bytes&&hash(bytes)===file.sha256,'Immutable upload bytes changed');
  const current=await request(`/releases/${release.id}/assets?per_page=100`);assert(Array.isArray(current)&&current.every(asset=>allowedNames.includes(asset.name)),'Unexpected file in exact208 release');
  let asset=current.find(asset=>asset.name===file.name);
  if(!asset){
   const response=await fetch(`https://uploads.github.com/repos/${REPO}/releases/${release.id}/assets?name=${encodeURIComponent(file.name)}`,{method:'POST',redirect:'error',headers:{...headers,'Content-Type':file.name.endsWith('.apk')?'application/vnd.android.package-archive':'application/octet-stream','Content-Length':String(bytes.length)},body:bytes,signal:AbortSignal.timeout(300000)});
   if(!response.ok){await response.body?.cancel();throw Error(`Exact immutable upload HTTP ${response.status}`);}asset=await response.json();
  }
  const url=`https://github.com/${REPO}/releases/download/${release.tag_name}/${file.name}`;
  assert(asset.name===file.name&&asset.size===file.bytes&&asset.state==='uploaded'&&asset.browser_download_url===url&&(!asset.digest||asset.digest==='sha256:'+file.sha256),'Existing/uploaded immutable asset differs');
  return {asset,url,local:bytes};
 }
 return {get:route=>request(route),request,authenticate,register,stageRelease,upload};
}
export async function verifyPublic(file,url,ranged=false){
 // No authenticated header is passed to public downloads or redirects.
 const response=await fetch(url,{method:'GET',headers:{'Accept-Encoding':'identity','Cache-Control':'no-cache'},cache:'no-store',signal:AbortSignal.timeout(180000)});
 assert(response.status===200,'Public immutable208 asset unavailable');
 const digest=crypto.createHash('sha256');let length=0;
 for await(const chunk of response.body){digest.update(chunk);length+=chunk.length;}
 assert(length===file.bytes&&digest.digest('hex')===file.sha256,'Complete public208 asset hash/size differs');
 const ranges=[];
 if(ranged){const local=fs.readFileSync(file.local_path);for(const start of rangeStarts(file.bytes)){
  const end=Math.min(start+65535,file.bytes-1),content_range=`bytes ${start}-${end}/${file.bytes}`;
  const response=await fetch(url,{method:'GET',headers:{Range:`bytes=${start}-${end}`,'Accept-Encoding':'identity','Cache-Control':'no-cache'},cache:'no-store',signal:AbortSignal.timeout(60000)});
  assert(response.status===206&&response.headers.get('content-range')===content_range,'Exact208 range response differs');
  const bytes=Buffer.from(await response.arrayBuffer());assert(bytes.equals(local.subarray(start,end+1)),'Public208 range bytes differ');ranges.push({start,end,content_range,sha256:hash(bytes),verified:true});
 }}
 return {name:file.name,role:file.role,bytes:file.bytes,sha256:file.sha256,url,full_download_verified:true,ranges};
}
