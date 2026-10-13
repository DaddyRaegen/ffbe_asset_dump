"""Extract exact retained image bytes and focused identity/provenance evidence.

No image edit, game payload edit, device action, or remote access.
"""
from pathlib import Path
import hashlib,json,sys,struct,io,re
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import rows_bytes,readable,crilayla
from cpk_convert import read_cpk
from PIL import Image
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
P205=ROOT.parent/'v205-patch5-events/payload/side_stories'
OLD=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction\banner_audit')
CAT=OLD.parents[2]/'catalog_output/event_catalog.json'
TARGETS=['7073','7081','7070','7082','7078','7065','7083','7076','7032','1500001','7074','7075','7299','1500002','1000986']
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,data):
 p=ROOT/'audit'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def put(path,blob):
 path.parent.mkdir(parents=True,exist_ok=True)
 assert path.resolve().is_relative_to(ROOT.resolve())
 if path.exists():assert path.read_bytes()==blob
 else:path.write_bytes(blob)
def image_info(blob):
 with Image.open(io.BytesIO(blob)) as im:im.verify()
 with Image.open(io.BytesIO(blob)) as im:return {'bytes':len(blob),'sha256':sha(blob),'dimensions':list(im.size),'format':im.format,'mode':im.mode}
books={r['M9mwe2cu']:readable(r) for r in rows_bytes((P205/'Nm36woZx.dat').read_bytes(),'Nm36woZx')}
icons={r['icon_id']:r for r in map(readable,rows_bytes((P205/'LM1APs6u.dat').read_bytes(),'LM1APs6u'))}
prior={r['book_id']:r for r in load(OLD/'book_banner_mapping.json')['books']}
events={e['catalog_id']:e for e in load(CAT)['events']}
sourceicons={s:{r['icon_id']:r for r in load(OLD/(s+'_icons_latest.json'))['rows']} for s in ['GL','JP']}
masters={s:load(OLD/(s+'_banner_master_latest.json')) for s in ['GL','JP']}
memberindex={(r['server'],r['filename']):r['sources'] for r in load(OLD/'banner_cpk_member_index.json')}
jpclues={r['book_id']:r for r in load(r'T:\Projects\FFBE Patch\story-ports\side-stories\reports\japanese-banner-candidates.json')}
_,_,_,toc,current=read_cpk((P205/'spdungeon9.cpk').read_bytes())
receipts={};source_hashes={}
def extract(candidate):
 key=(candidate['source_path'],candidate['source_member'],candidate['member_offset'])
 if key in receipts:return receipts[key]
 p=Path(candidate['source_path']);exists=p.exists()
 if not exists:return {**candidate,'source_exists':False,'status':'missing_retained_source_path'}
 with p.open('rb') as f:f.seek(candidate['member_offset']);packed=f.read(candidate['packed_bytes'])
 assert len(packed)==candidate['packed_bytes']
 blob=crilayla(packed) if packed.startswith(b'CRILAYLA') else packed
 assert len(blob)==candidate['extracted_bytes']
 raw_sha=sha(blob);mechanism='Exact source CPK member bytes; CRILAYLA expanded if present'
 if not blob.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8')):
  job=OLD/'private_extractor_jobs'/sha(str(p).encode())[:20]
  cached=job/'cpk'/Path(candidate['source_member']).name
  receipt=job/'extraction_complete.json'
  if not cached.exists() or not receipt.exists():return {**candidate,'source_exists':True,'status':'encrypted_source_not_yet_extracted','cached_path_checked':str(cached),'raw_source_member_sha256':raw_sha}
  evidence=load(receipt);assert evidence['source_path']==str(p) and evidence['returncode']==0
  blob=cached.read_bytes();mechanism='Read-only reuse of retained established DataExtractor output; no extractor executed'
  assert blob.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8'))
 info=image_info(blob)
 if str(p) not in source_hashes:
  with p.open('rb') as f:source_hashes[str(p)]=hashlib.file_digest(f,'sha256').hexdigest()
 dest=ROOT/'banner_sources'/'originals'/candidate['server']/(Path(candidate['source_member']).stem+'-'+info['sha256'][:16]+Path(candidate['source_member']).suffix)
 put(dest,blob)
 result={**candidate,'source_exists':True,'source_sha256':source_hashes[str(p)],'raw_source_member_sha256':raw_sha,'status':'full_original_image_extracted',**info,'staged_path':str(dest),'extraction_mechanism':mechanism,'image_edit_performed':False}
 receipts[key]=result;return result
