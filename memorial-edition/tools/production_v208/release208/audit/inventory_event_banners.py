"""Inventory actual207-equivalent event-menu icons; no payload or art edits."""
from pathlib import Path
import collections, datetime, hashlib, io, json, re, sys, unicodedata, zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT.parent/'v206-event-cleanup'
PAYLOAD205 = ROOT.parent/'v205-patch5-events/payload'
CODEC = Path('T:/Projects/FFBE Patch/story-ports/side-stories/scripts')
sys.path.insert(0, str(CODEC))
from common import rows_bytes, readable, crilayla
from cpk_convert import read_cpk

APK207 = ROOT.parent/'v207-download-spacing/staged_build/dist/FFBE-Memorial-EN-Download-Spacing-v207.apk'
APK_SHA = 'd9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
CATALOG_SHA = '963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a'
SIDE_SHA = '0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14'
BOOK = 'M9mwe2cu'; SEASON = '2ShgIRU8'; ICON = '0HUPxDf1'; NAME = 'G4L0YIB2'; FILE = 'qtkvrS60'; ORDER = 'Z0EN6jSh'
GENESIS_EXCEPTION = frozenset(('7032', '1000986', '1500002', '1500012'))
MAPPING = Path('C:/Users/Raegen/Documents/Codex/2026-10-02/task-2/integration_work/native_delivery_correction/banner_audit/book_banner_mapping.json')
MAPPING_SHA = 'de8872d83d163bdecf9eb201721df33d99dbb9c441b56c1b2a57b9af0ca97b6a'
SOURCE_INDEX = MAPPING.with_name('banner_cpk_member_index.json')
EXTRACTED_CACHE = MAPPING.parent/'private_extractor_jobs'
sha = lambda b: hashlib.sha256(b).hexdigest()
def file_sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def event_identity(title):
    """A conservative title relation, not an assertion of artwork correctness."""
    text = unicodedata.normalize('NFKC', title).strip().lower()
    text = re.sub(r'^\[(?:jp|gl|japan|global)\]\s*', '', text)
    text = re.sub(r'\s*\((?:revisited|reprint|revival|rerun|jp|gl|japan|global)\)', '', text)
    for _ in range(4):
        text = re.sub(r'\s*[-–—]\s*(?:battles?|story|additional battles?|event battles?|jp memories|memories)\s*$', '', text)
    return re.sub(r'[^\w]+', ' ', text).strip()

