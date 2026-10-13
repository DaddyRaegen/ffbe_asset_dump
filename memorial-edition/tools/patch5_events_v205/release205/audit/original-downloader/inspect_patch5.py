"""Read-only review of the literal Patch 5 APK and retained range-capable sources."""
from pathlib import Path
import collections
import hashlib
import json
import subprocess
import zipfile

OUT = Path(__file__).resolve().parent
APK = Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-09-29-units-cards-ios\dist\FFBE-Memorial-EN-Patch-5-Units-Cards.apk')
OLD_JAVA = Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-09-25-download-recovery\delivery\java\O1')
EXPECTED = '534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
def sha(blob):return hashlib.sha256(blob).hexdigest()
def parse(blob):
    lines=blob.decode('utf-8').splitlines()
    return lines[0],[line.split('\t') for line in lines[1:]]

assert sha(APK.read_bytes()) == EXPECTED
with zipfile.ZipFile(APK) as archive:
    content=archive.read('assets/content_delivery.tsv')
    base=archive.read('assets/base_delivery.tsv')
    manifest=archive.read('assets/side_stories/manifest.tsv')
    script=archive.read('assets/frida_script.js')
    dex=archive.read('classes.dex')
    for name,blob in [('content_delivery.tsv',content),('base_delivery.tsv',base),
                      ('side_stories-manifest.tsv',manifest),('frida_script.js',script)]:
        (OUT/name).write_bytes(blob)
    assets=[name for name in archive.namelist() if name.startswith('assets/') and not name.endswith('/')]

classes=['O1/e','O1/ContentDownloader','O1/ContentDownloader$1','O1/ContentDownloader$1$1',
         'O1/ContentDownloader$2','O1/ContentDownloader$2$1','O1/ContentDownloader$2$2',
         'O1/CdnDownloader','O1/CdnDownloader$FileEntry','O1/ExtraContent','O1/ExtraContent$Entry',
         'O1/ExtraContent$1','O1/ExtraContent$2','O1/ResumableTransfer',
         'O1/ResumableTransfer$Source','O1/ResumableTransfer$Redirect',
         'O1/ResumableTransfer$Attempt','O1/SideStoryTables','O1/StoryPortTables',
         'com/square_enix/ffbejpn/Lapis','com/square_enix/ffbejpn/FridaBootstrap',
         'org/cocos2dx/lib/Cocos2dxActivity']
command=['java','-jar',r'T:\Projects\FFBE Patch\tools\bin\baksmali.jar','d',
         '--classes',','.join('L'+name+';' for name in classes),'-o',str(OUT/'smali'),str(APK)]
completed=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
(OUT/'baksmali-readonly.txt').write_text(completed.stdout+completed.stderr,encoding='utf-8')
assert completed.returncode==0
assert all((OUT/'smali'/f'{name}.smali').is_file() for name in classes)

chead,crows=parse(content);bhead,brows=parse(base)
assert chead=='ffbe-content-v1' and bhead=='ffbe-base-v1'
newhead,nrows=parse(Path(r'S:\FFBE JP Data Export\build\v204-startup-fix\payload\content_delivery.tsv').read_bytes())
old={r[0]:r for r in crows};new={r[0]:r for r in nrows}
common=set(old)&set(new);unchanged=[p for p in common if old[p]==new[p]]
samebytes=[p for p in common if old[p][1:3]==new[p][1:3]]
changedbytes=[p for p in common if old[p][1:3]!=new[p][1:3]]
added=sorted(set(new)-set(old))
sources=[{'path':str(OLD_JAVA/(name+'.java')),'sha256':sha((OLD_JAVA/(name+'.java')).read_bytes())}
         for name in ('ContentDownloader','CdnDownloader','ExtraContent','ResumableTransfer')]
required=['githubRelease','ffbe-range=','release-assets.githubusercontent.com','Content-Range']
actual=(OUT/'smali/O1/ResumableTransfer.smali').read_text(encoding='utf-8')
assert all(marker in actual for marker in required)
entry=(OUT/'smali/O1/ExtraContent$Entry.smali').read_text(encoding='utf-8')
assert '(side_stories|story_ports|battle|encyclopedia)' in entry

report={
    'schema':'ffbe-patch5-original-downloader-readonly-v1','passed':True,
    'source_apk':str(APK),'source_apk_sha256':EXPECTED,'original_dex_sha256':sha(dex),
    'apk_assets':len(assets),'content_tsv_sha256':sha(content),'content_rows':len(crows),
    'content_namespace_counts':dict(collections.Counter(r[0].split('/')[0] for r in crows)),
    'base_tsv_sha256':sha(base),'base_rows':len(brows),
    'base_url_hosts':dict(collections.Counter(r[4].split('/')[2] for r in brows)),
    'content_url_hosts':dict(collections.Counter(r[3].split('/')[2] for r in crows)),
    'side_stories_manifest_sha256':sha(manifest),'side_stories_manifest_rows':len(manifest.decode('utf-8').splitlines()),
    'original_frida_script_sha256':sha(script),
    'shipped_packed_github_range_support_confirmed':True,
    'actual_apk_decoded_class_count':len(classes),
    'actual_smali':{'path':str(OUT/'smali'),'files':[{'path':name+'.smali','sha256':sha((OUT/'smali'/f'{name}.smali').read_bytes())}for name in classes]},
    'retained_readable_sources':sources,
    'retained_java_source_identity_note':'Readable historical sources reviewed against actual shipped smali; source compile equivalence not claimed.',
    'comparison_to_full203_catalog':{
        'rows':len(nrows),'same_path_count':len(common),'exact_same_rows':len(unchanged),
        'same_hash_and_size_count':len(samebytes),'changed_hash_or_size_count':len(changedbytes),
        'added_rows':len(added),'added_namespaces':dict(collections.Counter(p.split('/')[0] for p in added)),
        'all_added_namespaces_supported_by_original_extra_content':all(p.split('/')[0] in ('side_stories','story_ports','battle','encyclopedia')for p in added),
        'added_paths':added,'changed_hash_or_size_paths':sorted(changedbytes),
        'full203_catalog_not_recommended':'Only event closure belongs in new pinned rows; preserve all original Patch 5 routes.'},
    'no_source_edits':True,'network':False,'device_actions':False,
}
(OUT/'PATCH5_ORIGINAL_DOWNLOADER.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:report[key]for key in ('source_apk_sha256','content_rows','content_namespace_counts',
                 'base_rows','base_url_hosts','shipped_packed_github_range_support_confirmed','actual_apk_decoded_class_count')},indent=2))
print(json.dumps({key:value for key,value in report['comparison_to_full203_catalog'].items()if key not in ('added_paths','changed_hash_or_size_paths')},indent=2))
