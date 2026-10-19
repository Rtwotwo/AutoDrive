"""Opt-in, bounded public project media. Never uses model credentials or browser cookies."""
from html.parser import HTMLParser
import http.client
import ipaddress
import json
import socket
import ssl
from urllib.parse import urljoin, urlsplit
from pathlib import Path
import hashlib
import io
from publication import resource_url
from sources import write_json

MAX_IMAGE = 20 * 1024 * 1024
MAX_VIDEO = 80 * 1024 * 1024

def public_target(url):
    if not resource_url(url): raise ValueError('项目素材需要完整的公开 HTTP(S) 地址。')
    parts = urlsplit(url)
    port = parts.port or (443 if parts.scheme == 'https' else 80)
    if port not in {80, 443}: raise ValueError('项目素材仅支持标准 HTTP(S) 端口。')
    try: addresses = socket.getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
    except OSError: raise ValueError('无法解析项目主页域名。') from None
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('项目素材必须来自公网地址，不能读取本机或内网服务。')
    return parts, port, addresses[0][4][0]

def fetch_public(url, limit):
    for redirect in range(5):
        parts, port, address = public_target(url)
        conn = (http.client.HTTPSConnection(parts.hostname, port, timeout=30, context=ssl.create_default_context())
                if parts.scheme == 'https' else http.client.HTTPConnection(parts.hostname, port, timeout=30))
        # Pin the checked address; TLS still validates the original hostname.
        conn._create_connection = lambda _target, timeout, source_address=None: socket.create_connection((address, port), timeout, source_address)
        try:
            conn.request('GET', (parts.path or '/') + ('?' + parts.query if parts.query else ''),
                         headers={'User-Agent':'PaperStudio/1.0 (local project media reader)', 'Accept-Encoding':'identity'})
            response = conn.getresponse()
            if response.status in {301,302,303,307,308}:
                url = urljoin(url, response.getheader('Location', ''))
                continue
            if response.status != 200: raise ValueError(f'素材下载失败（HTTP {response.status}）。')
            size = response.getheader('Content-Length')
            if size and int(size) > limit: raise ValueError('项目素材超过大小限制。')
            data = response.read(limit + 1)
            if len(data) > limit: raise ValueError('项目素材超过大小限制。')
            return data, response.getheader('Content-Type',''), url
        except (OSError, http.client.HTTPException):
            raise ValueError('项目页面或素材读取失败，请稍后重试。') from None
        finally: conn.close()
    raise ValueError('项目页面跳转次数过多。')

class MediaParser(HTMLParser):
    def __init__(self, url):
        super().__init__(); self.url=url; self.items=[]; self.video_depth=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='video': self.video_depth+=1
        candidates=[]
        if tag=='img': candidates.append(('image',a.get('src') or a.get('data-src'),a.get('alt','')))
        if tag=='video' or tag=='source' and self.video_depth: candidates.append(('video',a.get('src'),a.get('title','')))
        if tag=='a':
            path=urlsplit(a.get('href','')).path.lower()
            if path.endswith(('.mp4','.webm')): candidates.append(('video',a.get('href'),a.get('title','')))
        for kind, ref, label in candidates:
            if not ref: continue
            link=resource_url(urljoin(self.url,ref))
            if not link or any(x['url']==link for x in self.items) or len(self.items)>=60: continue
            if kind=='image' and urlsplit(link).path.lower().endswith('.svg'): continue
            self.items.append({'id':hashlib.sha256(link.encode()).hexdigest()[:16], 'kind':kind, 'url':link,
                               'label':label.strip()[:300] or Path(urlsplit(link).path).name[:100] or '项目演示', 'page_url':self.url})
    def handle_endtag(self,tag):
        if tag=='video': self.video_depth=max(0,self.video_depth-1)

def discover(url):
    data, content_type, final_url=fetch_public(url,3*1024*1024)
    if 'html' not in content_type: raise ValueError('项目主页没有返回 HTML 页面。')
    parser=MediaParser(final_url);parser.feed(data.decode('utf-8',errors='replace'))
    return {'requested_url':url,'page_url':final_url, 'items':parser.items,
            'note':'仅识别公开 HTML 中的图片和 MP4/WebM；动态画廊、嵌入视频平台和需登录素材可能无法列出。来源可访问不代表可任意转载，请检查作者说明。'}

def import_material(folder, manifest, candidate):
    folder=Path(folder)
    if any(f.get('source_url')==candidate['url'] for f in manifest['figures']+manifest.get('project_media',[])):
        return manifest
    if len(manifest.get('project_media',[]))>=4 and candidate['kind']=='video': raise ValueError('每篇最多保存 4 个项目视频。')
    if len(manifest['figures'])>=100 and candidate['kind']=='image': raise ValueError('每篇最多保存 100 张候选配图。')
    data, mime, final_url=fetch_public(candidate['url'],MAX_IMAGE if candidate['kind']=='image' else MAX_VIDEO)
    common={'source_url':candidate['url'],'resolved_url':final_url,'project_url':candidate['page_url'],'caption':candidate['label']}
    if candidate['kind']=='image':
        from PIL import Image, ImageOps
        try:
            with Image.open(io.BytesIO(data)) as im:
                if im.width*im.height>25_000_000: raise ValueError('项目图片像素过大。')
                animated=getattr(im,'is_animated',False)
                im=ImageOps.exif_transpose(im).convert('RGB')
                fid=f'fig-{max([int(f["id"].split("-")[1]) for f in manifest["figures"]] or [0])+1:03}'
                image=f'images/{fid}.png'; im.save(folder/image)
        except (OSError, Image.DecompressionBombError): raise ValueError('素材不是可解码的图片。') from None
        manifest['figures'].append(dict(common,id=fid,image=image,page=None,kind='project_image',bbox=[],reviewed=False,selected=False,
                                       crop_status='project_original',animation_note='动画仅取首帧，请回看来源。' if animated else ''))
    else:
        ext='.mp4' if len(data)>12 and data[4:8]==b'ftyp' else '.webm' if data.startswith(b'\x1aE\xdf\xa3') else ''
        if not ext: raise ValueError('只支持有效的 MP4/WebM 原视频。')
        existing=manifest.setdefault('project_media',[])
        if sum(x.get('bytes',0) for x in existing)+len(data)>160*1024*1024: raise ValueError('此论文视频总量不能超过 160 MB。')
        fid='media-'+candidate['id']; relative=f'media/{fid}{ext}'
        (folder/'media').mkdir(exist_ok=True);(folder/relative).write_bytes(data)
        existing.append(dict(common,id=fid,file=relative,kind='video',bytes=len(data),selected=True,
                             evidence_note='仅下载原视频；写作模型未观看其时序内容。'))
    write_json(folder/'source.json',manifest)
    return manifest
