"""Seal a finite event-banner repair proposal; never modifies game payloads."""
from pathlib import Path
import collections,hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import cpk_read,rows_bytes

FROZEN=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\full_inventory\recovery_round2\assembled_release\payload')
INVENTORY=ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json'
REVIEW=ROOT/'audit/BOUNDED_BANNER_SOURCE_REVIEW.json'
CURRENT_CPK=ROOT.parent/'v206-event-cleanup/payload/side_stories/spdungeon9.cpk'
CURRENT_BOOKS=ROOT.parent/'v206-event-cleanup/payload/side_stories/Nm36woZx.dat'
EXPECTED_INVENTORY='1fcab68f8df8cbdd6d6784a51cf3d1aa306f4cfb4e3cc5a7e0e301d870d8ab3e'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
 b=p.read_bytes();return {'file':str(p),'bytes':len(b),'sha256':SHA(b)}

# Inspected header identities plus explicit same-event seasonal/reprint variants.
# Shared files are never replaced: all affected users receive finite icon remaps.
GENUINE_GROUP_OWNERS={
 'event_original_gl_886e2de7d9f00076.png':{'1000400','1400400'}, # Zanarkand Dome JP/GL
 'event_original_jp_4999a4c76db16c16.png':{'1400018','1000028'}, # Vault + New Year Vault
 'event_original_gl_e264356b1c37ab59.png':{'1000121'}, # Nibelheim
 'event_original_gl_b2e808d027ae613b.png':{'1000018'}, # GL Vault
 'event_original_jp_81cbbce9c4ce04ee.png':{'1000273'}, # Score Attack seasonal challenge
 'event_original_jp_26ab67c2ef6b1a11.png':{'1000247'}, # ElTira
 'event_original_gl_14420842ee9286dc.png':{'1000389'}, # Iifa
 'event_original_gl_c1a7a9b8c7e0e342.png':{'1000413'}, # Lilith
}
GENUINE_GENERIC_IDS={'1000263','1000264','1000265','1000266','1400242'} # Challenge Chambers
RECOVERED_IMAGES={'1000023':'JP','1000108':'GL','1000880':'GL','1000885':'GL','1401011':'GL','1500018':'GL'}
DIRECT_REUSE={'1500015':'6901'} # Same-named Fundamental Forces regional story route.
NAME_KEY='G4L0YIB2';BOOK_KEY='M9mwe2cu';ORDER_KEY='Z0EN6jSh'

