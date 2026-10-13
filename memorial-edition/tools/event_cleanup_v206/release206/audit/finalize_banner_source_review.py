"""Record source admission decisions; never modify image/game bytes."""
from pathlib import Path
import hashlib,json,csv,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
pin=lambda p:{'path':str(p),'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()}
p=ROOT/'audit/REQUESTED_BANNER_SOURCES.json';report=read(p)
web=read(ROOT/'audit/OFFICIAL_BANNER_IMAGES.json');web_by_id={r['book_id']:r for r in web['images']}
press=read(ROOT/'audit/PRESS_BANNER_IMAGES.json');press_by_id={r['book_id']:r for r in press['images']}
press_descriptions={
 '7073':('失われた鏡像','Complete 621×233 framed native story event banner: illuminated house background, original ornate frame, Elnath/Arde/Timorus pixel sprites and exact Japanese title. No image edits; native CPK byte identity is not proved by this press PNG.'),
 '7070':('人形館の謎','640×360 publisher presentation slide contains the complete framed native story event banner with mansion background, Jean Pignon and companion pixel sprites and exact title. The surrounding slide includes a header/date strip and Dengeki watermark outside the banner; not an exact standalone native CPK member.'),
}
descriptions={
 '7078':('未来へつなぐバトン','667×508 announcement artwork with date strip; Kalmia and the exact event title. Not the exact original CPK member.'),
 '7065':('せかい＝がようし','665×410 announcement includes the complete framed event banner above its date strip; Poppy and the exact event title. The standalone 640×240 CPK member remains missing.'),
 '7083':('鏡合わせのプリンセス','640×352 publisher event key art with Nerine and the two princesses; exact event title. Not the exact original CPK member.'),
 '7076':('心の中の伴奏者','640×352 publisher event key art with Cleome and the pianist; exact event title. Not the exact original CPK member.'),
 '7081':('潮騒デイドリーム','590×437 announcement artwork with Seaside Nichol, Luka and the date strip; exact event title. Not the exact original CPK member.'),
 '7082':('盾の少女と夢舞台','597×450 announcement artwork with Daisy and the theatrical setting/date strip; exact event title. Not the exact original CPK member.'),
}
original_map_path=Path(r'T:\Projects\FFBE Patch\story-ports\side-stories\artwork\original-banner-map.json')
original7032=next(r for r in read(original_map_path) if r['book_id']=='7032')
old7032=Path(original7032['path']);old7032_pin=pin(old7032)
summaries=[]
for b in report['books']:
 bid=b['book_id']
 for e in b['source_events']:
  for c in e['candidates']:
   if c['member']=='spd_20190729_bn_list_FF10.png':
    c['admitted_for_requested_event']=False
    c['visual_rejection']='Image title is FINAL FANTASY X Zanarkand Dome, not the requested story event. Multiple retained later area rows reuse this placeholder filename. An exact numeric icon join alone does not prove event artwork identity.'
 if bid in web_by_id:
  b['official_web_original']={**web_by_id[bid],'visual_admission_pending':False,'admitted_as_correct_event_artwork':True,'admitted_as_exact_native_cpk_banner':False,'original_title_confirmed_visually':descriptions[bid][0],'visual_review':descriptions[bid][1],'permitted_followup':'Root image tool may translate/reformat this genuine source artwork; preserve its characters/background. No such edit was performed in this source audit.'}
  status='correct_official_event_artwork_found_native_banner_missing'
 elif bid=='7032':
  assert old7032_pin['sha256']==b['existing_banner']['sha256']
  b['existing_original_provenance']={'map':pin(original_map_path),'map_record':original7032,'source_image':old7032_pin,'matches_actual205_bytes':True,'visual_review':'English Genesis of Chaos -DARK VISIONS- story event banner with red Its Back ribbon and the source character/monster artwork. Already complete English.'}
  status='existing_authentic_english_banner_keep_unchanged'
 elif bid in ['1500001','1500002','1000986']:
  expected='5155' if bid=='1500001' else '5160'
  exact=[i for e in b['source_events'] if e['server']=='JP' and str(e['original_id'])==expected for c in e['candidates'] if c['basis']=='Exact typed event deep link and original title' for i in c['extracted_images'] if i['status']=='full_original_image_extracted']
  assert exact
  b['admitted_originals']=exact
  b['source_identity_admission']='Exact original JP story event ID, typed banner-master deep link and title. Event variants remain separate; matching a common English title alone does not admit cross-reuse.'
  status='exact_jp_rerun_banner_found_for_translation'
 elif bid in press_by_id:
  b.pop('gap_truth',None)
  b['credited_press_mirror_original']={**press_by_id[bid],'visual_admission_pending':False,'admitted_as_correct_event_artwork':True,'admitted_as_exact_native_cpk_banner':False,'original_title_confirmed_visually':press_descriptions[bid][0],'visual_review':press_descriptions[bid][1],'permitted_followup':'Root image tool may translate/reformat this genuine source artwork while preserving original characters/background/frame. No such edit was performed in this source audit.'}
  status='correct_original_event_artwork_recovered_from_contemporary_credited_press_mirror'
 elif bid=='7074':status='new_banner_explicitly_authorized_root_image_tool_owns'
 elif bid=='7075':status='retain_existing_banner_move_book_to_bottom_root_table_agent_owns'
 elif bid=='7299':status='test_book_removed_from_menu_image_member_retained_unused'
 else:raise AssertionError(bid)
 b['source_review_status']=status
 summaries.append({'book_id':bid,'title':b['actual205_book']['name'],'icon_id':b['actual205_icon']['icon_id'],'current_member':b['existing_banner']['member'],'current_dimensions':b['existing_banner']['dimensions'],'current_sha256':b['existing_banner']['sha256'],'status':status,'source_path':b.get('official_web_original',{}).get('staged_path') or b.get('credited_press_mirror_original',{}).get('staged_path') or (b.get('admitted_originals') or [{}])[0].get('staged_path') or (str(old7032) if bid=='7032' else None)})
report['paired_image_policy']='Exact signed205 ARM64 static layout uses one title image plus shared spd_bn_press.png from the special atlas. No separate per-title selected-border PNG is required by this path. The JP _last files are explicitly named 最終日 (last day) in retained icon records, not selected borders.'
report['native_selected_frame_evidence']=pin(ROOT/'audit/NATIVE_BANNER_BUTTON_PROOF.json')
report['all_retained_region_cpks_search']=pin(ROOT/'audit/MISSING_BANNER_MEMBER_SEARCH.json')
report['official_source_artwork_receipt']=pin(ROOT/'audit/OFFICIAL_BANNER_IMAGES.json')
report['credited_press_mirror_artwork_receipt']=pin(ROOT/'audit/PRESS_BANNER_IMAGES.json')
report['source_review_summary']=summaries
report['scope']='Requested exact205 books, retained GL/JP CPK sources, publisher-owned FF Portal images and contemporary credited press mirrors explicitly authorized for original event artwork recovery. Original image bytes only. No image editing, APK/table/runtime/device/publication or remote modifications.'
report.pop('network_requests',None)
report['network_scope']='Read-only public article/image requests and search queries. Six publisher-hosted event artwork originals and two contemporary credited press mirror originals retrieved; no game asset packs downloaded. Mirror artwork primary origin is an inference documented per image; no mirror is described as publisher-hosted.'
report['release_history_warning']='Presence in retained GL data/icon tables proves retained source metadata only; it is not proof the event was activated or released on GL. No unverified claim of GL availability is made.'
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (ROOT/'audit/REQUESTED_BANNER_SOURCE_TABLE.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=['book_id','title','icon_id','current_member','current_dimensions','current_sha256','status','source_path']);w.writeheader();w.writerows(summaries)
web['visual_review_complete']=True
for r in web['images']:
 r['visual_admission_pending']=False;r['admitted_as_correct_event_artwork']=True;r['admitted_as_exact_native_cpk_banner']=False;r['visual_review']=descriptions[r['book_id']][1]
(ROOT/'audit/OFFICIAL_BANNER_IMAGES.json').write_text(json.dumps(web,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
press['visual_review_complete']=True
for r in press['images']:
 r['visual_admission_pending']=False;r['admitted_as_correct_event_artwork']=True;r['admitted_as_exact_native_cpk_banner']=False;r['visual_review']=press_descriptions[r['book_id']][1]
(ROOT/'audit/PRESS_BANNER_IMAGES.json').write_text(json.dumps(press,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Re-pin the receipt after its visual review fields are finalized.
report['official_source_artwork_receipt']=pin(ROOT/'audit/OFFICIAL_BANNER_IMAGES.json')
report['credited_press_mirror_artwork_receipt']=pin(ROOT/'audit/PRESS_BANNER_IMAGES.json')
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':pin(p),'source_table':pin(ROOT/'audit/REQUESTED_BANNER_SOURCE_TABLE.csv'),'summary':summaries},ensure_ascii=False))
