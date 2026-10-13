"""Qualify literal production Patch 5 plus only additive event delivery.

This policy deliberately does not import the 203/204 release guard. Its trust
anchor is the actual production APK, not a recompiled or extracted baseline.
"""
from pathlib import Path
import argparse, collections, copy, datetime, hashlib, importlib.util, json, re
import struct, subprocess, sys, urllib.parse, zipfile

BASELINE_SHA = '534a3ddd18de17ce22db3ab822127308d5463f55f61e2c8e506e50b05875e208'
CONTENT_SOURCE_SHA = '54c93c7562a14155db04a87ce5d94c817e797ef19014b3ce95332c938537b4c7'
SOURCE_GRAPH_SHA = 'b9dd01852a5210476fd0096e60ba491638a4e5527320b62051532c7d4d5e08f8'
DEPENDENCY_LEDGER_SHA = 'b9602984c382ae24322363e6205f88096b5be287dab3dad315d724066c9d3495'
SIGNER_SHA = '21aef3a4ddee69c63062fa15d3d6872918addb2a65d07f4e104dcfcf5ba9d6ee'
ALLOWED_MEMBERS = frozenset(('AndroidManifest.xml', 'classes.dex',
    'assets/frida_script.js', 'assets/content_delivery.tsv', 'assets/side_stories/manifest.tsv'))
ALLOWED_CLASSES = frozenset(('O1/ExtraContent$Entry.smali', 'O1/SideStoryTables.smali'))
UPDATER_URL = 'https://raw.githubusercontent.com/luminest-llc/ffbe-memorial-downloads/beta/channels/beta/patch_version.json'
DOWNLOAD_URL = 'https://ffbe.luminest.io/downloads/beta/'
CLASS_PINS = {
    'O1/ExtraContent$Entry.smali': '259c30849a729880005884265eac9f2f0be5da39c7e149010ce7662d415aa5f9',
    'O1/SideStoryTables.smali': '5977ecd452a81b531e4c2a69df689c48caa2645509c69fd771fa38d29252c697',
}
CORE = {'D2zaT7Ru':'2ShgIRU8', 'Nm36woZx':'M9mwe2cu',
        '9Zdr5ap0':'vG1hSm79', 'IL78hX09':'VMkv7S9R'}
EXPECTED_TABLES = frozenset(('D2zaT7Ru','Nm36woZx','9Zdr5ap0','IL78hX09','YW9MUm2H',
    '91vNbdxg','B7LnP2TH','24Eka6wL','1Bj4oy5Q','Fvix6V0n','LM1APs6u',
    'YW9MUm2H-legacy','bqR4p8SN','Wg1a5VJR','9mS1TPFJ'))
HASH = re.compile(r'[a-f0-9]{64}\Z')
SAFE_SIDE = re.compile(r'side_stories/(?:[A-Za-z0-9_.-]+|r2_scene_(?:jp|gl)/[a-f0-9]{16}/[A-Za-z0-9_.-]+[.]cpk)\Z')

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
        return f.read(info.compress_size)

def compare_members(baseline, candidate):
    """Every unlisted member keeps its raw compressed payload and compression."""
    with zipfile.ZipFile(baseline) as src, zipfile.ZipFile(candidate) as dst:
        require(dst.testzip() is None, 'Candidate ZIP CRC failure')
        for z in (src, dst):
            require(len(z.namelist()) == len(set(z.namelist())), 'Duplicate APK ZIP member')
        old = {n for n in src.namelist() if not signature(n)}
        new = {n for n in dst.namelist() if not signature(n)}
        require(old == new, 'APK member addition/removal: ' + str(sorted(old ^ new)))
        require(len([n for n in old if n.startswith('assets/') and not n.endswith('/')]) == 170,
                'Baseline must contain exactly 170 asset files')
        changed, preserved, natives = [], [], []
        for name in sorted(old):
            a, b = src.getinfo(name), dst.getinfo(name)
            before, after = src.read(name), dst.read(name)
            require(a.compress_type == b.compress_type, 'Compression changed: ' + name)
            if before != after:
                require(name in ALLOWED_MEMBERS, 'Unlisted APK member changed: ' + name)
                changed.append({'path':name, 'before_sha256':sha(before), 'after_sha256':sha(after),
                                'before_bytes':len(before), 'after_bytes':len(after)})
            else:
                require(compressed_blob(src,a) == compressed_blob(dst,b), 'Raw ZIP data changed: ' + name)
                preserved.append(name)
            if name.endswith('.so'):
                require(before == after, 'Native library changed: ' + name)
                natives.append({'path':name, 'sha256':sha(before), 'bytes':len(before)})
        require({r['path'] for r in changed} == ALLOWED_MEMBERS, 'Expected exactly five necessary member changes')
        return {'changed_members':changed, 'unchanged_member_count':len(preserved),
                'asset_files':170, 'native_libraries':natives, 'new_or_removed_members':0}

def pool_strings(chunk):
    header = struct.unpack_from('<H', chunk, 2)[0]
    count, _, flags, start, _ = struct.unpack_from('<5I', chunk, 8)
    result = []
    for i in range(count):
        pos = start + struct.unpack_from('<I', chunk, header + 4*i)[0]
        if flags & 0x100:
            def length(p):
                v = chunk[p]
                return (((v & 127)<<8)|chunk[p+1],p+2) if v & 128 else (v,p+1)
            _, pos = length(pos)
            n, pos = length(pos)
            result.append(chunk[pos:pos+n].decode('utf-8'))
        else:
            n = struct.unpack_from('<H',chunk,pos)[0]
            pos += 2
            if n & 0x8000:
                n = ((n&0x7fff)<<16)|struct.unpack_from('<H',chunk,pos)[0]
                pos += 2
            result.append(chunk[pos:pos+n*2].decode('utf-16-le'))
    return result

