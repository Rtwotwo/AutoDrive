"""Escaped, inline-style publication artifacts with original paper images."""
import base64
from html import escape
import io
import json
from pathlib import Path
import re
import zipfile
from writing import validate_article
from publication import clean_public_text, clean_article, paper_details, resource_url, layout_sections

FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Microsoft YaHei,sans-serif'
THEMES = {'ink': '#234d43', 'orange': '#b9552e', 'blue': '#285ba5'}


def safe_url(value):
    return resource_url(value)


def page_note(pages):
    return '原文 p. ' + ', '.join(str(p) for p in pages if type(p) is int) if isinstance(pages, list) and pages else '页码待核对'


def markdown_text(value):
    # The schema holds prose, not executable HTML, remote images or code fences.
    value = ' '.join(clean_public_text(value).splitlines()).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_{}\[\]()#!|~])', r'\\\1', value)


def markdown(article, manifest):
    article = clean_article(article)
    info = paper_details(article, manifest)
    figures = {f['id']: f for f in manifest['figures']}
    parts = ['# ' + markdown_text(article['title']), '', '## 论文信息', '',
             '**英文标题**：' + markdown_text(info['title']), '',
             '**作者**：' + markdown_text('；'.join(info.get('authors', [])) or '未核实'), '',
             '**机构**：' + markdown_text('；'.join(info.get('affiliations', [])) or '未核实'), '']
    for key, label in (('venue', '发表信息'), ('version_note', '版本说明')):
        if info.get(key): parts += ['**' + label + '**：' + markdown_text(info[key]), '']
    for key, label in (('paper_url', '论文'), ('project_url', '项目主页'), ('code_url', '代码仓库')):
        url = safe_url(info.get(key))
        parts += ['**' + label + '**：' + (url or '未核实'), '']
    parts += ['---', '', '> ' + markdown_text(article.get('digest', '')), '', markdown_text(article.get('lead', '')), '']
    for section in layout_sections(article):
        if section['heading']: parts += ['## ' + markdown_text(section['heading']), '']
        for para in section['paragraphs']:
            parts += [markdown_text(para['text']), '']
        for table in section.get('tables', []):
            parts += ['**' + markdown_text(table.get('title', '结果摘要')) + '**', '',
                      '| ' + ' | '.join(markdown_text(c) for c in table['columns']) + ' |',
                      '| ' + ' | '.join('---' for c in table['columns']) + ' |']
            parts += ['| ' + ' | '.join(markdown_text(c) for c in row) + ' |' for row in table['rows']]
            parts += ['', markdown_text(' · '.join(t for t in (table.get('source_label'), table.get('note')) if t)), '']
        for f in section.get('figures', []):
            original = figures[f['id']]
            caption = markdown_text(f.get('caption') or original['caption'])
            parts += [f'![{caption.replace("[", "(").replace("]", ")")}]({original["image"]})', '',
                      caption, '', markdown_text(f.get('explanation', '')), '']
            if original.get('kind') == 'project_image':
                parts += ['图片来源：' + safe_url(original.get('project_url')), markdown_text(original.get('animation_note','')), '']
    for media in manifest.get('project_media', []):
        if media.get('selected', True): parts += ['## 项目视频 · ' + markdown_text(media.get('caption','作者演示')), '', safe_url(media.get('source_url')), '']
    if article.get('takeaways'):
        parts += ['## 带走这几个判断', ''] + ['- ' + markdown_text(x) for x in article['takeaways']] + ['']
    parts += ['---', '', '图表来源：原论文；文中的结果摘要为选定指标的整理。本文为中文研究解读。', '']
    return '\n'.join(parts)


