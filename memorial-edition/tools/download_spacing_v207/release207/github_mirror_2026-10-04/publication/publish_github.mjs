// Mirror the qualified APK; no APK, event assets, source branch or production edits.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';

const ROOT='S:/FFBE JP Data Export/build/v207-github-mirror';
const BASE='S:/FFBE JP Data Export/build/v207-download-spacing';
const REPO='luminest-llc/ffbe-memorial-downloads';
const TAG='beta-apk-v207-d9181ffc05fa11e1';
const NAME='FFBE-Memorial-EN-Download-Spacing-v207.apk';
const SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e';
const SIZE=145206221;
const URL=`https://github.com/${REPO}/releases/download/${TAG}/${NAME}`;
const CHECKLIST='https://ffbe.luminest.io/downloads/beta/releases/download-spacing-v207-d9181ffc05fa11e1/phone-test-checklist.txt';
const PREFIX=`/repos/${REPO}`;
const mode=process.argv[2];
const assert=(value,message)=>{if(!value)throw Error(message);};
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const read=path=>JSON.parse(fs.readFileSync(path,'utf8'));
const save=(name,value)=>fs.writeFileSync(`${ROOT}/publication/${name}`,JSON.stringify(value,null,2)+'\n');
assert(process.argv.length===3&&['--upload','--activate-updater'].includes(mode),'Exact mirror operation required');
fs.mkdirSync(ROOT+'/publication',{recursive:true});
const plan=read(BASE+'/publication/plan.json'),activation=read(BASE+'/publication/activation-receipt.json');
const publicBytes=fs.readFileSync(BASE+'/audit/PUBLIC_V207_REVIEW.json');
const published=JSON.parse(publicBytes);
assert(sha(publicBytes)==='c56eced2b2690a969babbeacd036315e676fe66a401bae2512abf437c6097f9f'&&published.passed&&published.apk_sha256===SHA,'Qualified207 public readback changed');
assert(plan.sha256===SHA&&plan.bytes===SIZE&&plan.versionCode===207&&plan.asset_version===206&&activation.success&&activation.sha256===SHA&&activation.bytes===SIZE,'Original207 publication differs');
const apk=fs.readFileSync(plan.apk);
assert(apk.length===SIZE&&sha(apk)===SHA,'Only the already-qualified207 APK may be mirrored');