def expected_manifest(original):
    result = bytearray(original)
    offset, names, positions = 8, None, []
    require(len(result) >= 8 and struct.unpack_from('<I', result,4)[0] == len(result), 'Invalid AXML size')
    while offset < len(result):
        kind, header, size = struct.unpack_from('<HHI', result, offset)
        require(size >= header >= 8 and offset+size <= len(result), 'Invalid AXML chunk')
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
                        require(result[p+15] == 16 and struct.unpack_from('<I',result,p+16)[0] == 199,
                                'Baseline versionCode must be typed integer 199')
                        struct.pack_into('<I',result,p+16,205)
                        positions.append(p+16)
        offset += size
    require(offset == len(result) and len(positions) == 1, 'Ambiguous AXML versionCode')
    return bytes(result), {'versionCode_offset':positions[0], 'before':199, 'after':205,
                          'only_four_byte_value_replaced':True}

def expected_script(original, party_book_ids):
    text = original.decode('utf-8')
    marker = 'const SIDE_STORY_PARTIES = '
    require(text.count(marker) == 1, 'Ambiguous party map')
    start = text.index(marker)+len(marker)
    parties, length = json.JSONDecoder().raw_decode(text[start:])
    require(len(parties['books']) == 85 and len(parties['entries']) == 2177, 'Original party identities differ')
    require(len(party_book_ids) == len(set(map(str,party_book_ids))), 'Duplicate new party book IDs')
    added = []
    for book in party_book_ids:
        key = str(book)
        require(key not in parties['books'], 'Party marker already belongs to original book: '+key)
        parties['books'][key] = []
        added.append(key)
    text = text[:start]+json.dumps(parties,separators=(',',':'),ensure_ascii=False)+text[start+length:]
    changes = {
        'const PATCH_VERSION = 5;':'const PATCH_VERSION = 205;',
        'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/patch_version.json':UPDATER_URL,
        'const DOWNLOAD_URL   = "https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest";':
            'const DOWNLOAD_URL   = "'+DOWNLOAD_URL+'";',
    }
    for before, after in changes.items():
        require(text.count(before) == 1, 'Missing/ambiguous original updater constant')
        text = text.replace(before,after)
    return text.encode('utf-8'), {'added_party_book_count':len(added), 'added_party_book_ids':added,
                                 'original_party_entries_preserved':2177, 'other_script_bytes_preserved':True}

def compare_script(original, candidate, party_book_ids):
    expected, receipt = expected_script(original, party_book_ids)
    require(candidate == expected, 'Script changed beyond added party markers and three beta constants')
    return receipt

def parse_catalog(blob):
    lines = blob.decode('utf-8').splitlines()
    require(lines and lines[0] == 'ffbe-content-v1', 'Content catalog header differs')
    result = {}
    for line in lines[1:]:
        parts = line.split('\t')
        require(len(parts) == 8, 'Catalog must use original eight-field contract')
        path, digest, rawbytes, url, offset, wirebytes, method, sourcebytes = parts
        require(path not in result and '..' not in path and not path.startswith('/'), 'Unsafe/duplicate catalog path')
        require(bool(HASH.fullmatch(digest)), 'Invalid catalog hash')
        nums = list(map(int,(rawbytes,offset,wirebytes,method,sourcebytes)))
        require(nums[0] > 0 and nums[1] >= 0 and nums[2] > 0 and nums[3] in (0,8)
                and nums[4] > 0 and nums[1]+nums[2] <= nums[4], 'Invalid catalog sizes/range')
        result[path] = {'parts':parts, 'line':line, 'sha256':digest, 'bytes':nums[0], 'url':url,
                        'offset':nums[1], 'wirebytes':nums[2], 'method':nums[3], 'sourcebytes':nums[4]}
    return result

def immutable_transport(row):
    u = urllib.parse.urlsplit(row['url'])
    require(u.scheme == 'https' and u.netloc == 'github.com' and u.username is None,
            'Event transport must be immutable HTTPS GitHub release')
    require(re.fullmatch(r'/luminest-llc/ffbe-memorial-downloads/releases/download/[^/]+/[^/]+',u.path)
            and '/latest/' not in u.path and not u.query, 'Event transport must pin an immutable release asset')
    if u.fragment:
        m = re.fullmatch(r'ffbe-range=(\d+):(\d+):(\d+)',u.fragment)
        require(m is not None, 'Invalid GitHub range fragment')
        start, length, total = map(int,m.groups())
        require(length == row['sourcebytes'] and start+length <= total and length > 0,
                'GitHub range must cover source bytes exactly')
    require(row['method'] != 0 or row['wirebytes'] == row['bytes'], 'Stored asset raw/wire sizes differ')

def payload_inventory(payload, plan):
    require(plan.get('schema') == 'ffbe-patch5-events-payload-v1', 'Unsupported event plan')
    files = {}
    for row in plan['payload_files']:
        name = row.get('relative_path', row.get('path'))
        if name in ('side_stories/manifest.tsv','content_delivery.tsv'):
            continue
        require(name not in files and bool(SAFE_SIDE.fullmatch(name)) and '..' not in name, 'Unlisted/unsafe event payload path')
        blob = (Path(payload)/name).read_bytes()
        require(len(blob) == int(row['bytes']) and sha(blob) == row['sha256'], 'Staged payload pin mismatch: '+name)
        files[name] = row
    require(files, 'Empty event payload')
    return files

