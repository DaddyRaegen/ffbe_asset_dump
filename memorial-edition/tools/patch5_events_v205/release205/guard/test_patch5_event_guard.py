"""Mutation tests for the minimal Patch 5 release policy; no network/device."""
from pathlib import Path
import copy, json, tempfile, unittest, zipfile
import patch5_event_guard as g

P5_INSPECTION = Path(__file__).resolve().parents[1]/'audit/original-downloader'

def catrow(path, digest='a'*64, size=7, url=None):
    return '\t'.join((path,digest,str(size),url or
        'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/event-v205/events.pack',
        '0',str(size),'0',str(size)))

def catalog(rows):
    return ('ffbe-content-v1\n'+'\n'.join(rows)+'\n').encode()

def smali_fixture():
    original=g.smali_tree(P5_INSPECTION/'smali')
    candidate=dict(original)
    for p in g.ALLOWED_CLASSES:
        candidate[p]=g.expected_class(p,original[p])
    receipt={'schema':'ffbe-patch5-minimal-event-paths-smali-v1','classes':[
        {'path':p,'before_sha256':g.sha(original[p].encode()),'after_sha256':g.sha(candidate[p].encode())}
        for p in sorted(g.ALLOWED_CLASSES)]}
    return original,candidate,receipt

class RowPolicyTests(unittest.TestCase):
    def setUp(self):
        self.old=[{'id':'1','name':'Original','ref':'7'},{'id':'2','name':'Other','ref':'8'}]
        self.new=self.old+[{'id':'3','name':'Event','ref':'9'}]

    def test_accept_exact_additive_rows(self):
        self.assertEqual(g.compare_rows(self.old,self.new,['id'],['3'])['added_rows'],1)

    def test_reject_original_field_change(self):
        bad=copy.deepcopy(self.new);bad[0]['name']='Changed'
        with self.assertRaisesRegex(g.GuardError,'Original master'):
            g.compare_rows(self.old,bad,['id'])

    def test_reject_reordered_original(self):
        with self.assertRaises(g.GuardError):g.compare_rows(self.old,list(reversed(self.old))+self.new[2:],['id'])

    def test_reject_original_deletion(self):
        with self.assertRaises(g.GuardError):g.compare_rows(self.old,self.new[1:],['id'])

    def test_reject_duplicate_id(self):
        with self.assertRaisesRegex(g.GuardError,'Duplicate'):g.compare_rows(self.old,self.new+[self.new[0]],['id'])

    def test_reject_unplanned_new_identity(self):
        with self.assertRaisesRegex(g.GuardError,'identity'):g.compare_rows(self.old,self.new,['id'],['4'])

    def test_composite_identity(self):
        old=[{'id':'1','level':'a'}];new=old+[{'id':'1','level':'b'}]
        self.assertEqual(g.compare_rows(old,new,['id','level'],[['1','b']])['added_rows'],1)

class ReferencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tables={'D2zaT7Ru':[{'2ShgIRU8':'1'}],
            'Nm36woZx':[{'M9mwe2cu':'2','2ShgIRU8':'1'}],
            '9Zdr5ap0':[{'vG1hSm79':'3','M9mwe2cu':'2','2ShgIRU8':'1'}],
            'IL78hX09':[{'VMkv7S9R':'4','vG1hSm79':'3','M9mwe2cu':'2','2ShgIRU8':'1'}]}
        self.counts={s:0 for s in self.tables}

    def test_complete_chain(self):
        self.assertEqual(g.reference_closure(self.tables,self.counts)['added_playback_count'],1)

    def test_missing_parent(self):
        self.tables['IL78hX09'][0]['vG1hSm79']='99'
        with self.assertRaisesRegex(g.GuardError,'missing/mismatched'):g.reference_closure(self.tables,self.counts)

    def test_mismatched_season(self):
        self.tables['9Zdr5ap0'][0]['2ShgIRU8']='99'
        with self.assertRaises(g.GuardError):g.reference_closure(self.tables,self.counts)

    def test_orphan_added_book(self):
        self.tables['Nm36woZx'].append({'M9mwe2cu':'99','2ShgIRU8':'1'})
        with self.assertRaisesRegex(g.GuardError,'no reachable child'):g.reference_closure(self.tables,self.counts)