def main():
 assert SHA(INVENTORY.read_bytes())==EXPECTED_INVENTORY
 inv=json.loads(INVENTORY.read_bytes());review=json.loads(REVIEW.read_bytes())
 dv=json.loads((ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json').read_bytes())
 # Scope field is deliberately accepted by record identity, not title substring.
 protected={str(r['book_id']) for r in inv['books'] if r['actual_Dark_Visions_series_candidate']}|{'1000419'}
 assert len(protected)==66
 bs={b['book_id']:b for b in inv['books']};reviews={b['book_id']:b for b in review['books']}
 missing={b['book_id'] for b in review['books'] if b['source_status'] in ('source_icon_record_missing_or_zero','named_original_banner_not_found_in_region_dump_packs')}
 reasons={bid:{'unavailable_original_source'} for bid in missing}
 for g in inv['duplicate_RGBA_pixels']:
  if g['relation']!='cross_event_title_duplicate_candidate':continue
  for bid in g['book_ids']:
   b=bs[bid]
   if bid not in GENUINE_GROUP_OWNERS.get(b['member'],set()):reasons.setdefault(bid,set()).add('wrong_shared_cover_or_blank_placeholder')
 for b in inv['books']:
  if b['generic_original_banner_filename'] and b['book_id'] not in GENUINE_GENERIC_IDS:
   reasons.setdefault(b['book_id'],set()).add('generic_source_cover_not_specific_to_book')
 # Three retained title placeholders have no single resolved source artwork.
 for bid in ('1700000','1000645','1000648'):reasons.setdefault(bid,set()).add('ambiguous_source_art_retained_neutral')
 for bid in protected:reasons.pop(bid,None)
 for bid in RECOVERED_IMAGES|DIRECT_REUSE:reasons.pop(bid,None)
 # Frozen203 source misses were repaired in206; admit exact qualified current art,
 # and evaluate requested geometry separately rather than reverting these to neutral.
 qualified206=json.loads((ROOT.parent/'v206-event-cleanup/audit/BANNER_PLAN.json').read_bytes())
 qualified206_ids={str(bid) for m in qualified206['members'] for bid in m['book_ids']}
 for bid in qualified206_ids:reasons.pop(bid,None)
 fallback=set(reasons)
 # Only metadata master names change in past source; retain current neutral bytes if present.
 need201={bid for bid in fallback if not bs[bid]['member'].startswith('event_archive_book_')}
 names={f'event_archive_book_{bid}.png' for bid in need201}
 cards=cpk_read(FROZEN/'spdungeon9.cpk',lambda n:n in names)
 old_rows={str(r[BOOK_KEY]):r for r in rows_bytes((FROZEN/'Nm36woZx.dat').read_bytes(),'Nm36woZx')}
 current_rows={str(r[BOOK_KEY]):r for r in rows_bytes(CURRENT_BOOKS.read_bytes(),'Nm36woZx')}
 data=[];gaps=[]
 for bid in sorted(fallback,key=int):
  b=bs[bid];rec={'book_id':bid,'season_id':b['season_id'],'title':b['title'],'icon_id':b['icon_id'],'original_order':b['order'],'old_wrong_member':b['member'],'old_wrong_member_sha256':b['stored_sha256'],'reason':sorted(reasons[bid]),'status':'unresolved_authentic_art_neutral_fallback','native_gameplay_retained':True}
  if bid in need201:
   member=f'event_archive_book_{bid}.png';blob=cards.get(member)
   old=old_rows.get(bid);now=current_rows[bid]
   identity={'same_stable_book_id':old is not None,'retained_title':old.get(NAME_KEY) if old else None,'current_title':now[NAME_KEY],'exact_title_equal':old is not None and old[NAME_KEY]==now[NAME_KEY]}
   rec['source_identity']=identity
   if not blob or not identity['exact_title_equal']:
    rec['fallback_source_gap']=('member_missing' if not blob else 'title_changed');gaps.append(rec)
   else:rec['fallback']={'archive':str(FROZEN/'spdungeon9.cpk'),'member':member,'bytes':len(blob),'sha256':SHA(blob),'target_member':member,'mechanism':'Verbatim retained201 neutral titled PNG; no image editing'}
  else:rec['fallback']={'archive':str(CURRENT_CPK),'member':b['member'],'bytes':next(x['stored_bytes'] for x in inv['archive_members'] if x['member']==b['member']),'sha256':b['stored_sha256'],'target_member':b['member'],'mechanism':'Existing207 neutral titled PNG retained byte-identically'}
  data.append(rec)
 recovered=[]
 for bid,server in RECOVERED_IMAGES.items():
  options=[c for c in reviews[bid]['exact_native_title_image_candidates'] if c['image']['server']==server];assert len(options)==1
  c=options[0];image=c['image'];matches=[a['member'] for a in inv['books'] if a.get('decoded_sha256')==image['image_sha256']]
  recovered.append({'book_id':bid,'title':bs[bid]['title'],'old_member':bs[bid]['member'],'icon_id':bs[bid]['icon_id'],'candidate':image,'native_icon_name':c['native_icon_name'],'matching_existing_members':sorted(set(matches)),'decision':'exact_original_art_matches_event_title_after_visual_review'})
 for bid,source_id in DIRECT_REUSE.items():recovered.append({'book_id':bid,'title':bs[bid]['title'],'old_member':bs[bid]['member'],'icon_id':bs[bid]['icon_id'],'matching_existing_members':[bs[source_id]['member']],'source_book_id':source_id,'candidate_sha256':bs[source_id]['decoded_sha256'],'decision':'exact_named_same_event_regional_story_banner'})
 result={'schema':'ffbe208-finite-banner-repair-proposal-v1','passed':not gaps,'baseline_versionCode':207,'inventory_sha256':EXPECTED_INVENTORY,'source_pins':[pin(INVENTORY),pin(REVIEW),pin(FROZEN/'spdungeon9.cpk'),pin(FROZEN/'Nm36woZx.dat'),pin(CURRENT_CPK),pin(CURRENT_BOOKS),pin(ROOT.parent/'v206-event-cleanup/audit/BANNER_PLAN.json')],'qualified206_cover_book_ids':sorted(qualified206_ids,key=int),'protected_Dark_Visions_book_ids':sorted(protected,key=int),'genuine_group_owners':{k:sorted(v,key=int) for k,v in GENUINE_GROUP_OWNERS.items()},'genuine_generic_ids':sorted(GENUINE_GENERIC_IDS,key=int),'recovered_art':recovered,'fallback_books':data,'fallback_count':len(data),'restored_neutral_member_count':len(need201),'already_neutral_member_count':len(fallback-need201),'fallback_season_counts':dict(collections.Counter(r['season_id'] for r in data)),'source_gaps':gaps,'unresolved_art_must_sort_bottom':True,'all_wrong_members_retained_for_rollback':True,'oversized_cover_geometry_status':'Awaiting rendered207 comparison; native slot and pressframe640x240 proven. No geometry edits in this plan.','no_payload_mutations':True}
 (ROOT/'audit/BANNER_REPAIR_PROPOSAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:result[k] for k in ['passed','fallback_count','restored_neutral_member_count','already_neutral_member_count','fallback_season_counts']}))
 print(json.dumps({'gaps':[(x['book_id'],x['fallback_source_gap']) for x in gaps],'recovered':[(r['book_id'],r['matching_existing_members']) for r in recovered]},ensure_ascii=True))

if __name__=='__main__':main()
