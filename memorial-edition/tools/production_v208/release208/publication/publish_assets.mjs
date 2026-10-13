import {DIR,dataInputs,stageGuards,save,pin} from './inputs208.mjs';
import {github208,verifyPublic} from './github208.mjs';
if(process.argv.length!==3||process.argv[2]!=='--stage')throw Error('Explicit --stage required');
const inputs=dataInputs(),gh=github208(inputs,'assets');await gh.authenticate();
const before=await stageGuards(inputs,gh);
const release=await gh.stageRelease(inputs.download.release_tag,'FFBE Memorial208 immutable event data','Verified208 native content. Per-APK immutable catalogs preserve previous releases. This data release remains a nonlatest prerelease.');
save(DIR+'/asset-stage-progress.json',{release_id:release.id,release_tag:release.tag_name,prerelease:true,make_latest:false,success:false});
const files=[];
for(const file of inputs.download.files){const uploaded=await gh.upload(release,file,inputs.download.files.map(file=>file.name));files.push({...await verifyPublic(file,uploaded.url,file.role==='pack'),asset_id:uploaded.asset.id});console.log(JSON.stringify({verified_data:file.name,bytes:file.bytes}));}
const after=await stageGuards(inputs,gh);
save(DIR+'/asset-stage-receipt.json',{schema:'ffbe-production208-immutable-data-stage-v1',success:true,versionCode:208,release_tag:release.tag_name,release_id:release.id,prerelease:true,make_latest:false,download_plan_sha256:pin(inputs.downloadPath).sha256,content_catalog_sha256:inputs.download.content_catalog_sha256,side_manifest_sha256:inputs.download.side_manifest_sha256,files,production_before:before,production_after:after,completed_at:new Date().toISOString()});
console.log(JSON.stringify({success:true,immutable_data_staged:true,files:files.length,production_unchanged:true}));