class CatalogPolicyTests(unittest.TestCase):
    def setUp(self):
        self.lines=[catrow('side_stories/old'+str(i)+'.dat') for i in range(1411)]
        self.old=catalog(self.lines)
        self.files={'side_stories/event.dat':{'sha256':'b'*64,'bytes':9}}
        self.extra=catrow('side_stories/event.dat','b'*64,9)
        self.new=catalog(self.lines+[self.extra])

    def test_add_required_event_only(self):
        _,r=g.compare_catalog(self.old,self.new,self.files)
        self.assertEqual(r['original_rows_preserved'],1411);self.assertEqual(r['added_rows'],1)

    def test_reject_non_event_change(self):
        changed=self.lines[:];changed[0]=catrow('side_stories/old0.dat','c'*64)
        with self.assertRaisesRegex(g.GuardError,'Non-event'):g.compare_catalog(self.old,catalog(changed+[self.extra]),self.files)

    def test_reject_missing_original(self):
        with self.assertRaises(g.GuardError):g.compare_catalog(self.old,catalog(self.lines[1:]+[self.extra]),self.files)

    def test_reject_unlisted_addition(self):
        with self.assertRaisesRegex(g.GuardError,'Unlisted'):g.compare_catalog(self.old,catalog(self.lines+[self.extra,catrow('battle/new.dat')]),self.files)

    def test_reject_missing_dependency(self):
        with self.assertRaisesRegex(g.GuardError,'missing'):g.compare_catalog(self.old,self.old,self.files)

    def test_reject_bad_payload_pin(self):
        with self.assertRaisesRegex(g.GuardError,'pin mismatch'):g.compare_catalog(self.old,catalog(self.lines+[catrow('side_stories/event.dat','c'*64,9)]),self.files)

    def test_reject_latest_transport(self):
        bad=catrow('side_stories/event.dat','b'*64,9,'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/latest/download/e.pack')
        with self.assertRaisesRegex(g.GuardError,'immutable'):g.compare_catalog(self.old,catalog(self.lines+[bad]),self.files)

    def test_reject_other_host(self):
        bad=catrow('side_stories/event.dat','b'*64,9,'https://example.com/events.pack')
        with self.assertRaises(g.GuardError):g.compare_catalog(self.old,catalog(self.lines+[bad]),self.files)

    def test_reject_range_overshoot(self):
        bad=catrow('side_stories/event.dat','b'*64,9,'https://github.com/luminest-llc/ffbe-memorial-downloads/releases/download/event-v205/events.pack#ffbe-range=3:9:10')
        with self.assertRaisesRegex(g.GuardError,'range'):g.compare_catalog(self.old,catalog(self.lines+[bad]),self.files)

    def test_reject_original_order_change(self):
        with self.assertRaisesRegex(g.GuardError,'order'):g.compare_catalog(self.old,catalog(self.lines[::-1]+[self.extra]),self.files)

    def test_reject_duplicate_catalog_name(self):
        with self.assertRaisesRegex(g.GuardError,'duplicate'):g.parse_catalog(catalog(self.lines+[self.lines[0]]))

