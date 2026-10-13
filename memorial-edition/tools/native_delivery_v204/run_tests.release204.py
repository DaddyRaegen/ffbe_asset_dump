"""Run retained host fixtures without importing or overwriting legacy sources."""
from pathlib import Path
import json,subprocess,sys,time
ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'host_test_config.json').read_bytes())
stage=Path(cfg['correction_stage']);android=Path(cfg['android_jar']);out=Path(cfg['output'])
classes=out/'classes';fixtures=out/'fixtures'
for p in (classes,fixtures):p.mkdir(parents=True,exist_ok=True)
names=('TransferTest','GithubTransferTest','BaseTest','BaseCacheIntegrityTest','MetadataTest','NativeDeliveryTest','MovieCacheTest','PatchUpdaterTest','BundledStartupTest')
for name in names:assert (ROOT/'tests'/(name+'.java')).is_file(),'Required host fixture absent: '+name
results=[]
def run(label,args):
    start=time.time();r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    results.append({'label':label,'exit_code':r.returncode,'seconds':round(time.time()-start,2),'stdout':r.stdout,'stderr':r.stderr})
    print(label,r.returncode,r.stdout.strip(),flush=True)
    return r.returncode==0
sources=[p for folder in (ROOT/'java',ROOT/'tests') for p in sorted(folder.rglob('*.java'))]
if run('compile-actual-overlays-and-retained-fixtures',['javac','-encoding','UTF-8','-cp',android,'-d',classes,*sources]):
    for name in names:
        run(name,['java','-cp',str(classes)+';'+str(android),'O1.'+name,stage if name in ('MetadataTest','PatchUpdaterTest') else fixtures])
    run('MetadataTest-actual204',['java','-cp',str(classes)+';'+str(android),'O1.MetadataTest',ROOT.parent,'204'])
report={'schema':'ffbe-native-delivery-host-regression-v1','device_runtime_tested':False,'network':'in-memory fake HTTPS routes only','results':results,'passed':len(results)==len(names)+2 and all(x['exit_code']==0 for x in results)}
(out/'HOST_REGRESSION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
raise SystemExit(0 if report['passed'] else 1)
