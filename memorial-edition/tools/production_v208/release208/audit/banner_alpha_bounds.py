"""Bounded PNG canvas/alpha inspection, without editing or extracting art."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT.parent/'v206-event-cleanup'
paths=list((PREVIOUS/'banner_sources/current205').glob('*.png'))+list((PREVIOUS/'banner_outputs/native').glob('*.png'))
records=[]
for path in sorted(paths):
 with Image.open(path) as image:
  alpha=image.convert('RGBA').getchannel('A')
  records.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mode':image.mode,'canvas':list(image.size),'alpha_bbox':alpha.getbbox(),'alpha_extrema':alpha.getextrema(),'nontransparent_pixel_count':sum(alpha.histogram()[1:]),'fully_opaque_pixel_count':alpha.histogram()[255]})
report={'schema':'ffbe-v208-bounded-banner-alpha-bounds-v1','read_only':True,'image_edits':False,'displayed_size_proven':False,'records':records}
(ROOT/'audit/BANNER_ALPHA_BOUNDS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(ROOT/'audit/BANNER_ALPHA_BOUNDS.json'),'records':records}))
