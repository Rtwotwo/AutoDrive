"""Local, single-user paper-to-WeChat workbench. Human-reviewed draft submission; no public publication."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import threading
import time
from urllib.parse import parse_qs, urlsplit
import uuid
import webbrowser

from materials import catalog as material_catalog, extract_embedded, accept_image, accept_candidate, MAX_UPLOAD
from sources import MAX_BYTES, crop_figure, download_arxiv, extract_pdf, parse_arxiv, write_json, repair_crops, refresh_identity
from publication import clean_article, paper_details, validate_paper_info
from project_media import discover, import_material
from writing import generate_article, prompt_pack, validate_article, provider_config
from exporting import article_html, document_html, export_bundle, markdown
from model_store import ModelStore
from wechat_api import Account, submit_draft, recheck, reset_submission, image_file
from wechat_review import prepare, approve, is_approved, revoke, read_json, asset_path
from covers import generate_cover
from formatting import compact_baoyu, current_baoyu, layout_markdown
from autofeed import AutoFeed
from wechat_fields import adapt_fields, record_adjustments, validated_adjustments

ROOT = Path(__file__).resolve().parent
JOB_ID = re.compile(r'^[0-9a-f]{32}$')


def bun_runner():
    local = ROOT / '.runtime' / 'node_modules' / 'bun' / 'bin' / ('bun.exe' if os.name == 'nt' else 'bun')
    return str(local) if local.is_file() else shutil.which('bun')


class Studio:
    def __init__(self, data_dir, config_path=None):
        self.data_dir = Path(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.token = secrets.token_urlsafe(32)
        self.desktop = False
        self.cookie = secrets.token_urlsafe(32)
        self.launch_ticket = secrets.token_urlsafe(32)
        self.provider = {}
        self.model_store = ModelStore(config_path) if config_path else None
        self.profiles = {}
        self.active_profile = ''
        self.remember_models = False
        self.model_warning = ''
        self.model_revision = 0
        self.wechat = Account(Path(config_path).with_name("wechat.dpapi") if config_path else None)
        self.desktop_action = None
        self.processes = set()
        self.closing = False
        self.lock = threading.RLock()
        self.jobs = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='studio')
        for path in self.data_dir.glob('*/status.json'):
            try:
                item = json.loads(path.read_text(encoding='utf-8'))
                if item['status'] in {'running', 'queued'}:
                    item.update(status='error', message='上次运行已中断；原文与已保存成稿仍可使用。')
                self.jobs[path.parent.name] = item
            except (ValueError, KeyError, OSError):
                continue
        if self.model_store:
            try:
                stored = self.model_store.load()
                if stored:
                    profiles = stored.get('profiles')
                    if not isinstance(profiles, list) or len(profiles) > 30:
                        raise ValueError('模型配置格式错误。')
                    checked = {}
                    for profile in profiles:
                        if not isinstance(profile, dict) or not JOB_ID.fullmatch(str(profile.get('id', ''))):
                            raise ValueError('模型配置格式错误。')
                        checked[profile['id']] = self.profile_values(profile)
                    active = stored.get('active_id', '')
                    if checked and active not in checked: raise ValueError('模型配置格式错误。')
                    self.profiles, self.active_profile = checked, active
                    self.provider = dict(checked.get(active, {}))
                    self.remember_models = True
            except (ValueError, OSError):
                self.model_warning = '已保存的模型配置无法读取，请重新填写并保存；原加密文件未改动。'
        self.autofeed = AutoFeed(self)

    @staticmethod
    def profile_values(values):
        result = {key: str(values.get(key, '')).strip() for key in ('base_url', 'model', 'api_key')}
        result['name'] = str(values.get('name') or result['model'])[:80]
        validated = provider_config({**result, 'output_tokens': values.get('output_tokens'),
                                     'thinking': values.get('thinking')}, use_environment=False)
        result.update(output_tokens=validated['output_tokens'], thinking=validated['thinking'])
        return result

    def model_session(self):
        with self.lock:
            safe = [{key: profile.get(key) for key in ('name', 'base_url', 'model', 'output_tokens', 'thinking')}
                    | {'id': ident, 'configured': bool(profile.get('api_key'))}
                    for ident, profile in self.profiles.items()]
            return {'profiles': safe, 'active_profile': self.active_profile,
                    'remember_models': self.remember_models, 'model_warning': self.model_warning,
                    'output_tokens': self.provider.get('output_tokens', 0),
                    'thinking': self.provider.get('thinking', 'high')}

    def configure_models(self, body):
        with self.lock:
            if hasattr(self,'autofeed') and self.autofeed.running:
                raise ValueError('自动任务正在运行，请先暂停并等待请求结束，再修改模型配置。')
            profiles = {key: dict(value) for key, value in self.profiles.items()}
            active = self.active_profile
            remember = bool(body.get('remember', self.remember_models))
            if body.get('clear'):
                profiles, active, remember = {}, '', False
            elif body.get('activate'):
                active = str(body['activate'])
                if active not in profiles: raise ValueError('模型配置不存在。')
            elif body.get('delete'):
                ident = str(body['delete'])
                if ident not in profiles: raise ValueError('模型配置不存在。')
                del profiles[ident]
                if active == ident: active = next(iter(profiles), '')
            else:
                ident = str(body.get('profile_id', active))
                if ident and ident not in profiles: raise ValueError('模型配置不存在。')
                previous = profiles.get(ident, self.provider if 'profile_id' not in body else {})
                values = dict(body)
                if not str(values.get('api_key', '')).strip() and str(values.get('base_url', '')).strip().rstrip('/') == previous.get('base_url', '').rstrip('/'):
                    values['api_key'] = previous.get('api_key', '')
                profile = self.profile_values(values)
                active = ident or uuid.uuid4().hex
                profiles[active] = profile
                if len(profiles) > 30: raise ValueError('最多保存 30 个模型配置。')
            if remember:
                if not self.model_store: raise ValueError('请使用桌面版加密保存配置。')
                self.model_store.save({'version': 1, 'active_id': active,
                                       'profiles': [dict(value, id=key) for key, value in profiles.items()]})
            elif self.model_store:
                self.model_store.clear()
            self.profiles, self.active_profile = profiles, active
            self.provider = dict(profiles.get(active, {}))
            self.remember_models, self.model_warning = remember, ''
            self.model_revision += 1

    def folder(self, job_id):
        if not JOB_ID.fullmatch(job_id) or job_id not in self.jobs:
            raise ValueError('论文任务不存在。')
        return self.data_dir / job_id

    def load(self, job_id, name='source.json'):
        path = self.folder(job_id) / name
        if not path.is_file(): raise ValueError('该内容尚未生成。')
        return json.loads(path.read_text(encoding='utf-8'))

    def update(self, job_id, **values):
        with self.lock:
            self.jobs[job_id].update(values)
            write_json(self.folder(job_id) / 'status.json', self.jobs[job_id])

    def create(self, label):
        job_id = uuid.uuid4().hex
        (self.data_dir / job_id).mkdir()
        self.jobs[job_id] = {'id': job_id, 'title': str(label)[:300], 'status': 'ready', 'message': '', 'created_at': time.time(), 'cancelled': False}
        return job_id

    def idle(self, job_id):
        self.folder(job_id)
        self.manual_available()
        if self.jobs[job_id]['status'] in {'queued', 'running'}:
            raise ValueError('当前任务还在处理，请等待完成或取消后重试。')

    def manual_available(self):
        if self.autofeed.running and self.autofeed.mode in {'selected','batch'}:
            raise ValueError('逐篇投递正在运行；请先停止队列或完成本篇后停止，再编辑或导入作品。')

    def library_update(self, job_id, values):
        with self.lock:
            self.idle(job_id)
            changes = {}
            if 'display_name' in values:
                name = str(values['display_name']).strip()
                if len(name) > 160: raise ValueError('作品名称最多 160 字。')
                changes['display_name'] = name
            for key in ('pinned', 'trashed'):
                if key in values:
                    if not isinstance(values[key], bool): raise ValueError('作品设置无效。')
                    changes[key] = values[key]
            self.update(job_id, **changes)
            return dict(self.jobs[job_id])

    def submit(self, job_id, operation, work):
        with self.lock:
            self.idle(job_id)
            self.update(job_id, status='queued', operation=operation, message='等待处理…', cancelled=False)
        def run():
            try:
                if self.jobs[job_id]['cancelled']: raise ValueError('任务已取消。')
                self.update(job_id, status='running', message='开始处理…')
                work(lambda message: self.update(job_id, message=message))
                if self.jobs[job_id]['cancelled']: raise ValueError('任务已取消；已保存内容保留。')
                self.update(job_id, status='ready', message='处理完成。')
            except Exception as exc:
                message = str(exc) if isinstance(exc, ValueError) else '处理未完成，请检查输入文件或模型服务后重试。'
                self.update(job_id, status='error', message=message)
        self.pool.submit(run)

    def save_article(self, job_id, article):
        article = clean_article(article)
        folder = self.folder(job_id)
        source = self.load(job_id)
        audit = validate_article(article, source)
        if read_json(folder / 'article.json') == article:
            return audit
        if (folder / 'article.json').exists():
            (folder / 'history').mkdir(exist_ok=True)
            shutil.copyfile(folder / 'article.json', folder / 'history' / (uuid.uuid4().hex + '.json'))
        write_json(folder / 'article.json', article)
        write_json(folder / 'audit.json', audit)
        return audit

    def format_skill(self, job_id, progress):
        folder = self.folder(job_id)
        script = ROOT / 'skills' / 'baoyu-markdown-to-html' / 'scripts' / 'main.ts'
        if not script.exists(): raise ValueError('未安装 baoyu-markdown-to-html。请参考 README 中的安装说明。')
        runner = bun_runner()
        if not runner: raise ValueError('宝玉排版需要 Bun。请运行 setup-formatter.ps1；内置 HTML 导出不需要额外运行时。')
        source=self.load(job_id);article=self.load(job_id,'article.json')
        options=read_json(folder/'wechat-options.json',{})
        theme=options.get('baoyu_theme','simple')
        if theme not in {'simple','default','grace','modern'}:raise ValueError('无效宝玉主题。')
        progress('正在调用宝玉排版：'+theme+' 主题…')
        input_markdown=layout_markdown(article,source,options)
        (folder / 'article.md').write_text(input_markdown, encoding='utf-8')
        # Only a fixed local script and server-owned input path are executed.
        env = {k: v for k, v in os.environ.items() if not re.search(r'KEY|TOKEN|SECRET|PASSWORD', k, re.I)}
        with self.lock:
            if self.closing: raise ValueError('软件正在关闭。')
            process = subprocess.Popen([runner, str(script), str(folder / 'article.md'), '--theme', theme, '--no-mermaid'],
                                       cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self.processes.add(process)
        try:
            process.communicate(timeout=180)
        except subprocess.TimeoutExpired:
            process.kill(); process.communicate()
            raise ValueError('宝玉排版超时；内置导出仍可使用。') from None
        finally:
            with self.lock: self.processes.discard(process)
        if process.returncode or not (folder / 'article.html').is_file():
            raise ValueError('宝玉排版未完成。请确认 Bun 依赖可下载；内置导出仍可使用。')
        html = (folder / 'article.html').read_text(encoding='utf-8')
        content=compact_baoyu(html,source)
        write_json(folder/'baoyu-layout.json',{'markdown':input_markdown,'content':content,'baoyu_theme':theme})
        options['theme']='baoyu'
        write_json(folder/'wechat-options.json',options)
        for figure in self.load(job_id)['figures']:
            data = 'data:image/png;base64,' + base64.b64encode((folder / figure['image']).read_bytes()).decode()
            html = html.replace('src="' + figure['image'] + '"', 'src="' + data + '"')
        html = re.sub(r'\sdata-local-path="[^"]*"', '', html)
        (folder / 'article.html').write_text(html, encoding='utf-8')

    def wechat_prepared(self, job_id):
        folder=self.folder(job_id)
        return prepare(folder,self.load(job_id,'article.json'),self.load(job_id),
                       read_json(folder/'wechat-options.json',{}),self.wechat.public())

    def wechat_status(self, job_id):
        folder=self.folder(job_id);article=read_json(folder/'article.json',{})
        saved=read_json(folder/'wechat-options.json',{})
        options={'title':article.get('title',''),'digest':article.get('digest',''),'author':'','cover_id':'','theme':'ink',**saved}
        status={'options':options,'approved':False,'blocker':'','reviewed_at':None,'video_count':0,'html_chars':0}
        changes=read_json(folder/'wechat-field-adjustments.json',{}).get('adjustments',[])
        status['field_adjustments']=[c for c in changes if options.get(c['field'])==c['after']]
        review=read_json(folder/'wechat-review.json',{})
        try:
            prepared=self.wechat_prepared(job_id)
            status.update(approved=is_approved(folder,prepared),video_count=prepared['video_count'],html_chars=len(prepared['content']),reviewed_at=review.get('reviewed_at'))
        except ValueError as exc:status['blocker']=str(exc)
        except (KeyError,TypeError):status['blocker']='请保存标题、摘要和封面，检查稿件内容后再审核。'
        status['layout']='baoyu' if saved.get('theme')=='baoyu' else 'builtin'
        record=read_json(folder/'wechat-submission.json',{})
        status['submission']={k:record.get(k) for k in ('state','message','media_id','verified_at','account') if k in record}
        return status

    def close(self):
        with self.lock:
            self.closing = True
            self.autofeed.stop_requested = True
            self.autofeed.metadata_pool.shutdown(wait=False,cancel_futures=True)
            self.wechat.close()
            self.provider.clear()
            self.profiles.clear()
            for item in self.jobs.values(): item['cancelled'] = True
            for process in tuple(self.processes):
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)
        self.pool.shutdown(wait=False, cancel_futures=True)


class Handler(BaseHTTPRequestHandler):
    server_version = 'PaperStudio/1.0'

    @property
    def studio(self): return self.server.studio

    def log_message(self, *_): pass  # Never log request payloads or credentials.

    def valid_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def authorized(self):
        if not self.studio.desktop:
            return True
        origin = self.headers.get('Origin')
        if origin and origin != f'http://127.0.0.1:{self.server.server_port}':
            return False
        try:
            cookies = SimpleCookie(self.headers.get('Cookie', ''))
            value = cookies.get('studio_session')
            return bool(value and secrets.compare_digest(value.value, self.studio.cookie))
        except Exception:
            return False

    def send(self, body, content_type='application/json; charset=utf-8', code=200, attachment=None):
        if isinstance(body, (dict, list)): body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str): body = body.encode()
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; connect-src 'self'; frame-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'")
        if attachment: self.send_header('Content-Disposition', f'attachment; filename="{attachment}"')
        self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError): pass

    def error(self, exc, code=400):
        self.send({'error': str(exc) if isinstance(exc, ValueError) else '请求无法处理。请重试并检查输入。'}, code=code)

    def do_GET(self):
        if not self.valid_host(): return self.send({'error': 'Invalid Host'}, code=403)
        try:
            url = urlsplit(self.path)
            path = url.path
            query = parse_qs(url.query)
            if self.studio.desktop and path == '/launch':
                ticket = query.get('ticket', [''])[0]
                with self.studio.lock:
                    if not self.studio.launch_ticket or not secrets.compare_digest(ticket, self.studio.launch_ticket):
                        return self.send({'error': '请从桌面快捷方式打开 Paper Studio。'}, code=403)
                    self.studio.launch_ticket = ''
                self.send_response(303)
                self.send_header('Location', '/')
                self.send_header('Set-Cookie', f'studio_session={self.studio.cookie}; HttpOnly; SameSite=Strict; Path=/')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Referrer-Policy', 'no-referrer')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
            if not self.authorized():
                return self.send({'error': '请从桌面快捷方式打开 Paper Studio。'}, code=403)
            if path == '/api/session':
                if self.studio.desktop:
                    with self.studio.lock: provider = dict(self.studio.provider)
                    return self.send({'token': self.studio.token, 'desktop': True,
                                      'configured': bool(provider.get('api_key')),
                                      'base_url': provider.get('base_url', 'https://api.openai.com/v1'),
                                      'model': provider.get('model', ''), 'skill_available': bool(bun_runner()),
                                      **self.studio.model_session()})
                return self.send({'token': self.studio.token, 'configured': bool(os.environ.get('PAPER_STUDIO_API_KEY')),
                                  'base_url': os.environ.get('PAPER_STUDIO_API_BASE', 'https://api.openai.com/v1'),
                                  'model': os.environ.get('PAPER_STUDIO_MODEL', ''),
                                  'skill_available': bool(bun_runner())})
            if path == '/api/wechat':
                return self.send(self.studio.wechat.public())
            if path == '/api/autofeed':
                return self.send(self.studio.autofeed.status())
            if path == '/api/jobs':
                with self.studio.lock: items = [dict(x) for x in self.studio.jobs.values()]
                return self.send(sorted(items, key=lambda j: (bool(j.get('pinned')), j['created_at']), reverse=True))
            match = re.fullmatch(r'/api/jobs/([0-9a-f]{32})/(status|source|article|audit|preview|export|asset|project-media|wechat|wechat-preview|materials)', path)
            if match:
                job_id, action = match.groups()
                folder = self.studio.folder(job_id)
                if action == 'status': return self.send(dict(self.studio.jobs[job_id]))
                if action == 'wechat':return self.send(self.studio.wechat_status(job_id))
                if action == 'wechat-preview':
                    prepared=self.studio.wechat_prepared(job_id);content=prepared['content']
                    for item in prepared['assets']:
                        _,mime,data=image_file(asset_path(folder,item['image']))
                        content=content.replace('src="'+item['image']+'"','src="data:'+mime+';base64,'+base64.b64encode(data).decode()+'"')
                    return self.send(document_html(prepared['options']['title'],content),'text/html; charset=utf-8')

                if action == 'materials': return self.send(material_catalog(folder))
                if action == 'project-media':
                    return self.send(self.studio.load(job_id, 'project-media.json') if (folder / 'project-media.json').exists() else {'items':[]})
                if action == 'audit': return self.send(validate_article(self.studio.load(job_id, 'article.json'), self.studio.load(job_id)))
                if action == 'article': return self.send(clean_article(self.studio.load(job_id, 'article.json')))
                if action == 'source':
                    source = self.studio.load(job_id)
                    article = self.studio.load(job_id, 'article.json') if (folder / 'article.json').is_file() else {}
                    return self.send(dict(source, publication_info=paper_details(article, source)))
                if action == 'asset':
                    name = query.get('name', [''])[0]
                    if not (name == 'source.pdf' or re.fullmatch(r'images/(?:page|fig)-\d{3}\.png|materials/pdf-\d+-\d+\.png|covers/cover-[0-9a-f]{16}\.png|media/media-[0-9a-f]{16}\.(?:mp4|webm)', name)):
                        raise ValueError('无效资源路径。')
                    return self.send((folder / name).read_bytes(), mimetypes.guess_type(name)[0] or 'application/octet-stream')
                article = self.studio.load(job_id, 'article.json')
                source = self.studio.load(job_id)
                theme = query.get('theme', ['ink'])[0]
                fmt = query.get('format', ['zip'])[0]
                if action == 'preview':
                    if theme=='baoyu':
                        try:content=current_baoyu(folder,article,source,read_json(folder/'wechat-options.json',{}))
                        except ValueError as exc:
                            from html import escape
                            return self.send(document_html('排版需要更新','<p>'+escape(str(exc))+'</p>'),'text/html; charset=utf-8')
                        for f in source['figures']:
                            content=content.replace('src="'+f['image']+'"','src="'+f'/api/jobs/{job_id}/asset?name='+f['image']+'"')
                        return self.send(document_html(article['title'],content),'text/html; charset=utf-8')
                    return self.send(document_html(article['title'], article_html(article, source, folder, theme, embed=True, preview_media=True, asset_prefix=f'/api/jobs/{job_id}/asset?name=')), 'text/html; charset=utf-8')
                if fmt == 'zip': return self.send(export_bundle(article, source, folder, theme), 'application/zip', attachment='paper-article.zip')
                if fmt == 'md': return self.send(markdown(article, source), 'text/markdown; charset=utf-8', attachment='article.md')
                if fmt == 'html': return self.send(article_html(article, source, folder, theme, embed=True), 'text/html; charset=utf-8', attachment='wechat.html')
                if fmt == 'json': return self.send(article, attachment='article.json')
                if fmt == 'skill': return self.send((folder / 'article.html').read_bytes(), 'text/html; charset=utf-8', attachment='article-baoyu.html')
                raise ValueError('不支持的导出格式。')
            static = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}
            if path in static:
                file = ROOT / 'static' / static[path]
                mime = mimetypes.guess_type(file.name)[0] or 'text/plain'
                return self.send(file.read_bytes(), mime + '; charset=utf-8')
            self.send({'error': 'Not found'}, code=404)
        except Exception as exc:
            self.error(exc)

    def do_POST(self):
        if not self.valid_host(): return self.send({'error': 'Invalid Host'}, code=403)
        if not self.authorized(): return self.send({'error': 'Desktop session required'}, code=403)
        allowed_origins = {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}
        if self.headers.get('Origin') not in allowed_origins | {None} or not secrets.compare_digest(self.headers.get('X-Studio-Token', ''), self.studio.token):
            return self.send({'error': '请从本地 Paper Studio 页面操作。'}, code=403)
        try:
            path = urlsplit(self.path).path
            length = int(self.headers.get('Content-Length', 0))
            image_upload = re.fullmatch(r'/api/jobs/([0-9a-f]{32})/import-image',path)
            limit = MAX_UPLOAD if image_upload else MAX_BYTES if path == '/api/import/pdf' else 3_000_000
            if not 0 < length <= limit: raise ValueError('请求为空或超过大小限制。')
            self.connection.settimeout(60)
            raw = self.rfile.read(length)
            if len(raw) != length: raise ValueError('上传中断，请重试。')
            body = {} if path == '/api/import/pdf' or image_upload else json.loads(raw)
            if not isinstance(body, dict): raise ValueError('请求需要 JSON 对象。')
            if path in {'/api/autofeed/config','/api/autofeed/run','/api/autofeed/discover','/api/autofeed/pause','/api/autofeed/links','/api/autofeed/resume','/api/autofeed/finish-current'}:
                if not self.studio.desktop:raise ValueError('自动投递仅在私有桌面版使用。')
                feed=self.studio.autofeed
                if path.endswith('/config'):return self.send(feed.configure(body))
                if path.endswith('/pause'):return self.send(feed.pause())
                if path.endswith('/finish-current'):return self.send(feed.stop_after_current())
                if path.endswith('/links'):return self.send(feed.start_links(body.get('urls')),code=202)
                if path.endswith('/resume'):return self.send(feed.resume_selected(),code=202)
                return self.send(feed.start(discover_only=path.endswith('/discover')),code=202)
            if image_upload:
                job_id=image_upload.group(1);folder=self.studio.folder(job_id)
                opts={k:v[0] for k,v in parse_qs(urlsplit(self.path).query).items()}
                with self.studio.lock:
                    self.studio.idle(job_id)
                    if self.studio.jobs[job_id].get('trashed'):raise ValueError('请先恢复作品。')
                    return self.send(accept_image(folder,self.studio.load(job_id),raw,
                        replace_id=opts.get('replace_id'),caption=opts.get('caption',''),
                        page=int(opts['page']) if opts.get('page') else None,filename=opts.get('filename','')))
            if self.studio.desktop and path == '/api/credentials':
                self.studio.configure_models(body)
                return self.send({'ok': True, 'configured': bool(self.studio.provider.get('api_key')),
                                  **self.studio.model_session()})
            if path in {'/api/wechat/config','/api/wechat/check'}:
                if not self.studio.desktop:raise ValueError('公众号接入仅在私有桌面版中使用。')
                with self.studio.lock:
                    if self.studio.autofeed.running:raise ValueError('自动任务正在运行，请先暂停并等待请求结束，再修改公众号配置。')
                    if any(j['status'] in {'queued','running'} and str(j.get('operation','')).startswith('wechat') for j in self.studio.jobs.values()):
                        raise ValueError('公众号任务正在处理，请完成后再修改或检测连接。')
                    if path.endswith('/config'):self.studio.wechat.save(body)
                    else:self.studio.wechat.check()
                    return self.send(self.studio.wechat.public())
            if self.studio.desktop and path == '/api/desktop/action':
                if not self.studio.desktop_action: raise ValueError('桌面窗口尚未就绪。')
                return self.send(self.studio.desktop_action(body))
            if path in {'/api/import/pdf', '/api/import/arxiv'}:
                if path.endswith('arxiv'): parse_arxiv(body.get('url', ''))
                elif not raw.startswith(b'%PDF-'): raise ValueError('上传文件不是有效 PDF。')
                if path.endswith('arxiv') and body.get('auto_draft') is True:
                    if not self.studio.desktop:raise ValueError('一键投递仅在私有桌面版使用。')
                    return self.send(self.studio.autofeed.start_links([body['url']]),code=202)
                with self.studio.lock:
                    self.studio.manual_available()
                    job_id = self.studio.create(body.get('url', 'PDF 论文'))
                def work(progress):
                    data, meta = download_arxiv(body['url'], progress) if path.endswith('arxiv') else (raw, {})
                    manifest = extract_pdf(data, self.studio.folder(job_id), 'paper.pdf', meta, progress)
                    if path.endswith('pdf'):
                        manifest = refresh_identity(self.studio.folder(job_id), manifest, progress)
                    self.studio.update(job_id, title=manifest['title'])
                self.studio.submit(job_id, 'import', work)
                return self.send({'id': job_id}, code=202)
            match = re.fullmatch(r'/api/jobs/([0-9a-f]{32})/(generate|article|crop|figures|prompt|cancel|skill|paper-info|repair-crops|scan-media|import-media|wechat-options|wechat-fit|wechat-approve|wechat-revoke|wechat-submit|wechat-recheck|wechat-reset|library|refresh-identity|cover|scan-materials|accept-material)', path)
            if not match: return self.send({'error': 'Not found'}, code=404)
            job_id, action = match.groups()
            folder = self.studio.folder(job_id)
            if action == 'library':
                return self.send(self.studio.library_update(job_id, body))
            if action == 'cancel':
                self.studio.update(job_id, cancelled=True, message='正在取消；当前网络请求结束后停止。')
                return self.send({'ok': True})
            with self.studio.lock:
                self.studio.idle(job_id)
                source = self.studio.load(job_id)
                if action == 'cover':
                    return self.send(generate_cover(folder, source, self.studio.load(job_id,'article.json'), body))
                if self.studio.jobs[job_id].get('trashed'):
                    raise ValueError('请先从回收站恢复这篇作品。')
                if action == 'refresh-identity':
                    def refresh(progress):
                        updated = refresh_identity(folder, source, progress)
                        self.studio.update(job_id, title=updated.get('paper_info', {}).get('title') or updated['title'])
                    self.studio.submit(job_id, action, refresh)
                    return self.send({'id':job_id}, code=202)
                if action.startswith('wechat-'):
                    if not self.studio.desktop:raise ValueError('公众号提交仅在私有桌面版中使用。')
                    if action=='wechat-fit':
                        values,changes=adapt_fields(body,self.studio.load(job_id,'article.json'))
                        return self.send({'options':values,'field_adjustments':changes})
                    if action=='wechat-options':
                        from wechat_review import clean_options
                        article=self.studio.load(job_id,'article.json')
                        fitted,changes=adapt_fields(body,article)
                        values=clean_options(fitted,article,source)
                        write_json(folder/'wechat-options.json',values)
                        previews=validated_adjustments(values,article,body.get('field_adjustments',[]))
                        record_adjustments(folder,previews+changes)
                    elif action=='wechat-approve':
                        approve(folder,self.studio.wechat_prepared(job_id),body.get('checks'),body.get('reviewer',''))
                    elif action=='wechat-revoke':revoke(folder)
                    elif action=='wechat-reset':reset_submission(folder,body.get('confirmed'))
                    elif action in {'wechat-submit','wechat-recheck'}:
                        if not self.studio.wechat.config:raise ValueError('请先配置公众号。')
                        account=Account(request=self.studio.wechat.request)
                        account.config=dict(self.studio.wechat.config)
                        if action=='wechat-submit':
                            from wechat_review import require_approved
                            prepared=self.studio.wechat_prepared(job_id)
                            require_approved(folder,prepared)
                            if read_json(folder/'wechat-submission.json',{}).get('state') in {'unknown','submitted','submitted_unverified'}:
                                raise ValueError('已有提交记录，请先检查或重新核对公众号草稿，避免重复创建。')
                            def work(progress):
                                try:submit_draft(folder,prepared,account,progress)
                                finally:account.close()
                        else:
                            def work(progress):
                                try:
                                    progress('读回已有草稿，核对正文、图片与封面…');recheck(folder,account)
                                finally:account.close()
                        self.studio.submit(job_id,action,work)
                        return self.send({'id':job_id},code=202)
                    return self.send(self.studio.wechat_status(job_id))
                if action in {'scan-media', 'import-media'}:
                    article = self.studio.load(job_id, 'article.json') if (folder / 'article.json').is_file() else {}
                    project = paper_details(article, source).get('project_url')
                    if not project: raise ValueError('请先在论文资料中保存已确认的项目主页链接。')
                    if action == 'scan-media':
                        def scan(progress):
                            progress('读取作者项目主页中的公开图片与视频链接…')
                            write_json(folder / 'project-media.json', discover(project))
                        self.studio.submit(job_id, 'scan-media', scan)
                    else:
                        catalog = self.studio.load(job_id, 'project-media.json')
                        if catalog.get('requested_url') != project: raise ValueError('项目主页已改变，请重新查找素材。')
                        candidate = next((x for x in catalog['items'] if x['id'] == body.get('id')), None)
                        if not candidate: raise ValueError('请从已发现的项目素材中选择。')
                        self.studio.submit(job_id, 'import-media', lambda progress: import_material(folder, source, candidate))
                    return self.send({'id':job_id}, code=202)
                if action == 'paper-info':
                    source['paper_info'] = validate_paper_info(body)
                    write_json(folder / 'source.json', source)
                    if source['paper_info'].get('title'):
                        source['title'] = source['paper_info']['title']
                        write_json(folder / 'source.json', source)
                        self.studio.update(job_id, title=source['title'])
                    return self.send(source['paper_info'])
                if action == 'scan-materials':
                    def scan_materials(progress):
                        repair_crops(folder,source,progress)
                        extract_embedded(folder,progress)
                    self.studio.submit(job_id,action,scan_materials)
                    return self.send({'id':job_id},code=202)
                if action == 'accept-material':return self.send(accept_candidate(folder,source,body))
                if action == 'repair-crops':
                    self.studio.submit(job_id, 'repair-crops', lambda progress: repair_crops(folder, source, progress))
                    return self.send({'id': job_id}, code=202)
                if action == 'prompt': return self.send({'prompt': prompt_pack(source, body)})
                if action == 'article': return self.send(self.studio.save_article(job_id, body))
                if action == 'crop':
                    return self.send(crop_figure(folder, source, body.get('page'), body.get('box'), body.get('caption', ''), body.get('figure_id')))
                if action == 'figures':
                    updates = body.get('figures', [])
                    if not isinstance(updates, list): raise ValueError('配图格式错误。')
                    known = {f['id']: f for f in source['figures']}
                    for f in updates:
                        if not isinstance(f, dict) or f.get('id') not in known: raise ValueError('图片 ID 无效。')
                        target = known[f['id']]
                        target.update(selected=bool(f.get('selected')), reviewed=bool(f.get('reviewed')),
                                      caption=str(f.get('caption', target['caption']))[:1800])
                    videos = {m['id']:m for m in source.get('project_media', [])}
                    for item in body.get('media', []):
                        if not isinstance(item,dict) or item.get('id') not in videos: raise ValueError('视频 ID 无效。')
                        videos[item['id']].update(selected=bool(item.get('selected')),caption=str(item.get('caption',''))[:500])
                    write_json(folder / 'source.json', source)
                    return self.send(source)
                if action == 'skill':
                    self.studio.submit(job_id, 'skill', lambda progress: self.studio.format_skill(job_id, progress))
                    return self.send({'id': job_id}, code=202)
                if action == 'generate':
                    if self.studio.desktop:
                        with self.studio.lock:
                            queued_base = self.studio.provider.get('base_url', '').rstrip('/')
                            queued_model = self.studio.provider.get('model', '')
                            queued_revision = self.studio.model_revision
                            body.update(output_tokens=self.studio.provider.get('output_tokens', 0),
                                        thinking=self.studio.provider.get('thinking', 'high'))
                        body.update(base_url=queued_base, model=queued_model)
                        body.pop('api_key', None)
                        body['_desktop'] = True
                    def generate(progress):
                        if self.studio.desktop:
                            # Keep the receiving service fixed; a later settings change must not redirect queued paper text.
                            with self.studio.lock:
                                current = self.studio.provider
                                if not current or self.studio.model_revision != queued_revision or current.get('base_url', '').rstrip('/') != queued_base or current.get('model') != queued_model:
                                    raise ValueError('模型设置已修改或清除；此任务已停止，请确认接收服务后重新生成。')
                                body['api_key'] = current.get('api_key', '')
                        try:
                            article, notes, audit = generate_article(source, folder, body, progress,
                                                                   cancelled=lambda: self.studio.jobs[job_id]['cancelled'])
                            self.studio.save_article(job_id, article)
                            write_json(folder / 'audit.json', audit)
                            write_json(folder / 'analysis-notes.json', notes)
                        finally:
                            body.pop('api_key', None)
                    self.studio.submit(job_id, 'generate', generate)
                    return self.send({'id': job_id}, code=202)
        except Exception as exc:
            self.error(exc)


def make_server(studio, port=8765):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.studio = studio
    server.daemon_threads = True
    return server


def smoke(directory):
    # Explicit synthetic fixture for the CLI; never represents a real paper.
    from tests.test_sources import fixture_pdf
    from tests.test_writing import fixture_article
    folder = directory / 'synthetic-fixture'
    manifest = extract_pdf(fixture_pdf(), folder)
    article = fixture_article(manifest)
    (folder / 'fixture.zip').write_bytes(export_bundle(article, manifest, folder))
    print(f'Synthetic fixture: {folder / "fixture.zip"}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Paper Studio — local paper-to-WeChat workbench')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open', action='store_true')
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('PAPER_STUDIO_DATA_DIR', ROOT / '.local')))
    args = parser.parse_args()
    if args.smoke:
        smoke(args.data_dir)
    else:
        studio = Studio(args.data_dir)
        server = make_server(studio, args.port)
        url = f'http://127.0.0.1:{server.server_port}'
        print(f'Paper Studio: {url}', flush=True)
        print('Press Ctrl+C to stop. Documents stay local until you request model generation.', flush=True)
        if args.open: webbrowser.open(url)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close(); studio.pool.shutdown(wait=False, cancel_futures=True)