class ManifestPolicyTests(unittest.TestCase):
    def setUp(self):
        self.lines=['old'+str(i)+'.dat\t'+'a'*64+'\t'+'c'*64 for i in range(1370)]
        self.old=('\n'.join(self.lines)+'\n').encode()
        self.files={'side_stories/old0.dat':{'sha256':'b'*64,'bytes':7}}
        lines=self.lines[:];lines[0]='old0.dat\t'+'b'*64+'\t'+'a'*64+','+'c'*64
        self.new=('\n'.join(lines)+'\n').encode()
        self.cat={'side_stories/old0.dat':{'sha256':'b'*64}}

    def test_accept_original_history_and_new_hash(self):
        r=g.compare_side_manifest(self.old,self.new,self.files,self.cat)
        self.assertEqual(len(r['side_manifest_changes']),1)

    def test_reject_lost_accepted_history(self):
        bad=self.new.replace(('a'*64+','+'c'*64).encode(),('a'*64).encode(),1)
        with self.assertRaisesRegex(g.GuardError,'accepted'):g.compare_side_manifest(self.old,bad,self.files,self.cat)

    def test_reject_lost_original_current(self):
        bad=self.new.replace(('a'*64+','+'c'*64).encode(),('c'*64).encode(),1)
        with self.assertRaisesRegex(g.GuardError,'current'):g.compare_side_manifest(self.old,bad,self.files,self.cat)

    def test_reject_unlisted_accepted_hash(self):
        bad=self.new.replace(('a'*64+','+'c'*64).encode(),('a'*64+','+'c'*64+','+'d'*64).encode(),1)
        with self.assertRaisesRegex(g.GuardError,'Unlisted accepted'):g.compare_side_manifest(self.old,bad,self.files,self.cat)

    def test_reject_new_variant_in_original_row(self):
        bad=self.new.replace(('old0.dat\t'+'b'*64+'\t'+'a'*64+','+'c'*64).encode(),
            ('old0.dat\t'+'b'*64+'\t'+'a'*64+','+'c'*64+'\t'+'d'*64+'=other.dat').encode())
        with self.assertRaisesRegex(g.GuardError,'variant mapping'):g.compare_side_manifest(self.old,bad,self.files,self.cat)

    def test_reject_extra_metadata_change(self):
        bad=self.new.replace(('old1.dat\t'+'a'*64).encode(),('old1.dat\t'+'b'*64).encode())
        with self.assertRaisesRegex(g.GuardError,'Unlisted'):g.compare_side_manifest(self.old,bad,self.files,self.cat)

    def test_reject_hash_mismatch_to_catalog(self):
        self.cat['side_stories/old0.dat']['sha256']='d'*64
        with self.assertRaisesRegex(g.GuardError,'hash differs'):g.compare_side_manifest(self.old,self.new,self.files,self.cat)

    def test_reject_traversal_variant(self):
        with self.assertRaises(g.GuardError):g.parse_side_manifest(('a.dat\t'+'a'*64+'\t\t'+'b'*64+'=../a.dat').encode())

class ScriptPolicyTests(unittest.TestCase):
    def setUp(self):
        self.old=(P5_INSPECTION/'frida_script.js').read_bytes()

    def test_preserve_original_parties_and_hooks(self):
        blob,r=g.expected_script(self.old,[9999999])
        self.assertEqual(r['added_party_book_count'],1)
        self.assertIn(g.UPDATER_URL.encode(),blob)
        self.assertIn(b'"9999999":[]',blob)

    def test_reject_original_book_override(self):
        text=self.old.decode();start=text.index('const SIDE_STORY_PARTIES = ')+len('const SIDE_STORY_PARTIES = ')
        parties,_=json.JSONDecoder().raw_decode(text[start:])
        with self.assertRaisesRegex(g.GuardError,'original book'):g.expected_script(self.old,[next(iter(parties['books']))])

    def test_reject_duplicate_new_book(self):
        with self.assertRaisesRegex(g.GuardError,'Duplicate'):g.expected_script(self.old,[9999999,9999999])

    def test_script_change_outside_party_map_differs(self):
        expected,_=g.expected_script(self.old,[9999999])
        with self.assertRaisesRegex(g.GuardError,'Script changed'):
            g.compare_script(self.old,expected+b'\n// lifecycle change',[9999999])

    def test_reject_removed_original_party_entry(self):
        expected,_=g.expected_script(self.old,[9999999])
        text=expected.decode();start=text.index('const SIDE_STORY_PARTIES = ')+len('const SIDE_STORY_PARTIES = ')
        parties,length=json.JSONDecoder().raw_decode(text[start:]);parties['entries'].pop(next(iter(parties['entries'])))
        bad=(text[:start]+json.dumps(parties,separators=(',',':'))+text[start+length:]).encode()
        with self.assertRaisesRegex(g.GuardError,'Script changed'):g.compare_script(self.old,bad,[9999999])

    def test_reject_production_update_route(self):
        expected,_=g.expected_script(self.old,[9999999])
        bad=expected.replace(g.UPDATER_URL.encode(),b'https://example.com/prod.json')
        with self.assertRaisesRegex(g.GuardError,'Script changed'):g.compare_script(self.old,bad,[9999999])

