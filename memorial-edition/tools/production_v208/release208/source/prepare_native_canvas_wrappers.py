"""Seal only the50 approved genuine600x120 native-canvas wrappers; no art changes."""
from pathlib import Path
import hashlib,json,sys
from candidate1_archive import ROOT,put
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import cpk_read
SHA=lambda b:hashlib.sha256(b).hexdigest()
AUDIT_SHA='b983ada38a857bdc43a05a5b7c70e1ea558dd7ad62b0300d95625017324c64fd'
def main():
    source=ROOT/'audit/NONSTANDARD_GENUINE_BANNER_GEOMETRY.json';blob=source.read_bytes();assert SHA(blob)==AUDIT_SHA
    audit=json.loads(blob);assert audit['passed'] and audit['book_count']==audit['member_count']==50
    archive=ROOT.parent/'v206-event-cleanup/payload/side_stories/spdungeon9.cpk';archive_blob=archive.read_bytes()
    assert SHA(archive_blob)=='f54af511c7eaf2a3b75d00a631d8e3182df4d53c35ba2bdbda5eec0dfe5e9059'
    names={r['current_member'] for r in audit['records']};raw=cpk_read(archive,lambda n:n in names);assert set(raw)==names
    records=[]
    for r in audit['records']:
        data=raw[r['current_member']];assert len(data)==r['bytes'] and SHA(data)==r['sha256'] and r['canvas']==[600,120]
        assert r['source_image_matches_current'] and not r['protected_Dark_Visions_member']
        records.append({'book_id':r['book_id'],'book_ids':[r['book_id']],'icon_id':r['icon_id'],'title':r['title'],'season_id':r['season_id'],'name':'event_native_canvas_book_'+r['book_id']+'.png','old_member':r['current_member'],'source_archive':str(archive),'source_archive_sha256':SHA(archive_blob),'source_member':r['current_member'],'bytes':r['bytes'],'sha256':r['sha256'],'original_source_member':r['selected_original_source_member'],'original_source_sha256':r['selected_original_source_image_sha256'],'source_geometry':[600,120],'target_canvas':[640,240],'offset':[20,60],'padding':[20,60,20,60],'transform_kind':'native_canvas_padding','resampling':False,'crop':False,'recolor':False,'alpha_compositing':False,'preserve_source_RGBA_pixels':True,'change_order':False})
    assert len(records)==len({r['name'] for r in records})==50
    result={'schema':'ffbe208-genuine-native-canvas-wrapper-plan-v1','passed':True,'source_audit_sha256':AUDIT_SHA,'source_audit_file':str(source),'source_archive':str(archive),'source_archive_sha256':SHA(archive_blob),'member_count':50,'records':records,'all_old_source_raw_members_retained':True,'protected_Dark_Visions_unchanged':True,'no_order_changes':True,'no_resampling':True,'no_creative_image_generation':True,'no_network_requests':True,'no_device_actions':True}
    data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8');put(ROOT/'audit/NATIVE_CANVAS_WRAPPER_PLAN.json',data)
    print(json.dumps({'passed':True,'members':50,'sha256':SHA(data),'source_audit_sha256':AUDIT_SHA}))
if __name__=='__main__':main()
