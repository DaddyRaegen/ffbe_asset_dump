"""Qualify exactly the build206 download-counter formatting fix and version207."""
from pathlib import Path
import argparse, datetime, hashlib, json, re, struct, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE_APK_SHA = '345967a814abb6ab645f280dd3c2b0195c5f395dd3e18e1227ef78515e5bb00d'
BASELINE_SCRIPT_SHA = '54072bcb90afcde6a7a3b16b60ebd55a51162b1ed267d126ae94460b6a8bfac5'
BASELINE_DEX_SHA = '408b8332dfbe4aaccb239ca0de3e3a71a7dc02e54f84135c321eeca2b58cc558'
BASELINE_CATALOG_SHA = '963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a'
BASELINE_SIDE_SHA = '0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14'
SIGNER_SHA = '21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
ALLOWED = frozenset(('AndroidManifest.xml', 'assets/frida_script.js'))
DEFAULT_BASELINE = ROOT.parent / 'v206-event-cleanup/staged_build/dist/FFBE-Memorial-EN-Event-Cleanup-v206.apk'
BUILD_TOOLS = Path('T:/Projects/FFBE Patch/graphics-localization/2026-09-19/apk-build/tools/android-16')
INSERT_BEFORE = '  function punctuation(text) {\r\n'
INSERT_AFTER = (
    INSERT_BEFORE + '    // The native downloader supplies compact grouped MB/MB counters.\r\n'
    '    if (/^(?:[0-9]+|[0-9]{1,3}(?:[,，][ \\t\\u00a0\\u3000]*[0-9]{3})+)(?:\\.[0-9]{3})?MB\\/'
    '(?:[0-9]+|[0-9]{1,3}(?:[,，][ \\t\\u00a0\\u3000]*[0-9]{3})+)(?:\\.[0-9]{3})?MB$(?![\\s\\S])/.test(text))\r\n'
    "      return text.replace(/[,，][ \\t\\u00a0\\u3000]*/g, ',');\r\n")

class GuardError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise GuardError(message)

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def file_sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def signature(name):
    return bool(re.fullmatch(r'META-INF/(?:MANIFEST[.]MF|[^/]+[.](?:SF|RSA|DSA|EC))', name, re.I))

def compressed_blob(z, info):
    with Path(z.filename).open('rb') as f:
        f.seek(info.header_offset)
        header = f.read(30)
        require(header[:4] == b'PK\x03\x04', 'Invalid ZIP local header')
        name_len, extra_len = struct.unpack_from('<HH', header, 26)
        f.seek(name_len + extra_len, 1)
        result = f.read(info.compress_size)
        require(len(result) == info.compress_size, 'Truncated ZIP data')
        return result

def compare_members(baseline, candidate, asset_count=170, member_count=312):
    with zipfile.ZipFile(baseline) as old, zipfile.ZipFile(candidate) as new:
        require(old.testzip() is None and new.testzip() is None, 'ZIP CRC failure')
        for z in (old, new):
            require(len(z.namelist()) == len(set(z.namelist())), 'Duplicate APK ZIP member')
        require(old.namelist() == new.namelist(), 'APK full member names/order changed, including signing metadata')
        before = {n for n in old.namelist() if not signature(n)}
        after = {n for n in new.namelist() if not signature(n)}
        require(before == after, 'APK member addition/removal')
        require(len(before) == member_count, 'Unexpected APK nonsigning member count')
        require(len([n for n in before if n.startswith('assets/') and not n.endswith('/')]) == asset_count,
                'Unexpected asset member count')
        changed, preserved, natives = [], [], []
        for name in sorted(before):
            a, b = old.getinfo(name), new.getinfo(name)
            require(a.compress_type == b.compress_type, 'Compression method changed: ' + name)
            ab, bb = old.read(name), new.read(name)
            if ab != bb:
                require(name in ALLOWED, 'Unrequested member changed: ' + name)
                changed.append({'path': name, 'before_sha256': sha(ab), 'after_sha256': sha(bb),
                                'before_bytes': len(ab), 'after_bytes': len(bb)})
            else:
                require(compressed_blob(old, a) == compressed_blob(new, b), 'Unchanged member recompressed: ' + name)
                preserved.append(name)
            if name.endswith('.so'):
                require(ab == bb, 'Native library changed: ' + name)
                natives.append({'path': name, 'bytes': len(ab), 'sha256': sha(ab)})
        require({r['path'] for r in changed} == ALLOWED, 'Expected exactly two requested member changes')
        return {'changed_members': changed, 'unchanged_member_count': len(preserved),
                'raw_compressed_preserved_members': preserved, 'asset_files': asset_count,
                'native_libraries': natives, 'new_or_removed_members': 0}