class BinaryManifestTests(unittest.TestCase):
    def setUp(self):
        p=Path('T:/Projects/FFBE Patch/localization-rounds/2026-09-29-units-cards-ios/dist/FFBE-Memorial-EN-Patch-5-Units-Cards.apk')
        with zipfile.ZipFile(p) as z:self.original=z.read('AndroidManifest.xml')

    def test_exact_version_value_only(self):
        expected,receipt=g.expected_manifest(self.original)
        pos=receipt['versionCode_offset']
        self.assertEqual(expected[:pos],self.original[:pos]);self.assertEqual(expected[pos+4:],self.original[pos+4:])
        self.assertEqual(int.from_bytes(expected[pos:pos+4],'little'),205)

    def test_reject_wrong_baseline_version(self):
        expected,_=g.expected_manifest(self.original)
        with self.assertRaisesRegex(g.GuardError,'199'):g.expected_manifest(expected)

class DexPolicyTests(unittest.TestCase):
    def setUp(self):
        self.old,self.new,self.receipt=smali_fixture()

    def test_accept_exact_two_minimal_edits(self):
        r=g.compare_smali(self.old,self.new,self.receipt)
        self.assertEqual(len(r['changed_classes']),2)

    def test_accept_real_reassembled_reference(self):
        decoded=g.smali_tree(P5_INSPECTION/'patched-decoded-smali')
        self.assertTrue(decoded)
        self.new.update(decoded)
        g.compare_smali(self.old,self.new,self.receipt)

    def test_reject_new_runtime_class(self):
        self.new['O1/GameAssets.smali']='.class public LO1/GameAssets;\n'
        with self.assertRaisesRegex(g.GuardError,'addition/removal'):g.compare_smali(self.old,self.new,self.receipt)

    def test_reject_modified_startup(self):
        p='com/square_enix/ffbejpn/Lapis.smali';self.new[p]+='\n# startup gate\n'
        with self.assertRaisesRegex(g.GuardError,'Unlisted DEX'):g.compare_smali(self.old,self.new,self.receipt)

    def test_reject_extra_instruction_in_allowed_class(self):
        self.new['O1/SideStoryTables.smali']=self.new['O1/SideStoryTables.smali'].replace('    return-void','    nop\n\n    return-void',1)
        with self.assertRaisesRegex(g.GuardError,'Unlisted DEX'):g.compare_smali(self.old,self.new,self.receipt)

    def test_normalization_preserves_string_literals(self):
        a='.method a()V\n :cond_ab\n const-string v0, ":cond_ab"\n goto :cond_ab\n.end method\n'
        b=a.replace(':cond_ab\n',':cond_cd\n').replace('goto :cond_ab','goto/16 :cond_cd')
        self.assertEqual(g.normalize_smali(a)[0],g.normalize_smali(b)[0])
        self.assertNotEqual(g.normalize_smali(a)[0],g.normalize_smali(a.replace('\":cond_ab\"','\":cond_cd\"'))[0])

    def test_branch_target_change_rejected(self):
        a='.method a()V\n :cond_a\n nop\n :cond_b\n goto :cond_a\n.end method\n'
        self.assertNotEqual(g.normalize_smali(a)[0],g.normalize_smali(a.replace('goto :cond_a','goto :cond_b'))[0])

    def test_case_collision_suffix_does_not_change_dex_identity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'B.smali').write_bytes(b'.class public LG0/B;\r\n')
            (root/'b.1.smali').write_bytes(b'.class public LG0/b;\r\n')
            self.assertEqual(set(g.smali_tree(root)),{'G0/B.smali','G0/b.smali'})

    def test_duplicate_actual_class_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'a.smali').write_bytes(b'.class public LG0/B;\n')
            (root/'other.smali').write_bytes(b'.class public LG0/B;\n')
            with self.assertRaisesRegex(g.GuardError,'Duplicate disassembled'):g.smali_tree(root)

