from pathlib import Path
import json,sys,hashlib
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import rows_bytes,readable
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
P205=ROOT.parent/'v205-patch5-events/payload/side_stories'
OLD=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction\banner_audit')
titles=['The Lost Reflection','Seaside Daydream','Dollhouse','The Shield Maiden and the Dream Stage','A Baton Passed to the Future','The World Is My Canvas','Princess','An Accompanist in My Heart','Genesis of Chaos','Gathering','Story Event Revival','Party Test']
for stem in ['Nm36woZx','LM1APs6u','YW9MUm2H']:
 rows=[readable(r) for r in rows_bytes((P205/(stem+'.dat')).read_bytes(),stem)]
 print(json.dumps({'table':stem,'row_count':len(rows),'first':rows[0]},ensure_ascii=False))
 matches=[r for r in rows if any(t.lower() in json.dumps(r,ensure_ascii=False).lower() for t in titles)]
 print(json.dumps({'table':stem,'title_matches':matches},ensure_ascii=False))
mapping=json.loads((OLD/'book_banner_mapping.json').read_text(encoding='utf-8'))['books']
for r in mapping:
 if any(t.lower() in json.dumps(r.get('current_name',''),ensure_ascii=False).lower() for t in titles):
  print(json.dumps({'prior_banner_book':{k:r.get(k) for k in ['book_id','current_name','current_icon_id','current_icon','sources','status']}},ensure_ascii=False))
