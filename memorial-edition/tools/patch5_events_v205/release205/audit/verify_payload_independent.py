"""Independent local payload qualification before the signed APK is available."""
from pathlib import Path
import datetime,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'guard'))
import patch5_event_guard as g
PROJECT=Path('T:/Projects/FFBE Patch')
sys.path.insert(0,str(PROJECT/'story-ports/side-stories/scripts'))
from common import rows_bytes,FIELDS,crilayla
from cpk_convert import read_cpk

def main():
    plan=json.loads((ROOT/'audit/EVENT_PLAN.json').read_bytes())
    payload=ROOT/'payload'
    original=PROJECT/'localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk'
    content=original.with_name('FFBE-Memorial-EN-Patch-5-Content-Source.apk')
    graphpath=PROJECT/'localization-rounds/2026-10-03-native-delivery-v203/delivery_metadata/game_asset_manifest.json'
    g.require(g.file_sha(original)==g.BASELINE_SHA,'P5 production pin')
    g.require(g.file_sha(content)==g.CONTENT_SOURCE_SHA,'P5 content pin')
    g.require(g.file_sha(graphpath)==g.SOURCE_GRAPH_SHA,'Frozen graph pin')
    files=g.payload_inventory(payload,plan)
    admitted={r['path']:r for r in json.loads(graphpath.read_bytes())['assets'] if r['namespace']=='root' and r['path'].startswith('side_stories/') and r['path']!='side_stories/manifest.tsv'}
    g.require(set(files)==set(admitted),'Event dependency set')
    tables=g.qualify_tables(payload,plan,rows_bytes,lambda stem:g.production_table(stem,original,content,PROJECT))
    artwork=g.qualify_artwork(payload,plan,content,rows_bytes,FIELDS,read_cpk,crilayla)
    companions=g.qualify_companions(payload,plan,original,rows_bytes,read_cpk,ROOT/'audit/EVENT_COMPANION_ASSET_PROOF.json')
    with zipfile.ZipFile(original) as z:
        catalog,catalog_report=g.compare_catalog(z.read('assets/content_delivery.tsv'),(payload/'content_delivery.tsv').read_bytes(),files)
        source_manifest=Path('C:/Users/Raegen/Documents/Codex/2026-10-02/task-2/integration_work/native_delivery_correction/payload/side_stories/manifest.tsv')
        side_report=g.compare_side_manifest(z.read('assets/side_stories/manifest.tsv'),(payload/'side_stories/manifest.tsv').read_bytes(),files,catalog,source_manifest.read_bytes())
    tablepaths={r['candidate_relative_path'] for r in plan['table_provenance']}
    sources=[]
    for name,row in files.items():
        source=row['source'];blob=g.load_source(source)
        g.require(g.sha(blob)==source['sha256']==admitted[name]['sha256'] and len(blob)==source['bytes']==admitted[name]['bytes'],'Frozen admission differs: '+name)
        if name not in tablepaths and name!='side_stories/spdungeon9.cpk':
            g.require(g.sha(blob)==row['sha256'] and len(blob)==row['bytes'],'Raw payload differs: '+name)
        sources.append({'path':name,'source':source,'sha256':g.sha(blob),'bytes':len(blob)})
    report={'schema':'ffbe-patch5-event-only-payload-qualification-v1','passed':True,'table_checks':tables,
            'event_artwork':artwork,'event_companions':companions,'payload_file_count':len(files),'payload_bytes':sum(r['bytes'] for r in files.values()),
            'catalog':catalog_report,'side_manifest':side_report,
            'frozen_source_pins':sources,'plan_sha256':g.file_sha(ROOT/'audit/EVENT_PLAN.json'),
            'guard_sha256':g.file_sha(ROOT/'guard/patch5_event_guard.py'),'network_checks':False,'device_actions':False,
            'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (ROOT/'audit/INDEPENDENT_PAYLOAD_QUALIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'payload_files':len(files),'table_count':len(tables['tables']),
                      'original_artwork_members':artwork['original_member_count'],'new_artwork_members':artwork['appended_member_count']}))

if __name__=='__main__':main()
