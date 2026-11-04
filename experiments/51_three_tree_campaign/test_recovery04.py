"""Exercise archive restore only; never invoke FDS or network."""
import unittest,sys,types,hashlib,io,tarfile,tempfile
from pathlib import Path
import worker03
sys.modules['worker_base04']=worker03
sys.modules['transport']=types.SimpleNamespace(upload=None,token=None)
from recovery_worker04 import restore_archive
class RestoreTests(unittest.TestCase):
 def archive(self,name='evidence/state.restart',symlink=False):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w:gz') as t:
   m=tarfile.TarInfo(name)
   if symlink:m.type=tarfile.SYMTYPE;m.linkname='/tmp/outside'
   else:m.size=3
   t.addfile(m,None if symlink else io.BytesIO(b'abc'))
  b.seek(0);return b
 def test_hash_verified_restore(self):
  with tempfile.TemporaryDirectory() as d:
   restore_archive(self.archive(),Path(d),[dict(name='state.restart',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())]);self.assertEqual((Path(d)/'state.restart').read_bytes(),b'abc')
 def test_corrupt_file_rejected(self):
  with tempfile.TemporaryDirectory() as d,self.assertRaises(AssertionError):restore_archive(self.archive(),Path(d),[dict(name='state.restart',bytes=3,sha256='0'*64)])
 def test_escape_rejected(self):
  with tempfile.TemporaryDirectory() as d,self.assertRaises(AssertionError):restore_archive(self.archive('evidence/../outside'),Path(d),[])
 def test_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as d,self.assertRaises(AssertionError):restore_archive(self.archive(symlink=True),Path(d),[])
if __name__=='__main__':unittest.main()