def article_html(article, manifest, folder, theme='ink', embed=False, asset_prefix='', preview_media=False):
    if theme=='baoyu':
        from formatting import current_baoyu
        path=Path(folder)/'wechat-options.json'
        options=json.loads(path.read_text(encoding='utf8')) if path.exists() else {}
        content=current_baoyu(folder,article,manifest,options)
        for f in manifest['figures']:
            url=('data:image/png;base64,'+base64.b64encode((Path(folder)/f['image']).read_bytes()).decode()) if embed else asset_prefix+f['image']
            content=content.replace('src="'+f['image']+'"','src="'+escape(url,quote=True)+'"')
        return content
    article = clean_article(article)
    info = paper_details(article, manifest)
    color = THEMES.get(theme, THEMES['ink'])
    figures = {f['id']: f for f in manifest['figures']}
    def p(text, style=''):
        return f'<p style="margin:0 0 20px;font-size:16px;line-height:1.95;color:#303936;text-align:left;word-break:break-word;{style}">{escape(clean_public_text(text)).replace(chr(10), "<br>")}</p>'
    out = [f'<section style="font-family:{FONT};color:#303936;padding:8px 4px;max-width:100%;box-sizing:border-box;">',
           f'<section style="margin:0 0 28px;padding:20px;background:#f3f6f2;border-top:3px solid {color};">',
           p('PAPER / 论文信息', f'font-size:11px;letter-spacing:2px;color:{color};margin-bottom:10px;font-weight:700;'),
           p(info['title'], f'font-size:20px;line-height:1.5;color:{color};font-weight:700;margin-bottom:16px;'),
           p('作者  /  ' + '；'.join(info.get('authors', [])) if info.get('authors') else '作者  /  未核实', 'font-size:12px;line-height:1.8;margin-bottom:10px;'),
           p('机构  /  ' + '；'.join(info.get('affiliations', [])) if info.get('affiliations') else '机构  /  未核实', 'font-size:12px;line-height:1.8;margin-bottom:10px;')]
    for key in ('venue', 'version_note'):
        if info.get(key): out += [p(info[key], 'font-size:12px;line-height:1.7;color:#60736a;margin-bottom:10px;')]
    for key, label in (('paper_url', '论文'), ('project_url', '项目主页'), ('code_url', '代码仓库')):
        url = safe_url(info.get(key))
        out += [f'<p style="font-size:12px;line-height:1.7;margin:8px 0;overflow-wrap:anywhere;"><strong>{label}</strong><br>' +
                (f'<a href="{escape(url, quote=True)}" style="color:{color};word-break:break-all;text-decoration:underline;">{escape(url)}</a>' if url else '未核实') + '</p>']
    out += ['</section>']
    if article.get('digest'):
        out += [f'<section style="background:#f2f5f3;padding:20px;margin:0 0 28px;border-left:3px solid {color};">', p(article['digest'], 'font-size:15px;margin:0;'), '</section>']
    out += [p(article.get('lead', ''))]
    for section in layout_sections(article):
        index=section['display_number']-1
        if section['heading']: out += [f'<h2 style="margin:38px 0 22px;padding:0 0 14px;border-bottom:1px solid #dce3df;font-size:21px;line-height:1.55;color:{color};"><span style="display:block;font-size:11px;letter-spacing:2px;font-weight:500;margin-bottom:7px;color:#8b9b8e;">{index + 1:02d} / RESEARCH NOTE</span>{escape(section["heading"])}</h2>']
        for para in section['paragraphs']:
            out += [p(para['text'])]
        for table in section.get('tables', []):
            out += [f'<section style="margin:24px 0;padding:16px 12px;background:#f5f7f3;border:1px solid #e2e8df;">',
                    p(table.get('title', '结果摘要'), f'color:{color};font-size:15px;font-weight:700;margin-bottom:14px;'),
                    '<table style="border-collapse:collapse;table-layout:fixed;width:100%;font-size:12px;line-height:1.7;"><thead><tr>']
            for column in table['columns']:
                out += [f'<th style="padding:8px 5px;border-bottom:2px solid {color};text-align:left;word-break:break-word;color:{color};">{escape(column)}</th>']
            out += ['</tr></thead><tbody>']
            for row_index, row in enumerate(table['rows']):
                out += [f'<tr style="background:{"#ffffff" if row_index % 2 == 0 else "#eef3ed"};">']
                out += ['<td style="padding:9px 5px;border-bottom:1px solid #dfe6db;vertical-align:top;word-break:break-word;">' + escape(cell) + '</td>' for cell in row]
                out += ['</tr>']
            out += ['</tbody></table>', p(' · '.join(t for t in (table.get('source_label'), table.get('note')) if t), 'font-size:11px;line-height:1.7;color:#758477;margin:12px 0 0;'), '</section>']
        for fig in section.get('figures', []):
            original = figures[fig['id']]
            image = original['image']
            if embed:
                image = 'data:image/png;base64,' + base64.b64encode((Path(folder) / image).read_bytes()).decode()
            else:
                image = asset_prefix + image
            caption = fig.get('caption') or original['caption']
            out += [f'<section style="margin:26px 0;text-align:center;"><img src="{escape(image, quote=True)}" alt="{escape(caption, quote=True)}" style="max-width:100%;height:auto;display:block;margin:0 auto;">',
                    p(caption, 'font-size:12px;line-height:1.7;color:#7a8580;text-align:left;margin-top:10px;'), '</section>']
            if fig.get('explanation'):
                out += [p(fig['explanation'], f'font-size:14px;line-height:1.85;color:{color};padding:0 0 0 12px;border-left:2px solid #c2d0bf;')]
            if original.get('kind') == 'project_image':
                url = safe_url(original.get('project_url'))
                out += [p('图片来源：作者项目主页。' + (original.get('animation_note') or ''), 'font-size:11px;color:#78827e;'),
                        f'<p style="font-size:11px;word-break:break-all;"><a href="{escape(url,quote=True)}">{escape(url)}</a></p>']
    for media in manifest.get('project_media', []):
        if not media.get('selected', True): continue
        url = safe_url(media.get('source_url'))
        out += [f'<section style="padding:18px;margin:26px 0;background:#f2f5f3;border-left:3px solid {color};">',
                p('项目视频｜' + media.get('caption', '作者演示'), 'font-size:15px;font-weight:600;')]
        if preview_media:
            out += [f'<video controls preload="metadata" style="width:100%;height:auto;" src="{escape(asset_prefix+media["file"],quote=True)}"></video>']
        out += [f'<p style="font-size:12px;word-break:break-all;">作者发布的演示：<a href="{escape(url,quote=True)}">{escape(url)}</a></p></section>']
    if article.get('takeaways'):
        out += [f'<h2 style="margin:34px 0 18px;font-size:21px;color:{color};">带走这几个判断</h2>']
        for i, text in enumerate(article['takeaways']): out += [p(f'{i + 1}. {text}')]
    out += ['<section style="margin:32px 0 0;padding:20px 0 0;border-top:1px solid #dce3df;">',
            p('图表来源：原论文；文中的结果摘要为选定指标的整理。本文为中文研究解读。', 'font-size:12px;color:#78827e;'), '</section></section>']
    return ''.join(out)


