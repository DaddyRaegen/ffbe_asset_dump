"""Verify all 500 event download ranges from exact local pack bytes."""
from pathlib import Path
import datetime,json,sys,urllib.parse,zipfile,zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'guard'))
import patch5_event_guard as g
FROZEN=Path('C:/Users/Raegen/Documents/Codex/2026-10-02/task-2/integration_work/native_delivery_correction/asset_publication')
GRAPH=Path('T:/Projects/FFBE Patch/localization-rounds/2026-10-03-native-delivery-v203/delivery_metadata/game_asset_manifest.json')
BASELINE=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk')

def check_wire(row,wire):
    g.require(len(wire)==row['wirebytes'],'Truncated transport wire bytes')
    if row['method']==8:
        decoder=zlib.decompressobj(-15)
        decoded=decoder.decompress(wire)+decoder.flush()
        g.require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,'Deflate slice has truncation or trailing bytes')
    else:
        decoded=wire
    g.require(len(decoded)==row['bytes'] and g.sha(decoded)==row['sha256'],'Downloaded raw bytes differ from signed payload metadata')
    return {'wire_sha256':g.sha(wire),'decoded_sha256':g.sha(decoded),'decoded_bytes':len(decoded)}

def main():
    g.require(g.file_sha(GRAPH)==g.SOURCE_GRAPH_SHA,'Frozen graph pin differs')
    g.require(g.file_sha(FROZEN/'manifest.json')==g.SOURCE_GRAPH_SHA,'Frozen transport source manifest pin differs')
    g.require(g.file_sha(BASELINE)==g.BASELINE_SHA,'Production APK pin differs')
    signed=ROOT/'staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk'
    qualification=json.loads((ROOT/'staged_build/SIGNED_EVENT_QUALIFICATION.json').read_bytes())
    g.require(qualification['passed'] and g.file_sha(signed)==qualification['apk_sha256'],'Signed APK qualification/pin differs')
    plan=json.loads((ROOT/'audit/EVENT_PLAN.json').read_bytes())
    files={r['relative_path']:r for r in plan['payload_files']}
    admitted={r['path']:r for r in json.loads(GRAPH.read_bytes())['assets']
              if r['namespace']=='root' and r['path'].startswith('side_stories/') and r['path']!='side_stories/manifest.tsv'}
    with zipfile.ZipFile(BASELINE) as z:old=g.parse_catalog(z.read('assets/content_delivery.tsv'))
    with zipfile.ZipFile(signed) as z:catalogblob=z.read('assets/content_delivery.tsv')
    rows=g.parse_catalog(catalogblob)
    changes={p for p in rows if p not in old or rows[p]['line']!=old[p]['line']}
    g.require(changes==set(files)==set(admitted),'Exact changed event descriptor set differs')
    identity=g.sha(json.dumps([{'path':r['relative_path'],'sha256':r['sha256'],'bytes':r['bytes']}
        for r in sorted(files.values(),key=lambda r:r['relative_path'])],sort_keys=True,separators=(',',':')).encode())
    tag='beta-content-v205-'+identity[:16]
    download_plan=json.loads((ROOT/'asset_publication/DOWNLOAD_PLAN.json').read_bytes())
    g.require(download_plan['passed'] and download_plan['release_tag']==tag and download_plan['catalog_identity_sha256']==identity,
              'Transport release identity differs')
    pack=download_plan['new_pack'];newpack=Path(pack['path'])
    packhash=g.file_sha(newpack)
    g.require(packhash==pack['sha256'] and newpack.stat().st_size==pack['bytes'] and
              newpack.name=='patch5-events-v205-'+packhash[:16]+'.pack','New pack pin/name differs')
    prefix='https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/'+tag+'/'
    g.require(pack['url']==prefix+newpack.name,'New pack URL identity differs')
    receipts=[];reused=rebuilt=0
    for name in sorted(files):
        row=rows[name];asset=files[name];source=admitted[name]
        g.require(row['sha256']==asset['sha256'] and row['bytes']==asset['bytes'],'Catalog payload pin differs')
        g.immutable_transport(row)
        if row['sha256']==source['sha256'] and row['bytes']==source['bytes']:
            t=source['transport']
            g.require((row['url'],row['offset'],row['wirebytes'],row['method'],row['sourcebytes'])==
                      (t['url'],t['offset'],t['wire_bytes'],t['method'],t['source_bytes']),
                      'Reused descriptor differs from frozen transport: '+name)
            local=FROZEN/urllib.parse.urlsplit(row['url']).path.rsplit('/',1)[1]
            mode='reused_frozen203';reused+=1
        else:
            g.require(row['url']==pack['url'] and row['sourcebytes']==newpack.stat().st_size and row['method']==8,
                      'Rebuilt descriptor does not use the exact new immutable pack: '+name)
            local=newpack;mode='rebuilt_v205';rebuilt+=1
        g.require(local.stat().st_size==row['sourcebytes'],'Transport source byte count differs: '+name)
        with local.open('rb') as f:
            f.seek(row['offset']);wire=f.read(row['wirebytes'])
        checked=check_wire(row,wire)
        receipts.append({'path':name,'mode':mode,'source_file':str(local),'url':row['url'],
                         'offset':row['offset'],'wire_bytes':row['wirebytes'],'method':row['method'],**checked})
    g.require(reused==495 and rebuilt==5,'Expected495 reused and5 precisely rebuilt event transports')
    report={'schema':'ffbe-patch5-event-transport-qualification-v1','passed':True,'assets_verified':len(receipts),
            'reused_frozen203':reused,'rebuilt_v205':rebuilt,'release_tag':tag,'catalog_identity_sha256':identity,
            'source_graph_sha256':g.SOURCE_GRAPH_SHA,'new_pack_sha256':packhash,'new_pack_bytes':newpack.stat().st_size,
            'signed_apk_sha256':qualification['apk_sha256'],'signed_catalog_sha256':g.sha(catalogblob),
            'content_catalog_sha256':g.sha(catalogblob),'download_plan_sha256':g.file_sha(ROOT/'asset_publication/DOWNLOAD_PLAN.json'),
            'event_plan_sha256':g.file_sha(ROOT/'audit/EVENT_PLAN.json'),'source_manifest_sha256':g.file_sha(FROZEN/'manifest.json'),
            'local_pack_slices':receipts,'guard_sha256':g.file_sha(ROOT/'guard/patch5_event_guard.py'),
            'auditor_sha256':g.file_sha(__file__),'network_checks':False,'device_actions':False,
            'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','assets_verified','reused_frozen203','rebuilt_v205','release_tag','new_pack_sha256')}))

if __name__=='__main__':main()
