import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_store import ModelStore
from server import Studio
from writing import generate_article, provider_config, chat_json, OutputLimitError
from sources import extract_pdf
from tests.test_sources import fixture_pdf
from tests.test_writing import fixture_article


class LongWritingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.manifest = extract_pdf(fixture_pdf(), self.folder)
        self.article = fixture_article(self.manifest)
        self.options = {'base_url': 'https://api.deepseek.com', 'model': 'deepseek-flash',
                        'api_key': 'FAKE_LONGWRITE_KEY', 'length': 6500, '_desktop': True}

    def tearDown(self): self.temp.cleanup()

    def test_large_context_and_official_maximum_budgets(self):
        self.manifest['pages'].append({'number': 3, 'text': 'FINAL_UNSELECTED_PAGE_EVIDENCE'})
        with patch('writing.chat_json', side_effect=[{'facts': []}, self.article, self.article]) as chat:
            article, _, _ = generate_article(self.manifest, self.folder, self.options)
        self.assertEqual([c.kwargs['max_tokens'] for c in chat.call_args_list], [393216, 393216, 393216])
        for call in chat.call_args_list[1:]:
            self.assertIn('FINAL_UNSELECTED_PAGE_EVIDENCE', call.args[1])
        self.assertEqual(article['generation']['source_context'], 'full-text')
        for path in self.folder.rglob('*.json'):
            self.assertNotIn('FAKE_LONGWRITE_KEY', path.read_text(encoding='utf-8'))

    def test_resume_at_review_after_failure_and_budget_change(self):
        with patch('writing.chat_json', side_effect=[{'facts': []}, self.article, ValueError('timeout')]):
            with self.assertRaises(ValueError): generate_article(self.manifest, self.folder, self.options)
        self.assertFalse((self.folder / 'article.json').exists())
        self.assertIn('draft', json.loads((self.folder / 'generation-progress.json').read_text(encoding='utf-8')))
        with patch('writing.chat_json', return_value=self.article) as chat:
            generate_article(self.manifest, self.folder, dict(self.options, output_tokens=100000))
        self.assertEqual(chat.call_count, 1)
        self.assertIn('请审校', chat.call_args.args[1])

    def test_resume_invalidated_when_source_changes(self):
        with patch('writing.chat_json', side_effect=[{'facts': []}, ValueError('timeout')]):
            with self.assertRaises(ValueError): generate_article(self.manifest, self.folder, self.options)
        self.manifest['pages'][0]['text'] += ' corrected source'
        with patch('writing.chat_json', side_effect=[{'facts': []}, self.article, self.article]) as chat:
            generate_article(self.manifest, self.folder, self.options)
        self.assertEqual(chat.call_count, 3)

    def test_manual_cap_and_no_unbounded_retry(self):
        with patch('writing.chat_json', side_effect=OutputLimitError('truncated')) as chat:
            with self.assertRaisesRegex(ValueError, '提取证据'):
                generate_article(self.manifest, self.folder, dict(self.options, output_tokens=4000))
        self.assertEqual(chat.call_count, 1)
        with patch('writing.chat_json', side_effect=OutputLimitError('truncated')) as chat:
            with self.assertRaisesRegex(ValueError, '提取证据'):
                generate_article(self.manifest, self.folder, self.options)
        self.assertEqual(chat.call_count, 1)

    def test_official_profile_does_not_leak_special_parameters_to_other_services(self):
        config = provider_config(self.options)
        remote = provider_config(dict(self.options, base_url='https://third-party.example/v1'))
        self.assertTrue(config['deepseek']); self.assertFalse(remote['deepseek'])
        for settings in (config, remote):
            response = Mock()
            response.__enter__ = Mock(return_value=response)
            response.__exit__ = Mock(return_value=False)
            response.read.return_value = b'{"choices":[{"message":{"content":"{\\"ok\\":true}"},"finish_reason":"stop"}]}'
            with patch('writing.urllib.request.build_opener') as opener:
                opener.return_value.open.return_value = response
                self.assertTrue(chat_json(settings, 'JSON test', max_tokens=65536)['ok'])
                request = opener.return_value.open.call_args.args[0]
                payload = json.loads(request.data)
            self.assertEqual('thinking' in payload, settings['deepseek'])
            if settings['deepseek']:
                self.assertEqual(payload['reasoning_effort'], 'high')
                self.assertEqual(payload['response_format'], {'type': 'json_object'})

    def test_truncation_reports_numeric_usage_without_provider_text(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({'choices': [{'finish_reason': 'length', 'message': {
            'content': 'UNSAFE_TEXT', 'reasoning_content': 'PRIVATE_REASONING'}}],
            'usage': {'completion_tokens': 65536}}).encode()
        with patch('writing.urllib.request.build_opener') as opener:
            opener.return_value.open.return_value = response
            with self.assertRaises(OutputLimitError) as error:
                chat_json(provider_config(self.options), 'test', max_tokens=65536)
        self.assertIn('65,536', str(error.exception))
        self.assertNotIn('UNSAFE_TEXT', str(error.exception))
        self.assertNotIn('PRIVATE_REASONING', str(error.exception))


@unittest.skipUnless(os.name == 'nt', 'Windows DPAPI')
class ModelStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = self.root / 'settings' / 'models.dpapi'
        self.studio = Studio(self.root / 'data', config_path=self.config)
        self.first = {'profile_id': '', 'name': 'First', 'base_url': 'https://api.deepseek.com',
                      'model': 'deepseek-flash', 'api_key': 'SYNTHETIC_KEY_ONE', 'remember': True}
        self.second = {'profile_id': '', 'name': 'Second', 'base_url': 'https://other.example/v1',
                       'model': 'other-model', 'api_key': 'SYNTHETIC_KEY_TWO', 'remember': True}

    def tearDown(self):
        self.studio.close()
        self.temp.cleanup()

    def test_multiple_profiles_restart_switch_and_delete(self):
        self.studio.configure_models(self.first); first_id = self.studio.active_profile
        self.studio.configure_models(self.second); second_id = self.studio.active_profile
        self.studio.configure_models({'activate': first_id})
        self.assertEqual(self.studio.provider['api_key'], 'SYNTHETIC_KEY_ONE')
        self.assertNotIn('SYNTHETIC_KEY', json.dumps(self.studio.model_session()))
        for path in self.root.rglob('*'):
            if path.is_file(): self.assertNotIn(b'SYNTHETIC_KEY', path.read_bytes())
        reopened = Studio(self.root / 'data', config_path=self.config)
        try:
            self.assertEqual(reopened.active_profile, first_id)
            self.assertEqual(reopened.provider['api_key'], 'SYNTHETIC_KEY_ONE')
            reopened.configure_models({'delete': first_id})
            self.assertEqual(reopened.active_profile, second_id)
            self.assertEqual(reopened.provider['api_key'], 'SYNTHETIC_KEY_TWO')
            reopened.configure_models({'clear': True})
            self.assertFalse(self.config.exists())
            self.assertEqual(reopened.provider, {})
        finally: reopened.close()

    def test_new_profile_and_changed_endpoint_cannot_reuse_another_key(self):
        self.studio.configure_models(self.first)
        with self.assertRaises(ValueError):
            self.studio.configure_models(dict(self.first, api_key=''))
        with self.assertRaises(ValueError):
            self.studio.configure_models(dict(self.first, profile_id=self.studio.active_profile,
                                              base_url='https://changed.example/v1', api_key=''))
        self.assertEqual(self.studio.provider['api_key'], 'SYNTHETIC_KEY_ONE')

    def test_opt_out_removes_encrypted_copy_and_failed_save_is_atomic(self):
        self.studio.configure_models(self.first)
        before = self.config.read_bytes()
        with patch('model_store.crypt', side_effect=ValueError('test encryption failure')):
            with self.assertRaises(ValueError): self.studio.configure_models(self.second)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(len(self.studio.profiles), 1)
        self.studio.configure_models(dict(self.first, profile_id=self.studio.active_profile, remember=False))
        self.assertFalse(self.config.exists())
        self.assertTrue(self.studio.provider['api_key'])

    def test_corrupt_config_kept_and_secret_not_written_as_fallback(self):
        self.config.parent.mkdir(parents=True)
        self.config.write_bytes(b'corrupt ciphertext')
        reopened = Studio(self.root / 'data', config_path=self.config)
        try:
            self.assertTrue(reopened.model_warning)
            self.assertEqual(reopened.provider, {})
            self.assertEqual(self.config.read_bytes(), b'corrupt ciphertext')
        finally: reopened.close()


if __name__ == '__main__': unittest.main()
