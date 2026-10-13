"""Inspect alpha geometry of finite neutral-card sources; no image edits."""
from pathlib import Path
from PIL import Image
import collections,hashlib,io,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import cpk_read
SHA=lambda b:hashlib.sha256(b).hexdigest()
def main():
 proposal=ROOT/'audit/BANNER_REPAIR_PROPOSAL.json'
 assert SHA(proposal.read_bytes())=='da1911049240d7ffb6ae21e5ab1b3bf2a4672d33dfc4e57a0052c7c0efa281e5'
 plan=json.loads(proposal.read_bytes());grouped=collections.defaultdict(set)
 for r in plan['fallback_books']:grouped[r['fallback']['archive']].add(r['fallback']['member'])
 sources={}
 for archive,names in grouped.items():sources[archive]=cpk_read(archive,lambda n:n in names)
 records=[]
 for row in plan['fallback_books']:
  s=row['fallback'];blob=sources[s['archive']][s['member']];assert SHA(blob)==s['sha256'] and len(blob)==s['bytes']
  im=Image.open(io.BytesIO(blob));a=im.convert('RGBA').getchannel('A')
  bounds={str(t):a.point(lambda v:255 if v>=t else 0).getbbox() for t in (1,32,128,224,255)}
  records.append({'book_id':row['book_id'],'title':row['title'],'source':s,'mode':im.mode,'dimensions':list(im.size),'alpha_extrema':list(a.getextrema()),'alpha_bbox_by_threshold':bounds,'full_canvas_alpha128':bounds['128']==(0,0,640,240)})
 result={'schema':'ffbe208-neutral-card-geometry-audit-v1','passed':True,'proposal_sha256':SHA(proposal.read_bytes()),'count':len(records),'dimensions_histogram':dict(collections.Counter('x'.join(map(str,r['dimensions'])) for r in records)),'alpha128_bounds_histogram':dict(collections.Counter(str(r['alpha_bbox_by_threshold']['128']) for r in records)),'full_canvas_alpha128_count':sum(r['full_canvas_alpha128'] for r in records),'records':records,'image_edits':False,'payload_writes':False,'network_requests':0}
 (ROOT/'audit/NEUTRAL_CARD_GEOMETRY.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:result[k] for k in ['count','dimensions_histogram','alpha128_bounds_histogram','full_canvas_alpha128_count']}))
if __name__=='__main__':main()