def compare_catalog(original, candidate, files):
    old, new = parse_catalog(original), parse_catalog(candidate)
    require(len(old) == 1411, 'Original catalog must contain 1411 rows')
    require(set(old) <= set(new), 'Original catalog rows removed')
    require(set(new)-set(old) <= set(files), 'Unlisted catalog path added')
    receipts = []
    for name,row in new.items():
        if name not in files:
            require(name in old and row['line'] == old[name]['line'], 'Non-event catalog row changed: '+name)
            continue
        planned = files[name]
        require(row['sha256'] == planned['sha256'] and row['bytes'] == int(planned['bytes']), 'Catalog payload pin mismatch: '+name)
        if name in old and planned.get('baseline_sha256'):
            require(old[name]['sha256'] == planned['baseline_sha256'], 'Wrong original event hash receipt: '+name)
        immutable_transport(row)
        if name not in old or row['line'] != old[name]['line']:
            receipts.append({'path':name, 'before':old.get(name,{}).get('parts'), 'after':row['parts']})
    require(set(files) <= set(new), 'Required event payload missing from catalog')
    require([p for p in new if p in old] == list(old), 'Original catalog order changed')
    return new, {'original_rows_preserved':len(old), 'event_catalog_changes':receipts,
                 'added_rows':len(new)-len(old), 'total_rows':len(new)}

def parse_side_manifest(blob):
    result = {}
    for line in blob.decode('utf-8').splitlines():
        p = line.split('\t')
        require(len(p) in (3,4) and p[0] not in result, 'Invalid/duplicate side-story manifest row')
        require(bool(SAFE_SIDE.fullmatch('side_stories/'+p[0])) and '..' not in p[0], 'Unsafe side-story name')
        require(bool(HASH.fullmatch(p[1])), 'Invalid current side-story hash')
        accepted = set(filter(None,p[2].split(',')))
        require(all(HASH.fullmatch(h) for h in accepted), 'Invalid accepted side-story hash')
        variants = {}
        if len(p) == 4 and p[3]:
            for pair in p[3].split(','):
                h,name = pair.split('=',1)
                require(HASH.fullmatch(h) and bool(SAFE_SIDE.fullmatch('side_stories/'+name))
                        and '..' not in name and h not in variants, 'Unsafe/duplicate side-story variant')
                variants[h] = name
        result[p[0]] = {'line':line,'sha256':p[1], 'accepted':accepted,'variants':variants}
    return result

def compare_side_manifest(original, candidate, files, catalog, frozen=None):
    old, new = parse_side_manifest(original), parse_side_manifest(candidate)
    source=parse_side_manifest(frozen) if frozen is not None else None
    require(len(old) == 1370 and set(old) <= set(new), 'Original side-story manifest row removed')
    receipts = []
    for name,row in new.items():
        path = 'side_stories/'+name
        if path not in files:
            require(name in old and row['line'] == old[name]['line'], 'Unlisted side-story metadata changed: '+name)
        else:
            require(row['sha256'] == files[path]['sha256'] == catalog[path]['sha256'], 'Manifest/catalog current hash differs: '+name)
            if name in old:
                require(old[name]['accepted'] <= row['accepted'], 'Original accepted hashes lost: '+name)
                require(old[name]['sha256'] in row['accepted'], 'Original current hash no longer accepted: '+name)
                require(row['accepted']==old[name]['accepted']|{old[name]['sha256']},'Unlisted accepted hash added: '+name)
                require(row['variants']==old[name]['variants'], 'Original variant mapping changed: '+name)
                expected=old[name]['line'].split('\t')
                expected[1],expected[2]=files[path]['sha256'],','.join(sorted(old[name]['accepted']|{old[name]['sha256']}))
                require(row['line']=='\t'.join(expected),'Original manifest differs from exact event hash update: '+name)
            elif source is not None:
                require(name in source,'New side-story row lacks frozen metadata: '+name)
                expected=source[name]['line'].split('\t');expected[1]=files[path]['sha256']
                require(row['line']=='\t'.join(expected),'New side-story metadata differs from frozen event row: '+name)
            if name not in old or row['line'] != old[name]['line']:
                receipts.append({'path':path,'before':old.get(name,{}).get('line'),'after':row['line']})
        for variant in row['variants'].values():
            require('side_stories/'+variant in catalog, 'Manifest variant missing catalog metadata: '+variant)
    require({p.removeprefix('side_stories/') for p in files} <= set(new), 'Event payload missing manifest row')
    require([p for p in new if p in old] == list(old), 'Original side-story manifest order changed')
    return {'original_rows_preserved':len(old), 'side_manifest_changes':receipts,'total_rows':len(new)}

def compare_rows(original, candidate, keys, planned_added=None):
    require(keys and len(candidate) >= len(original), 'Invalid table primary keys or row removal')
    def key(r):
        return tuple(str(r[k]) for k in keys)
    oldids, newids = [key(r) for r in original], [key(r) for r in candidate]
    require(len(set(oldids)) == len(oldids) and len(set(newids)) == len(newids), 'Duplicate table primary key')
    require(candidate[:len(original)] == original, 'Original master rows/fields/order changed')
    added = newids[len(oldids):]
    if planned_added is not None:
        expected = [tuple(map(str,x)) if isinstance(x,(list,tuple)) else (str(x),) for x in planned_added]
        require(added == expected, 'Added table identity/order differs from plan')
    return {'baseline_rows':len(original),'candidate_rows':len(candidate),'added_rows':len(added),
            'original_rows_and_order_preserved':True, 'added_ids':[x[0] if len(x)==1 else list(x) for x in added]}

