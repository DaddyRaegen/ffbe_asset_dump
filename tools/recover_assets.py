"""Inventory and recover FFBE visual assets without replacing existing files.

The source dump is read-only. JP archives require the user's DataExtractor.exe
and its sibling DLLs/CriPakTools.exe; those binaries are never redistributed.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from cpk import Cpk

PRIORITY = ('unit_', 'monster_', 'battle_bg_', 'vc_')
VISUAL = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.csv', '.ssbp', '.plist', '.atlas', '.skel', '.eff', '.efk', '.efkefc', '.bmb', '.m3r', '.bin', '.maps', '.map', '.fnt'}
IMAGES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2, sort_keys=True), encoding='utf-8', newline='\n')

def safe_name(name):
    if not name or Path(name).name != name or any(c in name for c in '\\/:') or name in ('.', '..'):
        raise ValueError(f'unsafe member filename: {name!r}')
    return name

def category(name, source, baseline_by_name):
    n = name.lower()
    ext = Path(n).suffix
    if n.startswith('unit_'):
        if ext == '.csv': return 'unit_animated_csv'
        if n.startswith('unit_anime_'): return 'unit_animated'
        if n.startswith('unit_icon_'): return 'unit_icons'
        if n.startswith('unit_ills_'): return 'unit_illustrations'
        return 'unit_assets'
    if n.startswith('monster_'):
        if ext == '.csv': return 'monster_animated_csv'
        if n.startswith('monster_anime_'): return 'monster_animated'
        if n.startswith('monster_icon_'): return 'monster_icon'
        return 'monster_assets'
    if n.startswith('battle_bg_'): return 'battle_bg'
    if n.startswith('vc_'):
        if ext == '.csv': return 'vc_animated_csv'
        for prefix, folder in [('vc_vignette_anime_', 'vc_vignette_animated'), ('vc_vignette_item_', 'vc_vignette_item'), ('vc_vignette_icon_', 'vc_vignette_icon'), ('vc_bg_', 'vc_bg'), ('vc_frame_', 'vc_frame')]:
            if n.startswith(prefix): return folder
        return 'vc_assets'
    if name in baseline_by_name: return baseline_by_name[name][0].split('/')[0]
    for prefix, folder in [('global_ability_', 'global_abilities'), ('global_emblem_', 'global_emblems'), ('global_equip_', 'global_equipment'), ('global_item_', 'global_items'), ('global_materia_', 'global_materia'), ('ability_', 'abilities'), ('emblem_', 'emblems'), ('equip_', 'equip'), ('item_', 'items'), ('materia_', 'materia'), ('chain_ability_', 'chain_ability'), ('ex_gambit_icon_', 'ex_gambit_icons')]:
        if n.startswith(prefix): return folder
    # Unknown assets retain their archive category, region and localization.
    p = source.replace('\\', '/').split('/')
    region = p[0].removeprefix('FFBE_').lower()
    if 'dlc_assets_prod' in p:
        rest = p[p.index('dlc_assets_prod') + 1:]
        if len(rest) >= 4 and rest[1] in ('sd', 'hd'): return '/'.join(['additional', region, *rest[:1], *rest[2:-1]])
    if 'resource' in p:
        rest = p[p.index('resource') + 1:]
        return '/'.join(['additional', region, *rest[:-1]])
    return '/'.join(['additional', region, 'loose', *p[1:-1]])

def rank(candidate):
    s = candidate['source'].lower()
    ver = re.search(r'/ver(\d+)_', s)
    return (0 if '/hd/' in s else 1, 0 if s.startswith('ffbe_jp/') else 1,
            -int(ver[1]) if ver else 0, 0 if candidate['kind'] == 'cpk' else 1, s)

def inventory(args):
    if not (args.work/'baseline.json').exists():
        tree = subprocess.check_output(['git', '-C', str(args.repo), 'ls-tree', '-r', '-l', 'HEAD'], text=True)
        baseline = {}
        for line in tree.splitlines():
            metadata, path = line.split('\t', 1)
            baseline[path] = int(metadata.split()[-1])
        save(args.work/'baseline.json', baseline)
        commit = subprocess.check_output(['git', '-C', str(args.repo), 'rev-parse', 'HEAD'], text=True).strip()
        (args.work/'baseline-commit.txt').write_text(commit+'\n', encoding='utf-8')
    baseline = json.loads((args.work/'baseline.json').read_text())
    by_name = collections.defaultdict(list)
    for path in baseline: by_name[Path(path).name].append(path)
    assets = collections.defaultdict(list); errors = []; archives = []; extensions = collections.Counter()
    files = sorted(p for p in args.dump.rglob('*') if p.is_file())
    t = time.time()
    for i, path in enumerate(files):
        rel = path.relative_to(args.dump).as_posix()
        if path.suffix.lower() == '.cpk':
            try:
                c = Cpk(path)
                try:
                    entries = c.entries
                    archives.append({'source': rel, 'members': len(entries), 'bytes': path.stat().st_size})
                    for e in entries:
                        name = safe_name(e['name']); ext = Path(name).suffix.lower(); extensions[ext] += 1
                        if ext not in VISUAL: continue
                        dest = f'{category(name, rel, by_name)}/{name}'
                        assets[dest].append({'source': rel, 'kind': 'cpk', 'entry': e})
                finally: c.f.close()
            except Exception as e: errors.append({'source': rel, 'error': str(e)})
        elif path.suffix.lower() in IMAGES:
            dest = f'{category(path.name, rel, by_name)}/{path.name}'
            assets[dest].append({'source': rel, 'kind': 'loose'})
        if (i + 1) % 2000 == 0: print(f'Indexed {i+1}/{len(files)} sources; {len(assets)} destinations; {len(errors)} errors', flush=True)
    for values in assets.values(): values.sort(key=rank)
    summary = {'source_files': len(files), 'archives': len(archives), 'archive_members': sum(x['members'] for x in archives),
               'destinations': len(assets), 'new_destinations': sum(x not in baseline for x in assets), 'errors': errors,
               'extensions': dict(extensions), 'new_by_folder': dict(collections.Counter(x.split('/')[0] for x in assets if x not in baseline)), 'seconds': round(time.time()-t,1)}
    save(args.work/'inventory.json', dict(assets)); save(args.work/'archives.json', archives); save(args.work/'inventory-summary.json', summary)
    print(json.dumps(summary, indent=2), flush=True)

def verify_bytes(name, data):
    ext = Path(name).suffix.lower()
    if not data: raise ValueError('empty asset')
    if ext in IMAGES:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as im: im.verify()
        with Image.open(io.BytesIO(data)) as im: im.load()
    elif ext == '.csv':
        text = data.decode('utf-8-sig')
        if '\x00' in text or not any(c.isdigit() for c in text): raise ValueError('invalid CSV data')
        # Animation CSVs are numeric. This catches encrypted but accidentally decodable data.
        if '_cgg_' in name or '_cgs_' in name:
            if re.search(r'[^\d\s,\.\-+eE]', text): raise ValueError('non-numeric animation CSV')
    elif ext == '.ssbp' and not data.startswith(b'SSPB'): raise ValueError('invalid SSBP signature')
    elif ext == '.bmb' and not data.startswith(b'IBMB'): raise ValueError('invalid BMB signature')

def extract_archive(args, source, selected):
    """Return a decrypted cache directory, isolated per source archive."""
    key = hashlib.sha256(source.encode()).hexdigest()[:20]
    job = args.work/'extracted'/key
    marker = job/'complete.json'
    if marker.exists() and all((job/'cpk'/name).exists() for name in selected): return job/'cpk'
    job.mkdir(parents=True, exist_ok=True)
    target = job/'cpk'; target.mkdir(exist_ok=True)
    src = args.dump/source
    if source.startswith('FFBE_JP/'):
        for p in args.extractor.iterdir():
            if p.suffix.lower() in ('.exe', '.dll') and not (job/p.name).exists(): shutil.copy2(p, job/p.name)
        staged = target/src.name
        if not staged.exists(): shutil.copy2(src, staged)
        result = subprocess.run([str(job/'DataExtractor.exe')], cwd=job, capture_output=True, timeout=600)
        if result.returncode: raise RuntimeError(f'DataExtractor exit {result.returncode}: {result.stderr[-500:]!r}')
        # Only the private staged copy is removed, never the source dump.
        staged.unlink()
    else:
        c = Cpk(src)
        try:
            for e in c.entries:
                if Path(e['name']).suffix.lower() not in VISUAL: continue
                name = safe_name(e['name'])
                out = target/name
                if not out.exists(): out.write_bytes(c.read(e))
        finally: c.f.close()
    missing = [x for x in selected if not (target/x).exists()]
    if missing: raise ValueError(f'extractor omitted {len(missing)} files: {missing[:3]}')
    save(marker, {'source': source})
    return target

def recover(args):
    assets = json.loads((args.work/'inventory.json').read_text())
    baseline = json.loads((args.work/'baseline.json').read_text())
    manifest_path = args.work/'recovered.json'
    recovered = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    errors = []; grouped = collections.defaultdict(list)
    for dest, candidates in assets.items():
        if dest in baseline or dest in recovered: continue
        if args.existing_folders_only and dest.startswith('additional/'): continue
        priority = Path(dest).name.lower().startswith(PRIORITY)
        if args.phase == 'priority' and not priority: continue
        if args.phase == 'additional' and priority: continue
        candidate = candidates[0]
        grouped[(candidate['kind'], candidate['source'])].append((dest, candidate))
    print(f'{args.phase}: {sum(map(len,grouped.values()))} new files from {len(grouped)} sources', flush=True)
    def job(key, items):
        kind, source = key
        cache = extract_archive(args, source, [Path(d).name for d,c in items]) if kind == 'cpk' else None
        results=[]; failures=[]
        for dest, candidate in items:
            try:
                p = cache/Path(dest).name if cache else args.dump/source
                data = p.read_bytes()
                extraction = None
                try:
                    verify_bytes(Path(dest).name, data)
                except Exception:
                    if kind != 'cpk': raise
                    # Some JP CPKs mix plaintext legacy files with encrypted members.
                    # DataExtractor applies decryption archive-wide; recover untouched
                    # members directly only when the original bytes validate.
                    c = Cpk(args.dump/source)
                    try: original = c.read(candidate['entry'])
                    finally: c.f.close()
                    verify_bytes(Path(dest).name, original)
                    data = original
                    extraction = 'plaintext member in otherwise encrypted CPK'
                if len(data) >= 100*1024*1024: raise ValueError('exceeds GitHub single-file limit; retained in source dump')
                target = args.repo/dest
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    if target.read_bytes()!=data: raise ValueError('destination exists with different content; preserved')
                else:
                    with target.open('xb') as f: f.write(data)
                record = {'source': source, 'member': candidate.get('entry',{}).get('name'), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
                if extraction: record['extraction'] = extraction
                results.append((dest, record))
            except Exception as e: failures.append({'destination':dest,'source':source,'error':str(e)})
        return results,failures
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(job,k,v):k for k,v in grouped.items()}
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            try:
                results, failures=f.result(); recovered.update(results); errors.extend(failures)
            except Exception as e: errors.append({'source':futures[f][1],'error':str(e)})
            if i%20==0 or i==len(futures):
                save(manifest_path,recovered);save(args.work/f'errors-{args.phase}.json',errors)
                print(f'{i}/{len(futures)} sources; {len(recovered)} recovered files; {len(errors)} errors',flush=True)
    save(manifest_path,recovered);save(args.work/f'errors-{args.phase}.json',errors)
    print(json.dumps({'files':len(recovered),'bytes':sum(x['bytes'] for x in recovered.values()),'by_folder':dict(collections.Counter(x.split('/')[0] for x in recovered)),'errors':errors[:10]},indent=2))
    if errors: raise SystemExit(1)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['inventory','recover'])
    p.add_argument('--dump',type=Path,required=True)
    p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--extractor',type=Path)
    p.add_argument('--phase',choices=['priority','additional','all'],default='priority')
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--existing-folders-only',action='store_true',help='Skip additional/ assets outside the original categories')
    args=p.parse_args()
    args.dump=args.dump.resolve();args.repo=args.repo.resolve();args.work=args.work.resolve()
    if args.extractor:args.extractor=args.extractor.resolve()
    (inventory if args.command=='inventory' else recover)(args)

if __name__=='__main__': main()
