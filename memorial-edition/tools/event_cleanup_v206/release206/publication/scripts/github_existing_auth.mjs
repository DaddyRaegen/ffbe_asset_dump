// Reuses only the project's established Git Credential Manager account.
// No token, authenticated headers or signed CDN redirects are returned/logged.
import {execFileSync} from 'node:child_process';
export const REPOSITORY='luminest-llc/ffbe-memorial-downloads';
export async function githubExistingAuth(){
  let raw;
  try { raw=execFileSync('git',['credential','fill'],{
    input:'protocol=https\nhost=github.com\nusername=luminest-llc\n\n',encoding:'utf8',timeout:20000,
    env:{...process.env,GCM_INTERACTIVE:'Never',GIT_TERMINAL_PROMPT:'0'},stdio:['pipe','pipe','pipe'],
  }); } catch { throw Error('Existing GitHub credentials unavailable; no new credential created.'); }
  const saved=Object.fromEntries(raw.trim().split(/\r?\n/).map(l=>{const n=l.indexOf('=');return[l.slice(0,n),l.slice(n+1)];}));
  if(!saved.password||saved.username?.toLowerCase()!=='luminest-llc')throw Error('Wrong existing GitHub account.');
  const headers={Authorization:'Bearer '+saved.password,'X-GitHub-Api-Version':'2022-11-28','User-Agent':'FFBE-Beta-Assets',Accept:'application/vnd.github+json'};
  async function request(suffix,{method='GET',body,allow404=false}={}){
    if(!['GET','POST'].includes(method))throw Error('Only scoped GET and create-only POST are supported; metadata PUT uses a separate narrow function.');
    if(!suffix.startsWith('/repos/'+REPOSITORY+'/')&&suffix!=='/repos/'+REPOSITORY&&suffix!=='/user')throw Error('Unexpected GitHub destination.');
    if(method==='POST'){
      const refCreation=suffix===`/repos/${REPOSITORY}/git/refs`&&body?.ref==='refs/heads/beta'&&body?.sha==='85c4db89497262fbc74c86a1fa31419ce09fb25e';
      const releaseCreation=suffix===`/repos/${REPOSITORY}/releases`&&/^beta-content-v206-[0-9a-f]{16}$/.test(body?.tag_name||'')&&body?.target_commitish==='beta'&&body?.prerelease===true&&body?.make_latest==='false'&&body?.draft===false;
      if(!refCreation&&!releaseCreation)throw Error('Only the exact beta asset ref and prerelease creation are allowed.');
    }
    const r=await fetch('https://api.github.com'+suffix,{method,redirect:'error',headers:{...headers,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(60000)});
    if(r.status===404&&allow404){await r.body?.cancel();return null;}
    if(!r.ok){await r.body?.cancel();throw Error(`GitHub ${method} ${suffix}: HTTP ${r.status}`);}
    return r.json();
  }
  const me=await request('/user');if(me.login.toLowerCase()!=='luminest-llc')throw Error('Authenticated account differs from established publisher.');
  const project=await request('/repos/'+REPOSITORY);
  if(project.full_name.toLowerCase()!==REPOSITORY||project.private||!project.permissions?.push)throw Error('Asset destination is not the established writable public repository.');
  async function uploadAsset(releaseId,name,bytes){
    if(!Number.isSafeInteger(releaseId)||releaseId<=0||!/^[A-Za-z0-9._-]+$/.test(name))throw Error('Unsafe release asset destination.');
    if(/\.(apk|ipa|js|mjs|py|exe|dll|so|dex)$/i.test(name)||bytes.length>128*1024*1024)throw Error('Only bounded data assets are permitted.');
    const release=await request(`/repos/${REPOSITORY}/releases/${releaseId}`);
    if(!/^beta-content-v206-[0-9a-f]{16}$/.test(release.tag_name)||release.target_commitish!=='beta'||release.prerelease!==true||release.draft)throw Error('Upload target is not the scoped beta asset prerelease.');
    const r=await fetch(`https://uploads.github.com/repos/${REPOSITORY}/releases/${releaseId}/assets?name=${encodeURIComponent(name)}`,{
      method:'POST',redirect:'error',headers:{...headers,'Content-Type':'application/octet-stream','Content-Length':String(bytes.length)},body:bytes,signal:AbortSignal.timeout(1800000),
    });
    if(!r.ok){await r.body?.cancel();throw Error(`GitHub asset upload: HTTP ${r.status}. No existing asset was deleted or replaced.`);}
    return r.json();
  }
  async function putBetaMetadata(filePath,bytes,previousSHA){
    if(!['channels/beta/manifest.json','channels/beta/patch_version.json','channels/beta/descriptor.tsv'].includes(filePath))throw Error('Only beta asset metadata paths are allowed.');
    if(bytes.length>16*1024*1024)throw Error('Beta metadata unexpectedly large.');
    if(previousSHA!==null&&!/^[0-9a-f]{40}$/.test(previousSHA))throw Error('Expected previous blob SHA missing or unsafe.');
    if(filePath.endsWith('.json')&&JSON.parse(bytes.toString('utf8')).channel!=='beta')throw Error('Metadata body is not beta.');
    const body={message:'Update beta asset delivery metadata',branch:'beta',content:bytes.toString('base64'),...(previousSHA?{sha:previousSHA}:{})};
    const r=await fetch(`https://api.github.com/repos/${REPOSITORY}/contents/${filePath}`,{
      method:'PUT',redirect:'error',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(60000),
    });
    if(!r.ok){await r.body?.cancel();throw Error(`Beta metadata update: HTTP ${r.status}. Production was not targeted.`);}
    const j=await r.json();return {path:filePath,blob_sha:j.content.sha,commit_sha:j.commit.sha};
  }
  return {request,uploadAsset,putBetaMetadata,repository:project.full_name,authenticated_login:me.login};
}