def reference_closure(tables, baseline_counts):
    seasons = {str(r['2ShgIRU8']):r for r in tables['D2zaT7Ru']}
    books = {str(r['M9mwe2cu']):r for r in tables['Nm36woZx']}
    maps = {str(r['vG1hSm79']):r for r in tables['9Zdr5ap0']}
    childbooks, childmaps, childentries = collections.Counter(), collections.Counter(), collections.Counter()
    for r in tables['Nm36woZx'][baseline_counts['Nm36woZx']:]:
        require(str(r['2ShgIRU8']) in seasons, 'Added book has missing season')
        childbooks[str(r['2ShgIRU8'])] += 1
    for r in tables['9Zdr5ap0'][baseline_counts['9Zdr5ap0']:]:
        book = books.get(str(r['M9mwe2cu']))
        require(book is not None and str(book['2ShgIRU8']) == str(r['2ShgIRU8']), 'Added map has missing/mismatched book/season')
        childmaps[str(r['M9mwe2cu'])] += 1
    for r in tables['IL78hX09'][baseline_counts['IL78hX09']:]:
        parent = maps.get(str(r['vG1hSm79']))
        require(parent is not None and all(str(parent[k]) == str(r[k]) for k in ('M9mwe2cu','2ShgIRU8')),
                'Added playback has missing/mismatched map/book/season')
        childentries[str(r['vG1hSm79'])] += 1
    for stem, field, children in (('D2zaT7Ru','2ShgIRU8',childbooks),('Nm36woZx','M9mwe2cu',childmaps),('9Zdr5ap0','vG1hSm79',childentries)):
        for r in tables[stem][baseline_counts[stem]:]:
            require(children[str(r[field])] > 0, 'Added record has no reachable child: '+stem)
    return {'added_parent_references_valid':True, 'all_added_seasons_books_maps_have_children':True,
            'added_playback_count':len(tables['IL78hX09'])-baseline_counts['IL78hX09']}

def load_source(source):
    if 'archive' in source:
        archive = Path(source['archive'])
        with zipfile.ZipFile(archive) as z:
            return z.read(source['member'])
    return Path(source.get('file',source.get('path'))).read_bytes()

def production_table(stem, baseline_apk, content_apk, project):
    """Derive original source from pinned P5 archives or its signed base metadata."""
    with zipfile.ZipFile(content_apk) as source:
        for folder in ('side_stories','story_ports','battle','encyclopedia','memory_room'):
            member='assets/'+folder+'/'+stem+'.dat'
            if member in source.namelist():
                blob=source.read(member)
                if folder == 'side_stories':
                    rows=parse_side_manifest(source.read('assets/side_stories/manifest.tsv'))
                    require(rows[stem+'.dat']['sha256'] == sha(blob),'P5 content source manifest mismatch')
                return blob
    with zipfile.ZipFile(baseline_apk) as source:
        rows=[line.split('\t') for line in source.read('assets/base_delivery.tsv').decode().splitlines()[1:]]
    matches=[r for r in rows if len(r)==5 and r[1] == stem+'.dat']
    require(len(matches)==1,'Missing original signed base metadata for table: '+stem)
    pack,name,size,digest,_=matches[0]
    require('/' not in pack and '..' not in pack,'Invalid base pack name')
    path=Path(project)/'localization-rounds/2026-09-25-download-recovery/base-source'/pack/'199/199/assets'/name
    blob=path.read_bytes()
    require(len(blob)==int(size) and sha(blob)==digest,'P5 signed base table pin differs: '+stem)
    return blob

