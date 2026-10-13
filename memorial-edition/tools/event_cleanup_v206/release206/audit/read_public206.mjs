// Read-only independent publication check. Every remote request is GET.
// The existing account helper is used solely for protected repository reads.
import fs from 'node:fs';
import crypto from 'node:crypto';
import zlib from 'node:zlib';
import {githubExistingAuth,REPOSITORY} from '../publication/scripts/github_existing_auth.mjs';

const ROOT='S:/FFBE JP Data Export/build/v206-event-cleanup';
const EXPECTED_APK_SHA='345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d';
const EXPECTED_CATALOG_SHA='963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a';
const EXPECTED_SIDE_SHA='0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14';
const STABLE203_SHA='b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8';
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const require=(ok,message)=>{if(!ok)throw Error(message);};
const report={schema:'ffbe-public206-independent-review-v1',passed:false,network_requested:true,
  remote_mutations:false,device_actions:false,runtime_verified:false,requests:[]};
require(process.argv.length===3&&process.argv[2]==='--verify-published','Explicit --verify-published is required after activation.');

async function get(url,range=null){
  const headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'};
  if(range)headers.Range=`bytes=${range.start}-${range.end}`;
  const r=await fetch(url,{method:'GET',headers,cache:'no-store',signal:AbortSignal.timeout(180000)});
  require(r.status===(range?206:200),`Public GET returned HTTP ${r.status}: ${url}`);
  if(range)require(r.headers.get('content-range')===`bytes ${range.start}-${range.end}/${range.total}`,`Public range header differs: ${url}`);
  const bytes=Buffer.from(await r.arrayBuffer());
  if(range)require(bytes.length===range.end-range.start+1,`Public range length differs: ${url}`);
  report.requests.push({url,status:r.status,bytes:bytes.length,...(range?{range:{start:range.start,end:range.end,total:range.total}}:{})});
  return bytes;
}

function parseCatalog(blob){
  const lines=blob.toString('utf8').trimEnd().split('\n');require(lines.shift()==='ffbe-content-v1','Public catalog header differs');
  const rows=new Map();
  for(const line of lines){const p=line.split('\t');require(p.length===8&&!rows.has(p[0]),'Public catalog duplicate or field count');
    rows.set(p[0],{path:p[0],sha256:p[1],bytes:Number(p[2]),url:p[3],offset:Number(p[4]),wire:Number(p[5]),method:Number(p[6]),source:Number(p[7]),line});}
  return rows;
}

