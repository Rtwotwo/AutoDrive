"""PDF evidence extraction. PDF text is source data, never instructions."""
import json
from functools import wraps
import threading
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from publication import resource_url

import pdf_backend as pdf

MAX_BYTES = 60 * 1024 * 1024
MAX_PAGES = 120
MAX_TEXT = 600_000
ARXIV_ID = re.compile(r'(?:\d{4}\.\d{4,5}|[a-zA-Z][a-zA-Z.\-]+/\d{7})(?:v\d+)?')
CAPTION = re.compile(r'^(?i:Figure|Fig\.|Table|图|表)\s*\d+(?:[A-Za-z])?(?:\s*[.:：]|\s+(?=[A-Z\u4e00-\u9fff]))')
PDF_LOCK = threading.RLock()


def serialized_pdf(function):
    @wraps(function)
    def locked(*args, **kwargs):
        with PDF_LOCK:
            return function(*args, **kwargs)
    return locked


def write_json(path, value):
    import time
    import uuid
    path = Path(path)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        # Windows readers/virus scanners can briefly prevent atomic replacement.
        # Retry only the local rename, never the API operation producing this data.
        for attempt in range(8):
            try:
                tmp.replace(path)
                break
            except PermissionError:
                if attempt == 7:
                    raise
                time.sleep(0.05 * (attempt + 1))
    finally:
        tmp.unlink(missing_ok=True)


def parse_arxiv(value):
    value = str(value).strip()
    if ARXIV_ID.fullmatch(value):
        return value
    url = urllib.parse.urlsplit(value)
    if url.scheme != 'https' or url.hostname not in {'arxiv.org', 'www.arxiv.org', 'export.arxiv.org'} or url.username or url.password or url.port:
        raise ValueError('请输入 arxiv.org 的 HTTPS 链接或 arXiv ID。')
    path = urllib.parse.unquote(url.path).removesuffix('.pdf').rstrip('/')
    for prefix in ('/abs/', '/pdf/', '/html/'):
        if path.startswith(prefix) and ARXIV_ID.fullmatch(path[len(prefix):]):
            return path[len(prefix):]
    raise ValueError('无法识别 arXiv ID。示例：https://arxiv.org/abs/2212.10156')


class ArxivRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlsplit(newurl)
        if url.scheme != 'https' or url.hostname not in {'arxiv.org', 'www.arxiv.org', 'export.arxiv.org'}:
            raise ValueError('arXiv 返回了不受支持的下载跳转。')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_arxiv_bytes(url, limit=MAX_BYTES, *, timeout=60, attempts=2, check_cancel=lambda:None):
    opener = urllib.request.build_opener(ArxivRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': 'AutoDrive-Paper-Studio/1.0 (local research reader)'})
    for attempt in range(attempts):
        check_cancel()
        try:
            with opener.open(request, timeout=timeout) as response:
                data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError('下载文件超过大小限制。')
            return data
        except urllib.error.HTTPError as exc:
            check_cancel()
            if attempt + 1 < attempts and exc.code in {429, 502, 503, 504}:
                time.sleep(3)
                continue
            raise ValueError(f'arXiv 下载失败（HTTP {exc.code}）；可直接上传 PDF。') from None
        except (urllib.error.URLError, TimeoutError, OSError):
            check_cancel()
            if attempt + 1 < attempts:
                time.sleep(3)
                # Retry a public PDF through arXiv's own export host; keep TLS verification.
                if url.startswith('https://arxiv.org/pdf/'):
                    request=urllib.request.Request(url.replace('https://arxiv.org/','https://export.arxiv.org/',1),headers={'User-Agent':'PaperStudio/1.0 (local research reader)'})
                continue
            raise ValueError('arXiv 连接中断或超时；已保留本地进度，请稍后重试。') from None
    raise ValueError('arXiv 下载失败。')


def download_arxiv(value, progress=lambda *_: None):
    aid = parse_arxiv(value)
    progress('正在从 arXiv 下载论文 PDF…')
    data = fetch_arxiv_bytes('https://arxiv.org/pdf/' + aid,check_cancel=lambda:progress('正在从 arXiv 下载当前论文 PDF…'))
    progress('正在读取论文元数据…')
    return data, arxiv_metadata(aid,check_cancel=lambda:progress('正在读取论文元数据…'))


def arxiv_metadata(aid,check_cancel=lambda:None):
    aid = parse_arxiv(aid)
    meta = {'arxiv_id': aid, 'url': 'https://arxiv.org/abs/' + aid}
    try:
        raw = fetch_arxiv_bytes('https://export.arxiv.org/api/query?id_list=' + urllib.parse.quote(aid), 2_000_000,check_cancel=check_cancel)
        entry = ET.fromstring(raw).find('{http://www.w3.org/2005/Atom}entry')
        if entry is not None and 'arxiv.org/abs/' in (entry.findtext('{http://www.w3.org/2005/Atom}id') or ''):
            ns = '{http://www.w3.org/2005/Atom}'
            meta.update(title=' '.join((entry.findtext(ns + 'title') or '').split()),
                        authors=[a.findtext(ns + 'name', '') for a in entry.findall(ns + 'author')],
                        published=entry.findtext(ns + 'published', '')[:10])
    except Exception:
        meta['metadata_note'] = 'arXiv 元数据接口未响应；标题来自 PDF，请检查。'
    check_cancel()
    return meta


def render_clip(page, path, box=None, width=2000, trim=False):
    rect = pdf.Rect(box) if box else page.rect
    rect = rect & page.rect
    if rect.is_empty or rect.width < 10 or rect.height < 10:
        raise ValueError('裁剪区域过小或超出页面。')
    scale = min(width / rect.width, 4, (8_000_000 / (rect.width * rect.height)) ** .5)
    pix = page.get_pixmap(matrix=pdf.Matrix(scale, scale), clip=rect, alpha=False)
    if trim:
        from PIL import Image, ImageChops
        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        difference = ImageChops.difference(image, Image.new('RGB', image.size, 'white')).convert('L')
        bounds = difference.point(lambda p: 255 if p > 7 else 0).getbbox()
        if bounds:
            a,b,c,d = bounds; pad = 12
            bounds = (max(0,a-pad),max(0,b-pad),min(image.width,c+pad),min(image.height,d+pad))
            image = image.crop(bounds)
            rect = pdf.Rect(rect.x0+bounds[0]/scale,rect.y0+bounds[1]/scale,rect.x0+bounds[2]/scale,rect.y0+bounds[3]/scale) & page.rect
        image.save(path)
    else: pix.save(path)
    return list(rect)


def guess_title(page, metadata, filename):
    if metadata.get('title'):
        return metadata['title']
    spans = [s for b in page.get_text('dict')['blocks'] if 'lines' in b
             for line in b['lines'] if abs(line.get('dir', (1, 0))[1]) < .1
             for s in line['spans'] if s['text'].strip() and 25 < s['bbox'][1] < page.rect.height * .45
             and not re.search(r'arxiv:|preprint|under review|conference on|copyright', s['text'], re.I)]
    if spans:
        largest = max(s['size'] for s in spans)
        title = ' '.join(s['text'].strip() for s in spans if s['size'] >= largest - .8)
        if len(title) >= 12:
            return title[:400]
    return Path(filename).stem[:200]


@serialized_pdf
def refresh_identity(folder, manifest, progress=lambda *_: None, online=True):
    """Repair extraction independently of explicit user-entered paper_info."""
    with pdf.open(Path(folder) / 'source.pdf') as doc:
        first = doc[0]
        text = first.get_text()
        match = re.search(r'\barXiv\s*:\s*(' + ARXIV_ID.pattern + ')', text, re.I)
        aid = manifest.get('arxiv_id') or (match.group(1) if match else '')
        title = guess_title(first, {}, manifest.get('filename', 'paper.pdf'))
        meta = {}
        if aid:
            meta = {'arxiv_id': aid, 'url': 'https://arxiv.org/abs/' + aid}
            if online:
                progress('已识别 PDF 中的 arXiv ID，正在补齐官方题名与作者…')
                meta = arxiv_metadata(aid)
        manifest.update(title=meta.get('title') or title)
        for key in ('arxiv_id', 'authors', 'published', 'metadata_note'):
            if key in meta: manifest[key] = meta[key]
        if meta.get('url'): manifest['source_url'] = meta['url']
        if meta.get('title'): manifest['metadata_note'] = ''
    write_json(Path(folder) / 'source.json', manifest)
    return manifest


def caption_box(page, block, captions, table_boxes=None):
    """Keep table headers/rows/footnotes; a full page is the honest uncertain fallback."""
    x0, y0, x1, y1 = block[:4]
    left, right = max(12, x0 - 8), min(page.rect.width - 12, x1 + 8)
    if right - left > page.rect.width * .65: left, right = 24, page.rect.width - 24
    def same_column(rect):
        overlap = min(right, rect[2]) - max(left, rect[0])
        return overlap > .45 * min(right - left, rect[2] - rect[0])
    previous = max([24] + [b[3] + 3 for b in captions if b[3] < y0 and same_column(b)])
    following = min([page.rect.height - 24] + [b[1] - 3 for b in captions if b[1] > y1 and same_column(b)])
    if re.match(r'^(Table|表)', block[4].strip(), re.I):
        boxes = [pdf.Rect(r) for r in (table_boxes or []) if same_column(r)]
        above = [r for r in boxes if previous <= r.y0 and r.y1 <= y0 + 2]
        below = [r for r in boxes if y1 - 2 <= r.y0 and r.y1 <= following]
        near_above = above and y0 - max(r.y1 for r in above) < 85
        near_below = below and min(r.y0 for r in below) - y1 < 85
        # A top-caption table earlier on this page owns the rows immediately
        # above the next caption. Do not mistake its closing rows for this table.
        table_captions = sorted([b for b in captions if re.match(r'^(Table|表)', b[4].strip(), re.I)],key=lambda b:b[1])
        if near_above and near_below and table_captions and boxes:
            first=table_captions[0]
            if first[3] < min(r.y0 for r in boxes) and first[1] < y0:near_above=False
        if bool(near_above) == bool(near_below):
            return list(page.rect), 'page_fallback'
        candidates = above if near_above else below
        chosen = [min(candidates, key=lambda r: abs((y0-r.y1) if near_above else (r.y0-y1)))]
        # Join nearby fragments of this table, not all tables in the column.
        for r in sorted(candidates, key=lambda r: abs((y0-r.y1) if near_above else (r.y0-y1))):
            if any(not (r.y0 > c.y1+35 or r.y1 < c.y0-35) for c in chosen): chosen.append(r)
        # Adjacent table fragments often represent header, body and subtables separately.
        lower = min(r.y0 for r in chosen)
        upper = max(r.y1 for r in chosen)
        try:
            rules = []
            for drawing in page.get_drawings():
                for item in drawing['items']:
                    if item[0] == 'l':
                        a, b = item[1:3]
                        if abs(a.y - b.y) < 1 and abs(a.x - b.x) > (right - left) * .45:
                            r = (min(a.x, b.x), a.y, max(a.x, b.x), b.y)
                            if same_column(r): rules.append(a.y)
            candidates = sorted(y for y in rules if previous <= y <= (y0 if near_above else following) and (near_above or y >= y1))
            for y in reversed([y for y in candidates if y < lower]):
                if lower - y > 85: break
                lower = y
            for y in [y for y in candidates if y > upper]:
                if y - upper > 85: break
                upper = y
        except Exception:
            pass
        return [max(12, min(left, min(r.x0 for r in chosen)) - 3), max(12, min(lower, y0) - 7),
                min(page.rect.width - 12, max(right, max(r.x1 for r in chosen)) + 3),
                min(page.rect.height - 12, max(upper, y1) + 8)], 'table_detected'
    visuals = [pdf.Rect(i['bbox']) for i in page.get_image_info()]
    try: visuals += list(page.cluster_drawings())
    except Exception: pass
    relevant = [r for r in visuals if r.width > 25 and r.height > 20 and r.y0 >= previous - 4
                and r.y1 <= y0 + 4 and r.y1 > max(previous, y0 - page.rect.height * .65) and same_column(r)]
    if not relevant: return list(page.rect), 'page_fallback'
    nearest = max(relevant, key=lambda r:r.y1)
    if y0-nearest.y1 > 85: return list(page.rect), 'page_fallback'
    chosen = [nearest]
    # Spatially connected panels. Text paragraphs between a picture and caption
    # make the association uncertain, instead of swallowing the whole page.
    changed = True
    while changed:
        changed = False
        for r in relevant:
            if r in chosen: continue
            def aligned_panel(c):
                vertical=min(r.y1,c.y1)-max(r.y0,c.y0)
                gap=max(r.x0-c.x1,c.x0-r.x1,0)
                return vertical>.75*min(r.height,c.height) and gap<=max(36,(right-left)*.10)
            if any((r+(-22,-22,22,22)).intersects(c) or aligned_panel(c) for c in chosen):
                chosen.append(r); changed = True
    rect = pdf.Rect(chosen[0])
    for r in chosen: rect |= r
    # Thin colour bars and legends are visually small but scientifically essential.
    for r in visuals:
        if r.width > 1 and r.height > 1 and r.y0 >= previous-4 and r.y1 < y0 and (rect+(-16,-10,16,10)).intersects(r):
            rect |= r
    for b in page.get_text('blocks'):
        if b[6] == 0 and same_column(b) and b[1] >= rect.y1+2 and b[3] < y0-2 and len(b[4].split()) > 30:
            return list(page.rect), 'page_fallback'
    # Include nearby short axis/panel labels, but keep the caption separate.
    for b in page.get_text('blocks'):
        if b[6] == 0 and b[3] < y0-2 and len(b[4].split()) < 30 and (rect+(-10,-10,10,10)).intersects(pdf.Rect(b[:4])):
            rect |= pdf.Rect(b[:4])
    return list((rect+(-5,-5,5,5)) & page.rect), 'figure_detected'


def page_tables(page, captions):
    if not any(re.match(r'^(Table|表)', b[4].strip(), re.I) for b in captions): return []
    try: boxes=[t.bbox for t in page.find_tables().tables]
    except Exception: boxes=[]
    # Borderless two-column tables often have only top/header/bottom rules.
    # Detect those without relying on grid intersections; whitespace separates
    # table rows from prose or another table.
    rules=[]
    for d in page.get_drawings():
        for item in d['items']:
            if item[0]=='l':
                a,b=item[1:3]
                if abs(a.y-b.y)<1 and abs(a.x-b.x)>100:rules.append((min(a.x,b.x),a.y,max(a.x,b.x),b.y))
    text=page.get_text('blocks')
    for caption in captions:
        if not re.match(r'^(Table|表)',caption[4].strip(),re.I):continue
        following=min([page.rect.height-24]+[b[1] for b in captions if b[1]>caption[3]])
        near=sorted([r for r in rules if caption[3]<=r[1]<following and min(r[2],caption[2])-max(r[0],caption[0])>.6*min(r[2]-r[0],caption[2]-caption[0])],key=lambda r:r[1])
        if len(near)<2 or near[0][1]-caption[3]>30:continue
        first=near[0];group=[first]
        for r in near[1:]:
            if abs(r[0]-first[0])>5 or abs(r[2]-first[2])>5:break
            rows=sorted([(max(b[1],group[-1][1]),min(b[3],r[1])) for b in text if b[6]==0 and b[3]>group[-1][1] and b[1]<r[1] and b[0]<r[2] and b[2]>r[0]])
            end=group[-1][1];gap=0
            for lo,hi in rows:gap=max(gap,lo-end);end=max(end,hi)
            gap=max(gap,r[1]-end)
            if gap>20:break
            group.append(r)
        if len(group)>=2:boxes.append((first[0],first[1],first[2],group[-1][1]))
    return boxes


@serialized_pdf
def repair_crops(folder, manifest, progress=lambda *_: None):
    folder = Path(folder)
    links = list(manifest.get('resource_links', []))
    with pdf.open(folder / 'source.pdf') as doc:
        for index, page in enumerate(doc):
            progress(f'重新识别第 {index + 1}/{len(doc)} 页图表，保留已确认的裁剪…')
            for link in page.get_links():
                url = resource_url(link.get('uri', ''))
                if url and url not in links: links.append(url)
            captions = [b for b in page.get_text('blocks') if b[6] == 0 and CAPTION.match(b[4].strip())]
            tables = page_tables(page, captions)
            for figure in list(manifest['figures']):
                if figure.get('page') != index + 1 or figure.get('reviewed') or figure.get('origin') or figure.get('crop_status') == 'manual': continue
                prefix = CAPTION.match(figure.get('original_caption', figure['caption']))
                match = next((b for b in captions if prefix and b[4].strip().startswith(prefix.group(0))), None)
                if match is None: continue
                box, status = caption_box(page, match, captions, tables) if match else (list(page.rect), 'page_fallback')
                box = render_clip(page, folder / figure['image'], box, trim=status!='page_fallback')
                figure.update(bbox=[round(v, 2) for v in box], crop_status=status)
                if status == 'page_fallback': figure['selected'] = False
            for block in captions:
                caption = ' '.join(block[4].split())[:1800]
                if any(f.get('original_page',f.get('page')) == index+1 and f.get('original_caption',f['caption']) == caption for f in manifest['figures']): continue
                if len(manifest['figures']) >= 100: break
                fid = next_figure_id(manifest)
                box, status = caption_box(page, block, captions, tables)
                box = render_clip(page, folder/'images'/(fid+'.png'), box, trim=status!='page_fallback')
                manifest['figures'].append({'id':fid,'page':index+1,'original_page':index+1,'caption':caption,'original_caption':caption,
                    'bbox':list(box),'original_bbox':list(box),'image':'images/'+fid+'.png','kind':'table' if caption.startswith(('Table','表')) else 'figure',
                    'crop_status':status,'selected':False,'reviewed':False})
    manifest['resource_links'] = links
    write_json(folder / 'source.json', manifest)
    return manifest


def next_figure_id(manifest):
    numbers = [int(f['id'][4:]) for f in manifest['figures'] if re.fullmatch(r'fig-\d{3}', f['id'])]
    return f'fig-{max(numbers, default=0)+1:03}'


@serialized_pdf
def extract_pdf(data, folder, filename='paper.pdf', metadata=None, progress=lambda *_: None):
    folder = Path(folder)
    if not data.startswith(b'%PDF-') or len(data) > MAX_BYTES:
        raise ValueError('请上传有效的 PDF，大小不超过 60 MB。')
    try:
        doc = pdf.open(stream=data, filetype='pdf')
    except Exception:
        raise ValueError('PDF 无法解析，请确认文件完整。') from None
    with doc:
        if doc.needs_pass:
            raise ValueError('请先解除 PDF 密码保护。')
        if not 1 <= len(doc) <= MAX_PAGES:
            raise ValueError('当前支持 1–120 页论文；请将超长附件拆分。')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'images').mkdir(exist_ok=True)
        (folder / 'source.pdf').write_bytes(data)
        metadata = metadata or {}
        pages, figures, links = [], [], []
        total_text = 0
        for index, page in enumerate(doc):
            page.set_rotation(0)
            progress(f'解析第 {index + 1}/{len(doc)} 页：正文、图注与原图…')
            text = page.get_text(sort=True)
            for link in page.get_links():
                url = resource_url(link.get('uri', ''))
                if url and url not in links: links.append(url)
            total_text += len(text)
            if total_text > MAX_TEXT:
                raise ValueError('提取文字超过 60 万字符；请拆分论文与补充材料。')
            page_image = f'images/page-{index + 1:03}.png'
            render_clip(page, folder / page_image, width=1050)
            pages.append({'number': index + 1, 'text': text, 'image': page_image,
                          'width': round(page.rect.width, 2), 'height': round(page.rect.height, 2)})
            blocks = [b for b in page.get_text('blocks') if b[6] == 0]
            captions = [b for b in blocks if CAPTION.match(b[4].strip())]
            tables = page_tables(page, captions)
            for block in captions:
                if len(figures) >= 50:
                    break
                x0, y0, x1, y1 = block[:4]
                caption = ' '.join(block[4].split())[:1800]
                is_table = bool(re.match(r'^(Table|表)', caption, re.I))
                box, crop_status = caption_box(page, block, captions, tables)
                fid = f'fig-{len(figures) + 1:03}'
                image = f'images/{fid}.png'
                box = render_clip(page, folder / image, box, trim=crop_status!='page_fallback')
                figures.append({'id': fid, 'page': index + 1, 'caption': caption, 'original_caption': caption,
                                'original_page': index + 1, 'original_bbox': [round(v, 2) for v in box], 'image': image,
                                'kind': 'table' if is_table else 'figure', 'bbox': [round(v, 2) for v in box],
                                'crop_status': crop_status, 'reviewed': False, 'selected': len(figures) < 8 and crop_status!='page_fallback'})
        title = guess_title(doc[0], metadata, filename)
    warnings = []
    thin_pages = [p['number'] for p in pages if len(p['text'].strip()) < 80]
    if thin_pages:
        warnings.append('以下页面文字不足，可能是扫描页或纯图页：' + ', '.join(map(str, thin_pages)) + '。图像不是已识别的正文。')
    if not figures:
        warnings.append('未定位到标准图注；可从原文页拖选图片区域。')
    if len(figures) == 50:
        warnings.append('已达到 50 张自动候选图上限，其他图片可从原文页手动裁剪。')
    manifest = {'id': folder.name, 'title': title, 'authors': metadata.get('authors', []),
                'source_url': metadata.get('url', ''), 'arxiv_id': metadata.get('arxiv_id', ''),
                'published': metadata.get('published', ''), 'filename': Path(filename).name, 'resource_links': links,
                'pages': pages, 'figures': figures, 'warnings': warnings,
                'metadata_note': metadata.get('metadata_note', ''), 'text_chars': total_text,
                'can_generate': total_text >= 300 and len(thin_pages) < max(2, len(pages) // 2),
                'created_at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
    write_json(folder / 'source.json', manifest)
    return manifest


@serialized_pdf
def crop_figure(folder, manifest, page_number, normalized_box, caption='', figure_id=None):
    if not isinstance(page_number, int) or isinstance(page_number, bool) or not 1 <= page_number <= len(manifest['pages']):
        raise ValueError('无效页码。')
    if not isinstance(normalized_box, list) or len(normalized_box) != 4 or not all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in normalized_box):
        raise ValueError('裁剪坐标必须是 0–1 范围内的四个值。')
    x0, y0, x1, y1 = normalized_box
    if x1 - x0 < .02 or y1 - y0 < .02:
        raise ValueError('请拖选一个更大的区域。')
    old = next((f for f in manifest['figures'] if f['id'] == figure_id), None)
    if figure_id and not old:
        raise ValueError('图片不存在。')
    if not old and len(manifest['figures']) >= 100:
        raise ValueError('每篇论文最多保留 100 张图片。')
    fid = old['id'] if old else f'fig-{len(manifest["figures"]) + 1:03}'
    with pdf.open(Path(folder) / 'source.pdf') as doc:
        page = doc[page_number - 1]
        page.set_rotation(0)
        box = [x0 * page.rect.width, y0 * page.rect.height, x1 * page.rect.width, y1 * page.rect.height]
        box = render_clip(page, Path(folder) / 'images' / (fid + '.png'), box, trim=True)
    figure = {'id': fid, 'page': page_number, 'caption': str(caption)[:1800] or (old or {}).get('caption', f'原文第 {page_number} 页选图'),
              'original_caption': (old or {}).get('original_caption', (old or {}).get('caption', '')),
              'original_page': (old or {}).get('original_page', (old or {}).get('page', page_number)),
              'original_bbox': (old or {}).get('original_bbox', (old or {}).get('bbox', box)),
              'kind': (old or {}).get('kind', 'figure'), 'bbox': box, 'image': f'images/{fid}.png', 'reviewed': True, 'selected': True, 'crop_status':'manual'}
    if old:
        manifest['figures'][manifest['figures'].index(old)] = figure
    else:
        manifest['figures'].append(figure)
    write_json(Path(folder) / 'source.json', manifest)
    return manifest