def qualify_tables(payload, plan, decoder, baseline_resolver=None):
    reports, tables, counts, expected_tables = {}, {}, {}, {}
    require({r['stem'] for r in plan['table_provenance']} == EXPECTED_TABLES
            and len(plan['table_provenance']) == len(EXPECTED_TABLES), 'Event master/dependency table inventory differs')
    for row in plan['table_provenance']:
        stem = row['stem']
        before = load_source(row['baseline_source'])
        if baseline_resolver is not None:
            require(before == baseline_resolver(stem),'Plan table source is not the original P5 source: '+stem)
        after = (Path(payload)/row['candidate_relative_path']).read_bytes()
        expected = row.get('baseline_sha256',row['baseline_source'].get('sha256'))
        if expected:
            require(sha(before) == expected, 'Baseline table pin mismatch: '+stem)
        decode_stem=row.get('decode_stem',stem)
        a,b = decoder(before,decode_stem),decoder(after,decode_stem)
        keys = row.get('primary_key_fields') or [row['primary_key']]
        reports[stem] = compare_rows(a,b,keys,row.get('added_ids'))
        require(len(a) == row['baseline_rows'] and len(b)-len(a) == row['added_rows'], 'Table row count differs from plan: '+stem)
        reports[stem].update({'baseline_raw_sha256':sha(before),'candidate_raw_sha256':sha(after), 'primary_key_fields':keys})
        tables[stem],counts[stem] = b,len(a)
        current_blob=load_source(row['candidate_source'])
        require(sha(current_blob) == row['candidate_source']['sha256'] and len(current_blob) == row['candidate_source']['bytes'],
                'Frozen table source pin differs: '+stem)
        current=decoder(current_blob,decode_stem)
        identity=lambda r:tuple(str(r[k]) for k in keys)
        oldids={identity(r) for r in a}
        appended=[copy.deepcopy(r) for r in current if identity(r) not in oldids]
        if stem in ('Nm36woZx','9Zdr5ap0','IL78hX09'):
            if stem == 'IL78hX09':
                omitted=[r for r in appended if str(r['M9mwe2cu']) == '1550000']
                signature=lambda r:tuple(str(r[k]) for k in ('89EvGKHx','6uIYE15X','tse2kWp6','8aVAUgN5','V2mCH5UR'))
                require(len(omitted)==18 and all(signature(r) in {signature(x) for x in a} for r in omitted),
                        'Omitted Greetings aggregation is not an exact original scene duplicate')
            appended=[r for r in appended if str(r['M9mwe2cu']) != '1550000']
        if stem == 'LM1APs6u':
            appended=[r for r in appended if str(r['0HUPxDf1']) != '151550000']
        expected_tables[stem]=a+appended
    require(set(CORE) <= set(tables), 'All four event master tables are required')
    # Restore original parent IDs, then attach only new children to those parents.
    books={str(r['M9mwe2cu']):r for r in expected_tables['Nm36woZx']}
    for r in expected_tables['9Zdr5ap0'][counts['9Zdr5ap0']:]:
        require(str(r['M9mwe2cu']) in books,'Frozen new map parent missing')
        r['2ShgIRU8']=books[str(r['M9mwe2cu'])]['2ShgIRU8']
    maps={str(r['vG1hSm79']):r for r in expected_tables['9Zdr5ap0']}
    for r in expected_tables['IL78hX09'][counts['IL78hX09']:]:
        require(str(r['vG1hSm79']) in maps,'Frozen new playback parent missing')
        for key in ('M9mwe2cu','2ShgIRU8'):
            r[key]=maps[str(r['vG1hSm79'])][key]
    for stem,expected in expected_tables.items():
        require(tables[stem] == expected,'Candidate differs from exact original-plus-missing-events formula: '+stem)
    relations = reference_closure(tables,counts)
    addedbooks = [str(r['M9mwe2cu']) for r in tables['Nm36woZx'][counts['Nm36woZx']:]]
    require(addedbooks == list(map(str,plan['new_book_ids'])), 'New book ID list differs')
    require(set(map(str,plan['party_book_ids'])) <= set(addedbooks), 'Party marker for a non-added book')
    # Literal P5 battle mode marker requires an empty override only for added TargetType=0 books.
    battlebooks = {str(r['M9mwe2cu']) for r in tables['IL78hX09'][counts['IL78hX09']:] if str(r.get('89EvGKHx')) == '0'}
    require(set(map(str,plan['party_book_ids'])) == battlebooks & set(addedbooks), 'Party markers do not match added battle books')
    return {'tables':reports,'reference_closure':relations}

def compare_artwork_members(original, candidate, frozen, required_new_names, decompress):
    expected_names=set(original)|set(required_new_names)
    require(set(candidate)==expected_names,'Artwork archive has omitted original or unneeded added members')
    receipts=[]
    for name,blob in original.items():
        require(candidate[name]==blob,'Original Patch 5 artwork bytes changed: '+name)
    for name in sorted(set(required_new_names)-set(original)):
        require(name in frozen,'Required event artwork missing frozen source: '+name)
        blob=frozen[name]
        if blob.startswith(b'CRILAYLA'):
            blob=decompress(blob)
        require(candidate[name]==blob,'Added event artwork differs from frozen source: '+name)
        receipts.append({'name':name,'sha256':sha(blob),'bytes':len(blob)})
    return {'original_member_count':len(original),'original_members_byte_identical':True,
            'appended_members':receipts,'appended_member_count':len(receipts),'total_member_count':len(candidate),
            'omitted_unused_new_members':sorted(set(frozen)-expected_names)}

def qualify_artwork(payload, plan, content_apk, decoder, fields, read_cpk, decompress):
    info=next(r for r in plan['table_provenance'] if r['stem']=='LM1APs6u')
    rows=decoder((Path(payload)/info['candidate_relative_path']).read_bytes(),'LM1APs6u')
    added=rows[info['baseline_rows']:]
    filename_fields=[k for k in added[0] if fields.get(k,k)=='file_name']
    require(len(filename_fields)==1,'Event icon filename field ambiguous')
    needed={str(r[filename_fields[0]]) for r in added}
    asset=next(r for r in plan['payload_files'] if r['relative_path']=='side_stories/spdungeon9.cpk')
    with zipfile.ZipFile(content_apk) as z:
        baseline=z.read('assets/side_stories/spdungeon9.cpk')
        metadata=parse_side_manifest(z.read('assets/side_stories/manifest.tsv'))
        require(sha(baseline)==metadata['spdungeon9.cpk']['sha256'],'P5 artwork archive pin differs')
    frozen=load_source(asset['source'])
    candidate=(Path(payload)/'side_stories/spdungeon9.cpk').read_bytes()
    report=compare_artwork_members(read_cpk(baseline)[4],read_cpk(candidate)[4],read_cpk(frozen)[4],needed,decompress)
    report.update({'baseline_sha256':sha(baseline),'frozen_source_sha256':sha(frozen),'candidate_sha256':sha(candidate)})
    proof=json.loads(Path(plan['banner_preservation_report']).read_bytes())
    for key in ('original_member_count','appended_member_count','total_member_count','appended_members','omitted_unused_new_members'):
        require(report[key]==proof[key],'Artwork preparation proof differs from independent verification: '+key)
    return report

