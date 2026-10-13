"""Pack exactly three208 banner/icon/order resources into immutable GitHub slices.

All1898 catalog and1857 side-manifest paths/order remain;1895 descriptors retain
every byte field and their inherited206 public asset metadata. No remote writes.
"""
from pathlib import Path
import hashlib,json,zlib,zipfile
from candidate1_archive import put
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'v206-event-cleanup'
APK=ROOT.parent/'v207-download-spacing/staged_build/dist/FFBE-Memorial-EN-Download-Spacing-v207.apk'
APK_SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
CAT_SHA='963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a'
SIDE_SHA='0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14'
PATHS={'side_stories/'+n for n in ('spdungeon9.cpk','LM1APs6u.dat','Nm36woZx.dat')}
REPO='luminest-llc/ffbe-memorial-downloads'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
 b=Path(p).read_bytes();return {'bytes':len(b),'sha256':SHA(b)}
def save(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))

def main():
 assert pin(APK)['sha256']==APK_SHA
 banner_path=ROOT/'audit/BANNER_PLAN.json';order_path=ROOT/'audit/ORDER_PLAN.json'
 banner=json.loads(banner_path.read_bytes());ordering=json.loads(order_path.read_bytes())
 assert banner['passed'] and banner['ready_for_catalog'] and ordering['passed'] and ordering['ready_for_catalog']
 changes=[banner['asset'],banner['icon_table']]+ordering['table_changes']
 assert len(changes)==3 and {r['path'] for r in changes}==PATHS
 with zipfile.ZipFile(APK) as z:catalog=z.read('assets/content_delivery.tsv');side=z.read('assets/side_stories/manifest.tsv');base=z.read('assets/base_delivery.tsv')
 assert SHA(catalog)==CAT_SHA and SHA(side)==SIDE_SHA
 lines=catalog.decode().splitlines();assert lines[0]=='ffbe-content-v1'
 old={r[0]:r for r in (l.split('\t') for l in lines[1:])};assert len(old)==1898 and all(len(r)==8 for r in old.values())
 entries={p:list(r) for p,r in old.items()}
 side_order=[l.split('\t') for l in side.decode().splitlines()];side_rows={r[0]:r for r in side_order};assert len(side_rows)==1857
 old_plan=json.loads((BASE/'asset_publication/DOWNLOAD_PLAN.json').read_bytes());old_manifest_file=next(f for f in old_plan['files'] if f['role']=='manifest')
 assert pin(old_manifest_file['local_path'])=={k:old_manifest_file[k] for k in ('bytes','sha256')}
 inherited=json.loads(Path(old_manifest_file['local_path']).read_bytes());inherited_assets={a['path']:a for a in inherited['assets']}
 assert inherited['asset_version']==206 and inherited['content_catalog']['sha256']==CAT_SHA and inherited['bundled_side_manifest_sha256']==SIDE_SHA and set(inherited_assets)==set(old)
 for p,row in old.items():
  a=inherited_assets[p];t=a['transport'];assert a['sha256']==row[1] and a['bytes']==int(row[2]) and [t['url'],str(t['offset']),str(t['wire_bytes']),str(t['method']),str(t['source_bytes'])]==row[3:]
 items=[]
 for a in sorted(changes,key=lambda r:r['path']):
  p=Path(a['local_path']);data=p.read_bytes();actual=pin(p);assert actual=={k:a[k] for k in ('bytes','sha256')}
  assert old[a['path']][1]==a['baseline']['sha256'] and int(old[a['path']][2])==a['baseline']['bytes'] and actual['sha256']!=old[a['path']][1]
  items.append({'path':a['path'],'local_path':str(p),**actual})
 identity=SHA(json.dumps([{k:a[k] for k in ('path','bytes','sha256')} for a in items],sort_keys=True,separators=(',',':')).encode())
 tag='content-v208-'+identity[:16];prefix=f'https://github.com/{REPO}/releases/download/{tag}/'
 pack=bytearray();packed_rows=[]
 for a in items:
  blob=Path(a['local_path']).read_bytes();compressor=zlib.compressobj(6,zlib.DEFLATED,-15);wire=compressor.compress(blob)+compressor.flush()
  assert zlib.decompress(wire,-15)==blob
  packed_rows.append({**a,'offset':len(pack),'wire_bytes':len(wire),'wire_sha256':SHA(wire)});pack.extend(wire)
 assert 0<len(pack)<128*1024*1024
 out=ROOT/'asset_publication';pack_hash=SHA(pack);pack_name='banner-fixes-v208-'+pack_hash[:16]+'.pack';pack_file=out/pack_name;put(pack_file,pack)
 public_assets={p:dict(a) for p,a in inherited_assets.items()}
 for a in packed_rows:
  row=[a['path'],a['sha256'],str(a['bytes']),prefix+pack_name,str(a['offset']),str(a['wire_bytes']),'8',str(len(pack))];entries[a['path']]=row
  name=a['path'].removeprefix('side_stories/');prior=side_rows[name];assert prior[1]==old[a['path']][1] and len(prior) in (3,4)
  new=list(prior);new[1]=a['sha256'];new[2]=','.join(sorted(set((prior[2].split(',') if prior[2] else [])+[prior[1]])));side_rows[name]=new
  public_assets[a['path']]={'path':a['path'],'version':208,'sha256':a['sha256'],'bytes':a['bytes'],'transport':{'url':row[3],'offset':a['offset'],'wire_bytes':a['wire_bytes'],'method':8,'source_bytes':len(pack)}}
 for p in old:
  if p not in PATHS:assert entries[p]==old[p] and public_assets[p]==inherited_assets[p]
 modified=[p for p in old if entries[p]!=old[p]];assert set(modified)==PATHS
 prepared=('ffbe-content-v1\n'+'\n'.join('\t'.join(entries[p]) for p in old)+'\n').encode()
 new_side=('\n'.join('\t'.join(side_rows[r[0]]) for r in side_order)+'\n').encode()
 for r in side_order:
  new=side_rows[r[0]];assert entries['side_stories/'+new[0]][1]==new[1]
  if 'side_stories/'+r[0] not in PATHS:assert new==r
 put(ROOT/'payload/content_delivery.tsv',prepared);put(ROOT/'payload/side_stories/manifest.tsv',new_side)
 catalog_name='content_delivery-'+SHA(prepared)[:16]+'.tsv';put(out/catalog_name,prepared)
 manifest={'schema':'ffbe-production208-banner-assets-v1','channel':'production','asset_version':208,'APK_min_version':208,'package':'com.square_enix.ffbejpn','signing_certificate_sha256':'21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee','release_tag':tag,'source_patch5_sha256':inherited['source_patch5_sha256'],'source_build207_sha256':APK_SHA,'parent_asset_version':206,'content_catalog':{'url':prefix+catalog_name,'bytes':len(prepared),'sha256':SHA(prepared)},'base_catalog_unchanged_sha256':SHA(base),'bundled_side_manifest_sha256':SHA(new_side),'assets':[public_assets[p] for p in old]}
 manifest_name='event-assets-'+identity[:16]+'.json';manifest_path=out/manifest_name;save(manifest_path,manifest)
 report={'schema':'ffbe-production208-banner-download-plan-v1','passed':True,'versionCode':208,'asset_version':208,'channel':'production','baseline_apk_sha256':APK_SHA,'release_tag':tag,'catalog_identity_sha256':identity,'new_pack':{'path':str(pack_file),'name':pack_name,'bytes':len(pack),'sha256':pack_hash,'url':prefix+pack_name},'new_pack_files':packed_rows,'reused_event_files':[],'original_content_rows':1898,'final_content_rows':1898,'original_side_rows':1857,'final_side_rows':1857,'unchanged_original_rows':1895,'modified_original_paths':modified,'new_paths':[],'every_unrelated_descriptor_unchanged':True,'all_required_side_manifest_rows_resolve':True,'asset_metadata_versions_unchanged_for_reused_assets':True,'banner_plan_sha256':pin(banner_path)['sha256'],'ordering_plan_sha256':pin(order_path)['sha256'],'content_catalog_sha256':SHA(prepared),'content_catalog_bytes':len(prepared),'side_manifest_sha256':SHA(new_side),'unchanged_base_catalog_sha256':SHA(base),'inherited_manifest_sha256':pin(old_manifest_file['local_path'])['sha256'],'files':[{'name':pack_name,'local_path':str(pack_file),**pin(pack_file),'role':'pack'},{'name':catalog_name,'local_path':str(out/catalog_name),**pin(out/catalog_name),'role':'catalog'},{'name':manifest_name,'local_path':str(manifest_path),**pin(manifest_path),'role':'manifest'}],'published':False}
 save(out/'DOWNLOAD_PLAN.json',report)
 print(json.dumps({k:report[k] for k in ('release_tag','unchanged_original_rows','modified_original_paths','content_catalog_sha256','side_manifest_sha256')}));print(json.dumps({'new_pack_bytes':len(pack),'files':[f['name'] for f in report['files']]}))
if __name__=='__main__':main()
