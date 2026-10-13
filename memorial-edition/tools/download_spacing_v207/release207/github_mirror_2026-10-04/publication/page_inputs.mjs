import fs from 'node:fs';
import crypto from 'node:crypto';
export const ROOT='S:/FFBE JP Data Export/build/v207-github-mirror';
export const DIR=ROOT+'/publication';
export const FROZEN=DIR+'/frozen207';
export const APK_SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e';
export const APK_BYTES=145206221;
export const RELEASE_TAG='beta-apk-v207-d9181ffc05fa11e1';
export const GITHUB_URL=`https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/${RELEASE_TAG}/FFBE-Memorial-EN-Download-Spacing-v207.apk`;
export const LUMINEST_URL='https://ffbe.luminest.io/downloads/beta/releases/download-spacing-v207-d9181ffc05fa11e1/FFBE-Memorial-EN-Download-Spacing-v207.apk';
export const STABLE203_SHA='b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8';
export const FROZEN_PINS_SHA='af6f713042b6fe51a90b18652e6105f04094ddb94156e900698f5efc4eabf00c';
export const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
export const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
export const assert=(v,m)=>{if(!v)throw Error(m);};
export const save=(p,v)=>fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n');
export const pin=p=>{const b=fs.readFileSync(p);return {bytes:b.length,sha256:hash(b)};};
export function frozenInputs(){
 assert(pin(FROZEN+'/pins.json').sha256===FROZEN_PINS_SHA,'Published207 freeze changed');
 const pins=read(FROZEN+'/pins.json');for(const [name,expected] of Object.entries(pins.files)){const actual=pin(FROZEN+'/'+name);assert(actual.bytes===expected.bytes&&actual.sha256===expected.sha256,'Frozen207 source changed');}
 const receipt=read(FROZEN+'/activation-receipt.json'),plan=read(FROZEN+'/plan.json'),before=fs.readFileSync(FROZEN+'/index.html');
 assert(receipt.success&&receipt.versionCode===207&&receipt.sha256===APK_SHA&&receipt.bytes===APK_BYTES&&receipt.apk_url===LUMINEST_URL&&receipt.page.sha256===hash(before),'Exact published207 page receipt differs');
 const protection=read('S:/FFBE JP Data Export/build/v203-publication/assets/frozen-plan.json').production_guard;
 assert(JSON.stringify(protection)===JSON.stringify(plan.production_guard),'Production guards changed');
 return {receipt,plan,before,protection};
}
export function pageDelta(){
 const inputs=frozenInputs(),before=inputs.before.toString('utf8');
 const oldBlock=`<a class="button" href="${LUMINEST_URL}" download>Download Build 207 APK &mdash; 145.2 MB</a>`;
 const newBlock=`<a class="button" href="${GITHUB_URL}" download>Download Build 207 APK from GitHub &mdash; 145.2 MB</a>\n<p class="details"><a href="${LUMINEST_URL}" download>Luminest mirror &mdash; 145.2 MB</a></p>`;
 assert(before.split(oldBlock).length===2,'Exact207 download button absent or duplicated');
 const after=before.replace(oldBlock,newBlock);
 assert(after.replace(newBlock,oldBlock)===before,'Page exceeds one-button mirror change');
 const existingLinks=[...before.matchAll(/href="([^"]+\.apk)"/g)].map(m=>m[1]);
 const finalLinks=[...after.matchAll(/href="([^"]+\.apk)"/g)].map(m=>m[1]);
 assert(existingLinks.length===9&&finalLinks.length===10&&existingLinks.every(u=>finalLinks.includes(u))&&finalLinks[0]===GITHUB_URL&&finalLinks[1]===LUMINEST_URL,'APK links or primary/mirror order changed');
 return {...inputs,oldBlock,newBlock,after:Buffer.from(after),existingLinks,finalLinks};
}
export function preparedPage(){
 const delta=pageDelta(),page=fs.readFileSync(DIR+'/site/index.html'),plan=read(DIR+'/page-plan.json');
 assert(page.equals(delta.after)&&plan.previous_sha256===hash(delta.before)&&plan.new_sha256===hash(page)&&plan.apk_sha256===APK_SHA&&plan.github_url===GITHUB_URL&&plan.luminest_mirror_url===LUMINEST_URL,'Prepared mirror page differs');
 return {...delta,page,pagePlan:plan};
}
export function verifiedUpload(){
 const receipt=read(DIR+'/github-apk-receipt.json');
 assert(receipt.success&&receipt.versionCode===207&&receipt.bytes===APK_BYTES&&receipt.sha256===APK_SHA&&receipt.url===GITHUB_URL&&receipt.release_tag===RELEASE_TAG&&receipt.full_download_verified===true&&receipt.prerelease===true&&receipt.make_latest===false&&Number.isSafeInteger(receipt.release_id)&&receipt.release_id>0,'Root verified exact207 GitHub APK receipt required');
 const starts=[0,Math.floor(APK_BYTES/2),APK_BYTES-65536];
 assert(receipt.ranges?.length===3&&starts.every(start=>receipt.ranges.some(r=>r.start===start&&r.end===Math.min(start+65535,APK_BYTES-1)&&r.verified===true)),'Three verified exact207 GitHub APK ranges required');
 return receipt;
}