def qualify_companions(payload, plan, baseline_apk, decoder, read_cpk, proof_path):
    proof=json.loads(Path(proof_path).read_bytes())
    require(proof.get('schema')=='ffbe-patch5-event-companion-asset-proof-v1','Unsupported companion proof')
    require({r['path'] for r in proof['assets']}=={'side_stories/monster2c.cpk','side_stories/monster2d.cpk'},'Companion archive set differs')
    with zipfile.ZipFile(baseline_apk) as z:
        descriptors=[line.split('\t') for line in z.read('assets/base_delivery.tsv').decode().splitlines()[1:]]
    info=next(r for r in plan['table_provenance'] if r['stem']=='IL78hX09')
    added=decoder((Path(payload)/info['candidate_relative_path']).read_bytes(),'IL78hX09')[info['baseline_rows']:]
    newmissions={(str(r['M9mwe2cu']),str(r['6uIYE15X'])) for r in added if str(r['89EvGKHx'])=='0'}
    reports=[]
    for row in proof['assets']:
        require(row['baseline_descriptor'] in descriptors,'Companion original descriptor not signed by P5')
        baseline=Path(row['baseline_source_file']).read_bytes()
        require(sha(baseline)==row['baseline_descriptor'][3] and len(baseline)==int(row['baseline_descriptor'][2]),'Companion P5 source pin differs')
        candidate=(Path(payload)/row['path']).read_bytes()
        require(sha(candidate)==row['candidate_sha256'] and len(candidate)==row['candidate_bytes'],'Companion candidate pin differs')
        oldmembers,newmembers=read_cpk(baseline)[4],read_cpk(candidate)[4]
        for name,blob in oldmembers.items():
            require(newmembers.get(name)==blob,'Original companion archive member changed: '+name)
        appended={r['name']:r for r in row['appended_members']}
        require(set(newmembers)==set(oldmembers)|set(appended),'Unlisted companion member addition/removal')
        ledgerpath=Path(row['source_ledger'])
        require(file_sha(ledgerpath)==row['source_ledger_sha256']==DEPENDENCY_LEDGER_SHA,'Frozen dependency ledger pin differs')
        ledger=json.loads(ledgerpath.read_bytes())
        witnessed=collections.defaultdict(set)
        for mission in ledger['missions']:
            identity=(str(mission['book_id']),str(mission['mission_id']))
            if identity not in newmissions:
                continue
            for asset in mission.get('monster_assets',[]):
                for match in asset.get('delivered_matches',[]):
                    if match['filename']==Path(row['path']).name:
                        require(match['delivery']['sha256']==sha(candidate),'Ledger companion source hash differs')
                        witnessed[match['member']].add(identity)
        for name,item in appended.items():
            blob=newmembers[name]
            require(sha(blob)==item['sha256'] and len(blob)==item['bytes'],'Appended companion member pin differs')
            identities={(str(r['book_id']),str(r['mission_id'])) for r in item['required_by_new_events']}
            require(identities and identities <= witnessed[name],'Companion artwork not required by retained new event: '+name)
        require(len(oldmembers)==row['baseline_original_members'] and len(newmembers)==row['candidate_members'],'Companion member counts differ')
        reports.append({'path':row['path'],'baseline_members_byte_identical':len(oldmembers),
                        'appended_members':row['appended_members'],'candidate_sha256':sha(candidate),
                        'frozen_ledger_sha256':DEPENDENCY_LEDGER_SHA})
    return reports

def expected_class(path, original):
    text = original.replace('\r\n','\n')
    require(path in CLASS_PINS and sha(text.encode()) == CLASS_PINS[path], 'Original class seal differs: '+path)
    flat = '(side_stories|story_ports|battle|encyclopedia)/[A-Za-z0-9_.-]+'
    scene = 'r2_scene_(jp|gl)/[a-f0-9]{16}/[A-Za-z0-9_.-]+[.]cpk'
    if path == 'O1/ExtraContent$Entry.smali':
        before,after,count = '"'+flat+'"','"(?:'+flat+'|side_stories/'+scene+')"',1
    else:
        before,after,count = '"[A-Za-z0-9_.-]+"','"(?:[A-Za-z0-9_.-]+|'+scene+')"',2
    require(text.count(before) == count,'Original exact path predicate differs')
    text = text.replace(before,after)
    if path == 'O1/SideStoryTables.smali':
        before = '    :try_start_eb\n    invoke-virtual {v6}, Ljava/io/File;->isDirectory()Z\n\n    move-result v8\n\n    if-nez v8, :cond_f9\n\n    invoke-virtual {v6}, Ljava/io/File;->mkdirs()Z\n'
        after = '    :try_start_eb\n    invoke-virtual {v7}, Ljava/io/File;->getParentFile()Ljava/io/File;\n\n    move-result-object v9\n\n    invoke-virtual {v9}, Ljava/io/File;->isDirectory()Z\n\n    move-result v8\n\n    if-nez v8, :cond_f9\n\n    invoke-virtual {v9}, Ljava/io/File;->mkdirs()Z\n'
        require(text.count(before) == 1,'Original parent directory block differs')
        text = text.replace(before,after)
    return text

