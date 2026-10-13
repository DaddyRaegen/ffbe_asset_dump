"""Exact v205 preservation with finite, explicitly authorized event changes.

The final content-plan adapter is intentionally separate from these differential
primitives. Table names alone never confer permission to change a record.
"""
from pathlib import Path
import argparse,collections,datetime,io,json,re,struct,sys,urllib.parse,zipfile,zlib
import baseline205_guard as common

BASELINE205_SHA='e5cd92390929216666cebdbb9055d1f216cf2001c20dc4f8fe63225101dbf039'
BASELINE205_DEX_SHA='408b8332dfbe4aaccb239ca0de3e3a71a7dc02e54f84135c321eeca2b58cc558'
BASELINE205_HELPER_SHA='15f868b4d48d6d74c9ef467ebac7fdb3dffdf39c8983ad263b4da80fdc1a4408'
ALLOWED_APK_MEMBERS=frozenset(('AndroidManifest.xml','assets/frida_script.js',
                            'assets/content_delivery.tsv','assets/side_stories/manifest.tsv'))
REMOVED_BOOKS=frozenset(('7077','7299','1000099'))
REVIVAL_BOOKS=('7074','7075')
MOVED_BOOKS=frozenset('1000072 1000089 1000093 1000098 1000103 1000108 1000113 1000118 1000123 1000133 1000138 1000143 1000148 1000154 1000159 1000165 1000170 1000191 1000220 1000986'.split())
DEFERRED_BOOKS=frozenset('1000002 1000004 1000005 1000010 1000012 1000013 1000014 1000015 1000035 1000036 1000237 1000238 1000240 1000241 1000242 1000243 1000246 1000347 1001215 1001216 1001217 1001218 1001220 1001221 1001222 1001223 1001226 1001227 1001228 1001229 1001231 1001234 1001235 1001238 1001239 1001242 1001243'.split())
EXCLUDED_BOOKS=REMOVED_BOOKS|DEFERRED_BOOKS|{'1700001'}
TABLE_KEYS={'D2zaT7Ru':'2ShgIRU8','Nm36woZx':'M9mwe2cu','9Zdr5ap0':'vG1hSm79','IL78hX09':'VMkv7S9R'}
BANNER_TARGETS={**{id:'side_book_'+id+'.png' for id in '7065 7070 7073 7074 7076 7078 7081 7082 7083'.split()},
                '1500001':'event_archive_book_1500001.png','1500002':'event_archive_book_1500002.png',
                '1000986':'event_original_jp_7f580191810790d3.png'}
BASELINE205_CATALOG_SHA='5c9947b79a60f8a07914ab70d75080939034993fda3891626b0b762438037415'
BASELINE205_SIDE_SHA='f4c3f34d5fa1cb8ef85bac51e8cfa55267bfe8266fe45f2295e3d495367e0230'
ROOT=Path(__file__).resolve().parents[1]
APK205=ROOT.parent/'v205-patch5-events/staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk'
PAYLOAD205=ROOT.parent/'v205-patch5-events/payload'
SEASON='2ShgIRU8';BOOK='M9mwe2cu';MAP='vG1hSm79';ENTRY='VMkv7S9R';ORDER='Z0EN6jSh';ICON='0HUPxDf1'
require=common.require
sha=common.sha

def compare_apk_members(baseline,candidate):
    with zipfile.ZipFile(baseline) as old,zipfile.ZipFile(candidate) as new:
        require(new.testzip() is None,'Candidate ZIP CRC failure')
        for z in (old,new):require(len(z.namelist())==len(set(z.namelist())),'Duplicate APK ZIP member')
        before={n for n in old.namelist() if not common.signature(n)}
        after={n for n in new.namelist() if not common.signature(n)}
        require(before==after,'APK member addition/removal')
        assets={n for n in before if n.startswith('assets/') and not n.endswith('/')}
        require(len(assets)==170,'Expected exact original170 asset members')
        changed=[];native=[]
        for name in sorted(before):
            a,b=old.getinfo(name),new.getinfo(name)
            require(a.compress_type==b.compress_type,'APK compression changed: '+name)
            ab,bb=old.read(name),new.read(name)
            if ab!=bb:
                require(name in ALLOWED_APK_MEMBERS,'Unrequested APK member changed: '+name)
                changed.append({'path':name,'before_sha256':sha(ab),'after_sha256':sha(bb),
                                'before_bytes':len(ab),'after_bytes':len(bb)})
            else:
                require(common.compressed_blob(old,a)==common.compressed_blob(new,b),'Unchanged member recompressed: '+name)
            if name.endswith('.so'):
                require(ab==bb,'Native library changed: '+name)
                native.append({'path':name,'bytes':len(ab),'sha256':sha(ab)})
        require({r['path'] for r in changed}==ALLOWED_APK_MEMBERS,'Expected exactlyfour requested APK member changes')
        dex=old.read('classes.dex')
        require(sha(dex)==BASELINE205_DEX_SHA and new.read('classes.dex')==dex,'v205 runtime DEX is not byte-identical')
        return {'changed_members':changed,'unchanged_member_count':len(before)-len(changed),'assets':170,
                'runtime_dex_sha256':sha(dex),'all10950_classes_preserved':True,'native_libraries':native,
                'new_or_removed_members':0}

