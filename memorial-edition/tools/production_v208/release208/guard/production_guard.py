"""Exact build207 preservation and finite production208 banner operations.

Only the APK differential primitives are prepared before final source plans.
Content qualification and CLI are added once those finite plans are available.
"""
from pathlib import Path
import argparse, datetime, hashlib, io, json, re, struct, sys, urllib.parse, zipfile, zlib
import baseline207_guard as primitives

ROOT = Path(__file__).resolve().parents[1]
BASELINE_APK_SHA = 'd9181ffc05fa11e15f18102646734f33832b5d70793357ffa24a643ec8209f2e'
BASELINE_SCRIPT_SHA = 'd766347efe033dbeb2bc358e99c6cf74385da95d19a0528d20f8841bacd0d696'
BASELINE_DEX_SHA = '408b8332dfbe4aaccb239ca0de3e3a71a7dc02e54f84135c321eeca2b58cc558'
BASELINE_CATALOG_SHA = '963a25b4e8e616aacb29b3a868237c04ae8fab7fb2505fd2fbc19f892e77f59a'
BASELINE_SIDE_SHA = '0cffedb63a0090b636e022c842ce3ce14656c578a11884ba88fdc44317673c14'
BASELINE_QUALIFICATION_SHA = '1368c69047515c6f36a7500144ec2da4c23e430fbbe16e9b22bbb471a6513f17'
PRIMITIVES_SHA = '4ff86911976689bf7d21bc45a74a783628ede49b2747331752e46d6b47b538ce'
INVENTORY_SHA = '1fcab68f8df8cbdd6d6784a51cf3d1aa306f4cfb4e3cc5a7e0e301d870d8ab3e'
DARK_VISIONS_SCOPE_SHA = 'a8cdb18d0671ad4de43b250becb55111ef37ff7670a9513a893a4cf2fea77e3b'
PROPOSAL_SHA = 'da1911049240d7ffb6ae21e5ab1b3bf2a4672d33dfc4e57a0052c7c0efa281e5'
ACTIVE_PROPOSAL_SHA = '0a9e374dd92c47bef4e6ad8f7b40a9bc86a9eef16f84d2f7fd24687cb90ee251'
WRAPPER_AUDIT_SHA = 'b983ada38a857bdc43a05a5b7c70e1ea558dd7ad62b0300d95625017324c64fd'
WRAPPER_PLAN_SHA = '037f3e3e4a0786404b995e279a8c2dd8d0bea97b2f5470530e2e7782fe0a98cf'
REVISION2_ORDER_PLAN_SHA = 'ae3411d1435c9e64b4146330ef3492d51530b3d5f45f1f8c072a606148743cb9'
PLACEHOLDER_EXTENSION_SHA = '6c23225531820504d4bcb3252fa21cd00bf147db3b2f0e47fa66a24e310c88eb'
PLACEHOLDER_EXTENSION = {
    '7051': ('70000049','side_book_7051.png',8,'4f21a8d28853e66b4d0922d1c81d2693ddbb7270497f3728d5840e31a56fb0cd'),
    '7067': ('70000065','side_book_7067.png',2,'f1886ae2cc9bd9dadeab637ccceb44d9cb75c9342b0e875d714aeb94e299d59e'),
    '7069': ('70000067','side_book_7069.png',1,'9e22ca30d164a1bf3e0f492ca24c4ad4833cf61be5b3c9b69320ab3be1595421'),
}
BASELINE_APK = ROOT.parent/'v207-download-spacing/staged_build/dist/FFBE-Memorial-EN-Download-Spacing-v207.apk'
SIGNER_SHA = primitives.SIGNER_SHA
ALLOWED_APK_MEMBERS = frozenset(('AndroidManifest.xml','assets/frida_script.js',
    'assets/content_delivery.tsv','assets/side_stories/manifest.tsv'))
SCRIPT_OPERATIONS = (
    ('const PATCH_VERSION = 207;', 'const PATCH_VERSION = 208;'),
    ('const MANIFEST_URL   = "https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json";',
     'const MANIFEST_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json";'),
    ('const DOWNLOAD_URL   = "https://ffbe.luminest.io/downloads/beta/";',
     'const DOWNLOAD_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest";'))
require = primitives.require
sha = primitives.sha
file_sha = primitives.file_sha
BOOK = 'M9mwe2cu'
ICON = '0HUPxDf1'
ORDER = 'Z0EN6jSh'
SEASON = '2ShgIRU8'
FILENAME = 'qtkvrS60'
HASH = re.compile(r'[a-f0-9]{64}')
BASELINE_EXTERNAL = {
    'side_stories/spdungeon9.cpk': ROOT.parent/'v206-event-cleanup/payload/side_stories/spdungeon9.cpk',
    'side_stories/Nm36woZx.dat': ROOT.parent/'v206-event-cleanup/payload/side_stories/Nm36woZx.dat',
    'side_stories/LM1APs6u.dat': ROOT.parent/'v205-patch5-events/payload/side_stories/LM1APs6u.dat',
}
CHANGED_EXTERNAL = frozenset(BASELINE_EXTERNAL)

def pinned_file(row):
    path = Path(row.get('local_path', row.get('file', row.get('path', ''))))
    blob = path.read_bytes()
    require(len(blob) == int(row['bytes']) and sha(blob) == row['sha256'], 'Source pin differs: '+str(path))
    return blob

def parse_catalog(blob):
    lines = blob.decode('utf-8').splitlines()
    require(lines and lines[0] == 'ffbe-content-v1', 'Content catalog header differs')
    result = {}
    for line in lines[1:]:
        parts = line.split('\t')
        require(len(parts) == 8, 'Catalog eight-field contract changed')
        path, digest, rawbytes, url, offset, wirebytes, method, sourcebytes = parts
        require(path not in result and '..' not in path and not path.startswith('/'), 'Unsafe/duplicate catalog path')
        require(HASH.fullmatch(digest), 'Invalid catalog digest')
        nums = list(map(int, (rawbytes, offset, wirebytes, method, sourcebytes)))
        require(nums[0]>0 and nums[1]>=0 and nums[2]>0 and nums[3] in (0,8)
                and nums[4]>0 and nums[1]+nums[2]<=nums[4], 'Invalid catalog bytes/range')
        result[path] = {'parts':parts, 'line':line, 'sha256':digest, 'bytes':nums[0], 'url':url,
                        'offset':nums[1], 'wirebytes':nums[2], 'method':nums[3], 'sourcebytes':nums[4]}
    require(blob == ('ffbe-content-v1\n'+'\n'.join(r['line'] for r in result.values())+'\n').encode(),
            'Catalog formatting changed')
    return result

def immutable_transport(row):
    url = urllib.parse.urlsplit(row['url'])
    require(url.scheme == 'https' and url.netloc == 'github.com' and url.username is None
            and re.fullmatch(r'/luminest-llc/ffbe-memorial-downloads/releases/download/[^/]+/[^/]+', url.path)
            and '/latest/' not in url.path and not url.query, 'Transport must pin immutable GitHub release')
    if url.fragment:
        match = re.fullmatch(r'ffbe-range=(\d+):(\d+):(\d+)', url.fragment)
        require(match is not None, 'Invalid transport range fragment')
        start, length, total = map(int, match.groups())
        require(length == row['sourcebytes'] and length>0 and start+length<=total, 'Source range differs')
    require(row['method'] != 0 or row['wirebytes'] == row['bytes'], 'Stored wire/raw bytes differ')

def parse_side_manifest(blob):
    result = {}
    for line in blob.decode('utf-8').splitlines():
        p = line.split('\t')
        require(len(p) in (3,4) and p[0] not in result and '..' not in p[0]
                and re.fullmatch(r'[A-Za-z0-9_./-]+', p[0]) and not p[0].startswith('/'), 'Unsafe/duplicate side row')
        require(HASH.fullmatch(p[1]), 'Invalid current side hash')
        accepted = set(filter(None, p[2].split(',')))
        require(all(HASH.fullmatch(x) for x in accepted), 'Invalid accepted side hash')
        variants = {}
        if len(p)==4 and p[3]:
            for pair in p[3].split(','):
                digest, name = pair.split('=',1)
                require(HASH.fullmatch(digest) and digest not in variants and '..' not in name
                        and re.fullmatch(r'[A-Za-z0-9_./-]+', name) and not name.startswith('/'), 'Unsafe side variant')
                variants[digest] = name
        result[p[0]] = {'line':line, 'sha256':p[1], 'accepted':accepted, 'variants':variants}
    require(blob == ('\n'.join(r['line'] for r in result.values())+'\n').encode(), 'Side manifest formatting changed')
    return result

