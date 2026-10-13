"""Stage608 approved fits and50 pixel-preserving nativecanvas wrappers."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'v206-event-cleanup'
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from cpk_convert import read_cpk
from common import cpk_read
from candidate1_archive import put
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 plan=json.loads((BASE/'audit/BANNER_PLAN.json').read_bytes());assert plan['passed'] and len(plan['members'])==12
 proposal=ROOT/'audit/BANNER_REPAIR_PROPOSAL.json'
 assert SHA(proposal.read_bytes())=='0a9e374dd92c47bef4e6ad8f7b40a9bc86a9eef16f84d2f7fd24687cb90ee251'
 approved=json.loads(proposal.read_bytes());assert approved['passed'] and approved['fallback_count']==597
 cpk=BASE/'payload/side_stories/spdungeon9.cpk';blob=cpk.read_bytes();assert SHA(blob)==plan['asset']['sha256']
 _,_,_,rows,members=read_cpk(blob);out=ROOT/'banner_sources/current206';out.mkdir(parents=True,exist_ok=True);records=[]
 for item in plan['members']:
  name=item['name'];data=members[name];assert SHA(data)==item['candidate']['sha256'] and len(data)==item['candidate']['bytes'] and data.startswith(b'\x89PNG\r\n\x1a\n')
  if name=='side_book_7074.png':continue # Already correctly inset602x203 at19,19.
  target=out/name
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  records.append({'name':name,'book_ids':item['book_ids'],'kind':'generated206','local_path':str(target),'bytes':len(data),'sha256':SHA(data),'source_archive':str(cpk),'source_archive_sha256':SHA(blob),'source_member':name,'source_qualified206_plan_sha256':SHA((BASE/'audit/BANNER_PLAN.json').read_bytes())})
 grouped={}
 for r in approved['fallback_books']:grouped.setdefault(r['fallback']['archive'],set()).add(r['fallback']['member'])
 neutral=ROOT/'banner_sources/neutral';neutral.mkdir(parents=True,exist_ok=True)
 for archive,names in grouped.items():
  source=Path(archive);raw=cpk_read(source,lambda n:n in names);archive_sha=SHA(source.read_bytes())
  for r in approved['fallback_books']:
   f=r['fallback']
   if f['archive']!=archive:continue
   data=raw[f['member']];assert SHA(data)==f['sha256'] and len(data)==f['bytes'] and data.startswith(b'\x89PNG\r\n\x1a\n')
   target=neutral/f['target_member']
   if target.exists():assert target.read_bytes()==data
   else:target.write_bytes(data)
   kind='neutral_P5_template' if r.get('source_origin')=='literal_patch5_template' else 'neutral_retained201' if r.get('source_identity') else 'neutral_current207'
   records.append({'name':f['target_member'],'book_ids':[r['book_id']],'kind':kind,'local_path':str(target),'bytes':len(data),'sha256':SHA(data),'source_archive':archive,'source_archive_sha256':archive_sha,'source_member':f['member'],'source_identity':r.get('source_identity'),'source_proposal_sha256':SHA(proposal.read_bytes())})
 assert len(records)==608 and len({r['name'] for r in records})==608
 wrapper_file=ROOT/'audit/NATIVE_CANVAS_WRAPPER_PLAN.json'
 assert SHA(wrapper_file.read_bytes())=='037f3e3e4a0786404b995e279a8c2dd8d0bea97b2f5470530e2e7782fe0a98cf'
 wrappers=json.loads(wrapper_file.read_bytes());assert wrappers['passed'] and wrappers['member_count']==50
 names={r['source_member'] for r in wrappers['records']};archive=Path(wrappers['source_archive'])
 source=cpk_read(archive,lambda n:n in names);assert SHA(archive.read_bytes())==wrappers['source_archive_sha256']
 directory=ROOT/'banner_sources/native_canvas';directory.mkdir(parents=True,exist_ok=True)
 for r in wrappers['records']:
  data=source[r['source_member']];assert len(data)==r['bytes'] and SHA(data)==r['sha256']
  target=directory/r['name']
  if target.exists():assert target.read_bytes()==data
  else:target.write_bytes(data)
  records.append({'name':r['name'],'book_ids':r['book_ids'],'kind':'native_canvas_wrapper','local_path':str(target),'bytes':len(data),'sha256':SHA(data),'source_archive':r['source_archive'],'source_archive_sha256':r['source_archive_sha256'],'source_member':r['source_member'],'original_source_member':r['original_source_member'],'original_source_sha256':r['original_source_sha256'],'source_wrapper_plan_sha256':SHA(wrapper_file.read_bytes())})
 assert len(records)==658 and len({r['name'] for r in records})==658
 report={'schema':'ffbe208-approved-banner-geometry-input-v1','passed':True,'source_versionCode':207,'geometry':[640,240],'approved_content_box':[610,213],'approved_expected_resized_art':[568,213],'approved_offset':[36,13],'approved_padding':[36,13,36,14],'approved_kernel':'lanczos3','transform':'608 proportional whole-canvas fits plus50 pixel-preserving600x120 wrappers at20,60 on transparent640x240; no alpha crop, recolor or creative image generation.','fit_count':608,'native_canvas_wrapper_count':50,'wrapper_plan_sha256':SHA(wrapper_file.read_bytes()),'records':records,'genuine_genesis7032_unchanged_sha256':SHA(members['side_book_7032.png']),'already_inset7074_unchanged_sha256':SHA(members['side_book_7074.png']),'already_inset7075_unchanged_sha256':SHA(members['side_book_7075.png']),'source_images_edited':False}
 put(ROOT/'audit/BANNER_GEOMETRY_INPUTS.json',(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
 print(json.dumps({'passed':True,'member_count':len(records),'genuine_genesis7032_unchanged_sha256':report['genuine_genesis7032_unchanged_sha256']}))
if __name__=='__main__':main()
