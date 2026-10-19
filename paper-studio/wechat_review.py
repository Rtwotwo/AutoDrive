"""Human approval and exact, compact WeChat draft payloads. No network access."""
import json
import re
import time
from html import escape
from pathlib import Path
from publication import clean_article, paper_details, resource_url, layout_sections
from sources import write_json

CHECKS = ('facts', 'figures', 'attribution', 'final_read')
THEMES = {'ink':'#234d43', 'orange':'#b9552e', 'blue':'#285ba5', 'baoyu':'#234d43'}


def read_json(path, default=None):
    return json.loads(path.read_text(encoding='utf8')) if path.exists() else default


def asset_path(folder, name):
    if not re.fullmatch(r'images/fig-\d{3}\.png|covers/cover-[0-9a-f]{16}\.png', str(name)):
        raise ValueError('提交图片路径无效，请重新选择配图。')
    folder=Path(folder).resolve(); path=(folder/name).resolve()
    if not path.is_relative_to(folder) or not path.is_file():
        raise ValueError('提交图片不存在，请重新选择配图。')
    return path


def clean_options(values, article, source):
    result={key:str(values.get(key, default)).strip() for key,default in
            [('title',article.get('title','')),('digest',article.get('digest','')),
             ('author',''),('cover_id',''),('theme','ink')]}
    result['source_url']=resource_url(values.get('source_url',paper_details(article,source).get('paper_url','')))
    if not result['title'] or len(result['title'])>32: raise ValueError('公众号标题需为 1–32 个字符，请在审核页调整。')
    if len(result['author'])>16: raise ValueError('公众号署名最多 16 个字符。')
    if len(result['digest'])>120: raise ValueError('投递摘要尚未适配，请保存提交设置以自动生成短版；原稿摘要完整保留。')
    if len(result['source_url'].encode())>1024: raise ValueError('阅读原文链接过长。')
    if result['theme'] not in THEMES: raise ValueError('无效排版主题。')
    result['baoyu_theme']=str(values.get('baoyu_theme','simple'))
    if result['baoyu_theme'] not in {'simple','default','grace','modern'}:raise ValueError('无效宝玉主题。')
    if result['cover_id'] not in {f['id'] for f in source['figures']+source.get('covers',[])}:
        raise ValueError('请先选择一张封面图。')
    return result


def render_content(article, source, options):
    """Compact inline HTML; all content preserved, no data URI or hidden evidence."""
    article=clean_article(article); info=paper_details(article,source)
    color=THEMES[options['theme']]; figures={f['id']:f for f in source['figures']}
    def p(text, style=''):
        return ('<p style="'+style+'">' if style else '<p>')+escape(str(text)).replace('\n','<br>')+'</p>'
    def link(url):
        url=resource_url(url)
        return '<a href="'+escape(url,quote=True)+'" style="word-break:break-all;">'+escape(url)+'</a>' if url else '未核实'
    out=['<section style="font-size:16px;line-height:1.9;color:#303936;word-break:break-word;">',
         '<section style="padding:16px;background:#f3f6f2;border-top:3px solid '+color+';font-size:12px;">',
         p(info['title'],'font-size:20px;font-weight:bold;'),p('作者：'+('；'.join(info.get('authors',[])) or '未核实')),
         p('机构：'+('；'.join(info.get('affiliations',[])) or '未核实'))]
    for key in ('venue','version_note'):
        if info.get(key):out.append(p(info[key]))
    for key,label in [('paper_url','论文'),('project_url','项目主页'),('code_url','代码仓库')]:
        out.append('<p>'+label+'：<br>'+link(info.get(key))+'</p>')
    out.append('</section>')
    out.append(p(article.get('digest',''),'padding:16px;background:#f2f5f3;margin-top:20px;'))
    out.append(p(article.get('lead','')))
    for section in layout_sections(article):
        if section['heading']: out.append('<h2 style="font-size:21px;color:'+color+';margin:32px 0 20px;">'+escape(section['heading'])+'</h2>')
        out.extend(p(x['text']) for x in section['paragraphs'])
        for t in section.get('tables',[]):
            out.append(p(t.get('title','结果摘要'),'font-weight:bold;'))
            out.append('<table border="1" bordercolor="#cdd7ce" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:12px;table-layout:fixed;"><tbody><tr>')
            out.extend('<th>'+escape(c)+'</th>' for c in t['columns']);out.append('</tr>')
            for row in t['rows']:
                out.append('<tr>');out.extend('<td>'+escape(c)+'</td>' for c in row);out.append('</tr>')
            out.append('</tbody></table>');out.append(p(' · '.join(x for x in [t.get('source_label'),t.get('note')] if x),'font-size:12px;color:#718175;'))
        for fig in section.get('figures',[]):
            original=figures[fig['id']]
            out.append('<p><img src="'+escape(original['image'],quote=True)+'" style="width:100%;height:auto;"></p>')
            out.append(p(fig.get('caption') or original.get('caption',''),'font-size:12px;color:#718175;'))
            if fig.get('explanation'):out.append(p(fig['explanation'],'font-size:14px;'))
            if original.get('kind')=='project_image':out.append('<p style="font-size:12px;">图片来源：作者项目主页 '+link(original.get('project_url'))+'</p>')
    for media in source.get('project_media',[]):
        if media.get('selected',True):out.append('<p>项目视频｜'+escape(media.get('caption','作者演示'))+'<br>'+link(media.get('source_url'))+'</p>')
    if article.get('takeaways'):
        out.append('<h2 style="font-size:21px;">结语</h2>');out.extend(p(x) for x in article['takeaways'])
    out.append(p('图表来源：原论文及标注的作者项目页；结果摘要为选定指标的整理。本文为中文研究解读。','font-size:12px;color:#718175;'))
    out.append('</section>')
    return ''.join(out)


