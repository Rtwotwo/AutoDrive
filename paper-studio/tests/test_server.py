import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server import Studio, make_server
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.studio = Studio(self.tmp.name)
        self.server = make_server(self.studio, 0)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown(); self.server.server_close()
        self.studio.pool.shutdown(wait=True)
        self.tmp.cleanup()

    def call(self, path, body=None, token=True):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.url + path, data=raw, headers={'X-Studio-Token': self.studio.token if token else '', 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read(), response.headers

    def ready(self, job):
        for _ in range(100):
            item = self.studio.jobs[job]
            if item['status'] not in {'running', 'queued'}: return item
            time.sleep(.02)
        self.fail('Task did not finish')

    def test_http_pdf_article_export_and_generation(self):
        raw, _ = self.call('/api/import/pdf', fixture_pdf())
        job = json.loads(raw)['id']
        self.assertEqual(self.ready(job)['status'], 'ready')
        manifest = self.studio.load(job)
        article = fixture_article(manifest)
        self.call(f'/api/jobs/{job}/article', article)
        raw, _ = self.call(f'/api/jobs/{job}/export?format=zip')
        self.assertTrue(raw.startswith(b'PK'))
        raw, _ = self.call(f'/api/jobs/{job}/preview')
        self.assertIn(b'data:image/png;base64', raw)
        with patch('writing.chat_json', side_effect=[{'facts': []}, article, article]):
            self.call(f'/api/jobs/{job}/generate', {'base_url': 'http://localhost:11434/v1', 'model': 'test', 'api_key': 'TEST_SECRET_DO_NOT_PERSIST'})
            self.assertEqual(self.ready(job)['status'], 'ready')
        for path in Path(self.tmp.name).rglob('*.json'):
            self.assertNotIn('TEST_SECRET_DO_NOT_PERSIST', path.read_text(encoding='utf-8'))
        self.assertTrue(list((Path(self.tmp.name) / job / 'history').glob('*.json')))

    def test_origin_token_host_and_path(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx: self.call('/api/import/pdf', fixture_pdf(), token=False)
        self.assertEqual(ctx.exception.code, 403)
        req = urllib.request.Request(self.url + '/api/jobs', headers={'Host': 'evil.example'})
        with self.assertRaises(urllib.error.HTTPError) as ctx: urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 403)
        req = urllib.request.Request(self.url + '/api/import/arxiv', data=b'{}', headers={'Origin': 'https://evil.example', 'X-Studio-Token': self.studio.token})
        with self.assertRaises(urllib.error.HTTPError) as ctx: urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 403)
        with self.assertRaises(urllib.error.HTTPError): self.call('/../server.py')
        with self.assertRaises(urllib.error.HTTPError): self.call('/api/jobs/' + 'a' * 32 + '/source')

    def test_failure_preserves_draft_and_restart(self):
        raw, _ = self.call('/api/import/pdf', fixture_pdf())
        job = json.loads(raw)['id']; self.ready(job)
        article = fixture_article(self.studio.load(job))
        self.call(f'/api/jobs/{job}/article', article)
        with patch('writing.chat_json', side_effect=ValueError('request timed out')):
            self.call(f'/api/jobs/{job}/generate', {'base_url': 'http://localhost:11434/v1', 'model': 'test'})
            self.assertEqual(self.ready(job)['status'], 'error')
        self.assertEqual(self.studio.load(job, 'article.json')['title'], article['title'])
        reopened = Studio(self.tmp.name)
        self.assertIn(job, reopened.jobs)
        reopened.pool.shutdown()


if __name__ == '__main__': unittest.main()
