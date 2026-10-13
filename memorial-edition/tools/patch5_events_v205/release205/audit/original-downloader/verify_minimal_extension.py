"""Test the sealed smali edit and equivalent minimal readable-Java reference."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parent
STAGE = ROOT.parents[1]
OLD = Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-09-25-download-recovery')
SIDESOURCE = Path(r'T:\Projects\FFBE Patch\story-ports\side-stories\delivery\java\O1\SideStoryTables.java')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load_helper():
    spec=importlib.util.spec_from_file_location('minimal_event_paths',STAGE/'source/patch_event_paths.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
helper=load_helper()
tests=[]
def run(label,args):
    start=time.monotonic();r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    row={'label':label,'exit_code':r.returncode,'seconds':round(time.monotonic()-start,3),'stdout':r.stdout,'stderr':r.stderr};tests.append(row)
    print(label+': '+str(r.returncode)+' '+r.stdout.strip(),flush=True)
    assert r.returncode==0,(label,r.stderr)
    return row

patched=ROOT/'patched-smali'
patched.mkdir(exist_ok=True)
for name in helper.ORIGINAL_CLASS_PINS:
    dest=patched/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'smali'/name,dest)
receipt=helper.patch_smali(patched)
method_deltas=[];checks=0
def methods(text):return dict((m.group(1),m.group(0))for m in re.finditer(r'^\.method ([^\n]+)\n.*?^\.end method',text,re.M|re.S))
allowed={'O1/ExtraContent$Entry.smali': {'constructor <init>([Ljava/lang/String;)V'},
         'O1/SideStoryTables.smali': {'public static declared-synchronized choose(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;','private static load(Ljava/lang/Object;)V'}}
for name in helper.ORIGINAL_CLASS_PINS:
    before=(ROOT/'smali'/name).read_text(encoding='utf-8');after=(patched/name).read_text(encoding='utf-8')
    old=methods(before);new=methods(after);assert set(old)==set(new);checks+=1
    changed={signature for signature in old if old[signature]!=new[signature]}
    assert changed==allowed[name];checks+=1
    method_deltas.append({'path':name,'changed_methods':sorted(changed),'all_other_methods_byte_identical':True})
    for invalid in (before+'\n# changed baseline\n',after):
        try:helper.patch_text(name,invalid)
        except ValueError:checks+=1
        else:raise AssertionError('Modified or already-patched class accepted')

assembled=ROOT/'patched-reference.dex'
assembler_classes=ROOT/'assembler-classes';assembler_classes.mkdir(exist_ok=True)
apktool=Path(r'T:\Projects\FFBE Patch\tools\bin\apktool.jar')
run('compile-isolated-retained-assembler-wrapper',['javac','--release','8','-cp',apktool,'-d',assembler_classes,ROOT/'AssembleReference.java'])
run('assemble-two-class-minimal-smali',['java','-cp',str(assembler_classes)+';'+str(apktool),'AssembleReference',patched,assembled])
run('decode-patched-two-class-reference',['java','-jar',r'T:\Projects\FFBE Patch\tools\bin\baksmali.jar','d',assembled,'-o',ROOT/'patched-decoded-smali'])
for row in receipt['classes']:
    row['assembled_reference_decoded_sha256']=digest(ROOT/'patched-decoded-smali'/row['path'])

java=ROOT/'host-source/O1';java.mkdir(parents=True,exist_ok=True)
source_pins=[]
for name in ('ExtraContent','ResumableTransfer','CdnDownloader'):
    source=OLD/'delivery/java/O1'/f'{name}.java';dest=java/f'{name}.java'
    text=source.read_text(encoding='utf-8')
    if name=='ExtraContent':
        needle='"'+helper.ORIGINAL_EXTRA_PATH_PATTERN+'"';assert text.count(needle)==1
        text=text.replace(needle,'"'+helper.EXTRA_PATH_PATTERN+'"')
    dest.write_text(text,encoding='utf-8');source_pins.append({'path':str(source),'sha256':digest(source),'reference':str(dest),'reference_sha256':digest(dest),'only_change':'narrow scene path predicate'if name=='ExtraContent'else'line endings only; original Java statements unchanged'})
text=SIDESOURCE.read_text(encoding='utf-8');needle='"'+helper.ORIGINAL_SIDE_PATH_PATTERN+'"';assert text.count(needle)==2
text=text.replace(needle,'"'+helper.SIDE_PATH_PATTERN+'"')
before='if(!dir.isDirectory()&&!dir.mkdirs())return original;File temp=new File(dir,name+".tmp");'
after='File parent=target.getParentFile();if(!parent.isDirectory()&&!parent.mkdirs())return original;File temp=new File(dir,name+".tmp");'
assert text.count(before)==1;text=text.replace(before,after)
(java/'SideStoryTables.java').write_text(text,encoding='utf-8')
source_pins.append({'path':str(SIDESOURCE),'sha256':digest(SIDESOURCE),'reference':str(java/'SideStoryTables.java'),'reference_sha256':digest(java/'SideStoryTables.java'),'only_changes':'two narrow scene path predicates; target parent mkdir'})
stubs=ROOT/'host-source/android';shutil.copytree(OLD/'tests/android',stubs,dirs_exist_ok=True)
test_source=ROOT/'host-tests';test_source.mkdir(exist_ok=True)
names=('TransferTest','GithubTransferTest','BaseTest','ExtraContentTest','PackedExtraContentTest','NestedScenePathsTest')
for name in names:
    src=ROOT/f'{name}.java' if name=='NestedScenePathsTest'else OLD/'tests'/f'{name}.java'
    shutil.copyfile(src,test_source/src.name)
classes=ROOT/'host-classes';classes.mkdir(exist_ok=True);fixtures=ROOT/'host-fixtures';fixtures.mkdir(exist_ok=True)
sources=sorted((ROOT/'host-source').rglob('*.java'))+sorted(test_source.glob('*.java'))
run('compile-original-reference-with-only-path-extension',['javac','--release','8','-encoding','UTF-8','-d',classes,*sources])
for name in names:run(name,['java','-cp',classes,'O1.'+name,fixtures])
report={'schema':'ffbe-patch5-minimal-event-paths-host-test-v1','passed':True,
        'source_apk_sha256':helper.PATCH5_APK_SHA256,'smali_receipt':receipt,
        'exact_smali_method_delta_checks':checks,'smali_method_deltas':method_deltas,
        'results':tests,'readable_reference_source_pins':source_pins,
        'smali_helper_sha256':digest(STAGE/'source/patch_event_paths.py'),
        'network':'in-memory fake HTTPS fixtures only','no_external_network':True,
        'compiled_Java_used_in_APK':False,'APK_modified':False,'runtime_verified':False,
        'device_or_save_actions':False}
(ROOT/'MINIMAL_EXTENSION_TESTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(STAGE/'audit/MINIMAL_RUNTIME_SOURCE_REVIEW.json').write_text(json.dumps({
    'schema':'ffbe-patch5-minimal-runtime-source-review-v1','passed':True,
    'source_apk_sha256':helper.PATCH5_APK_SHA256,'helper':str(STAGE/'source/patch_event_paths.py'),
    'helper_sha256':digest(STAGE/'source/patch_event_paths.py'),'class_delta':receipt,
    'test_report':str(ROOT/'MINIMAL_EXTENSION_TESTS.json'),'test_report_sha256':digest(ROOT/'MINIMAL_EXTENSION_TESTS.json'),
    'original_downloader_report':str(ROOT/'PATCH5_ORIGINAL_DOWNLOADER.json'),
    'original_Patch5_data_routes_preserved':True,'versioned_graph_OTA_added':False,
    'new_startup_gate_added':False,'full203overlay_used':False,
    'runtime_verified':False,'scope':'Literal Patch 5 classes plus only two class/three method nested-scene path edits; isolated host reference and smali assembly checks.'},indent=2)+'\n',encoding='utf-8')
print('PASSED minimal source review; exact class and host evidence saved',flush=True)
