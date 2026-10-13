"""Read retained CPK tables only; no member extraction or source changes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import csv,json,hashlib,sys,collections,time
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,r'T:\Projects\FFBE Patch\story-ports\side-stories\scripts')
from common import cpk_entries
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
INV=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\catalog_output\asset_filename_clues.csv')
focus=json.loads((ROOT/'audit/REQUESTED_BANNER_SOURCES.json').read_text(encoding='utf-8'))
wanted=sorted({c['member'] for b in focus['books'] for e in b['source_events'] for c in e['candidates'] if c.get('status')=='exact_named_member_absent_from_retained_region_CPK_index'})
wanted_set=set(wanted)
sources=[r for r in csv.DictReader(INV.open(encoding='utf-8-sig')) if r['extension']=='.cpk' and (r['region']=='JP' or '\\en\\' in r['path'] or '\\common_lang\\' in r['path'])]

def check(r):
 p=Path(r['path'])
 try:
  with p.open('rb') as f:h,rows=cpk_entries(f)
  matches=[]
  for m in rows:
   if m['FileName'] in wanted_set:
    matches.append({'server':r['region'],'source_path':str(p),'source_bytes':p.stat().st_size,'source_member':'/'.join(s for s in (m['DirName'],m['FileName']) if s),'member_offset':min(h['TocOffset'],h['ContentOffset'])+m['FileOffset'],'packed_bytes':m['FileSize'],'extracted_bytes':m['ExtractSize']})
  return {'matches':matches,'members':len(rows)}
 except Exception as e:return {'error':{'path':str(p),'type':type(e).__name__,'message':str(e)}}

errors=[];matches=[];members=0;start=time.monotonic()
with ThreadPoolExecutor(max_workers=6) as pool:
 for n,result in enumerate(pool.map(check,sources),1):
  if result.get('error'):errors.append(result['error'])
  else:members+=result['members'];matches.extend(result['matches'])
  if n%2000==0:print(json.dumps({'cpks_checked':n,'matches':len(matches),'errors':len(errors)}),flush=True)
report={'schema':'ffbe-v206-missing-banner-retained-cpk-search-v1','inventory':{'path':str(INV),'sha256':hashlib.sha256(INV.read_bytes()).hexdigest()},'scope':'Every retained JP and GL English/common CPK in the existing dump inventory, across all pack names. CPK headers/TOCs read only; no payloads decrypted or changed. Other GL language variants are not automatically admitted.','wanted_filenames':wanted,'source_packs':len(sources),'packs_by_region':dict(collections.Counter(r['region'] for r in sources)),'member_rows_read':members,'matches':matches,'errors':errors,'elapsed_seconds':round(time.monotonic()-start,2),'complete':not errors,'no_source_edits':True,'network_requests':0}
out=ROOT/'audit/MISSING_BANNER_MEMBER_SEARCH.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':str(out),'source_packs':len(sources),'member_rows':members,'matches':len(matches),'errors':len(errors)}),flush=True)
