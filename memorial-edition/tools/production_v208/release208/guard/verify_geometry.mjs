// Independent, fixed geometry formula; no candidate image or payload is written.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const sharp = require('C:/Users/Raegen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const assert = (value,message) => { if(!value) throw Error(message); };
assert(process.argv.length===4, 'Exact source-list and output paths required');
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
assert(input.schema==='ffbe-production208-geometry-input-v1' && input.records.length===658,
       'Only exact608 fits and50 unchanged-pixel wrappers may be checked');
assert(input.records.filter(item=>item.mode==='fit').length===608 &&
       input.records.filter(item=>item.mode==='pad').length===50,'Exact transform mode counts differ');
const seen=new Set(),records=[];
for(const item of input.records){
  assert(!seen.has(item.name),'Duplicate geometry member');seen.add(item.name);
  const source=fs.readFileSync(item.source_file),candidate=fs.readFileSync(item.candidate_file);
  assert(hash(source)===item.source_sha256 && source.length===item.source_bytes &&
         hash(candidate)===item.candidate_sha256 && candidate.length===item.candidate_bytes,
         'Sealed geometry bytes changed: '+item.name);
  const before=await sharp(source).metadata(),after=await sharp(candidate).metadata();
  assert(before.format==='png' && ['fit','pad'].includes(item.mode) &&
         before.width===(item.mode==='pad'?600:640) && before.height===(item.mode==='pad'?120:240) &&
         after.format==='png' && after.width===640 && after.height===240 && after.hasAlpha,
         'Native640x240 geometry/alpha contract changed: '+item.name);
  let artwork;
  if(item.mode==='fit') artwork=await sharp(source).ensureAlpha().resize({width:610,height:213,fit:'inside',
    kernel:'lanczos3',withoutEnlargement:true}).raw().toBuffer({resolveWithObject:true});
  else artwork=await sharp(source).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  const width=item.mode==='fit'?568:600,height=item.mode==='fit'?213:120;
  const x=item.mode==='fit'?36:20,y=item.mode==='fit'?13:60;
  assert(artwork.info.width===width && artwork.info.height===height && artwork.info.channels===4,
         'Exact approved artwork dimensions differ: '+item.name);
  // Construct the transparent canvas separately to verify the exact approved offset.
  const expected=Buffer.alloc(640*240*4);
  for(let row=0;row<height;row++) artwork.data.copy(expected,((row+y)*640+x)*4,
                                                   row*width*4,(row+1)*width*4);
  const actual=await sharp(candidate).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  assert(actual.info.channels===4 && actual.data.equals(expected),
         'Candidate exceeds proportional fit/transparent placement: '+item.name);
  records.push({name:item.name,source_sha256:item.source_sha256,
    candidate_sha256:item.candidate_sha256,rgba_sha256:hash(actual.data),
    mode:item.mode,artwork:[width,height],canvas:[640,240],offset:[x,y],
    padding:item.mode==='fit'?[36,13,36,14]:[20,60,20,60],
    original_pixels_not_resampled:item.mode==='pad',
    exact_approved_formula_pixels:true});
}
const report={schema:'ffbe-production208-geometry-verification-v1',passed:true,
  input_sha256:hash(fs.readFileSync(process.argv[2])),records,sharp_versions:sharp.versions,
  fit_count:608,wrapper_count:50,
  formula:'608 whole640x240 fits use Lanczos3 inside610x213;568x213 pixels at36,13. Fifty original600x120 RGBA wrappers use20,60 without resampling. Both use transparent640x240 canvas.',
  candidate_images_written:false,network_requests:false,device_actions:false};
fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,transformed_members:records.length}));
