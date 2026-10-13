"""Build finite208 image/icon/order payloads from exact approved207/source bytes.

Only proposed wrong/missing covers, approved proportional geometry, and display
ordering change. Every underlying event and unlisted resource remains retained.
"""
from pathlib import Path
import collections,hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'v206-event-cleanup'
APK=ROOT.parent/'v207-download-spacing/staged_build/dist/FFBE-Memorial-EN-Download-Spacing-v207.apk'
APK_SHA='d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
PROPOSAL_SHA='0a9e374dd92c47bef4e6ad8f7b40a9bc86a9eef16f84d2f7fd24687cb90ee251'
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import rows_bytes,encode
from cpk_convert import read_cpk,repack,extend_cpk
from candidate1_archive import put
SHA=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
 b=Path(p).read_bytes();return {'local_path':str(p),'bytes':len(b),'sha256':SHA(b)}
def save(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def asset(path,p,baseline):return {'path':path,'local_path':str(p),**pin(p),'baseline':{'local_path':str(baseline),**pin(baseline)}}

def master(stem,source,changes,primary):
 blob=source.read_bytes();lines=blob.splitlines(keepends=True);rows=rows_bytes(blob,stem)
 assert len(lines)==len(rows) and all(line.strip() for line in lines)
 positions={str(r[primary]):i for i,r in enumerate(rows)};assert len(positions)==len(rows)
 updated=list(lines);ops=[]
 for rid,change in changes.items():
  index=positions[rid];before=rows[index];after=dict(before);after[change['field']]=change['value']
  assert before!=after and {k for k in before if before[k]!=after[k]}=={change['field']}
  newline=b'\r\n' if lines[index].endswith(b'\r\n') else b'\n'
  updated[index]=encode([after],stem).rstrip(b'\r\n')+newline
  ops.append({'index':index,'id':rid,'before':before,'after':after,'fields':[change['field']],'reason':change['reason'],'book_ids':change['book_ids']})
 after_blob=b''.join(updated);decoded=rows_bytes(after_blob,stem)
 assert len(decoded)==len(rows) and [str(r[primary]) for r in decoded]==[str(r[primary]) for r in rows]
 for i,(old,new) in enumerate(zip(rows,decoded)):
  rid=str(old[primary])
  if rid not in changes:assert old==new and lines[i]==updated[i]
  else:assert new==next(op['after'] for op in ops if op['id']==rid)
 target=ROOT/'payload/side_stories'/f'{stem}.dat';put(target,after_blob)
 return {**asset('side_stories/'+stem+'.dat',target,source),'stem':stem,'primary_key':primary,'operations':sorted(ops,key=lambda o:o['index']),'baseline_rows':len(rows),'candidate_rows':len(decoded),'physical_row_order_preserved':True,'all_unlisted_decoded_rows_and_raw_lines_unchanged':True}

def main():
 assert pin(APK)['sha256']==APK_SHA
 pfile=ROOT/'audit/BANNER_REPAIR_PROPOSAL.json';assert SHA(pfile.read_bytes())==PROPOSAL_SHA
 proposal=json.loads(pfile.read_bytes());assert proposal['passed'] and proposal['fallback_count']==597 and proposal['restored_neutral_member_count']==420
 geometry_file=ROOT/'audit/BANNER_GEOMETRY_PLAN.json';geometry=json.loads(geometry_file.read_bytes());assert geometry['passed'] and len(geometry['records'])==658
 wrapper_file=ROOT/'audit/NATIVE_CANVAS_WRAPPER_PLAN.json';assert SHA(wrapper_file.read_bytes())=='037f3e3e4a0786404b995e279a8c2dd8d0bea97b2f5470530e2e7782fe0a98cf'
 wrapper_plan=json.loads(wrapper_file.read_bytes());assert wrapper_plan['passed'] and wrapper_plan['member_count']==50
 wrappers={r['name']:r for r in wrapper_plan['records']};assert len(wrappers)==50
 inv=json.loads((ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json').read_bytes());books={r['book_id']:r for r in inv['books']}
 protected=json.loads((ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json').read_bytes());protected_ids=set(protected['book_ids']);assert len(protected_ids)==66
 fallback={r['book_id']:r for r in proposal['fallback_books']};new_names={r['fallback']['target_member'] for r in proposal['fallback_books'] if r.get('source_identity')}|set(wrappers)
 gen206=json.loads((BASE/'audit/BANNER_PLAN.json').read_bytes());generated_names={r['name'] for r in gen206['members'] if r['name']!='side_book_7074.png'}
 expected={r['fallback']['target_member'] for r in proposal['fallback_books']}|generated_names|set(wrappers)
 assert len(expected)==658 and {r['name'] for r in geometry['records']}==expected
 cpk_source=BASE/'payload/side_stories/spdungeon9.cpk';baseline=cpk_source.read_bytes();_,_,_,old_rows,old_members=read_cpk(baseline)
 replacement={};addition={};members=[]
 for r in geometry['records']:
  name=r['name'];candidate=r['candidate'];data=Path(candidate['local_path']).read_bytes()
  assert SHA(data)==candidate['sha256'] and len(data)==candidate['bytes'] and candidate['width']==640 and candidate['height']==240
  transform=r['transform'];assert transform['whole_canvas'] and not transform['alpha_crop']
  if name in wrappers:
   wrapper=wrappers[name];assert transform['kind']=='native_canvas_padding' and transform['source_art']==[600,120] and transform['offset']==[20,60] and transform['padding']==[20,60,20,60] and transform['preserve_source_RGBA_pixels'] and not transform['resampling'] and not transform['recolor']
   assert r['source']['sha256']==wrapper['sha256'] and r['source']['source_member']==wrapper['source_member'] and old_members[wrapper['old_member']]==Path(r['source']['local_path']).read_bytes()
  else:assert transform['resized_art']==[568,213] and transform['offset']==[36,13] and transform['kernel']=='lanczos3'
  source=r['source'];assert SHA(Path(source['local_path']).read_bytes())==source['sha256']
  if name in new_names:
   assert name not in old_members;addition[name]=data;operation='add';before=None
  else:
   assert name in old_members and SHA(old_members[name])==source['sha256'];replacement[name]=data;operation='replace';before={'bytes':len(old_members[name]),'sha256':SHA(old_members[name])}
  actual_books=r['book_ids'] if operation=='add' else sorted([b['book_id'] for b in inv['books'] if b['member']==name],key=int)
  assert actual_books and not set(actual_books)&protected_ids
  members.append({'name':name,'operation':operation,'book_ids':actual_books,'baseline':before,'candidate':candidate,'before_alpha128_bbox':r['before_alpha128_bbox'],'after_alpha128_bbox':r['after_alpha128_bbox'],'provenance':source,'transform':r['transform']})
 assert len(addition)==470 and len(replacement)==188
 interim=repack(baseline,replacement);candidate_cpk=extend_cpk(interim,addition)
 _,_,_,after_rows,after_members=read_cpk(candidate_cpk)
 assert set(after_members)==set(old_members)|set(addition) and len(after_members)==1031
 for name,data in old_members.items():assert after_members[name]==replacement.get(name,data)
 old_names=[r['FileName'] for r in old_rows];assert [r['FileName'] for r in after_rows if r['FileName'] in old_members]==old_names
 after_by_name={r['FileName']:r for r in after_rows}
 for row in old_rows:
  new=after_by_name[row['FileName']]
  for field,value in row.items():
   if field not in ('FileOffset','FileSize','ExtractSize'):assert new[field]==value
 for row in protected['books']:assert after_members[row['member']]==old_members[row['member']]
 for name in ('side_book_7032.png','side_book_7074.png','side_book_7075.png'):assert after_members[name]==old_members[name]
 cpk_target=ROOT/'payload/side_stories/spdungeon9.cpk';put(cpk_target,candidate_cpk)
 # Remap only the exact existing icon row belonging to each affected book.
 icon_source=ROOT.parent/'v205-patch5-events/payload/side_stories/LM1APs6u.dat';icon_rows=rows_bytes(icon_source.read_bytes(),'LM1APs6u');icon_lookup={str(r['0HUPxDf1']):r for r in icon_rows}
 changes={};remap_books={}
 for bid,r in fallback.items():
  if r.get('source_identity'):remap_books[bid]=(r['fallback']['target_member'],'normalize_literal_patch5_template_alias' if r.get('source_origin')=='literal_patch5_template' else 'restore_matching_neutral_title_card')
 for r in proposal['recovered_art']:
  choices=r['matching_existing_members'];assert choices
  selected=choices[0];assert selected in old_members
  expected_hash=r.get('candidate_sha256') or r['candidate']['image_sha256'];assert SHA(old_members[selected])==expected_hash
  remap_books[r['book_id']]=(selected,'recover_verified_existing_same_event_art')
 for name,r in wrappers.items():
  assert r['book_id'] not in remap_books and r['book_id'] not in fallback
  remap_books[r['book_id']]=(name,'center_genuine_600x120_pixels_on_native640x240_canvas')
 for bid,(filename,reason) in remap_books.items():
  book=books[bid];rid=book['icon_id'];assert bid not in protected_ids
  consumers={r['book_id'] for r in inv['books'] if r['icon_id']==rid};assert consumers=={bid},'Shared icon requires explicit alias: '+rid
  before=icon_lookup[rid];assert before['qtkvrS60']==book['member'] and before['qtkvrS60']!=filename
  assert rid not in changes;changes[rid]={'field':'qtkvrS60','value':filename,'reason':reason,'book_ids':[bid]}
 assert len(changes)==477
 icon_table=master('LM1APs6u',icon_source,changes,'0HUPxDf1')
 # Missing-art cards retain their previous relative order, then the two Revivals remain final.
 book_source=BASE/'payload/side_stories/Nm36woZx.dat';book_rows=rows_bytes(book_source.read_bytes(),'Nm36woZx');positions={str(r['M9mwe2cu']):i for i,r in enumerate(book_rows)}
 order_changes={};order_sections=[]
 for season in ('70','71','92'):
  section=[r for r in book_rows if str(r['2ShgIRU8'])==season];start=max(int(r['Z0EN6jSh']) for r in section)+1
  ids=sorted([bid for bid in fallback if books[bid]['season_id']==season],key=lambda bid:(books[bid]['order'],positions[bid]))
  for offset,bid in enumerate(ids):order_changes[bid]={'field':'Z0EN6jSh','value':str(start+offset),'reason':'unresolved_art_bottom_of_existing_section','book_ids':[bid]}
  if season=='70':
   for offset,bid in enumerate(('7074','7075')):order_changes[bid]={'field':'Z0EN6jSh','value':str(start+len(ids)+offset),'reason':'keep_revival_parts_final_after_unresolved_art','book_ids':[bid]}
  order_sections.append({'season_id':season,'baseline_max_order':start-1,'fallback_book_ids_in_display_order':ids,'fallback_count':len(ids),'first_fallback_order':start,'last_fallback_order':start+len(ids)-1})
 assert len(order_changes)==599 and not set(order_changes)&protected_ids
 order_table=master('Nm36woZx',book_source,order_changes,'M9mwe2cu')
 new_book_rows=rows_bytes(Path(order_table['local_path']).read_bytes(),'Nm36woZx')
 story=sorted([r for r in new_book_rows if r['2ShgIRU8']=='70'],key=lambda r:int(r['Z0EN6jSh']))
 assert [str(r['M9mwe2cu']) for r in story[-2:]]==['7074','7075']
 with zipfile.ZipFile(APK) as z:catalog=z.read('assets/content_delivery.tsv')
 descriptors={r[0]:r for r in (l.split('\t') for l in catalog.decode().splitlines()[1:])}
 for a in (asset('side_stories/spdungeon9.cpk',cpk_target,cpk_source),icon_table,order_table):assert descriptors[a['path']][1]==a['baseline']['sha256'] and int(descriptors[a['path']][2])==a['baseline']['bytes']
 ordering={'schema':'ffbe208-neutral-art-ordering-plan-v1','passed':True,'ready_for_catalog':True,'baseline_versionCode':207,'baseline_apk_sha256':APK_SHA,'proposal_sha256':PROPOSAL_SHA,'fallback_book_ids':sorted(fallback,key=int),'fallback_count':597,'sections':order_sections,'revival_final_book_ids':['7074','7075'],'table_changes':[order_table],'only_numeric_display_order_fields_changed':True,'native_signed_ascending_order_proof_sha256':SHA((BASE/'audit/NATIVE_EVENT_MENU_ORDER.json').read_bytes()),'all_underlying_events_preserved':True,'all_Dark_Visions_order_fields_unchanged':True}
 save(ROOT/'audit/ORDER_PLAN.json',ordering)
 report={'schema':'ffbe208-banner-and-icon-plan-v1','passed':True,'ready_for_catalog':True,'baseline_versionCode':207,'baseline_apk_sha256':APK_SHA,'proposal_sha256':PROPOSAL_SHA,'geometry_plan_sha256':SHA(geometry_file.read_bytes()),'geometry_inputs_sha256':SHA((ROOT/'audit/BANNER_GEOMETRY_INPUTS.json').read_bytes()),'native_canvas_wrapper_plan_sha256':SHA(wrapper_file.read_bytes()),'native_canvas_wrapper_member_count':50,'proportional_fit_member_count':608,'rendered207_review_sha256':SHA((ROOT/'audit/RENDERED_207_BANNER_REVIEW.json').read_bytes()),'asset':asset('side_stories/spdungeon9.cpk',cpk_target,cpk_source),'members':members,'icon_table':icon_table,'icon_rows':icon_table['operations'],'original_member_count':561,'final_member_count':1031,'added_member_count':470,'replaced_member_count':188,'unchanged_original_member_count':373,'original_members_order_is_identical_subsequence':True,'original_member_IDs_preserved':True,'all_unlisted_raw_members_unchanged':True,'neutral_source_counts':{'retained201':417,'current207':177,'literal_patch5_template':3},'unresolved_art_book_count':597,'recovered_art':proposal['recovered_art'],'protected_Dark_Visions_book_ids':sorted(protected_ids,key=int),'protected_Dark_Visions_scope_sha256':SHA((ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json').read_bytes()),'preserved_original_inset_members':[{'name':n,'bytes':len(old_members[n]),'sha256':SHA(old_members[n])} for n in ('side_book_7032.png','side_book_7074.png','side_book_7075.png')],'all_old_wrong_art_members_retained_for_rollback':True,'creative_image_generation':False,'network_requests':0,'device_actions':0,'runtime_tested':False}
 save(ROOT/'audit/BANNER_PLAN.json',report)
 print(json.dumps({'passed':True,'CPK_members':1031,'added':470,'replaced':188,'unchanged_old':373,'icon_rows_changed':477,'book_order_rows_changed':599,'payload_paths':['side_stories/spdungeon9.cpk','side_stories/LM1APs6u.dat','side_stories/Nm36woZx.dat']}))
if __name__=='__main__':main()
