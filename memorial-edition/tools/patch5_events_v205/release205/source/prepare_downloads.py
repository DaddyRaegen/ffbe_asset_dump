"""Extend Patch 5's existing pinned download table with approved event files only."""
from pathlib import Path
import hashlib,json,zlib,zipfile
ROOT=Path(__file__).resolve().parent.parent
BASELINE=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk')
SOURCE=Path('C:/Users/Raegen/Documents/Codex/2026-10-02/task-2/integration_work/native_delivery_correction')
REPO='luminest-llc/ffbe-memorial-downloads'
def digest(data):return hashlib.sha256(data).hexdigest()
def filehash(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 plan=json.loads((ROOT/'audit/EVENT_PLAN.json').read_bytes());assets=plan['assets'];payload=ROOT/'payload';out=ROOT/'asset_publication';out.mkdir(parents=True,exist_ok=True)
 assert filehash(BASELINE)=='534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
 with zipfile.ZipFile(BASELINE) as z:original=z.read('assets/content_delivery.tsv');old_manifest=z.read('assets/side_stories/manifest.tsv');base=z.read('assets/base_delivery.tsv')
 original_lines=original.decode().splitlines();assert original_lines[0]=='ffbe-content-v1';entries={line.split('\t')[0]:line.split('\t') for line in original_lines[1:]};assert len(entries)==1411
 old=dict(entries);graph=json.loads((SOURCE/'asset_publication/manifest.json').read_bytes());remote={a['path']:a for a in graph['assets'] if a['namespace']=='root'}
 items=[];seen=set()
 for item in assets:
  path=item['path'];assert path.startswith('side_stories/') and path!='side_stories/manifest.tsv' and path not in seen;seen.add(path)
  local=Path(item.get('local_path') or payload/path);assert local.is_file()
  size=local.stat().st_size;sha=filehash(local);assert size==item['bytes'] and sha==item['sha256']
  if path in old and old[path][1]==sha:assert int(old[path][2])==size;continue
  items.append({**item,'local_path':str(local),'bytes':size,'sha256':sha})
 identity=digest(json.dumps([{'path':a['path'],'sha256':a['sha256'],'bytes':a['bytes']} for a in sorted(items,key=lambda a:a['path'])],sort_keys=True,separators=(',',':')).encode())
 tag='beta-content-v205-'+identity[:16];prefix=f'https://github.com/{REPO}/releases/download/{tag}/'
 packed=bytearray();packed_rows=[];reused=[]
 for a in sorted(items,key=lambda a:a['path']):
  existing=remote.get(a['path'])
  if existing and existing['sha256']==a['sha256'] and existing['bytes']==a['bytes']:
   t=existing['transport'];row=[a['path'],a['sha256'],str(a['bytes']),t['url'],str(t['offset']),str(t['wire_bytes']),str(t['method']),str(t['source_bytes'])]
   pack=SOURCE/'asset_publication'/t['url'].split('/')[-1];assert pack.is_file()
   with pack.open('rb') as f:f.seek(t['offset']);wire=f.read(t['wire_bytes'])
   decoded=wire if t['method']==0 else zlib.decompress(wire,-15);assert len(decoded)==a['bytes'] and digest(decoded)==a['sha256']
   reused.append({'path':a['path'],'sha256':a['sha256'],'bytes':a['bytes'],'url':t['url'],'wire_bytes':t['wire_bytes'],'local_packed_bytes_verified':True})
   entries[a['path']]=row
  else:
   blob=Path(a['local_path']).read_bytes();c=zlib.compressobj(6,zlib.DEFLATED,-15);wire=c.compress(blob)+c.flush();offset=len(packed);packed.extend(wire)
   assert zlib.decompress(wire,-15)==blob
   packed_rows.append({**a,'offset':offset,'wire_bytes':len(wire),'wire_sha256':digest(wire)})
 assert packed and len(packed)<128*1024*1024
 pack_hash=digest(packed);pack_name='patch5-events-v205-'+pack_hash[:16]+'.pack';pack_path=out/pack_name;assert not pack_path.exists();pack_path.write_bytes(packed)
 for a in packed_rows:entries[a['path']]=[a['path'],a['sha256'],str(a['bytes']),prefix+pack_name,str(a['offset']),str(a['wire_bytes']),'8',str(len(packed))]
 modified=[p for p in old if entries[p]!=old[p]];added=sorted(set(entries)-set(old));assert set(modified+added)=={a['path'] for a in items}
 for p,row in old.items():
  if p not in modified:assert entries[p]==row
 # Preserve every existing row's order and exact fields, appending new paths.
 order=list(old)+added;catalog=('ffbe-content-v1\n'+'\n'.join('\t'.join(entries[p]) for p in order)+'\n').encode();(payload/'content_delivery.tsv').write_bytes(catalog)
 side=(payload/'side_stories/manifest.tsv').read_bytes();side_rows={line.split('\t')[0]:line.split('\t') for line in side.decode().splitlines()};prior_rows={line.split('\t')[0]:line.split('\t') for line in old_manifest.decode().splitlines()}
 assert set(side_rows).issuperset(prior_rows)
 for name,row in side_rows.items():
  e=entries.get('side_stories/'+name);assert e and e[1]==row[1],name
 for p in added:assert p.startswith('side_stories/')
 catalog_name='content_delivery-'+digest(catalog)[:16]+'.tsv';(out/catalog_name).write_bytes(catalog)
 manifest={'schema':'ffbe-patch5-event-assets-v1','channel':'beta','asset_version':205,'APK_min_version':205,'package':'com.square_enix.ffbejpn','signing_certificate_sha256':'21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee','release_tag':tag,'source_patch5_sha256':filehash(BASELINE),'content_catalog':{'url':prefix+catalog_name,'bytes':len(catalog),'sha256':digest(catalog)},'base_catalog_unchanged_sha256':digest(base),'bundled_side_manifest_sha256':digest(side),'assets':[{'path':p,'version':205 if p in modified or p in added else 5,'sha256':entries[p][1],'bytes':int(entries[p][2]),'transport':{'url':entries[p][3],'offset':int(entries[p][4]),'wire_bytes':int(entries[p][5]),'method':int(entries[p][6]),'source_bytes':int(entries[p][7])}} for p in order]}
 manifest_name='event-assets-'+identity[:16]+'.json';save(out/manifest_name,manifest)
 report={'schema':'ffbe-patch5-event-download-plan-v1','passed':True,'release_tag':tag,'catalog_identity_sha256':identity,'new_pack':{'path':str(pack_path),'name':pack_name,'bytes':len(packed),'sha256':pack_hash,'url':prefix+pack_name},'new_pack_files':packed_rows,'reused_event_files':reused,'original_content_rows':1411,'final_content_rows':len(entries),'unchanged_original_rows':1411-len(modified),'modified_original_paths':modified,'new_paths':added,'every_unrelated_descriptor_unchanged':True,'all_required_side_manifest_rows_resolve':True,'event_plan_sha256':filehash(ROOT/'audit/EVENT_PLAN.json'),'content_catalog_sha256':digest(catalog),'content_catalog_bytes':len(catalog),'side_manifest_sha256':digest(side),'files':[{'name':pack_name,'local_path':str(pack_path),'bytes':len(packed),'sha256':pack_hash,'role':'pack'},{'name':catalog_name,'local_path':str(out/catalog_name),'bytes':len(catalog),'sha256':digest(catalog),'role':'catalog'},{'name':manifest_name,'local_path':str(out/manifest_name),'bytes':(out/manifest_name).stat().st_size,'sha256':filehash(out/manifest_name),'role':'manifest'}],'published':False}
 save(out/'DOWNLOAD_PLAN.json',report);print(json.dumps({k:report[k] for k in ('release_tag','original_content_rows','final_content_rows','unchanged_original_rows')}))
if __name__=='__main__':main()
