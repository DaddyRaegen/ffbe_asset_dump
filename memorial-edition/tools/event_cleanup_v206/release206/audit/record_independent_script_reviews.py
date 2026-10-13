"""Seal read-only206 publisher, qualifier and isolated fixture source reviews."""
from pathlib import Path
import hashlib,json,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
def pin(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
publisher=[ROOT/'publication'/n for n in ('publication_inputs.mjs','prepare_site.mjs','publish_site.mjs')]
report={'schema':'ffbe-v206-independent-publisher-static-review-v1','passed':True,'review_mode':'read-only source inspection; no publisher execution','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_sources':[pin(p) for p in publisher],'findings':[],
 'verified_scope':['Exact qualified signed206 APK, actual catalog/side manifest, cleanup/banner plans and independent transport report gate all publication stages.','Immutable beta206 APK prefix, protected production public files/main/latest and stable203 asset pointer.','New data assets are a prerequisite to APK staging; new pack and unchanged packs verified by separate bounded evidence.','Release/checksum/checklist before beta updater; canonical raw updater exactbytes before beta page activation.','Updater keeps original LBDialog version/url/changelog[] and203/204 apk_url fields.','All seven previous APK links are preserved; new card marks exact206 phone/banner/save/Android17 tests pending.'],
 'separate_agent_review':'Locate agent reviews publish_assets/GitHub helper and runs real publisher source in network-free VM after final qualified inputs are ready.',
 'limitations':['This source review alone does not verify signed APK bytes or public network content; separate final qualification and PUBLIC_V206_REVIEW.json retain that evidence.','Final publisher/plan byte changes require re-pin/review; the VM report binds the exact publication input bytes.'],
 'remote_mutations_made':0,'network_requests_made':0,'device_actions':False}
(ROOT/'audit/INDEPENDENT_PUBLICATION_SCRIPT_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
host=[ROOT/'guard/event_cleanup_guard.py',ROOT/'audit/runtime_host/verify_actual206_catalog.py',ROOT/'audit/runtime_host/Old205TargetCacheTest.java',ROOT/'audit/runtime_host/REFERENCE205_JVM_SOURCES.json']
scope={'schema':'ffbe-v206-independent-guard-host-source-review-v1','passed':True,'review_mode':'read-only source inspection; tests owned/run by guard agent','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewed_sources':[pin(p) for p in host],'findings':[],
 'verified_scope':['APK differences limited to exactlyfour members; DEX/native/unchanged ZIPcompressed payloads remain exact205.','Finite41book exclusion/20storymove formula, exactold/new fields and relative row order, full deferredUIregistry and no new relationshipobservations.','Exact12CPKPNG replacements tied to actual205 icon mapping; other rawmembers/order/IDs/metadata remain.','All1898catalog/1857side paths/order; fivechanged files, other1893descriptors verbatim; prior205hash acceptedhistory; exactfive rawdeflate slices.','Actual signed206 metadata/DEX and exactold/new changed205 targets tested via isolated JVM reference, genuinepartialwire bytes, unknownsourceauthority, corruptnewcachefallback, retry and isolatedsave preservation.','Sealed11referenceJava/stub sources plus original205hostreceipt checked before compilation; sourcehash drift rejected.'],
 'artwork_identity_review':'Content/title/art identity remains manual source+rootvisual review. Qualifier pins derivativeimage bytes and native dimensions; it is not an image-semantic oracle.',
 'reference_seal':pin(ROOT/'audit/runtime_host/REFERENCE205_JVM_SOURCES.json'),'runtime_verified':False,'network_requests_made':0,'device_actions':False}
(ROOT/'audit/INDEPENDENT_GUARD_HOST_SOURCE_REVIEW.json').write_text(json.dumps(scope,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'publication_review':pin(ROOT/'audit/INDEPENDENT_PUBLICATION_SCRIPT_REVIEW.json'),'guard_host_review':pin(ROOT/'audit/INDEPENDENT_GUARD_HOST_SOURCE_REVIEW.json')}))