def inventory():
    assert file_sha(APK207) == APK_SHA
    with zipfile.ZipFile(APK207) as z:
        catalog = z.read('assets/content_delivery.tsv'); side = z.read('assets/side_stories/manifest.tsv')
    assert sha(catalog) == CATALOG_SHA and sha(side) == SIDE_SHA
    assert file_sha(MAPPING) == MAPPING_SHA
    mappings = {str(r['book_id']): r for r in json.loads(MAPPING.read_text(encoding='utf-8'))['books']}
    source_index = collections.defaultdict(list)
    for item in json.loads(SOURCE_INDEX.read_text(encoding='utf-8')):
        source_index[item['filename']].extend(item['sources'])
    parent = {}
    def root(value):
        parent.setdefault(value, value)
        if parent[value] != value: parent[value] = root(parent[value])
        return parent[value]
    def unite(a, b):
        a, b = root(a), root(b)
        parent[max(a,b)] = min(a,b)
    for mapped in mappings.values():
        for source in mapped['sources']:
            if source.get('regional_match_status') == 'supported_regional_counterpart':
                for other in source.get('regional_match_ids', []): unite(source['catalog_id'], other)
    descriptors = {}
    for line in catalog.decode().splitlines()[1:]:
        parts = line.split('\t'); assert len(parts) == 8
        descriptors[parts[0]] = {'sha256': parts[1], 'bytes': int(parts[2])}
    sources = {
        'books': (PREVIOUS/'payload/side_stories/Nm36woZx.dat', 'side_stories/Nm36woZx.dat', 'Nm36woZx'),
        'seasons': (PREVIOUS/'payload/side_stories/D2zaT7Ru.dat', 'side_stories/D2zaT7Ru.dat', 'D2zaT7Ru'),
        'icons': (PAYLOAD205/'side_stories/LM1APs6u.dat', 'side_stories/LM1APs6u.dat', 'LM1APs6u'),
        'archive': (PREVIOUS/'payload/side_stories/spdungeon9.cpk', 'side_stories/spdungeon9.cpk', None)}
    loaded, pins = {}, {}
    for role, (path, logical, stem) in sources.items():
        blob = path.read_bytes()
        assert len(blob) == descriptors[logical]['bytes'] and sha(blob) == descriptors[logical]['sha256']
        pins[role] = {'local_path': str(path), 'logical_path': logical, 'bytes': len(blob), 'sha256': sha(blob)}
        loaded[role] = rows_bytes(blob, stem) if stem else read_cpk(blob)
    books, icons = loaded['books'], loaded['icons']
    assert len(books) == 1004 and len({r[BOOK] for r in books}) == 1004
    assert len({r[ICON] for r in icons}) == len(icons)
    by_icon = {r[ICON]: r for r in icons}
    main_members = {by_icon[r[ICON]][FILE] for r in books if r[SEASON] not in ('70','71','92') and r[ICON] in by_icon}
    seasons = {r[SEASON]: readable(r).get('name', r.get(NAME,'')) for r in loaded['seasons']}
    raw_members = loaded['archive'][4]; toc = loaded['archive'][3]
    assert len(raw_members) == 561
    p5_archive = Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Content-Source.apk')
    with zipfile.ZipFile(p5_archive) as z: p5_cpk = z.read('assets/side_stories/spdungeon9.cpk')
    assert sha(p5_cpk) == '2f2be2a15887aebf90ed82395e2fcd6d62dad4aae1f84a9d6b07324626481dd6' and len(p5_cpk)==14913696
    p5_members = read_cpk(p5_cpk)[4]
    assert len(main_members) == 101 and all(raw_members[n] == p5_members[n] for n in main_members)
    toc_index = {'/'.join(v for v in (r['DirName'], r['FileName']) if v): r for r in toc}
    artwork = {}
    for name, wire in raw_members.items():
        packed = wire.startswith(b'CRILAYLA')
        blob = crilayla(wire) if packed else wire
        entry = {'member': name, 'stored_bytes': len(wire), 'stored_sha256': sha(wire),
            'decoded_bytes': len(blob), 'decoded_sha256': sha(blob), 'crilayla': packed,
            'toc_id': str(toc_index[name]['ID']), 'is_png': blob.startswith(b'\x89PNG\r\n\x1a\n')}
        entry['native_encrypted_main_image'] = not entry['is_png'] and name in main_members
        if entry['native_encrypted_main_image']:
            for source in source_index[Path(name).name]:
                if source['packed_bytes'] != len(wire): continue
                source_path = Path(source['source_path'])
                if not source_path.exists(): continue
                with source_path.open('rb') as f:
                    f.seek(source['member_offset']); original_wire = f.read(source['packed_bytes'])
                if original_wire != wire: continue
                job = EXTRACTED_CACHE/sha(str(source_path).encode())[:20]
                cached_png = job/'cpk'/name; receipt_path = job/'extraction_complete.json'
                entry['same_encrypted_member_in_original_source'] = {k:source[k] for k in
                    ('server','source_path','source_bytes','source_member','member_offset','packed_bytes')}
                if not cached_png.exists() or not receipt_path.exists(): continue
                extraction = json.loads(receipt_path.read_text(encoding='utf-8'))
                assert extraction['source_path'] == str(source_path) and extraction['returncode'] == 0
                with Image.open(cached_png) as image:
                    image.load()
                    entry.update({'width':image.width,'height':image.height,
                        'decoded_cache_png_sha256':file_sha(cached_png),
                        'established_extractor_cache':str(cached_png),
                        'extraction_receipt_sha256':file_sha(receipt_path)})
                break
        if entry['is_png']:
            with Image.open(io.BytesIO(blob)) as image:
                image.load(); rgba = image.convert('RGBA'); alpha = rgba.getchannel('A')
                entry.update({'width': image.width, 'height': image.height,
                    'pixel_sha256': sha(rgba.tobytes()), 'alpha_bbox': alpha.getbbox(),
                    'alpha_extrema': list(alpha.getextrema()), 'fully_transparent': alpha.getbbox() is None,
                    'visible_bounds_bytes': len(rgba.tobytes())})
                entry['alpha_padding'] = None if alpha.getbbox() is None else [alpha.getbbox()[0], alpha.getbbox()[1],
                    image.width-alpha.getbbox()[2], image.height-alpha.getbbox()[3]]
        artwork[name] = entry
    rows, alias_members, duplicate_pixels, duplicate_raw = [], collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for row in books:
        icon = by_icon.get(row[ICON]); member = icon.get(FILE) if icon else None
        art = artwork.get(member)
        title = row[NAME]
        dark_candidate = bool(re.search(r'dark\s*visions?|ダークビジョン', unicodedata.normalize('NFKC',title), re.I))
        status = 'missing_icon_row' if not icon else 'missing_CPK_member' if not art else 'encrypted_original_main_image' if art['native_encrypted_main_image'] else 'not_png' if not art['is_png'] else 'fully_transparent' if art['fully_transparent'] else 'present'
        mapped = mappings.get(row[BOOK], {})
        primary = mapped.get('primary_source_event_candidates', [])
        chosen = mapped.get('selected_original_banner') or {}
        original_names = {(s.get('source_icon') or {}).get('record', {}).get('file_name') for s in primary}
        original_names.discard(None)
        source_families = sorted({root(s['catalog_id']) for s in primary})
        routine_dv = dark_candidate and row[BOOK] not in GENESIS_EXCEPTION and not re.search(r'harbinger of chaos', title, re.I)
        item = {'book_id': row[BOOK], 'season_id': row[SEASON], 'season_name': seasons[row[SEASON]],
            'title': title, 'order': int(row[ORDER]), 'icon_id': row[ICON],
            'icon_name': icon.get(NAME) if icon else None, 'member': member, 'status': status,
            'event_identity_candidate': event_identity(title), 'dark_visions_title_match': dark_candidate,
            'actual_Dark_Visions_series_candidate': routine_dv,
            'Dark_Visions_preserve_candidate':dark_candidate and row[BOOK] not in GENESIS_EXCEPTION,
            'explicit_genesis_repair_exception': row[BOOK] in GENESIS_EXCEPTION,
            'primary_source_catalog_ids': sorted({s['catalog_id'] for s in primary}),
            'source_event_families': source_families,
            'source_event_names': sorted({s.get('event_name','') for s in primary}),
            'original_master_icon_filenames': sorted(original_names),
            'selected_original_source_member': chosen.get('source_member'),
            'selected_original_source_image_sha256': chosen.get('image_sha256'),
            'selected_original_source_image_matches_current': bool(chosen.get('image_sha256') and art and chosen['image_sha256']==art['decoded_sha256']),
            'generic_original_banner_filename': bool(re.fullmatch(r'(?:spd_bn_top_\d+|dummy_.*|test\d*|none)\.png', chosen.get('source_member','')))}
        if art:
            for key in ('stored_sha256','decoded_sha256','pixel_sha256','width','height','alpha_bbox','alpha_extrema','alpha_padding','crilayla','toc_id',
                        'same_encrypted_member_in_original_source','decoded_cache_png_sha256','established_extractor_cache','extraction_receipt_sha256'):
                if key in art: item[key] = art[key]
        rows.append(item)
        if member: alias_members[member].append(item)
        if art and art['is_png']:
            duplicate_pixels[(art['width'],art['height'],art['pixel_sha256'])].append(item)
            duplicate_raw[art['decoded_sha256']].append(item)
    def groups(mapping):
        result = []
        for key, users in mapping.items():
            if len(users) < 2: continue
            identities = {r['event_identity_candidate'] for r in users}
            exact_titles = {r['title'] for r in users}
            common_families = set.intersection(*(set(u['source_event_families']) for u in users))
            sourced_names = {event_identity(n) for u in users for n in u['source_event_names']}
            same_named_baseline = len(sourced_names)==1 and all(u['source_event_names'] or
                any(event_identity(u['title']).startswith(n) for n in sourced_names) for u in users)
            relation = 'source_proven_same_event_regional_reuse' if common_families else 'same_named_baseline_and_source_regional_reuse_candidate' if same_named_baseline else 'exact_same_title_reuse' if len(exact_titles)==1 else 'same_event_regional_or_reprint_candidate' if len(identities)==1 else 'cross_event_title_duplicate_candidate'
            partitions = collections.defaultdict(list)
            for u in users: partitions[','.join(u['source_event_families']) or u['event_identity_candidate']].append(u['book_id'])
            result.append({'identity': list(key) if isinstance(key, tuple) else key, 'book_count': len(users),
                'relation': relation, 'book_ids': [r['book_id'] for r in users], 'titles': sorted(exact_titles),
                'shared_source_families': sorted(common_families), 'source_family_partitions': dict(partitions),
                'season_ids': sorted({r['season_id'] for r in users}), 'members': sorted({r['member'] for r in users}),
                'dark_visions_book_ids': [r['book_id'] for r in users if r['dark_visions_title_match']],
                'requires_source_review_before_replacing': relation=='cross_event_title_duplicate_candidate'})
        return sorted(result, key=lambda r:(-r['book_count'],str(r['identity'])))
    dark = [r for r in rows if r['Dark_Visions_preserve_candidate']]
    report = {'schema': 'ffbe-production208-baseline-banner-inventory-v1', 'passed': True,
        'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'baseline_versionCode': 207, 'baseline_apk_sha256': APK_SHA,
        'content_catalog_sha256': CATALOG_SHA, 'side_manifest_sha256': SIDE_SHA, 'source_pins': pins,
        'book_count': len(rows), 'season_book_counts': dict(sorted(collections.Counter(r['season_id'] for r in rows).items())),
        'season_names': seasons, 'CPK_members': len(artwork),
        'CPK_PNG_dimensions': dict(sorted(collections.Counter(f"{a['width']}x{a['height']}" for a in artwork.values() if a['is_png']).items())),
        'menu_PNG_dimensions': dict(sorted(collections.Counter(f"{r['width']}x{r['height']}" for r in rows if r.get('width')).items())),
        'status_counts': dict(collections.Counter(r['status'] for r in rows)),
        'missing_or_unusable': [r for r in rows if r['status'] not in ('present','encrypted_original_main_image')],
        'main_encrypted_original_images': [r for r in rows if r['status']=='encrypted_original_main_image'],
        'main_original_decoded_dimensions_available': sum(r['status']=='encrypted_original_main_image' and 'width' in r for r in rows),
        'main_original_dimensions_unavailable_in_existing_cache':sum(r['status']=='encrypted_original_main_image' and 'width' not in r for r in rows),
        'all101_main_image_raw_bytes_identical_to_literal_Patch5':True,
        'literal_Patch5_banner_source':{'archive':str(p5_archive),'member':'assets/side_stories/spdungeon9.cpk',
            'bytes':len(p5_cpk),'sha256':sha(p5_cpk)},
        'shared_member_aliases': groups(alias_members), 'duplicate_decoded_PNG_hashes': groups(duplicate_raw),
        'duplicate_RGBA_pixels': groups(duplicate_pixels),
        'Dark_Visions_preserve_title_matched_candidates': dark,
        'Dark_Visions_preserve_candidates_sha256': sha(json.dumps(dark, sort_keys=True, separators=(',',':'),ensure_ascii=False).encode()),
        'explicit_Genesis_exception_book_ids': sorted(GENESIS_EXCEPTION),
        'dark_visions_scope_requires_series_identity_review': True,
        'non_series_Dark_Visions_name_matches': [r for r in rows if r['dark_visions_title_match'] and not r['actual_Dark_Visions_series_candidate']],
        'Harbinger_of_Chaos_protected_conservatively':True,
        'source_family_mapping': {'file':str(MAPPING),'sha256':MAPPING_SHA,
            'method':'Only explicit supported_regional_counterpart edges union catalog identities; shared book or art alone does not union events'},
        'original_source_member_index':{'file':str(SOURCE_INDEX),'sha256':file_sha(SOURCE_INDEX)},
        'generic_original_banner_filename_books': [r for r in rows if r['generic_original_banner_filename']],
        'same_event_relation_is_conservative_title_inference': True,
        'cross_title_duplicates_are_candidates_not_automatic_art_replacement_authority': True,
        'inventory_scope': 'all1004 current books and exact icon master aliases/current override spdungeon9 CPK',
        'books': rows, 'archive_members': list(artwork.values()),
        'network_requests': 0, 'device_actions': False, 'payloads_modified': False,
        'inventory_source_sha256': file_sha(Path(__file__))}
    return report

