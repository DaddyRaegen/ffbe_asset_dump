"""Fresh local qualification of unchanged asset203 source ledgers and packs.

No network, runtime, build-source edits, publication or frozen-input writes.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

OUT=Path(__file__).resolve().parent
CURRENT=OUT.parents[1]
FROZEN=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction')
WORKSPACE=FROZEN.parents[1]
MANIFEST_SHA='b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8'

def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def save(name,data):
    destination=OUT/name
    assert destination.resolve().is_relative_to(OUT.resolve())
    destination.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def main():
    adaptations=json.loads((OUT/'CHECK_SCRIPT_ADAPTATIONS.json').read_bytes())
    for script in adaptations:
        assert digest(script['frozen_original'])==script['original_sha256']
        assert digest(script['adapted_script'])==script['adapted_sha256']
    old_reports=[FROZEN/'event_audit/STATIC_REGRESSION_CHECKS.json',FROZEN/'banner_audit/INDEPENDENT_BANNER_VERIFICATION.json',FROZEN/'ASSET_PLAN_VALIDATION.json']
    protected=[
        FROZEN/'asset_publication/manifest.json',FROZEN/'asset_publication/frozen-plan.json',
        FROZEN/'event_audit/build_event_correction.py',FROZEN/'event_audit/EVENT_CORRECTION_LEDGER.json',
        FROZEN/'event_audit/GREETING_PHASE_PROOF.json',FROZEN/'banner_audit/BANNER_CORRECTION_VALIDATION.json',
        FROZEN/'banner_audit/book_banner_mapping.json',FROZEN/'banner_audit/banner_owner_updates.json',
        FROZEN/'banner_audit/banner_gap_ledger.json',
        WORKSPACE/'catalog_output/event_catalog.json',WORKSPACE/'catalog_output/regional_relationships.json',
        WORKSPACE/'integration_work/events/scripts/event_context.py',
    ]+[Path(x['frozen_original']) for x in adaptations]+old_reports
    before={str(path):digest(path) for path in protected}
    graph_identity=[]
    for current_relative,frozen_relative in [
        ('game_asset_manifest.json','asset_publication/manifest.json'),
        ('root_delivery.tsv','payload/root_delivery.tsv'),
        ('content_delivery.tsv','payload/content_delivery.tsv'),
        ('base_delivery.tsv','payload/base_delivery.tsv'),
    ]:
        current=CURRENT/'payload'/current_relative;frozen=FROZEN/frozen_relative
        assert current.read_bytes()==frozen.read_bytes(),current_relative
        graph_identity.append({'current':str(current),'frozen':str(frozen),'sha256':digest(current),'bytes':current.stat().st_size,'byte_identical':True})
    assert digest(CURRENT/'payload/game_asset_manifest.json')==MANIFEST_SHA
    assert (CURRENT/'payload/base_delivery.tsv').read_bytes()==(FROZEN.parent/'thin_delivery/payload/base_delivery.tsv').read_bytes()
    save('CURRENT_GRAPH_IDENTITY.json',{'passed':True,'manifest_sha256':MANIFEST_SHA,'asset_version':203,'APK_min_version':203,'catalogs_and_manifest':graph_identity,'original_base_bytes_preserved':True})

    jobs=[
        ('source-event-identity-ledger',[sys.executable,'-B',OUT/'scripts/verify_event_correction.py','--payload',FROZEN/'payload/side_stories','--allow-banner-icons'],'EVENT_STATIC_REGRESSION_CHECKS.json'),
        ('source-banner-identity-ledger',[sys.executable,'-B',OUT/'scripts/verify_banner_correction.py'],'INDEPENDENT_BANNER_VERIFICATION.json'),
        ('packed-game-byte-and-catalog-verification',[sys.executable,'-B',OUT/'scripts/verify_asset_plan.py'],'ASSET_PLAN_VALIDATION.json'),
    ]
    def run(job):
        name,command,report_name=job
        env=os.environ.copy();env['PYTHONUTF8']='1';env['PYTHONDONTWRITEBYTECODE']='1'
        started=time.monotonic()
        process=subprocess.run(list(map(str,command)),cwd=OUT,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600)
        log=OUT/'logs'/(name+'.txt');log.write_text(process.stdout+process.stderr,encoding='utf-8')
        result={'name':name,'exit_code':process.returncode,'seconds':round(time.monotonic()-started,3),'log':str(log),'report':str(OUT/report_name)}
        if process.returncode==0:
            report=json.loads((OUT/report_name).read_bytes());assert report['passed']
            result.update(report_sha256=digest(OUT/report_name),checks=report.get('checks_count',report.get('checks')))
        return result
    checks=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for future in as_completed([pool.submit(run,job) for job in jobs]):
            result=future.result();checks.append(result);print(json.dumps(result),flush=True)
    for path,sha in before.items():assert digest(path)==sha,'Frozen input or old report changed: '+path
    for script in adaptations:
        assert digest(script['frozen_original'])==script['original_sha256']
        assert digest(script['adapted_script'])==script['adapted_sha256']
    for entry in graph_identity:assert digest(entry['current'])==entry['sha256']
    passed=all(check['exit_code']==0 for check in checks)
    report={'schema':'ffbe-unchanged-v203-content-checks-v1','passed':passed,'manifest_sha256':MANIFEST_SHA,'asset_version':203,'intended_APK_version':204,'current_graph_byte_identity_verified':True,'source_script_adaptations':adaptations,'frozen_source_pins':[{'path':path,'sha256':sha,'unchanged_after_checks':True} for path,sha in before.items()],'checks':sorted(checks,key=lambda check:check['name']),'all_checks_rerun_locally_for_current_graph':True,'network_requested':False,'runtime_tested':False,'APK_qualification_included':False,'runtime_cache_or_saves_touched':False,'build_sources_modified':False,'remote_mutations':False,'frozen_inputs_or_old_reports_modified':False,'scope':'Original source-event ledger and mutation regressions, banner CPK/icon/image provenance, complete locally staged root pack bytes and all unchanged asset203 graph records. Reused base/additional packs are catalog/hash-pinned; no new full network verification.'}
    save('CONTENT_QUALIFICATION.json',report)
    print(json.dumps({'passed':passed,'report':str(OUT/'CONTENT_QUALIFICATION.json'),'checks':sum(check.get('checks',0) for check in checks)}),flush=True)
    if not passed:raise SystemExit(1)

if __name__=='__main__':main()