def baseline_external(path, prior):
    require(path in BASELINE_EXTERNAL, 'Unrequested external file')
    blob = BASELINE_EXTERNAL[path].read_bytes()
    require(len(blob)==prior[path]['bytes'] and sha(blob)==prior[path]['sha256'], 'Qualified207 external baseline differs: '+path)
    return blob

def compare_exact_row_operations(original, candidate, operations, primary_key, allowed_field):
    """A row declaration never authorizes any other field, ordering or membership change."""
    require(len(original)==len(candidate), 'Table row membership changed')
    require(len({str(r[primary_key]) for r in original})==len(original), 'Duplicate baseline primary key')
    expected = [dict(row) for row in original]
    seen = set()
    receipts = []
    for operation in operations:
        index, key = int(operation['index']), str(operation['id'])
        require(0<=index<len(original) and key not in seen, 'Invalid/duplicate table operation')
        seen.add(key)
        before, after = operation['before'], operation['after']
        require(str(original[index][primary_key])==key and before==original[index], 'Exact original row/index differs')
        require(set(before)==set(after) and str(after[primary_key])==key, 'Table columns/key changed')
        require(operation['fields']==[allowed_field], 'Unrequested field allowance')
        differences = {field for field in before if before[field]!=after[field]}
        require(differences=={allowed_field}, 'Row operation must change exactly its single approved field')
        expected[index] = dict(after)
        receipts.append({'index':index, 'id':key, 'field':allowed_field,
                         'before':before[allowed_field], 'after':after[allowed_field]})
    require(candidate==expected, 'Unlisted table row, value or physical order changed')
    return receipts

def compare_metadata(old_catalog, new_catalog, old_side, new_side, files):
    require(sha(old_catalog)==BASELINE_CATALOG_SHA and sha(old_side)==BASELINE_SIDE_SHA, 'Qualified207 metadata seal differs')
    old, new = parse_catalog(old_catalog), parse_catalog(new_catalog)
    require(len(old)==1898 and list(old)==list(new), 'Catalog path membership/order changed')
    require(set(files)==CHANGED_EXTERNAL, 'Expected only three requested external changes')
    changed = []
    for name,row in new.items():
        if name not in files:
            require(row['line']==old[name]['line'], 'Unrequested catalog descriptor changed: '+name)
        else:
            require(row['sha256']==files[name]['sha256'] and row['bytes']==files[name]['bytes']
                    and row['sha256']!=old[name]['sha256'], 'Candidate raw catalog pin differs: '+name)
            immutable_transport(row)
            changed.append({'path':name, 'before':old[name]['parts'], 'after':row['parts']})
    a,b = parse_side_manifest(old_side), parse_side_manifest(new_side)
    require(len(a)==1857 and list(a)==list(b), 'Side path membership/order changed')
    side = []
    for name,row in b.items():
        path = 'side_stories/'+name
        if path not in files:
            require(row['line']==a[name]['line'], 'Unrequested side descriptor changed: '+name)
        else:
            expected = a[name]['line'].split('\t')
            expected[1] = files[path]['sha256']
            expected[2] = ','.join(sorted(a[name]['accepted']|{a[name]['sha256']}))
            require(row['line']=='\t'.join(expected), 'Side descriptor exceeds exact new hash/prior acceptance: '+name)
            side.append({'path':path, 'before':a[name]['line'], 'after':row['line']})
        require(all('side_stories/'+p in new for p in row['variants'].values()), 'Side variant absent from catalog')
    return new, {'catalog_rows':1898, 'side_manifest_rows':1857, 'catalog_changes':changed,
                 'side_manifest_changes':side, 'unchanged_descriptor_count':1895,
                 'all_other_descriptor_bytes_and_order_preserved':True, 'added_or_removed_paths':0}

def approved_proposal():
    path = ROOT.parent/'v208-production-candidate1/audit/BANNER_REPAIR_PROPOSAL.json'
    require(file_sha(path)==PROPOSAL_SHA, 'Finite approved source proposal seal differs')
    plan = json.loads(path.read_bytes())
    require(plan['passed'] is True and plan['inventory_sha256']==INVENTORY_SHA
            and plan['fallback_count']==594 and plan['restored_neutral_member_count']==417
            and plan['already_neutral_member_count']==177 and len(plan['recovered_art'])==7
            and not plan['source_gaps'], 'Approved finite proposal scope differs')
    for source in plan['source_pins']: pinned_file(source)
    extension_path=ROOT/'audit/REMAINING_BASELINE_PLACEHOLDERS.json'
    require(file_sha(extension_path)==PLACEHOLDER_EXTENSION_SHA, 'Exact three-placeholder source audit seal differs')
    extension=json.loads(extension_path.read_bytes())
    require(extension['passed'] and extension['count']==3
            and {str(row['book_id']) for row in extension['records']}==set(PLACEHOLDER_EXTENSION), 'Unlisted placeholder extension')
    for row in extension['records']:
        icon,member,order,digest=PLACEHOLDER_EXTENSION[str(row['book_id'])]
        require(str(row['icon_id'])==icon and row['member']==member and int(row['current_order'])==order
                and row['sha256']==digest and str(row['season_id'])=='71'
                and row['current208_bytes_equal_literalP5'] and row['generated_PNG_equals_P5_member'],
                'Exact additional P5 placeholder identity differs')
    current_path=ROOT/'audit/BANNER_REPAIR_PROPOSAL.json'
    require(file_sha(current_path)==ACTIVE_PROPOSAL_SHA, 'Exact revision2 proposal seal differs')
    current=json.loads(current_path.read_bytes())
    require(current['passed'] and current['schema']==plan['schema'] and current['inventory_sha256']==INVENTORY_SHA
            and current['fallback_count']==597 and current['restored_neutral_member_count']==420
            and current['already_neutral_member_count']==177 and not current['source_gaps'], 'Extended finite source proposal scope differs')
    require(current['supplemental_template_proof_sha256']==PLACEHOLDER_EXTENSION_SHA, 'Additional literal P5 provenance proof differs')
    original_rows={str(row['book_id']):row for row in plan['fallback_books']}
    current_rows={str(row['book_id']):row for row in current['fallback_books']}
    require(len(current_rows)==len(current['fallback_books'])==597
            and set(current_rows)==set(original_rows)|set(PLACEHOLDER_EXTENSION)
            and all(current_rows[bid]==row for bid,row in original_rows.items()),
            'Original594 fallback identities changed or unlisted new source added')
    for key in ('recovered_art','qualified206_cover_book_ids','protected_Dark_Visions_book_ids','genuine_group_owners','genuine_generic_ids'):
        require(current[key]==plan[key], 'Unrequested recovery/protected-owner scope changed: '+key)
    for record in extension['records']:
        bid=str(record['book_id']);row=current_rows[bid]
        require(row['source_origin']=='literal_patch5_template' and row['title']==record['title']
                and str(row['icon_id'])==record['icon_id'] and str(row['season_id'])=='71'
                and int(row['original_order'])==record['current_order']
                and row['fallback']['target_member']=='event_missing_art_book_'+bid+'.png'
                and row['fallback']['sha256']==record['sha256'] and row['fallback']['bytes']==record['bytes'],
                'Extended source proposal does not equal exact additional P5 ID/title/image identity')
    plan['_active_proposal_sha256']=file_sha(current_path)
    plan['_placeholder_extension']=extension['records']
    return plan

def archive_row_name(row):
    return '/'.join(str(row[k]) for k in ('DirName','FileName') if row[k])

