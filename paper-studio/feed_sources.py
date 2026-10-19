"""Bounded official arXiv discovery and evidence-based author resource lookup."""
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
import base64
import json
import re
import time
from urllib.parse import urlencode, urljoin, urlsplit, quote, unquote
import xml.etree.ElementTree as ET
from pathlib import Path
from sources import fetch_arxiv_bytes, parse_arxiv, write_json, MAX_BYTES
from project_media import fetch_public

TOPICS = {
    'driving': ('自动驾驶', r'autonomous driving|self.driving|end.to.end driving'),
    'world': ('世界模型', r'world model|world simulator|video generation.*action'),
    'embodied': ('具身智能', r'embodied|vision.language.action|robot learning|robotic manipulation|humanoid'),
    'infra': ('AI Infra', r'llm serving|inference engine|kv.cache|distributed training|model parallel|speculative decoding|gpu kernel|attention kernel'),
    'foundation': ('基础大模型', r'large language model|foundation model|reasoning model|multimodal language|test.time scaling|recursive self.improvement'),
    'agents': ('Agent 方法', r'(?:llm|language.model|reasoning|autonomous|multi)[ -]agents?|agentic|tool.use|tool.calling|agent planning'),
    'rsi': ('RSI · 递归自我改进', r'recursive self.improv|self.improving (?:agent|model|system)|self.evolving (?:agent|model)|self.refin(?:e|ement)|self.training.*(?:agent|language model)'),
}
QUERIES = [
    'ti:"autonomous driving" OR abs:"world model" OR ti:"self-driving"',
    'ti:"embodied" OR abs:"vision-language-action" OR ti:"robot learning" OR ti:"humanoid"',
    'ti:"LLM serving" OR ti:"KV cache" OR ti:"distributed training" OR ti:"speculative decoding" OR ti:"GPU kernel"',
    'ti:"large language model" OR ti:"foundation model" OR ti:"reasoning model" OR ti:"test-time scaling"',
    'ti:"agentic" OR ti:"LLM agent" OR ti:"multi-agent" OR ti:"tool use" OR ti:"agent planning"',
    'abs:"recursive self-improvement" OR ti:"self-improving" OR ti:"self-evolving" OR ti:"self-refinement"',
]
NS = '{http://www.w3.org/2005/Atom}'

def stable_id(value):
    return re.sub(r'v\d+$', '', parse_arxiv(value.replace('http://arxiv.org/', 'https://arxiv.org/')))

def topic_labels(title, abstract):
    text = title + ' ' + abstract
    result=[key for key, (_, pattern) in TOPICS.items() if re.search(pattern, text, re.I)]
    if 'foundation' in result and not re.search(r'pre.train|post.train|training|reasoning|architect|transformer|scal|alignment|tokeniz|foundation|generalist|recursive|self.improv|language model.*(?:learn|general)',title,re.I):
        result.remove('foundation')
    return result

def parse_feed(raw, now=None):
    now = now or datetime.now(timezone.utc)
    root = ET.fromstring(raw)
    records = []
    for e in root.findall(NS+'entry'):
        try:
            aid = stable_id(e.findtext(NS+'id', ''))
            published = e.findtext(NS+'published', '')
            date = datetime.fromisoformat(published.replace('Z','+00:00'))
        except (ValueError, TypeError):
            continue
        if not now-timedelta(days=7) <= date <= now+timedelta(minutes=5): continue
        title = ' '.join(e.findtext(NS+'title', '').split())
        abstract = ' '.join(e.findtext(NS+'summary', '').split())
        topics = topic_labels(title, abstract)
        if not topics: continue
        records.append({'id':aid, 'arxiv_id':aid, 'title':title, 'abstract':abstract,
                        'authors':[a.findtext(NS+'name','') for a in e.findall(NS+'author')],
                        'published':published, 'topics':topics, 'url':'https://arxiv.org/abs/'+aid})
    return records

def fetch_titles(url,limit):
    return fetch_arxiv_bytes(url,limit,timeout=15,attempts=1)

