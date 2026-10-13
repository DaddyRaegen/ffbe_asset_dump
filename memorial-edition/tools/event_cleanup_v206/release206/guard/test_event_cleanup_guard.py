from pathlib import Path
import copy,json,tempfile,unittest,zipfile
from unittest.mock import patch
import event_cleanup_guard as g

class OperationTests(unittest.TestCase):
    def setUp(self):
        self.old=[{'id':'1','season':'91','order':'1','text':'keep'},
                  {'id':'2','season':'70','order':'2','text':'other'},
                  {'id':'3','season':'71','order':'9','text':'named removal'}]
        self.update={'key':['1'],'before':copy.deepcopy(self.old[0]),'fields':{'season':{'before':'91','after':'70'}}}
        self.remove={'key':['3'],'before':copy.deepcopy(self.old[2])}
        self.new=[{**self.old[0],'season':'70'},self.old[1]]

    def test_exact_named_changes(self):g.compare_exact_rows(self.old,self.new,['id'],[self.update],[self.remove])

    def test_reject_unlisted_field(self):
        bad=copy.deepcopy(self.new);bad[0]['text']='extra'
        with self.assertRaises(g.common.GuardError):g.compare_exact_rows(self.old,bad,['id'],[self.update],[self.remove])

    def test_reject_unlisted_row_removal(self):
        with self.assertRaises(g.common.GuardError):g.compare_exact_rows(self.old,self.new[:1],['id'],[self.update],[self.remove])

    def test_reject_other_row_order_change(self):
        with self.assertRaises(g.common.GuardError):g.compare_exact_rows(self.old,self.new[::-1],['id'],[self.update],[self.remove])

    def test_reject_wrong_old_row_receipt(self):
        self.update['before']['text']='not baseline'
        with self.assertRaises(g.common.GuardError):g.compare_exact_rows(self.old,self.new,['id'],[self.update],[self.remove])

    def test_reject_identity_change(self):
        self.update['fields']['id']={'before':'1','after':'7'}
        with self.assertRaises(g.common.GuardError):g.apply_exact_operations(self.old,['id'],[self.update],[])

    def test_reject_update_remove_overlap(self):
        with self.assertRaises(g.common.GuardError):g.apply_exact_operations(self.old,['id'],[self.update],[{'key':['1'],'before':self.old[0]}])

    def test_reject_missing_requested_update(self):
        with self.assertRaises(g.common.GuardError):g.compare_exact_rows(self.old,self.old[:2],['id'],[self.update],[self.remove])

class OrderingTests(unittest.TestCase):
    def setUp(self):
        self.books=[{g.BOOK:'7074',g.SEASON:'70',g.ORDER:'2'},
                    {g.BOOK:'7075',g.SEASON:'70',g.ORDER:'3'},
                    {g.BOOK:'7001',g.SEASON:'70',g.ORDER:'35'},
                    {g.BOOK:'1000001',g.SEASON:'91',g.ORDER:'1047'},
                    {g.BOOK:'7077',g.SEASON:'70',g.ORDER:'99999'}]

    def test_include_moved_exclude_removed(self):
        self.assertEqual(g.revival_orders(self.books,{'1000001':'70'}),{'7074':'1048','7075':'1049'})

    def test_do_not_count_other_categories(self):
        self.assertEqual(g.revival_orders(self.books,{}),{'7074':'36','7075':'37'})

    def test_reject_native_signed_overflow(self):
        self.books[2][g.ORDER]='2147483646'
        with self.assertRaises(g.common.GuardError):g.revival_orders(self.books,{})

class ArchiveTests(unittest.TestCase):
    def fixture(self,d):
        source=Path(d)/'prepared.png';source.write_bytes(b'new event banner')
        old={'named.png':b'old banner','other.png':b'untouched','test.png':b'party test'}
        operations=[{'name':'named.png','action':'replace','before_sha256':g.sha(old['named.png']),
            'after_sha256':g.sha(source.read_bytes()),'after_bytes':source.stat().st_size,'source_file':str(source)},
            {'name':'test.png','action':'remove','before_sha256':g.sha(old['test.png']),'after_sha256':None}]
        new={'named.png':source.read_bytes(),'other.png':old['other.png']}
        return old,new,operations

    def test_only_named_texture_and_removal(self):
        with tempfile.TemporaryDirectory() as d:g.compare_archive_members(*self.fixture(d))

    def test_reject_unrelated_art_change(self):
        with tempfile.TemporaryDirectory() as d:
            old,new,ops=self.fixture(d);new['other.png']=b'changed'
            with self.assertRaises(g.common.GuardError):g.compare_archive_members(old,new,ops)

    def test_reject_wrong_prepared_source(self):
        with tempfile.TemporaryDirectory() as d:
            old,new,ops=self.fixture(d);ops[0]['after_sha256']='a'*64
            with self.assertRaises(g.common.GuardError):g.compare_archive_members(old,new,ops)

    def test_reject_unlisted_member(self):
        with tempfile.TemporaryDirectory() as d:
            old,new,ops=self.fixture(d);new['extra.png']=b'extra'
            with self.assertRaises(g.common.GuardError):g.compare_archive_members(old,new,ops)

class ScriptAndManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path('S:/FFBE JP Data Export/build/v205-patch5-events/staged_build/dist/FFBE-Memorial-EN-Patch-5-Events-v205.apk')
        with zipfile.ZipFile(p) as z:cls.script=z.read('assets/frida_script.js');cls.manifest=z.read('AndroidManifest.xml')

    def test_script_counter_only(self):
        after=self.script.replace(b'const PATCH_VERSION = 205;',b'const PATCH_VERSION = 206;')
        self.assertEqual(g.compare_script(self.script,after)['party_books_preserved'],920)

    def test_reject_classifier_change(self):
        after=self.script.replace(b'const PATCH_VERSION = 205;',b'const PATCH_VERSION = 206;').replace(b'function isImported(scene)',b'function isImportedElsewhere(scene)')
        with self.assertRaises(g.common.GuardError):g.compare_script(self.script,after)

    def test_reject_removed_dead_party_marker(self):
        after=self.script.replace(b'const PATCH_VERSION = 205;',b'const PATCH_VERSION = 206;').replace(b'"1000099":[],',b'')
        with self.assertRaises(g.common.GuardError):g.compare_script(self.script,after)

    def test_binary_version_value_only(self):
        after,r=g.expected_manifest(self.manifest);pos=r['value_offset']
        self.assertEqual(self.manifest[:pos],after[:pos]);self.assertEqual(self.manifest[pos+4:],after[pos+4:])
        self.assertEqual(int.from_bytes(after[pos:pos+4],'little'),206)

    def test_reject_repeat_manifest_patch(self):
        after,_=g.expected_manifest(self.manifest)
        with self.assertRaises(g.common.GuardError):g.expected_manifest(after)

