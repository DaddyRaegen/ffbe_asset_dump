"""Retrieve unmodified event artwork credited in contemporary press."""
from pathlib import Path
from PIL import Image
import urllib.request,urllib.parse,hashlib,json,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
links=json.loads((ROOT/'audit/PRESS_BANNER_LINKS.json').read_text(encoding='utf-8'))
pages={p['page_url']:p for p in links['pages']}
url='https://dengekionline.com/articles/12287/'
page=pages[url]
item=next(i for i in page['images'] if '人形館の謎' in i.get('preceding_text',''))
image_url=urllib.parse.urljoin(url,item['data-src'])
dst=ROOT/'banner_sources/originals/press_mirrors/7070-dengeki-12287-dollhouse.jpg'
dst.parent.mkdir(parents=True,exist_ok=True)
if not dst.exists():
 with urllib.request.urlopen(urllib.request.Request(image_url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:data=r.read()
 dst.write_bytes(data)
data=dst.read_bytes()
with Image.open(dst) as im:dims=list(im.size);mode=im.mode;fmt=im.format
row={'book_id':'7070','page_url':url,'page_date':'2019-09-14','article_snapshot':page['page_snapshot'],'article_sha256':page['page_sha256'],'image_url':image_url,'staged_path':str(dst),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'dimensions':dims,'mode':mode,'format':fmt,'adjacent_article_text':item['preceding_text'],'article_credit':'(C) 2015-2019 SQUARE ENIX CO., LTD. All Rights Reserved. Developed by Alim Co., Ltd.','source_kind':'contemporary_press_mirror_of_publisher_presentation_artwork','primary_origin_is_inference':True,'primary_origin_basis':'The contemporaneous article describes information presented at the Square Enix studio booth at TGS2019, labels this image under the exact event title and credits Square Enix/Alim. Hosted by Dengeki, not the publisher.','image_editing_performed':False,'visual_admission_pending':True}
out=ROOT/'audit/PRESS_BANNER_IMAGES.json'
existing=json.loads(out.read_text(encoding='utf-8')) if out.exists() else {'schema':'ffbe-v206-contemporary-press-banner-originals-v1','images':[]}
existing['images']=[r for r in existing['images'] if r['book_id']!='7070']+[row]
out.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(row,ensure_ascii=False))
url='https://gamebiz.jp/news/240327';page=pages[url]
item=next(i for i in page['images'] if i.get('preceding_text','').rstrip().endswith('ストーリーイベント「失われた鏡像」開催！'))
image_url=item['data-src']
dst=ROOT/'banner_sources/originals/press_mirrors/7073-gamebiz-240327-lost-reflection.png'
if not dst.exists():
 with urllib.request.urlopen(urllib.request.Request(image_url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:data=r.read()
 dst.write_bytes(data)
data=dst.read_bytes()
with Image.open(dst) as im:dims=list(im.size);mode=im.mode;fmt=im.format
row={'book_id':'7073','page_url':url,'page_date':'2019-06-07','article_snapshot':page['page_snapshot'],'article_sha256':page['page_sha256'],'image_url':image_url,'staged_path':str(dst),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'dimensions':dims,'mode':mode,'format':fmt,'adjacent_article_text':item['preceding_text'],'article_credit':'© 2015-2019 SQUARE ENIX CO., LTD. All Rights Reserved. Developed by Alim Co., Ltd.','source_kind':'contemporary_press_mirror_of_publisher_announcement_artwork','primary_origin_is_inference':True,'primary_origin_basis':'The 2019-06-07 article identifies Square Enix as the announcer and labels this image immediately after the exact Lost Reflection story event heading. It credits Square Enix/Alim. Hosted by Gamebiz, not the publisher.','image_editing_performed':False,'visual_admission_pending':True}
existing['images']=[r for r in existing['images'] if r['book_id']!='7073']+[row]
out.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(row,ensure_ascii=False))
