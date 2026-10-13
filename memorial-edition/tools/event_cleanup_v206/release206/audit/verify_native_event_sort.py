"""Pin the actual ascending event menu comparator and its parser/call site."""
from pathlib import Path
import datetime,hashlib,json,struct,zipfile
from native_event_sort import elf64,memory,signed
ROOT=Path(__file__).resolve().parents[1]
APK=Path('S:/FFBE JP Data Export/build/v205-patch5-events/staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk')
PIN='e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'
def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    with APK.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==PIN
    with zipfile.ZipFile(APK) as z:blob=z.read('lib/arm64-v8a/libgame.so')
    original=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/source/production-libgame.so').read_bytes()
    assert blob==original
    headers,sections,symbols=elf64(blob);by={s['name']:s for s in symbols}
    comparator=by['_ZN18PlaybackChapterMst13sortDispOrderEPKvS1_']
    instructions=memory(blob,headers,comparator['address'],comparator['size'])
    words=list(struct.unpack('<5I',instructions))
    assert words==[0xb9402808,0xb9402829,0x6b09011f,0x1a9fa7e0,0xd65f03c0]
    getter=by['_ZNK18PlaybackChapterMst12getDispOrderEv']
    assert memory(blob,headers,getter['address'],getter['size'])==struct.pack('<II',0xb9402800,0xd65f03c0)
    parser=by['_ZN26PlaybackChapterMstResponse9readParamEiiPKcS1_b']
    code=memory(blob,headers,parser['address'],parser['size'])
    # ADRP x1; ADD x1,x1,#imm before strcmp at parser+0x80.
    adrp,add=struct.unpack_from('<II',code,0x74)
    assert adrp==0xb0004001 and add==0x9126dc21
    page=((parser['address']+0x74)&~4095)+(signed(((adrp>>5&0x7ffff)<<2)|(adrp>>29&3),21)<<12)
    fieldaddr=page+((add>>10&4095)<<(12 if add&(1<<22) else 0))
    field=memory(blob,headers,fieldaddr,9)
    assert field==b'Z0EN6jSh\0'
    assert struct.unpack_from('<I',code,0x94)[0]==0xb9002ae0 # str w0,[x23,#0x28]
    setup=by['_ZN20PlaybackChapterScene16setupChapterListEv']
    code=memory(blob,headers,setup['address'],setup['size'])
    adrp=struct.unpack_from('<I',code,0x54)[0]
    load=struct.unpack_from('<I',code,0x68)[0]
    assert adrp==0xd0009989 and load==0xf941e929
    page=((setup['address']+0x54)&~4095)+(signed(((adrp>>5&0x7ffff)<<2)|(adrp>>29&3),21)<<12)
    gotaddr=page+((load>>10&4095)*8)
    relocation=None
    for h in headers:
        if h[1]!=4:continue
        for p in range(h[4],h[4]+h[5],h[9]):
            address,info,_=struct.unpack_from('<QQq',blob,p)
            if address==gotaddr:relocation=symbols[info>>32]['name']
    assert relocation==comparator['name']
    call=struct.unpack_from('<I',code,0x74)[0]
    target=setup['address']+0x74+(signed(call&0x3ffffff,26)<<2)
    assert call&0xfc000000==0x94000000
    # This static call was independently resolved from the PLT in the symbol audit.
    audit=json.loads((ROOT/'audit/NATIVE_EVENT_SORT_SYMBOLS.json').read_bytes())
    setupcalls=next(s['calls'] for s in audit if s['name']==setup['name'])
    assert any(c['offset']=='0x74' and '__sort' in c['target'] for c in setupcalls)
    assert any(c['target']=='_ZN22PlaybackChapterMstList19getListFromSeasonIdEi' for c in setupcalls)
    report={'schema':'ffbe-native-event-menu-order-v1','passed':True,'baseline205_apk':str(APK),
            'baseline205_apk_sha256':PIN,'native_member':'lib/arm64-v8a/libgame.so','native_sha256':sha(blob),
            'comparator':{'symbol':comparator['name'],'address':hex(comparator['address']),
                          'bytes_sha256':sha(instructions),'words':[hex(w) for w in words],
                          'decoded':['ldr w8, [x0, #0x28]','ldr w9, [x1, #0x28]','cmp w8, w9','cset w0, lt','ret'],
                          'direction':'signed integer ascending','field_offset':'0x28'},
            'parser':{'symbol':parser['name'],'field':'Z0EN6jSh','store_offset':'0x94','object_field_offset':'0x28'},
            'menu':{'symbol':setup['name'],'season_filter_call':'PlaybackChapterMstList::getListFromSeasonId',
                    'sort_call_offset':'0x74','sort_callback_GOT_address':hex(gotaddr),'sort_callback_symbol':relocation},
            'recommendation':{'revival_book_ids':['7074','7075'],'fields_to_change':['Z0EN6jSh'],
                              'new_values':'maximum order among all other retained/moved season70 books plus1/plus2',
                              'physical_table_order_preserved':True,'runtime_hooks_needed':False},
            'party_classifier':{'policy':'explicit SIDE_STORY_PARTIES.books membership by scene book ID',
                                'category_dependent':False,'changes_needed':False},
            'runtime_verified':False,'device_actions':False,'source_sha256':sha(Path(__file__).read_bytes()),
            'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (ROOT/'audit/NATIVE_EVENT_MENU_ORDER.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'direction':'signed ascending','field':'Z0EN6jSh','runtime_hooks_needed':False}))

if __name__=='__main__':main()