def document_html(title, fragment):
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + escape(title) + '</title></head><body style="margin:0;background:#edf0ed;"><main style="box-sizing:border-box;max-width:720px;margin:24px auto;padding:30px 24px;background:white;"><h1 style="font-family:' + FONT + ';font-size:28px;line-height:1.45;color:#183d32;">' + escape(title) + '</h1>' + fragment + '</main></body></html>'


def export_bundle(article, manifest, folder, theme='ink'):
    audit = validate_article(article, manifest)
    fragment = article_html(article, manifest, folder, theme)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('article.md', markdown(article, manifest))
        archive.writestr('wechat.html', fragment)
        archive.writestr('preview.html', document_html(article['title'], article_html(article, manifest, folder, theme, preview_media=True)))
        archive.writestr('article.json', json.dumps(article, ensure_ascii=False, indent=2))
        archive.writestr('evidence-check.json', json.dumps(audit, ensure_ascii=False, indent=2))
        archive.writestr('source-metadata.json', json.dumps({k: v for k, v in manifest.items() if k != 'pages'}, ensure_ascii=False, indent=2))
        archive.writestr('source-dossier.md', '\n\n'.join(f'## PDF page {p["number"]}\n\n{p["text"]}' for p in manifest['pages']))
        used = {f['id'] for s in article['sections'] for f in s.get('figures', [])}
        for f in manifest['figures']:
            if f['id'] in used or f.get('kind') == 'project_image':
                archive.write(Path(folder) / f['image'], f['image'])
        for cover in manifest.get('covers', []):
            archive.write(Path(folder) / cover['image'], cover['image'])
        for media in manifest.get('project_media', []):
            if media.get('selected', True): archive.write(Path(folder) / media['file'], media['file'])
        archive.writestr('项目素材说明.txt', '项目图片与视频保留在 source-metadata.json 中的作者来源。视频原文件位于 media/，preview.html 可本地播放。公众号不支持直接粘贴本地 HTML 视频：请在后台添加视频并上传原文件，替换正文的视频来源卡片。模型未分析视频时序；请观看后再撰写具体行为结论。图片来源可访问不代表无限制转载，请核对作者许可。')
        archive.writestr('使用说明.txt', '1. 打开 preview.html 查看完整图文。\n2. 微信正文使用 wechat.html，标题填写 article.json 的 title。\n3. 图片在 images 文件夹。微信可能不保留本地图片路径或剪贴板图像，请在公众号编辑器逐张上传并对照图注。\n4. 发布前检查 evidence-check.json 中的警告，并回查原文。机械匹配不代表事实验证。\n5. source-dossier.md 是原文提取记录，不是推文，不应直接发布。\n')
    return stream.getvalue()
