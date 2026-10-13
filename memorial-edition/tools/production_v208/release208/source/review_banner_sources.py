"""Bounded read-only join of signed207 banner inventory and retained source ledger.

This stage classifies evidence and copies selected existing PNG bytes for inspection.
It does not edit any image, master, catalog or release file.
"""
from pathlib import Path
import collections,hashlib,json,re,sys

ROOT=Path(__file__).resolve().parents[1]
FROZEN=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction\banner_audit')
CATALOG=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\catalog_output\event_catalog.json')
INVENTORY=ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json'
CPK=ROOT.parent/'v206-event-cleanup/payload/side_stories/spdungeon9.cpk'
EXPECTED_INVENTORY='1fcab68f8df8cbdd6d6784a51cf3d1aa306f4cfb4e3cc5a7e0e301d870d8ab3e'
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import cpk_read

def sha(b):return hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'file':str(p),'bytes':len(b),'sha256':sha(b)}
def normalize(s):return re.sub(r'[\W_]+','',(s or '').casefold())

def main():
 assert sha(INVENTORY.read_bytes())==EXPECTED_INVENTORY
 inv=json.loads(INVENTORY.read_bytes());source=json.loads((FROZEN/'book_banner_mapping.json').read_bytes())
 catalog=json.loads(CATALOG.read_bytes());events={e['catalog_id']:e for e in catalog['events']}
 books={b['book_id']:b for b in inv['books']};mapping={b['book_id']:b for b in source['books']}
 image_by_exact_native_name=collections.defaultdict(list)
 for b in source['books']:
  for e in b.get('primary_source_event_candidates',[]):
   icon=(e.get('source_icon') or {}).get('record',{});key=normalize(icon.get('name',''))
   if not key:continue
   for image in [e.get('original_primary_regional_banner_image'),e.get('selected_source_image')]:
    if image and image.get('staged_path'):
     item={'native_icon_name':icon['name'],'catalog_id':e['catalog_id'],'event_name':e.get('event_name'),'image':image}
     if not any(x['image']['image_sha256']==image['image_sha256'] for x in image_by_exact_native_name[key]):image_by_exact_native_name[key].append(item)
 cross=[g for g in inv['duplicate_RGBA_pixels'] if g['relation']=='cross_event_title_duplicate_candidate']
 affected=set(x for g in cross for x in g['book_ids'])
 affected|={b['book_id'] for b in inv['books'] if b['generic_original_banner_filename']}
 affected|={b['book_id'] for b in inv['books'] if mapping.get(b['book_id'],{}).get('status') in ('source_icon_record_missing_or_zero','named_original_banner_not_found_in_region_dump_packs')}
 selected={books[x]['member'] for x in affected if books[x]['member'] and (any(x in g['book_ids'] for g in cross) or books[x]['member'].startswith('event_archive_'))}
 # One selected byte-identical representative per cross-group plus two placeholder examples.
 selected={books[g['book_ids'][0]]['member'] for g in cross}|{'event_archive_book_1000249.png','event_archive_book_1000652.png'}
 decoded=cpk_read(CPK,lambda n:n.split('/')[-1] in selected)
 outdir=ROOT/'audit/selected_banners';outdir.mkdir(parents=True,exist_ok=True)
 specimens=[]
 for n,blob in decoded.items():
  p=outdir/Path(n).name
  if p.exists():assert p.read_bytes()==blob
  else:p.write_bytes(blob)
  specimens.append({'member':n,'inspection_file':str(p),'bytes':len(blob),'sha256':sha(blob)})
 review=[]
 for bid in sorted(affected,key=int):
  b=books[bid];m=mapping.get(bid,{})
  names={normalize(b['title'])}
  for eid in b['primary_source_catalog_ids']:
   e=events.get(eid,{})
   names|={normalize(e.get(k,'')) for k in ['name_original','name_localized','display_name']}
  names.discard('')
  alternatives=[]
  for name in names:
   for candidate in image_by_exact_native_name.get(name,[]):
    im=candidate['image'];p=Path(im['staged_path'])
    if not p.is_file():continue
    raw=p.read_bytes()
    assert sha(raw)==im['image_sha256'] and len(raw)==im['image_bytes']
    if not any(x['image']['image_sha256']==im['image_sha256'] for x in alternatives):alternatives.append(candidate)
  originals=[]
  for e in m.get('primary_source_event_candidates',[]):
   ic=(e.get('source_icon') or {}).get('record',{})
   originals.append({'catalog_id':e['catalog_id'],'event_name':e.get('event_name'),'native_icon_name':ic.get('name'),'native_icon_filename':ic.get('file_name'),'original_primary_status':e.get('original_primary_regional_banner_status'),'original_primary_image':e.get('original_primary_regional_banner_image')})
  review.append({'book_id':bid,'season_id':b['season_id'],'title':b['title'],'order':b['order'],'icon_id':b['icon_id'],'current_member':b['member'],'current_decoded_sha256':b.get('decoded_sha256'),'routine_Dark_Visions':b['actual_Dark_Visions_series_candidate'],'Harbinger_preserve_proposed':bid=='1000419','source_status':m.get('status'),'generic_source':b['generic_original_banner_filename'],'original_icon_evidence':originals,'exact_native_title_image_candidates':alternatives,'candidate_found':bool(alternatives),'decision':'review_required'})
 report={'schema':'ffbe208-bounded-banner-source-review-v1','passed':True,'source_pins':[pin(INVENTORY),pin(FROZEN/'book_banner_mapping.json'),pin(FROZEN/'banner_cpk_member_index.json'),pin(CATALOG)],'cross_event_group_count':len(cross),'review_book_count':len(review),'exact_title_candidate_book_count':sum(r['candidate_found'] for r in review),'specimens':specimens,'books':review,'scope':'Source review only; exact-name candidates still need event/variant and visual matching before admission. No image modifications or payload writes.','network_requests':0,'device_actions':0,'payloads_modified':False}
 (ROOT/'audit/BOUNDED_BANNER_SOURCE_REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:report[k] for k in ['passed','cross_event_group_count','review_book_count','exact_title_candidate_book_count']}))

if __name__=='__main__':main()