def pool_strings(chunk):
    header = struct.unpack_from('<H', chunk, 2)[0]
    count, _, flags, start, _ = struct.unpack_from('<5I', chunk, 8)
    result = []
    for i in range(count):
        pos = start + struct.unpack_from('<I', chunk, header + 4*i)[0]
        if flags & 0x100:
            def length(p):
                v = chunk[p]
                return (((v & 127) << 8) | chunk[p+1], p+2) if v & 128 else (v, p+1)
            _, pos = length(pos)
            n, pos = length(pos)
            result.append(chunk[pos:pos+n].decode('utf-8'))
        else:
            n = struct.unpack_from('<H', chunk, pos)[0]
            pos += 2
            if n & 0x8000:
                n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', chunk, pos)[0]
                pos += 2
            result.append(chunk[pos:pos+n*2].decode('utf-16-le'))
    return result

def expected_manifest(original):
    result = bytearray(original)
    offset, names, positions = 8, None, []
    require(len(result) >= 8 and struct.unpack_from('<I', result, 4)[0] == len(result), 'Invalid AXML size')
    while offset < len(result):
        kind, header, size = struct.unpack_from('<HHI', result, offset)
        require(size >= header >= 8 and offset + size <= len(result), 'Invalid AXML chunk')
        if kind == 1:
            names = pool_strings(result[offset:offset+size])
        if kind == 0x102:
            require(names is not None, 'Missing AXML string pool')
            tag = struct.unpack_from('<I', result, offset+header+4)[0]
            if names[tag] == 'manifest':
                start, width, count = struct.unpack_from('<HHH', result, offset+header+8)
                for i in range(count):
                    p = offset+header+start+i*width
                    name = struct.unpack_from('<I', result, p+4)[0]
                    if names[name] == 'versionCode':
                        require(result[p+15] == 16 and struct.unpack_from('<I', result, p+16)[0] == 206,
                                'Expected typed versionCode206')
                        struct.pack_into('<I', result, p+16, 207)
                        positions.append(p+16)
        offset += size
    require(offset == len(result) and len(positions) == 1, 'Ambiguous versionCode')
    return bytes(result), {'value_offset': positions[0], 'before': 206, 'after': 207,
                           'typed_four_byte_value_only': True}

def expected_script(original, plan):
    require(sha(original) == BASELINE_SCRIPT_SHA, 'Unqualified baseline script')
    require(plan['schema'] == 'ffbe-download-spacing-plan-v1' and
            plan['scope'] == 'native-download-screen-comma-spacing-only', 'Unrecognized spacing plan')
    require(plan['baseline_apk_sha256'] == BASELINE_APK_SHA and
            plan['baseline_script_sha256'] == BASELINE_SCRIPT_SHA and
            plan['baseline_version'] == 206 and plan['candidate_version'] == 207, 'Plan baseline/version differs')
    expected_ops = [{'before': INSERT_BEFORE, 'after': INSERT_AFTER, 'count': 1}]
    require(plan['operations'] == expected_ops, 'Plan widens the approved finite insertion')
    before, after = b'const PATCH_VERSION = 206;', b'const PATCH_VERSION = 207;'
    require(original.count(before) == 1, 'Ambiguous updater counter')
    result = original.replace(before, after)
    target = INSERT_BEFORE.encode('utf-8')
    require(result.count(target) == 1, 'Ambiguous punctuation helper')
    result = result.replace(target, INSERT_AFTER.encode('utf-8'))
    require(sha(result) == plan['candidate_script_sha256'], 'Plan candidate hash differs')
    return result

def compare_script(original, candidate, plan):
    require(candidate == expected_script(original, plan), 'Script differs beyond the finite spacing/version operations')
    return {'counter_before': 206, 'counter_after': 207, 'finite_insertions': 1,
            'expected_js_delta_passed': True, 'other_display_rules_and_all_hooks_preserved': True,
            'routing_party_lifecycle_movie_startup_unchanged': True}

def run_tool(args, log):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, encoding='utf-8',
                            errors='replace', timeout=600)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(result.stdout + result.stderr, encoding='utf-8')
    require(result.returncode == 0, 'Qualification tool failed; see ' + str(log))
    return result.stdout + result.stderr