def normalize_smali(text):
    """Only offset-derived labels and equivalent instruction width encodings."""
    text = text.replace('\r\n','\n')
    # Labels can repeat in different methods; keep a separate mapping per method.
    result, facts = [], {'label_definitions':0,'const_string_jumbo':0,'goto_width':0}
    segments = re.split(r'(?=^\.method )',text,flags=re.M)
    for segment in segments:
        definitions = re.findall(r'^\s*(:\w+)\s*$',segment,re.M)
        mapping = {name:':label_'+str(i) for i,name in enumerate(definitions)}
        facts['label_definitions'] += len(mapping)
        lines=[]
        for line in segment.splitlines():
            # Preserve every literal string, including path predicates.
            tokens = re.split(r'("(?:\\.|[^"\\])*")',line)
            for i in range(0,len(tokens),2):
                tokens[i] = re.sub(r':\w+',lambda m:mapping.get(m[0],m[0]),tokens[i])
            line=''.join(tokens)
            if re.match(r'^\s*const-string/jumbo\b',line):
                facts['const_string_jumbo'] += 1
                line=line.replace('const-string/jumbo','const-string',1)
            if re.match(r'^\s*goto/(16|32)\b',line):
                facts['goto_width'] += 1
                line=re.sub(r'goto/(16|32)\b','goto',line,count=1)
            lines.append(line)
        result.append('\n'.join(lines)+'\n')
    return ''.join(result),facts

def compare_smali(original, candidate, receipt):
    require(set(original) == set(candidate),'DEX class addition/removal: '+str(sorted(set(original)^set(candidate))))
    require(receipt.get('schema') == 'ffbe-patch5-minimal-event-paths-smali-v1', 'Unsupported smali receipt')
    pinned = {r['path']:r for r in receipt['classes']}
    require(set(pinned) == ALLOWED_CLASSES, 'Smali receipt may allow exactly two classes')
    changes, serialization = [], []
    for path in sorted(original):
        a,b=original[path].replace('\r\n','\n'),candidate[path].replace('\r\n','\n')
        expected=a
        if path in ALLOWED_CLASSES:
            expected=expected_class(path,a)
            require(sha(original[path].encode()) == pinned[path]['before_sha256'] and sha(expected.encode()) == pinned[path]['after_sha256'],
                    'Smali before/after receipt differs: '+path)
        if expected != b:
            canonical_a,fa=normalize_smali(expected)
            canonical_b,fb=normalize_smali(b)
            require(canonical_a == canonical_b,'Unlisted DEX semantic change: '+path)
        if path in ALLOWED_CLASSES:
            changes.append({'path':path,'baseline_sha256':sha(a.encode()),'expected_source_sha256':sha(expected.encode()),
                            'final_disassembled_sha256':sha(b.encode())})
        if expected != b:
            serialization.append({'path':path,'expected_encoding':fa,'actual_encoding':fb,
                                  'only_labels_or_equivalent_instruction_widths':True})
    return {'class_count':len(original),'changed_classes':changes,'untouched_class_count':len(original)-2,
            'added_or_removed_classes':0,'serialization_differences':serialization,
            'lifecycle_downloader_callbacks_updater_UI_movies_unchanged':True}

def run_tool(args, log):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=600)
    log.parent.mkdir(parents=True,exist_ok=True)
    log.write_text(result.stdout+result.stderr,encoding='utf-8')
    require(result.returncode == 0,'Qualification tool failed; see '+str(log))
    return result.stdout+result.stderr

def smali_tree(root):
    result={}
    for p in Path(root).rglob('*.smali'):
        text=p.read_bytes().decode('utf-8')
        declaration=re.search(r'^\.class\s+(?:[^\r\n]*\s)?(L[^;\s]+;)\s*$',text,re.M)
        require(declaration is not None,'Disassembled file lacks class declaration: '+str(p))
        # Baksmali changes Windows file suffixes to avoid case collisions. The
        # exact DEX descriptor, not the filesystem spelling, is the identity.
        identity=declaration[1][1:-1]+'.smali'
        require(identity not in result,'Duplicate disassembled DEX class: '+identity)
        result[identity]=text
    return result

