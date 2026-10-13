import fs from 'node:fs';
import {ROOT,DIR,APK_SHA,APK_BYTES,GITHUB_URL,LUMINEST_URL,pageDelta,save,hash,assert,pin} from './page_inputs.mjs';
assert(process.argv.length===2,'No configurable destination');
const delta=pageDelta();fs.mkdirSync(DIR+'/site',{recursive:true});fs.writeFileSync(DIR+'/site/index.html',delta.after);
save(DIR+'/page-plan.json',{schema:'ffbe-207-github-primary-page-plan-v1',versionCode:207,apk_sha256:APK_SHA,apk_bytes:APK_BYTES,github_url:GITHUB_URL,luminest_mirror_url:LUMINEST_URL,previous_sha256:hash(delta.before),previous_bytes:delta.before.length,new_sha256:hash(delta.after),new_bytes:delta.after.length,existing_APK_links:delta.existingLinks,final_APK_links:delta.finalLinks,approved_delta:{before:delta.oldBlock,after:delta.newBlock},all_other_page_bytes_preserved:true,required_upload_receipt:'publication/github-apk-receipt.json',remote_published:false});
console.log(JSON.stringify({ready:true,github_primary:GITHUB_URL,luminest_mirror:LUMINEST_URL,previous_APK_links_preserved:delta.existingLinks.length,earlier_build_links_preserved:8,page:pin(DIR+'/site/index.html'),publication_waiting_for_verified_GitHub_upload:true}));
