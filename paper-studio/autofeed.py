"""Private, bounded discovery → illustrated writing → draft-box delivery.

No scheduler here: a single daily Codex heartbeat invokes the desktop trigger.
The user explicitly authorizes draft delivery and reviews in WeChat afterwards.
"""
from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import copy
import json
import time
from PIL import Image,ImageChops
from feed_sources import TOPICS,discover_recent,verify_resources,stable_id
from figure_plan import build_plan,coverage,adaptive_style,usable
from sources import extract_pdf,write_json,download_arxiv,parse_arxiv
from writing import generate_article,validate_article
from publication import paper_details
from covers import generate_cover
from wechat_review import read_json
from wechat_api import submit_automated_draft
from wechat_fields import adapt_fields, record_adjustments

def today(): return datetime.now(timezone(timedelta(hours=8))).date().isoformat()

def automatic_checks(article,source,folder,resources):
    """Mechanical readiness only; does not certify scientific claims or licensing."""
    audit=validate_article(article,source); problems=[]
    info=paper_details(article,source)
    direct=resources.get('mode')=='user_selected'
    if not direct and resources.get('verified') is not True: problems.append('项目与代码来源未核实')
    required=('title','authors','paper_url') if direct else ('title','authors','affiliations','paper_url','project_url','code_url')
    for key in required:
        if not info.get(key): problems.append('论文资料缺少 '+key)
    for key in (('paper_url',) if direct else ('paper_url','project_url','code_url')):
        if info.get(key)!=resources.get(key): problems.append('成稿链接与已核实来源不一致：'+key)
    page_ids={p['number'] for p in source['pages']}
    for section in article['sections']:
        for p in section['paragraphs']:
            if not p.get('pages') or any(x not in page_ids for x in p['pages']): problems.append('正文缺少可追溯原页'); break
    if not audit['evidence'] or any(not c['quote_found'] for c in audit['evidence']): problems.append('关键结论原文证据未匹配')
    plan=build_plan(source,folder); problems.extend(coverage(article,plan))
    used={f['id'] for s in article['sections'] for f in s.get('figures',[])}
    if len(used)<min(2,len(plan['ids'])) or not used: problems.append('正文配图不足')
    by_id={f['id']:f for f in source['figures']}; pages={p['number']:p for p in source['pages']}
    for fid in used:
        f=by_id[fid]
        if not usable(f,folder): problems.append(fid+' 素材未通过基本检查');continue
        box=f.get('bbox',[]);page=pages.get(f.get('page'),{})
        if len(box)==4 and page.get('width') and (box[2]-box[0])*(box[3]-box[1])/(page['width']*page['height'])>.75:
            problems.append(fid+' 接近整页，需要核对裁剪')
        with Image.open(Path(folder)/f['image']) as im:
            thumb=im.convert('RGB');thumb.thumbnail((256,256))
            mask=ImageChops.difference(thumb,Image.new('RGB',thumb.size,'white')).convert('L')
            ink=sum(n for v,n in enumerate(mask.histogram()) if v>20)/(thumb.width*thumb.height)
            if ink<.01: problems.append(fid+' 图片近乎空白')
    return {'passed':not problems,'problems':list(dict.fromkeys(problems)), 'figure_plan':plan,
            'figures_used':len(used),'evidence_matched':sum(c['quote_found'] for c in audit['evidence']),
            'note':'仅检查资料、证据定位和图文结构；事实、裁剪完整性、图像含义与转载权限仍需在公众号后台审核。'}

