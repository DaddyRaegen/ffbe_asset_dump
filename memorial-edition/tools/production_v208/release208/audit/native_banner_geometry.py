"""Bounded static evidence for actual chapter image sizing; no runtime changes."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, plistlib, struct, sys, zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/source/production-libgame.so')
HELPER = ROOT.parent/'v206-event-cleanup/audit/native_event_sort.py'
sha = lambda b:hashlib.sha256(b).hexdigest()

def prove():
    assert sha(HELPER.read_bytes())=='0233130f603a0465309b6e260c5b020f87f9f171a2d53366ee3cdd033268c90b'
    spec=importlib.util.spec_from_file_location('sealed_elf_reader',HELPER)
    elf=importlib.util.module_from_spec(spec);spec.loader.exec_module(elf)
    blob=SOURCE.read_bytes()
    assert sha(blob)=='6c7e501c98939581528df3d712ff1f58afcfd392160f1e71ef1f903d49926b77'
    headers,sections,symbols=elf.elf64(blob);index={s['name']:s for s in symbols}
    scene='_ZN20PlaybackChapterScene9setLayoutEv'
    image='_ZN11LayoutUtils23createGameSpriteByImageEPN7cocos2d15SpriteBatchNodeEffRKNS0_4Vec2E'
    header_image='_ZN11LayoutUtils23createGameSpriteByImageEPKciffffiRKN7cocos2d4Vec2E'
    selected=[scene,image,header_image,'_ZN9GameScene30createSpriteButtonForBatchNodeEiffiP10GameSpriteS1_S1_S1_t',
              '_ZN12SpriteButton32initForChangeSpriteWithBatchNodeEiffiP10GameSpriteS1_S1_S1_']
    functions=[]
    for name in selected:
        symbol=index[name];raw=elf.memory(blob,headers,symbol['address'],symbol['size'])
        functions.append({'name':name,'address':hex(symbol['address']),'bytes':symbol['size'],'sha256':sha(raw),
            'calls':elf.calls(blob,headers,sections,symbols,symbol)})
    calls={int(c['offset'],16):c['target'] for c in functions[0]['calls']}
    assert calls[0x120]=='_ZN11IconMstList11getFileNameEi'
    assert calls[0x190]==image and calls[0x5e8]==header_image
    assert calls[0x20c]=='_ZN9GameScene30createSpriteButtonForBatchNodeEiffiP10GameSpriteS1_S1_S1_t'
    assert any(c['offset']=='0x44' and c['target']=='_ZNK7cocos2d9Texture2D14getContentSizeEv' for c in functions[1]['calls'])
    assert any(c['offset']=='0x58' and c['target']=='_ZN7cocos2d4RectC1Effff' for c in functions[1]['calls'])
    assert any(c['offset']=='0x70' and c['target']=='_ZN10GameSprite4initEPN7cocos2d9Texture2DERKNS0_4RectE' for c in functions[1]['calls'])
    image_raw=elf.memory(blob,headers,index[image]['address'],index[image]['size'])
    assert struct.unpack_from('<I',image_raw,0x48)[0]==0x2d420fe2
    assert struct.unpack_from('<I',image_raw,0x50)[0]==0x1e2703e0 and struct.unpack_from('<I',image_raw,0x54)[0]==0x1e2703e1
    apk207=ROOT.parent/'v207-download-spacing/staged_build/dist/FFBE-Memorial-EN-Download-Spacing-v207.apk'
    p5=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk')
    sys.path.insert(0,'T:/Projects/FFBE Patch/story-ports/side-stories/scripts')
    from cpk_convert import read_cpk
    from common import crilayla
    with zipfile.ZipFile(apk207) as current,zipfile.ZipFile(p5) as original:
        layout=current.read('assets/cpk/layout.cpk');resources=current.read('assets/cpk/resources.cpk')
        assert layout==original.read('assets/cpk/layout.cpk') and resources==original.read('assets/cpk/resources.cpk')
    key='layout/playback/layout_playback_chapter_frame_list.csv'
    csv=read_cpk(layout)[4][key]
    assert csv==b'0,0,640,240,0,playback_chapter_frame_list,spd_bn_top_dummy.png,\r\n'
    atlas_key='image/ui/special/special.plist'
    plist=read_cpk(resources)[4][atlas_key]
    if plist.startswith(b'CRILAYLA'):plist=crilayla(plist)
    pressed=plistlib.loads(plist)['frames']['spd_bn_press.png']
    assert pressed['spriteSize']=='{640,240}' and pressed['spriteSourceSize']=='{640,240}'
    assert pressed['textureRect']=='{{1280,432},{640,240}}' and pressed['spriteOffset']=='{0,0}'
    return {'schema':'ffbe-native208-banner-geometry-v1','passed':True,'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseline_apk_sha256':'d9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e',
        'native_sha256':sha(blob),'functions':functions,
        'book_image_path':{'scene_offset':'0x190','parameters':['SpriteBatchNode texture','x','y','anchor'],
            'width_height_parameters':False,'texture_size_rect_used':True,
            'evidence':['+0x44 Texture2D.getContentSize returns dimensions',
                '+0x48 ldp s2,s3,[sp,#16] loads those dimensions for Rect',
                '+0x50/+0x54 fmov s0/s1,wzr supplies Rect origin0,0',
                '+0x58 Rect(0,0,textureContentWidth,textureContentHeight)',
                '+0x70 GameSprite.init(texture,thatRect)',
                'Remaining virtual calls set anchor and x/y position and add to batch; no target width/height parameters']},
        'season_selector_header_path':{'scene_offset':'0x5e8','layout_key':'playback_chapter_season_select_frame',
            'explicit_width_height_parameters':True,'applies_to_book_banners':False},
        'shared_pressed_overlay_literal':{'address':'0x258c9a3','text':'spd_bn_press.png'},
        'layout_spacing_key':'playback_chapter_frame_list',
        'literal_Patch5_layout_bytes_preserved':True,
        'bundled_layout_geometry':{'APK_member':'assets/cpk/layout.cpk','APK_member_sha256':sha(layout),
            'CPK_member':key,'CPK_member_sha256':sha(csv),'CSV':csv.decode(),
            'slot_x':0,'slot_y':0,'slot_width':640,'slot_height':240},
        'bundled_pressed_frame_geometry':{'APK_member':'assets/cpk/resources.cpk','APK_member_sha256':sha(resources),
            'CPK_member':atlas_key,'CPK_member_sha256':sha(plist),'sprite':'spd_bn_press.png','frame':pressed},
        'no_book_image_autofit_to_fixed_layout_size_observed':True,
        'does_not_establish_texture_content_scale_factor':True,
        'existing_standard_book_slot_canvas':[640,240],
        'universal_resize_of_standard640x240_art_to600x120_is_not_supported':True,
        'generated_art_visual_size_may_require_internal_composition_changes_within640x240_canvas':True,
        'actual_final_size_decision_requires_existing_style_and_rendered_comparison':True,
        'device_actions':False,'native_modified':False,'proof_source_sha256':sha(Path(__file__).read_bytes())}

if __name__=='__main__':
    report=prove();target=ROOT/'audit/NATIVE_BANNER_GEOMETRY.json'
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'report':str(target),'sha256':sha(target.read_bytes())}))