async function main(){
  const activation=read(ROOT+'/publication/activation-receipt.json');
  require(activation.success&&activation.versionCode===206&&activation.sha256===EXPECTED_APK_SHA,'Publication is not confirmed for the exact206 APK.');
  const plan=read(ROOT+'/publication/plan.json'),download=read(ROOT+'/asset_publication/DOWNLOAD_PLAN.json');
  const signed=read(ROOT+'/staged_build/SIGNED_EVENT_QUALIFICATION.json');
  require(plan.versionCode===206&&plan.sha256===EXPECTED_APK_SHA&&plan.bytes===145206221&&signed.passed&&signed.apk_sha256===EXPECTED_APK_SHA
    &&signed.manifest.before===205&&signed.manifest.after===206&&signed.manifest.typed_four_byte_value_only===true,'Exact206 local qualification/version differs');
  require(plan.event_catalog_sha256===EXPECTED_CATALOG_SHA&&download.content_catalog_sha256===EXPECTED_CATALOG_SHA&&download.side_manifest_sha256===EXPECTED_SIDE_SHA,'Exact206 metadata pin differs');
  const protectedPlan=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard;
  require(JSON.stringify(protectedPlan)===JSON.stringify(plan.production_guard),'Production protection plan differs');
  const apk=fs.readFileSync(plan.apk);require(apk.length===plan.bytes&&sha(apk)===EXPECTED_APK_SHA,'Local qualified206 APK changed');
  const publicAPK=await get(plan.apk_url);require(publicAPK.equals(apk),'Full public APK bytes differ from signed206');
  const apkRanges=[];
  for(const start of [0,Math.floor(apk.length/2),apk.length-65536]){
    const end=Math.min(start+65535,apk.length-1);const bytes=await get(plan.apk_url,{start,end,total:apk.length});
    require(bytes.equals(apk.subarray(start,end+1)),'Public APK first/middle/last bytes differ');apkRanges.push({start,end,bytes:bytes.length,sha256:sha(bytes),verified:true});
  }
  report.apk={url:plan.apk_url,versionCode:206,bytes:publicAPK.length,sha256:sha(publicAPK),full_signed_bytes_identical:true,ranges:apkRanges};
  console.log(JSON.stringify({verified:'signed206 APK full bytes and three ranges',bytes:apk.length}));

  const pageURL='https://ffbe.luminest.io/downloads/beta/',page=await get(pageURL),localPage=fs.readFileSync(ROOT+'/publication/site/index.html');
  require(page.equals(localPage),'Public beta page differs from prepared206 page');
  const links=[...page.toString('utf8').matchAll(/href="([^\"]+\.apk)"/g)].map(m=>m[1]);
  const prior=read(ROOT+'/publication/site/page-plan.json').previous_APK_downloads;
  require(links.length===8&&new Set(links).size===8&&links.includes(plan.apk_url)&&prior.length===7&&prior.every(url=>links.includes(url)),'Public beta eight APK links do not preserve all previous seven');
  require(page.includes(Buffer.from('<h1>Try build 206</h1>')),'Public beta206 heading missing');
  report.page={url:pageURL,sha256:sha(page),all_prepared_bytes_identical:true,APK_links:links,prior_seven_downloads_preserved:true};

  const updaterURL=`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/patch_version.json`;
  const updaterBytes=await get(updaterURL),updater=JSON.parse(updaterBytes),localUpdater=fs.readFileSync(ROOT+'/publication/site/patch_version.json');
  require(updaterBytes.equals(localUpdater),'Public updater bytes differ from prepared206 pointer');
  require(updater.version===206&&updater.versionCode===206&&updater.asset_version===206&&updater.apk_update_enabled===true&&updater.channel==='beta'&&updater.package==='com.square_enix.ffbejpn','Public updater version/channel/package differs');
  require(updater.url===plan.apk_url&&updater.apk_url===plan.apk_url&&updater.sha256===EXPECTED_APK_SHA&&updater.bytes===apk.length,'Public updater URLs/hash/size differ');
  require(Array.isArray(updater.changelog)&&updater.changelog.length===0,'Public updater changelog must remain empty');
  report.updater={url:updaterURL,sha256:sha(updaterBytes),version:206,versionCode:206,asset_version:206,both_APK_URLs_verified:true,changelog:[]};
  const releaseURL='https://ffbe.luminest.io/'+plan.prefix+'release.json';
  const release=await get(releaseURL);require(release.equals(fs.readFileSync(ROOT+'/publication/site/release.json')),'Public release details differ');
  const checksum=await get('https://ffbe.luminest.io/'+plan.prefix+'checksums.txt');require(checksum.equals(fs.readFileSync(ROOT+'/publication/site/checksums.txt')),'Public checksum differs');
  const checklistURL='https://ffbe.luminest.io/'+plan.prefix+'phone-test-checklist.txt';
  const checklist=await get(checklistURL);require(checklist.equals(fs.readFileSync(ROOT+'/publication/site/phone-test-checklist.txt')),'Public phone-test checklist differs');
  report.release_metadata={url:releaseURL,sha256:sha(release),checksum_sha256:sha(checksum),checklist_url:checklistURL,
    checklist_sha256:sha(checklist),exact_prepared_bytes:true};
  console.log(JSON.stringify({verified:'beta206 page, eight APK links, updater and release details'}));

  const publicFiles=new Map();
  for(const item of download.files){
    const url=`https://github.com/${REPOSITORY}/releases/download/${download.release_tag}/${item.name}`;
    const bytes=await get(url),local=fs.readFileSync(item.local_path);
    require(bytes.equals(local)&&bytes.length===item.bytes&&sha(bytes)===item.sha256,'Full public206 asset publication bytes differ');
    publicFiles.set(item.role,{item,url,bytes});
  }
  const catalog=parseCatalog(publicFiles.get('catalog').bytes),manifest=JSON.parse(publicFiles.get('manifest').bytes);
  require(catalog.size===1898&&manifest.assets.length===1898&&manifest.content_catalog.sha256===EXPECTED_CATALOG_SHA&&manifest.bundled_side_manifest_sha256===EXPECTED_SIDE_SHA,'Public asset manifest/catalog identity differs');
  const pack=publicFiles.get('pack'),slices=[];
  for(const item of download.new_pack_files){
    const row=catalog.get(item.path);require(row&&row.method===8&&row.url===pack.url&&row.source===pack.bytes.length,'Public catalog packed source differs');
    const start=row.offset,end=start+row.wire-1;
    const wire=await get(row.url,{start,end,total:pack.bytes.length});
    require(wire.equals(pack.bytes.subarray(start,end+1))&&sha(wire)===item.wire_sha256,'Public event range wire bytes differ');
    const inflated=zlib.inflateRawSync(wire,{info:true});
    require(inflated.engine.bytesWritten===wire.length,'Public raw-deflate slice has trailing/unconsumed data');
    const raw=inflated.buffer,local=fs.readFileSync(ROOT+'/payload/'+item.path);
    require(raw.equals(local)&&raw.length===row.bytes&&sha(raw)===row.sha256,'Public event range raw bytes differ from prepared206 payload');
    slices.push({path:item.path,url:row.url,start,end,wire_bytes:wire.length,wire_sha256:sha(wire),raw_bytes:raw.length,raw_sha256:sha(raw),exact_prepared_raw_bytes:true});
  }
  require(slices.length===5,'Expected five public206 event ranges');
  const host=read(ROOT+'/audit/ACTUAL206_CATALOG_HOST_ADMISSION.json');
  require(host.passed&&host.apk_sha256===EXPECTED_APK_SHA&&host.catalog_sha256===EXPECTED_CATALOG_SHA,'Exact signed206 host qualification differs');
  const baseline=fs.readFileSync(host.work_directory+'/baseline205/content_delivery.tsv');
  require(sha(baseline)==='5c9947b79a60f8a07914ab70d75080939034993fda3891626b0b762438037415','Exact205 baseline catalog differs');
  const old=parseCatalog(baseline),changed=new Set(slices.map(s=>s.path));
  require(JSON.stringify([...old.keys()])===JSON.stringify([...catalog.keys()]),'Public catalog logical paths/order changed');
  let unchanged=0;
  for(const [name,row] of catalog)if(!changed.has(name)){require(row.line===old.get(name).line,'Public unrelated205 transport descriptor changed');unchanged++;}
  require(unchanged===1893,'Expected1893 unchanged public transport descriptors');
  report.event_assets={release_tag:download.release_tag,files:[...publicFiles.values()].map(f=>({role:f.item.role,url:f.url,bytes:f.bytes.length,sha256:sha(f.bytes),full_GET_byte_identical:true})),
    catalog_rows:catalog.size,new_paths:0,unchanged205_descriptors:unchanged,exact_public_deflate_slices:slices};
  console.log(JSON.stringify({verified:'three immutable206 data files and five independent packed ranges',unchanged_descriptors:unchanged}));

  require(protectedPlan.public_files.length===6,'Expected six frozen production/legacy public sources');
  const protections=await Promise.allSettled(protectedPlan.public_files.map(async f=>{
    const bytes=await get(f.url);require(bytes.length===f.bytes&&sha(bytes)===f.sha256,'Protected public production/legacy file changed');
    return {url:f.url,bytes:bytes.length,sha256:sha(bytes),unchanged:true};
  }));
  report.protected_public_files=protections.map(r=>{if(r.status==='rejected')throw r.reason;return r.value;});
  const stableURL=`https://raw.githubusercontent.com/${REPOSITORY}/beta/channels/beta/manifest.json`;
  const stable=await get(stableURL);require(sha(stable)===STABLE203_SHA,'Stable203 beta asset pointer changed');
  report.stable203_asset_pointer={url:stableURL,bytes:stable.length,sha256:sha(stable),unchanged:true};
  // Existing helper authenticates the established account without returning or
  // logging credentials. This checker invokes its request function only as GET.
  const gh=await githubExistingAuth();
  const [mainRef,latest]=await Promise.all([
    gh.request(`/repos/${REPOSITORY}/git/ref/heads/main`),gh.request(`/repos/${REPOSITORY}/releases/latest`)]);
  require(mainRef.object.sha===protectedPlan.main_sha&&latest.id===protectedPlan.latest_release_id&&latest.tag_name===protectedPlan.latest_tag,'Protected main/latest repository state changed');
  report.production_repository={main_sha:mainRef.object.sha,latest_release_id:latest.id,latest_tag:latest.tag_name,unchanged:true,method:'GET through existing established-account helper'};
  report.apk_sha256=EXPECTED_APK_SHA;report.apk_bytes=apk.length;report.versionCode=206;
  report.content_catalog_sha256=EXPECTED_CATALOG_SHA;report.side_manifest_sha256=EXPECTED_SIDE_SHA;
  report.source_manifest_sha256=sha(publicFiles.get('manifest').bytes);report.new_pack_sha256=sha(pack.bytes);
  report.independent_local_signed_qualification_sha256=sha(fs.readFileSync(ROOT+'/staged_build/SIGNED_EVENT_QUALIFICATION.json'));
  report.passed=true;
  console.log(JSON.stringify({verified:'six protected public files, main/latest and stable203 pointer'}));
}

try{await main();}catch(error){report.failure=error.message;}
report.time_utc=new Date().toISOString();report.checker_sha256=sha(fs.readFileSync(new URL(import.meta.url)));
fs.writeFileSync(ROOT+'/audit/PUBLIC_V206_REVIEW.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,report:ROOT+'/audit/PUBLIC_V206_REVIEW.json',failure:report.failure||null}));
if(!report.passed)process.exitCode=1;