def expected_manifest(original):
    result=bytearray(original);offset=8;names=None;positions=[]
    require(len(result)>=8 and struct.unpack_from('<I',result,4)[0]==len(result),'Invalid AXML size')
    while offset<len(result):
        kind,header,size=struct.unpack_from('<HHI',result,offset)
        require(size>=header>=8 and offset+size<=len(result),'Invalid AXML chunk')
        if kind==1:names=common.pool_strings(result[offset:offset+size])
        if kind==0x102:
            require(names is not None,'Missing AXML pool')
            tag=struct.unpack_from('<I',result,offset+header+4)[0]
            if names[tag]=='manifest':
                start,width,count=struct.unpack_from('<HHH',result,offset+header+8)
                for i in range(count):
                    p=offset+header+start+i*width;name=struct.unpack_from('<I',result,p+4)[0]
                    if names[name]=='versionCode':
                        require(result[p+15]==16 and struct.unpack_from('<I',result,p+16)[0]==205,'Expected typed versionCode205')
                        struct.pack_into('<I',result,p+16,206);positions.append(p+16)
        offset+=size
    require(offset==len(result) and len(positions)==1,'Ambiguous versionCode')
    return bytes(result),{'value_offset':positions[0],'before':205,'after':206,'typed_four_byte_value_only':True}

def compare_script(original,candidate):
    before=b'const PATCH_VERSION = 205;';after=b'const PATCH_VERSION = 206;'
    require(original.count(before)==1,'Ambiguous existing update counter')
    require(candidate==original.replace(before,after),'Party, lifecycle, movie, routing or other script changed')
    marker='const SIDE_STORY_PARTIES = ';text=original.decode('utf-8')
    require(text.count(marker)==1,'Ambiguous existing party map')
    parties,_=json.JSONDecoder().raw_decode(text[text.index(marker)+len(marker):])
    require(len(parties['books'])==920 and len(parties['entries'])==2177,'Existing v205 party map differs')
    return {'counter_before':205,'counter_after':206,'party_books_preserved':920,'party_entry_policies_preserved':2177,
            'classifier_and_all_hooks_byte_identical':True,'beta_routes_byte_identical':True}

def apply_exact_operations(original,keys,updates,removals,additions=()):
    """Each operation includes a complete old row, plus exact changed fields."""
    identity=lambda r:tuple(str(r[k]) for k in keys)
    old={identity(r):r for r in original}
    require(len(old)==len(original),'Duplicate original primary key')
    changes={};deleted=set()
    for op in updates:
        key=tuple(map(str,op['key']))
        require(key in old and key not in changes and key not in deleted,'Unknown/duplicate update key')
        require(old[key]==op['before'],'Update old row differs from baseline')
        result=dict(old[key]);fields=op['fields']
        require(fields,'Empty update operation')
        for field,delta in fields.items():
            require(field not in keys and field in result and result[field]==delta['before'],'Update field/old value differs')
            require(delta['before']!=delta['after'],'Redundant update field')
            result[field]=delta['after']
        changes[key]=result
    for op in removals:
        key=tuple(map(str,op['key']))
        require(key in old and key not in deleted and key not in changes,'Unknown/duplicate removal key')
        require(old[key]==op['before'],'Removed old row differs from baseline')
        deleted.add(key)
    result=[changes.get(identity(r),r) for r in original if identity(r) not in deleted]
    inserted=set()
    for row in additions:
        key=identity(row)
        require(key not in old and key not in inserted,'Duplicate/existing addition key')
        inserted.add(key);result.append(row)
    return result

def compare_exact_rows(original,candidate,keys,updates,removals,additions=()):
    expected=apply_exact_operations(original,keys,updates,removals,additions)
    require(candidate==expected,'Candidate contains unlisted fields, records or ordering changes')
    return {'baseline_rows':len(original),'candidate_rows':len(candidate),'updated_rows':len(updates),
            'removed_rows':len(removals),'added_rows':len(additions),'all_other_rows_and_relative_order_preserved':True}

def revival_orders(books,target_seasons,removed=REMOVED_BOOKS):
    candidates=[int(r[ORDER]) for r in books if str(r[BOOK]) not in set(removed)|set(REVIVAL_BOOKS)
                and str(target_seasons.get(str(r[BOOK]),r[SEASON]))=='70']
    require(candidates,'Missing retained Story Events')
    maximum=max(candidates)
    require(maximum<2147483645,'Native signed ordering would overflow')
    return {REVIVAL_BOOKS[0]:str(maximum+1),REVIVAL_BOOKS[1]:str(maximum+2)}

