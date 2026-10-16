import tempfile,struct,unittest
from pathlib import Path
from symbolize import read_profile
class Format(unittest.TestCase):
 def test_counts_and_mappings(self):
  b=struct.pack('<5Q',0,3,0,10000,0)+struct.pack('<4Q',7,2,0x1010,0x2020)+struct.pack('<3Q',0,1,0)+b'1000-2000 r-xp 00000000 00:00 1 /usr/local/bin/fds\n'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'test.prof';p.write_bytes(b);period,records,maps=read_profile(p)
  self.assertEqual(period,10000);self.assertEqual(records,[(7,(0x1010,0x2020))]);self.assertEqual(maps,[(0x1000,0x2000,0,'/usr/local/bin/fds')])
if __name__=='__main__':unittest.main()