def qualify(args):
    require(file_sha(args.baseline_apk) == BASELINE_APK_SHA, 'Baseline is not qualified build206')
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8-sig'))
    result = compare_members(args.baseline_apk, args.apk)
    work = ROOT / 'audit/signed_spacing_tools'
    with zipfile.ZipFile(args.baseline_apk) as old, zipfile.ZipFile(args.apk) as new:
        expected, receipt = expected_manifest(old.read('AndroidManifest.xml'))
        require(new.read('AndroidManifest.xml') == expected, 'Binary manifest changed beyond versionCode')
        result['manifest_delta'] = receipt
        original, candidate = old.read('assets/frida_script.js'), new.read('assets/frida_script.js')
        result['script_delta'] = compare_script(original, candidate, plan)
        for member, pin, field in [('classes.dex', BASELINE_DEX_SHA, 'runtime_dex_sha256'),
                ('assets/content_delivery.tsv', BASELINE_CATALOG_SHA, 'content_catalog_sha256'),
                ('assets/side_stories/manifest.tsv', BASELINE_SIDE_SHA, 'side_manifest_sha256')]:
            require(new.read(member) == old.read(member) and sha(new.read(member)) == pin, 'Frozen runtime/data pin differs: ' + member)
            result[field] = pin
        work.mkdir(parents=True, exist_ok=True)
        old_path, new_path = work / 'baseline_script.js', work / 'candidate_script.js'
        old_path.write_bytes(original)
        new_path.write_bytes(candidate)
    host_path = ROOT / 'audit/DOWNLOAD_SPACING_HOST_TESTS.json'
    fixtures = Path(__file__).with_name('formatter_fixtures.mjs')
    run_tool(['node', '--check', new_path], work / 'js_syntax.txt')
    run_tool(['node', fixtures, old_path, new_path, host_path], work / 'formatter_tests.txt')
    host = json.loads(host_path.read_text())
    require(host['passed'] and host['baseline_script_sha256'] == BASELINE_SCRIPT_SHA and
            host['candidate_script_sha256'] == plan['candidate_script_sha256'], 'Host proof does not bind actual APK scripts')
    proof_path = ROOT/'audit/NATIVE_DOWNLOAD_COUNTER_PROOF.json'
    proof = json.loads(proof_path.read_text())
    require(proof['passed'] and proof['baseline_apk_sha256'] == BASELINE_APK_SHA and
            proof['proof_source_sha256'] == file_sha(Path(__file__).with_name('native_counter_proof.py')),
            'Native formatter proof is absent, stale or not bound to build206')
    require(len(result['native_libraries']) == 8, 'Unexpected native library inventory')
    signed = run_tool(['java', '-jar', BUILD_TOOLS/'lib/apksigner.jar', 'verify', '--verbose', '--print-certs', args.apk], work/'signature.txt')
    require('Signer #1 certificate SHA-256 digest: ' + SIGNER_SHA in signed and
            'Verified using v2 scheme (APK Signature Scheme v2): true' in signed, 'Signer/signature differs')
    badging = run_tool([BUILD_TOOLS/'aapt2.exe', 'dump', 'badging', args.apk], work/'package.txt')
    require("package: name='com.square_enix.ffbejpn' versionCode='207' versionName='11.1.1'" in badging,
            'Package/version differs')
    run_tool([BUILD_TOOLS/'zipalign.exe', '-c', '-P', '16', '-v', '4', args.apk], work/'alignment.txt')
    result.update({'schema': 'ffbe-download-spacing-qualification-v1', 'passed': True,
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'apk_sha256': file_sha(args.apk), 'apk_bytes': Path(args.apk).stat().st_size,
        'versionCode': 207, 'baseline_apk_sha256': BASELINE_APK_SHA, 'expected_js_delta_passed': True,
        'spacing_plan_sha256': file_sha(args.plan), 'signer_sha256': SIGNER_SHA,
        'formatter_host_report': str(host_path), 'formatter_host_report_sha256': file_sha(host_path),
        'formatter_host_assertions': host['assertions'], 'guard_sha256': file_sha(__file__),
        'native_format_proof_sha256': file_sha(proof_path), 'native_format_proof': str(proof_path),
        'formatter_fixture_sha256': file_sha(fixtures), 'all10950_classes_preserved': True,
        'unchanged_asset_files': 169, 'changed_asset_files': 1,
        'underlying_downloader_and_external_assets_unchanged': True, 'phone_rendering_tested': False,
        'qualification_tools': {str(p): file_sha(p) for p in [BUILD_TOOLS/'aapt2.exe',
            BUILD_TOOLS/'zipalign.exe', BUILD_TOOLS/'lib/apksigner.jar']}})
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apk', required=True)
    parser.add_argument('--baseline-apk', default=str(DEFAULT_BASELINE))
    parser.add_argument('--plan', default=str(ROOT/'audit/DOWNLOAD_SPACING_PLAN.json'))
    parser.add_argument('--output', default=str(ROOT/'staged_build/SIGNED_SPACING_QUALIFICATION.json'))
    args = parser.parse_args()
    try:
        report = qualify(args)
    except Exception as exc:
        report = {'schema': 'ffbe-download-spacing-qualification-v1', 'passed': False,
                  'error': str(exc), 'guard_sha256': file_sha(__file__)}
        if Path(args.apk).is_file():
            report.update({'apk_sha256': file_sha(args.apk), 'apk_bytes': Path(args.apk).stat().st_size})
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ['passed', 'apk_sha256', 'apk_bytes', 'error'] if k in report}))
    raise SystemExit(0 if report['passed'] else 1)
