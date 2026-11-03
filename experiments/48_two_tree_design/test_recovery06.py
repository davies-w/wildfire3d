"""Offline restoration tests only; no FDS, network or cloud creation."""
import sys,types,unittest,io,tarfile,tempfile,hashlib
from pathlib import Path
sys.modules['transport']=types.SimpleNamespace(upload=None,token=None)
from recovery_worker06 import restore_archive
class RestoreTests(unittest.TestCase):
 def restore(self,name,data,expected):
  b=io.BytesIO()
  with tarfile.open(fileobj=b,mode='w:gz') as t:
   m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
  b.seek(0)
  with tempfile.TemporaryDirectory() as td:
   restore_archive(b,Path(td),expected)
   return (Path(td)/'case.restart').read_bytes()
 def test_exact_checkpoint_restored(self):
  data=b'saved solver state';f=dict(name='case.restart',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
  self.assertEqual(self.restore('evidence/case.restart',data,[f]),data)
 def test_wrong_hash_rejected(self):
  with self.assertRaises(AssertionError):self.restore('evidence/case.restart',b'wrong',[dict(name='case.restart',bytes=5,sha256='0'*64)])
 def test_path_traversal_rejected(self):
  with self.assertRaises(AssertionError):self.restore('evidence/../case.restart',b'x',[])
if __name__=='__main__':unittest.main()