def discover_recent(cache_dir, now=None, fetch=fetch_titles, sleep=time.sleep, on_update=lambda _:None, cancelled=lambda:False):
    now = now or datetime.now(timezone.utc)
    cache_dir = Path(cache_dir); cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir/('arxiv-'+now.date().isoformat()+'.json')
    if path.exists():
        cached=json.loads(path.read_text(encoding='utf-8'))
        if cached.get('queries')==QUERIES:
            on_update(dict(cached,cached=True,queries_done=len(QUERIES),queries_total=len(QUERIES)))
            return cached
    records = {}; errors = []
    for index, query in enumerate(QUERIES):
        if cancelled():raise ValueError('论文检索已暂停；已取得的标题和链接保留。')
        on_update({'items':list(records.values()),'errors':errors,'queries_done':index,'queries_total':len(QUERIES),'checking':index+1})
        if index: sleep(3.1)
        if cancelled():raise ValueError('论文检索已暂停；已取得的标题和链接保留。')
        url = 'https://export.arxiv.org/api/query?'+urlencode({
            'search_query':query,'start':0,'max_results':100,'sortBy':'submittedDate','sortOrder':'descending'})
        try:
            for item in parse_feed(fetch(url, 4_000_000), now): records[item['id']] = item
        except Exception:
            errors.append('arXiv 查询 '+str(index+1)+' 暂时失败。')
        on_update({'items':list(records.values()),'errors':errors,'queries_done':index+1,'queries_total':len(QUERIES)})
        if cancelled():raise ValueError('论文检索已暂停；已取得的标题和链接保留。')
    result = {'items':sorted(records.values(),key=lambda x:x['published'],reverse=True),
              'errors':errors,'queries':QUERIES,'checked_at':now.isoformat(), 'coverage':f'最近七天；{len(QUERIES)} 组官方查询，每组最多 100 条，不代表穷尽全部研究。'}
    # A partial outage must not become a permanent successful no-new result.
    if not errors: write_json(path,result)
    if len(errors)==len(QUERIES): raise ValueError('arXiv 暂时不可达；本轮未生成文章，下次可重试。')
    return result

class Links(HTMLParser):
    def __init__(self, html, url):
        super().__init__(); self.links=[]; self.words=[]; self.url=url; self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag=='a':
            href=urljoin(self.url,dict(attrs).get('href',''))
            if href.startswith('https://') and href not in self.links: self.links.append(href)
    def handle_data(self,text): self.words.append(text)

class RepositoryPage(Links):
    def __init__(self,html,url):
        self.in_article=False;self.readme=[];self.readme_links=[]
        self.in_payload=False;self.payload_text=[];self.payloads=[]
        super().__init__(html,url)
    def handle_starttag(self,tag,attrs):
        super().handle_starttag(tag,attrs)
        if tag=='article':self.in_article=True
        a=dict(attrs)
        if tag=='a' and self.in_article:
            self.readme_links.append(urljoin(self.url,a.get('href','')))
        if tag=='script' and a.get('type')=='application/json' and a.get('data-target')=='react-app.embeddedData':
            self.in_payload=True;self.payload_text=[]
    def handle_endtag(self,tag):
        if tag=='article':self.in_article=False
        if tag=='script' and self.in_payload:
            try:self.payloads.append(json.loads(''.join(self.payload_text)))
            except ValueError:pass
            self.in_payload=False
    def handle_data(self,text):
        if self.in_article:self.readme.append(text)
        if self.in_payload:self.payload_text.append(text)
        super().handle_data(text)