if __name__ == '__main__':
    report = inventory()
    target = ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    protected = report['Dark_Visions_preserve_title_matched_candidates']
    members = {r['member']:r for r in report['archive_members']}
    protected_names = sorted({r['member'] for r in protected})
    scope = {'schema':'ffbe-production208-Dark-Visions-preservation-v1','passed':True,
        'baseline_apk_sha256':APK_SHA,'source_inventory_sha256':file_sha(target),
        'catalog_sha256':CATALOG_SHA,'banner_CPK_sha256':report['source_pins']['archive']['sha256'],
        'scope':'Preserve all DarkVisions title-matched book/icon bindings and actual existing image member bytes/sizes; all4 explicit Genesis aliases are outside this exclusion',
        'book_ids':[r['book_id'] for r in protected],'books':protected,
        'members':[members[n] for n in protected_names],
        'Harbinger_of_Chaos_preserved_conservatively':True,
        'explicit_Genesis_exceptions':sorted(GENESIS_EXCEPTION),
        'new_non_DV_image_and_icon_alias_required_when_an_incorrect_image_is_shared_with_protected_DV':True}
    (ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','book_count','season_book_counts','season_names','status_counts','CPK_PNG_dimensions','menu_PNG_dimensions')},ensure_ascii=True))
    print(json.dumps({'report': str(target), 'sha256': file_sha(target),
        'cross_title_pixel_groups': sum(g['relation']=='cross_event_title_duplicate_candidate' for g in report['duplicate_RGBA_pixels']),
        'dark_visions_preserve_title_candidates': len(report['Dark_Visions_preserve_title_matched_candidates'])}))
