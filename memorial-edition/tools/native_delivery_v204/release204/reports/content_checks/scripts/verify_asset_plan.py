from pathlib import Path
import json,hashlib,zlib,urllib.parse
ROOT=Path('C:\\Users\\Raegen\\Documents\\Codex\\2026-10-02\\task-2\\integration_work\\native_delivery_correction')
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    stage=ROOT/'asset_publication';plan=json.loads((stage/'frozen-plan.json').read_text());manifest=json.loads((stage/'manifest.json').read_text());checks=0
    def check(condition,name):
        nonlocal checks;checks+=1
        if not condition:raise AssertionError(name)
    check(manifest['channel']==plan['branch']==plan['channel']=='beta','channel isolation')
    check(manifest['asset_version']==plan['version_code']==manifest['APK_min_version']==203,'version coherence')
    check(manifest['engine_compat']=='ffbe-native-delivery-v203' and plan['prerelease'] and not plan['make_latest'],'native engine and no production promotion')
    files={x['name']:x for x in plan['files']}
    for f in plan['files']+plan['pointers']:
        p=Path(f['local_path'])
        with p.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        check(actual==f['sha256'] and p.stat().st_size==f['bytes'],'frozen artifact hash/size')
    root_rows=[x.split('\t') for x in (ROOT/'payload/root_delivery.tsv').read_text().splitlines()[1:]]
    content_rows=[x.split('\t') for x in (ROOT/'payload/content_delivery.tsv').read_text().splitlines()[1:]]
    base_rows=[x.split('\t') for x in (ROOT/'payload/base_delivery.tsv').read_text().splitlines()[1:]]
    assets={(x['namespace'],x['path']):x for x in manifest['assets']}
    check(len(assets)==len(manifest['assets'])==5201,'unique namespace/path identity')
    check(len(root_rows)==663 and len(content_rows)==1411 and len(base_rows)==3127,'source record counts')
    for namespace,rows in [('root',root_rows),('content',content_rows)]:
        check(len({r[0] for r in rows})==len(rows),'unique catalog paths')
        for row in rows:
            path,h,n,url,off,wire,method,total=row;asset=assets[namespace,path]
            check(asset['sha256']==h and asset['bytes']==int(n) and 0<asset['version']<=203,'asset revision/hash/size')
            check(asset['transport']=={'url':url,'offset':int(off),'wire_bytes':int(wire),'method':int(method),'source_bytes':int(total)},'native transport fields')
            parsed=urllib.parse.urlparse(url)
            check(parsed.scheme=='https' and parsed.hostname=='github.com' and parsed.path.startswith('/luminest-llc/ffbe-memorial-downloads/releases/download/'),'verified project data destination')
    check((ROOT/'payload/base_delivery.tsv').read_bytes()==(ROOT.parent/'thin_delivery/payload/base_delivery.tsv').read_bytes(),'base graph exactly preserved')
    opened={};pack_ranges={}
    try:
        for row in root_rows:
            path,h,n,url,off,wire,method,total=row;name=urllib.parse.urlparse(url).path.split('/')[-1];f=files[name]
            check(f['role']=='pack' and int(total)==f['bytes'] and 0<=int(off)<=int(total)-int(wire),'root range bounds')
            handle=opened.setdefault(name,Path(f['local_path']).open('rb')) if name not in opened else opened[name]
            handle.seek(int(off));compressed=handle.read(int(wire));check(len(compressed)==int(wire),'packed range length')
            data=zlib.decompress(compressed,-15) if int(method)==8 else compressed
            check(len(data)==int(n) and sha(data)==h and data==(ROOT/'payload'/path).read_bytes(),'every packed root asset decoded hash and original/corrected bytes')
            pack_ranges.setdefault(name,[]).append((int(off),int(wire)))
        for name,ranges in pack_ranges.items():
            position=0
            for start,n in sorted(ranges):check(start==position,'no pack gaps/overlap');position+=n
            check(position==files[name]['bytes'],'complete pack graph')
    finally:
        for handle in opened.values():handle.close()
    roots={r[0]:r for r in root_rows};overlap=[r for r in content_rows if r[0] in roots]
    check(len(overlap)==13 and all(r==roots[r[0]] for r in overlap),'all stale root/content conflicts resolved')
    for key in ('root','content','base'):
        info=manifest[key+'_catalog'];data=(ROOT/'payload'/({'root':'root_delivery.tsv','content':'content_delivery.tsv','base':'base_delivery.tsv'}[key])).read_bytes()
        check(sha(data)==info['sha256'] and len(data)==info['bytes'],'catalog pin bound to signed metadata')
        check(Path(files[info['url'].split('/')[-1]]['local_path']).read_bytes()==data,'immutable catalog publication matches metadata')
    release=(ROOT/'payload/delivery_release.tsv').read_text().splitlines()[1].split('\t')
    check(len(release)==7 and release[:3]==['beta','203','203'] and release[3]==manifest['root_catalog']['sha256'] and release[4]==manifest['content_catalog']['sha256'],'release pin and channel version')
    check(release[5]=='https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json' and release[6]=='https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/manifest.json','stable beta pointers isolated from production')
    updater=json.loads((stage/'patch_version.json').read_text());check(updater['version']==202 and updater['asset_version']==203 and not updater['apk_update_enabled'],'staged APK203 not announced')
    check(manifest['package']=='com.square_enix.ffbejpn' and manifest['signing_certificate_sha256']=='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee','manifest application identity')
    check(updater['package']=='com.square_enix.ffbejpn' and updater['versionCode']==202,'beta updater package/versionCode schema')
    report={'passed':True,'checks':checks,'manifest_sha256':sha((stage/'manifest.json').read_bytes()),'frozen_plan_sha256':sha((stage/'frozen-plan.json').read_bytes()),'all_663_packed_asset_bytes_independently_decoded_verified':True,'all_5201_versioned_manifest_records_checked':True,'thirteen_stale_catalog_conflicts_resolved':True,'unchanged_base_preserved':True,'no_production_manifest_or_APK_publication':True}
    Path('S:\\FFBE JP Data Export\\build\\v204-startup-fix\\audit\\content_checks\\ASSET_PLAN_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