class ApkMemberPolicyTests(unittest.TestCase):
    def fixture(self,root,mutation=None):
        assets={'assets/frida_script.js':b'old','assets/content_delivery.tsv':b'old','assets/side_stories/manifest.tsv':b'old'}
        assets.update({'assets/startup'+str(i)+'.dat':b'boot'+str(i).encode() for i in range(167)})
        members={**assets,'AndroidManifest.xml':b'manifest','classes.dex':b'dex','lib/arm64-v8a/libgame.so':b'native','res/view.xml':b'UI'}
        newer={**members,**{p:b'new '+members[p] for p in g.ALLOWED_MEMBERS}}
        if mutation:mutation(newer)
        paths=[]
        for name,entries in (('old',members),('new',newer)):
            path=Path(root)/(name+'.apk')
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
                for p,blob in entries.items():z.writestr(p,blob)
            paths.append(path)
        return paths

    def test_accept_only_five_changes(self):
        with tempfile.TemporaryDirectory() as d:
            r=g.compare_members(*self.fixture(d));self.assertEqual(len(r['changed_members']),5)

    def test_reject_changed_startup_asset(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(g.GuardError,'Unlisted'):g.compare_members(*self.fixture(d,lambda x:x.update({'assets/startup1.dat':b'broken'})))

    def test_reject_native_change(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(g.GuardError):g.compare_members(*self.fixture(d,lambda x:x.update({'lib/arm64-v8a/libgame.so':b'newnative'})))

    def test_reject_new_asset_member(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(g.GuardError,'addition/removal'):g.compare_members(*self.fixture(d,lambda x:x.update({'assets/root_assets_manifest.json':b'{}'})))

    def test_reject_UI_change(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(g.GuardError):g.compare_members(*self.fixture(d,lambda x:x.update({'res/view.xml':b'newUI'})))

class ArtworkPolicyTests(unittest.TestCase):
    def setUp(self):
        self.original={'original.png':b'P5 original'}
        self.frozen={**self.original,'event.png':b'new icon','unused.png':b'unused'}
        self.candidate={**self.original,'event.png':b'new icon'}

    def check(self):
        return g.compare_artwork_members(self.original,self.candidate,self.frozen,{'event.png'},lambda b:b[8:])

    def test_preserve_original_add_required_only(self):
        r=self.check();self.assertEqual(r['appended_member_count'],1)
        self.assertEqual(r['omitted_unused_new_members'],['unused.png'])

    def test_reject_changed_original_artwork(self):
        self.candidate['original.png']=b'changed'
        with self.assertRaisesRegex(g.GuardError,'Original Patch 5 artwork'):self.check()

    def test_reject_extra_unneeded_artwork(self):
        self.candidate['unused.png']=b'unused'
        with self.assertRaisesRegex(g.GuardError,'unneeded'):self.check()

    def test_reject_missing_required_artwork(self):
        self.candidate.pop('event.png')
        with self.assertRaises(g.GuardError):self.check()

    def test_reject_wrong_new_icon(self):
        self.candidate['event.png']=b'wrong icon'
        with self.assertRaisesRegex(g.GuardError,'frozen source'):self.check()

    def test_accept_decompressed_new_icon_preserve_raw_original(self):
        self.frozen['event.png']=b'CRILAYLAnew icon'
        self.check()

if __name__ == '__main__':
    unittest.main()
