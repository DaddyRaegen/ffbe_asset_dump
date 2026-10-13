from pathlib import Path
import json,hashlib,zipfile,struct,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(r'S:\FFBE JP Data Export\build\v206-event-cleanup')
apk=ROOT.parent/'v205-patch5-events/staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk'
with zipfile.ZipFile(apk) as z:data=z.read('lib/arm64-v8a/libgame.so')
digest=hashlib.sha256(data).hexdigest()
old=Path(r'C:\Users\Raegen\Documents\Codex\2026-10-02\task-2\integration_work\native_delivery_correction\banner_audit\native_banner_load_trace.json')
trace=json.loads(old.read_text(encoding='utf-8'));assert digest==trace['lib_sha256']
phoff=struct.unpack_from('<Q',data,32)[0];entsize,count=struct.unpack_from('<HH',data,54)
segments=[struct.unpack_from('<IIQQQQQQ',data,phoff+i*entsize) for i in range(count)]
def raw(addr,size):
 p=next(p for p in segments if p[0]==1 and p[3]<=addr and addr+size<=p[3]+p[5]);offset=p[2]+addr-p[3];return data[offset:offset+size]
start,end=0x1ade300,0x1ade420
instructions=[{'address':hex(start+i),'word':hex(struct.unpack_from('<I',raw(start+i,4))[0])} for i in range(0,end-start,4)]
layout=next(t for t in trace['traces'] if t['name']=='_ZN20PlaybackChapterScene9setLayoutEv')
# Decode only a narrow, explicitly checked AArch64 MOV alias (ORR rd,xzr,rm).
# These instructions bind the two creation results into button arguments.
expected_moves={0x1ade39c:(25,0),0x1ade3a4:(1,24),0x1ade3d4:(26,0),0x1ade400:(3,25),0x1ade404:(4,31),0x1ade408:(5,26),0x1ade40c:(6,31)}
move_proof=[]
for pc,(rd,rm) in expected_moves.items():
 word=struct.unpack_from('<I',raw(pc,4))[0]
 assert word==0xaa0003e0+(rm<<16)+rd,(hex(pc),hex(word),rd,rm)
 move_proof.append({'pc':hex(pc),'word':hex(word),'instruction':f'mov x{rd}, '+('xzr' if rm==31 else f'x{rm}')})
lit=next(v for v in layout['inferred_ADRP_ADD_or_ADR_literals'] if v['text']=='spd_bn_press.png')
assert raw(int(lit['address'],16),17)==b'spd_bn_press.png\x00'
calls={int(c['pc'],16):c for c in layout['direct_BL_calls']}
assert int(calls[0x1ade398]['target'],16)==0x10d6260
assert int(calls[0x1ade3cc]['target'],16)==0x10fc310
assert int(calls[0x1ade414]['target'],16)==0x10c9fa0
report={'schema':'ffbe-v206-native-banner-button-source-proof-v1','lib_sha256':digest,'apk':str(apk),'prior_trace_path':str(old),'prior_trace_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'exact_native_bytes_match_prior_trace':True,'layout_literals':layout['inferred_ADRP_ADD_or_ADR_literals'],'relevant_direct_calls':[r for r in layout['direct_BL_calls'] if start<=int(r['pc'],16)<end],'instructions_raw_words':instructions,'checked_mov_instructions':move_proof,'static_interpretation':'PlaybackChapterScene obtains one title image via IconMstList::getFileName and createGameSpriteByImage, saves it in x25, creates the shared spd_bn_press.png sprite frame and saves it in x26. The button call receives x3=title sprite, x4=null, x5=shared press sprite, x6=null. The native layout does not request a second per-title selected filename in this path. Existing special atlas supplies the shared press frame.','per_title_paired_selected_image_required_by_this_path':False,'limits':'Static source evidence on exact signed205 ARM64 bytes; no device/rendering/runtime guarantee. Other scenes are outside this narrow check. _last event banners are last-day variants and are not inferred to be selected borders.','runtime_execution':False}
output=ROOT/'audit/NATIVE_BANNER_BUTTON_PROOF.json';output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