def compare_archive_members(original,candidate,operations):
    """Every edited artwork member needs an exact old/new pin and source bytes."""
    expected=dict(original);receipt=[];seen=set()
    for op in operations:
        name=op['name']
        require(name not in seen,'Duplicate banner member operation');seen.add(name)
        before=original.get(name)
        require((sha(before) if before is not None else None)==op['before_sha256'],'Banner original pin differs: '+name)
        if op['action']=='remove':
            require(before is not None,'Cannot remove absent banner member')
            require(op.get('after_sha256') is None,'Removed banner must not have an after hash')
            del expected[name]
        else:
            require(op['action'] in ('replace','add'),'Unknown artwork operation')
            require((before is None)==(op['action']=='add'),'Wrong artwork action for original member')
            source=Path(op['source_file']).read_bytes()
            require(sha(source)==op['after_sha256'] and len(source)==op['after_bytes'],'Prepared banner source pin differs')
            expected[name]=source
        receipt.append({k:v for k,v in op.items() if k!='source_file'})
    require(set(candidate)==set(expected),'Unlisted artwork member addition/removal')
    require(all(candidate[n]==b for n,b in expected.items()),'Unlisted artwork bytes changed')
    return {'original_members':len(original),'candidate_members':len(candidate),'operations':receipt,
            'all_other_raw_members_byte_identical':True}

def pinned_file(row):
    path=Path(row.get('local_path',row.get('file',row.get('path',''))))
    blob=path.read_bytes()
    require(sha(blob)==row['sha256'] and len(blob)==int(row['bytes']),'Source pin differs: '+str(path))
    return blob

def authorized_table_operations(tables):
    """Derive a finite operation formula from independently sealed human scope."""
    books=tables['Nm36woZx']
    require({r[BOOK] for r in books if r[SEASON]=='91'}==MOVED_BOOKS,'Archived event baseline ID set differs')
    require(EXCLUDED_BOOKS<={r[BOOK] for r in books},'Authorized excluded book absent')
    orders=revival_orders(books,{id:'70' for id in MOVED_BOOKS},EXCLUDED_BOOKS)
    require(orders=={'7074':'1507','7075':'1508'},'Revival derived baseline order differs')
    result={}
    for stem,key in TABLE_KEYS.items():
        operations=[]
        for row in tables[stem]:
            id=row[key];book=row.get(BOOK)
            if (stem=='D2zaT7Ru' and id in {'91','93'}) or (stem!='D2zaT7Ru' and book in EXCLUDED_BOOKS):
                operations.append({'op':'remove','id':id,'before':row})
            elif book in MOVED_BOOKS:
                require(row[SEASON]=='91','Moved event hierarchy baseline season differs')
                operations.append({'op':'update','id':id,'fields':{SEASON:{'before':'91','after':'70'}}})
            elif stem=='Nm36woZx' and book in REVIVAL_BOOKS:
                operations.append({'op':'update','id':id,'fields':{ORDER:{'before':row[ORDER],'after':orders[book]}}})
        result[stem]=operations
    return result,orders

def canonical_operations(operations):
    result=[];seen=set()
    for op in operations:
        require(op['op'] in ('remove','update'),'Table additions or unknown operations are forbidden')
        require(op['id'] not in seen,'Duplicate table operation');seen.add(op['id'])
        base={'op':op['op'],'id':op['id']}
        base['before' if op['op']=='remove' else 'fields']=op['before' if op['op']=='remove' else 'fields']
        result.append(base)
    return sorted(result,key=lambda op:op['id'])

def relationship_observations(tables):
    books={r[BOOK]:r for r in tables['Nm36woZx']};maps={r[MAP]:r for r in tables['9Zdr5ap0']}
    observations=set()
    for stem,key in (('9Zdr5ap0',MAP),('IL78hX09',ENTRY)):
        for row in tables[stem]:
            book=books.get(row[BOOK]);parent=maps.get(row.get(MAP))
            if book is None:observations.add((stem,row[key],'book_missing',row[BOOK]))
            elif row[SEASON]!=book[SEASON]:observations.add((stem,row[key],'book_season_alias',row[SEASON],book[SEASON]))
            if stem=='IL78hX09':
                if parent is None:observations.add((stem,row[key],'map_missing',row[MAP]))
                elif any(row[f]!=parent[f] for f in (BOOK,SEASON)):
                    observations.add((stem,row[key],'map_parent_alias',row[MAP],row[BOOK],row[SEASON],parent[BOOK],parent[SEASON]))
    return observations

