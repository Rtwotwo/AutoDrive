"""Baoyu HTML adapter, tied to the exact saved Markdown input."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
from publication import resource_url

ALLOWED={'section','div','p','span','h1','h2','h3','h4','strong','b','em','i','a','img','br','hr','blockquote','ul','ol','li','table','thead','tbody','tr','th','td','code','pre','sup','sub'}
VOID={'img','br','hr'}
PROPERTIES={'color','background-color','font-size','font-weight','font-style','text-align','line-height','margin','margin-top','margin-bottom','padding','padding-left','border','border-left','border-top','border-bottom','border-collapse','border-radius','width','max-width','height','display','vertical-align','word-break','table-layout','text-decoration','letter-spacing'}


class FormatterHTML(HTMLParser):
    def __init__(self, allowed_images, compact=False):
        super().__init__(convert_charrefs=True)
        self.parts=[];self.body=False;self.skip=0;self.images=allowed_images;self.compact=compact
    def handle_starttag(self,tag,attrs):
        if tag=='body':self.body=True;return
        if not self.body:return
        if tag in {'script','style','iframe','object','svg'}:self.skip+=1;return
        if self.skip or tag not in ALLOWED:return
        values=dict(attrs);safe=[]
        if tag=='img':
            src=values.get('src','')
            if src not in self.images:raise ValueError('宝玉排版含未知图片，请重新排版。')
            safe.append(('src',src))
        if tag=='a':
            url=resource_url(values.get('href'))
            if url:safe.append(('href',url))
        if tag in {'td','th'}:
            for key in ('colspan','rowspan'):
                if re.fullmatch(r'[1-9][0-9]?',values.get(key,'')):safe.append((key,values[key]))
        styles={}
        for item in values.get('style','').split(';'):
            key,sep,val=item.partition(':');key=key.strip().lower();val=val.strip()
            if sep and key in PROPERTIES and not re.search(r'url|expression|@|[<>]',val,re.I):styles[key]=val
        if tag=='img':styles.update(width='100%',height='auto')
        if self.compact:
            # Compaction removes background wrappers: do not keep their white text.
            if tag in {'h1','h2','h3','h4'}:styles={'color':'#234d43'}
            elif tag=='img':styles={'width':'100%','height':'auto'}
            elif tag=='table':
                styles={'width':'100%','border-collapse':'collapse','font-size':'12px'}
                safe.extend([('border','1'),('cellpadding','5'),('cellspacing','0')])
            elif tag=='blockquote':styles={'border-left':'3px solid #234d43','padding-left':'12px','color':'#50635b'}
            else:styles={}
        if styles:safe.append(('style',';'.join(k+':'+v for k,v in styles.items())))
        self.parts.append('<'+tag+''.join(' '+k+'="'+escape(v,quote=True)+'"' for k,v in safe)+'>')
    def handle_endtag(self,tag):
        if tag=='body':self.body=False;return
        if tag in {'script','style','iframe','object','svg'} and self.skip:self.skip-=1;return
        if self.body and not self.skip and tag in ALLOWED and tag not in VOID:self.parts.append('</'+tag+'>')
    def handle_data(self,data):
        if self.body and not self.skip:self.parts.append(escape(data))


class UnwrapLayout(HTMLParser):
    """Only flatten attribute-free wrappers whose children already form blocks."""
    BLOCKS={'section','div','p','h1','h2','h3','h4','blockquote','ul','ol','table','hr','pre'}
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root={'tag':'','start':'','children':[],'attrs':[]};self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        n={'tag':tag,'attrs':attrs,'start':self.get_starttag_text(),'children':[]}
        self.stack[-1]['children'].append(n)
        if tag not in VOID:self.stack.append(n)
    def handle_endtag(self,tag):
        if len(self.stack)>1 and self.stack[-1]['tag']==tag:self.stack.pop()
    def handle_data(self,data):self.stack[-1]['children'].append(data)
    def handle_entityref(self,name):self.handle_data('&'+name+';')
    def handle_charref(self,name):self.handle_data('&#'+name+';')
    def render(self,node=None):
        n=self.root if node is None else node
        children=''.join(c if isinstance(c,str) else self.render(c) for c in n['children'])
        removable=n['tag']=='span' or (n['tag'] in {'section','div'} and all((not c.strip()) if isinstance(c,str) else c['tag'] in self.BLOCKS for c in n['children']))
        if not n['tag'] or (not n['attrs'] and removable):return children
        return n['start']+children+('' if n['tag'] in VOID else '</'+n['tag']+'>')


def compact_content(content,source):
    if len(content)<19500:return content
    parser=FormatterHTML({f['image'] for f in source['figures']},compact=True)
    parser.feed('<body>'+content+'</body>')
    tree=UnwrapLayout();tree.feed(''.join(parser.parts))
    return '<section style="font-size:16px;line-height:1.9;color:#303936;word-break:break-word">'+tree.render()+'</section>'


def compact_baoyu(html,source):
    parser=FormatterHTML({f['image'] for f in source['figures']});parser.feed(html)
    content=''.join(parser.parts)
    if not content:raise ValueError('宝玉排版没有生成可用正文。')
    return compact_content(content,source)


def layout_markdown(article,source,options=None):
    from exporting import markdown
    value=dict(article)
    for key in ('title',):
        if options and key in options:value[key]=options[key]
    return markdown(value,source)


def current_baoyu(folder,article,source,options=None):
    from exporting import markdown
    path=Path(folder)/'baoyu-layout.json'
    if not path.is_file():raise ValueError('尚未应用宝玉排版，请先点击“宝玉排版并预览”。')
    saved=json.loads(path.read_text(encoding='utf8'))
    if saved.get('markdown')!=layout_markdown(article,source,options) or saved.get('baoyu_theme','simple')!=(options or {}).get('baoyu_theme','simple'):
        raise ValueError('正文或论文资料已修改，请重新应用宝玉排版后审核。')
    return compact_content(saved['content'],source)
