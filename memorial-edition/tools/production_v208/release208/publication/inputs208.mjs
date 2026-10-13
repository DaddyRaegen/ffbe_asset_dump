import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
export const ROOT='S:/FFBE JP Data Export/build/v208-production';
export const DIR=ROOT+'/publication';
export const REPO='luminest-llc/ffbe-memorial-downloads';
export const PACKAGE='com.square_enix.ffbejpn';
export const SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee';
export const BASELINE='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e';
export const MESSAGE='added all the global story events and event battles.';
export const ISSUES=['Overdrive skills crash the game.','dark visions crash the game'];
export const STABLE203='b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8';
export const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
export const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
export const assert=(value,message)=>{if(!value)throw Error(message);};
export const pin=file=>{const bytes=fs.readFileSync(file);return {bytes:bytes.length,sha256:hash(bytes)};};
export const save=(file,value)=>fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n');
function owned(relative){
 assert(typeof relative==='string'&&!path.isAbsolute(relative),'Owned relative input required');
 const file=path.resolve(ROOT,relative),prefix=path.resolve(ROOT)+path.sep;
 assert(file.startsWith(prefix),'Input outside production208 root');return file;
}
export function dataInputs(){
 const cfg=read(DIR+'/config.json');assert(cfg.schema==='ffbe-production208-publication-config-v1','Unexpected208 publisher configuration');
 const downloadPath=owned(cfg.download_plan),download=read(downloadPath);
 assert(download.passed===true&&/^[a-f0-9]{64}$/.test(download.content_catalog_sha256)&&/^[a-f0-9]{64}$/.test(download.side_manifest_sha256),'Passed208 download/catalog/side plan required');
 const planPins={banner_plan_sha256:pin(owned(cfg.banner_plan)).sha256,ordering_plan_sha256:pin(owned(cfg.ordering_plan)).sha256,download_plan_sha256:pin(downloadPath).sha256};
 assert(download.banner_plan_sha256===planPins.banner_plan_sha256&&download.ordering_plan_sha256===planPins.ordering_plan_sha256,'Download plan must bind final banner/order plans');
 assert(download.original_content_rows===1898&&download.final_content_rows===1898&&Array.isArray(download.files)&&download.files.length>=3&&download.files.filter(f=>f.role==='catalog').length===1&&download.files.filter(f=>f.role==='manifest').length===1&&download.files.some(f=>f.role==='pack'),'208 must preserve all1898 native descriptors');
 assert(new Set(download.files.map(file=>file.name)).size===download.files.length,'208 immutable asset names must be unique');
 assert(/^(?:content|production-content|beta-content)-v208-[a-f0-9]{16}$/.test(download.release_tag),'Exact immutable208 data release tag required');
 for(const file of download.files){
  assert(['pack','catalog','manifest'].includes(file.role)&&/^[A-Za-z0-9._-]+$/.test(file.name)&&path.resolve(file.local_path).startsWith(path.resolve(ROOT)+path.sep),'Unapproved new208 publication file');
  const actual=pin(file.local_path);assert(actual.bytes===file.bytes&&actual.sha256===file.sha256,'New208 public data bytes changed');
 }
 const catalog=download.files.find(file=>file.role==='catalog');assert(catalog.sha256===download.content_catalog_sha256,'Published catalog must equal planned native catalog');
 const manifest=read(download.files.find(file=>file.role==='manifest').local_path);
 assert(manifest.asset_version===208&&manifest.APK_min_version===208&&manifest.package===PACKAGE&&manifest.signing_certificate_sha256===SIGNER&&manifest.release_tag===download.release_tag&&manifest.content_catalog?.url===`https://github.com/${REPO}/releases/download/${download.release_tag}/${catalog.name}`&&manifest.content_catalog.sha256===catalog.sha256&&manifest.content_catalog.bytes===catalog.bytes&&manifest.bundled_side_manifest_sha256===download.side_manifest_sha256,'Public208 asset manifest must bind exact package/signer/catalog/side and immutable URLs');
 const transport=read(owned(cfg.transport));assert(transport.passed===true&&transport.content_catalog_sha256===download.content_catalog_sha256&&transport.side_manifest_sha256===download.side_manifest_sha256&&transport.download_plan_sha256===planPins.download_plan_sha256,'Exact independent208 transport gate required');
 const scope=read(ROOT+'/audit/RELEASE_SCOPE.json');assert(scope.explicit_production_promotion_authorized===true&&scope.versionCode===208&&scope.update_message===MESSAGE&&JSON.stringify(scope.known_issues)===JSON.stringify(ISSUES),'Exact user-authorized208 production scope required');
 const snapshot=read(ROOT+'/audit/CURRENT_PRODUCTION_ROUTES.json'),oldUpdater=snapshot.files.find(file=>file.url.endsWith('/releases/latest/download/patch_version.json')).parsed;
 assert(snapshot.passed&&snapshot.latest.tag_name==='patch-5'&&snapshot.latest.id===399650413&&oldUpdater.version===5,'Frozen productionPatch5 baseline differs');
 const protection=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard;
 assert(protection.main_sha===snapshot.main_sha&&protection.latest_release_id===snapshot.latest.id,'Production repository baseline changed');
 return {cfg,download,downloadPath,planPins,transport,scope,snapshot,oldUpdater,protection};
}
export function qualifiedInputs(){
 const inputs=dataInputs(),{cfg,download,planPins}=inputs;
 const build=read(ROOT+'/staged_build/PRODUCTION_APK_BUILD.json'),signed=read(owned(cfg.qualifier));
 assert(build.versionCode===208&&build.package===PACKAGE&&build.signer_sha256===SIGNER&&build.baseline_apk_sha256===BASELINE,'Exact signed208 foundation required');
 assert(path.resolve(build.apk).startsWith(path.resolve(ROOT)+path.sep),'APK outside current208 root');
 const apk=pin(build.apk);assert(apk.bytes===build.bytes&&apk.sha256===build.sha256&&path.basename(build.apk)==='FFBE-Memorial-EN-Global-Events-v208.apk','Current208 APK differs');
 assert(signed.schema==='ffbe-production208-qualification-v1'&&signed.passed===true&&signed.versionCode===208&&signed.apk_sha256===build.sha256&&signed.apk_bytes===build.bytes&&signed.baseline_apk_sha256===BASELINE&&signed.signer_sha256===SIGNER,'Exact independent signed208 qualification required');
 for(const [field,value] of Object.entries(planPins))assert(signed[field]===value,'Qualified208 plan changed: '+field);
 assert(signed.content_catalog_sha256===download.content_catalog_sha256&&signed.side_manifest_sha256===download.side_manifest_sha256,'Qualified208 native metadata differs');
 const tag='production-v208-'+build.sha256.slice(0,16),filename=path.basename(build.apk),url=`https://github.com/${REPO}/releases/download/${tag}/${filename}`;
 return {...inputs,build,signed,tag,filename,url};
}
export function emulatorGate(inputs){
 const file=owned(inputs.cfg.emulator),receipt=read(file);
 assert(receipt.passed===true&&receipt.versionCode===208&&receipt.apk_sha256===inputs.build.sha256&&receipt.apk_bytes===inputs.build.bytes,'Passed exact208 BlueStacks test required before production promotion');
 return {file,receipt,pin:pin(file)};
}
export const rangeStarts=size=>[0,Math.floor(size/2),Math.max(0,size-65536)];
export function rangesGate(file,expected){
 assert(file.ranges?.length===3&&file.ranges.every((r,i)=>r.verified===true&&r.start===rangeStarts(expected.bytes)[i]&&r.end===Math.min(r.start+65535,expected.bytes-1)&&r.content_range===`bytes ${r.start}-${r.end}/${expected.bytes}`),'Exact first/middle/last range evidence required');
}
export function assetsGate(inputs){
 const file=DIR+'/asset-stage-receipt.json',receipt=read(file);
 assert(receipt.success===true&&receipt.versionCode===208&&receipt.release_tag===inputs.download.release_tag&&receipt.download_plan_sha256===inputs.planPins.download_plan_sha256&&receipt.content_catalog_sha256===inputs.download.content_catalog_sha256&&receipt.side_manifest_sha256===inputs.download.side_manifest_sha256,'Verified208 immutable data staging required');
 assert(receipt.files.length===inputs.download.files.length,'Missing208 staged data file');
 for(const expected of inputs.download.files){const actual=receipt.files.find(file=>file.name===expected.name);assert(actual&&actual.bytes===expected.bytes&&actual.sha256===expected.sha256&&actual.full_download_verified===true&&actual.url===`https://github.com/${REPO}/releases/download/${inputs.download.release_tag}/${expected.name}`,'Exact208 data receipt differs');if(expected.role==='pack')rangesGate(actual,expected);}
 return {receipt,pin:pin(file)};
}
export async function publicGET(url){
 const response=await fetch(url,{method:'GET',headers:{'Accept-Encoding':'identity','Cache-Control':'no-cache'},cache:'no-store',signal:AbortSignal.timeout(60000)});
 assert(response.status===200,'Public GET failed: '+new URL(url).pathname);return Buffer.from(await response.arrayBuffer());
}
export async function immutableGuards(inputs,gh){
 const files=inputs.protection.public_files.filter(file=>!['https://github.com/'+REPO+'/releases/latest/download/patch_version.json','https://cdn.luminest.io/ffbe/patch_version.json','https://ffbe.luminest.io/downloads/'].includes(file.url));
 files.push({url:'https://github.com/'+REPO+'/releases/download/patch-5/patch_version.json',bytes:921,sha256:'8deeb621846ec600653294e9888d3ced32207448b277bfdcbbdc082caf12a3e9'});
 const results=await Promise.allSettled(files.map(async file=>{const bytes=await publicGET(file.url);assert(bytes.length===file.bytes&&hash(bytes)===file.sha256,'Immutable historical asset changed');return {...file,unchanged:true};}));
 const protected_files=results.map(result=>{if(result.status==='rejected')throw result.reason;return result.value;});
 const stable=await publicGET(`https://raw.githubusercontent.com/${REPO}/beta/channels/beta/manifest.json`);assert(hash(stable)===STABLE203,'Stable beta203 asset pointer changed');
 const main=await gh.get('/git/ref/heads/main');assert(main.object.sha===inputs.protection.main_sha,'Production main source changed');
 const oldRelease=await gh.get(`/releases/${inputs.protection.latest_release_id}`);
 assert(oldRelease.id===inputs.snapshot.latest.id&&oldRelease.tag_name==='patch-5'&&oldRelease.prerelease===false&&oldRelease.draft===false&&oldRelease.assets.length===inputs.snapshot.latest.assets.length,'Historical Patch5 release changed');
 for(const expected of inputs.snapshot.latest.assets){const asset=oldRelease.assets.find(asset=>asset.name===expected.name);assert(asset&&asset.id===expected.id&&asset.size===expected.size&&asset.browser_download_url===expected.browser_download_url&&asset.digest===expected.digest,'Historical Patch5 APK/metadata asset was replaced or removed');}
 return {protected_files,stable203_sha256:hash(stable),main_sha:main.object.sha,old_patch5_release_id:oldRelease.id,old_patch5_assets_unchanged:true};
}
export async function stageGuards(inputs,gh){
 const immutable=await immutableGuards(inputs,gh),latest=await gh.get('/releases/latest');
 assert(latest.id===inputs.protection.latest_release_id&&latest.tag_name==='patch-5','Staging must not change production latest');
 const files=inputs.protection.public_files.filter(file=>['https://github.com/'+REPO+'/releases/latest/download/patch_version.json','https://cdn.luminest.io/ffbe/patch_version.json','https://ffbe.luminest.io/downloads/'].includes(file.url));
 const results=await Promise.allSettled(files.map(async file=>{const bytes=await publicGET(file.url);assert(bytes.length===file.bytes&&hash(bytes)===file.sha256,'Production changed during staging');return {...file,unchanged:true};}));
 return {...immutable,latest_release_id:latest.id,latest_tag:latest.tag_name,production_files:results.map(result=>{if(result.status==='rejected')throw result.reason;return result.value;})};
}
export function updaterBytes(inputs,channel='production'){
 const alias=`https://github.com/${REPO}/releases/download/${inputs.tag}/event-assets.json`,catalog=`https://github.com/${REPO}/releases/download/${inputs.tag}/content_delivery.tsv`;
 return Buffer.from(JSON.stringify({channel,package:PACKAGE,version:208,versionCode:208,asset_version:208,apk_update_enabled:true,bytes:inputs.build.bytes,sha256:inputs.build.sha256,url:inputs.url,apk_url:inputs.url,changelog:[MESSAGE,...ISSUES],known_issues:ISSUES,released:inputs.scope.release_date||'2026-10-04',content_manifest_url:inputs.oldUpdater.content_manifest_url,base_manifest_url:inputs.oldUpdater.base_manifest_url,event_manifest_url:alias,content_catalog_url:catalog},null,2)+'\n');
}
