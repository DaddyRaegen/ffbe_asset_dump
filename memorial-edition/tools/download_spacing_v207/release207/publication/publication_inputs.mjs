import fs from 'node:fs';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
export const ROOT='S:/FFBE JP Data Export/build/v207-download-spacing';
export const DIR=ROOT+'/publication';
export const PREVIOUS='S:/FFBE JP Data Export/build/v206-event-cleanup';
export const FROZEN=DIR+'/frozen206';
export const BASELINE206_SHA='345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d';
export const FROZEN206_PINS_SHA='d3f42096704c38f88b90aeea31cb44db85940775a80e827fd0a78dffbc3b1d9a';
export const STABLE203_SHA='b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8';
export const SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee';
export const CATALOG_SHA='963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a';
export const SIDE_SHA='0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14';
export const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
export const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
export const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
export const assert=(v,m)=>{if(!v)throw Error(m);};
export const pin=p=>{const b=fs.readFileSync(p);return {bytes:b.length,sha256:hash(b)};};
export function frozenInputs(){
 assert(pin(FROZEN+'/pins.json').sha256===FROZEN206_PINS_SHA,'Frozen206 input pins changed');
 const pins=read(FROZEN+'/pins.json');
 for(const [name,expected] of Object.entries(pins.files)){const actual=pin(FROZEN+'/'+name);assert(actual.bytes===expected.bytes&&actual.sha256===expected.sha256,'Frozen206 publication input changed');}
 const previousReceipt=read(FROZEN+'/activation-receipt.json'),previousPlan=read(FROZEN+'/plan.json'),download=read(FROZEN+'/DOWNLOAD_PLAN.json'),assets=read(FROZEN+'/asset-receipt.json'),signed206=read(FROZEN+'/SIGNED_EVENT_QUALIFICATION.json');
 assert(previousReceipt.success&&previousReceipt.versionCode===206&&previousReceipt.sha256===BASELINE206_SHA&&previousReceipt.bytes===145206221&&previousReceipt.page.sha256===pin(FROZEN+'/index.html').sha256&&previousReceipt.pointer.sha256===pin(FROZEN+'/patch_version.json').sha256,'Published206 receipt/page/updater pins differ');
 assert(signed206.passed&&signed206.apk_sha256===BASELINE206_SHA&&signed206.content_catalog_sha256===CATALOG_SHA&&signed206.side_manifest_sha256===SIDE_SHA,'Published206 qualification differs');
 assert(download.passed&&download.content_catalog_sha256===CATALOG_SHA&&download.side_manifest_sha256===SIDE_SHA&&download.original_content_rows===1898&&download.final_content_rows===1898&&assets.success&&assets.release_tag===download.release_tag&&previousReceipt.event_release===download.release_tag,'Existing206 asset publication differs');
 for(const file of download.files){const actual=pin(file.local_path);assert(actual.bytes===file.bytes&&actual.sha256===file.sha256,'Existing206 GitHub data bytes changed');}
 const protection=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard;
 assert(JSON.stringify(protection)===JSON.stringify(previousPlan.production_guard),'Production protection pins differ');
 return {previousReceipt,previousPlan,download,assets,signed206,protection};
}
export function qualifiedInputs(){
 const frozen=frozenInputs(),build=read(ROOT+'/staged_build/DOWNLOAD_SPACING_APK_BUILD.json'),signed=read(ROOT+'/staged_build/SIGNED_SPACING_QUALIFICATION.json'),spacing=read(ROOT+'/audit/DOWNLOAD_SPACING_PLAN.json');
 assert(build.versionCode===207&&build.package==='com.square_enix.ffbejpn'&&build.signer_sha256===SIGNER&&build.baseline_apk_sha256===BASELINE206_SHA&&build.runtime_verified===false,'Exact207 signed206 foundation required');
 const apk=pin(build.apk);assert(apk.bytes===build.bytes&&apk.sha256===build.sha256,'Qualified207 APK changed');
 assert(signed.passed&&signed.versionCode===207&&signed.apk_sha256===build.sha256&&signed.apk_bytes===build.bytes&&signed.baseline_apk_sha256===BASELINE206_SHA&&signed.expected_js_delta_passed===true&&signed.spacing_plan_sha256===pin(ROOT+'/audit/DOWNLOAD_SPACING_PLAN.json').sha256,'Exact207 signed spacing qualification required');
 const changedPaths=signed.changed_members.map(member=>typeof member==='string'?member:member.path);
 assert(JSON.stringify(changedPaths.sort())===JSON.stringify(['AndroidManifest.xml','assets/frida_script.js'])&&signed.content_catalog_sha256===CATALOG_SHA&&signed.side_manifest_sha256===SIDE_SHA,'207 exceeds spacing-only APK scope');
 const local=JSON.parse(execFileSync('C:/Users/Raegen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',['-B',DIR+'/verify_apk_delta.py'],{encoding:'utf8',timeout:120000,maxBuffer:1024*1024}));
 assert(local.passed&&local.apk_sha256===build.sha256&&local.apk_bytes===build.bytes&&local.expected_js_delta_passed&&local.content_catalog_sha256===CATALOG_SHA&&local.side_manifest_sha256===SIDE_SHA&&local.spacing_plan_sha256===signed.spacing_plan_sha256,'Independent207 member/script delta differs');
 return {...frozen,build,signed,spacing,local};
}