class AutoFeed:
    def __init__(self,studio):
        self.studio=studio
        self.root=studio.data_dir.parent/'automation'
        self.root.mkdir(parents=True,exist_ok=True)
        self.config=read_json(self.root/'config.json',{
            'enabled':False,'max_daily':5,'topics':list(TOPICS),'style':'adaptive',
            'model_profile':'','account_appid':'','vision':False,'schedule':'每日 09:00（北京时间，Codex 本地任务）'})
        self.state=read_json(self.root/'state.json',{'items':{},'attempts':{},'message':'尚未检查','last_run':None})
        self.running=False;self.stop_requested=False;self.future=None
        self.finish_current=False;self.mode=''
        self.metadata_pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='arxiv-titles')
        if self.state.get('selected_queue',{}).get('state')=='running':
            self.state['selected_queue']['state']='stopped'
            self.state['message']='上次逐篇队列已中断；确认当前篇回执后可手动继续。'
        for item in self.state['items'].values():
            if item.get('state')=='processing':
                item.update(state='held',message='上次运行中断；检查本地稿与公众号回执后人工继续，不自动重发。')

    def save(self): write_json(self.root/'state.json',self.state)

    def status(self):
        with self.studio.lock:
            return {'config':copy.deepcopy(self.config),'running':self.running,'stop_requested':self.stop_requested,'mode':self.mode,
                    'selected_queue':copy.deepcopy(self.state.get('selected_queue',{})),
                    'today':today(),'today_attempts':self.state['attempts'].get(today(),0),
                    'message':self.state['message'],'last_run':self.state.get('last_run'),
                    'discovery':copy.deepcopy(self.state.get('discovery',{})), 'candidate_count':len(self.state['items']),
                    'items':copy.deepcopy(sorted(self.state['items'].values(),key=lambda x:x.get('published',''),reverse=True))[:1000],
                    'topics':[{'id':k,'label':v[0]} for k,v in TOPICS.items()]}

    def configure(self,body):
        with self.studio.lock:
            if self.running: raise ValueError('自动任务正在运行；请先暂停并等待当前请求结束，再改设置。')
            config=dict(self.config)
            for key in ('enabled','max_daily','topics','style','model_profile','vision'):
                if key in body: config[key]=body[key]
            if type(config['max_daily']) is not int or not 1<=config['max_daily']<=5: raise ValueError('每天最多 1–5 篇。')
            if not isinstance(config['topics'],list) or not config['topics'] or any(x not in TOPICS for x in config['topics']):raise ValueError('请选择有效研究方向。')
            if config['style'] not in {'adaptive','technical','world','systems','benchmark','news','reproduction'}:raise ValueError('无效写作风格。')
            if type(config['enabled']) is not bool or type(config['vision']) is not bool:raise ValueError('无效开关。')
            config['account_appid']=self.studio.wechat.config.get('appid','')
            if config['enabled']:
                self.credentials(config)
            self.config=config;write_json(self.root/'config.json',config)
            return self.status()

    def credentials(self,config=None):
        config=config or self.config
        profile=self.studio.profiles.get(config['model_profile'])
        if not profile or not self.studio.remember_models:raise ValueError('自动运行需要选择已加密保存的写作模型。')
        account=self.studio.wechat
        if not account.config or not account.remember or account.config.get('appid')!=config['account_appid']:
            raise ValueError('请加密保存公众号配置，并重新绑定自动投递目标。')
        return dict(profile)

    def pause(self):
        with self.studio.lock:
            self.stop_requested=True;self.config['enabled']=False
            write_json(self.root/'config.json',self.config)
            self.state['message']='已暂停；等待当前网络请求返回，已发起的草稿创建将保留回执。'
            self.save();return self.status()

    def check_stop(self):
        if self.stop_requested or self.studio.closing: raise ValueError('自动任务已暂停；已保存内容保留。')

    def stop_after_current(self):
        with self.studio.lock:
            self.finish_current=True
            self.message('已设置完成本篇后停止；不会下载或生成下一篇。')
            return self.status()

    def start(self,discover_only=False):
        with self.studio.lock:
            if self.running: return self.status()
            if not discover_only:
                if not self.config['enabled']:raise ValueError('请先启用自动投递。')
                self.credentials()
            self.running=True;self.stop_requested=False;self.finish_current=False;self.mode='discovery' if discover_only else 'batch'
            self.state['message']='等待后台处理…';self.save()
            self.future=(self.metadata_pool if discover_only else self.studio.pool).submit(self._run,discover_only)
            return self.status()

    def known_ids(self):
        result=set()
        for job in self.studio.jobs:
            source=read_json(self.studio.data_dir/job/'source.json',{})
            if source.get('arxiv_id'):
                try:result.add(stable_id(source['arxiv_id']))
                except ValueError:pass
        return result

    def message(self,text):
        with self.studio.lock:
            self.state['message']=text;self.save()

    def selected_job(self,url):
        aid=stable_id(url)
        for job,record in self.studio.jobs.items():
            source=read_json(self.studio.folder(job)/'source.json',{})
            known=source.get('arxiv_id') or record.get('requested_arxiv_id')
            if known and stable_id(known)==aid:
                if record.get('trashed'):raise ValueError('这篇论文已在回收站，请先恢复作品。')
                self.studio.update(job,cancelled=False)
                return job
        candidate=self.state['items'].get(aid,{})
        job=self.studio.create(candidate.get('title') or url)
        self.studio.update(job,requested_arxiv_id=aid)
        return job

    def start_links(self,values):
        if not isinstance(values,list) or not 1<=len(values)<=5:raise ValueError('每次请选择 1–5 篇，按顺序逐篇完成。')
        urls=[];seen=set()
        for value in values:
            aid=parse_arxiv(value);ident=stable_id(aid)
            if ident not in seen:urls.append('https://arxiv.org/abs/'+aid);seen.add(ident)
        with self.studio.lock:
            if self.running or any(j['status'] in {'queued','running'} for j in self.studio.jobs.values()):raise ValueError('请先完成或停止当前处理任务，再开始新队列。')
            profile=dict(self.studio.provider or self.studio.profiles.get(self.studio.active_profile,{}))
            if not profile.get('model'):raise ValueError('请先在模型设置中配置写作模型。')
            if not self.studio.wechat.config:raise ValueError('请先配置目标公众号。')
            job=self.selected_job(urls[0])
            receipt=read_json(self.studio.folder(job)/'wechat-submission.json',{})
            if len(urls)==1 and receipt.get('state') in {'submitted','submitted_unverified','unknown'}:
                return {'id':job,'existing':True,'message':'已有提交记录，已打开本地稿；请核对草稿箱，不会重复创建。'}
            self.running=True;self.stop_requested=False;self.finish_current=False;self.mode='selected'
            self.state['selected_queue']={'urls':urls,'next':0,'completed':[],'state':'running','current_job':job}
            self.studio.update(job,status='queued',operation='direct-draft',message='等待开始单篇图文流程…')
            self.message('按顺序处理所选论文；只下载当前篇，不预下载后续 PDF。')
            self.future=self.studio.pool.submit(self._run_links,urls,job,profile,self.studio.wechat.config['appid'])
            return {'id':job,'count':len(urls),'existing':False}

    def resume_selected(self):
        queue=self.state.get('selected_queue',{})
        return self.start_links(queue.get('urls',[])[queue.get('next',0):])

    def _run_links(self,urls,first,profile,appid):
        queue=self.state['selected_queue']
        try:
            for index,url in enumerate(urls):
                self.check_stop()
                if self.finish_current:break
                job=first if index==0 else self.selected_job(url)
                folder=self.studio.folder(job);queue['current_job']=job;self.save()
                receipt=read_json(folder/'wechat-submission.json',{})
                if receipt.get('state')=='submitted':
                    self.studio.update(job,status='ready',message=receipt.get('message','已有已确认草稿，不重复提交。'))
                    queue['completed'].append(job);queue['next']=index+1;self.save();continue
                if receipt.get('state') in {'unknown','submitted_unverified'}:
                    raise ValueError('当前篇已有待核对的提交记录，请先查看草稿箱；后续队列暂停。')
                self.studio.update(job,status='running',operation='direct-draft')
                def progress(text):
                    self.check_stop()
                    if self.studio.jobs[job].get('cancelled'):raise ValueError('当前篇已请求停止，阶段内容保留。')
                    self.studio.update(job,message=text);self.message(f'当前第 {index+1}/{len(urls)} 篇 · '+text)
                progress('读取当前论文；未下载后续论文。')
                if (folder/'source.json').exists():source=self.studio.load(job)
                else:
                    data,meta=download_arxiv(url,progress);progress('提取当前论文的正文和图表…')
                    source=extract_pdf(data,folder,'paper.pdf',meta,progress)
                    self.studio.update(job,title=source['title'])
                paper_url=source.get('source_url') or url
                source.setdefault('paper_info',{})['paper_url']=paper_url
                write_json(folder/'source.json',source)
                item={'url':paper_url,'resources':{'mode':'user_selected','paper_url':paper_url},'account_appid':appid}
                record=self.finish_article(item,job,source,profile,direct=True,progress=progress)
                self.studio.update(job,status='ready',message=record['message'])
                queue['completed'].append(job);queue['next']=index+1;self.save()
            queue['state']='complete' if queue['next']==len(urls) else 'stopped'
            self.message(f'已完成 {queue["next"]}/{len(urls)} 篇；'+('所选队列完成。' if queue['state']=='complete' else '后续未下载，可手动继续。'))
        except Exception as exc:
            message=str(exc) if isinstance(exc,ValueError) else '本篇未完成；本地材料保留，队列已停止。'
            queue['state']='stopped' if self.stop_requested or self.studio.jobs.get(queue.get('current_job'),{}).get('cancelled') else 'failed'
            if self.studio.jobs.get(queue['current_job'],{}).get('status') in {'queued','running'}:
                self.studio.update(queue['current_job'],status='error',message=message)
            self.message(message+' 后续论文未开始，可调整后继续队列。')
        finally:
            with self.studio.lock:self.running=False;self.mode='';self.save()

    def _run(self,discover_only):
        try:
            self.check_stop();self.message('正在查询最近七天 arXiv 新论文…')
            known=self.known_ids()
            def publish(partial):
                with self.studio.lock:
                    for item in partial['items']:
                        if item['id'] not in self.state['items']:
                            self.state['items'][item['id']]={**item,'state':'existing' if item['id'] in known else 'candidate','message':'已在作品库中' if item['id'] in known else '标题已取得，可直接选择生成草稿'}
                    self.state['discovery']={k:partial[k] for k in ('queries_done','queries_total','checking','cached','checked_at') if k in partial}
                    self.state['discovery_errors']=list(partial.get('errors',[]))
                    done=partial.get('queries_done',0);total=partial.get('queries_total',6)
                    self.state['message']=f'标题检索 {done}/{total}，已取得 {len(partial["items"])} 篇。仅请求 arXiv 元数据，不调用模型。'+(' 使用今日缓存。' if partial.get('cached') else '')
                    self.save()
            found=discover_recent(self.root/'cache',on_update=publish,cancelled=lambda:self.stop_requested or self.studio.closing)
            with self.studio.lock:
                for item in found['items']:
                    if item['id'] not in self.state['items']:
                        self.state['items'][item['id']]={**item,'state':'existing' if item['id'] in known else 'candidate','message':'已在作品库中' if item['id'] in known else '等待核实项目与代码'}
                self.state['discovery_errors']=found['errors'];self.save()
            if discover_only:
                self.message(f'检索完成，找到 {len(found["items"])} 篇相关候选。尚未调用模型或投递。'+(' '.join(found['errors'])))
                return
            profile=self.credentials();day=today();checked=0;delivered=0
            for candidate in found['items']:
                self.check_stop()
                if self.finish_current:break
                if self.state['attempts'].get(today(),0)>=self.config['max_daily']: break
                item=self.state['items'][candidate['id']]
                if item['state'] not in {'candidate','resources_pending'} or item['id'] in known: continue
                if not set(item['topics'])&set(self.config['topics']):continue
                if checked>=20:break
                if item.get('resource_check_day')==today() and not item.get('resources',{}).get('verified'):continue
                checked+=1;self.message(f'标题已找到 {len(found["items"])} 篇；正在核实资源 {checked}/20：'+item['title'])
                try: resources=verify_resources(item,self.root/'downloads',check_cancel=self.check_stop)
                except Exception:resources={'verified':False,'note':'论文或资源页面暂时不可达，等待下次检查。'}
                self.check_stop()
                with self.studio.lock:
                    item.update(resources=resources,resource_check_day=today())
                    if not resources['verified']:item.update(state='resources_pending',message=resources['note'])
                    self.save()
                if not resources['verified']:
                    self.message('当前篇资源未核实，本轮停止。标题已列出，可明确选择论文后直接生成；不会继续下载其他候选。')
                    return
                self.check_stop()
                # Persist reservation before any model call; crashes cannot silently spend twice.
                with self.studio.lock:
                    day=today();self.state['attempts'][day]=self.state['attempts'].get(day,0)+1
                    job=self.studio.create(item['title']);self.studio.update(job,status='running',operation='autofeed',message='自动图文处理中…')
                    item.update(state='processing',job_id=job,attempt_day=day,message='正在生成图文');self.save()
                known.add(item['id'])
                try:
                    record=self.process(item,job,profile)
                    item.update(state=record['state'],message=record['message']);delivered+=1
                    self.studio.update(job,status='ready',message=record['message'])
                except Exception as exc:
                    msg=str(exc) if isinstance(exc,ValueError) else '处理未完成；原文、阶段进度和草稿保留，请手动检查。'
                    receipt=read_json(self.studio.folder(job)/'wechat-submission.json',{})
                    item.update(state=receipt.get('state') if receipt.get('state') in {'unknown','submitted_unverified','submitted'} else 'held',message=msg)
                    self.studio.update(job,status='error',message=msg)
                    self.message(msg+' 本轮停止，后续论文未开始。');self.save();return
                self.save()
            self.message(f'本轮完成，新增投递 {delivered} 篇；今日已尝试 {self.state["attempts"].get(today(),0)}/{self.config["max_daily"]} 篇。无符合条件的新论文时不生成。'+(' '.join(found['errors'])))
        except Exception as exc:
            self.message(str(exc) if isinstance(exc,ValueError) else '自动任务未完成，请检查网络与本地配置。')
        finally:
            with self.studio.lock:
                self.running=False;self.mode='';self.state['last_run']=time.time();self.save()

    def process(self,item,job,profile):
        folder=self.studio.folder(job)
        def cancelled():
            return self.stop_requested or self.studio.closing or self.studio.jobs[job].get('cancelled',False)
        def check_job():
            if cancelled():raise ValueError('此论文自动任务已取消；本地材料与阶段进度保留。')
        def progress(text):
            check_job();self.studio.update(job,message=text);self.message(text)
        source=extract_pdf((self.root/'downloads'/(item['id'].replace('/','_')+'.pdf')).read_bytes(),folder,'paper.pdf',item,progress)
        source['abstract']=item['abstract']
        source['paper_info']={k:item['resources'][k] for k in ('paper_url','project_url','code_url')}
        source['resource_links']=list(dict.fromkeys(source['resource_links']+list(source['paper_info'].values())))
        source['resource_verification']=item['resources'];write_json(folder/'source.json',source)
        return self.finish_article(item,job,source,profile,progress=progress)

    def finish_article(self,item,job,source,profile,direct=False,progress=lambda _:None):
        folder=self.studio.folder(job)
        def cancelled():return self.stop_requested or self.studio.closing or self.studio.jobs[job].get('cancelled',False)
        def check_job():
            if cancelled():raise ValueError('此论文任务已取消；本地材料与阶段进度保留。')
        plan=build_plan(source,folder)
        if not plan['ids']:raise ValueError('未找到可自动使用的完整原图；请在作品库中补图后继续。')
        style,theme,color=adaptive_style(source)
        if not direct and self.config['style']!='adaptive':style=self.config['style']
        if direct and (folder/'article.json').exists():
            progress('沿用已有成稿，检查配图和投递条件…')
            article=self.studio.load(job,'article.json');audit=validate_article(article,source)
        else:
            article,notes,audit=generate_article(source,folder,{**profile,'_desktop':True,'auto_figures':True,
                'length':0,'style':style,'vision':False if direct else self.config['vision']},progress,cancelled)
        self.studio.save_article(job,article)
        write_json(folder/'audit.json',audit)
        check=automatic_checks(article,source,folder,item['resources']);write_json(folder/'automatic-checks.json',check)
        if not check['passed']:raise ValueError('已生成本地稿，待补充后手动审核：'+'；'.join(check['problems']))
        check_job()
        saved=read_json(folder/'wechat-options.json',{})
        options,adjustments=adapt_fields({'title':article['title'],'digest':article.get('digest',''),
            'source_url':item['url'],'theme':'baoyu','baoyu_theme':theme,**saved},article)
        if options.get('cover_id') not in {f['id'] for f in source['figures']+source.get('covers',[])}:
            covers=generate_cover(folder,source,article,{'theme':color,'label':'研究精选 · Paper Studio','title':options['title']})
            options['cover_id']=covers[0]['id']
        record_adjustments(folder,adjustments)
        if adjustments:progress('已自动整理提交标题与摘要，原稿保留；继续排版和投递…')
        write_json(folder/'wechat-options.json',options)
        if options.get('theme')=='baoyu':self.studio.format_skill(job,progress)
        prepared=self.studio.wechat_prepared(job)
        check_job()
        if direct:
            if self.studio.wechat.config.get('appid')!=item['account_appid']:raise ValueError('目标公众号已改变，请重新操作。')
        else:
            self.credentials()
            if not self.config['enabled']:raise ValueError('自动投递已关闭。')
        write_json(folder/'automatic-draft-permit.json',{'mode':'automatic_draft_only','created_at':time.time(),
            'checks_passed':True,'snapshot':prepared,'review_destination':'WeChat draft box; not human reviewed'})
        return submit_automated_draft(folder,prepared,self.studio.wechat,progress)
