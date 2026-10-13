"""Record the focused read-only review of the fixed GitHub APK mirror publisher."""
from pathlib import Path
import datetime,hashlib,json
ROOT=Path(r'S:\FFBE JP Data Export\build\v207-github-mirror')
path=ROOT/'publication/publish_github.mjs';data=path.read_bytes()
expected='06ebfef3df0034da03f7daf79ac0e3173438efa8fd6703ddcc2fd16fd9c0b762'
assert len(data)==12572 and hashlib.sha256(data).hexdigest()==expected
report={'schema':'ffbe-v207-github-mirror-publisher-review-v1','passed':True,'review_mode':'Focused read-only source review; no tests or network execution.',
 'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':{'path':str(path),'bytes':len(data),'sha256':expected},'findings':[],
 'APK':{'versionCode':207,'bytes':145206221,'sha256':'d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e','rebuilt':False},
 'verified_scope':['Creates or reuses only beta-apk-v207-d9181ffc05fa11e1; prerelease true, draft false, make_latest false; new tag targets current beta SHA.','Only the exact existing207 APK can be uploaded. Existing assets are never deleted or overwritten. No new event assets, code/source push or production route is allowed.','Public full GET and first/middle/last exact ranges carry no publisher credentials through redirects.','Beta updater changes only apk_url/url to the same verified GitHub APK; version/versionCode207, asset_version206, bytes/hash/changelog and other fields remain.','Production main/latest and six protected public file pins checked before and after each mode.','Existing publisher credentials remain in memory and are absent from receipts/logged output.'],
 'network_requests_made':0,'remote_mutations_made':0,'device_actions':False,'runtime_verified':False,'physical_phone_test':'pending'}
target=ROOT/'audit/INDEPENDENT_PUBLISHER_SOURCE_REVIEW.json'
target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'source_sha256':expected,'report':str(target),'report_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
local=json.loads((ROOT/'audit/LOCAL_PAGE_REVIEW.json').read_text(encoding='utf-8'))
assert local['passed'] is True and local['all_other_page_bytes_preserved'] is True
sources=[]
for name,pin in local['source_pins'].items():
 source=ROOT/'publication'/name;content=source.read_bytes()
 assert len(content)==pin['bytes'] and hashlib.sha256(content).hexdigest()==pin['sha256']
 sources.append({'path':str(source),**pin})
page_review={'schema':'ffbe-v207-github-mirror-page-source-review-v1','passed':True,'review_mode':'Focused read-only source and exact prepared HTML delta review; no tests/network execution.',
 'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':sources,'findings':[],
 'prepared_page':local['prepared_page'],'verified_scope':['Only the current207 button block changes: GitHub primary plus Luminest mirror. All other page bytes and nine previous APK URLs remain.','Checksum/release/checklist links and pending phone wording are retained.','Publisher admits exact verified GitHub full/range APK receipt and canonical207 updater with both GitHub URLs, asset_version206 and changelog[].','Only guarded beta index may be written; production/legacy sources, main/latest and stable203 pointer checked before/after.'],
 'network_requests_made':0,'remote_mutations_made':0,'device_actions':False,'runtime_verified':False}
target=ROOT/'audit/INDEPENDENT_PAGE_SOURCE_REVIEW.json'
target.write_text(json.dumps(page_review,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'page_review_passed':True,'report':str(target),'report_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
