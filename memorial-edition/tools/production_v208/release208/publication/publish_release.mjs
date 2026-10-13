// --stage is nonlatest. --promote is gated by the exact signed208 BlueStacks report.
import fs from 'node:fs';
import path from 'node:path';
import {ROOT,DIR,REPO,MESSAGE,ISSUES,PACKAGE,SIGNER,qualifiedInputs,assetsGate,emulatorGate,stageGuards,immutableGuards,hash,pin,save,read,assert,rangesGate,publicGET,updaterBytes} from './inputs208.mjs';
import {github208,verifyPublic} from './github208.mjs';
import {put} from 'file:///T:/Projects/FFBE%20Patch/localization-rounds/2026-09-25-download-recovery/scripts/hosting.mjs';
const mode=process.argv[2];assert(process.argv.length===3&&['--stage','--promote'].includes(mode),'Explicit --stage or --promote required');
const inputs=qualifiedInputs(),assets=assetsGate(inputs),plan=read(DIR+'/plan.json');
assert(plan.schema==='ffbe-production208-publication-plan-v1'&&plan.versionCode===208&&plan.sha256===inputs.build.sha256&&plan.bytes===inputs.build.bytes&&plan.release_tag===inputs.tag&&plan.apk_url===inputs.url&&plan.download_plan_sha256===inputs.planPins.download_plan_sha256&&plan.asset_stage_receipt_sha256===assets.pin.sha256&&plan.signed_qualification_sha256===pin(path.resolve(ROOT,inputs.cfg.qualifier)).sha256&&plan.transport_qualification_sha256===pin(path.resolve(ROOT,inputs.cfg.transport)).sha256,'Prepared exact208 publication changed');
for(const [name,expected] of Object.entries(plan.sources))assert(pin(DIR+'/'+name).sha256===expected,'Reviewed208 publisher source changed: '+name);
for(const file of [...plan.stage_files,plan.page,plan.beta_updater]){assert(path.resolve(file.local_path).startsWith(path.resolve(DIR+'/site')+path.sep),'Prepared metadata outside exact site directory');const actual=pin(file.local_path);assert(actual.bytes===file.bytes&&actual.sha256===file.sha256,'Prepared208 metadata changed');}
assert(plan.stage_files.map(file=>file.name).join('|')==='patch_version.json|checksums.txt|phone-test-checklist.txt|content_delivery.tsv|event-assets.json'&&fs.readFileSync(plan.production_updater.local_path).equals(updaterBytes(inputs))&&fs.readFileSync(plan.beta_updater.local_path).equals(updaterBytes(inputs,'beta')),'Exact208 metadata/updaters required');
// Promotion eligibility is established before credentials or remote operations.
const emulator=mode==='--promote'?emulatorGate(inputs):null;
const gh=github208(inputs,mode==='--stage'?'stage':'promote');await gh.authenticate();
const finalNames=['release.json','bluestacks-test.json'];
const allowed=[inputs.filename,...plan.stage_files.map(file=>file.name),...finalNames];
const apkFile={name:inputs.filename,role:'apk',local_path:inputs.build.apk,bytes:inputs.build.bytes,sha256:inputs.build.sha256};
if(mode==='--stage'){
 const before=await stageGuards(inputs,gh);
 const release=await gh.stageRelease(inputs.tag,'FFBE Memorial — Global Events build208',`${MESSAGE}\n\nKnown issues:\n${ISSUES.join('\n')}\n\nInstall over the existing English edition and keep saves. VersionCode208, ${inputs.build.bytes} bytes, SHA-256 ${inputs.build.sha256}. GitHub hosts the APK. Production promotion requires BlueStacks review of this exact APK; the completed report and release details are attached when promoted. A physical phone retest remains pending.`);
 save(DIR+'/apk-stage-progress.json',{release_id:release.id,release_tag:release.tag_name,prerelease:true,make_latest:false,success:false});
 const files=[];
 for(const file of [apkFile,...plan.stage_files]){const uploaded=await gh.upload(release,file,allowed);files.push({...await verifyPublic(file,uploaded.url,file.role==='apk'),asset_id:uploaded.asset.id});console.log(JSON.stringify({verified:file.name,bytes:file.bytes}));}
 const after=await stageGuards(inputs,gh);
 save(DIR+'/apk-stage-receipt.json',{schema:'ffbe-production208-apk-stage-v1',success:true,versionCode:208,asset_version:208,bytes:inputs.build.bytes,sha256:inputs.build.sha256,url:inputs.url,release_tag:inputs.tag,release_id:release.id,prerelease:true,make_latest:false,files,publication_plan_sha256:pin(DIR+'/plan.json').sha256,asset_stage_receipt_sha256:assets.pin.sha256,signed_qualification_sha256:plan.signed_qualification_sha256,production_before:before,production_after:after,physical_phone_test:'pending',completed_at:new Date().toISOString()});
 console.log(JSON.stringify({success:true,staged:true,release_id:release.id,apk_url:inputs.url,production_unchanged:true}));
}else{
 const staged=read(DIR+'/apk-stage-receipt.json');
 assert(staged.success===true&&staged.versionCode===208&&staged.sha256===inputs.build.sha256&&staged.bytes===inputs.build.bytes&&staged.url===inputs.url&&staged.release_tag===inputs.tag&&staged.publication_plan_sha256===pin(DIR+'/plan.json').sha256&&staged.asset_stage_receipt_sha256===assets.pin.sha256&&staged.signed_qualification_sha256===plan.signed_qualification_sha256,'Verified exact208 APK stage receipt required');
 assert(staged.files.length===plan.stage_files.length+1,'Exact staged208 APK/metadata set required');
 for(const expected of [apkFile,...plan.stage_files]){const file=staged.files.find(file=>file.name===expected.name);assert(file&&file.bytes===expected.bytes&&file.sha256===expected.sha256&&file.full_download_verified===true&&file.url===`https://github.com/${REPO}/releases/download/${inputs.tag}/${expected.name}`,'Staged208 asset proof differs');if(expected.role==='apk')rangesGate(file,expected);}
 const release=await gh.get('/releases/tags/'+inputs.tag);gh.register(release,inputs.tag);
 assert(release.id===staged.release_id&&release.target_commitish===inputs.protection.main_sha,'Staged208 release changed');
 const before=await immutableGuards(inputs,gh),currentLatest=await gh.get('/releases/latest');
 assert([inputs.protection.latest_release_id,release.id].includes(currentLatest.id),'Another production release is now latest');
 const productionBytes=fs.readFileSync(plan.production_updater.local_path),betaBytes=fs.readFileSync(plan.beta_updater.local_path),pageBytes=fs.readFileSync(plan.page.local_path);
 const mutableBefore=[];
 for(const [url,newBytes,oldSHA] of [
  [`https://github.com/${REPO}/releases/latest/download/patch_version.json`,productionBytes,inputs.snapshot.files.find(file=>file.url.endsWith('/releases/latest/download/patch_version.json')).sha256],
  ['https://cdn.luminest.io/ffbe/patch_version.json',productionBytes,inputs.snapshot.files.find(file=>file.url==='https://cdn.luminest.io/ffbe/patch_version.json').sha256],
  [plan.page.url,pageBytes,plan.page.previous_sha256],
  [`https://raw.githubusercontent.com/${REPO}/beta/channels/beta/patch_version.json`,betaBytes,inputs.snapshot.files.find(file=>file.url.endsWith('/beta/channels/beta/patch_version.json')).sha256]
 ]){const current=await publicGET(url);assert(current.equals(newBytes)||hash(current)===oldSHA,'Production/beta route changed before promotion: '+new URL(url).pathname);mutableBefore.push({url,bytes:current.length,sha256:hash(current)});}
 const liveAssets=await gh.get(`/releases/${release.id}/assets?per_page=100`);
 assert(liveAssets.every(asset=>allowed.includes(asset.name)),'Unexpected staged APK release asset');
 for(const file of staged.files){const asset=liveAssets.find(asset=>asset.name===file.name);assert(asset&&asset.id===file.asset_id&&asset.size===file.bytes&&asset.state==='uploaded'&&(!asset.digest||asset.digest==='sha256:'+file.sha256),'Verified staged APK/metadata asset was replaced or removed');if(file.name!==inputs.filename)assert(hash(await publicGET(file.url))===file.sha256,'Staged public208 metadata differs');}
 const releaseMetadata={schema:'ffbe-production208-release-v1',versionCode:208,versionName:inputs.build.versionName,asset_version:208,package:PACKAGE,signer_sha256:SIGNER,apk_url:inputs.url,bytes:inputs.build.bytes,sha256:inputs.build.sha256,update_message:MESSAGE,known_issues:ISSUES,content_catalog_sha256:inputs.signed.content_catalog_sha256,side_manifest_sha256:inputs.signed.side_manifest_sha256,download_plan_sha256:inputs.planPins.download_plan_sha256,immutable_data_release:inputs.download.release_tag,BlueStacks:{passed:true,report_url:`https://github.com/${REPO}/releases/download/${inputs.tag}/bluestacks-test.json`,report_sha256:emulator.pin.sha256,apk_sha256:inputs.build.sha256},physical_phone_test:'pending',save_migration_verified:emulator.receipt.save_migration_verified===true,previous_patch5_apk:inputs.snapshot.latest.assets.find(asset=>asset.name.endsWith('.apk')).browser_download_url};
 save(DIR+'/site/release.json',releaseMetadata);fs.copyFileSync(emulator.file,DIR+'/site/bluestacks-test.json');assert(pin(DIR+'/site/bluestacks-test.json').sha256===emulator.pin.sha256,'BlueStacks report changed before publication');
 const finalFiles=finalNames.map(name=>({name,role:'metadata',local_path:DIR+'/site/'+name,...pin(DIR+'/site/'+name)})),finalProof=[];
 for(const file of finalFiles){const uploaded=await gh.upload(release,file,allowed);finalProof.push({...await verifyPublic(file,uploaded.url),asset_id:uploaded.asset.id});}
 save(DIR+'/promotion-progress.json',{success:false,qualified208:true,release_id:release.id,emulator_report_sha256:emulator.pin.sha256,final_metadata:finalProof,steps:[]});
 const steps=[];
 async function step(name,value){steps.push({name,...value});save(DIR+'/promotion-progress.json',{success:false,release_id:release.id,emulator_report_sha256:emulator.pin.sha256,steps});}
 if(currentLatest.id!==release.id){assert(release.prerelease===true,'Candidate must be a staged prerelease');await gh.request(`/releases/${release.id}`,{method:'PATCH',body:{prerelease:false,make_latest:'true'}});}
 const promoted=await gh.get('/releases/latest');assert(promoted.id===release.id&&promoted.tag_name===inputs.tag&&promoted.prerelease===false&&promoted.draft===false,'Exact qualified208 release did not become latest');
 await step('GitHub latest production208',{release_id:release.id});
 async function waitExact(url,bytes){for(let attempt=0;attempt<60;attempt++){if((await publicGET(url)).equals(bytes))return {url,bytes:bytes.length,sha256:hash(bytes),canonical_public_verified:true};if(attempt%6===0)console.log(JSON.stringify({waiting_for_canonical_cache:new URL(url).pathname,attempt:attempt+1}));await new Promise(resolve=>setTimeout(resolve,10000));}throw Error('Canonical production208 public route differs: '+new URL(url).pathname);}
 const latestUpdater=await waitExact(`https://github.com/${REPO}/releases/latest/download/patch_version.json`,productionBytes);await step('GitHub latest updater208',latestUpdater);
 const oldCDN=inputs.protection.public_files.find(file=>file.url==='https://cdn.luminest.io/ffbe/patch_version.json');
 // The hosting helper is exposed only to these two exact preauthorized file paths.
 await put('cdn.luminest.io','ffbe/patch_version.json',productionBytes,{overwrite:true,expectedPrevious:oldCDN.sha256});
 const cdn=await waitExact(oldCDN.url,productionBytes);await step('CDN updater208',cdn);
 const betaFile=await gh.get('/contents/channels/beta/patch_version.json?ref=beta'),betaPrevious=Buffer.from((betaFile.content||'').replace(/\s/g,''),'base64');
 const snapshotBeta=inputs.snapshot.files.find(file=>file.url.endsWith('/beta/channels/beta/patch_version.json'));
 assert(betaPrevious.equals(betaBytes)||hash(betaPrevious)===snapshotBeta.sha256,'Canonical beta updater changed concurrently');
 let pointer={path:'channels/beta/patch_version.json',blob_sha:betaFile.sha,reused:true};
 if(!betaPrevious.equals(betaBytes)){const updated=await gh.request('/contents/channels/beta/patch_version.json',{method:'PUT',body:{message:'Point previous beta builds to qualified production208 GitHub APK',branch:'beta',sha:betaFile.sha,content:betaBytes.toString('base64')}});pointer={path:'channels/beta/patch_version.json',blob_sha:updated.content.sha,commit_sha:updated.commit.sha};}
 const beta=await waitExact(`https://raw.githubusercontent.com/${REPO}/beta/channels/beta/patch_version.json`,betaBytes);await step('Beta updater208',{...beta,pointer});
 await put('ffbe.luminest.io','downloads/index.html',pageBytes,{overwrite:true,expectedPrevious:plan.page.previous_sha256});
 const page=await waitExact(plan.page.url,pageBytes);await step('Production Android page208',page);
 const after=await immutableGuards(inputs,gh),latestAfter=await gh.get('/releases/latest');assert(latestAfter.id===release.id&&latestAfter.prerelease===false,'Production208 latest changed during promotion');
 save(DIR+'/production-activation-receipt.json',{schema:'ffbe-production208-activation-v1',success:true,versionCode:208,asset_version:208,apk_url:inputs.url,bytes:inputs.build.bytes,sha256:inputs.build.sha256,release_id:release.id,release_tag:inputs.tag,prerelease:false,make_latest:true,update_message:MESSAGE,known_issues:ISSUES,latest_updater:latestUpdater,cdn_updater:cdn,beta_updater:{...beta,pointer},page,final_metadata:finalProof,asset_stage_receipt_sha256:assets.pin.sha256,apk_stage_receipt_sha256:pin(DIR+'/apk-stage-receipt.json').sha256,publication_plan_sha256:pin(DIR+'/plan.json').sha256,signed_qualification_sha256:plan.signed_qualification_sha256,BlueStacks:{passed:true,report_sha256:emulator.pin.sha256,apk_sha256:inputs.build.sha256},mutable_routes_before:mutableBefore,protected_before:before,protected_after:after,source_main_unchanged:true,old_patch5_release_preserved:true,stable_beta203_asset_pointer_unchanged:true,physical_phone_test:'pending',completed_at:new Date().toISOString()});
 await step('Completed',{success:true});console.log(JSON.stringify({success:true,production208:true,apk_url:inputs.url,GitHub_latest_release_id:release.id,physical_phone_test:'pending'}));
}