def web_repository(repo,fetch,url=None):
    url=url or 'https://github.com/'+repo
    raw,mime,final=fetch(url,3_000_000)
    if 'html' not in mime:raise ValueError('代码仓库网页不是 HTML。')
    if urlsplit(final).hostname!='github.com' or not urlsplit(final).path.startswith('/'+repo):
        raise ValueError('代码仓库网页跳转到了其他来源。')
    page=RepositoryPage(raw.decode('utf8',errors='replace'),final)
    entries=[]
    for payload in page.payloads:
        route=payload.get('payload',{}).get('codeViewRepoRoute',{})
        directory=str(route.get('path','')).strip('/')
        ref=str(route.get('refInfo',{}).get('name',''))
        expected='/'+repo+('/tree/'+ref+'/'+directory if directory else '')
        if not ref or unquote(urlsplit(final).path).rstrip('/')!=expected:continue
        for entry in route.get('tree',{}).get('items',[]):
            path=str(entry.get('path',''));name=str(entry.get('name',''))
            # Only immediate directory entries count. README links are not a file listing.
            if not name or name in {'.','..'} or '/' in name or '\\' in name:continue
            if path!=(directory+'/' if directory else '')+name:continue
            kind=entry.get('contentType')
            if kind not in {'file','directory'}:continue
            entries.append({'name':name,'type':'file' if kind=='file' else 'dir',
                            'web_url':'https://github.com/'+repo+('/blob/' if kind=='file' else '/tree/')+quote(ref,safe='')+'/'+quote(path,safe='/')})
    # Only rendered README text and its links establish paper identity, never global page links.
    readme=' '.join(page.readme)+'\n'+'\n'.join(page.readme_links)
    return readme,entries

def repository_record(repo,fetch):
    try:
        raw,_,_=fetch('https://api.github.com/repos/'+repo+'/readme',2_000_000)
        record=json.loads(raw);readme=base64.b64decode(record.get('content','')).decode('utf8',errors='replace')
        raw,_,_=fetch('https://api.github.com/repos/'+repo+'/contents',2_000_000)
        entries=json.loads(raw)
        if not isinstance(entries,list):raise ValueError('仓库目录不可读。')
        return readme,entries
    except (ValueError,KeyError,TypeError):
        return web_repository(repo,fetch)

def identity_match(text,item):
    normalized = re.sub(r'\W+','',text).lower()
    title = re.sub(r'\W+','',item['title']).lower()
    return item['id'] in text or (len(title)>=12 and title in normalized)

def github_repo(url):
    p=urlsplit(url)
    bits=p.path.strip('/').split('/')
    if p.scheme=='https' and p.hostname in {'github.com','www.github.com'} and len(bits)>=2:
        if all(re.fullmatch(r'[A-Za-z0-9_.-]+',b) for b in bits[:2]): return '/'.join(bits[:2]).removesuffix('.git')
    return ''