def main():
    parser=argparse.ArgumentParser()
    for flag in ('baseline-apk','apk','payload','event-plan','smali-receipt','output'):
        parser.add_argument('--'+flag,type=Path,required=True)
    parser.add_argument('--project',type=Path,default=Path('T:/Projects/FFBE Patch'))
    parser.add_argument('--codec-dir',type=Path,default=Path('T:/Projects/FFBE Patch/story-ports/side-stories/scripts'))
    parser.add_argument('--baseline-content-apk',type=Path,default=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Content-Source.apk'))
    parser.add_argument('--source-graph',type=Path,default=Path('T:/Projects/FFBE Patch/localization-rounds/2026-10-03-native-delivery-v203/delivery_metadata/game_asset_manifest.json'))
    parser.add_argument('--source-side-manifest',type=Path,default=Path('C:/Users/Raegen/Documents/Codex/2026-10-02/task-2/integration_work/native_delivery_correction/payload/side_stories/manifest.tsv'))
    args=parser.parse_args()
    audit=args.output.parent/(args.output.stem+'_work_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    audit.mkdir(parents=True,exist_ok=False)
    report={'schema':'ffbe-patch5-event-only-qualification-v1','passed':False,'apk':str(args.apk.resolve()),
            'work_directory':str(audit.resolve()),'runtime_verified':False,'device_actions':False,'network_checks':False,'published':False}
    try:
        require(file_sha(args.baseline_apk) == BASELINE_SHA,'Production Patch 5 baseline identity differs')
        require(file_sha(args.baseline_content_apk) == CONTENT_SOURCE_SHA,'Production Patch 5 content-source identity differs')
        plan=json.loads(args.event_plan.read_bytes())
        source_archives={Path(r['baseline_source']['archive']) for r in plan['table_provenance'] if 'archive' in r['baseline_source']}
        require(all(file_sha(p) == CONTENT_SOURCE_SHA for p in source_archives),'Event table baseline content-source APK differs')
        files=payload_inventory(args.payload,plan)
        require(file_sha(args.source_graph)==SOURCE_GRAPH_SHA,'Frozen event source admission graph differs')
        graph=json.loads(args.source_graph.read_bytes())
        manifest_row=next(r for r in graph['assets'] if r['namespace']=='root' and r['path']=='side_stories/manifest.tsv')
        require(file_sha(args.source_side_manifest)==manifest_row['sha256'],'Frozen side-story manifest pin differs')
        admitted={r['path']:r for r in graph['assets']
                  if r['namespace']=='root' and r['path'].startswith('side_stories/') and r['path']!='side_stories/manifest.tsv'}
        require(set(files)==set(admitted),'Event payload must match the admitted 500-file event dependency set')
        report['apk_members']=compare_members(args.baseline_apk,args.apk)
        with zipfile.ZipFile(args.baseline_apk) as old,zipfile.ZipFile(args.apk) as new:
            manifest,report['manifest']=expected_manifest(old.read('AndroidManifest.xml'))
            require(new.read('AndroidManifest.xml') == manifest,'Manifest changed beyond versionCode 199 to 205')
            report['script']=compare_script(old.read('assets/frida_script.js'),new.read('assets/frida_script.js'),plan['party_book_ids'])
            require(new.read('assets/content_delivery.tsv') == (args.payload/'content_delivery.tsv').read_bytes(),'Signed catalog differs from staged payload')
            require(new.read('assets/side_stories/manifest.tsv') == (args.payload/'side_stories/manifest.tsv').read_bytes(),'Signed manifest differs from staged payload')
            catalog,report['catalog']=compare_catalog(old.read('assets/content_delivery.tsv'),new.read('assets/content_delivery.tsv'),files)
            report['side_manifest']=compare_side_manifest(old.read('assets/side_stories/manifest.tsv'),new.read('assets/side_stories/manifest.tsv'),files,catalog,args.source_side_manifest.read_bytes())
            for z,name in ((old,'baseline'),(new,'candidate')):
                (audit/(name+'.dex')).write_bytes(z.read('classes.dex'))
        sys.path.insert(0,str(args.codec_dir))
        from common import rows_bytes, FIELDS, crilayla
        from cpk_convert import read_cpk
        report['event_tables']=qualify_tables(args.payload,plan,rows_bytes,
            lambda stem:production_table(stem,args.baseline_apk,args.baseline_content_apk,args.project))
        report['event_artwork']=qualify_artwork(args.payload,plan,args.baseline_content_apk,rows_bytes,FIELDS,read_cpk,crilayla)
        report['event_companions']=qualify_companions(args.payload,plan,args.baseline_apk,rows_bytes,read_cpk,args.event_plan.parent/'EVENT_COMPANION_ASSET_PROOF.json')
        tablepaths={r['candidate_relative_path'] for r in plan['table_provenance']}
        sources=[]
        for name,row in files.items():
            source=row.get('source') or row.get('source_provenance')
            if source:
                blob=load_source(source)
                require(sha(blob)==source['sha256']==admitted[name]['sha256']
                        and len(blob)==int(source['bytes'])==admitted[name]['bytes'],'Frozen event source admission differs: '+name)
                if name not in tablepaths and name != 'side_stories/spdungeon9.cpk':
                    require(sha(blob) == row['sha256'] and len(blob) == int(row['bytes']),'Frozen raw source differs: '+name)
                sources.append({'path':name,'source':source,'sha256':sha(blob),'bytes':len(blob)})
            else:
                require(name in tablepaths,'Raw dependency lacks frozen source provenance: '+name)
        report['raw_source_pins']=sources
        bt=args.project/'graphics-localization/2026-09-19/apk-build/tools/android-16'
        signer=run_tool(['java','-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',args.apk],audit/'signature.txt')
        require('Signer #1 certificate SHA-256 digest: '+SIGNER_SHA in signer,'Signer differs from production')
        require(len(re.findall(r'Signer #\d+ certificate SHA-256 digest:',signer)) == 1,'Additional APK signer found')
        run_tool([bt/'zipalign.exe','-c','-P','16','4',args.apk],audit/'alignment.txt')
        badging=run_tool([bt/'aapt2.exe','dump','badging',args.apk],audit/'package.txt')
        require("name='com.square_enix.ffbejpn'" in badging and "versionCode='205'" in badging
                and "versionName='11.1.1'" in badging and 'application-debuggable' not in badging,'Package identity/version/debug policy differs')
        for name in ('baseline','candidate'):
            target=audit/(name+'-smali')
            require(not target.exists(),'Use a fresh output qualification path; disassembly already exists')
            run_tool(['java','-jar',args.project/'tools/bin/baksmali.jar','d',audit/(name+'.dex'),'-o',target],audit/(name+'-dex.txt'))
        receipt=json.loads(args.smali_receipt.read_bytes())
        report['dex']=compare_smali(smali_tree(audit/'baseline-smali'),smali_tree(audit/'candidate-smali'),receipt)
        report.update({'passed':True,'apk_sha256':file_sha(args.apk),'apk_bytes':args.apk.stat().st_size,
                       'baseline_sha256':BASELINE_SHA,'event_plan_sha256':file_sha(args.event_plan),
                       'smali_receipt_sha256':file_sha(args.smali_receipt),'signer_sha256':SIGNER_SHA,
                       'qualification_tools':{str(p):file_sha(p) for p in (bt/'aapt2.exe',bt/'zipalign.exe',bt/'lib/apksigner.jar',args.project/'tools/bin/baksmali.jar')},
                       'guard_sha256':file_sha(__file__)})
    except Exception as error:
        report['failure']=str(error)
    report['time_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'report':str(args.output),'failure':report.get('failure')}))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
