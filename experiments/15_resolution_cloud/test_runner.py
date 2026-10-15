"""Regression for the container's shallow /study path and environment override."""
import json,os,unittest
from pathlib import Path
from unittest.mock import patch
import study

class ContainerPath(unittest.TestCase):
    def test_explicit_binary_does_not_evaluate_laptop_fallback(self):
        with patch.object(study,'ROOT',Path('/study')),patch.dict(os.environ,{'FDS_BINARY':'/usr/local/bin/fds'}),patch('sys.argv',['study.py','run','--cases=flow_medium']),patch.object(Path,'read_text',return_value=json.dumps([{'case':'flow_medium'}])),patch.object(study,'run_one') as run:
            study.main()
            self.assertEqual(run.call_args.args[-1],Path('/usr/local/bin/fds'))

if __name__=='__main__':unittest.main()