def approved_wrappers():
    audit_path=ROOT/'audit/NONSTANDARD_GENUINE_BANNER_GEOMETRY.json'
    plan_path=ROOT/'audit/NATIVE_CANVAS_WRAPPER_PLAN.json'
    require(file_sha(audit_path)==WRAPPER_AUDIT_SHA and file_sha(plan_path)==WRAPPER_PLAN_SHA,
            'Exact50 native-canvas source identities or scope changed')
    audit=json.loads(audit_path.read_bytes());plan=json.loads(plan_path.read_bytes())
    require(audit['passed'] and audit['book_count']==audit['member_count']==50
            and audit['section_counts']=={'JP Memories':47,'Event Battles':3}
            and audit['size_counts']=={'600x120':50}, 'Wrapper source audit scope differs')
    require(plan['schema']=='ffbe208-genuine-native-canvas-wrapper-plan-v1' and plan['passed']
            and plan['source_audit_sha256']==WRAPPER_AUDIT_SHA and plan['member_count']==len(plan['records'])==50,
            'Native canvas wrapper plan identity differs')
    source={str(row['book_id']):row for row in audit['records']}
    require(len(source)==50 and {str(row['book_id']) for row in plan['records']}==set(source), 'Unlisted/omitted wrapper book')
    for record in plan['records']:
        bid=str(record['book_id']);before=source[bid]
        require(record['name']=='event_native_canvas_book_'+bid+'.png' and record['book_ids']==[bid]
                and str(record['icon_id'])==str(before['icon_id']) and record['title']==before['title']
                and str(record['season_id'])==str(before['season_id'])
                and record['old_member']==record['source_member']==before['current_member']
                and record['bytes']==before['bytes'] and record['sha256']==before['sha256']
                and record['original_source_sha256']==before['selected_original_source_image_sha256']==record['sha256']
                and record['original_source_member']==before['selected_original_source_member']
                and before['source_image_matches_current'] and not before['protected_Dark_Visions_member'],
                'Wrapper source/owner identity differs from exact genuine image audit')
        require(record['source_geometry']==[600,120] and record['target_canvas']==[640,240]
                and record['offset']==[20,60] and record['padding']==[20,60,20,60]
                and record['transform_kind']=='native_canvas_padding' and record['preserve_source_RGBA_pixels']
                and all(record[key] is False for key in ('resampling','crop','recolor','alpha_compositing','change_order')),
                'Wrapper exceeds exact unchanged-pixel transparent canvas allowance')
    return plan

def verify_cpk_preservation(old, new, operations):
    old_rows, new_rows = old[3], new[3]
    old_names, new_names = [archive_row_name(r) for r in old_rows], [archive_row_name(r) for r in new_rows]
    require(len(old_names)==len(set(old_names)) and len(new_names)==len(set(new_names)), 'Duplicate CPK TOC name')
    require(list(old[4])==old_names and list(new[4])==new_names, 'CPK TOC/raw member linkage differs')
    require([name for name in new_names if name in old[4]]==old_names, 'Original CPK relative TOC order changed')
    require(new_names==sorted(new_names) and int(old[0]['Sorted'])==int(new[0]['Sorted'])==1,
            'Native sorted CPK contract changed')
    require(int(old[0]['Align'])==int(new[0]['Align']), 'CPK alignment changed')
    expected = dict(old[4]); seen = set()
    for operation in operations:
        name, kind = operation['name'], operation['operation']
        require(name not in seen and kind in ('add','replace'), 'Duplicate/unknown CPK operation')
        seen.add(name)
        require((name not in old[4])==(kind=='add'), 'CPK operation does not match original presence')
        before = operation['baseline']
        if kind=='add': require(before is None, 'New member must have null baseline')
        else: require(before and sha(old[4][name])==before['sha256'] and len(old[4][name])==before['bytes'], 'CPK original pin differs')
        candidate = pinned_file(operation['candidate'])
        require(candidate!=old[4].get(name), 'CPK operation is a no-op')
        expected[name] = candidate
    require(set(new[4])==set(expected) and all(new[4][name]==blob for name,blob in expected.items()),
            'Unlisted CPK member addition, removal or raw-byte change')
    new_index = {archive_row_name(row):row for row in new_rows}
    for old_row in old_rows:
        name=archive_row_name(old_row); new_row=new_index[name]
        require(set(old_row)==set(new_row), 'CPK metadata columns changed')
        ignored={'FileOffset'}|({'FileSize','ExtractSize'} if name in seen else set())
        require(all(old_row[k]==new_row[k] for k in old_row if k not in ignored), 'Original CPK ID/metadata changed: '+name)
    ids=[str(row['ID']) for row in new_rows]
    require(len(ids)==len(set(ids)), 'CPK IDs are not unique')
    return {'original_members':len(old[4]), 'candidate_members':len(new[4]),
            'added_members':sum(o['operation']=='add' for o in operations),
            'replaced_members':sum(o['operation']=='replace' for o in operations),
            'unchanged_original_raw_members':len(old[4])-sum(o['operation']=='replace' for o in operations),
            'all_other_raw_members_byte_identical':True, 'original_relative_TOC_order_and_IDs_preserved':True,
            'native_sorted_flag_preserved':True}

def qualify_ordering(payload, plan, proposal, prior, rows_bytes, protected_ids):
    require(file_sha(ROOT/'audit/ORDER_PLAN.json')==REVISION2_ORDER_PLAN_SHA,
            'The50 genuine image wrappers must preserve the prior599 ordering operations exactly')
    require(plan.get('schema')=='ffbe208-neutral-art-ordering-plan-v1' and plan.get('passed') is True
            and plan['baseline_apk_sha256']==BASELINE_APK_SHA and plan['baseline_versionCode']==207
            and plan['proposal_sha256']==proposal['_active_proposal_sha256'], 'Ordering plan identity incomplete')
    changes=plan['table_changes'];require(len(changes)==1, 'Only book Order table may change')
    item=changes[0];name='side_stories/Nm36woZx.dat'
    require(item['path']==name and item['stem']=='Nm36woZx', 'Unrequested ordering table')
    before=baseline_external(name,prior);after=pinned_file(item)
    require(pinned_file(item['baseline'])==before and after==(Path(payload)/name).read_bytes(), 'Ordering source identity differs')
    original,candidate=rows_bytes(before,'Nm36woZx'),rows_bytes(after,'Nm36woZx')
    require(len(original)==1004, 'Qualified207 book membership differs')
    receipts=compare_exact_row_operations(original,candidate,item['operations'],BOOK,ORDER)
    fallback={str(row['book_id']) for row in proposal['fallback_books']}|set(PLACEHOLDER_EXTENSION)
    require(set(map(str,plan['fallback_book_ids']))==fallback and len(fallback)==597, 'Fallback Order scope differs')
    changed={str(row['id']) for row in item['operations']}
    require(changed==fallback|{'7074','7075'} and not(changed&protected_ids), 'Unrequested/missing Order change or protected DV operation')
    old_index={str(row[BOOK]):row for row in original};new_index={str(row[BOOK]):row for row in candidate}
    source_fallback={str(row['book_id']):row for row in proposal['fallback_books']}
    source_fallback.update({str(row['book_id']):{**row,'original_order':row['current_order']} for row in proposal['_placeholder_extension']})
    for bid in fallback:
        require(str(old_index[bid][SEASON])==str(source_fallback[bid]['season_id'])
                and int(old_index[bid][ORDER])==int(source_fallback[bid]['original_order']), 'Original fallback identity/Order differs')
    for season in ('70','71','92'):
        targets=[row for row in candidate if str(row[SEASON])==season and str(row[BOOK]) in fallback]
        normal=[row for row in candidate if str(row[SEASON])==season and str(row[BOOK]) not in fallback|{'7074','7075'}]
        require(targets and normal and min(int(row[ORDER]) for row in targets)>max(int(row[ORDER]) for row in normal),
                'Unresolved banners must follow every retained normal entry in their native menu')
        original_order=sorted((int(old_index[str(row[BOOK])][ORDER]),original.index(old_index[str(row[BOOK])]),str(row[BOOK])) for row in targets)
        candidate_order=sorted((int(row[ORDER]),str(row[BOOK])) for row in targets)
        require([row[2] for row in original_order]==[row[1] for row in candidate_order], 'Fallback relative native Order changed')
        require(len({int(row[ORDER]) for row in targets})==len(targets), 'Fallback Orders are not unique')
    story=[row for row in candidate if str(row[SEASON])=='70' and str(row[BOOK]) not in {'7074','7075'}]
    maximum=max(int(row[ORDER]) for row in story)
    require(int(new_index['7074'][ORDER])==maximum+1 and int(new_index['7075'][ORDER])==maximum+2,
            'Revival1 and2 must remain the absolute last Story Events')
    return {name:{'bytes':len(after),'sha256':sha(after)}},original,candidate,{
        'book_count':1004,'physical_row_order_and_all_other_fields_preserved':True,
        'operations':receipts,'fallback_books':597,'Revival1_and2_absolute_last':True,
        'only_native_Order_field_changed':True}

