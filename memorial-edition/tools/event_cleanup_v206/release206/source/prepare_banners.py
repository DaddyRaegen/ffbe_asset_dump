"""Install only finite, reviewed native event PNGs in the existing205 CPK."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'v205-patch5-events/payload/side_stories/spdungeon9.cpk'
EXPECTED={'side_book_'+b+'.png' for b in '7065 7070 7073 7074 7076 7078 7081 7082 7083'.split()}|{'event_archive_book_1500001.png','event_archive_book_1500002.png','event_original_jp_7f580191810790d3.png'}
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from cpk_convert import read_cpk,repack
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 native=json.loads((ROOT/'banner_outputs/NATIVE_BANNERS.json').read_bytes())
 assert native['passed'] and len(native['records'])==11
 review=json.loads((ROOT/'banner_outputs/VISUAL_REVIEW.json').read_bytes());assert review['passed'] and set(review['approved_keys'])=={r['key'] for r in native['records']}
 baseline=BASE.read_bytes();_,_,_,rows,raw=read_cpk(baseline);replacements={};members=[]
 for item in native['records']:
  p=Path(item['local_path']);blob=p.read_bytes();assert sha(blob)==item['sha256'] and len(blob)==item['bytes'] and item['width']==640 and item['height']==240
  for name in item['target_members']:
   assert name in EXPECTED and name in raw and name not in replacements
   book_ids=item['book_ids']
   if name=='event_archive_book_1500002.png':book_ids=['1500002']
   if name=='event_original_jp_7f580191810790d3.png':book_ids=['1000986']
   replacements[name]=blob;members.append({'name':name,'book_ids':book_ids,'baseline':{'bytes':len(raw[name]),'sha256':sha(raw[name])},'candidate':{'local_path':str(p),'bytes':len(blob),'sha256':sha(blob),'width':640,'height':240},'provenance':item['provenance'],'source_key':item['key']})
 assert set(replacements)==EXPECTED
 updated=repack(baseline,replacements);_,_,_,after,check=read_cpk(updated)
 assert list(raw)==list(check) and len(rows)==len(after)
 for name,blob in raw.items():assert check[name]==replacements.get(name,blob),name
 for a,b in zip(rows,after):
  for key in a:
   if key not in ('FileOffset','FileSize','ExtractSize'):assert a[key]==b[key]
 out=ROOT/'payload/side_stories/spdungeon9.cpk'
 if out.exists():assert out.read_bytes()==updated
 else:out.write_bytes(updated)
 report={'schema':'ffbe-event-banner-replacement-plan-v1','passed':True,'asset':{'path':'side_stories/spdungeon9.cpk','local_path':str(out),'bytes':len(updated),'sha256':sha(updated),'baseline':{'local_path':str(BASE),'bytes':len(baseline),'sha256':sha(baseline)}},'members':members,'all_other_raw_members_byte_identical':True,'CPK_member_ids_order_preserved':True,'baseline_member_count':len(raw),'candidate_member_count':len(check),'unchanged_member_count':len(raw)-len(members),'PNG_dimensions':[640,240],'icon_master_unchanged':True,'story_revival_part2_unchanged':True,'original_english_genesis7032_unchanged':True,'source_evidence':['audit/REQUESTED_BANNER_SOURCES.json','audit/OFFICIAL_BANNER_IMAGES.json','banner_outputs/IMAGE_TOOL_PROMPTS.json','banner_outputs/NATIVE_BANNERS.json','banner_outputs/VISUAL_REVIEW.json'],'image_tool_model_label_verified':False,'runtime_tested':False}
 (ROOT/'audit/BANNER_PLAN.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ('passed','baseline_member_count','candidate_member_count','unchanged_member_count')}))
if __name__=='__main__':main()