def qualify_cleanup(payload,plan,rows_bytes,prior_catalog):
    require(plan.get('schema_version')==1 and plan.get('version')==206 and plan.get('ready_for_catalog') is True,'Cleanup plan incomplete')
    for key,expected in (('moved_book_ids',MOVED_BOOKS),('named_removed_book_ids',REMOVED_BOOKS),
                         ('deferred_greeting_book_ids',{'1700001'}),('deferred_vortex_book_ids',DEFERRED_BOOKS),
                         ('excluded_book_ids',EXCLUDED_BOOKS),('removed_season_ids',{'91','93'})):
        require(len(plan[key])==len(expected) and set(plan[key])==expected,'Cleanup authorized ID set differs: '+key)
    require(plan['moved_from_season_id']=='91' and plan['moved_to_season_id']=='70','Unauthorized event category target')
    entries={r['stem']:r for r in plan['table_changes']}
    require(len(entries)==len(plan['table_changes']) and set(entries)==set(TABLE_KEYS),'Unlisted cleanup table')
    original={};candidate={};files={}
    for stem,row in entries.items():
        name='side_stories/'+stem+'.dat'
        require(row['path']==name and row['baseline']['primary_key']==TABLE_KEYS[stem],'Cleanup path/primary key differs')
        before=pinned_file(row['baseline']);after=pinned_file(row)
        require((PAYLOAD205/name).read_bytes()==before,'Cleanup baseline is not exact205 payload')
        require((Path(payload)/name).read_bytes()==after,'Cleanup prepared candidate differs')
        require(sha(before)==prior_catalog[name]['sha256'] and len(before)==prior_catalog[name]['bytes'],'Baseline catalog table pin differs')
        original[stem]=rows_bytes(before,stem);candidate[stem]=rows_bytes(after,stem)
        files[name]={'bytes':len(after),'sha256':sha(after)}
    formula,orders=authorized_table_operations(original)
    reports=[];deferred=[]
    for stem,row in entries.items():
        require(canonical_operations(row['operations'])==canonical_operations(formula[stem]),'Unlisted cleanup row/field operations: '+stem)
        index={r[TABLE_KEYS[stem]]:r for r in original[stem]};updates=[];removals=[]
        for op in formula[stem]:
            parsed={'key':[op['id']],'before':index[op['id']]}
            if op['op']=='update':parsed['fields']=op['fields'];updates.append(parsed)
            else:
                removals.append(parsed)
                deferred.append((stem,op['id'],op['before']))
        receipt=compare_exact_rows(original[stem],candidate[stem],[TABLE_KEYS[stem]],updates,removals)
        require(receipt['baseline_rows']==row['before_rows'] and receipt['candidate_rows']==row['after_rows'],'Cleanup table count receipt differs')
        reports.append({'stem':stem,**receipt,'bytes':row['bytes'],'sha256':row['sha256']})
    require(plan['revival_orders']==orders,'Revival plan order differs')
    proof=json.loads(pinned_file(plan['order_proof']))
    require(proof['passed'] is True and proof['baseline205_apk_sha256']==BASELINE205_SHA,'Native numeric order proof differs')
    before_gaps=relationship_observations(original);after_gaps=relationship_observations(candidate)
    require(after_gaps<=before_gaps,'Cleanup creates a new parent relationship observation')
    books={r[BOOK]:r for r in candidate['Nm36woZx']};maps={r[MAP]:r for r in candidate['9Zdr5ap0']}
    for stem in ('9Zdr5ap0','IL78hX09'):
        for row in candidate[stem]:
            if row[BOOK] in MOVED_BOOKS:
                require(row[SEASON]==books[row[BOOK]][SEASON]=='70','Moved event hierarchy is not closed')
                if stem=='IL78hX09':require(row[BOOK]==maps[row[MAP]][BOOK] and maps[row[MAP]][SEASON]=='70','Moved event map missing')
    preserved=json.loads(pinned_file(plan['deferred_ui_records']))
    receipts=[(r['stem'],r['id'],r['before']) for r in preserved['records']]
    require(sorted(receipts,key=lambda r:(r[0],r[1]))==sorted(deferred,key=lambda r:(r[0],r[1])),'Deferred original UI records incomplete or changed')
    sourcepins={key:{'sha256':sha(pinned_file(row)),'bytes':row['bytes']} for key,row in plan['source_provenance'].items()}
    for key in ('inherited_playback_relationships','event71_decision_ledger'):pinned_file(plan[key])
    return files,{'tables':reports,'native_revival_orders':orders,'moved_books':len(MOVED_BOOKS),
                  'excluded_books':len(EXCLUDED_BOOKS),'all_unlisted_rows_fields_order_preserved':True,
                  'inherited_relationship_observations':len(before_gaps),'new_relationship_observations':0,
                  'deferred_original_ui_rows_preserved':len(deferred),'classification_source_pins':sourcepins}

