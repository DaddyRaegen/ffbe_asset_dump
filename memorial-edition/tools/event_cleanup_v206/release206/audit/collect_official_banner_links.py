"""Fetch observed publisher article pages; inventory image links without edits."""
from pathlib import Path
import urllib.request,urllib.parse,json,re,hashlib,sys
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
PAGES={'7078':'https://jp.finalfantasy.com/news/2892','7065':'https://jp.finalfantasy.com/news/2940','7083':'https://jp.finalfantasy.com/news/2973','7076':'https://jp.finalfantasy.com/news/3017','7081':'https://jp.finalfantasy.com/news/2638','7082':'https://jp.finalfantasy.com/news/2835'}
class Images(HTMLParser):
 def __init__(self):super().__init__();self.images=[]
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='img':
   u=a.get('src','')
   if u.startswith('https://cache-jp.finalfantasy.com/uploads/content/'):
    self.images.append({'url':u,'alt':a.get('alt'),'html_dimensions':[a.get('width'),a.get('height')]})
def fetch(row):
 bid,u=row
 req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=30) as response:blob=response.read();final=response.url;status=response.status
 parser=Images();parser.feed(blob.decode('utf-8'))
 return {'book_id':bid,'page_url':u,'final_page_url':final,'http_status':status,'page_sha256':hashlib.sha256(blob).hexdigest(),'page_bytes':len(blob),'images':parser.images}
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(fetch,PAGES.items()))
output=ROOT/'audit/OFFICIAL_BANNER_LINKS.json'
output.write_text(json.dumps({'schema':'ffbe-v206-official-banner-web-source-links-v1','source_type':'Publisher-owned FF Portal dated event announcement pages','scope':'Only images linked in observed official pages; identity/visual admission is separate. No image edit or remote modification.','pages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