class ApkTests(unittest.TestCase):
    def fixtures(self,d,change=None):
        old={'assets/frida_script.js':b'script','assets/content_delivery.tsv':b'catalog','assets/side_stories/manifest.tsv':b'side'}
        old.update({'assets/startup'+str(i):b'boot'+str(i).encode() for i in range(167)})
        old.update({'AndroidManifest.xml':b'version205','classes.dex':b'unchanged runtime','lib/arm64-v8a/libgame.so':b'unchanged native','res/movie.xml':b'unchanged movie UI'})
        new={**old,**{n:b'206 '+old[n] for n in g.ALLOWED_APK_MEMBERS}}
        if change:change(new)
        result=[]
        for label,members in (('old',old),('new',new)):
            p=Path(d)/(label+'.apk')
            with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
                for n,blob in members.items():z.writestr(n,blob)
            result.append(p)
        return result

    def test_exact_four_changes_and_runtime(self):
        with tempfile.TemporaryDirectory() as d,patch.object(g,'BASELINE205_DEX_SHA',g.sha(b'unchanged runtime')):
            r=g.compare_apk_members(*self.fixtures(d));self.assertEqual(len(r['changed_members']),4)

    def test_reject_new_runtime_dex(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(g.common.GuardError,'Unrequested APK'):g.compare_apk_members(*self.fixtures(d,lambda x:x.update({'classes.dex':b'new runtime'})))

    def test_reject_new_native(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(g.common.GuardError):g.compare_apk_members(*self.fixtures(d,lambda x:x.update({'lib/arm64-v8a/libgame.so':b'new native'})))

    def test_reject_startup_change(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(g.common.GuardError):g.compare_apk_members(*self.fixtures(d,lambda x:x.update({'assets/startup0':b'missing startup'})))

    def test_reject_movie_UI_change(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(g.common.GuardError):g.compare_apk_members(*self.fixtures(d,lambda x:x.update({'res/movie.xml':b'new UI'})))

    def test_reject_added_boot_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(g.common.GuardError,'addition/removal'):g.compare_apk_members(*self.fixtures(d,lambda x:x.update({'assets/bootstrap_inventory.json':b'{}'})))

class ActualCleanupFormulaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys,json
        sys.path.insert(0,'T:/Projects/FFBE Patch/story-ports/side-stories/scripts')
        from common import rows_bytes
        cls.tables={stem:rows_bytes((g.PAYLOAD205/('side_stories/'+stem+'.dat')).read_bytes(),stem) for stem in g.TABLE_KEYS}
        cls.plan=json.loads((g.ROOT/'audit/CLEANUP_PLAN.json').read_bytes())
        cls.formula,cls.orders=g.authorized_table_operations(cls.tables)

    def test_actual_scope_matches_all_declared_operations(self):
        for row in self.plan['table_changes']:
            self.assertEqual(g.canonical_operations(row['operations']),g.canonical_operations(self.formula[row['stem']]))
        self.assertEqual(self.orders,{'7074':'1507','7075':'1508'})

    def test_unrequested_book_7067_cannot_be_removed(self):
        operations=list(self.formula['Nm36woZx'])
        row=next(r for r in self.tables['Nm36woZx'] if r[g.BOOK]=='7067')
        operations.append({'op':'remove','id':'7067','before':row})
        self.assertNotEqual(g.canonical_operations(operations),g.canonical_operations(self.formula['Nm36woZx']))

    def test_unrequested_title_translation_cannot_be_folded_into_move(self):
        import copy
        operations=copy.deepcopy(self.formula['Nm36woZx']);op=next(x for x in operations if x['op']=='update' and g.SEASON in x['fields'])
        op['fields']['G4L0YIB2']={'before':'prior','after':'new title'}
        self.assertNotEqual(g.canonical_operations(operations),g.canonical_operations(self.formula['Nm36woZx']))

    def test_child_season_move_cannot_be_omitted(self):
        operations=self.formula['IL78hX09']
        self.assertNotEqual(g.canonical_operations(operations[1:]),g.canonical_operations(operations))

    def test_new_operations_cannot_add_rows(self):
        with self.assertRaises(g.common.GuardError):g.canonical_operations([{'op':'add','id':'9999999'}])

    def test_baseline_unknown_archived_family_rejected(self):
        import copy
        tables=copy.deepcopy(self.tables);row=dict(tables['Nm36woZx'][0]);row[g.BOOK]='999999';row[g.SEASON]='91';tables['Nm36woZx'].append(row)
        with self.assertRaises(g.common.GuardError):g.authorized_table_operations(tables)

    def test_actual_relative_positions_preserved_with_no_global_legacy_repairs(self):
        candidates={}
        for stem,ops in self.formula.items():
            key=g.TABLE_KEYS[stem];old=self.tables[stem];index={r[key]:r for r in old}
            updates=[{'key':[op['id']],'before':index[op['id']],'fields':op['fields']} for op in ops if op['op']=='update']
            removals=[{'key':[op['id']],'before':op['before']} for op in ops if op['op']=='remove']
            candidates[stem]=g.apply_exact_operations(old,[key],updates,removals)
            old_positions={r[key]:i for i,r in enumerate(old)}
            positions=[old_positions[r[key]] for r in candidates[stem]]
            self.assertEqual(positions,sorted(positions))
        self.assertEqual(len(g.relationship_observations(self.tables)),1735)
        self.assertEqual(g.relationship_observations(candidates),g.relationship_observations(self.tables))

class MetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(g.APK205) as z:
            cls.old_catalog=z.read('assets/content_delivery.tsv');cls.old_side=z.read('assets/side_stories/manifest.tsv')

    def fixture(self):
        old=g.common.parse_catalog(self.old_catalog);side=g.common.parse_side_manifest(self.old_side)
        names=['side_stories/'+s+'.dat' for s in g.TABLE_KEYS]+['side_stories/spdungeon9.cpk'];files={}
        for i,name in enumerate(names):
            digest=g.sha(('new206-'+name).encode());files[name]={'sha256':digest,'bytes':100+i}
            parts=list(old[name]['parts']);parts[1]=digest;parts[2]=str(100+i)
            parts[3]='https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/frozen-test206/event.pack';parts[4:]=['0',str(100+i),'0','1000']
            old[name]['line']='\t'.join(parts)
            leaf=name.removeprefix('side_stories/');parts=side[leaf]['line'].split('\t');parts[1]=digest
            parts[2]=','.join(sorted(side[leaf]['accepted']|{side[leaf]['sha256']}));side[leaf]['line']='\t'.join(parts)
        catalog=('ffbe-content-v1\n'+'\n'.join(r['line'] for r in old.values())+'\n').encode()
        manifest=('\n'.join(r['line'] for r in side.values())+'\n').encode()
        return catalog,manifest,files

    def test_exact_five_updates_and_prior205_acceptance(self):
        catalog,side,files=self.fixture();_,r=g.compare_metadata(self.old_catalog,catalog,self.old_side,side,files)
        self.assertEqual(len(r['catalog_changes']),5);self.assertEqual(len(r['side_manifest_changes']),5)

    def test_reject_unchanged_descriptor_retarget(self):
        catalog,side,files=self.fixture();lines=catalog.splitlines();lines[1]=lines[1].replace(b'https://',b'http://')
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,b'\n'.join(lines)+b'\n',self.old_side,side,files)

    def test_reject_catalog_reorder(self):
        catalog,side,files=self.fixture();lines=catalog.splitlines();lines[1],lines[2]=lines[2],lines[1]
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,b'\n'.join(lines)+b'\n',self.old_side,side,files)

    def test_reject_catalog_path_removal(self):
        catalog,side,files=self.fixture();lines=catalog.splitlines();lines.pop(1)
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,b'\n'.join(lines)+b'\n',self.old_side,side,files)

    def test_reject_changed_path_nonimmutable_transport(self):
        catalog,side,files=self.fixture();catalog=catalog.replace(b'/download/frozen-test206/',b'/download/latest/')
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,catalog,self.old_side,side,files)

    def test_reject_unlisted_accepted_hash(self):
        catalog,side,files=self.fixture();lines=side.splitlines();index=next(i for i,line in enumerate(lines) if line.startswith(b'D2zaT7Ru.dat\t'))
        p=lines[index].split(b'\t');p[2]+=b','+b'f'*64;lines[index]=b'\t'.join(p)
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,catalog,self.old_side,b'\n'.join(lines)+b'\n',files)

    def test_reject_prior205_current_hash_lost(self):
        catalog,side,files=self.fixture();prior=g.common.parse_side_manifest(self.old_side)['D2zaT7Ru.dat']['sha256'].encode()
        side=side.replace(prior,b'e'*64)
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,catalog,self.old_side,side,files)

    def test_reject_unlisted_side_row_change(self):
        catalog,side,files=self.fixture();lines=side.splitlines();p=lines[0].split(b'\t');p[1]=b'a'*64;lines[0]=b'\t'.join(p)
        with self.assertRaises(g.common.GuardError):g.compare_metadata(self.old_catalog,catalog,self.old_side,b'\n'.join(lines)+b'\n',files)