let raw;
try{raw=execFileSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\nusername=luminest-llc\n\n',encoding:'utf8',timeout:20000,env:{...process.env,GCM_INTERACTIVE:'Never',GIT_TERMINAL_PROMPT:'0'},stdio:['pipe','pipe','pipe']});}
catch{throw Error('Existing publisher credentials unavailable');}
const credentials=Object.fromEntries(raw.trim().split(/\r?\n/).map(line=>{const n=line.indexOf('=');return[line.slice(0,n),line.slice(n+1)];}));
assert(credentials.username?.toLowerCase()==='luminest-llc'&&credentials.password,'Existing publisher account differs');
const headers={Authorization:'Bearer '+credentials.password,'X-GitHub-Api-Version':'2022-11-28',Accept:'application/vnd.github+json','User-Agent':'FFBE-207-GitHub-Mirror'};
let releaseId=null;
const readPaths=['/user',PREFIX,PREFIX+'/git/ref/heads/main',PREFIX+'/git/ref/heads/beta',PREFIX+'/releases/latest',PREFIX+'/releases/tags/'+TAG,PREFIX+'/contents/channels/beta/patch_version.json?ref=beta'];
async function api(path,{method='GET',body,allow404=false}={}){
 if(method==='GET')assert(body===undefined&&(readPaths.includes(path)||path===PREFIX+`/releases/${releaseId}/assets?per_page=100`&&Number.isSafeInteger(releaseId)),'Read outside exact mirror scope');
 else if(method==='POST')assert(mode==='--upload'&&path===PREFIX+'/releases'&&body?.tag_name===TAG&&/^[0-9a-f]{40}$/.test(body?.target_commitish||'')&&body?.draft===false&&body?.prerelease===true&&body?.make_latest==='false'&&!body?.generate_release_notes,'Release exceeds exact beta mirror scope');
 else if(method==='PUT')assert(mode==='--activate-updater'&&path===PREFIX+'/contents/channels/beta/patch_version.json'&&body?.branch==='beta'&&/^[0-9a-f]{40}$/.test(body?.sha||''),'Only canonical beta updater may change');
 else throw Error('Unsupported remote mutation');
 const response=await fetch('https://api.github.com'+path,{method,redirect:'error',headers:{...headers,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(60000)});
 if(allow404&&method==='GET'&&response.status===404){await response.body?.cancel();return null;}
 if(!response.ok){await response.body?.cancel();throw Error(`Scoped GitHub ${method}: HTTP ${response.status}`);}
 return response.json();
}
const account=await api('/user'),project=await api(PREFIX);
assert(account.login.toLowerCase()==='luminest-llc'&&project.full_name.toLowerCase()===REPO&&!project.private&&project.permissions?.push,'Established writable public publisher differs');
async function getPublic(url){const response=await fetch(url,{headers:{'Accept-Encoding':'identity','Cache-Control':'no-cache'},cache:'no-store',signal:AbortSignal.timeout(60000)});assert(response.ok,'Protected public readback failed');return Buffer.from(await response.arrayBuffer());}
async function productionGuard(){
 const main=await api(PREFIX+'/git/ref/heads/main'),latest=await api(PREFIX+'/releases/latest');
 assert(main.object.sha===plan.production_guard.main_sha&&latest.id===plan.production_guard.latest_release_id&&latest.tag_name===plan.production_guard.latest_tag,'Production repository differs');
 const results=await Promise.allSettled(plan.production_guard.public_files.map(async file=>{const bytes=await getPublic(file.url);assert(bytes.length===file.bytes&&sha(bytes)===file.sha256,'Protected production/legacy download differs');return {url:file.url,sha256:sha(bytes),bytes:bytes.length,unchanged:true};}));
 const files=results.map(result=>{if(result.status==='rejected')throw result.reason;return result.value;});
 return {main_sha:main.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name,files};
}
const before=await productionGuard();
if(mode==='--upload'){
 const beta=await api(PREFIX+'/git/ref/heads/beta');
 let release=await api(PREFIX+'/releases/tags/'+TAG,{allow404:true});
 if(!release){
  release=await api(PREFIX+'/releases',{method:'POST',body:{tag_name:TAG,target_commitish:beta.object.sha,name:'FFBE Memorial — build207 beta APK',body:`GitHub mirror of the exact published build207 download spacing fix. Existing build206 events and assets are retained.\n\nVersionCode: 207 / versionName: 11.1.1\nSize: ${SIZE} bytes\nSHA-256: ${SHA}\n\nPhone/runtime and saves are pending for this exact APK. Install over the existing app and keep data. Check download spacing and saves. [Phone checklist and inherited known limits](${CHECKLIST}).\n\nProduction remains Patch 5.`,draft:false,prerelease:true,make_latest:'false',generate_release_notes:false}});
 }
 assert(release.tag_name===TAG&&release.prerelease===true&&release.draft===false&&Number.isSafeInteger(release.id),'Exact beta APK release differs');
 releaseId=release.id;
 save('release-stage.json',{release_id:releaseId,release_tag:TAG,prerelease:true,make_latest:false,target_commitish:release.target_commitish,APK_published:false});
 const existing=await api(PREFIX+`/releases/${releaseId}/assets?per_page=100`);
 assert(Array.isArray(existing)&&existing.every(asset=>asset.name===NAME),'Unexpected asset in APK-only mirror release');
 let asset=existing.find(asset=>asset.name===NAME);
 if(!asset){
  const response=await fetch(`https://uploads.github.com/repos/${REPO}/releases/${releaseId}/assets?name=${encodeURIComponent(NAME)}`,{method:'POST',redirect:'error',headers:{...headers,'Content-Type':'application/vnd.android.package-archive','Content-Length':String(SIZE)},body:apk,signal:AbortSignal.timeout(300000)});
  if(!response.ok){await response.body?.cancel();throw Error(`Exact APK upload: HTTP ${response.status}`);}
  asset=await response.json();
 }
 assert(asset.name===NAME&&asset.size===SIZE&&asset.state==='uploaded'&&asset.browser_download_url===URL&&(!asset.digest||asset.digest==='sha256:'+SHA),'GitHub APK identity differs');
 console.log(JSON.stringify({uploaded:true,release_id:releaseId,bytes:SIZE,verifying_public_download:true}));
 // Public redirects intentionally carry no publisher credentials.
 const response=await fetch(URL,{headers:{'Accept-Encoding':'identity','Cache-Control':'no-cache'},cache:'no-store',signal:AbortSignal.timeout(180000)});
 assert(response.status===200,'Public GitHub APK unavailable');
 const hash=crypto.createHash('sha256');let length=0;
 for await(const chunk of response.body){hash.update(chunk);length+=chunk.length;}
 assert(length===SIZE&&hash.digest('hex')===SHA,'Complete GitHub APK hash/size differs');
 const ranges=[];
 for(const start of [0,Math.floor(SIZE/2),SIZE-65536]){
  const end=Math.min(start+65535,SIZE-1);
  const response=await fetch(URL,{headers:{Range:`bytes=${start}-${end}`,'Accept-Encoding':'identity','Cache-Control':'no-cache'},cache:'no-store',signal:AbortSignal.timeout(60000)});
  assert(response.status===206&&response.headers.get('content-range')===`bytes ${start}-${end}/${SIZE}`,'GitHub APK exact range header differs');
  const bytes=Buffer.from(await response.arrayBuffer());assert(bytes.equals(apk.subarray(start,end+1)),'GitHub APK range bytes differ');
  ranges.push({start,end,verified:true,sha256:sha(bytes)});
 }
 const after=await productionGuard();
 save('github-apk-receipt.json',{success:true,APK_published:true,versionCode:207,versionName:'11.1.1',bytes:SIZE,sha256:SHA,url:URL,release_tag:TAG,release_id:releaseId,asset_id:asset.id,prerelease:true,make_latest:false,full_download_verified:true,ranges,original_apk_url:plan.apk_url,original_public_review_sha256:sha(publicBytes),APK_modified:false,event_assets_modified:false,new_asset_uploads:0,production_before:before,production_after:after,physical_phone_test:'pending',runtime_verified:false,completed_at:new Date().toISOString()});
 console.log(JSON.stringify({success:true,url:URL,bytes:SIZE,sha256:SHA,full_download_verified:true,ranges_verified:ranges.length}));
}else{
 const receipt=read(ROOT+'/publication/github-apk-receipt.json');
 assert(receipt.success&&receipt.versionCode===207&&receipt.url===URL&&receipt.sha256===SHA&&receipt.bytes===SIZE&&receipt.prerelease===true&&receipt.full_download_verified&&receipt.ranges?.length===3&&receipt.ranges.every(range=>range.verified),'Verified GitHub APK missing');
 const file=await api(PREFIX+'/contents/channels/beta/patch_version.json?ref=beta');
 const previous=Buffer.from((file.content||'').replace(/\s/g,''),'base64');
 const value=JSON.parse(previous.toString('utf8'));
 assert(value.channel==='beta'&&value.package==='com.square_enix.ffbejpn'&&value.version===207&&value.versionCode===207&&value.asset_version===206&&value.bytes===SIZE&&value.sha256===SHA&&value.apk_update_enabled===true&&Array.isArray(value.changelog)&&value.changelog.length===0,'Current207 beta updater differs');
 const updated={...value,apk_url:URL,url:URL},bytes=Buffer.from(JSON.stringify(updated,null,2)+'\n');
 const same=previous.equals(bytes);
 assert(same||(sha(previous)===activation.pointer.sha256&&value.apk_url===plan.apk_url&&value.url===plan.apk_url),'Beta updater changed concurrently');
 let pointer={path:'channels/beta/patch_version.json',blob_sha:file.sha,reused:true};
 if(!same){
  const result=await api(PREFIX+'/contents/channels/beta/patch_version.json',{method:'PUT',body:{message:'Use verified GitHub mirror for beta build207 APK',branch:'beta',sha:file.sha,content:bytes.toString('base64')}});
  pointer={path:'channels/beta/patch_version.json',blob_sha:result.content.sha,commit_sha:result.commit.sha};
 }
 const updaterURL=`https://raw.githubusercontent.com/${REPO}/beta/channels/beta/patch_version.json`;
 save('updater-progress.json',{pointer,url:updaterURL,sha256:sha(bytes),public_verified:false});
 let verified=false;
 for(let attempt=0;attempt<60;attempt++){
  if((await getPublic(updaterURL)).equals(bytes)){verified=true;break;}
  if(attempt%6===0)console.log(JSON.stringify({waiting_for_beta_updater_cache:true,attempt:attempt+1}));
  await new Promise(resolve=>setTimeout(resolve,10000));
 }
 assert(verified,'Public GitHub207 updater readback differs');
 save('github-updater-receipt.json',{success:true,versionCode:207,asset_version:206,apk_url:URL,url:URL,bytes:SIZE,sha256:SHA,updater:{...pointer,url:updaterURL,sha256:sha(bytes),full_download_verified:true},previous_sha256:sha(previous),only_apk_urls_changed:true,production_before:before,production_after:await productionGuard(),physical_phone_test:'pending',completed_at:new Date().toISOString()});
 fs.writeFileSync(ROOT+'/publication/patch_version.json',bytes);
 console.log(JSON.stringify({success:true,beta_updater_uses_GitHub:true,versionCode:207,asset_version:206}));
}
