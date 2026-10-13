"""Read-only pinned ELF/actual-APK evidence for the narrow counter formatter."""
from pathlib import Path
import datetime, hashlib, importlib.util, json, struct, zipfile

ROOT = Path(__file__).resolve().parents[1]
APK206 = ROOT.parent/'v206-event-cleanup/staged_build/dist/FFBE-Memorial-EN-Event-Cleanup-v206.apk'
APK205 = ROOT.parent/'v205-patch5-events/staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk'
APK5 = Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk')
HELPER = ROOT.parent/'v206-event-cleanup/audit/native_event_sort.py'
SOURCE = Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/source/production-libgame.so')
sha = lambda b: hashlib.sha256(b).hexdigest()
def file_sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def prove():
    assert file_sha(HELPER) == '0233130f603a0465309b6e260c5b020f87f9f171a2d53366ee3cdd033268c90b'
    spec = importlib.util.spec_from_file_location('sealed_elf_reader', HELPER)
    elf = importlib.util.module_from_spec(spec); spec.loader.exec_module(elf)
    blob = SOURCE.read_bytes()
    assert sha(blob) == '6c7e501c98939581528df3d712ff1f58afcfd392160f1e71ef1f903d49926b77'
    pins = [
        (APK5, '534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'),
        (APK205, 'e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'),
        (APK206, '345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d')]
    archives = []
    for apk, pin in pins:
        assert file_sha(apk) == pin
        with zipfile.ZipFile(apk) as z:
            native = [(n, z.read(n)) for n in z.namelist() if n.endswith('/libgame.so')]
            native = [(n, b) for n, b in native if sha(b) == sha(blob)]
            assert len(native) == 1
            script = z.read('assets/frida_script.js')
            marker = b'// Apply English display rules after data parsing, never to CSV/script delimiters.'
            assert script.count(marker) == 1
            tail = script[script.index(marker):]
            assert sha(tail) == '4709fa04483026ca0d3941b0ad883073a991922db32cce85088f76b49873b164'
            closing = b'})(globalThis);'
            helper = tail[:tail.index(closing)+len(closing)]
            archives.append({'apk': str(apk), 'apk_sha256': pin, 'native_member': native[0][0],
                'native_sha256': sha(blob), 'script_sha256': sha(script),
                'original_display_helper_sha256': sha(helper), 'display_helper_bytes': len(helper),
                'display_section_and_following_tail_sha256': sha(tail)})
    assert len({a['original_display_helper_sha256'] for a in archives}) == 1
    headers, sections, symbols = elf.elf64(blob)
    by_name = {s['name']: s for s in symbols}
    selected = [
      ('_ZN11CommonUtils20adjustFileSizeStringEy', 0x15922f4, 800),
      ('_ZN11CommonUtils14getCommaNumberEi', 0x1592614, 808),
      ('_ZN20InitialDownloadScene17updateProgressBarEv', 0x19e5b30, 852),
      ('_ZN13DownloadScene11updateEventEv', 0x19e66dc, 940),
      ('_ZN15StringLabelList12changeStringERKNSt6__ndk112basic_stringIcNS0_11char_traitsIcEENS0_9allocatorIcEEEE', 0x14b4694, 604)]
    functions = []
    for name, address, size in selected:
        symbol = by_name[name]
        assert (symbol['address'], symbol['size']) == (address, size)
        raw = elf.memory(blob, headers, address, size)
        functions.append({'symbol': name, 'address': hex(address), 'bytes': size, 'sha256': sha(raw),
                          'calls': elf.calls(blob, headers, sections, symbols, symbol)})
    literals = [{'address': hex(a), 'bytes': elf.memory(blob, headers, a, n).hex(), 'text': text}
                for a, n, text in [(0x25d31e4, 1, ','), (0x25c0638, 2, 'MB'), (0x263bce6, 1, '/')]]
    assert [x['bytes'] for x in literals] == ['2c', '4d42', '2f']
    raw = elf.memory(blob, headers, 0x15922f4, 800)
    fixed = [(0x154, 0x321e0129, 'fixed floating-point flag'),
             (0x160, 0x52800069, 'precision3'), (0x164, 0x9a8903e9, 'precision0 only for zero'),
             (0x1cc, 0x52800023, 'comma insertion length1'), (0x1ec, 0x52800042, 'MB append length2')]
    words = []
    for offset, expected, meaning in fixed:
        actual = struct.unpack_from('<I', raw, offset)[0]
        assert actual == expected, (hex(offset), hex(actual), hex(expected))
        words.append({'function_offset': hex(offset), 'instruction': hex(actual), 'meaning': meaning})
    initial = functions[2]['calls']; counts = functions[3]['calls']; updated = functions[4]['calls']
    assert sum(c['target'] == selected[0][0] for c in initial) == 4
    assert any('IntToString' in c['target'] for c in counts)
    assert any(c['target'] == '_ZN9TagString5parseEv' for c in updated)
    return {'schema': 'ffbe-native-download-counter-proof-v1', 'passed': True,
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseline_apk_sha256': pins[2][1], 'archives': archives, 'functions': functions,
        'literal_evidence': literals, 'precision_instruction_evidence': words,
        'size_pair_format': 'sizeMB/sizeMB; each nonzero size uses exactly3 fractional digits; zero is 0MB',
        'approved_display_predicate_format': 'Standalone integer/grouped or three-fractional-digit uppercase MB/MB counters; no prefix/suffix, unit/slash spaces or linebreaks',
        'approved_whole_number_counter_variants_exceed_current_native_precision': True,
        'size_suffixes': ['MB'], 'separator_codepoints': ['U+002C', 'U+002F'],
        'native_separator_or_unit_spaces': 0, 'count_pair_format': 'IntToString(finished)/IntToString(total)',
        'percentage_is_separate_bitmap_label': True, 'updated_size_labels_call_existing_TagString_parse': True,
        'new_hooks_required': False, 'baseline_punctuation_replaces_ASCII_comma_with_UFF0C': True,
        'baseline_punctuation_already_consumes_after_comma_horizontal_spaces': ['U+0020','U+0009','U+00A0','U+3000'],
        'visual_cell_gap_is_static_inference': True, 'phone_rendering_tested': False,
        'elf_reader_sha256': file_sha(HELPER), 'proof_source_sha256': file_sha(Path(__file__))}

if __name__ == '__main__':
    result = prove()
    target = ROOT/'audit/NATIVE_DOWNLOAD_COUNTER_PROOF.json'
    target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'report': str(target), 'baseline_apk_sha256': result['baseline_apk_sha256']}))
