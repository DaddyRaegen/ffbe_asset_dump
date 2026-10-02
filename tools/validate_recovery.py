"""Validate recovered files and publish a source manifest and category catalog."""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from PIL import Image
from recover_assets import save, verify_bytes, PRIORITY

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    args=p.parse_args();repo=args.repo;work=args.work
    recovered=json.loads((work/'recovered.json').read_text())
    inventory=json.loads((work/'inventory.json').read_text())
    baseline=json.loads((work/'baseline.json').read_text())
    failures=[]
    def check(item):
        dest,record=item
        try:
            data=(repo/dest).read_bytes()
            assert hashlib.sha256(data).hexdigest()==record['sha256'], 'SHA-256 mismatch'
            assert len(data)==record['bytes'], 'size mismatch'
            verify_bytes(Path(dest).name,data)
        except Exception as e:return {'path':dest,'error':str(e)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i,result in enumerate(pool.map(check,sorted(recovered.items())),1):
            if result:failures.append(result)
            if i%5000==0:print(f'Validated {i}/{len(recovered)} files',flush=True)
    groups=[('units','unit','unit_animated','unit_animated_csv','unit_idle_cgs'),
            ('monsters','monster','monster_animated','monster_animated_csv','monster_idle_cgs'),
            ('vision_cards','vc_vignette','vc_vignette_animated','vc_animated_csv','vc_cgs')]
    catalog={};animation_checks={}
    for label,prefix,folder,csvfolder,cgsname in groups:
        ids=sorted(m[1] for path in (repo/folder).glob('*.png') if (m:=re.fullmatch(prefix+r'_anime_(\d+)\.png',path.name)))
        entries=[];new_count=0;bounds=[];bad_indices=[];missing=[]
        for uid in ids:
            sheet=f'{folder}/{prefix}_anime_{uid}.png';pre='vc' if prefix=='vc_vignette' else prefix
            cgg=f'{csvfolder}/{pre}_cgg_{uid}.csv';cgs=f'{csvfolder}/{cgsname}_{uid}.csv'
            is_new=sheet in recovered
            entry={'id':uid,'sprite_sheet':sheet,'frame_data':cgg if (repo/cgg).exists() else None,'idle_animation':cgs if (repo/cgs).exists() else None,'added_in_recovery':is_new}
            entries.append(entry)
            if not is_new:continue
            new_count+=1
            if not entry['frame_data'] or not entry['idle_animation']:
                missing.append(uid);continue
            rows=(repo/cgg).read_text(encoding='utf-8-sig').splitlines()
            idle_indices=set()
            for line in (repo/cgs).read_text(encoding='utf-8-sig').splitlines():
                if not line.strip():continue
                idx=int(line.split(',')[0])
                idle_indices.add(idx)
                if idx<0 or idx>=len(rows):bad_indices.append({'id':uid,'index':idx,'frames':len(rows)})
            # Atlas bounds for single-page sprites identify HD/SD mismatches.
            with Image.open(repo/sheet) as image:width,height=image.size
            for row_no,line in enumerate(rows):
                values=[int(v) for v in line.strip().split(',') if v]
                if len(values)<2 or not values[1]:continue
                count=values[1];parts=values[2:];stride=len(parts)//count
                if len(parts)%count or stride<10:
                    failures.append({'path':cgg,'row':row_no,'error':'invalid CGG part layout'});continue
                for start in range(0,len(parts),stride):
                    part=parts[start:start+stride];page=part[10] if stride>10 else 0
                    x,y,w,h=part[6:10]
                    if page==0 and (x<0 or y<0 or x+w>width or y+h>height):
                        bounds.append({'id':uid,'row':row_no,'rectangle':[x,y,w,h],'atlas':[width,height],'used_by_idle':row_no in idle_indices})
        if label == 'units' and (repo/'catalog/unit_identity_decisions.json').exists():
            from build_unit_master import annotate_legacy
            decisions=json.loads((repo/'catalog/unit_identity_decisions.json').read_text(encoding='utf-8'))
            entries=annotate_legacy(entries,decisions)
        catalog[label]=entries
        animation_checks[label]={'new_sprite_ids':new_count,'missing_companions':missing,'invalid_idle_frame_references':bad_indices,'atlas_bounds_warnings':bounds}
    selected={d for d in inventory if d not in baseline and not d.startswith('additional/')}
    remaining=sorted(selected-set(recovered))
    baseline_commit=(work/'baseline-commit.txt').read_text().strip()
    changes=subprocess.check_output(['git','-C',str(repo),'diff','--name-only',baseline_commit],text=True).splitlines()
    changed_assets=[d for d in changes if d in baseline and '/' in d]
    summary={'baseline_commit':baseline_commit,
             'files_added':len(recovered),'bytes_added':sum(v['bytes'] for v in recovered.values()),
             'priority_files_added':sum(Path(d).name.startswith(PRIORITY) for d in recovered),
             'extra_files_added':sum(not Path(d).name.startswith(PRIORITY) for d in recovered),
             'by_folder':dict(sorted(collections.Counter(d.split('/')[0] for d in recovered).items())),
             'plaintext_members_recovered':sum('extraction' in r for r in recovered.values()),
             'file_validation_errors':failures,'remaining_selected_gaps':remaining,
             'existing_asset_files_changed':changed_assets,'animation_checks':animation_checks,
             'additional_visual_destinations_not_imported':sum(d.startswith('additional/') and d not in baseline for d in inventory)}
    save(work/'validation.json',summary)
    report_date=datetime.now(timezone.utc).date().isoformat()
    reports=repo/'reports'/f'{report_date}-recovery';reports.mkdir(parents=True,exist_ok=True)
    save(reports/'summary.json',summary)
    for label,entries in catalog.items():save(repo/'catalog'/f'{label}.json',entries)
    if (repo/'catalog/unit_identity_decisions.json').exists():
        from build_unit_master import build_master, read_json, DEFAULT_REPORT
        # Preserve the regional registry when regenerating the legacy catalogs.
        # Missing evidence is an error; never collapse collisions back to raw IDs.
        master=build_master(read_json(repo/'catalog/unit_identity_sources.json'),
                            read_json(repo/'catalog/unit_identity_decisions.json'),
                            catalog['units'],read_json(repo/DEFAULT_REPORT),repo=repo)
        (repo/'catalog/unit_master.json').write_text(json.dumps(master,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        from validate_unit_identities import validate
        validate(repo)
    with (reports/'source-manifest.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['destination','source','member','bytes','sha256','extraction'])
        for dest,r in sorted(recovered.items()):writer.writerow([dest,r['source'],r.get('member',''),r['bytes'],r['sha256'],r.get('extraction','standard')])
    print(json.dumps({k:v for k,v in summary.items() if k!='animation_checks'},indent=2))
    print(json.dumps({k:{x:len(y) if isinstance(y,list) else y for x,y in v.items()} for k,v in animation_checks.items()},indent=2))
    if failures or remaining or any(v['missing_companions'] or v['invalid_idle_frame_references'] for v in animation_checks.values()):raise SystemExit(1)

if __name__=='__main__':main()
