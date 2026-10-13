"""Read-only qualification of the actual native delivery manifests and signed APK.

No network, publication, game installation, cache or save actions. CLI verifies
Android tooling directly; fixture tests inject a runner only to test that interface.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
from urllib.parse import urlsplit
import zipfile

PACKAGE='com.square_enix.ffbejpn'
SIGNER='21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
REPO='luminest-llc/ffbe-memorial-downloads'
ENGINE='ffbe-native-delivery-v203'
BETA_PREFIX=f'https://raw.githubusercontent.com/{REPO}/beta/channels/beta/'
ALLOWED_ASSETS=frozenset({
    'assets/frida_script.js','assets/arm64-v8a/libparser.so','assets/armeabi-v7a/libparser.so',
    'assets/dexopt/baseline.prof','assets/dexopt/baseline.profm',
    'assets/base_delivery.tsv','assets/content_delivery.tsv','assets/root_delivery.tsv','assets/delivery_release.tsv','assets/game_asset_manifest.json',
})
BOOTSTRAP_MEMBER='assets/bootstrap_inventory.json'
BOOTSTRAP_SCHEMA='ffbe-bootstrap-inventory-v1'
BAD_CLASSES=(b'LO1/AssetBundle;',b'LO1/BundleAssets;',b'LO1/BootstrapActivity;',b'LO1/ThinBootstrap;')
HASH=re.compile(r'^[0-9a-f]{64}$')
DEFAULT_TOOLS=Path(r'T:\Projects\FFBE Patch\graphics-localization\2026-09-19\apk-build\tools\android-16')

def require(condition,message):
    if not condition: raise ValueError(message)

def integer(value,minimum=1):
    return type(value) is int and value>=minimum and value<=9223372036854775807

def digest(data): return hashlib.sha256(data).hexdigest()

def file_digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def unique_object(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'Duplicate JSON key: '+key);result[key]=value
    return result

def load_json(data):
    require(len(data)<=4*1024*1024,'Manifest exceeds native pointer bound')
    return json.loads(data.decode('utf-8'),object_pairs_hook=unique_object)

def safe_path(path):
    return isinstance(path,str) and len(path)<=512 and bool(re.fullmatch(r'[A-Za-z0-9_./-]+',path)) and all(p not in ('','.','..') for p in path.split('/'))

def release_url(value,allow_fragment=False):
    require(isinstance(value,str),'Transport URL is not a string')
    u=urlsplit(value)
    require(u.scheme=='https' and u.netloc=='github.com' and u.username is None and not u.query and bool(re.fullmatch('/'+REPO+r'/releases/download/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',u.path)),'Asset URL must use the established immutable GitHub repository')
    require(allow_fragment or not u.fragment,'Catalog URL cannot have a fragment')
    if u.fragment:
        match=re.fullmatch(r'ffbe-range=(\d+):(\d+):(\d+)',u.fragment)
        require(match is not None,'Unsupported asset range fragment')
        start,length,total=map(int,match.groups())
        require(length>0 and total>0 and start>=0 and start<=total-length,'Asset fragment exceeds source pack bounds')
        return start,length,total
    return None

def validate_transport(t,decoded_bytes):
    require(isinstance(t,dict),'Missing asset transport')
    fragment=release_url(t.get('url'),True)
    require(integer(t.get('offset'),0) and integer(t.get('wire_bytes')) and integer(t.get('source_bytes')),'Invalid transport size/offset')
    require(type(t.get('method')) is int and t['method'] in (0,8),'Unsupported native transport compression method')
    require(t['offset']<=t['source_bytes']-t['wire_bytes'],'Wire range exceeds selected source bounds')
    if fragment: require(fragment[1]==t['source_bytes'],'Range fragment length differs from native source_bytes')
    if t['method']==0: require(t['wire_bytes']==decoded_bytes,'Stored native member wire/decoded length differs')
    return t

def text_rows(data,header,fields,lf_only=False):
    require(len(data)<=8*1024*1024 and b'\0' not in data,'Native catalog exceeds bounds or contains NUL')
    require(not lf_only or b'\r' not in data,'Release metadata must use LF-only native records')
    lines=data.decode('utf-8').splitlines()
    require(lines and lines[0]==header,'Wrong native catalog header')
    result=[]
    for line in lines[1:]:
        p=line.split('\t');require(len(p)==fields,'Wrong native catalog field count');result.append(p)
    require(result,'Empty native catalog');return result

def parse_catalog(data,namespace):
    rows=text_rows(data,'ffbe-base-v1' if namespace=='base' else 'ffbe-content-v1',5 if namespace=='base' else 8)
    result={}
    for p in rows:
        if namespace=='base':
            path=p[0]+'/'+p[1];size=int(p[2]);h=p[3];url=p[4]
            f=release_url(url,True);source=f[1] if f else size
            t={'url':url,'offset':0,'wire_bytes':size,'method':0,'source_bytes':source}
        else:
            path,h,size,url=p[:4];size=int(size)
            t={'url':url,'offset':int(p[4]),'wire_bytes':int(p[5]),'method':int(p[6]),'source_bytes':int(p[7])}
        require(safe_path(path) and path not in result,'Unsafe or duplicate native catalog path: '+path)
        require(integer(size) and bool(HASH.fullmatch(h)),'Invalid native catalog hash or size')
        validate_transport(t,size);result[path]={'namespace':namespace,'path':path,'sha256':h,'bytes':size,'transport':t}
    return result

def validate_manifest(m,catalogs,previous=None,expected_apk_version=203,expected_asset_version=None):
    require(m.get('schema')=='ffbe-asset-manifest-v1' and m.get('channel')=='beta','Wrong actual manifest schema/channel')
    require(m.get('package')==PACKAGE and m.get('signing_certificate_sha256')==SIGNER,'Manifest app package/signing identity changed')
    require(m.get('engine_compat')==ENGINE,'Native engine compatibility changed')
    require(integer(m.get('asset_version')) and integer(m.get('APK_min_version')),'Missing versioned manifest compatibility')
    require(203<=m['APK_min_version']<=expected_apk_version and expected_apk_version>=203,'Manifest requires another APK or old correction version')
    if expected_asset_version is not None: require(m['asset_version']==expected_asset_version,'Asset-set version differs from build expectation')
    expected={}
    for namespace in ('root','content','base'):
        data=catalogs[namespace];pin=m.get(namespace+'_catalog')
        require(isinstance(pin,dict) and pin.get('sha256')==digest(data) and pin.get('bytes')==len(data),'Manifest/native catalog pin mismatch: '+namespace)
        release_url(pin.get('url'))
        expected.update({(namespace,path):entry for path,entry in parse_catalog(data,namespace).items()})
    require(sum(k[0]=='base' for k in expected)==3127,'Original base catalog must preserve all3127 rows')
    require(sum(k[0]=='content' for k in expected)==1411,'Content catalog must preserve all1411 paths')
    assets=m.get('assets');require(isinstance(assets,list) and assets,'Manifest has no per-file version graph')
    seen={};old={(e['namespace'],e['path']):e for e in (previous or {}).get('assets',[])}
    if previous:
        require(previous.get('channel')=='beta' and previous.get('engine_compat')==ENGINE,'Previous manifest has incompatible channel/engine')
        require(m['asset_version']>=previous['asset_version'],'Asset-set version rollback')
    for e in assets:
        require(isinstance(e,dict),'Asset row must be an object')
        key=(e.get('namespace'),e.get('path'))
        require(key[0] in ('root','content','base') and safe_path(key[1]) and key not in seen,'Duplicate/unsafe regional namespace/path identity')
        require(integer(e.get('version')) and integer(e.get('bytes')) and isinstance(e.get('sha256'),str) and bool(HASH.fullmatch(e['sha256'])),'Per-file version/hash/size missing')
        validate_transport(e.get('transport'),e['bytes'])
        require(key in expected,'Manifest file absent from native downloader catalogs: '+str(key))
        require(all(e.get(field)==expected[key][field] for field in ('namespace','path','sha256','bytes','transport')),'Manifest/native downloader record mismatch: '+str(key))
        if key[0]=='root': require(e.get('phase') in ('boot','game'),'Root asset boot/game phase missing')
        if key in old:
            require(e['version']>=old[key]['version'],'Per-file revision rollback')
            if e['sha256']!=old[key]['sha256']: require(e['version']>old[key]['version'],'Changed asset bytes without revision increment')
        seen[key]=e
    require(set(seen)==set(expected),'Manifest does not enumerate the complete native graph')
    require(set(old)<=set(seen),'Updated manifest silently removes existing assets')
    roots={k[1]:v for k,v in seen.items() if k[0]=='root'}
    for key,e in seen.items():
        if key[0]=='content' and key[1] in roots:
            r=roots[key[1]];require(e['sha256']==r['sha256'] and e['bytes']==r['bytes'],'Root/content logical path has conflicting bytes: '+key[1])
    return {'asset_version':m['asset_version'],'APK_min_version':m['APK_min_version'],'namespace_counts':dict(Counter(k[0] for k in seen)),'per_file_versions_verified':len(seen),'root_content_shared_paths':len(set(roots)&{k[1] for k in seen if k[0]=='content'})}

def validate_release_metadata(data,catalogs,apk_version,asset_version):
    p=text_rows(data,'ffbe-delivery-release-v1',7,True)
    require(len(p)==1,'Release metadata must have exactly one row');p=p[0]
    require(p[:3]==['beta',str(asset_version),str(apk_version)],'Release metadata channel/versions differ')
    require(p[3:5]==[digest(catalogs['root']),digest(catalogs['content'])],'Release metadata baseline pins differ')
    require(p[5:]==[BETA_PREFIX+'patch_version.json',BETA_PREFIX+'manifest.json'],'Release metadata follows wrong updater/asset channel')
    return p

def validate_bootstrap_inventory(data,manifest_data,apk_version):
    """Allow only an explicit signed subset of the already qualified root graph.

    APK and asset-set versions may advance independently. Bootstrap bytes do not
    replace catalog rows or their immutable GitHub transport, so absent/changed
    non-bootstrap files retain the native per-file downloader.
    """
    inventory=load_json(data);manifest=load_json(manifest_data)
    require(isinstance(inventory,dict) and inventory.get('schema')==BOOTSTRAP_SCHEMA,'Wrong bootstrap inventory schema')
    require(inventory.get('package')==PACKAGE and inventory.get('signing_certificate_sha256')==SIGNER,'Bootstrap inventory app identity changed')
    require(inventory.get('APK_version')==apk_version and integer(inventory.get('APK_version')),'Bootstrap inventory APK version differs')
    require(apk_version>=204,'Startup correction APK must exceed203')
    require(inventory.get('asset_version')==manifest.get('asset_version') and integer(inventory.get('asset_version')),'Bootstrap inventory asset version differs')
    require(inventory.get('manifest_sha256')==digest(manifest_data),'Bootstrap inventory manifest pin differs')
    rows=inventory.get('assets');require(isinstance(rows,list) and rows,'Bootstrap inventory has no exact asset allowlist')
    graph={(e['namespace'],e['path']):e for e in manifest['assets']}
    selected={};identities=set()
    for row in rows:
        require(isinstance(row,dict),'Bootstrap inventory row must be an object')
        namespace,path=row.get('namespace'),row.get('path')
        require(namespace=='root' and safe_path(path),'Bootstrap inventory must select a safe native root asset')
        member='assets/'+path
        require(row.get('apk_path')==member and member not in ALLOWED_ASSETS and member!=BOOTSTRAP_MEMBER,'Bootstrap inventory APK path differs or overlaps delivery metadata')
        require(not member.lower().endswith('.zip') and Path(member).name!='asset_bundle.tsv','Custom bulk ZIP bootstrap is forbidden')
        require(member not in selected,'Duplicate bootstrap inventory APK path')
        require(integer(row.get('bytes')) and isinstance(row.get('sha256'),str) and bool(HASH.fullmatch(row['sha256'])),'Bootstrap inventory hash/size missing')
        key=(namespace,path);require(key in graph,'Bootstrap inventory asset absent from signed per-file manifest: '+path)
        require(graph[key].get('phase')=='boot','Bootstrap inventory cannot bundle a non-startup root asset: '+path)
        require(all(row[field]==graph[key][field] for field in ('namespace','path','bytes','sha256')),'Bootstrap inventory differs from signed per-file manifest: '+path)
        selected[member]=row;identities.add(key)
    require(identities=={key for key,e in graph.items() if key[0]=='root' and e.get('phase')=='boot'},'Bootstrap inventory is missing a required startup manifest asset')
    require(len(identities)<len(graph),'Bootstrap inventory cannot replace all external file delivery')
    # A shared root/content file is physically bundled once but represents both
    # identical manifest identities; report the remaining external-only rows.
    bundled_identities={key for key,e in graph.items() if key in identities or (key[0]=='content' and 'assets/'+key[1] in selected and all(e[f]==selected['assets/'+key[1]][f] for f in ('bytes','sha256')))}
    report={'bootstrap_mode':'pinned_startup_assets','bootstrap_inventory_sha256':digest(data),'bootstrap_inventory_bytes':len(data),'bundled_game_asset_count':len(selected),'bundled_game_asset_bytes':sum(e['bytes'] for e in selected.values()),'bundled_manifest_asset_rows':len(bundled_identities),'external_only_manifest_asset_rows':len(graph)-len(bundled_identities),'all_manifest_assets_retain_github_transport':True}
    return selected,report

def execute(args):
    r=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    require(r.returncode==0,'Android verification tool failed: '+Path(str(args[0])).name)
    return r.stdout+r.stderr

def uncomment_js(text):
    # Preserve quoted URL strings while removing comments; updater evidence must
    # be an executable call rather than a commented example.
    return re.sub(r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`)|//[^\n]*|/\*[\s\S]*?\*/',lambda m:m.group(1) or '',text)

def dex_public_static_check(data,descriptor):
    """Verify a real class_def and direct public static check()V method.

    Merely placing the class name in DEX string data is insufficient evidence.
    Parsing is bounded and uses native DEX ID/class-data records.
    """
    require(len(data)>=112 and data[:4]==b'dex\n' and data[7]==0,'Invalid DEX header')
    def u32(at):
        require(0<=at<=len(data)-4,'DEX record out of bounds');return struct.unpack_from('<I',data,at)[0]
    def table(header,size):
        count,at=u32(header),u32(header+4);require(count<=1000000 and 0<=at<=len(data)-count*size,'DEX table out of bounds');return count,at
    sc,so=table(56,4);tc,to=table(64,4);pc,po=table(72,12);mc,mo=table(88,8);cc,co=table(96,32)
    def leb(at):
        value=0
        for i in range(5):
            require(at<len(data),'DEX ULEB exceeds bounds');b=data[at];at+=1;value|=(b&127)<<(7*i)
            if not b&128:return value,at
        raise ValueError('DEX ULEB exceeds five bytes')
    def string(index):
        require(index<sc,'DEX string index out of bounds');at=u32(so+4*index);_,at=leb(at);end=data.find(b'\0',at)
        require(end>=at and end-at<65536,'DEX string exceeds bounds');return data[at:end].decode('utf-8',errors='replace')
    def typename(index):
        require(index<tc,'DEX type index out of bounds');return string(u32(to+4*index))
    for i in range(cc):
        at=co+32*i;classindex=u32(at)
        if typename(classindex)!=descriptor:continue
        classdata=u32(at+24);require(classdata>0,'PatchUpdater class has no executable class data')
        static,classdata=leb(classdata);instance,classdata=leb(classdata);direct,classdata=leb(classdata);virtual,classdata=leb(classdata)
        require(static+instance+direct+virtual<=1000000,'DEX class-data count exceeds bounds')
        for _ in range(static+instance):_,classdata=leb(classdata);_,classdata=leb(classdata)
        methodindex=0
        for _ in range(direct):
            diff,classdata=leb(classdata);flags,classdata=leb(classdata);code,classdata=leb(classdata);methodindex+=diff
            require(methodindex<mc,'DEX method index out of bounds');member,proto,name=struct.unpack_from('<HHI',data,mo+8*methodindex)
            require(proto<pc,'DEX proto index out of bounds');protoat=po+12*proto
            if member==classindex and string(name)=='check' and typename(u32(protoat+4))=='V' and u32(protoat+8)==0 and flags&9==9 and code>0:
                require(code<=len(data)-16 and u32(code+12)>0,'PatchUpdater check has no executable code');return True
        return False
    return False

def verify_apk(apk,catalogs,release_data,expected_version=203,aapt=None,apksigner=None,zipalign=None,java=None,runner=execute,manifest_data=None,bootstrap_inventory_data=None):
    apk=Path(apk)
    bootstrap={};bootstrap_report={'bootstrap_mode':'external_only','bundled_game_asset_count':0,'bundled_game_asset_bytes':0,'bundled_game_assets_verified':False,'bootstrap_inventory_signed':False}
    if bootstrap_inventory_data is not None:
        require(manifest_data is not None,'Bootstrap inventory requires the qualified signed per-file manifest')
        bootstrap,bootstrap_report=validate_bootstrap_inventory(bootstrap_inventory_data,manifest_data,expected_version)
    with zipfile.ZipFile(apk) as z:
        names=z.namelist();require(len(names)==len(set(names)),'APK contains duplicate ZIP members')
        actual={n for n in names if n.startswith('assets/') and not n.endswith('/')}
        expected_assets=ALLOWED_ASSETS|set(bootstrap)|({BOOTSTRAP_MEMBER} if bootstrap_inventory_data is not None else set())
        require(actual==expected_assets,'APK bundles game data or has an incomplete bootstrap allowlist: '+str(sorted(actual^expected_assets)[:12]))
        require(manifest_data is not None and z.read('assets/game_asset_manifest.json')==manifest_data,'Actual APK baseline game manifest differs from qualified per-file revisions')
        if bootstrap_inventory_data is not None:
            require(z.read(BOOTSTRAP_MEMBER)==bootstrap_inventory_data,'Signed APK bootstrap inventory differs from exact supplied allowlist')
            for member,row in bootstrap.items():
                require(z.getinfo(member).file_size==row['bytes'],'Bundled bootstrap asset size differs: '+member)
                with z.open(member) as f:actual_hash=hashlib.file_digest(f,'sha256').hexdigest()
                require(actual_hash==row['sha256'],'Bundled bootstrap asset hash differs: '+member)
            bootstrap_report.update({'bundled_game_assets_verified':True,'bootstrap_inventory_signed':True})
        for n,k in [('assets/root_delivery.tsv','root'),('assets/content_delivery.tsv','content'),('assets/base_delivery.tsv','base')]: require(z.read(n)==catalogs[k],'Actual APK native catalog differs: '+k)
        require(z.read('assets/delivery_release.tsv')==release_data,'Actual APK channel metadata differs')
        script=uncomment_js(z.read('assets/frida_script.js').decode('utf-8'))
        require('cdn.luminest.io/ffbe/movies' not in script,'Legacy Hostinger CG movie networking remains executable')
        require(not re.search(r'\bfireCurl\s*\(',script),'Legacy fireCurl CG network function or invocation remains')
        movie_request=r'jniCallStatic\w*\s*\(\s*[^,;]+,\s*[\"\']requestDownload[\"\']\s*,|\brequestDownload\s*\('
        require(not re.search(movie_request,script),'Legacy CG requestDownload invocation remains')
        for field,expected in [('MANIFEST_URL',BETA_PREFIX+'patch_version.json')]:
            match=re.search(r'const '+field+r'\s*=\s*[\"\']([^\"\']+)',script);require(match and match.group(1)==expected,'Actual beta updater follows production/latest')
        counter=re.search(r'const PATCH_VERSION\s*=\s*(\d+)\s*;',script);require(counter and int(counter.group(1))==expected_version,'Actual JS updater counter differs from APKversion')
        download=re.search(r'const DOWNLOAD_URL\s*=\s*[\"\']([^\"\']+)',script)
        destination=urlsplit(download.group(1)) if download else None
        require(destination and destination.scheme=='https' and destination.netloc=='ffbe.luminest.io' and destination.path.startswith('/downloads/beta/') and not destination.query and not destination.fragment,'Actual beta update destination is not beta')
        adapter=r'jniCallStaticVoid\s*\(\s*[\"\']O1/PatchUpdater[\"\']\s*,\s*[\"\']check[\"\']\s*,\s*[\"\']\(\)V[\"\']\s*,\s*\[\s*\]\s*\)'
        require(len(re.findall(adapter,script))==1,'Canonical native PatchUpdater.check() JNI adapter absent or duplicated')
        legacy=r'jniCallStaticVoid\s*\(\s*[^,;]+,\s*[\"\']checkForUpdate[\"\']\s*,'
        require(not re.search(legacy,script),'Legacy three-argument updater remains the canonical primary call')
        adapter_class=False
        for n in names:
            if re.fullmatch(r'classes\d*\.dex',n):
                dex=z.read(n);require(not any(c in dex for c in BAD_CLASSES),'DEX retains custom bulk ZIP bootstrap classes')
                adapter_class=dex_public_static_check(dex,'LO1/PatchUpdater;') or adapter_class
        require(adapter_class,'DEX has no actual public static PatchUpdater.check()V implementation')
        require(z.testzip() is None,'APK ZIP CRC failure')
    aapt=Path(aapt) if aapt else DEFAULT_TOOLS/'aapt2.exe'
    signer=Path(apksigner) if apksigner else DEFAULT_TOOLS/'lib/apksigner.jar'
    align=Path(zipalign) if zipalign else DEFAULT_TOOLS/'zipalign.exe'
    java=java or shutil.which('java') or 'java'
    package_output=runner([aapt,'dump','badging',apk])
    package=re.search(r"package: name='([^']+)' versionCode='(\d+)'",package_output)
    require(package and package.group(1)==PACKAGE and int(package.group(2))==expected_version,'Actual Android package/version changed')
    require('application-debuggable' not in package_output,'APK is debuggable')
    signature_output=runner([java,'-jar',signer,'verify','--verbose','--print-certs',apk])
    certs=re.findall(r'Signer #\d+ certificate SHA-256 digest:\s*([0-9a-fA-F]{64})',signature_output)
    require(len(certs)==1 and certs[0].lower()==SIGNER,'Actual signed APK certificate changed')
    require('DOES NOT VERIFY' not in signature_output,'Actual APK signature does not verify')
    runner([align,'-c','-P','16','4',apk])
    return dict(bootstrap_report,apk_bytes=apk.stat().st_size,apk_sha256=file_digest(apk),package=package.group(1),version_code=int(package.group(2)),signer_sha256=certs[0].lower(),apk_asset_entries=len(actual),native_updater_adapter_verified=True,signature_checked_by_apksigner=True,package_checked_by_aapt=True,zip_alignment_16k_verified=True,native_ELF_16k_compatibility_verified=False,runtime_verified=False)

def qualify(manifest_data,catalogs,release_data,baseline_base,apk=None,previous=None,expected_version=203,expected_asset_version=None,bootstrap_inventory_data=None,**tools):
    require(catalogs['base']==baseline_base,'Original3127 base descriptor bytes changed')
    manifest=load_json(manifest_data)
    result=validate_manifest(manifest,catalogs,previous,expected_version,expected_asset_version)
    validate_release_metadata(release_data,catalogs,expected_version,manifest['asset_version'])
    if bootstrap_inventory_data is not None:
        _,bootstrap_report=validate_bootstrap_inventory(bootstrap_inventory_data,manifest_data,expected_version)
        result.update(bootstrap_report,bundled_game_assets_verified=False,bootstrap_inventory_signed=False)
    if apk is not None: result.update(verify_apk(apk,catalogs,release_data,expected_version,manifest_data=manifest_data,bootstrap_inventory_data=bootstrap_inventory_data,**tools))
    result.update({'passed':True,'signed_apk_qualified':apk is not None,'manifest_sha256':digest(manifest_data),'manifest_bytes':len(manifest_data),'base_byte_identity_verified':True,'qualification_scope':'Catalog/package/signature/channel/static delivery policy; native/lifecycle host fixtures and runtime are separate gates','publication_performed':False})
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--root-catalog',type=Path,required=True);p.add_argument('--content-catalog',type=Path,required=True);p.add_argument('--base-catalog',type=Path,required=True);p.add_argument('--release-metadata',type=Path,required=True);p.add_argument('--baseline-base',type=Path,required=True);p.add_argument('--apk',type=Path);p.add_argument('--metadata-only',action='store_true')
    p.add_argument('--previous-manifest',type=Path);p.add_argument('--expected-apk-version',type=int,default=203);p.add_argument('--expected-asset-version',type=int,default=203)
    p.add_argument('--bootstrap-inventory',type=Path,help='Exact signed assets/bootstrap_inventory.json; omitted keeps the strict external-only policy')
    p.add_argument('--aapt',type=Path);p.add_argument('--apksigner',type=Path);p.add_argument('--zipalign',type=Path);p.add_argument('--java');p.add_argument('--output',type=Path)
    a=p.parse_args();require(a.expected_apk_version>=203,'Correction APK must exceed202')
    require((a.metadata_only and a.apk is None) or (not a.metadata_only and a.apk is not None),'Supply --apk for signed qualification, or --metadata-only explicitly')
    catalogs={n:getattr(a,n+'_catalog').read_bytes() for n in ('root','content','base')}
    previous=load_json(a.previous_manifest.read_bytes()) if a.previous_manifest else None
    result=qualify(a.manifest.read_bytes(),catalogs,a.release_metadata.read_bytes(),a.baseline_base.read_bytes(),a.apk,previous,a.expected_apk_version,a.expected_asset_version,bootstrap_inventory_data=a.bootstrap_inventory.read_bytes() if a.bootstrap_inventory else None,aapt=a.aapt,apksigner=a.apksigner,zipalign=a.zipalign,java=a.java)
    output=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(output,encoding='utf-8')
    print(output)

if __name__=='__main__':main()
