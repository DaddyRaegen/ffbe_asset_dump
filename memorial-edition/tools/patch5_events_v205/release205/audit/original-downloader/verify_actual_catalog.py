"""Independent actual metadata admission and isolated P5/203 cache compatibility test."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import time
import urllib.parse
import zipfile
import zlib

ROOT=Path(__file__).resolve().parent;STAGE=ROOT.parents[1]
PLAN=STAGE/'audit/EVENT_PLAN.json';PAYLOAD=STAGE/'payload';DOWNLOAD=STAGE/'asset_publication/DOWNLOAD_PLAN.json'
FROZEN=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\full_inventory\recovery_round2\build_release\FFBE-Memorial-EN-Patch-6-Full-Inventory-Round2.apk')
ORIGINAL_SOURCE=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-09-25-download-recovery\delivery\java\O1')
TABLE_SOURCE=Path(r'T:\Projects\FFBE Patch\story-ports\side-stories\delivery\java\O1')
JAVA203=Path(r'S:\FFBE JP Data Export\ffbe_asset_dump\tools\native_delivery_v203\java\O1\ExtraContent.java')
SOURCE_PACKS=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction\asset_publication')
def sha(data):return hashlib.sha256(data).hexdigest()
def digest(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def catalog(path):
    lines=path.read_text(encoding='utf-8').splitlines();assert lines[0]=='ffbe-content-v1'
    pairs=[line.split('\t')for line in lines[1:]];assert all(len(p)==8 for p in pairs)
    rows={p[0]:p for p in pairs};assert len(rows)==len(pairs);return rows
def method(text,start):
    body=text.split(start,1)[1].split('\n    }',1)[0];return body
def normalized(text):return re.sub(r'\s+','',text)

assert PLAN.is_file()and DOWNLOAD.is_file()and(PAYLOAD/'content_delivery.tsv').is_file(),'Actual205 metadata is not ready'
original=catalog(ROOT/'content_delivery.tsv');actual=catalog(PAYLOAD/'content_delivery.tsv')
plan=json.loads(PLAN.read_bytes());download=json.loads(DOWNLOAD.read_bytes());assert download['passed']
approved={a['path']for a in plan['assets']};changed={p for p in original if actual.get(p)!=original[p]};added=set(actual)-set(original)
assert len(original)==1411 and set(original).issubset(actual)and changed|added<=approved
assert list(actual)[:len(original)]==list(original)
for p in set(original)-changed:assert actual[p]==original[p]

# Compare the actual203 method body with literal P5, allowing only the unrelated root-object branch.
p5=(ROOT/'host-source/O1/ExtraContent.java').read_text(encoding='utf-8');v203=JAVA203.read_text(encoding='utf-8')
sig='static File target(Entry e) throws Exception {'
p5body=method(p5,sig)
v203body=method(v203,sig)
non_side='        if(!p[0].matches("side_stories|story_ports|battle|encyclopedia"))return new File(files(),"game_assets/objects/"+e.hash+"/"+e.path);'
assert v203body.count(non_side)==1 and normalized(p5body)==normalized(v203body.replace(non_side,''))
partial_p5=re.search(r'private static File partial\(Entry e\) throws Exception \{([^}]+)\}',p5).group(1)
partial_203=re.search(r'private static File partial\(Entry e\) throws Exception \{([^}]+)\}',v203).group(1)
assert normalized(partial_p5)==normalized(partial_203)

requirements=ROOT/'actual-catalog/requirements';requirements.mkdir(parents=True,exist_ok=True)
(requirements/'approved-paths.txt').write_text('\n'.join(sorted(approved))+'\n',encoding='utf-8')
samples=[]
old_content_source=Path(plan['production_content_source'])
with zipfile.ZipFile(old_content_source)as z:
    members=set(z.namelist())
    for path,row in sorted(original.items(),key=lambda kv:int(kv[1][2])):
        member='assets/'+path
        if path in changed or path in approved or member not in members:continue
        blob=z.read(member)
        if len(blob)==int(row[2])and sha(blob)==row[1]:
            sample=requirements/'unchanged-old.bin';sample.write_bytes(blob);samples.append({'role':'old','path':path,'sample':str(sample),'sha256':row[1],'bytes':len(blob),'source_apk':str(old_content_source),'source_member':member,'sample_matches_literal_P5_signed_descriptor':True});break
assert len(samples)==1,'No matching retained P5-content bytes found for isolated inherited-cache proof'
for item in sorted(plan['assets'],key=lambda a:a['bytes']):
    path=item['path']
    if path not in added or actual[path][1]==samples[0]['sha256']:continue
    local=Path(item.get('local_path')or PAYLOAD/path);blob=local.read_bytes();row=actual[path]
    assert len(blob)==int(row[2])and sha(blob)==row[1]
    sample=requirements/'experimental-event.bin';sample.write_bytes(blob);samples.append({'role':'experimental','path':path,'sample':str(sample),'sha256':row[1],'bytes':len(blob)});break
assert len(samples)==2
for sample in samples:
    path=sample['path'];namespace,leaf=path.split('/',1);directory={'story_ports':'story_ports/pilot1','battle':'battle/r8','encyclopedia':'encyclopedia/r7'}.get(namespace,namespace)
    relative=directory+'/'+sample['sha256']+'/'+leaf;sample['relative_cache_path']=relative
    (requirements/('cached-'+sample['role']+'.tsv')).write_text(path+'\t'+sample['sample']+'\t'+relative+'\n',encoding='utf-8')

seeded_hashes={s['sha256']for s in samples};partial=None
for path in sorted(changed|added):
    row=actual[path]
    if row[1]in seeded_hashes or int(row[5])<2:continue
    url=urllib.parse.urlsplit(row[3]);filename=url.path.split('/')[-1]
    pack=STAGE/'asset_publication'/filename
    if not pack.is_file():pack=SOURCE_PACKS/filename
    if not pack.is_file():continue
    physical=int(row[4]);source_size=int(row[7])
    if url.fragment:
        assert url.fragment.startswith('ffbe-range=');start,size,total=map(int,url.fragment.split('=',1)[1].split(':'));assert size==source_size;physical+=start
    with pack.open('rb')as f:f.seek(physical);wire=f.read(int(row[5]))
    plain=wire if row[6]=='0'else zlib.decompress(wire,-15);assert len(plain)==int(row[2])and sha(plain)==row[1]
    part=wire[:min(17,len(wire)-1)];sample=requirements/'genuine-event.part';sample.write_bytes(part)
    (requirements/'partial.tsv').write_text(path+'\t'+str(sample)+'\n',encoding='utf-8')
    partial={'path':path,'sha256':row[1],'wire_bytes':int(row[5]),'saved_bytes':len(part),'actual_pack':str(pack),'physical_offset':physical,'wire_sha256':sha(wire),'saved_partial_sha256':sha(part)};break
assert partial,'No actual staged compressed range available for saved partial proof'

source=ROOT/'actual-catalog/source';shutil.copytree(ROOT/'host-source',source,dirs_exist_ok=True)
shutil.copyfile(ORIGINAL_SOURCE/'ContentDownloader.java',source/'O1/ContentDownloader.java')
shutil.copyfile(TABLE_SOURCE/'StoryPortTables.java',source/'O1/StoryPortTables.java')
classes=ROOT/'actual-catalog/classes';classes.mkdir(parents=True,exist_ok=True);fixtures=ROOT/'actual-catalog/fixtures';fixtures.mkdir(exist_ok=True)
android=Path(r'T:\Projects\FFBE Patch\story-ports\side-stories\delivery\android.jar')
results=[]
for label,args in [('compile-literal-P5-reference-and-actual-catalog-fixture',['javac','--release','8','-encoding','UTF-8','-cp',android,'-d',classes,*sorted(source.rglob('*.java')),ROOT/'ActualCatalogTest.java']),('ActualCatalogTest',['java','-cp',str(classes)+';'+str(android),'O1.ActualCatalogTest',PAYLOAD,ROOT,fixtures,requirements])]:
    start=time.monotonic();r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180);results.append({'label':label,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,3),'stdout':r.stdout,'stderr':r.stderr});print(label+': '+str(r.returncode)+' '+r.stdout.strip(),flush=True);assert r.returncode==0,r.stderr
report={'schema':'ffbe-patch5-actual205-catalog-host-admission-v1','passed':True,
        'catalog_sha256':digest(PAYLOAD/'content_delivery.tsv'),'catalog_bytes':(PAYLOAD/'content_delivery.tsv').stat().st_size,'side_manifest_sha256':digest(PAYLOAD/'side_stories/manifest.tsv'),'event_plan_sha256':digest(PLAN),
        'original_descriptor_rows':len(original),'final_descriptor_rows':len(actual),'unchanged_original_rows':len(original)-len(changed),'approved_changed_original_paths':sorted(changed),'added_event_rows':len(added),'results':results,
        'isolated_verified_cache_samples':samples,'genuine_saved_partial':partial,
        'P5_203_side_story_target_body_identical':True,'P5_203_partial_target_identical':True,'actual203_source':str(JAVA203),'actual203_source_sha256':digest(JAVA203),
        'source_statement_edits_only_minimal_path_extension':True,'original_ContentDownloader_reference_sha256':digest(source/'O1/ContentDownloader.java'),
        'helper_frozen_sha256':digest(STAGE/'source/patch_event_paths.py'),'APK_code_modified':False,'network_requested':False,'device_or_user_cache_or_save_actions':False,'runtime_verified':False,
        'runtime_fixture_scope':'Isolated JVM using retained readable Patch 5 ExtraContent/CdnDownloader/ContentDownloader/SideStoryTables with only the approved nested scene predicates and parent mkdir reference. Every actual205 content row and side-manifest row admitted; native callback state/totals, verified original/compatible203-layout cache objects and genuine partial length tested. No real transfers, Android native lifecycle, physical files or saves tested.',
        'device_runtime_tested':False}
(STAGE/'audit/ACTUAL205_CATALOG_HOST_ADMISSION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('PASSED actual205 catalog admission and unchanged native queue/cache compatibility',flush=True)
