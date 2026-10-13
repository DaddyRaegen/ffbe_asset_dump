// Deterministic technical sizing only. No creative generation or Python image editing.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('C:/Users/Raegen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const ROOT='S:/FFBE JP Data Export/build/v208-production';
const inputFile=ROOT+'/audit/BANNER_GEOMETRY_INPUTS.json';
const input=JSON.parse(fs.readFileSync(inputFile));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const assert=(v,m)=>{if(!v)throw Error(m);};
assert(input.passed&&input.records.length===658,'Exact658 approved technical encodings required');
const proposalFile=ROOT+'/audit/BANNER_REPAIR_PROPOSAL.json';assert(sha(fs.readFileSync(proposalFile))==='0a9e374dd92c47bef4e6ad8f7b40a9bc86a9eef16f84d2f7fd24687cb90ee251','Approved neutral proposal changed');
const proposal=JSON.parse(fs.readFileSync(proposalFile));
const generated=new Set('side_book_7065.png side_book_7070.png side_book_7073.png side_book_7076.png side_book_7078.png side_book_7081.png side_book_7082.png side_book_7083.png event_archive_book_1500001.png event_archive_book_1500002.png event_original_jp_7f580191810790d3.png'.split(' '));
const neutral=new Map(proposal.fallback_books.map(r=>[r.fallback.target_member,r.fallback]));
const wrapperFile=ROOT+'/audit/NATIVE_CANVAS_WRAPPER_PLAN.json';assert(sha(fs.readFileSync(wrapperFile))==='037f3e3e4a0786404b995e279a8c2dd8d0bea97b2f5470530e2e7782fe0a98cf','Wrapper plan changed');
const wrapperPlan=JSON.parse(fs.readFileSync(wrapperFile));assert(wrapperPlan.passed&&wrapperPlan.member_count===50,'Exact50 wrappers required');
const wrappers=new Map(wrapperPlan.records.map(r=>[r.name,r]));
const allowed=new Set([...generated,...neutral.keys(),...wrappers.keys()]);
assert(allowed.size===658&&new Set(input.records.map(r=>r.name)).size===658&&input.records.every(r=>allowed.has(r.name)),'Geometry scope differs');
const target=ROOT+'/banner_outputs/normalized';fs.mkdirSync(target,{recursive:true});
const records=[];
for(const item of input.records){
 const source=fs.readFileSync(item.local_path);assert(source.length===item.bytes&&sha(source)===item.sha256,'Source PNG changed');
 const wrapper=wrappers.get(item.name);const meta=await sharp(source).metadata();assert(meta.width===(wrapper?600:640)&&meta.height===(wrapper?120:240),'Exact approved source dimensions required');
 if(wrapper)assert(item.kind==='native_canvas_wrapper'&&item.bytes===wrapper.bytes&&item.sha256===wrapper.sha256&&item.source_member===wrapper.source_member,'Exact genuine wrapper source changed');
 if(neutral.has(item.name)){const approved=neutral.get(item.name);assert(item.bytes===approved.bytes&&item.sha256===approved.sha256&&item.source_member===approved.member,'Neutral exact source changed');}
 const before=await sharp(source).ensureAlpha().raw().toBuffer({resolveWithObject:true});assert(before.info.channels===4,'Source RGBA expected');
 const bounds=(pixels,threshold,width=640,height=240)=>{let x0=width,y0=height,x1=-1,y1=-1;for(let y=0;y<height;y++)for(let x=0;x<width;x++){if(pixels[(y*width+x)*4+3]>=threshold){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}}return [x0,y0,x1+1,y1+1];};
 const before128=bounds(before.data,128,meta.width,meta.height);const expectedBounds=wrapper?[0,0,600,120]:generated.has(item.name)?[0,0,640,240]:item.kind==='neutral_P5_template'?[3,3,637,237]:[1,2,639,239];assert(JSON.stringify(before128)===JSON.stringify(expectedBounds),'Only confirmed source bounds admitted');
 let result,transform;const offset=wrapper?[20,60]:[36,13];const art=wrapper?[600,120]:[568,213];
 if(wrapper){
  result=await sharp(source).ensureAlpha().extend({left:20,right:20,top:60,bottom:60,background:{r:0,g:0,b:0,alpha:0}}).png({compressionLevel:9,adaptiveFiltering:true,palette:false}).toBuffer();
  transform={kind:'native_canvas_padding',fit:'none',whole_canvas:true,alpha_crop:false,resampling:false,recolor:false,source_art:[600,120],canvas:[640,240],offset:[20,60],padding:[20,60,20,60],preserve_source_RGBA_pixels:true,creative_generation:false};
 }else{
  const resized=await sharp(source).ensureAlpha().resize({width:610,height:213,fit:'inside',kernel:'lanczos3',withoutEnlargement:true}).png({compressionLevel:9,adaptiveFiltering:true,palette:false}).toBuffer();
  const fitted=await sharp(resized).metadata();assert(fitted.width===568&&fitted.height===213,'Approved proportionate art rectangle differs');
  result=await sharp(resized).extend({left:36,right:36,top:13,bottom:14,background:{r:0,g:0,b:0,alpha:0}}).png({compressionLevel:9,adaptiveFiltering:true,palette:false}).toBuffer();
  transform={fit:'inside',whole_canvas:true,alpha_crop:false,content_box:[610,213],resized_art:[568,213],canvas:[640,240],offset:[36,13],padding:[36,13,36,14],kernel:'lanczos3',preserve_full_art_and_aspect:true,creative_generation:false};
 }
 const actual=await sharp(result).metadata();assert(actual.width===640&&actual.height===240&&actual.hasAlpha,'Native canvas differs');
 const pixels=await sharp(result).raw().toBuffer({resolveWithObject:true});assert(pixels.info.channels===4,'RGBA expected');
 let xmin=640,ymin=240,xmax=-1,ymax=-1;
 for(let y=0;y<240;y++)for(let x=0;x<640;x++){const a=pixels.data[(y*640+x)*4+3];if(a){assert(x>=offset[0]&&x<offset[0]+art[0]&&y>=offset[1]&&y<offset[1]+art[1],'Pixel outside approved art extent');xmin=Math.min(xmin,x);ymin=Math.min(ymin,y);xmax=Math.max(xmax,x);ymax=Math.max(ymax,y);}}
 if(wrapper)for(let y=0;y<120;y++)assert(before.data.subarray(y*600*4,(y+1)*600*4).equals(pixels.data.subarray(((y+60)*640+20)*4,((y+60)*640+620)*4)),'Genuine source pixels changed');
 const after128=bounds(pixels.data,128);
 const local=target+'/'+item.name;if(fs.existsSync(local))assert(fs.readFileSync(local).equals(result),'Refuse to overwrite different normalized bytes');else fs.writeFileSync(local,result);
 records.push({name:item.name,book_ids:item.book_ids,source:item,candidate:{local_path:local,bytes:result.length,sha256:sha(result),width:640,height:240,art_width:art[0],art_height:art[1],alpha_bbox:[xmin,ymin,xmax+1,ymax+1],alpha128_bbox:after128},before_alpha128_bbox:before128,after_alpha128_bbox:after128,transform});
}
const pin=file=>{const b=fs.readFileSync(file);return {file,bytes:b.length,sha256:sha(b)};};
const evidence=['audit/NATIVE_BANNER_GEOMETRY.json','audit/BANNER_ALPHA_BOUNDS.json','audit/NEUTRAL_CARD_GEOMETRY.json','audit/RENDERED_207_BANNER_REVIEW.json','audit/REMAINING_BASELINE_PLACEHOLDERS.json','audit/NONSTANDARD_GENUINE_BANNER_GEOMETRY.json','audit/NATIVE_CANVAS_WRAPPER_PLAN.json','device/build207-shield-baton.png','device/build207-story-oversized.png','device/build208-event-top.png','device/final208-baseline-placeholders.png'].map(f=>pin(ROOT+'/'+f));
const report={schema:'ffbe208-proportional-banner-geometry-plan-v1',passed:true,input_sha256:sha(fs.readFileSync(inputFile)),source_code_sha256:sha(fs.readFileSync(new URL(import.meta.url))),encoder:'Sharp/libvips under Node.js',node_version:process.version,sharp_versions:sharp.versions,PNG_options:{compressionLevel:9,adaptiveFiltering:true,palette:false},fit_member_count:608,native_canvas_wrapper_member_count:50,wrapper_plan_sha256:sha(fs.readFileSync(wrapperFile)),records,evidence,genuine_genesis7032_unchanged_sha256:input.genuine_genesis7032_unchanged_sha256,already_inset7074_unchanged_sha256:input.already_inset7074_unchanged_sha256,already_inset7075_unchanged_sha256:input.already_inset7075_unchanged_sha256,original_genesis7032_checked_and_already_standard:true,all_routine_Dark_Visions_assets_unchanged:true,no_network_requests:true,no_device_actions:true};
const outputFile=ROOT+'/audit/BANNER_GEOMETRY_PLAN.json',output=Buffer.from(JSON.stringify(report,null,2)+'\n');
if(fs.existsSync(outputFile)&&!fs.readFileSync(outputFile).equals(output))assert(['-candidate2','-candidate1'].some(suffix=>fs.existsSync(ROOT+suffix+'/audit/BANNER_GEOMETRY_PLAN.json')&&fs.readFileSync(outputFile).equals(fs.readFileSync(ROOT+suffix+'/audit/BANNER_GEOMETRY_PLAN.json'))),'Active geometry plan differs from immutable candidate archives');
fs.writeFileSync(outputFile,output);
console.log(JSON.stringify({passed:true,members:records.length,fits:608,pixel_preserving_wrappers:50,canvas:[640,240]}));