def compare_metadata(old_catalog,new_catalog,old_side,new_side,files):
    require(sha(old_catalog)==BASELINE205_CATALOG_SHA and sha(old_side)==BASELINE205_SIDE_SHA,'Exact205 metadata baseline differs')
    old,new=common.parse_catalog(old_catalog),common.parse_catalog(new_catalog)
    require(new_catalog==('ffbe-content-v1\n'+'\n'.join(r['line'] for r in new.values())+'\n').encode(),'Catalog text formatting changed')
    require(len(old)==1898 and list(old)==list(new),'Catalog path membership or order changed')
    changed=[]
    for name,row in new.items():
        if name not in files:require(row['line']==old[name]['line'],'Unlisted catalog descriptor changed: '+name)
        else:
            require(row['sha256']==files[name]['sha256'] and row['bytes']==int(files[name]['bytes']),'206 catalog payload pin differs: '+name)
            require(row['sha256']!=old[name]['sha256'],'Planned changed file must have different raw bytes')
            common.immutable_transport(row)
            changed.append({'path':name,'before':old[name]['parts'],'after':row['parts']})
    require(set(files)<={p for p in new},'Planned file absent from catalog')
    a,b=common.parse_side_manifest(old_side),common.parse_side_manifest(new_side)
    require(new_side==('\n'.join(r['line'] for r in b.values())+'\n').encode(),'Side manifest text formatting changed')
    require(len(a)==1857 and list(a)==list(b),'Side manifest path membership or order changed')
    side=[]
    for name,row in b.items():
        path='side_stories/'+name
        if path not in files:require(row['line']==a[name]['line'],'Unlisted side metadata changed: '+name)
        else:
            expected=a[name]['line'].split('\t');expected[1]=files[path]['sha256']
            expected[2]=','.join(sorted(a[name]['accepted']|{a[name]['sha256']}))
            require(row['line']=='\t'.join(expected),'206 side metadata exceeds exact current hash and prior205 acceptance: '+name)
            side.append({'path':path,'before':a[name]['line'],'after':row['line']})
        require(all('side_stories/'+p in new for p in row['variants'].values()),'Manifest variant absent from catalog')
    return new,{'catalog_rows':len(new),'side_manifest_rows':len(b),'added_or_removed_paths':0,
                'catalog_changes':changed,'side_manifest_changes':side,'all_other_descriptor_bytes_and_order_preserved':True}

def qualify_banners(payload,plan,prior_catalog,rows_bytes,read_cpk):
    require(plan.get('passed') is True,'Banner plan has not passed preparation')
    asset=plan['asset'];name='side_stories/spdungeon9.cpk'
    require(asset['path']==name,'Unlisted banner archive')
    before=pinned_file(asset['baseline']);after=pinned_file(asset)
    require(before==(PAYLOAD205/name).read_bytes(),'Banner baseline differs from exact205')
    require(after==(Path(payload)/name).read_bytes(),'Prepared banner archive differs')
    require(sha(before)==prior_catalog[name]['sha256'] and len(before)==prior_catalog[name]['bytes'],'Banner baseline catalog pin differs')
    old=read_cpk(before);new=read_cpk(after)
    require(list(old[4])==list(new[4]),'CPK member set/order changed')
    require(len(old[3])==len(new[3]),'CPK TOC member count changed')
    names=set(BANNER_TARGETS.values());operations=[];seen=set();mapped=set()
    icon_blob=(PAYLOAD205/'side_stories/LM1APs6u.dat').read_bytes()
    require(sha(icon_blob)==prior_catalog['side_stories/LM1APs6u.dat']['sha256']
            and len(icon_blob)==prior_catalog['side_stories/LM1APs6u.dat']['bytes'],'Original205 icon table source differs')
    icons=rows_bytes(icon_blob,'LM1APs6u')
    books=rows_bytes((PAYLOAD205/'side_stories/Nm36woZx.dat').read_bytes(),'Nm36woZx')
    book_index={r[BOOK]:r for r in books};icon_index={r[ICON]:r for r in icons}
    for item in plan['members']:
        member=item['name'];require(member in names and member not in seen,'Unrequested or duplicate banner replacement');seen.add(member)
        ids=set(map(str,item['book_ids']));expected_ids={id for id,n in BANNER_TARGETS.items() if n==member}
        require(ids==expected_ids,'Banner book-to-member scope differs')
        for id in ids:
            require(icon_index[book_index[id][ICON]]['qtkvrS60']==member,'Actual205 book icon mapping differs')
        mapped|=ids
        prior=item['baseline'];candidate=item['candidate'];png=pinned_file(candidate)
        require(member in old[4] and sha(old[4][member])==prior['sha256'] and len(old[4][member])==prior['bytes'],'Exact old banner texture pin differs')
        require(png[:8]==b'\x89PNG\r\n\x1a\n' and png[12:16]==b'IHDR' and struct.unpack_from('>II',png,16)==(640,240),'Candidate banner is not native640x240 PNG')
        from PIL import Image
        with Image.open(io.BytesIO(png)) as image:
            require(image.format=='PNG' and image.size==(640,240),'Banner image decode/dimensions differ')
            image.load()
        require(candidate['width']==640 and candidate['height']==240,'Candidate dimension receipt differs')
        require(png!=old[4][member],'Banner replacement is a no-op')
        operations.append({'name':member,'action':'replace','before_sha256':prior['sha256'],
                           'after_sha256':candidate['sha256'],'after_bytes':candidate['bytes'],
                           'source_file':candidate['local_path']})
    require(seen==names and mapped==set(BANNER_TARGETS),'Missing exact requested banner replacement')
    receipt=compare_archive_members(old[4],new[4],operations)
    for a,b in zip(old[3],new[3]):
        require(set(a)==set(b),'CPK TOC metadata columns changed')
        member='/'.join(x for x in (a['DirName'],a['FileName']) if x)
        ignored={'FileOffset'}|({'FileSize','ExtractSize'} if member in seen else set())
        require(all(a[k]==b[k] for k in a if k not in ignored),'CPK original ID/order/metadata changed: '+member)
    receipt.update({'book_ids':sorted(mapped),'replacement_png_members':len(seen),
                    'original_CPK_member_order_and_IDs_preserved':True,'all_icon_rows_preserved':True,'original_icon_master_sha256':sha(icon_blob),
                    'original_genesis7032_banner_preserved':True,'bytes':len(after),'sha256':sha(after)})
    return {name:{'sha256':sha(after),'bytes':len(after)}},receipt

