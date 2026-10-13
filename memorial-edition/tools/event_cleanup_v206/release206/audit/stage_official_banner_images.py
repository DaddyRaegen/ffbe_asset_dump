"""Collect unmodified publisher originals for the requested banner work."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib,io,sys
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
links=json.loads((ROOT/'audit/OFFICIAL_BANNER_LINKS.json').read_text(encoding='utf-8'))
CHOICE={'7078':'news_200110_brave_8.JPG','7065':'news_200210_brave_9.JPG','7083':'news_200310_brave_8.jpg','7076':'news_200410_brave_8.jpg','7081':'news_190808_brave_7.JPG','7082':'news_191211_brave_8.JPG'}
previous=ROOT/'audit/OFFICIAL_BANNER_IMAGES.json'
cached={r['image_url']:r for r in json.loads(previous.read_text(encoding='utf-8'))['images']} if previous.exists() else {}
def collect(p):
 bid=p['book_id'];filename=CHOICE[bid]
 link=next(i for i in p['images'] if i['url'].endswith('/'+filename))
 u=link['url'];req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
 if u in cached:
  prior=cached[u];assert hashlib.sha256(Path(prior['staged_path']).read_bytes()).hexdigest()==prior['sha256']
  return prior
 with urllib.request.urlopen(req,timeout=30) as response:
  data=response.read(2_000_001);status=response.status;final=response.url;ctype=response.headers.get('Content-Type')
 assert len(data)<=2_000_000
 with Image.open(io.BytesIO(data)) as im:im.verify()
 with Image.open(io.BytesIO(data)) as im:size=list(im.size);fmt=im.format;mode=im.mode
 digest=hashlib.sha256(data).hexdigest();out=ROOT/'banner_sources/originals/official_web'/f'{bid}-{filename}'
 out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():assert out.read_bytes()==data
 else:out.write_bytes(data)
 return {'book_id':bid,'source_type':'Publisher-owned FF Portal image linked in exact dated event announcement','page_url':p['page_url'],'page_sha256':p['page_sha256'],'image_url':u,'final_image_url':final,'http_status':status,'content_type':ctype,'bytes':len(data),'sha256':digest,'dimensions':size,'format':fmt,'mode':mode,'staged_path':str(out),'image_edit_performed':False,'visual_admission_pending':True}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(collect,links['pages']))
out=ROOT/'audit/OFFICIAL_BANNER_IMAGES.json';out.write_text(json.dumps({'schema':'ffbe-v206-official-banner-web-originals-v1','images':rows,'no_image_edits':True,'no_remote_modification':True,'physical_runtime_tested':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