def verify_resources(item, spool, fetch=fetch_public, arxiv_fetch=fetch_arxiv_bytes, check_cancel=lambda:None):
    """Only author-linked code + cross-identified project pages become eligible.

    GitHub search is a fallback candidate finder, never proof of authorship.
    An exact paper ID/title in a README plus a paper-author link is required.
    """
    supplied=fetch
    def fetch(url,limit):
        check_cancel();result=supplied(url,limit);check_cancel();return result
    check_cancel()
    spool=Path(spool); spool.mkdir(parents=True,exist_ok=True)
    pdf_path=spool/(item['id'].replace('/','_')+'.pdf')
    if not pdf_path.exists():
        kwargs={'check_cancel':check_cancel} if arxiv_fetch is fetch_arxiv_bytes else {}
        raw=arxiv_fetch('https://arxiv.org/pdf/'+item['id'],MAX_BYTES,**kwargs)
        check_cancel();pdf_path.write_bytes(raw)
    import pdf_backend as pdf
    author_links=[]
    with pdf.open(pdf_path) as doc:
        # References at the end are not declarations of author resources.
        for page in list(doc)[:2]:
            author_links.extend(l.get('uri','') for l in page.get_links())
            author_links.extend(re.findall(r'https://[^\s<>\[\]{}]+',page.get_text()))
    author_links=list(dict.fromkeys(u.rstrip('.,);') for u in author_links if u.startswith('https://')))[:40]
    candidates=list(author_links); evidence=[]; projects=[]; repositories=[]
    for url in author_links:
        repo=github_repo(url)
        if repo: repositories.append((repo,True))
    # Only visit author-linked pages, bounded to avoid crawling a bibliography.
    for url in author_links[:10]:
        host=urlsplit(url).hostname or ''
        if github_repo(url) or host.endswith(('arxiv.org','doi.org','openreview.net','youtube.com')): continue
        if len(projects)>=4: break
        try:
            raw,mime,final=fetch(url,2_000_000)
            if 'html' not in mime: continue
            parsed=Links(raw.decode('utf8',errors='replace'),final)
            if not identity_match(' '.join(parsed.words)+' '+' '.join(parsed.links),item): continue
            projects.append((final,parsed))
            for link in parsed.links:
                repo=github_repo(link)
                if repo: repositories.append((repo,True))
        except ValueError: continue
    if not repositories:
        # Search is discovery only; an unlinked mirror cannot qualify automatically.
        try:
            raw,_,_=fetch('https://api.github.com/search/repositories?'+urlencode({'q':'"'+item['title'][:100]+'"','per_page':3}),1_000_000)
            repositories.extend((r['full_name'],False) for r in json.loads(raw).get('items',[])[:3])
        except (ValueError,KeyError): pass
    for repo,author_linked in list(dict.fromkeys(repositories))[:5]:
        try:
            readme,tree=repository_record(repo,fetch)
            if not identity_match(readme,item): continue
            # A searched repo can qualify only if the verified project links back to it.
            if not author_linked: continue
            def has_code(entries):
                return any(x.get('type')=='file' and re.search(r'\.(py|cpp|cu|c|rs|jl|ipynb|sh)$',str(x.get('name','')),re.I) for x in entries)
            code=has_code(tree)
            if not code:
                dirs=[x for x in tree if x.get('type')=='dir' and x.get('name','').lower() in {'src','code','models','model','training','inference','scripts','lib',repo.split('/')[-1].lower()}][:2]
                for entry in dirs:
                    if entry.get('web_url'):
                        _,children=web_repository(repo,fetch,entry['web_url'])
                    else:
                        data,_,_=fetch('https://api.github.com/repos/'+repo+'/contents/'+entry['name'],2_000_000)
                        children=json.loads(data)
                    if isinstance(children,list) and has_code(children):code=True;break
            if not code: continue
            # README project links are checked for paper identity, not assumed from spelling.
            if not projects:
                checked_links=0
                for link in re.findall(r'https://[^\s<>"\)\]]+',readme)[:40]:
                    if github_repo(link) or (urlsplit(link).hostname or '').endswith(('arxiv.org','shields.io','youtube.com')): continue
                    if re.search(r'\.(png|jpg|svg|gif|pdf)(?:\?|$)',link,re.I):continue
                    if checked_links>=6:break
                    checked_links+=1
                    try:
                        data,mime,final=fetch(link,2_000_000)
                        if 'html' not in mime: continue
                        p=Links(data.decode('utf8',errors='replace'),final)
                        if identity_match(' '.join(p.words)+' '+' '.join(p.links),item): projects.append((final,p)); break
                    except ValueError: continue
            if not projects: continue
            project=projects[0][0]
            evidence=['PDF 首页链接或已核实项目页链接到代码仓库','仓库 README 含论文 ID 或完整标题','仓库根目录包含代码文件或实现目录','项目页含论文 ID 或完整标题']
            return {'verified':True,'code_url':'https://github.com/'+repo,'project_url':project,
                    'paper_url':item['url'],'evidence':evidence,'checked_at':time.time(),
                    'note':'检测到公开实现文件，不代表已复现、完整发布或特定开源许可。'}
        except (ValueError,KeyError,TypeError): continue
    return {'verified':False,'evidence':evidence,'checked_at':time.time(),
            'note':'尚未同时核实作者项目主页与已发布实现；保留候选，不调用写作模型。'}
