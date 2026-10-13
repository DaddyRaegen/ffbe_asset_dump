"""Run exact206 catalogs and old205 cache migration through retained JVM classes."""
from pathlib import Path
import argparse,datetime,hashlib,json,re,shutil,subprocess,sys,time,zipfile,zlib,urllib.parse
ROOT=Path(__file__).resolve().parents[2]
HOST=Path(__file__).resolve().parent
SOURCE205=Path('S:/FFBE JP Data Export/build/v205-patch5-events/audit/original-downloader/actual-catalog/source')
PAYLOAD205=Path('S:/FFBE JP Data Export/build/v205-patch5-events/payload')
APK205=Path('S:/FFBE JP Data Export/build/v205-patch5-events/staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk')
FROZEN_PACKS=Path('C:/Users/Raegen/Documents/Codex/2026-10-02/task-2/integration_work/native_delivery_correction/asset_publication')
REFERENCE205_PIN_SHA='ccdbe7b5981dbec1795d5157be04f53785b2bd3c28b3402976c6a80be4c2f9c0'
sys.path.insert(0,str(ROOT/'guard'))
import event_cleanup_guard as g

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--payload',type=Path,default=ROOT/'payload')
    parser.add_argument('--apk',type=Path);args=parser.parse_args();payload=args.payload
    require=g.require;sha=g.sha
    require(g.common.file_sha(APK205)==g.BASELINE205_SHA,'Actual205 baseline pin differs')
    require((payload/'content_delivery.tsv').is_file(),'Actual206 catalog not prepared')
    work=HOST/('work_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'));work.mkdir()
    source=work/'source';requirements=work/'requirements';baseline=work/'baseline205';classes=work/'classes';fixtures=work/'fixtures'
    for p in (requirements,baseline,classes,fixtures):p.mkdir()
    with zipfile.ZipFile(APK205) as z:
        for name in ('base_delivery.tsv','content_delivery.tsv'):(baseline/name).write_bytes(z.read('assets/'+name))
        (baseline/'side_manifest.tsv').write_bytes(z.read('assets/side_stories/manifest.tsv'))
    if args.apk:
        with zipfile.ZipFile(args.apk) as z:
            require(z.read('assets/content_delivery.tsv')==(payload/'content_delivery.tsv').read_bytes(),'Signed206 catalog differs')
            require(z.read('assets/side_stories/manifest.tsv')==(payload/'side_stories/manifest.tsv').read_bytes(),'Signed206 manifest differs')
            require(sha(z.read('classes.dex'))==g.BASELINE205_DEX_SHA,'Runtime DEX changed from205')
    prior=g.common.parse_catalog((baseline/'content_delivery.tsv').read_bytes());actual=g.common.parse_catalog((payload/'content_delivery.tsv').read_bytes())
    require(len(prior)==1898 and list(prior)==list(actual),'Catalog path set or row order changed from205')
    changed={p for p in prior if prior[p]['line']!=actual[p]['line']};require(changed,'Expected finite event changes')
    (requirements/'approved-paths.txt').write_text('\n'.join(sorted(changed))+'\n',encoding='utf-8')
    samples=[]
    for role,paths in (('old',set(prior)-changed),('experimental',changed)):
        candidates=sorted(paths,key=lambda p:actual[p]['bytes'])
        for name in candidates:
            local=(PAYLOAD205 if role=='old' else payload)/name
            if not local.is_file():continue
            blob=local.read_bytes();row=actual[name]
            if len(blob)!=row['bytes'] or sha(blob)!=row['sha256']:continue
            sample=requirements/('cached-'+role+'.bin');sample.write_bytes(blob)
            namespace,leaf=name.split('/',1);directory={'story_ports':'story_ports/pilot1','battle':'battle/r8','encyclopedia':'encyclopedia/r7'}.get(namespace,namespace)
            relative=directory+'/'+row['sha256']+'/'+leaf
            (requirements/('cached-'+role+'.tsv')).write_text(name+'\t'+str(sample)+'\t'+relative+'\n',encoding='utf-8')
            samples.append({'role':role,'path':name,'sha256':sha(blob),'bytes':len(blob),'original_source':str(local),'relative_cache_path':relative});break
    require(len(samples)==2,'Need retained and revised exact payload samples')
    seeded={r['sha256'] for r in samples};partial=None
    for name in sorted(changed):
        row=actual[name]
        if row['sha256'] in seeded or row['wirebytes']<2:continue
        url=urllib.parse.urlsplit(row['url']);filename=url.path.rsplit('/',1)[1]
        local=next((p/filename for p in (ROOT/'asset_publication',FROZEN_PACKS,PAYLOAD205.parent/'asset_publication') if (p/filename).is_file()),None)
        if local is None:continue
        offset=row['offset']
        if url.fragment:offset+=int(url.fragment.split('=',1)[1].split(':')[0])
        with local.open('rb') as f:f.seek(offset);wire=f.read(row['wirebytes'])
        decoded=zlib.decompress(wire,-15) if row['method']==8 else wire
        require(len(decoded)==row['bytes'] and sha(decoded)==row['sha256'],'Actual saved-partial source pin differs')
        blob=wire[:min(17,len(wire)-1)];sample=requirements/'genuine206.part';sample.write_bytes(blob)
        (requirements/'partial.tsv').write_text(name+'\t'+str(sample)+'\n',encoding='utf-8')
        partial={'path':name,'source_pack':str(local),'physical_offset':offset,'saved_bytes':len(blob),'saved_sha256':sha(blob),'full_wire_sha256':sha(wire)};break
    require(partial is not None,'No genuine changed event slice available for partial fixture')
    targets=[];target_lines=[]
    for name in sorted(changed):
        require(name.startswith('side_stories/'),'Unrequested changed namespace')
        before=(PAYLOAD205/name).read_bytes();after=(payload/name).read_bytes()
        require(sha(before)==prior[name]['sha256'] and len(before)==prior[name]['bytes'],'Old205 target source pin differs')
        require(sha(after)==actual[name]['sha256'] and len(after)==actual[name]['bytes'],'New206 target source pin differs')
        leaf=name.removeprefix('side_stories/');old_relative='side_stories/'+prior[name]['sha256']+'/'+leaf;new_relative='side_stories/'+actual[name]['sha256']+'/'+leaf
        target_lines.append('\t'.join((name,str(PAYLOAD205/name),str(payload/name),prior[name]['sha256'],actual[name]['sha256'],old_relative,new_relative)))
        targets.append({'path':name,'old_sha256':prior[name]['sha256'],'new_sha256':actual[name]['sha256'],'old_cache_path':old_relative,'new_cache_path':new_relative})
    (requirements/'old205-targets.tsv').write_text('\n'.join(target_lines)+'\n',encoding='utf-8')
    shutil.copytree(SOURCE205,source)
    source_pins={p.relative_to(SOURCE205).as_posix():g.common.file_sha(p) for p in SOURCE205.rglob('*.java')}
    reference_pins_path=HOST/'REFERENCE205_JVM_SOURCES.json'
    require(g.common.file_sha(reference_pins_path)==REFERENCE205_PIN_SHA,'Sealed205 readable JVM reference inventory differs')
    reference_pins=json.loads(reference_pins_path.read_bytes())
    require(reference_pins['java_source_pins']==source_pins and reference_pins['baseline205_apk_sha256']==g.BASELINE205_SHA,'Readable205 reference source differs from frozen admission snapshot')
    require(g.common.file_sha(reference_pins['qualified205_host_report'])==reference_pins['qualified205_host_report_sha256'],'Original205 host qualification receipt differs')
    require(all(g.common.file_sha(source/name)==pin for name,pin in source_pins.items()),'Retained205 JVM reference source copy differs')
    android=Path('T:/Projects/FFBE Patch/story-ports/side-stories/delivery/android.jar');results=[]
    commands=[('compile',['javac','--release','8','-encoding','UTF-8','-cp',android,'-d',classes,*sorted(source.rglob('*.java')),HOST/'ActualCatalog206Test.java',HOST/'Old205TargetCacheTest.java']),
              ('ActualCatalog206Test',['java','-cp',str(classes)+';'+str(android),'O1.ActualCatalog206Test',payload,baseline,fixtures,requirements]),
              ('Old205TargetCacheTest',['java','-cp',str(classes)+';'+str(android),'O1.Old205TargetCacheTest',payload,baseline,fixtures,requirements])]
    for label,command in commands:
        start=time.monotonic();result=subprocess.run(list(map(str,command)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        item={'label':label,'exit_code':result.returncode,'seconds':round(time.monotonic()-start,3),'stdout':result.stdout,'stderr':result.stderr};results.append(item)
        (work/(label+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
        require(result.returncode==0,'Host fixture failed: '+label+'; see '+str(work))
        print(label+': '+result.stdout.strip(),flush=True)
    counts=[int(re.search(r'PASSED (\d+)',r['stdout'])[1]) for r in results[1:]]
    report={'schema':'ffbe-actual206-catalog-and205-target-cache-v1','passed':True,'assertions':sum(counts),'fixture_assertions':counts,
            'actual_catalog_sha256':g.common.file_sha(payload/'content_delivery.tsv'),'actual_side_manifest_sha256':g.common.file_sha(payload/'side_stories/manifest.tsv'),
            'catalog_sha256':g.common.file_sha(payload/'content_delivery.tsv'),'side_manifest_sha256':g.common.file_sha(payload/'side_stories/manifest.tsv'),
            'apk_sha256':g.common.file_sha(args.apk) if args.apk else None,'apk_bytes':args.apk.stat().st_size if args.apk else None,
            'baseline205_apk_sha256':g.BASELINE205_SHA,'runtime_dex_sha256':g.BASELINE205_DEX_SHA,'catalog_rows':len(actual),
            'changed_paths':sorted(changed),'retained_verified_cache_samples':samples,'genuine_saved_partial':partial,'old205_target_sources':targets,
            'results':results,'retained_reference_source_pins':source_pins,'fixture_source_pins':{p.name:g.common.file_sha(p) for p in (HOST/'ActualCatalog206Test.java',HOST/'Old205TargetCacheTest.java',Path(__file__))},
            'sealed_reference_inventory_sha256':REFERENCE205_PIN_SHA,
            'work_directory':str(work),'network_requested':False,'device_or_user_cache_or_save_actions':False,'runtime_verified':False,
            'runtime_fixture_scope':'Isolated JVM, retained205/P5 downloader and table classes. Real206 catalog admission, original callbacks, cache queues and totals, genuine saved partial, every changed prior205 target refreshed using exact new cache bytes, unknown-source authority, corrupt-new-cache fallback, isolated saves retained. No Android/native gameplay or actual transfers.',
            'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (ROOT/'audit/ACTUAL206_CATALOG_HOST_ADMISSION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'assertions':sum(counts),'changed_targets':len(targets),'catalog_rows':len(actual)}))

if __name__=='__main__':main()
