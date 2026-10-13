// Encode image-tool results for the existing 640x240 native texture slots.
// This performs only proportional asset downsampling and PNG encoding.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('C:/Users/Raegen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const ROOT='S:/FFBE JP Data Export/build/v206-event-cleanup';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const items=JSON.parse(fs.readFileSync(ROOT+'/banner_outputs/ENCODE_INPUTS.json','utf8'));
fs.mkdirSync(ROOT+'/banner_outputs/native',{recursive:true});
const records=[];
for(const item of items){
 const input=fs.readFileSync(item.source),before=await sharp(input).metadata();
 if(Math.abs(before.width/before.height-640/240)>0.005)throw Error('Banner does not have the native8:3 proportions: '+item.key);
 const output=await sharp(input).resize(640,240,{fit:'fill',kernel:'lanczos3'}).png({compressionLevel:9,palette:false}).toBuffer();
 const metadata=await sharp(output).metadata();if(metadata.width!==640||metadata.height!==240||metadata.format!=='png')throw Error('Native banner encoding mismatch');
 const destination=ROOT+'/banner_outputs/native/'+item.key+'.png';
 if(fs.existsSync(destination)&&!fs.readFileSync(destination).equals(output))throw Error('Refuse to replace a different encoded texture');
 fs.writeFileSync(destination,output);
 records.push({...item,source_bytes:input.length,source_sha256:sha(input),source_width:before.width,source_height:before.height,local_path:destination,bytes:output.length,sha256:sha(output),width:640,height:240,alpha:metadata.hasAlpha,creative_edit:'Built-in image tool; only proportional native encoding here.'});
}
fs.writeFileSync(ROOT+'/banner_outputs/NATIVE_BANNERS.json',JSON.stringify({schema:'ffbe-event-banner-native-encoding-v1',passed:true,records},null,2)+'\n');
console.log(JSON.stringify({passed:true,native_banners:records.length,dimensions:'640x240'}));