def qualify_banners(payload, plan, proposal, prior, rows_bytes, read_cpk, books):
    require(plan.get('schema')=='ffbe208-banner-and-icon-plan-v1' and plan.get('passed') is True
            and plan['baseline_apk_sha256']==BASELINE_APK_SHA and plan['baseline_versionCode']==207
            and plan['proposal_sha256']==proposal['_active_proposal_sha256']
            and plan['protected_Dark_Visions_scope_sha256']==DARK_VISIONS_SCOPE_SHA, 'Banner plan identity incomplete')
    for field,path in [('geometry_plan_sha256',ROOT/'audit/BANNER_GEOMETRY_PLAN.json'),
                       ('geometry_inputs_sha256',ROOT/'audit/BANNER_GEOMETRY_INPUTS.json'),
                       ('rendered207_review_sha256',ROOT/'audit/RENDERED_207_BANNER_REVIEW.json')]:
        require(plan[field]==file_sha(path), 'Source/rendered geometry proof pin differs')
    asset=plan['asset'];name='side_stories/spdungeon9.cpk'
    require(asset['path']==name, 'Unrequested CPK asset')
    before=baseline_external(name,prior);after=pinned_file(asset)
    require(pinned_file(asset['baseline'])==before and after==(Path(payload)/name).read_bytes(), 'Banner archive source pin differs')
    old,new=read_cpk(before),read_cpk(after)
    require(len(old[4])==561, 'Qualified207 CPK membership differs')
    icon_name='side_stories/LM1APs6u.dat';icon_asset=plan['icon_table']
    require(icon_asset['path']==icon_name and icon_asset['stem']=='LM1APs6u', 'Unrequested icon master')
    original_icon=baseline_external(icon_name,prior);candidate_icon=pinned_file(icon_asset)
    require(pinned_file(icon_asset['baseline'])==original_icon and candidate_icon==(Path(payload)/icon_name).read_bytes(),
            'Icon master source pin differs')
    original_icons,candidate_icons=rows_bytes(original_icon,'LM1APs6u'),rows_bytes(candidate_icon,'LM1APs6u')
    icon_receipt=compare_exact_row_operations(original_icons,candidate_icons,plan['icon_rows'],ICON,FILENAME)
    old_icon_index={str(row[ICON]):row for row in original_icons};new_icon_index={str(row[ICON]):row for row in candidate_icons}
    book_index={str(row[BOOK]):row for row in books}
    require(len(book_index)==1004, 'Book baseline membership differs')
    protected=json.loads((ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json').read_bytes())
    protected_ids=set(map(str,protected['book_ids']));protected_names={row['member'] for row in protected['members']}
    require(len(protected_ids)==66, 'Protected Dark Visions scope differs')
    baseline_inventory=json.loads((ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json').read_bytes())
    inventory={row['book_id']:row for row in baseline_inventory['books']}
    archives={name:old[4]}
    archive_source_pins={source['file']:source for source in proposal['source_pins']}
    def source_member(archive,member):
        require(archive in archive_source_pins, 'Unapproved source archive')
        if archive not in archives: archives[archive]=read_cpk(pinned_file(archive_source_pins[archive]))[4]
        require(member in archives[archive], 'Approved source member is absent')
        return archives[archive][member]
    expected_geometry={};expected_icons={};fallback_ids=set()
    additions=set();retained=set()
    for entry in proposal['fallback_books']:
        bid=str(entry['book_id']);fallback_ids.add(bid);fallback=entry['fallback']
        require(bid not in protected_ids and str(book_index[bid][SEASON]) in {'70','71','92'}, 'Unrequested fallback menu or DV change')
        require(str(book_index[bid][ICON])==str(entry['icon_id']) and inventory[bid]['title']==entry['title'], 'Fallback book/icon/title identity differs')
        source=source_member(fallback['archive'],fallback['member'])
        require(sha(source)==fallback['sha256'] and len(source)==fallback['bytes'], 'Exact fallback source member differs')
        target=fallback['target_member'];require(target not in expected_geometry and target not in protected_names, 'Duplicate/protected fallback target')
        expected_geometry[target]={'source':source,'source_archive':fallback['archive'], 'source_member':fallback['member'], 'book_ids':{bid}}
        if target not in old[4]:
            additions.add(target)
            require(entry['source_identity']['same_stable_book_id'] and entry['source_identity']['exact_title_equal']
                    and entry['source_identity']['retained_title']==entry['title'], 'Restored neutral source ID/title differs')
            expected_icons[str(entry['icon_id'])]={target}
        else:
            retained.add(target)
            require(target==entry['old_wrong_member'] and source==old[4][target], 'Retained neutral source differs from207')
    require(len(fallback_ids)==594 and len(additions)==417 and len(retained)==177, 'Exact neutral source membership differs')
    original_p5_source=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Content-Source.apk')
    with zipfile.ZipFile(original_p5_source) as baseline:
        original_p5_cpk=baseline.read('assets/side_stories/spdungeon9.cpk')
        original_p5_book_blob=baseline.read('assets/side_stories/Nm36woZx.dat')
    require(sha(original_p5_cpk)=='2f2be2a15887aebf90ed82395e2fcd6d62dad4aae1f84a9d6b07324626481dd6',
            'Literal P5 source banner archive differs')
    require(sha(original_p5_book_blob)=='1db3d48ef4db819435af3ddda0cf35909bf42bd68e1851f6d454f8e5b8660026',
            'Literal P5 source book table differs')
    original_p5_books={str(row[BOOK]):row for row in rows_bytes(original_p5_book_blob,'Nm36woZx')}
    original_p5_members=read_cpk(original_p5_cpk)[4]
    for entry in proposal['_placeholder_extension']:
        bid=str(entry['book_id']);icon,original_member,order,digest=PLACEHOLDER_EXTENSION[bid]
        require(str(book_index[bid][ICON])==icon and str(book_index[bid][SEASON])=='71'
                and int(book_index[bid][ORDER])==order and inventory[bid]['title']==entry['title']
                and str(original_p5_books[bid][ICON])==icon
                and original_p5_books[bid]['G4L0YIB2']==book_index[bid]['G4L0YIB2']==entry['title']
                and old_icon_index[icon][FILENAME]==original_member, 'Additional placeholder book binding differs')
        source=original_p5_members[original_member]
        require(sha(source)==digest and len(source)==entry['bytes'] and source==old[4][original_member]
                and Path(entry['existing_generated_PNG_file']).read_bytes()==source,
                'Additional source is not the exact original P5 generated PNG')
        alias_members=[item['name'] for item in plan['members'] if set(map(str,item['book_ids']))=={bid}]
        require(len(alias_members)==1, 'Additional placeholder must bind exactly one new alias')
        target=alias_members[0]
        require(target=='event_missing_art_book_'+bid+'.png' and target not in old[4]
                and target not in expected_geometry and target not in protected_names,
                'Additional placeholder must preserve every original raw image member')
        require(all(old_icon_index[str(row[ICON])][FILENAME]!=original_member or str(row[BOOK])==bid for row in books),
                'Additional placeholder has an unlisted shared owner')
        expected_geometry[target]={'source':source,'source_archive':str(original_p5_source)+'!assets/side_stories/spdungeon9.cpk',
                                   'source_member':original_member,'book_ids':{bid}}
        additions.add(target);fallback_ids.add(bid);expected_icons[icon]={target}
    generated=set()
    for bid in map(str,proposal['qualified206_cover_book_ids']):
        if bid=='7074': continue
        member=inventory[bid]['member']
        require(member not in protected_names and member not in expected_geometry, 'Geometry reaches unrequested/shared neutral or DV member')
        source=old[4][member]
        require(sha(source)==inventory[bid]['stored_sha256'], 'Qualified206 geometry source differs')
        owners={str(row[BOOK]) for row in books if old_icon_index[str(row[ICON])][FILENAME]==member}
        require(not(owners&protected_ids) and all(str(book_index[id][SEASON]) in {'70','71','92'} for id in owners),
                'Generated cover geometry reaches a protected/unrequested book')
        expected_geometry[member]={'source':source,'source_archive':str(BASELINE_EXTERNAL[name]),'source_member':member,'book_ids':owners}
        generated.add(member)
    require(len(generated)==11 and len(expected_geometry)==608 and len(additions)==420 and len(fallback_ids)==597,
            'Exact generated geometry/three-placeholder extension scope differs')
    wrappers=approved_wrappers()
    require(plan['native_canvas_wrapper_plan_sha256']==WRAPPER_PLAN_SHA, 'Banner plan does not bind exact wrapper scope')
    wrapper_names=set();wrapper_ids=set()
    for record in wrappers['records']:
        bid=str(record['book_id']);icon=str(record['icon_id']);member=record['old_member'];target=record['name']
        require(bid not in fallback_ids|protected_ids and str(book_index[bid][ICON])==icon
                and str(book_index[bid][SEASON])==str(record['season_id']) and str(record['season_id']) in {'71','92'}
                and book_index[bid]['G4L0YIB2']==record['title'] and old_icon_index[icon][FILENAME]==member,
                'Genuine wrapper touches unrequested/fallback/protected owner')
        source=old[4][member]
        require(len(source)==record['bytes'] and sha(source)==record['sha256']
                and inventory[bid]['selected_original_source_image_sha256']==record['sha256']
                and inventory[bid]['selected_original_source_member']==record['original_source_member'],
                'Wrapper raw source differs from exact qualified original image')
        owners={str(row[BOOK]) for row in books if old_icon_index[str(row[ICON])][FILENAME]==member}
        require(owners=={bid} and member not in protected_names and target not in old[4]
                and target not in expected_geometry and icon not in expected_icons,
                'Wrapper source is shared with an unlisted/protected owner or overwrites an original image')
        expected_geometry[target]={'source':source,'source_archive':str(BASELINE_EXTERNAL[name]),
                                   'source_member':member,'book_ids':{bid},'mode':'pad'}
        additions.add(target);wrapper_names.add(target);wrapper_ids.add(bid);expected_icons[icon]={target}
    require(len(wrapper_ids)==len(wrapper_names)==50 and len(expected_geometry)==658 and len(additions)==470,
            'Exact50-wrapper member/owner closure differs')
    for item in proposal['recovered_art']:
        bid=str(item['book_id']);icon=str(item['icon_id'])
        require(bid not in fallback_ids|protected_ids and str(book_index[bid][ICON])==icon, 'Recovery book scope differs')
        targets=set(item['matching_existing_members']);require(targets, 'Authentic recovery must reuse exact existing art')
        source_sha=item['candidate']['image_sha256'] if 'candidate' in item else item['candidate_sha256']
        if 'source_book_id' in item:
            require(bid=='1500015' and item['source_book_id']=='6901' and targets=={'gl_ff.png'}
                    and old_icon_index[str(book_index['6901'][ICON])][FILENAME]=='gl_ff.png', 'Named regional recovery source identity differs')
        require(all(target in old[4] and sha(old[4][target])==source_sha for target in targets),
                'Authentic recovery raw source identity differs')
        expected_icons[icon]=targets
    require({str(row['id']) for row in plan['icon_rows']}==set(expected_icons), 'Unrequested/missing icon remap')
    for icon,targets in expected_icons.items():
        require(new_icon_index[icon][FILENAME] in targets, 'Icon does not bind exact approved source')
    require(len(plan['members'])==658 and {item['name'] for item in plan['members']}==set(expected_geometry),
            'CPK transformations exceed exact608 fits and50 wrappers')
    work=ROOT/'audit/exact_geometry_sources';work.mkdir(parents=True,exist_ok=True)
    geometry_records=[]
    for item in plan['members']:
        member=item['name'];expected=expected_geometry[member]
        require(item['operation']==('add' if member in additions else 'replace'), 'Wrong finite member operation')
        require(set(map(str,item['book_ids']))==expected['book_ids'], 'Finite banner owners/aliases differ')
        candidate=pinned_file(item['candidate'])
        require(item['candidate']['width']==640 and item['candidate']['height']==240, 'Native canvas receipt differs')
        require(re.fullmatch(r'[A-Za-z0-9_.-]+',member), 'Unsafe geometry output name')
        source_path=work/member;source_path.write_bytes(expected['source'])
        if member in wrapper_names:
            from PIL import Image
            with Image.open(io.BytesIO(expected['source'])) as image:
                require(image.format=='PNG' and image.size==(600,120), 'Genuine wrapper source dimensions differ')
                original_rgba=image.convert('RGBA')
                canvas=Image.new('RGBA',(640,240),(0,0,0,0));canvas.paste(original_rgba,(20,60))
            with Image.open(io.BytesIO(candidate)) as image:
                require(image.format=='PNG' and image.size==(640,240) and image.mode=='RGBA'
                        and image.tobytes()==canvas.tobytes(), 'Wrapper changed original RGBA pixels or transparent padding')
        geometry_records.append({'name':member,'source_file':str(source_path),'source_bytes':len(expected['source']),
            'mode':expected.get('mode','fit'),
            'source_sha256':sha(expected['source']),'source_archive':expected['source_archive'],'source_member':expected['source_member'],
            'candidate_file':item['candidate']['local_path'],'candidate_bytes':len(candidate),'candidate_sha256':sha(candidate)})
    geometry_input=ROOT/'audit/GEOMETRY_QUALIFICATION_INPUT.json';geometry_output=ROOT/'audit/GEOMETRY_QUALIFICATION.json'
    geometry_input.write_text(json.dumps({'schema':'ffbe-production208-geometry-input-v1','records':geometry_records},indent=2)+'\n',encoding='utf-8')
    geometry_driver=ROOT/'guard/verify_geometry.mjs'
    primitives.run_tool(['C:/Program Files/nodejs/node.exe',geometry_driver,geometry_input,geometry_output],ROOT/'audit/geometry_qualification.log')
    geometry=json.loads(geometry_output.read_bytes())
    require(geometry['passed'] and geometry['input_sha256']==file_sha(geometry_input)
            and len(geometry['records'])==658 and geometry['fit_count']==608 and geometry['wrapper_count']==50
            and all(row['exact_approved_formula_pixels'] for row in geometry['records']), 'Geometry verification incomplete')
    cpk_receipt=verify_cpk_preservation(old,new,plan['members'])
    require(cpk_receipt['added_members']==470 and cpk_receipt['replaced_members']==188
            and cpk_receipt['unchanged_original_raw_members']==373 and cpk_receipt['candidate_members']==1031, 'Exact CPK differential counts differ')
    for member in protected_names|{'side_book_7032.png','side_book_7074.png','side_book_7075.png'}|{r[1] for r in PLACEHOLDER_EXTENSION.values()}:
        require(old[4][member]==new[4][member], 'Protected inset/Dark Visions member changed: '+member)
    for bid in protected_ids|{str(row[BOOK]) for row in books if str(row[SEASON]) not in {'70','71','92'}}:
        icon=str(book_index[bid][ICON])
        require(old_icon_index[icon]==new_icon_index[icon], 'Protected main/Dark Visions icon binding changed')
    genuine=set(proposal['genuine_generic_ids'])|{bid for group in proposal['genuine_group_owners'].values() for bid in group}
    require(not(genuine&fallback_ids), 'Approved genuine regional/original ownership was replaced by fallback')
    for bid in genuine:
        icon=str(book_index[bid][ICON]);require(old_icon_index[icon]==new_icon_index[icon], 'Genuine owner icon changed')
    require(all(new_icon_index[str(row[ICON])][FILENAME] in new[4] for row in books), 'Current book/icon/archive join is incomplete')
    for record in wrappers['records']:
        require(old[4][record['old_member']]==new[4][record['old_member']], 'Original genuine600x120 image changed')
    files={name:{'bytes':len(after),'sha256':sha(after)},icon_name:{'bytes':len(candidate_icon),'sha256':sha(candidate_icon)}}
    return files,{'CPK':cpk_receipt,'icon_operations':icon_receipt,'all1004_book_icon_joins_closed':all(
        new_icon_index[str(row[ICON])][FILENAME] in new[4] for row in books),
        'geometry_report':str(geometry_output),'geometry_report_sha256':file_sha(geometry_output),
        'geometry_driver_sha256':file_sha(geometry_driver),'original594_source_proposal_sha256':PROPOSAL_SHA,
        'finite_source_proposal_sha256':proposal['_active_proposal_sha256'],
        'protected_Dark_Visions_books':66,'main101_bindings_and_raw_images_preserved':True,
        'original_inset7032_7074_7075_bytes_preserved':True,'authentic_recoveries':7,'fallback_sources':597,
        'additional_exact_P5_placeholder_ids':sorted(PLACEHOLDER_EXTENSION),'additional_P5_source_members_preserved':True,
        'additional_placeholder_source_audit_sha256':PLACEHOLDER_EXTENSION_SHA,
        'native_canvas_wrapper_plan_sha256':WRAPPER_PLAN_SHA,'native_canvas_source_audit_sha256':WRAPPER_AUDIT_SHA,
        'unchanged_pixel_wrappers':50,'exact_original_RGBA_pixels_at20_60':True,'all50_original_genuine_raw_images_preserved':True}

def qualify_transports(payload, catalog, files, download_path, banner_path, ordering_path):
    plan=json.loads(Path(download_path).read_bytes())
    require(plan.get('schema')=='ffbe-production208-banner-download-plan-v1' and plan.get('passed') is True
            and plan['baseline_apk_sha256']==BASELINE_APK_SHA and plan['versionCode']==plan['asset_version']==208
            and plan['channel']=='production' and plan['original_content_rows']==plan['final_content_rows']==1898
            and plan['unchanged_original_rows']==1895 and plan['new_paths']==[]
            and set(plan['modified_original_paths'])==set(files), 'Exact208 download scope differs')
    require(plan['banner_plan_sha256']==file_sha(banner_path) and plan['ordering_plan_sha256']==file_sha(ordering_path),
            'Transport banner/order source pins differ')
    pack=plan['new_pack'];blob=pinned_file(pack)
    require(pack['name']==Path(pack['path']).name, 'Pack basename differs')
    identity=sha(json.dumps([{'path':name,'sha256':files[name]['sha256'],'bytes':files[name]['bytes']}
        for name in sorted(files)],sort_keys=True,separators=(',',':')).encode())
    require(plan['catalog_identity_sha256']==identity
            and re.fullmatch(r'(?:content|production-content|beta-content)-v208-'+identity[:16],plan['release_tag']),
            'Immutable208 data release does not bind exact raw identities')
    prefix='https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/'+plan['release_tag']+'/'
    require(re.fullmatch(r'[A-Za-z0-9_.-]*v208-'+sha(blob)[:16]+r'[.]pack',pack['name'])
            and pack['url']==prefix+pack['name'], 'Immutable208 pack identity/URL differs')
    require(len(plan['new_pack_files'])==len(files)==3, 'Expected exactly three changed raw-deflate slices')
    position=0;receipts=[]
    for item in plan['new_pack_files']:
        name=item['path'];require(name in files and name not in {r['path'] for r in receipts}, 'Duplicate/unlisted packed path')
        row=catalog[name]
        require(row['method']==8 and row['url']==pack['url'] and row['sourcebytes']==len(blob)
                and row['offset']==item['offset']==position and row['wirebytes']==item['wire_bytes'], 'Packed descriptor/source range differs')
        wire=blob[position:position+row['wirebytes']];position+=len(wire)
        require(len(wire)==row['wirebytes'] and sha(wire)==item['wire_sha256'], 'Wire slice pin differs')
        decoder=zlib.decompressobj(-15);raw=decoder.decompress(wire)+decoder.flush()
        require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail, 'Wire is not one complete raw-deflate stream')
        require(raw==(Path(payload)/name).read_bytes() and sha(raw)==files[name]['sha256']==row['sha256']==item['sha256']
                and len(raw)==files[name]['bytes']==row['bytes']==item['bytes'], 'Raw/source/catalog/download identity differs')
        receipts.append({'path':name,'offset':row['offset'],'wire_bytes':len(wire),'wire_sha256':sha(wire),
                         'raw_bytes':len(raw),'raw_sha256':sha(raw),'exact_prepared_source_bytes':True})
    require(position==len(blob) and [row['path'] for row in receipts]==sorted(files), 'Pack order or exact slice partition differs')
    release_files={row['role']:row for row in plan['files']}
    require(set(release_files)=={'pack','catalog','manifest'} and len(plan['files'])==3, 'Unlisted immutable release file')
    for row in release_files.values(): pinned_file(row)
    require(pinned_file(release_files['pack'])==blob, 'Published pack bytes differ')
    content=(Path(payload)/'content_delivery.tsv').read_bytes();side=(Path(payload)/'side_stories/manifest.tsv').read_bytes()
    require(pinned_file(release_files['catalog'])==content and plan['content_catalog_sha256']==sha(content)
            and plan['side_manifest_sha256']==sha(side), 'Published native metadata differs')
    require(release_files['catalog']['name']=='content_delivery-'+sha(content)[:16]+'.tsv'
            and release_files['manifest']['name']=='event-assets-'+identity[:16]+'.json', 'Public metadata basename identity differs')
    source_manifest=pinned_file(release_files['manifest']);manifest=json.loads(source_manifest)
    require(manifest['schema']=='ffbe-production208-banner-assets-v1'
            and manifest['source_build207_sha256']==BASELINE_APK_SHA and manifest['parent_asset_version']==206
            and manifest['source_patch5_sha256']=='534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
            and manifest['asset_version']==manifest['APK_min_version']==208 and manifest['channel']=='production'
            and manifest['package']=='com.square_enix.ffbejpn' and manifest['signing_certificate_sha256']==SIGNER_SHA,
            'Public production208 asset identity differs')
    with zipfile.ZipFile(BASELINE_APK) as baseline: base_sha=sha(baseline.read('assets/base_delivery.tsv'))
    require(manifest['base_catalog_unchanged_sha256']==plan['unchanged_base_catalog_sha256']==base_sha,
            'Base asset catalog identity changed')
    require(manifest['content_catalog']=={'url':prefix+release_files['catalog']['name'],'bytes':len(content),'sha256':sha(content)}
            and manifest['release_tag']==plan['release_tag'] and manifest['bundled_side_manifest_sha256']==sha(side),
            'Public manifest/native release linkage differs')
    prior_manifest_path=ROOT.parent/'v206-event-cleanup/asset_publication/event-assets-ac96f646eaa91996.json'
    require(file_sha(prior_manifest_path)=='f7b9926a2fb6f6c8000e9fe10618aa59e2778f0d5b45d67550638379631a8002',
            'Reused206 manifest seal differs')
    prior_manifest=json.loads(prior_manifest_path.read_bytes());old_assets={row['path']:row for row in prior_manifest['assets']}
    require(len(manifest['assets'])==1898 and [row['path'] for row in manifest['assets']]==list(catalog),
            'Public manifest path membership/order differs')
    for item in manifest['assets']:
        row=catalog[item['path']]
        expected={'url':row['url'],'offset':row['offset'],'wire_bytes':row['wirebytes'],'method':row['method'],'source_bytes':row['sourcebytes']}
        require(item['transport']==expected and item['sha256']==row['sha256'] and item['bytes']==row['bytes'],
                'Public asset record does not equal native descriptor')
        if item['path'] in files: require(item['version']==208, 'Changed asset version differs')
        else: require(item==old_assets[item['path']], 'Unrequested public per-asset metadata changed')
    return {'schema':'ffbe-production208-transport-qualification-v1','passed':True,
        'versionCode':208,'baseline_apk_sha256':BASELINE_APK_SHA,
        'content_catalog_sha256':sha(content),'side_manifest_sha256':sha(side),
        'banner_plan_sha256':file_sha(banner_path),'ordering_plan_sha256':file_sha(ordering_path),
        'download_plan_sha256':file_sha(download_path),'source_manifest_sha256':sha(source_manifest),
        'new_pack_sha256':sha(blob),'new_pack_bytes':len(blob),'exact_local_deflate_slices':receipts,
        'changed_descriptors':3,'unchanged_descriptor_count':1895,'unchanged1895_descriptors_byte_identical':True,
        'network_requested':False,'runtime_verified':False}

def qualify_content(payload, banner_path, ordering_path, download_path):
    validate_baseline();proposal=approved_proposal()
    with zipfile.ZipFile(BASELINE_APK) as baseline:
        catalog_blob=baseline.read('assets/content_delivery.tsv');side_blob=baseline.read('assets/side_stories/manifest.tsv')
    prior=parse_catalog(catalog_blob)
    codec_dir=Path('T:/Projects/FFBE Patch/story-ports/side-stories/scripts')
    sys.path.insert(0,str(codec_dir))
    from common import rows_bytes
    from cpk_convert import read_cpk
    banners=json.loads(Path(banner_path).read_bytes());ordering=json.loads(Path(ordering_path).read_bytes())
    protected=json.loads((ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json').read_bytes())
    files,original_books,candidate_books,order_receipt=qualify_ordering(payload,ordering,proposal,prior,rows_bytes,set(protected['book_ids']))
    art,art_receipt=qualify_banners(payload,banners,proposal,prior,rows_bytes,read_cpk,original_books)
    require(not(set(files)&set(art)), 'Duplicate raw payload declaration');files.update(art)
    expected={*files,'content_delivery.tsv','side_stories/manifest.tsv'}
    require({path.relative_to(payload).as_posix() for path in Path(payload).rglob('*') if path.is_file()}==expected,
            'Unlisted staged external payload file')
    content=(Path(payload)/'content_delivery.tsv').read_bytes();side=(Path(payload)/'side_stories/manifest.tsv').read_bytes()
    catalog,metadata=compare_metadata(catalog_blob,content,side_blob,side,files)
    transport=qualify_transports(payload,catalog,files,download_path,banner_path,ordering_path)
    report={'schema':'ffbe-production208-content-qualification-v1','passed':True,
        'versionCode':208,'baseline_apk_sha256':BASELINE_APK_SHA,'ordering':order_receipt,'banners':art_receipt,
        'metadata':metadata,'transport':transport,'content_catalog_sha256':sha(content),'side_manifest_sha256':sha(side),
        'banner_plan_sha256':file_sha(banner_path),'ordering_plan_sha256':file_sha(ordering_path),
        'download_plan_sha256':file_sha(download_path),'proposal_sha256':proposal['_active_proposal_sha256'],
        'original594_source_proposal_sha256':PROPOSAL_SHA,'placeholder_extension_sha256':PLACEHOLDER_EXTENSION_SHA,
        'guard_sha256':file_sha(__file__),'raw_payload':files,
        'codec_source_pins':{str(codec_dir/name):file_sha(codec_dir/name) for name in ['common.py','cpk_convert.py']},
        'native_or_Java_runtime_changed':False,'physical_phone_tested':False,'network_requested':False}
    output=ROOT/'audit/CONTENT_QUALIFICATION.json'
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    transport.update({'guard_sha256':file_sha(__file__),'content_qualification_sha256':file_sha(output)})
    transport_path=ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json'
    transport_path.write_text(json.dumps(transport,indent=2)+'\n',encoding='utf-8')
    return report

def qualified_content_for_apk(args):
    content_path=ROOT/'audit/CONTENT_QUALIFICATION.json'
    transport_path=ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json'
    require(content_path.is_file() and transport_path.is_file(), 'Run independent content/transport qualification first')
    content=json.loads(content_path.read_bytes());transport=json.loads(transport_path.read_bytes())
    require(content['passed'] and transport['passed'] and content['guard_sha256']==transport['guard_sha256']==file_sha(__file__)
            and transport['content_qualification_sha256']==file_sha(content_path), 'Independent content/transport receipt is stale')
    for field,path in [('banner_plan_sha256',args.banner_plan),('ordering_plan_sha256',args.ordering_plan),('download_plan_sha256',args.download_plan)]:
        require(content[field]==transport[field]==file_sha(path), 'Qualified content plan pin changed')
    for name,pin in content['raw_payload'].items():
        blob=(Path(args.payload_root)/name).read_bytes();require(len(blob)==pin['bytes'] and sha(blob)==pin['sha256'], 'Qualified raw payload changed')
    for name,field in [('content_delivery.tsv','content_catalog_sha256'),('side_stories/manifest.tsv','side_manifest_sha256')]:
        require(file_sha(Path(args.payload_root)/name)==content[field]==transport[field], 'Qualified native metadata changed')
    plan=json.loads(Path(args.download_plan).read_bytes())
    for row in plan['files']: pinned_file(row)
    return content,transport

def qualify_signed(args):
    validate_baseline();content,transport=qualified_content_for_apk(args)
    result=compare_apk_members(BASELINE_APK,args.apk)
    work=ROOT/'audit/signed_production_tools';work.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(BASELINE_APK) as old,zipfile.ZipFile(args.apk) as new:
        expected,receipt=expected_manifest(old.read('AndroidManifest.xml'))
        require(new.read('AndroidManifest.xml')==expected, 'Manifest changed beyond typed207→208 counter')
        result['manifest_delta']=receipt
        result['script_delta']=compare_script(old.read('assets/frida_script.js'),new.read('assets/frida_script.js'))
        script=work/'frida_script.js';script.write_bytes(new.read('assets/frida_script.js'))
        for member,file in [('assets/content_delivery.tsv','content_delivery.tsv'),('assets/side_stories/manifest.tsv','side_stories/manifest.tsv')]:
            require(new.read(member)==(Path(args.payload_root)/file).read_bytes(), 'Bundled metadata differs from exact qualified source')
    primitives.run_tool(['node','--check',script],work/'script_syntax.txt')
    tools=primitives.BUILD_TOOLS
    signed=primitives.run_tool(['java','-jar',tools/'lib/apksigner.jar','verify','--verbose','--print-certs',args.apk],work/'signature.txt')
    require('Signer #1 certificate SHA-256 digest: '+SIGNER_SHA in signed
            and 'Verified using v2 scheme (APK Signature Scheme v2): true' in signed, 'Signer/signature differs')
    badging=primitives.run_tool([tools/'aapt2.exe','dump','badging',args.apk],work/'package.txt')
    require("package: name='com.square_enix.ffbejpn' versionCode='208' versionName='11.1.1'" in badging, 'Package/version differs')
    primitives.run_tool([tools/'zipalign.exe','-c','-P','16','-v','4',args.apk],work/'alignment.txt')
    result.update({'schema':'ffbe-production208-qualification-v1','passed':True,
        'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'apk_sha256':file_sha(args.apk),'apk_bytes':Path(args.apk).stat().st_size,'versionCode':208,
        'versionName':'11.1.1','package':'com.square_enix.ffbejpn','baseline_apk_sha256':BASELINE_APK_SHA,
        'signer_sha256':SIGNER_SHA,'expected_js_delta_passed':True,
        'content_catalog_sha256':content['content_catalog_sha256'],'side_manifest_sha256':content['side_manifest_sha256'],
        'banner_plan_sha256':content['banner_plan_sha256'],'ordering_plan_sha256':content['ordering_plan_sha256'],
        'download_plan_sha256':content['download_plan_sha256'],'guard_sha256':file_sha(__file__),
        'content_qualification_sha256':file_sha(ROOT/'audit/CONTENT_QUALIFICATION.json'),
        'transport_qualification_sha256':file_sha(ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json'),
        'source_manifest_sha256':transport['source_manifest_sha256'],'new_pack_sha256':transport['new_pack_sha256'],
        'qualified_geometry_members':658,'proportional_fits':608,'unchanged_pixel_wrappers':50,
        'native_canvas_wrapper_plan_sha256':WRAPPER_PLAN_SHA,'icon_filename_only_operations':477,'native_Order_only_operations':599,
        'Dark_Visions66_main101_original_inset_covers_preserved':True,
        'Java_native_runtime_and_all10950_classes_byte_identical':True,'startup_and_all_dependencies_preserved':True,
        'qualification_tools':{str(path):file_sha(path) for path in [tools/'aapt2.exe',tools/'zipalign.exe',tools/'lib/apksigner.jar']},
        'device_actions':False,'network_requests':False,'physical_phone_tested':False,
        'BlueStacks_test':'Separate exact208 APK device receipt required for promotion.'})
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--content-only',action='store_true')
    parser.add_argument('--apk')
    parser.add_argument('--payload-root',default=str(ROOT/'payload'))
    parser.add_argument('--banner-plan',default=str(ROOT/'audit/BANNER_PLAN.json'))
    parser.add_argument('--ordering-plan',default=str(ROOT/'audit/ORDER_PLAN.json'))
    parser.add_argument('--download-plan',default=str(ROOT/'asset_publication/DOWNLOAD_PLAN.json'))
    parser.add_argument('--output',default=str(ROOT/'staged_build/SIGNED_PRODUCTION_QUALIFICATION.json'))
    args=parser.parse_args()
    require(args.content_only or args.apk, 'Exact APK path required')
    try:
        if args.content_only:
            report=qualify_content(Path(args.payload_root),Path(args.banner_plan),Path(args.ordering_plan),Path(args.download_plan))
            print(json.dumps({'passed':True,'transport_report':str(ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json'),
                'catalog_sha256':report['content_catalog_sha256'],'side_manifest_sha256':report['side_manifest_sha256']}))
            return 0
        report=qualify_signed(args)
    except Exception as exc:
        report={'schema':'ffbe-production208-qualification-v1','passed':False,'error':str(exc),'guard_sha256':file_sha(__file__)}
        if args.apk and Path(args.apk).is_file():report.update(apk_sha256=file_sha(args.apk),apk_bytes=Path(args.apk).stat().st_size)
        if args.content_only:
            (ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(report));return 1
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:report[key] for key in ['passed','apk_sha256','apk_bytes','error'] if key in report}))
    return 0 if report['passed'] else 1

def validate_baseline():
    require(file_sha(primitives.__file__)==PRIMITIVES_SHA,'Copied207 primitive source differs')
    require(file_sha(BASELINE_APK)==BASELINE_APK_SHA,'Baseline is not the qualified207 APK')
    prior=ROOT.parent/'v207-download-spacing/staged_build/SIGNED_SPACING_QUALIFICATION.json'
    require(file_sha(prior)==BASELINE_QUALIFICATION_SHA,'Signed207 qualification seal differs')
    report=json.loads(prior.read_bytes())
    require(report['passed'] and report['apk_sha256']==BASELINE_APK_SHA and report['versionCode']==207,'Signed207 baseline is unqualified')
    for path,pin in [(ROOT/'audit/ALL_EVENT_BANNER_INVENTORY.json',INVENTORY_SHA),
                     (ROOT/'audit/DARK_VISIONS_PRESERVATION_SCOPE.json',DARK_VISIONS_SCOPE_SHA)]:
        require(file_sha(path)==pin,'Independent banner inventory/protection seal differs')

def compare_apk_members(baseline,candidate):
    with zipfile.ZipFile(baseline) as old,zipfile.ZipFile(candidate) as new:
        require(old.testzip() is None and new.testzip() is None,'APK ZIP CRC failure')
        for z in (old,new):require(len(z.namelist())==len(set(z.namelist())),'Duplicate APK ZIP member')
        require(old.namelist()==new.namelist(),'APK full member names/order changed')
        names=[n for n in old.namelist() if not primitives.signature(n)]
        require(len(names)==312,'Unexpected207 nonsigning member count')
        assets=[n for n in names if n.startswith('assets/') and not n.endswith('/')]
        require(len(assets)==170,'Startup/original170 asset membership changed')
        changed,preserved,natives=[],[],[]
        for name in names:
            a,b=old.getinfo(name),new.getinfo(name)
            require(a.compress_type==b.compress_type,'APK compression method changed: '+name)
            ab,bb=old.read(name),new.read(name)
            if ab!=bb:
                require(name in ALLOWED_APK_MEMBERS,'Unrequested APK member changed: '+name)
                changed.append({'path':name,'before_sha256':sha(ab),'after_sha256':sha(bb),
                                'before_bytes':len(ab),'after_bytes':len(bb)})
            else:
                require(primitives.compressed_blob(old,a)==primitives.compressed_blob(new,b),
                        'Unchanged APK member recompressed: '+name)
                preserved.append(name)
            if name.endswith('.so'):
                require(ab==bb,'Native library changed: '+name)
                natives.append({'path':name,'bytes':len(bb),'sha256':sha(bb)})
        require({r['path'] for r in changed}==ALLOWED_APK_MEMBERS,'Expected exactlyfour application-member changes')
        require(len(natives)==8,'Native library inventory differs')
        require(sha(new.read('classes.dex'))==BASELINE_DEX_SHA,'Frozen runtime DEX pin differs')
        return {'changed_members':changed,'unchanged_member_count':len(preserved),
            'raw_compressed_preserved_members':preserved,'asset_files':170,'unchanged_asset_files':167,
            'native_libraries':natives,'runtime_dex_sha256':BASELINE_DEX_SHA,'all10950_classes_preserved':True,
            'new_or_removed_members':0}

def expected_manifest(original):
    result=bytearray(original);offset=8;names=None;positions=[]
    require(len(result)>=8 and struct.unpack_from('<I',result,4)[0]==len(result),'Invalid AXML size')
    while offset<len(result):
        kind,header,size=struct.unpack_from('<HHI',result,offset)
        require(size>=header>=8 and offset+size<=len(result),'Invalid AXML chunk')
        if kind==1:names=primitives.pool_strings(result[offset:offset+size])
        if kind==0x102:
            require(names is not None,'Missing AXML pool')
            tag=struct.unpack_from('<I',result,offset+header+4)[0]
            if names[tag]=='manifest':
                start,width,count=struct.unpack_from('<HHH',result,offset+header+8)
                for i in range(count):
                    p=offset+header+start+i*width;name=struct.unpack_from('<I',result,p+4)[0]
                    if names[name]=='versionCode':
                        require(result[p+15]==16 and struct.unpack_from('<I',result,p+16)[0]==207,'Expected typed versionCode207')
                        struct.pack_into('<I',result,p+16,208);positions.append(p+16)
        offset+=size
    require(offset==len(result) and len(positions)==1,'Ambiguous versionCode')
    return bytes(result),{'value_offset':positions[0],'before':207,'after':208,'typed_four_byte_value_only':True}

def expected_script(original):
    require(sha(original)==BASELINE_SCRIPT_SHA,'Unqualified207 script')
    result=original
    for old,new in SCRIPT_OPERATIONS:
        before,after=old.encode(),new.encode()
        require(result.count(before)==1,'Ambiguous release constant: '+old)
        result=result.replace(before,after)
    return result

def compare_script(original,candidate):
    require(candidate==expected_script(original),'Frida changes exceed three literal production constants')
    return {'expected_js_delta_passed':True,'finite_literal_constant_changes':3,
        'counter_before':207,'counter_after':208,'production_updater_and_download_urls_restored_to_literal_Patch5_routes':True,
        '207_download_counter_spacing_predicate_preserved':True,'all_hooks_and_other_display_rules_byte_identical':True,
        'party_movie_lifecycle_startup_unchanged':True}

if __name__=='__main__':
    raise SystemExit(main())
