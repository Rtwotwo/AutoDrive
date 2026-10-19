import http.cookiejar
import json
from pathlib import Path
import tempfile
import threading
import time
import subprocess
import sys
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import Studio, make_server
from writing import provider_config, chat_json
from desktop import DesktopActions
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article
from sources import extract_pdf


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.studio = Studio(self.tmp.name); self.studio.desktop = True
        self.server = make_server(self.studio, 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.cookies = http.cookiejar.CookieJar()
        self.client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.studio.pool.shutdown(wait=True)
        self.tmp.cleanup()

    def login(self):
        ticket = self.studio.launch_ticket
        self.client.open(self.url + '/launch?ticket=' + ticket).read()
        return ticket

    def post(self, path, body):
        request = urllib.request.Request(self.url + path, json.dumps(body).encode(),
                                         headers={'X-Studio-Token': self.studio.token, 'Content-Type': 'application/json'})
        return self.client.open(request).read()

    def test_all_reads_require_desktop_session_and_ticket_is_single_use(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        for path in ('/', '/app.js', '/api/session', '/api/jobs'):
            with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(self.url + path)
            self.assertEqual(error.exception.code, 403)
        ticket = self.login()
        session = json.load(self.client.open(self.url + '/api/session'))
        self.assertTrue(session['desktop'])
        cookie = list(self.cookies)[0]
        self.assertTrue(cookie.has_nonstandard_attr('HttpOnly'))
        with self.assertRaises(urllib.error.HTTPError): self.client.open(self.url + '/launch?ticket=' + ticket)
        request = urllib.request.Request(self.url + '/api/session', headers={'Origin': 'https://attacker.invalid'})
        with self.assertRaises(urllib.error.HTTPError): self.client.open(request)

    def test_memory_credentials_not_returned_written_or_reused_for_changed_host(self):
        self.login()
        fake = 'DESKTOP_TEST_SECRET_ONLY_123456789'
        self.post('/api/credentials', {'base_url': 'https://example.test/v1', 'model': 'test', 'api_key': fake})
        self.assertNotIn(fake.encode(), self.client.open(self.url + '/api/session').read())
        self.post('/api/credentials', {'base_url': 'https://example.test/v1', 'model': 'test', 'api_key': ''})
        self.assertEqual(self.studio.provider['api_key'], fake)
        with self.assertRaises(urllib.error.HTTPError):
            self.post('/api/credentials', {'base_url': 'https://different.test/v1', 'model': 'test', 'api_key': ''})
        for file in Path(self.tmp.name).rglob('*'):
            if file.is_file(): self.assertNotIn(fake.encode(), file.read_bytes())
        self.post('/api/credentials', {'clear': True})
        self.assertEqual(self.studio.provider, {})
        restarted = Studio(self.tmp.name)
        self.assertEqual(restarted.provider, {})
        restarted.pool.shutdown()
        with patch.dict('os.environ', {'PAPER_STUDIO_API_KEY': fake, 'PAPER_STUDIO_MODEL': 'test'}):
            with self.assertRaises(ValueError): provider_config({'model': 'test', '_desktop': True})

    def test_export_dialog_writes_bundle_and_cancel_writes_nothing(self):
        job = self.studio.create('fixture')
        manifest = extract_pdf(fixture_pdf(), self.studio.folder(job))
        self.studio.save_article(job, fixture_article(manifest))
        destination = Path(self.tmp.name) / 'chosen.zip'
        window = Mock(); window.create_file_dialog.return_value = (str(destination),)
        actions = DesktopActions(self.studio, window, Path(self.tmp.name) / 'exports')
        self.assertTrue(actions({'action': 'export', 'id': job, 'format': 'zip'})['ok'])
        self.assertTrue(destination.read_bytes().startswith(b'PK'))
        window.create_file_dialog.return_value = None
        self.assertTrue(actions({'action': 'export', 'id': job, 'format': 'md'})['cancelled'])
        with self.assertRaises(ValueError): actions({'action': 'export', 'id': '../outside', 'format': 'zip'})

    def test_clear_key_prevents_queued_generation_and_close_stops_formatter(self):
        self.login()
        job = self.studio.create('queued fixture')
        extract_pdf(fixture_pdf(), self.studio.folder(job))
        self.post('/api/credentials', {'base_url': 'https://example.test/v1', 'model': 'test', 'api_key': 'TEST_MEMORY_KEY'})
        event = threading.Event()
        self.studio.pool.submit(lambda: event.wait(5))
        with patch('writing.chat_json') as chat:
            self.post(f'/api/jobs/{job}/generate', {'base_url': 'https://example.test/v1', 'model': 'test'})
            self.post('/api/credentials', {'clear': True})
            event.set()
            for _ in range(100):
                if self.studio.jobs[job]['status'] == 'error': break
                time.sleep(.02)
            self.assertEqual(self.studio.jobs[job]['status'], 'error')
            chat.assert_not_called()
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'],
                                 creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        self.studio.processes.add(child)
        self.studio.close()
        self.assertIsNotNone(child.poll())

    def test_local_model_does_not_use_configured_http_proxy(self):
        import io
        import urllib.response
        observed = []
        def intercept(handler, req):
            observed.append(req.host)
            payload = json.dumps({'choices': [{'message': {'content': '{"ok":true}'}}]}).encode()
            response = urllib.response.addinfourl(io.BytesIO(payload), {}, req.full_url, 200)
            response.msg = 'OK'
            return response
        with patch('urllib.request.getproxies', return_value={'http': 'http://proxy.example:8080'}), \
             patch('urllib.request.proxy_bypass', return_value=False), \
             patch('urllib.request.HTTPHandler.http_open', intercept):
            self.assertTrue(chat_json({'url': 'http://localhost:12345/v1/chat/completions', 'key': 'TEST_ONLY', 'model': 'test'}, 'fixture')['ok'])
        self.assertEqual(observed, ['localhost:12345'])

    def test_queued_local_paper_cannot_be_redirected_to_later_remote_setting(self):
        self.login()
        job = self.studio.create('local-only fixture')
        extract_pdf(fixture_pdf(), self.studio.folder(job))
        self.post('/api/credentials', {'base_url': 'http://localhost:12345/v1', 'model': 'local-model'})
        event = threading.Event()
        self.studio.pool.submit(lambda: event.wait(5))
        with patch('writing.chat_json') as chat:
            self.post(f'/api/jobs/{job}/generate', {'base_url': 'http://localhost:12345/v1', 'model': 'local-model'})
            self.post('/api/credentials', {'base_url': 'https://remote.example/v1', 'model': 'remote-model', 'api_key': 'TEST_ONLY'})
            event.set()
            for _ in range(100):
                if self.studio.jobs[job]['status'] == 'error': break
                time.sleep(.02)
            self.assertEqual(self.studio.jobs[job]['status'], 'error')
            self.assertIn('接收服务', self.studio.jobs[job]['message'])
            chat.assert_not_called()


if __name__ == '__main__': unittest.main()
