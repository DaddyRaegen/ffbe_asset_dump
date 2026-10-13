"""Canonical local-only release gates; no device or network/publication actions."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys
ROOT=Path(__file__).resolve().parent
def digest(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,default=ROOT/'qualification_config.json');args=parser.parse_args()
    cfg=json.loads(args.config.read_bytes());stage=Path(cfg['correction_stage']);native=Path(cfg['native_source']);guard=Path(cfg['guard_source']);build=Path(cfg['build_output'])
    result=json.loads((build/'NATIVE_APK_BUILD.json').read_bytes());apk=Path(result['apk']);assert digest(apk)==result['sha256']
    log=build/'qualification-logs';log.mkdir(exist_ok=True);checks=[]
    def run(name,command,cwd=None):
        child_env=os.environ.copy();child_env['PYTHONUTF8']='1'
        r=subprocess.run(list(map(str,command)),cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace',env=child_env,timeout=600)
        (log/(name+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8');checks.append({'name':name,'exit_code':r.returncode})
        print(name,r.returncode,flush=True)
        if r.returncode:raise RuntimeError(name+' failed; see qualification-logs')
    run('actual-release-guard-tests',[sys.executable,'-B','-m','unittest','-v','test_release_guard.py'],guard)
    run('native-host-fixtures',[sys.executable,'-B',native/'run_tests.py'])
    run('packed-game-byte-and-catalog-verification',[sys.executable,'-B',stage/'verify_asset_plan.py'])
    run('source-event-identity-ledger',[sys.executable,'-B',stage/'event_audit/verify_event_correction.py','--payload',stage/'payload/side_stories','--allow-banner-icons'])
    run('source-banner-identity-ledger',[sys.executable,'-B',stage/'banner_audit/verify_banner_correction.py'])
    run('exact-signed-apk-qualification',[sys.executable,'-B',guard/'release_guard.py','--manifest',stage/'asset_publication/manifest.json','--root-catalog',stage/'payload/root_delivery.tsv','--content-catalog',stage/'payload/content_delivery.tsv','--base-catalog',stage/'payload/base_delivery.tsv','--release-metadata',stage/'payload/delivery_release.tsv','--baseline-base',cfg['baseline_base'],'--apk',apk,'--output',build/'SIGNED_RELEASE_QUALIFICATION.json'])
    assert digest(apk)==result['sha256']
    report={'schema':'ffbe-native-delivery-release-gates-v1','passed':True,'apk':str(apk.resolve()),'apk_sha256':result['sha256'],'manifest_sha256':digest(stage/'asset_publication/manifest.json'),'checks':checks,'device_runtime_tested':False,'runtime_cache_or_save_touched':False,'published':False}
    (build/'RELEASE_GATES.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
