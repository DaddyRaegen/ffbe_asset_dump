import hashlib,unittest,zlib
from verify_transports_independent import check_wire
from patch5_event_guard import GuardError

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.raw=b'Pinned event data'*20
        compressor=zlib.compressobj(6,zlib.DEFLATED,-15)
        self.wire=compressor.compress(self.raw)+compressor.flush()
        self.row={'wirebytes':len(self.wire),'method':8,'bytes':len(self.raw),'sha256':hashlib.sha256(self.raw).hexdigest()}

    def test_exact_raw_deflate_slice(self):
        self.assertEqual(check_wire(self.row,self.wire)['decoded_bytes'],len(self.raw))

    def test_reject_truncated_slice(self):
        self.row['wirebytes']-=1
        with self.assertRaises(GuardError):check_wire(self.row,self.wire[:-1])

    def test_reject_trailing_wire_bytes(self):
        self.row['wirebytes']+=3
        with self.assertRaisesRegex(GuardError,'trailing'):check_wire(self.row,self.wire+b'bad')

    def test_reject_wrong_decoded_hash(self):
        self.row['sha256']='a'*64
        with self.assertRaisesRegex(GuardError,'signed payload'):check_wire(self.row,self.wire)

    def test_reject_wrong_decoded_size(self):
        self.row['bytes']+=1
        with self.assertRaises(GuardError):check_wire(self.row,self.wire)

    def test_stored_bytes(self):
        self.row['method']=0;self.row['wirebytes']=len(self.raw)
        self.assertEqual(check_wire(self.row,self.raw)['decoded_bytes'],len(self.raw))

if __name__=='__main__':unittest.main()
