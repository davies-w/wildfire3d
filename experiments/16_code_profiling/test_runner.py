import tempfile,unittest,json,os
from pathlib import Path
from unittest.mock import patch
import worker

class Runner(unittest.TestCase):
 def test_cpu_and_incomplete(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/'decks').mkdir();(root/'data').mkdir()
   binary=root/'fakefds';binary.write_text('''#!/usr/bin/env python3
import time,pathlib,sys
name=pathlib.Path(sys.argv[1]).stem
start=time.monotonic()
while time.monotonic()-start<.5 and not pathlib.Path(name+'.stop').exists():
 x=sum(i*i for i in range(1000))
complete=not pathlib.Path(name+'.stop').exists()
pathlib.Path(name+'.out').write_text('FDS completed successfully')
pathlib.Path(name+'_devc.csv').write_text('s,C\\nTime,temperature\\n'+('1,20\\n' if complete else '.1,20\\n'))
''');binary.chmod(0o755)
   with patch.object(worker,'ROOT',root),patch.object(worker,'DATA',root/'data'),patch.object(worker,'BINARY',str(binary)),patch.object(worker,'upload'):
    for name,limit,complete in [('complete',5,True),('cutoff',.01,False)]:
     (root/'decks'/(name+'.fds')).write_text('fake')
     r=worker.run(dict(case=name,profile=False,horizon_s=1,variant='baseline'),limit)
     self.assertEqual(r['full_horizon'],complete)
     self.assertGreater(r['cpu_user_s'],0)
     self.assertEqual(r['stopped_by_budget'],not complete)

if __name__=='__main__':unittest.main()
