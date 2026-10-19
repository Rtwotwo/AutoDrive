"""Private Windows desktop entry point; model credentials use the installation's encrypted store."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time

from server import ROOT, Studio, make_server
from exporting import export_bundle, markdown, article_html
from writing import prompt_pack
from sources import write_json
from desktop_window import main_window, window_state, activate, activate_existing
from desktop_window import claim_instance_mutex, release_instance_mutex


def installation_root():
    override = os.environ.get('PAPER_STUDIO_HOME', '').strip()
    if override:
        destination = Path(override).expanduser()
        if not destination.is_absolute():
            raise ValueError('PAPER_STUDIO_HOME must be an absolute private directory.')
        destination = destination.resolve()
        boundaries = [ROOT.resolve()]
        # A nested checkout can sit inside a user's dotfiles repository. Only
        # the nearest enclosing checkout owns this application source tree.
        checkout = next((p for p in (ROOT.resolve(), *ROOT.resolve().parents) if (p / '.git').exists()), None)
        if checkout is not None:
            boundaries.append(checkout)
        if any(destination == p or p in destination.parents for p in boundaries):
            raise ValueError('Keep PAPER_STUDIO_HOME outside the source checkout.')
        return destination
    if (getattr(sys, 'frozen', False) and Path(sys.executable).parent.name == 'app'
            and (Path(sys.executable).parent.parent / 'settings').is_dir()
            and (Path(sys.executable).parent.parent / 'data').is_dir()):
        # Preserve the private desktop installer layout. Generic builds use AppData.
        return Path(sys.executable).resolve().parent.parent
    config = ROOT / 'desktop-install.json'
    if config.is_file():
        return Path(json.loads(config.read_text(encoding='utf-8'))['installation_dir']).resolve()
    return (Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local') / 'PaperStudio').resolve()


class DesktopActions:
    def __init__(self, studio, window, export_dir):
        self.studio, self.window, self.export_dir = studio, window, Path(export_dir)

    def __call__(self, body):
        import webview
        action = body.get('action')
        if action == 'open-data':
            os.startfile(str(self.studio.data_dir))
            return {'ok': True}
        job_id = body.get('id', '')
        folder = self.studio.folder(job_id)
        source = self.studio.load(job_id)
        self.export_dir.mkdir(exist_ok=True, parents=True)
        if action == 'open-pdf':
            destination = self.export_dir / (job_id + '.pdf')
            shutil.copyfile(folder / 'source.pdf', destination)
            os.startfile(str(destination))
            return {'ok': True}
        if action == 'prompt':
            data = prompt_pack(source, body.get('options', {})).encode('utf-8')
            filename = 'paper-writing-prompt.txt'
        elif action == 'export':
            article = self.studio.load(job_id, 'article.json')
            fmt, theme = body.get('format'), body.get('theme', 'ink')
            if fmt == 'zip': data, filename = export_bundle(article, source, folder, theme), 'paper-article.zip'
            elif fmt == 'md': data, filename = markdown(article, source).encode('utf-8'), 'article.md'
            elif fmt == 'html': data, filename = article_html(article, source, folder, theme, embed=True).encode('utf-8'), 'wechat.html'
            elif fmt == 'skill': data, filename = (folder / 'article.html').read_bytes(), 'article-baoyu.html'
            else: raise ValueError('不支持的导出格式。')
        else:
            raise ValueError('不支持的桌面操作。')
        selected = self.window.create_file_dialog(webview.FileDialog.SAVE, directory=str(self.export_dir), save_filename=filename)
        if not selected: return {'cancelled': True}
        destination = Path(selected if isinstance(selected, str) else selected[0])
        if not destination.suffix:
            destination = destination.with_suffix(Path(filename).suffix)
            if destination.exists() and not self.window.create_confirmation_dialog('覆盖文件', f'{destination.name} 已存在，是否覆盖？'):
                return {'cancelled': True}
        destination.write_bytes(data)
        return {'ok': True, 'name': destination.name}


def self_test(result_path):
    from tests.test_sources import fixture_pdf
    from sources import extract_pdf
    from tests.test_writing import fixture_article
    import urllib.request
    import urllib.error
    import http.cookiejar
    with tempfile.TemporaryDirectory() as temp:
        studio = Studio(Path(temp) / 'jobs'); studio.desktop = True
        job = studio.create('synthetic desktop fixture')
        manifest = extract_pdf(fixture_pdf(), studio.folder(job))
        studio.save_article(job, fixture_article(manifest))
        server = make_server(studio, 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        url = f'http://127.0.0.1:{server.server_port}'
        try:
            try:
                urllib.request.urlopen(url + '/api/session')
                raise AssertionError('Anonymous access was accepted')
            except urllib.error.HTTPError as error: assert error.code == 403
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            opener.open(url + '/launch?ticket=' + studio.launch_ticket).read()
            session = json.load(opener.open(url + '/api/session'))
            assert session['desktop'] and not session['configured']
            bundle = opener.open(url + f'/api/jobs/{job}/export?format=zip').read()
            assert bundle.startswith(b'PK')
            import pypdfium2, webview
            result = {'ok': True, 'bind': server.server_address[0], 'authentication': 'passed',
                      'pdf_and_export': 'passed', 'pdfium': str(pypdfium2.PDFIUM_INFO), 'webview_import': 'passed'}
        finally:
            server.shutdown(); server.server_close(); studio.pool.shutdown(wait=True)
    Path(result_path).write_text(json.dumps(result, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--autofeed-run', action='store_true', help='Run the configured daily draft-only batch; reuse an open desktop.')
    parser.add_argument('--autofeed-discover', action='store_true', help='Read-only discovery, no model or WeChat submission.')
    parser.add_argument('--result', type=Path)
    parser.add_argument('--ui-smoke', action='store_true', help='Launch real WebView2, verify UI, then exit without user data changes.')
    parser.add_argument('--activation-smoke', action='store_true', help='Verify first display and duplicate-launch recovery for hidden/minimized windows.')
    args = parser.parse_args()
    base = installation_root()
    if args.self_test:
        self_test(args.result or base / 'self-test.json')
        return 0
    # A per-user mutex prevents simultaneous instances modifying the same draft.
    mutex = claim_instance_mutex()
    if mutex is None:
        if args.autofeed_run or args.autofeed_discover:
            from feed_trigger import request_run
            request_run(base,args.autofeed_discover)
            return 0
        if activate_existing(base / 'desktop-status.json'):
            return 0
        ctypes.windll.user32.MessageBoxW(None, 'Paper Studio 的窗口暂时没有响应，请稍后再试。', 'Paper Studio', 0x40)
        return 1
    # Use private encrypted profiles, never credentials inherited from shell files.
    for name in ('PAPER_STUDIO_API_KEY', 'PAPER_STUDIO_API_BASE', 'PAPER_STUDIO_MODEL'):
        os.environ.pop(name, None)
    import webview
    studio = Studio(base / 'data', config_path=base / 'settings' / 'models.dpapi'); studio.desktop = True
    from feed_trigger import listen
    listen(studio)
    server = make_server(studio, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    window = webview.create_window('Paper Studio · 私有论文工作台',
                                  f'http://127.0.0.1:{server.server_port}/launch?ticket={studio.launch_ticket}',
                                  width=1380, height=940, min_size=(980, 680), text_select=True,
                                  hidden=bool(args.autofeed_run or args.autofeed_discover),
                                  background_color='#f6f8f3')
    studio.desktop_action = DesktopActions(studio, window, base / 'exports')
    closing = False
    checking_close = False
    def close_requested():
        nonlocal closing, checking_close
        if closing: return True
        if checking_close: return False
        checking_close = True
        # The native closing callback runs on the UI thread. Querying JS there deadlocks
        # WebView2; cancel this close, inspect on a worker, then request a normal close again.
        def inspect_and_close():
            nonlocal closing, checking_close
            try:
                try:
                    dirty = window.evaluate_js("Boolean(window.paperStudioStatus && window.paperStudioStatus().dirty)")
                except Exception: dirty = True
                running = studio.autofeed.running or any(item['status'] in {'running', 'queued'} for item in studio.jobs.values())
                if dirty or running:
                    if not window.create_confirmation_dialog('关闭 Paper Studio', '有未保存的编辑或正在执行的任务。关闭会停止任务，并保留上次保存的草稿。确定关闭吗？'):
                        return
                closing = True
                window.destroy()
            finally:
                checking_close = False
        threading.Thread(target=inspect_and_close, name='desktop-close', daemon=True).start()
        return False
    window.events.closing += close_requested
    status_path = base / 'desktop-status.json'
    status_path.write_text(json.dumps({'pid': os.getpid(), 'port': server.server_port, 'ready': False}), encoding='utf-8')
    def check_ui():
        ok = False
        try:
            for _ in range(100):
                try: ok = bool(window.evaluate_js('Boolean(window.paperStudioReady)'))
                except Exception: pass
                if ok: break
                time.sleep(.2)
            handle = main_window(os.getpid())
            if not (args.autofeed_run or args.autofeed_discover):activate(handle)
            status = {'pid': os.getpid(), 'port': server.server_port, 'ready': ok, 'renderer': 'edgechromium', **window_state(handle)}
            status_path.write_text(json.dumps(status), encoding='utf-8')
            if args.autofeed_run or args.autofeed_discover:
                try:
                    studio.autofeed.start(discover_only=args.autofeed_discover)
                    studio.autofeed.future.result()
                except ValueError as exc:studio.autofeed.message(str(exc))
                finally:
                    write_json(base/'automation'/'last-cli.json',studio.autofeed.status())
                    if not window_state(handle).get('visible'):window.destroy()
            if args.ui_smoke or args.activation_smoke:
                initial = window_state(handle)
                result = {'ok': ok and initial['visible'] and not initial['minimized'], 'window_title': window.title,
                          'jobs': window.evaluate_js("document.getElementById('jobCount').textContent"), 'initial': initial}
                result['model_settings_ready'] = bool(window.evaluate_js("Boolean(document.getElementById('modelProfiles') && document.getElementById('rememberModels') && document.getElementById('outputTokens').placeholder.includes('393216'))"))
                result['ok'] = result['ok'] and result['model_settings_ready']
                result['wechat_review_ready'] = bool(window.evaluate_js("Boolean(document.querySelector('[data-tab=review]') && document.getElementById('wechatPreview') && document.getElementById('submitWechat') && document.getElementById('wechatSecret'))"))
                result['ok'] = result['ok'] and result['wechat_review_ready']
                if args.activation_smoke:
                    command = [sys.executable] if getattr(sys, 'frozen', False) else [sys.executable, str(ROOT / 'desktop.py')]
                    for name, prepare in (('hidden', window.hide), ('minimized', window.minimize)):
                        prepare()
                        time.sleep(.25)
                        before = window_state(handle)
                        child = subprocess.run(command, timeout=25, creationflags=subprocess.CREATE_NO_WINDOW)
                        after = window_state(handle)
                        prepared = not before['visible'] if name == 'hidden' else before['minimized']
                        passed = prepared and child.returncode == 0 and after['visible'] and not after['minimized']
                        result[name] = {'before': before, 'after': after, 'second_launcher_exit': child.returncode, 'ok': passed}
                        result['ok'] = result['ok'] and passed
                (args.result or base / 'ui-smoke.json').write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
        except Exception as error:
            if args.ui_smoke or args.activation_smoke:
                # Class name only: no provider payloads or credentials in diagnostic files.
                (args.result or base / 'ui-smoke.json').write_text(json.dumps({'ok': False, 'error_type': type(error).__name__}), encoding='utf-8')
        finally:
            if args.ui_smoke or args.activation_smoke: window.destroy()
    try:
        webview.start(check_ui, gui='edgechromium', debug=False, private_mode=True,
                      storage_path=str(base / '.webview-session'),
                      localization={'global.quitConfirmation': '确定退出 Paper Studio 吗？'})
    finally:
        studio.close()
        server.shutdown(); server.server_close()
        status_path.unlink(missing_ok=True)
        release_instance_mutex(mutex)
        # Closing the window terminates in-flight HTTP workers and releases in-memory credentials.
        # Persisted job states are repaired to 'interrupted' by Studio on next launch.
        os._exit(0)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        # No tracebacks or provider payloads are written to a desktop log.
        ctypes.windll.user32.MessageBoxW(None, 'Paper Studio 启动失败。请确认 Microsoft Edge WebView2 Runtime 已安装，并运行本地自检。', 'Paper Studio', 0x10)
        sys.exit(1)