def prepare(folder, article, source, values, account):
    options=clean_options(values,article,source)
    if options['theme']=='baoyu':
        from formatting import current_baoyu
        content=current_baoyu(folder,article,source,options)
    else:content=render_content(article,source,options)
    used=list(dict.fromkeys(f['id'] for section in article['sections'] for f in section.get('figures',[])))
    figures={f['id']:f for f in source['figures']+source.get('covers',[])}; assets=[]
    for ident in dict.fromkeys(used+[options['cover_id']]):
        figure=figures[ident]
        if figure.get('origin') in {'local_image','pdf_embedded'} and not figure.get('reviewed'):
            raise ValueError('待提交图中有新导入或替换的素材，请在“原文与配图”对照原页核对完整性并勾选“已核对”。')
        if figure.get('crop_status')=='page_fallback' and not figure.get('reviewed'):
            raise ValueError('待提交图中仍有未核对的整页回退，请在配图页重裁或明确核对后再审核。')
        path=asset_path(folder,figure['image']);stat=path.stat()
        assets.append({'id':ident,'image':figure['image'],'size':stat.st_size,'mtime_ns':stat.st_mtime_ns})
    # Official docs have a contradictory 2 KB sentence alongside 20k characters/1 MB.
    # Use the long-form limits and report any API rejection verbatim by numeric code.
    if len(content)>=20000 or len(content.encode())>=1_000_000:
        raise ValueError(f'公众号正文排版后为 {len(content):,} 字符，需少于 20,000；请减少正文或表格后重新审核。不会自动删减。')
    return {'options':options,'content':content,'assets':assets,'inline_ids':used,
            'account':{'appid':account.get('appid',''),'name':account.get('name','')},
            'video_count':sum(bool(m.get('selected',True)) for m in source.get('project_media',[]))}


def approve(folder, prepared, checks, reviewer=''):
    if not isinstance(checks,dict) or any(checks.get(k) is not True for k in CHECKS):
        raise ValueError('请完成人工审核的全部确认项。')
    if not prepared['account']['appid']:raise ValueError('请先配置目标公众号，再审核提交。')
    value={'approved':True,'reviewed_at':time.time(),'reviewer':str(reviewer).strip()[:80],
           'checks':{k:True for k in CHECKS},'snapshot':prepared}
    write_json(Path(folder)/'wechat-review.json',value)
    return value


def is_approved(folder,prepared):
    review=read_json(Path(folder)/'wechat-review.json',{})
    return review.get('approved') is True and review.get('snapshot')==prepared


def require_approved(folder,prepared):
    if not is_approved(folder,prepared):raise ValueError('文章、配图、排版或目标账号已变更，或尚未人工审核；请重新确认后提交。')


def revoke(folder):
    review=read_json(Path(folder)/'wechat-review.json',{})
    if review:
        review['approved']=False;write_json(Path(folder)/'wechat-review.json',review)
