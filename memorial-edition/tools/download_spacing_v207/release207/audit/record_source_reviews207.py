"""Seal final read-only207 source/publication review; no network or runtime tests."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(r'S:\FFBE JP Data Export\build\v207-download-spacing')
def pin(path):
 data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
plan=json.loads((ROOT/'audit/DOWNLOAD_SPACING_PLAN.json').read_text())
build=json.loads((ROOT/'staged_build/DOWNLOAD_SPACING_APK_BUILD.json').read_text())
signed=json.loads((ROOT/'staged_build/SIGNED_SPACING_QUALIFICATION.json').read_text())
local=json.loads((ROOT/'audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json').read_text())
assert signed['passed'] is True and signed['apk_sha256']==build['sha256'] and local['passed'] is True
assert signed['spacing_plan_sha256']==pin(ROOT/'audit/DOWNLOAD_SPACING_PLAN.json')['sha256']
paths=['source/build_download_spacing.py','source/frida_script.js','audit/DOWNLOAD_SPACING_PLAN.json',
 'guard/download_spacing_guard.py','guard/formatter_fixtures.mjs','guard/native_counter_proof.py',
 'publication/publication_inputs.mjs','publication/prepare_site.mjs','publication/publish_site.mjs',
 'publication/verify_apk_delta.py','publication/scripts/github_existing_auth.mjs','publication/review_publication_local.mjs']
report={'schema':'ffbe-v207-independent-source-publication-review-v1','passed':True,
 'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'review_mode':'Read-only source review; guard/formatter/VM executions owned by separate agents.',
 'reviewed_sources':[pin(ROOT/path) for path in paths],'apk_sha256':build['sha256'],'apk_bytes':build['bytes'],
 'spacing_plan_sha256':signed['spacing_plan_sha256'],'candidate_script_sha256':plan['candidate_script_sha256'],
 'qualification':pin(ROOT/'staged_build/SIGNED_SPACING_QUALIFICATION.json'),'network_free_scope_review':pin(ROOT/'audit/LOCAL_PUBLICATION_SCOPE_REVIEW.json'),
 'findings':[],
 'resolved_review_findings':['The counter matcher uses a strict end-of-input condition, preserving old behavior for trailing line breaks.','Publisher admission reads exact path fields from the sealed guard changed-member objects before comparing the two allowed paths.'],
 'approved_counter_scope_note':'The sealed matcher accepts whole-number MB/MB variants as well as the native zero-or-three-decimal form. Root explicitly accepted these within the requested counter domain. Matched strings without commas remain unchanged; the native proof does not claim the wider regex is the exact emitted grammar.',
 'verified_scope':['Only the existing punctuation helper insertion and PATCH_VERSION206 to207 change in Frida; only typed versionCode206 to207 in AXML.','Independent guard reconstructs the exact finite insertion rather than trusting arbitrary plan edits; all other members and compressed data remain206.','Native counter evidence is drawn from pinned original APK/ELF and actual formatter fixtures; phone appearance remains unverified.','Same DEX, native libraries, 170-member asset set, startup, movie, party, downloader/cache/resume/callback and event behavior.','All1898 catalog rows and1857 side paths remain206; frozen206 pack/catalog/manifest are reused, asset_version206 and zero asset uploads.','Immutable207 APK/checksum/release/checklist staging before beta updater; canonical raw207 pointer wait before beta page.','All eight old APK links retained; 207 updater keeps both URL fields, version/versionCode207, asset_version206 and changelog[].','Narrow GitHub helper permits only one beta updater PUT; no release/data/source mutation route. Six protected public files, main/latest and stable203 asset pointer checked before/after.'],
 'limitations':['Source review alone does not prove live public bytes; PUBLIC_V207_REVIEW.json provides the independent readback after activation.','No physical phone runtime, native ELF16KB compatibility, gameplay or save result is claimed. Unchanged206 pack public proof is inherited and not repeated.'],
 'network_requests_made':0,'remote_mutations_made':0,'device_actions':False,'runtime_verified':False}
target=ROOT/'audit/INDEPENDENT_SOURCE_PUBLICATION_REVIEW.json'
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'report':pin(target)}))
