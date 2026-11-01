"""Confidentiality and DVC object-format checks; no network or training."""
import hashlib
import json
import unittest
import dvc_hf as h

class PublicationPolicy(unittest.TestCase):
    def test_budget_and_credentials_are_rejected(self):
        for value in [b'{"estimated_spend": 12}', b'{"private_key":"secret"}',
                      b'{"nested":{"access_token":"secret"}}']:
            self.assertIsNotNone(h.byte_policy('sample.json', value))
        self.assertIsNotNone(h.byte_policy('sample.bin', b'-----BEGIN PRIVATE KEY-----'))
        self.assertIsNotNone(h.path_policy('experiments/33_representation_loss/budget.json'))

    def test_scientific_metrics_are_allowed(self):
        self.assertIsNone(h.byte_policy('epoch.json', b'{"epoch": 21,"validation_error":0.05}'))
        self.assertIsNone(h.path_policy('experiments/42_stacked_gru64/data/model.pt'))

    def test_private_recovery_is_not_exported(self):
        self.assertIsNotNone(h.path_policy('experiments/43_repository_preservation/data/private/file.pt'))
        self.assertIsNotNone(h.path_policy('FDS/src/fds/.git/config'))

    def test_dvc_directory_encoding(self):
        entries=[{'md5':hashlib.md5(b'alpha\n').hexdigest(),'relpath':'a.txt'},
                 {'md5':hashlib.md5(bytes(range(256))).hexdigest(),'relpath':'b.bin'}]
        data=json.dumps(sorted(entries,key=lambda x:x['relpath']),sort_keys=True).encode()
        # Independently obtained from installed dvc add on these exact fixture bytes.
        self.assertEqual(hashlib.md5(data).hexdigest()+'.dir','2dc7bad54c8ec9d2ffd2b42d9aee9fdc.dir')

if __name__=='__main__':
    unittest.main()
