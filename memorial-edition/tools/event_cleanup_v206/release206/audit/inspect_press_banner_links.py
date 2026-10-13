"""Read contemporary credited press pages to locate original event artwork."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import urllib.request,urllib.parse,json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
URLS=['https://www.gamer.ne.jp/news/%26word%3D%E3%83%96%E3%83%AC%E3%82%A4%E3%83%96%26page%3D19','https://dengekionline.com/articles/12287/']
if len(sys.argv)>1:URLS=sys.argv[1:]
class Links(HTMLParser):
 def __init__(self):super().__init__();self.images=[];self.links=[];self.link=None;self.text=[]
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  if t=='img':self.images.append({**a,'preceding_text':''.join(self.text)[-300:]})
  if t=='a':self.link={'href':a.get('href'),'text':''}
 def handle_data(self,s):
  if self.link is not None:self.link['text']+=s
  self.text.append(s)
 def handle_endtag(self,t):
  if t=='a' and self.link is not None:self.links.append(self.link);self.link=None
def fetch(u):
 req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
 with urllib.request.urlopen(req,timeout=30) as response:d=response.read();final=response.url;status=response.status
 page_path=ROOT/'banner_sources/press_pages'/('article-'+hashlib.sha256(u.encode()).hexdigest()[:16]+'.html')
 page_path.parent.mkdir(parents=True,exist_ok=True);page_path.write_bytes(d)
 p=Links();p.feed(d.decode('utf-8'))
 selected=[l for l in p.links if any(v in l['text'] for v in ['鏡像','エルナト','人形館'])]
 return {'page_url':u,'final_page_url':final,'http_status':status,'page_sha256':hashlib.sha256(d).hexdigest(),'page_bytes':len(d),'page_snapshot':str(page_path),'matching_links':selected,'images':p.images,'source_credit_clues':[s.strip() for s in p.text if any(v in s for v in ['2019年09月14','2019.06.07','スクウェア・エニックス','SQUARE ENIX','失われた鏡像','人形館の謎'])][:30]}
def safe_fetch(u):
 try:return fetch(u)
 except Exception as exc:return {'page_url':u,'error':str(exc),'status':'read_failed'}
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(safe_fetch,URLS))
p=ROOT/'audit/PRESS_BANNER_LINKS.json';p.write_text(json.dumps({'schema':'ffbe-v206-contemporary-press-banner-links-v1','pages':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{**r,'images':[i for i in r.get('images',[]) if any(v in i.get('preceding_text','') for v in ['鏡像','人形館','ストーリーイベント'])]} for r in rows],ensure_ascii=False))