rows=[]
for bid in TARGETS:
 book=books[bid];icon=icons[book['icon_id']];filename=icon['file_name'];assert filename in current
 oldblob=current[filename];oldblob=crilayla(oldblob) if oldblob.startswith(b'CRILAYLA') else oldblob
 oldinfo=image_info(oldblob);dest=ROOT/'banner_sources'/'current205'/filename;put(dest,oldblob)
 row={'book_id':bid,'actual205_book':book,'actual205_icon':icon,'existing_banner':{'CPK':str(P205/'spdungeon9.cpk'),'member':filename,**oldinfo,'staged_path':str(dest)},'source_events':[],'prior_mapping_status':prior[bid]['status']}
 for link in prior[bid]['sources']:
  event=events[link['catalog_id']];server=event['server'];iconid=str(event['raw_record'].get('icon_id'));sicon=sourceicons[server].get(iconid)
  erow={'catalog_id':event['catalog_id'],'server':server,'original_id':event['original_id'],'name_original':event['name_original'],'display_name':event['display_name'],'event_type':event['type'],'source_record_refs':event['source_record_refs'],'regional_relationship':event['regional_match_status'],'raw_area_icon_id':iconid,'source_icon':sicon,'candidates':[]}
  candidate_sets=[]
  if sicon:
   candidate_sets.append(('F_AREA_MST.icon_id -> exact same-region F_ICON_MST filename',sicon['file_name'],{'source_icon':sicon}))
  for banner in masters[server]['rows']:
   parts=banner.get('url','').split(',');direct=banner.get('rUP3Gix0')=='7' and parts[:3]==[event['world_id'],event['region_id'],event['original_id']]
   story=banner.get('rUP3Gix0')=='15' and event['type']=='story_event' and parts[:2]==['4',event['original_id']] and event['name_original'] and event['name_original'] in banner.get('name','')
   if direct or story:candidate_sets.append(('Exact typed event deep link and original title',banner['6Dgaqir0'],{'banner_record':banner,'banner_master_source':masters[server]['source']}))
  # Older baseline audit's named icon candidates are preserved as review-only,
  # never silently treated as an exact area join or cross-title rerun match.
  if server=='JP':
   for c in jpclues.get(bid,{}).get('candidates',[]):
    candidate_sets.append(('Prior exact Japanese title/icon clue; event variant needs review',c['file'],{'prior_title_candidate':c,'automatic_identity_admission':False}))
  seen=set()
  for basis,member,proof in candidate_sets:
   if member in seen:continue
   seen.add(member);cs=memberindex.get((server,member),[])
   candidate={'basis':basis,'member':member,'proof':proof,'retained_source_candidates':cs,'extracted_images':[]}
   if cs:
    ordered=sorted(cs,key=lambda c:(c['quality']!='hd',c['language']=='en',c['source_version'] or 0),reverse=True)
    candidate['extracted_images']=[extract(c) for c in ordered[:1]]
   else:candidate['status']='exact_named_member_absent_from_retained_region_CPK_index'
   erow['candidates'].append(candidate)
  row['source_events'].append(erow)
 rows.append(row)
selection_clues=[n for n in current if any(term in n.lower() for term in ['select','selected','border','frame'])]
report={'schema':'ffbe-v206-requested-banner-source-audit-v1','scope':'Requested exact205 books, retained GL/JP sources, original bytes only; no image editing, APK/table/runtime/device/remote modifications.','current205_spdungeon9_sha256':sha((P205/'spdungeon9.cpk').read_bytes()),'requested_primary_book_ids':TARGETS[:13],'same_title_genesis_variant_book_ids':TARGETS[13:],'books':rows,'cpk_selection_frame_member_clues':selection_clues,'paired_image_policy':'No selected-border variant inferred from _last (last-day event) suffix. Native frame/selection evidence still being examined.','source_provenance_pins':{'event_catalog':{'path':str(CAT),'sha256':sha(CAT.read_bytes())},'prior_mapping':{'path':str(OLD/'book_banner_mapping.json'),'sha256':sha((OLD/'book_banner_mapping.json').read_bytes())},'member_index':{'path':str(OLD/'banner_cpk_member_index.json'),'sha256':sha((OLD/'banner_cpk_member_index.json').read_bytes())}},'source_image_count':len(receipts),'physical_runtime_tested':False,'network_requests':0}
save('REQUESTED_BANNER_SOURCES.json',report)
print(json.dumps({'output':str(ROOT/'audit/REQUESTED_BANNER_SOURCES.json'),'books':len(rows),'original_images_extracted':len(receipts),'summary':[{'book':r['book_id'],'title':r['actual205_book']['name'],'current_size':r['existing_banner']['dimensions'],'source_events':[{'event':e['catalog_id'],'candidates':[{'member':c['member'],'status':c.get('status'),'images':[{'status':i['status'],'path':i.get('staged_path'),'size':i.get('dimensions')} for i in c['extracted_images']]} for c in e['candidates']]} for e in r['source_events']]} for r in rows]},ensure_ascii=False))
