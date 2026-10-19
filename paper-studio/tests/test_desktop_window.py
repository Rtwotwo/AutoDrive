import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
import uuid
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop_window import activate_existing
from desktop_window import claim_instance_mutex, release_instance_mutex, kernel


class ActivationTests(unittest.TestCase):
    def test_existing_unowned_mutex_does_not_block_restart(self):
        name='Local\\PaperStudioFixture'+uuid.uuid4().hex
        stale=kernel.CreateMutexW(None,False,name)
        handle=None
        try:
            handle=claim_instance_mutex(name)
            self.assertIsNotNone(handle)
        finally:
            release_instance_mutex(handle);kernel.CloseHandle(stale)

    def test_other_process_cannot_take_owned_mutex(self):
        name='Local\\PaperStudioFixture'+uuid.uuid4().hex
        handle=claim_instance_mutex(name)
        try:
            child=subprocess.run([sys.executable,'-c','from desktop_window import claim_instance_mutex;import sys;print(claim_instance_mutex(sys.argv[1]) is None)',name],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(child.returncode,0);self.assertEqual(child.stdout.strip(),'True')
        finally:release_instance_mutex(handle)

    def test_second_launch_waits_for_first_window_then_activates(self):
        with tempfile.TemporaryDirectory() as tmp:
            status = Path(tmp) / 'desktop-status.json'
            status.write_text(json.dumps({'pid': 1234}), encoding='utf-8')
            with patch('desktop_window.main_window', side_effect=[None, 5678]), \
                 patch('desktop_window.activate', side_effect=[False, True]) as activate, \
                 patch('desktop_window.time.sleep'):
                self.assertTrue(activate_existing(status, timeout=1))
            self.assertEqual(activate.call_args.args, (5678,))

    def test_missing_or_stale_status_is_not_a_successful_activation(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(activate_existing(Path(tmp) / 'absent.json', timeout=.01))


if __name__ == '__main__': unittest.main()
