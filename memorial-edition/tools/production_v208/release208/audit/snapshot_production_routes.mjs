// Read-only snapshot of existing production routes; no remote mutation.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {githubExistingAuth,REPOSITORY} from '../../v207-download-spacing/publication/scripts/github_existing_auth.mjs';
const ROOT='S:/FFBE JP Data Export/build/v208-production';
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const urls=[
 'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json',
 'https://cdn.luminest.io/ffbe/patch_version.json',
 'https://ffbe.luminest.io/downloads/',
 'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/content-manifest-v5-r2.json',
 'https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/manifest.json',
 'https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json'
];
const results=await Promise.allSettled(urls.map(async(url,index)=>{
 const response=await fetch(url,{method:'GET',headers:{'Cache-Control':'no-cache','Accept-Encoding':'identity'},cache:'no-store',signal:AbortSignal.timeout(60000)});
 if(index===3&&response.status===404){await response.body?.cancel();return {url,status:404,latest_compatibility_alias_present:false};}
 if(response.status!==200)throw Error(`Read-only snapshot HTTP ${response.status}: ${url}`);
 const bytes=Buffer.from(await response.arrayBuffer());
 const suffix=url.endsWith('/')?'html':'json',path=ROOT+`/audit/current-production-${index}.${suffix}`;
 fs.writeFileSync(path,bytes);
 return {url,status:200,redirect_host:new URL(response.url).host,bytes:bytes.length,sha256:sha(bytes),local_path:path,...(suffix==='json'?{parsed:JSON.parse(bytes)}:{})};
}));
const failure=results.find(result=>result.status==='rejected');if(failure)throw failure.reason;
const gh=await githubExistingAuth();
const latest=await gh.request(`/repos/${REPOSITORY}/releases/latest`),main=await gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`);
const report={schema:'ffbe-v208-current-production-readonly-snapshot-v1',passed:true,time_utc:new Date().toISOString(),network_requested:true,remote_mutations:false,
 files:results.map(result=>result.value),latest:{id:latest.id,tag_name:latest.tag_name,draft:latest.draft,prerelease:latest.prerelease,target_commitish:latest.target_commitish,assets:latest.assets.map(asset=>({id:asset.id,name:asset.name,size:asset.size,browser_download_url:asset.browser_download_url,digest:asset.digest}))},main_sha:main.object.sha};
fs.writeFileSync(ROOT+'/audit/CURRENT_PRODUCTION_ROUTES.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,latest:report.latest,main_sha:report.main_sha,files:report.files.map(({parsed,...file})=>file)}));