def qualify_transports(payload,catalog,files,download_plan_path,cleanup_plan_path,banner_plan_path):
    plan=json.loads(Path(download_plan_path).read_bytes())
    require(plan.get('schema')=='ffbe-event-cleanup-download-plan-v1' and plan.get('passed') is True,'Download plan incomplete')
    require(plan['cleanup_plan_sha256']==common.file_sha(cleanup_plan_path) and plan['banner_plan_sha256']==common.file_sha(banner_plan_path),'Content plan pins differ from transport preparation')
    require(plan['new_paths']==[] and plan['unchanged_original_rows']==1893,'Transport descriptor scope differs')
    require(set(plan['modified_original_paths'])==set(files),'Transport changed paths differ')
    pack=plan['new_pack'];blob=Path(pack['path']).read_bytes()
    require(sha(blob)==pack['sha256'] and len(blob)==pack['bytes'],'New transport pack pin differs')
    require(pack['name']==Path(pack['path']).name and pack['url'].endswith('/'+pack['name']),'Pack name/URL differs')
    identity=sha(json.dumps([{'path':p,'sha256':files[p]['sha256'],'bytes':files[p]['bytes']} for p in sorted(files)],sort_keys=True,separators=(',',':')).encode())
    tag='beta-content-v206-'+identity[:16]
    prefix='https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/'+tag+'/'
    require(plan['catalog_identity_sha256']==identity and plan['release_tag']==tag,'Immutable206 release identity differs')
    require(pack['name']=='event-cleanup-v206-'+sha(blob)[:16]+'.pack' and pack['url']==prefix+pack['name'],'Immutable206 pack URL/content identity differs')
    require(len(plan['new_pack_files'])==len(files)==5,'Expected five local event slices')
    position=0;receipts=[]
    for item in plan['new_pack_files']:
        name=item['path'];require(name in files and name not in {r['path'] for r in receipts},'Unlisted or duplicate packed path')
        row=catalog[name];require(row['method']==8 and row['url']==pack['url'] and row['sourcebytes']==len(blob),'Packed descriptor source/method differs')
        require(row['offset']==item['offset']==position and row['wirebytes']==item['wire_bytes'],'Packed ranges must partition exact five-slice source')
        wire=blob[position:position+row['wirebytes']];position+=len(wire)
        require(len(wire)==row['wirebytes'] and sha(wire)==item['wire_sha256'],'Transport wire pin differs')
        decoder=zlib.decompressobj(-15);raw=decoder.decompress(wire)+decoder.flush()
        require(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,'Raw-deflate wire not an exact complete stream')
        source=(Path(payload)/name).read_bytes()
        require(raw==source and sha(raw)==files[name]['sha256']==row['sha256']==item['sha256']
                and len(raw)==files[name]['bytes']==row['bytes']==item['bytes'],'Decoded transport source/payload/catalog pins differ')
        receipts.append({'path':name,'offset':row['offset'],'wire_bytes':len(wire),'wire_sha256':sha(wire),
                         'raw_bytes':len(raw),'raw_sha256':sha(raw),'exact_prepared_source_bytes':True})
    require(position==len(blob),'Pack contains unlisted trailing data')
    require([r['path'] for r in receipts]==sorted(files),'Pack entry order differs from exact path order')
    release_files={r['role']:r for r in plan['files']}
    require(set(release_files)=={'pack','catalog','manifest'} and len(plan['files'])==3,'Unexpected publication file role')
    for row in release_files.values():pinned_file(row)
    require(Path(release_files['pack']['local_path']).read_bytes()==blob,'Publication pack differs')
    content=(Path(payload)/'content_delivery.tsv').read_bytes();side=(Path(payload)/'side_stories/manifest.tsv').read_bytes()
    require(Path(release_files['catalog']['local_path']).read_bytes()==content,'Publication catalog differs')
    require(release_files['catalog']['name']=='content_delivery-'+sha(content)[:16]+'.tsv'
            and release_files['manifest']['name']=='event-assets-'+identity[:16]+'.json','Publication metadata content identity differs')
    require(plan['content_catalog_sha256']==sha(content) and plan['side_manifest_sha256']==sha(side),'Prepared metadata plan hash differs')
    source_manifest=pinned_file(release_files['manifest']);manifest=json.loads(source_manifest)
    require(manifest['schema']=='ffbe-event-cleanup-assets-v1' and manifest['channel']=='beta' and manifest['asset_version']==206
            and manifest['APK_min_version']==206 and manifest['source_build205_sha256']==BASELINE205_SHA,'Asset publication identity differs')
    with zipfile.ZipFile(APK205) as z:base_sha=sha(z.read('assets/base_delivery.tsv'))
    require(manifest['package']=='com.square_enix.ffbejpn' and manifest['signing_certificate_sha256']==common.SIGNER_SHA
            and manifest['source_patch5_sha256']==common.BASELINE_SHA,'Asset publication package/signer/preservation identity differs')
    require(manifest['base_catalog_unchanged_sha256']==plan['unchanged_base_catalog_sha256']==base_sha,'Unrequested base catalog changed')
    require(manifest['content_catalog']=={'url':prefix+release_files['catalog']['name'],'bytes':len(content),'sha256':sha(content)},'Asset manifest published catalog pointer differs')
    require(manifest['release_tag']==plan['release_tag'] and manifest['bundled_side_manifest_sha256']==sha(side),'Asset release/manifest linkage differs')
    require(len(manifest['assets'])==len(catalog) and [r['path'] for r in manifest['assets']]==list(catalog),'Asset manifest path order/membership differs')
    for item in manifest['assets']:
        row=catalog[item['path']]
        expected={'url':row['url'],'offset':row['offset'],'wire_bytes':row['wirebytes'],'method':row['method'],'source_bytes':row['sourcebytes']}
        require(item['transport']==expected and item['sha256']==row['sha256'] and item['bytes']==row['bytes'],'Asset manifest metadata/catalog differs')
        require(item['version']==(206 if item['path'] in files else 205),'Asset manifest version scope differs')
    return {'passed':True,'content_catalog_sha256':sha(content),'side_manifest_sha256':sha(side),
            'cleanup_plan_sha256':common.file_sha(cleanup_plan_path),'banner_plan_sha256':common.file_sha(banner_plan_path),
            'download_plan_sha256':common.file_sha(download_plan_path),
            'source_manifest_sha256':sha(source_manifest),'new_pack_sha256':sha(blob),'new_pack_bytes':len(blob),
            'exact_local_deflate_slices':receipts,'changed_descriptors':5,'unchanged1893_descriptors_byte_identical':True,
            'network_requested':False,'runtime_verified':False}