class TransportTests(unittest.TestCase):
    def fixture(self,d):
        import json,zlib
        root=Path(d);payload=root/'payload';payload.mkdir();(payload/'side_stories').mkdir()
        cleanup=root/'cleanup.json';cleanup.write_bytes(b'finite cleanup');banners=root/'banners.json';banners.write_bytes(b'finite banners')
        files={};packed=bytearray();parts=[];rows=[]
        with zipfile.ZipFile(g.APK205) as z:catalog=g.common.parse_catalog(z.read('assets/content_delivery.tsv'));side=z.read('assets/side_stories/manifest.tsv');base_sha=g.sha(z.read('assets/base_delivery.tsv'))
        for name in sorted(['side_stories/'+x+'.dat' for x in g.TABLE_KEYS]+['side_stories/spdungeon9.cpk']):
            raw=(name*20).encode();(payload/name).write_bytes(raw);files[name]={'bytes':len(raw),'sha256':g.sha(raw)}
            compressor=zlib.compressobj(6,zlib.DEFLATED,-15);wire=compressor.compress(raw)+compressor.flush()
            item={'path':name,**files[name],'offset':len(packed),'wire_bytes':len(wire),'wire_sha256':g.sha(wire)};parts.append(item);packed.extend(wire)
        identity=g.sha(json.dumps([{'path':p,**files[p]} for p in sorted(files)],sort_keys=True,separators=(',',':')).encode())
        tag='beta-content-v206-'+identity[:16];prefix='https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/'+tag+'/'
        pack=root/('event-cleanup-v206-'+g.sha(packed)[:16]+'.pack');pack.write_bytes(packed);url=prefix+pack.name
        for item in parts:
            name=item['path'];p=[name,item['sha256'],str(item['bytes']),url,str(item['offset']),str(item['wire_bytes']),'8',str(len(packed))]
            catalog[name]=g.common.parse_catalog(('ffbe-content-v1\n'+'\t'.join(p)+'\n').encode())[name]
        content=('ffbe-content-v1\n'+'\n'.join(r['line'] for r in catalog.values())+'\n').encode();(payload/'content_delivery.tsv').write_bytes(content);(payload/'side_stories/manifest.tsv').write_bytes(side)
        published=root/('content_delivery-'+g.sha(content)[:16]+'.tsv');published.write_bytes(content)
        manifest={'schema':'ffbe-event-cleanup-assets-v1','channel':'beta','asset_version':206,'APK_min_version':206,'source_build205_sha256':g.BASELINE205_SHA,'release_tag':tag,'bundled_side_manifest_sha256':g.sha(side),'package':'com.square_enix.ffbejpn','signing_certificate_sha256':g.common.SIGNER_SHA,'source_patch5_sha256':g.common.BASELINE_SHA,'base_catalog_unchanged_sha256':base_sha,'content_catalog':{'url':prefix+published.name,'bytes':len(content),'sha256':g.sha(content)},'assets':[]}
        for name,row in catalog.items():manifest['assets'].append({'path':name,'sha256':row['sha256'],'bytes':row['bytes'],'version':206 if name in files else 205,'transport':{'url':row['url'],'offset':row['offset'],'wire_bytes':row['wirebytes'],'method':row['method'],'source_bytes':row['sourcebytes']}})
        manifest_path=root/('event-assets-'+identity[:16]+'.json');manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        plan={'schema':'ffbe-event-cleanup-download-plan-v1','passed':True,'cleanup_plan_sha256':g.common.file_sha(cleanup),'banner_plan_sha256':g.common.file_sha(banners),'new_paths':[],'unchanged_original_rows':1893,'modified_original_paths':list(files),'new_pack':{'path':str(pack),'name':pack.name,'bytes':len(packed),'sha256':g.sha(packed),'url':url},'new_pack_files':parts,'files':[],'release_tag':tag,'catalog_identity_sha256':identity,'content_catalog_sha256':g.sha(content),'side_manifest_sha256':g.sha(side),'unchanged_base_catalog_sha256':base_sha}
        for role,p in [('pack',pack),('catalog',published),('manifest',manifest_path)]:plan['files'].append({'role':role,'name':p.name,'local_path':str(p),'bytes':p.stat().st_size,'sha256':g.common.file_sha(p)})
        plan_path=root/'plan.json';plan_path.write_text(json.dumps(plan),encoding='utf-8')
        return payload,catalog,files,plan_path,cleanup,banners,plan

    def test_five_exact_streams(self):
        with tempfile.TemporaryDirectory() as d:
            args= self.fixture(d);r=g.qualify_transports(*args[:6]);self.assertEqual(len(r['exact_local_deflate_slices']),5)

    def test_reject_overlapping_range(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(d);args[-1]['new_pack_files'][1]['offset']=0;args[3].write_text(json.dumps(args[-1]))
            with self.assertRaises(g.common.GuardError):g.qualify_transports(*args[:6])

    def test_reject_wrong_source_bytes_even_with_plan_pins_updated(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(d);name=next(iter(args[2]));(args[0]/name).write_bytes(b'unrequested source bytes')
            with self.assertRaises(g.common.GuardError):g.qualify_transports(*args[:6])

    def test_reject_additional_packed_path(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(d);args[-1]['new_pack_files'].append(dict(args[-1]['new_pack_files'][0]));args[3].write_text(json.dumps(args[-1]))
            with self.assertRaises(g.common.GuardError):g.qualify_transports(*args[:6])

    def test_reject_publication_manifest_descriptor_change(self):
        import json
        with tempfile.TemporaryDirectory() as d:
            args=self.fixture(d);item=next(r for r in args[-1]['files'] if r['role']=='manifest');p=Path(item['local_path']);m=json.loads(p.read_bytes());m['assets'][0]['sha256']='f'*64;p.write_text(json.dumps(m));item['sha256']=g.common.file_sha(p);item['bytes']=p.stat().st_size;args[3].write_text(json.dumps(args[-1]))
            with self.assertRaises(g.common.GuardError):g.qualify_transports(*args[:6])

if __name__=='__main__':unittest.main()
