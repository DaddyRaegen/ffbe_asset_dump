"""Copy frozen check scripts, changing only input-root resolution and outputs."""
from pathlib import Path
import hashlib
import json

OUT=Path(__file__).resolve().parent
FROZEN=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction')

def digest(data):return hashlib.sha256(data).hexdigest()

def replace_once(text,before,after):
    assert text.count(before)==1,before
    return text.replace(before,after)

sources=[]
for relative in ['event_audit/verify_event_correction.py','banner_audit/verify_banner_correction.py','verify_asset_plan.py']:
    original=FROZEN/relative
    blob=original.read_bytes();text=blob.decode('utf-8')
    if relative.startswith('event_audit/'):
        text=replace_once(text,'HERE = Path(__file__).resolve().parent','HERE = Path('+repr(str(original.parent))+')')
        text=replace_once(text,"    builder.save('STATIC_REGRESSION_CHECKS.json', receipt)","    Path("+repr(str(OUT/'EVENT_STATIC_REGRESSION_CHECKS.json'))+").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')")
    elif relative.startswith('banner_audit/'):
        text=replace_once(text,'ROOT = Path(__file__).resolve().parent','ROOT = Path('+repr(str(original.parent))+')')
        text=replace_once(text,"(ROOT / 'INDEPENDENT_BANNER_VERIFICATION.json')","Path("+repr(str(OUT/'INDEPENDENT_BANNER_VERIFICATION.json'))+")")
    else:
        text=replace_once(text,'ROOT=Path(__file__).resolve().parent','ROOT=Path('+repr(str(original.parent))+')')
        text=replace_once(text,"(ROOT/'ASSET_PLAN_VALIDATION.json')","Path("+repr(str(OUT/'ASSET_PLAN_VALIDATION.json'))+")")
    adapted=OUT/'scripts'/original.name
    adapted.write_text(text,encoding='utf-8')
    sources.append({'frozen_original':str(original),'original_sha256':digest(blob),'adapted_script':str(adapted),'adapted_sha256':digest(adapted.read_bytes()),'only_changes':'Resolve frozen input root explicitly and write report in current audit directory'})
(OUT/'CHECK_SCRIPT_ADAPTATIONS.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'adapted_scripts':len(sources),'output':str(OUT)}))