def qualify_content(payload,cleanup_plan_path,banner_plan_path,download_plan_path,codec_dir):
    require(common.file_sha(APK205)==BASELINE205_SHA,'Exact qualified205 APK identity differs')
    require(common.file_sha(Path(common.__file__))==BASELINE205_HELPER_SHA,'Frozen baseline utility source differs')
    with zipfile.ZipFile(APK205) as baseline:
        catalog_blob=baseline.read('assets/content_delivery.tsv');side_blob=baseline.read('assets/side_stories/manifest.tsv')
    prior=common.parse_catalog(catalog_blob)
    sys.path.insert(0,str(codec_dir))
    from common import rows_bytes
    from cpk_convert import read_cpk
    cleanup=json.loads(Path(cleanup_plan_path).read_bytes());banners=json.loads(Path(banner_plan_path).read_bytes())
    files,cleanup_report=qualify_cleanup(payload,cleanup,rows_bytes,prior)
    artwork,artwork_report=qualify_banners(payload,banners,prior,rows_bytes,read_cpk)
    require(not(set(files)&set(artwork)),'Duplicate external change');files.update(artwork)
    expected={*files,'content_delivery.tsv','side_stories/manifest.tsv'}
    require({p.relative_to(payload).as_posix() for p in Path(payload).rglob('*') if p.is_file()}==expected,'Unlisted staged external payload file')
    content=(Path(payload)/'content_delivery.tsv').read_bytes();side=(Path(payload)/'side_stories/manifest.tsv').read_bytes()
    catalog,metadata_report=compare_metadata(catalog_blob,content,side_blob,side,files)
    transport_report=qualify_transports(payload,catalog,files,download_plan_path,cleanup_plan_path,banner_plan_path)
    return {'cleanup':cleanup_report,'banners':artwork_report,'metadata':metadata_report,'transport':transport_report,
            'content_catalog_sha256':sha(content),'side_manifest_sha256':sha(side),
            'cleanup_plan_sha256':common.file_sha(cleanup_plan_path),'banner_plan_sha256':common.file_sha(banner_plan_path)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apk',type=Path)
    parser.add_argument('--payload',type=Path,default=ROOT/'payload')
    parser.add_argument('--cleanup-plan',type=Path,default=ROOT/'audit/CLEANUP_PLAN.json')
    parser.add_argument('--banner-plan',type=Path,default=ROOT/'audit/BANNER_PLAN.json')
    parser.add_argument('--download-plan',type=Path,default=ROOT/'asset_publication/DOWNLOAD_PLAN.json')
    parser.add_argument('--codec-dir',type=Path,default=Path('T:/Projects/FFBE Patch/story-ports/side-stories/scripts'))
    parser.add_argument('--project',type=Path,default=Path('T:/Projects/FFBE Patch'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    work=args.output.parent/(args.output.stem+'_work_'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    work.mkdir(parents=True,exist_ok=False)
    report={'schema':'ffbe-event-cleanup-qualification-v1','passed':False,'work_directory':str(work),
            'runtime_verified':False,'device_actions':False,'network_checks':False,'published':False}
    try:
        report.update(qualify_content(args.payload,args.cleanup_plan,args.banner_plan,args.download_plan,args.codec_dir))
        prior_report_path=APK205.parent.parent/'SIGNED_EVENT_QUALIFICATION.json'
        prior_report=json.loads(prior_report_path.read_bytes())
        require(prior_report['passed'] is True and prior_report['apk_sha256']==BASELINE205_SHA
                and prior_report['baseline_sha256']==common.BASELINE_SHA,'Qualified Patch5 preservation chain differs')
        report['preservation_chain']={'literal_patch5_sha256':common.BASELINE_SHA,'qualified205_apk_sha256':BASELINE205_SHA,
                                      'qualified205_report_sha256':common.file_sha(prior_report_path)}
        if args.apk:
            report['apk_members']=compare_apk_members(APK205,args.apk)
            require(len(report['apk_members']['native_libraries'])==8,'Original eight native libraries expected')
            with zipfile.ZipFile(APK205) as old,zipfile.ZipFile(args.apk) as new:
                manifest,report['manifest']=expected_manifest(old.read('AndroidManifest.xml'))
                require(new.read('AndroidManifest.xml')==manifest,'Binary manifest changed beyond four-byte205 to206 version value')
                report['script']=compare_script(old.read('assets/frida_script.js'),new.read('assets/frida_script.js'))
                require(new.read('assets/content_delivery.tsv')==(args.payload/'content_delivery.tsv').read_bytes(),'Signed catalog differs from qualified prepared bytes')
                require(new.read('assets/side_stories/manifest.tsv')==(args.payload/'side_stories/manifest.tsv').read_bytes(),'Signed side manifest differs from qualified prepared bytes')
            bt=args.project/'graphics-localization/2026-09-19/apk-build/tools/android-16'
            signer=common.run_tool(['java','-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',args.apk],work/'signature.txt')
            require('Signer #1 certificate SHA-256 digest: '+common.SIGNER_SHA in signer
                    and len(re.findall(r'Signer #\d+ certificate SHA-256 digest:',signer))==1,'Signer differs from exact production signer')
            common.run_tool([bt/'zipalign.exe','-c','-P','16','4',args.apk],work/'alignment.txt')
            badging=common.run_tool([bt/'aapt2.exe','dump','badging',args.apk],work/'package.txt')
            require("name='com.square_enix.ffbejpn'" in badging and "versionCode='206'" in badging
                    and "versionName='11.1.1'" in badging and 'application-debuggable' not in badging,'Package version/identity/debug policy differs')
            report.update({'apk':str(args.apk.resolve()),'apk_sha256':common.file_sha(args.apk),'apk_bytes':args.apk.stat().st_size,
                           'signer_sha256':common.SIGNER_SHA,'qualification_tools':{str(p):common.file_sha(p) for p in (bt/'aapt2.exe',bt/'zipalign.exe',bt/'lib/apksigner.jar')}})
        report.update({'passed':True,'signed_apk_qualified':bool(args.apk),'guard_sha256':common.file_sha(__file__),
                       'baseline205_sha256':BASELINE205_SHA})
        transport=report['transport']
        transport.update({'schema':'ffbe-event-cleanup-independent-transport-v1','guard_sha256':common.file_sha(__file__),
                          'baseline205_apk_sha256':BASELINE205_SHA})
        (ROOT/'audit/INDEPENDENT_TRANSPORT_QUALIFICATION.json').write_text(json.dumps(transport,indent=2)+'\n',encoding='utf-8')
    except Exception as error:report['failure']=str(error)
    report['time_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'report':str(args.output),'failure':report.get('failure')}))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
