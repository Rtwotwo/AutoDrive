import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from sources import write_json


class AtomicJsonTests(unittest.TestCase):
    def test_transient_lock_retries_local_replace_and_permanent_failure_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'receipt.json'
            write_json(target, {'state':'unknown'})
            original=Path.replace
            calls=[]
            def once_locked(source,destination):
                calls.append(source)
                if len(calls)==1:raise PermissionError('simulated reader lock')
                return original(source,destination)
            with patch.object(Path,'replace',once_locked),patch('time.sleep'):
                write_json(target, {'state':'submitted','media_id':'FIXTURE'})
            self.assertEqual(len(calls),2)
            self.assertEqual(json.loads(target.read_text())['state'],'submitted')
            with patch.object(Path,'replace',side_effect=PermissionError('persistent lock')) as replace,patch('time.sleep'):
                with self.assertRaises(PermissionError):write_json(target, {'state':'failed'})
                self.assertEqual(replace.call_count,8)
            self.assertEqual(json.loads(target.read_text())['state'],'submitted')
            self.assertEqual(list(Path(tmp).glob('*.tmp')),[])
