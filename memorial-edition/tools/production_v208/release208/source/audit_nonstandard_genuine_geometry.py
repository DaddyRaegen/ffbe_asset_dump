"""Read-only join of sealed inventory to active icon remaps; no image/payload edits."""
from pathlib import Path
import collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import rows_bytes,cpk_read
SHA=lambda b:hashlib.sha256(b).hexdigest()
def pin(p):
    b=Path(p).read_bytes();return {'file':str(p),'bytes':len(b),'sha256':SHA(b)}
def main():
    inventory_file=ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json'
    assert pin(inventory_file)['sha256']=='1fcab68f8df8cbdd6d6784a51cf3d1aa306f4cfb4e3cc5a7e0e301d870d8ab3e'
    inv=json.loads(inventory_file.read_bytes())
    banner_file=ROOT/'audit/BANNER_PLAN.json';plan=json.loads(banner_file.read_bytes());assert plan['passed']
    dv_file=ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json';dv=json.loads(dv_file.read_bytes());protected=set(dv['book_ids']);assert len(protected)==66
    protected_members={b['member'] for b in dv['books']}
    icon_file=ROOT/'payload/side_stories/LM1APs6u.dat'
    icons={str(r['0HUPxDf1']):r for r in rows_bytes(icon_file.read_bytes(),'LM1APs6u')}
    assert pin(icon_file)['sha256']==plan['icon_table']['sha256']
    members={r['member']:r for r in inv['archive_members']}
    for r in plan['members']:members[r['name']]={**r['candidate'],'member':r['name'],'from_active_plan':True}
    records=[]
    for b in inv['books']:
        if b['season_id'] not in ('70','71','92') or b['book_id'] in protected:continue
        name=icons[b['icon_id']]['qtkvrS60'];m=members[name]
        assert m.get('width') and m.get('height'),'Every event image has sealed dimensions'
        if (m['width'],m['height'])==(640,240):continue
        assert name==b['member'] and name not in protected_members
        assert b['selected_original_source_image_matches_current'] and not b['generic_original_banner_filename']
        assert [m['width'],m['height']]==[600,120] and b['alpha_extrema']==[255,255]
        records.append({'book_id':b['book_id'],'season_id':b['season_id'],'section':b['season_name'],'title':b['title'],'icon_id':b['icon_id'],'current_member':name,'bytes':m['stored_bytes'],'sha256':m['stored_sha256'],'canvas':[600,120],'alpha_bbox':b['alpha_bbox'],'alpha_extrema':b['alpha_extrema'],'selected_original_source_member':b['selected_original_source_member'],'selected_original_source_image_sha256':b['selected_original_source_image_sha256'],'source_image_matches_current':True,'primary_source_catalog_ids':b['primary_source_catalog_ids'],'source_event_families':b['source_event_families'],'classification':'Genuine JP rotation banner reused at native600x120 dimensions, without chapter640x240 canvas','protected_Dark_Visions_member':False,'unapproved_transforms':0})
    assert len(records)==50 and len({r['current_member'] for r in records})==50
    assert collections.Counter(r['season_id'] for r in records)=={'71':3,'92':47}
    cpk=Path(plan['asset']['local_path']);assert pin(cpk)['sha256']==plan['asset']['sha256']
    selected={r['current_member'] for r in records};raw=cpk_read(cpk,lambda n:n in selected);assert set(raw)==selected
    for r in records:assert len(raw[r['current_member']])==r['bytes'] and SHA(raw[r['current_member']])==r['sha256']==r['selected_original_source_image_sha256']
    evidence=ROOT/'device/final208-baseline-placeholders.png'
    geometry=ROOT/'audit/NATIVE_BANNER_GEOMETRY.json';native=json.loads(geometry.read_bytes());assert native['book_image_path']['texture_size_rect_used'] and native['existing_standard_book_slot_canvas']==[640,240]
    result={'schema':'ffbe208-genuine-nonstandard-banner-readonly-audit-v1','passed':True,'baseline_inventory_versionCode':207,'active_candidate_versionCode':208,'book_count':50,'member_count':50,'section_counts':dict(collections.Counter(r['section'] for r in records)),'size_counts':{'600x120':50},'records':records,'screenshot_identified_books':[{'book_id':'1000820','master_title':"A Summoner's Path",'screenshot_title':'Summoner’s Path','member':'event_original_jp_724f2b1ad1e136da.png'},{'book_id':'1000846','master_title':'Path of Vengeance','screenshot_title':'Journey of Revenge','member':'event_original_jp_6d27cb1145847e15.png'}],'all_current_bytes_equal_sealed_qualified_original_source':True,'native_640x240_slot_and_press_frame':True,'native_title_sprite_uses_natural_texture_rect':True,'recommended_minimal_transform_for_review':{'canvas':[640,240],'source_art_preserved_at':[600,120],'offset':[20,60],'background':'transparent RGBA0','resample':False,'crop':False,'recolor':False,'purpose':'Correct nativecanvas alignment while preserving authentic wide-banner aspect and pixel dimensions; thinner official art remains thinner.'},'no_height_fill_transform_without_distortion_or_cropping':True,'native_position_after_padding_requires_rendered_confirmation':True,'source_pins':[pin(inventory_file),pin(banner_file),pin(icon_file),pin(cpk),pin(dv_file),pin(geometry),pin(evidence)],'no_source_search':True,'no_network_requests':True,'no_device_actions':True,'payloads_modified':False}
    output=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8');target=ROOT/'audit/NONSTANDARD_GENUINE_BANNER_GEOMETRY.json';assert not target.exists() or target.read_bytes()==output
    target.write_bytes(output)
    print(json.dumps({'passed':True,'books':50,'members':50,'section_counts':result['section_counts'],'report':str(target),'sha256':SHA(output),'payloads_modified':False},ensure_ascii=True))
if __name__=='__main__':main()
