// Reuses the existing publisher account; only one beta updater path can be written.
import {execFileSync} from 'node:child_process';
export const REPOSITORY='luminest-llc/ffbe-memorial-downloads';
export async function githubExistingAuth(){
 let raw;
 try{raw=execFileSync('git',['credential','fill'],{input:'protocol=https\nhost=github.com\nusername=luminest-llc\n\n',encoding:'utf8',timeout:20000,env:{...process.env,GCM_INTERACTIVE:'Never',GIT_TERMINAL_PROMPT:'0'},stdio:['pipe','pipe','pipe']});}
 catch{throw Error('Existing GitHub publisher credentials unavailable.');}
 const saved=Object.fromEntries(raw.trim().split(/\r?\n/).map(l=>{const n=l.indexOf('=');return[l.slice(0,n),l.slice(n+1)];}));
 if(!saved.password||saved.username?.toLowerCase()!=='luminest-llc')throw Error('Wrong existing GitHub account.');
 const headers={Authorization:'Bearer '+saved.password,'X-GitHub-Api-Version':'2022-11-28','User-Agent':'FFBE-Beta-Download-Spacing',Accept:'application/vnd.github+json'};
 async function request(suffix,{method='GET'}={}){
  const allowed=['/user',`/repos/${REPOSITORY}`,`/repos/${REPOSITORY}/git/ref/heads/main`,`/repos/${REPOSITORY}/releases/latest`,`/repos/${REPOSITORY}/contents/channels/beta/patch_version.json?ref=beta`];
  if(method!=='GET'||!allowed.includes(suffix))throw Error('Only the exact publisher and production/updater readback paths are allowed.');
  const r=await fetch('https://api.github.com'+suffix,{method:'GET',redirect:'error',headers,signal:AbortSignal.timeout(60000)});
  if(!r.ok){await r.body?.cancel();throw Error(`GitHub scoped read: HTTP ${r.status}`);}return r.json();
 }
 const me=await request('/user');if(me.login.toLowerCase()!=='luminest-llc')throw Error('Established publisher account differs.');
 const project=await request('/repos/'+REPOSITORY);if(project.full_name.toLowerCase()!==REPOSITORY||project.private||!project.permissions?.push)throw Error('Established writable public repository differs.');
 async function putBetaMetadata(filePath,bytes,previousSHA){
  if(filePath!=='channels/beta/patch_version.json'||bytes.length>16384||!/^[0-9a-f]{40}$/.test(previousSHA))throw Error('Only the pinned beta APK updater can be written.');
  const value=JSON.parse(bytes.toString('utf8'));
  if(value.channel!=='beta'||value.package!=='com.square_enix.ffbejpn'||value.version!==207||value.versionCode!==207||value.asset_version!==206||value.apk_update_enabled!==true||!Array.isArray(value.changelog)||value.changelog.length||!Number.isSafeInteger(value.bytes)||value.bytes<=0||!/^[0-9a-f]{64}$/.test(value.sha256)||value.apk_url!==value.url||!new RegExp('^https://ffbe\\.luminest\\.io/downloads/beta/releases/download-spacing-v207-'+value.sha256.slice(0,16)+'/[A-Za-z0-9._-]+v207\\.apk$').test(value.apk_url))throw Error('Updater exceeds207 APK-only beta scope.');
  const body={message:'Update beta APK to build207 download spacing fix',branch:'beta',sha:previousSHA,content:bytes.toString('base64')};
  const r=await fetch(`https://api.github.com/repos/${REPOSITORY}/contents/${filePath}`,{method:'PUT',redirect:'error',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(60000)});
  if(!r.ok){await r.body?.cancel();throw Error(`Beta APK updater: HTTP ${r.status}`);}const j=await r.json();return {path:filePath,blob_sha:j.content.sha,commit_sha:j.commit.sha};
 }
 return {request,putBetaMetadata,repository:project.full_name,authenticated_login:me.login};
}
