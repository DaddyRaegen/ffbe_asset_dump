"""Replace five reviewed event assets in the exact build205 pinned catalog.

No additions, runtime edits, base catalog changes or remote writes.
"""
from pathlib import Path
import hashlib,json,zlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'v205-patch5-events'
APK=BASE/'staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk'
APK_SHA='e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'
CAT_SHA='5c9947b79a60f8a07914ab70d75080939034993fda3891626b0b762438037415'
SIDE_SHA='f4c3f34d5fa1cb8ef85bac51e8cfa55267bfe8266fe45f2295e3d495367e0230'
PATHS={'side_stories/'+x for x in ('D2zaT7Ru.dat','Nm36woZx.dat','9Zdr5ap0.dat','IL78hX09.dat','spdungeon9.cpk')}
REPO='luminest-llc/ffbe-memorial-downloads'
def sha(b):return hashlib.sha256(b).hexdigest()
def hashfile(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,'Refuse to overwrite different prepared bytes: '+str(p)
 else:p.write_bytes(b)
def main():
 assert hashfile(APK)==APK_SHA
 cleanup=json.loads((ROOT/'audit/CLEANUP_PLAN.json').read_bytes());banners=json.loads((ROOT/'audit/BANNER_PLAN.json').read_bytes())
 assert cleanup['ready_for_catalog'] and banners['passed']
 changes=cleanup['table_changes']+[banners['asset']]
 assert {a['path'] for a in changes}==PATHS and len(changes)==5
 with zipfile.ZipFile(APK) as z:catalog=z.read('assets/content_delivery.tsv');side=z.read('assets/side_stories/manifest.tsv');base=z.read('assets/base_delivery.tsv')
 assert sha(catalog)==CAT_SHA and sha(side)==SIDE_SHA
 lines=catalog.decode().splitlines();assert lines[0]=='ffbe-content-v1'
 old={r[0]:r for r in (line.split('\t') for line in lines[1:])};assert len(old)==1898 and all(len(r)==8 for r in old.values())
 entries={p:list(r) for p,r in old.items()}
 side_order=[line.split('\t') for line in side.decode().splitlines()];side_rows={r[0]:r for r in side_order};assert len(side_rows)==1857
 items=[]
 for a in sorted(changes,key=lambda a:a['path']):
  path=a['path'];p=Path(a['local_path']);blob=p.read_bytes();size=len(blob);h=sha(blob)
  assert size==a['bytes'] and h==a['sha256'] and old[path][1]!=h
  assert old[path][1]==a['baseline']['sha256'] and int(old[path][2])==a['baseline']['bytes']
  items.append({'path':path,'local_path':str(p),'bytes':size,'sha256':h})
 identity=sha(json.dumps([{'path':a['path'],'sha256':a['sha256'],'bytes':a['bytes']} for a in items],sort_keys=True,separators=(',',':')).encode())
 tag='beta-content-v206-'+identity[:16];prefix=f'https://github.com/{REPO}/releases/download/{tag}/'
 packed=bytearray();packed_rows=[]
 for a in items:
  blob=Path(a['local_path']).read_bytes();compress=zlib.compressobj(6,zlib.DEFLATED,-15);wire=compress.compress(blob)+compress.flush()
  assert zlib.decompress(wire,-15)==blob
  packed_rows.append({**a,'offset':len(packed),'wire_bytes':len(wire),'wire_sha256':sha(wire)});packed.extend(wire)
 assert 0<len(packed)<128*1024*1024
 out=ROOT/'asset_publication';pack_hash=sha(packed);pack_name='event-cleanup-v206-'+pack_hash[:16]+'.pack';pack_path=out/pack_name;put(pack_path,packed)
 for a in packed_rows:
  entries[a['path']]=[a['path'],a['sha256'],str(a['bytes']),prefix+pack_name,str(a['offset']),str(a['wire_bytes']),'8',str(len(packed))]
  name=a['path'].removeprefix('side_stories/');prior=side_rows[name];assert len(prior) in (3,4) and prior[1]==old[a['path']][1]
  updated=list(prior);updated[1]=a['sha256'];accepted=prior[2].split(',') if prior[2] else [];updated[2]=','.join(sorted(set(accepted+[prior[1]])));side_rows[name]=updated
 for path in old:
  if path not in PATHS:assert entries[path]==old[path]
 modified=[p for p in old if entries[p]!=old[p]];assert set(modified)==PATHS
 prepared=('ffbe-content-v1\n'+'\n'.join('\t'.join(entries[p]) for p in old)+'\n').encode()
 new_side=('\n'.join('\t'.join(side_rows[r[0]]) for r in side_order)+'\n').encode()
 for r in side_order:
  new=side_rows[r[0]];assert entries['side_stories/'+new[0]][1]==new[1]
  if 'side_stories/'+r[0] not in PATHS:assert new==r
 put(ROOT/'payload/content_delivery.tsv',prepared);put(ROOT/'payload/side_stories/manifest.tsv',new_side)
 catalog_name='content_delivery-'+sha(prepared)[:16]+'.tsv';put(out/catalog_name,prepared)
 manifest={'schema':'ffbe-event-cleanup-assets-v1','channel':'beta','asset_version':206,'APK_min_version':206,'package':'com.square_enix.ffbejpn','signing_certificate_sha256':'21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee','release_tag':tag,'source_patch5_sha256':'534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208','source_build205_sha256':APK_SHA,'content_catalog':{'url':prefix+catalog_name,'bytes':len(prepared),'sha256':sha(prepared)},'base_catalog_unchanged_sha256':sha(base),'bundled_side_manifest_sha256':sha(new_side),'assets':[{'path':p,'version':206 if p in PATHS else 205,'sha256':entries[p][1],'bytes':int(entries[p][2]),'transport':{'url':entries[p][3],'offset':int(entries[p][4]),'wire_bytes':int(entries[p][5]),'method':int(entries[p][6]),'source_bytes':int(entries[p][7])}} for p in old]}
 manifest_name='event-assets-'+identity[:16]+'.json';manifest_path=out/manifest_name;save(manifest_path,manifest)
 report={'schema':'ffbe-event-cleanup-download-plan-v1','passed':True,'release_tag':tag,'catalog_identity_sha256':identity,'new_pack':{'path':str(pack_path),'name':pack_name,'bytes':len(packed),'sha256':pack_hash,'url':prefix+pack_name},'new_pack_files':packed_rows,'reused_event_files':[],'original_content_rows':1898,'final_content_rows':1898,'unchanged_original_rows':1893,'modified_original_paths':modified,'new_paths':[],'every_unrelated_descriptor_unchanged':True,'all_required_side_manifest_rows_resolve':True,'cleanup_plan_sha256':hashfile(ROOT/'audit/CLEANUP_PLAN.json'),'banner_plan_sha256':hashfile(ROOT/'audit/BANNER_PLAN.json'),'content_catalog_sha256':sha(prepared),'content_catalog_bytes':len(prepared),'side_manifest_sha256':sha(new_side),'unchanged_base_catalog_sha256':sha(base),'files':[{'name':pack_name,'local_path':str(pack_path),'bytes':len(packed),'sha256':pack_hash,'role':'pack'},{'name':catalog_name,'local_path':str(out/catalog_name),'bytes':len(prepared),'sha256':sha(prepared),'role':'catalog'},{'name':manifest_name,'local_path':str(manifest_path),'bytes':manifest_path.stat().st_size,'sha256':hashfile(manifest_path),'role':'manifest'}],'published':False}
 save(out/'DOWNLOAD_PLAN.json',report)
 print(json.dumps({k:report[k] for k in ('release_tag','original_content_rows','final_content_rows','unchanged_original_rows','modified_original_paths')}))
if __name__=='__main__':main()
