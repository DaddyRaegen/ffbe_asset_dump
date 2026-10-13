"""Extend the frozen594 proposal by exactly three proved P5 title placeholders."""
from pathlib import Path
import collections,hashlib,json,sys,zipfile
from candidate1_archive import ROOT,ARCHIVE,put
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import rows_bytes
from cpk_convert import read_cpk
SHA=lambda b:hashlib.sha256(b).hexdigest()
ORIGINAL='da1911049240d7ffb6ae21e5ab1b3bf2a4672d33dfc4e57a0052c7c0efa281e5'
P5=Path(r'T:\Projects\FFBE Patch\localization-rounds\2026-09-29-units-cards-ios\dist\FFBE-Memorial-EN-Patch-5-Content-Source.apk')
CURRENT=ROOT.parent/'v206-event-cleanup/payload/side_stories/spdungeon9.cpk'
def pin(p):
    b=Path(p).read_bytes();return {'file':str(p),'bytes':len(b),'sha256':SHA(b)}
def main():
    old_file=ARCHIVE/'audit/BANNER_REPAIR_PROPOSAL.json';old_bytes=old_file.read_bytes();assert SHA(old_bytes)==ORIGINAL
    result=json.loads(old_bytes);assert result['passed'] and result['fallback_count']==594
    audit_file=ROOT/'audit/REMAINING_BASELINE_PLACEHOLDERS.json';audit=json.loads(audit_file.read_bytes())
    assert audit['passed'] and {r['book_id'] for r in audit['records']}=={'7051','7067','7069'}
    with zipfile.ZipFile(P5) as z:
        p5_cpk=z.read('assets/side_stories/spdungeon9.cpk');p5_book=z.read('assets/side_stories/Nm36woZx.dat')
    assert SHA(p5_cpk)=='2f2be2a15887aebf90ed82395e2fcd6d62dad4aae1f84a9d6b07324626481dd6'
    p5_rows={str(r['M9mwe2cu']):r for r in rows_bytes(p5_book,'Nm36woZx')}
    _,_,_,_,p5_members=read_cpk(p5_cpk)
    current_cpk=CURRENT.read_bytes();_,_,_,_,members=read_cpk(current_cpk)
    current_book=ROOT.parent/'v206-event-cleanup/payload/side_stories/Nm36woZx.dat'
    current_rows={str(r['M9mwe2cu']):r for r in rows_bytes(current_book.read_bytes(),'Nm36woZx')}
    old_ids={r['book_id'] for r in result['fallback_books']}
    additions=[]
    for row in audit['records']:
        bid=row['book_id'];member=row['member'];data=members[member];before=p5_rows[bid];now=current_rows[bid]
        assert bid not in old_ids and data==p5_members[member]==Path(row['existing_generated_PNG_file']).read_bytes()
        assert len(data)==row['bytes'] and SHA(data)==row['sha256']
        assert before['G4L0YIB2']==now['G4L0YIB2']==row['title'] and now['0HUPxDf1']==row['icon_id'] and now['2ShgIRU8']=='71'
        alias='event_missing_art_book_'+bid+'.png';assert alias not in members
        additions.append({'book_id':bid,'season_id':'71','title':row['title'],'icon_id':row['icon_id'],'original_order':row['current_order'],'old_wrong_member':member,'old_wrong_member_sha256':row['sha256'],'reason':['literal_patch5_generated_title_placeholder_no_qualified_original_art'],'status':'unresolved_authentic_art_neutral_fallback','native_gameplay_retained':True,'source_origin':'literal_patch5_template','source_identity':{'same_stable_book_id':True,'retained_title':before['G4L0YIB2'],'current_title':now['G4L0YIB2'],'exact_title_equal':True,'source_APK':str(P5),'source_APK_sha256':SHA(P5.read_bytes()),'source_book_table_member':'assets/side_stories/Nm36woZx.dat','source_book_table_sha256':SHA(p5_book),'source_CPK_member':'assets/side_stories/spdungeon9.cpk','source_CPK_sha256':SHA(p5_cpk)},'fallback':{'archive':str(CURRENT),'member':member,'bytes':len(data),'sha256':SHA(data),'target_member':alias,'mechanism':'Exact literal P5 generated title placeholder copied to new external alias; only approved proportional geometry is applied'}})
    result['fallback_books']=sorted(result['fallback_books']+additions,key=lambda r:int(r['book_id']))
    result.update({'revision':2,'candidate1_proposal_sha256':ORIGINAL,'fallback_count':597,'restored_neutral_member_count':420,'retained201_neutral_member_count':417,'literal_patch5_template_member_count':3,'already_neutral_member_count':177,'fallback_season_counts':dict(collections.Counter(r['season_id'] for r in result['fallback_books'])),'supplemental_template_book_ids':['7051','7067','7069'],'supplemental_template_proof_sha256':SHA(audit_file.read_bytes()),'oversized_cover_geometry_status':'Approved whole640x240 to568x213 fit, centered36,13 on transparent640x240; exact source images retained for rollback.'})
    result['source_pins']+=[pin(old_file),pin(audit_file)]
    assert len(result['fallback_books'])==597 and result['fallback_season_counts']=={'70':7,'71':271,'92':319}
    data=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    put(ROOT/'audit/BANNER_REPAIR_PROPOSAL.json',data)
    print(json.dumps({'passed':True,'proposal_sha256':SHA(data),'fallback_count':597,'new_aliases':[r['fallback']['target_member'] for r in additions],'candidate1_proposal_sha256':ORIGINAL}))
if __name__=='__main__':main()
