"""Official WeChat draft API. Secrets never enter article files or error strings."""
import io,json,re,secrets,time,ipaddress
import urllib.request,urllib.error
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode,urlsplit
from PIL import Image
from model_store import ModelStore
from sources import write_json
from wechat_review import asset_path,read_json,require_approved

APPID=re.compile(r'wx[0-9a-fA-F]{16}')

def whitelist_ip(message):
    """Extract only a validated IP from official 40164 errors, never echo raw errors."""
    match=re.search(r'\binvalid\s+ip\s+([0-9a-fA-F:.]+)(?=[\s,;]|$)',str(message)[:2048],re.I)
    if not match:return ''
    try:
        address=ipaddress.ip_address(match.group(1))
        address=getattr(address,'ipv4_mapped',None) or address
        return str(address) if address.is_global else ''
    except ValueError:return ''

class WechatError(ValueError):
    def __init__(self,code,message=''):
        self.code=int(code)
        self.observed_ip=whitelist_ip(message) if self.code==40164 else ''
        hints={40001:'AppSecret 无效，请在本机重新填写。',40013:'AppID 无效。',40125:'AppSecret 无效。',40164:'当前出口 IP 不在白名单。请在微信开发平台配置本机网络的公网出口 IP；软件不会代改白名单。',48001:'账号没有该接口权限，请到微信开发平台的接口管理中检查。',48002:'账号接口权限被限制。',45009:'微信接口调用次数已达限制，请稍后再试。',40007:'封面素材 ID 无效。',40009:'图片大小不符合微信要求。',40005:'图片格式不符合微信要求。',42001:'访问凭证过期，请重新检测连接。',40014:'访问凭证无效，请重新检测连接。',45003:'标题超过微信限制。',45004:'正文超过微信限制。',45005:'阅读原文链接超过微信限制。',45006:'摘要超过微信限制。'}
        hints.update({89503:'此次 API 调用需要管理员在微信中确认，请完成确认后再检测连接。',89506:'该 IP 调用已被管理员拒绝，请按微信提示等待后重试。',89507:'该 IP 调用已被管理员拒绝，请按微信提示等待后重试。'})
        if self.code==40164:
            address=f'微信本次识别的公网出口 IP：{self.observed_ip}。' if self.observed_ip else '微信未返回可识别的公网出口 IP。'
            hints[40164]=address+'请核对当前公众号的“API IP 白名单”，添加该出口地址并保存后再检测连接。不要填 127.0.0.1、192.168.x.x 或网页域名。软件直连微信，不使用系统 HTTP 代理；VPN/TUN、换网或宽带重拨仍可能改变出口。'
        super().__init__(f'微信返回错误 {self.code}：'+hints.get(self.code,'请求未被接受，请在微信开发平台诊断此错误码。'))

class TransportError(ValueError):pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def transport(path,token='',payload=None,file=None):
    if path not in {'stable_token','draft/count','draft/add','draft/get','media/uploadimg','material/add_material'}:
        raise ValueError('不支持的微信接口。')
    params={}
    if token:params['access_token']=token
    if path=='material/add_material':params['type']='image'
    url='https://api.weixin.qq.com/cgi-bin/'+path+('?' + urlencode(params) if params else '')
    headers={'User-Agent':'PaperStudio/1.0'}
    data=None
    if file:
        name,mime,blob=file;boundary='PaperStudio'+secrets.token_hex(16)
        data=(f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n').encode()+blob+f'\r\n--{boundary}--\r\n'.encode()
        headers['Content-Type']='multipart/form-data; boundary='+boundary
    elif payload is not None:
        data=json.dumps(payload,ensure_ascii=False).encode();headers['Content-Type']='application/json; charset=utf-8'
    req=urllib.request.Request(url,data=data,headers=headers)
    # Credentials go only to the fixed official host. Do not inherit proxy settings.
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    try:
        with opener.open(req,timeout=45) as response:
            raw=response.read(2_000_001)
            if len(raw)>2_000_000:raise TransportError('微信响应超过本地限制，请检查草稿箱后再操作。')
            result=json.loads(raw)
        if not isinstance(result,dict):raise ValueError()
    except TransportError:raise
    except Exception:raise TransportError('微信请求超时或连接中断；如已提交草稿，请先检查后台，不要重复提交。') from None
    if result.get('errcode'):raise WechatError(result['errcode'],result.get('errmsg',''))
    return result


class Account:
    def __init__(self,path=None,request=transport):
        self.store=ModelStore(path) if path else None;self.request=request
        self.config={};self.remember=False;self.warning='';self.token='';self.expires=0;self.checked=None
        if self.store:
            try:
                value=self.store.load()
                if value:self.config=self.validate(value.get('account',{}));self.remember=True
            except (ValueError,OSError):self.warning='公众号加密配置无法读取，请重新填写；原文件保留。'
    @staticmethod
    def validate(value):
        result={k:str(value.get(k,'')).strip() for k in ('appid','secret','name')}
        if not APPID.fullmatch(result['appid']):raise ValueError('请填写有效的公众号 AppID（wx 开头）。')
        if not 16<=len(result['secret'])<=128 or not re.fullmatch(r'[A-Za-z0-9_-]+',result['secret']):
            raise ValueError('请填写微信平台提供的 AppSecret。')
        if len(result['name'])>80:raise ValueError('公众号名称过长。')
        return result
    def save(self,body):
        if body.get('clear'):
            if self.store:self.store.clear()
            self.config={};self.remember=False
        else:
            values=dict(body)
            if not values.get('secret') and values.get('appid')==self.config.get('appid'):values['secret']=self.config.get('secret','')
            config=self.validate(values);remember=body.get('remember') is True
            if remember:
                if not self.store:raise ValueError('请使用桌面版加密保存公众号配置。')
                self.store.save({'version':1,'account':config})
            elif self.store:self.store.clear()
            self.config=config;self.remember=remember
        self.warning='';self.token='';self.expires=0;self.checked=None
    def public(self):
        return {'configured':bool(self.config),'appid':self.config.get('appid',''),'name':self.config.get('name',''),
                'remember':self.remember,'warning':self.warning,'check':self.checked}
    def get_token(self):
        if not self.config:raise ValueError('请先在公众号设置中填写 AppID 与 AppSecret。')
        if not self.token or time.time()>=self.expires:
            r=self.request('stable_token',payload={'grant_type':'client_credential','appid':self.config['appid'],'secret':self.config['secret'],'force_refresh':False})
            token=r.get('access_token');ttl=r.get('expires_in')
            if not isinstance(token,str) or not token or len(token)>4096 or type(ttl) not in (int,float):raise TransportError('微信未返回有效访问凭证，请重新检测连接。')
            self.token=token;self.expires=time.time()+max(0,ttl-120)
        return self.token
    def call(self,path,*,check_cancel=lambda:None,before_send=lambda:None,**kwargs):
        try:
            check_cancel()
            token=self.get_token()
            check_cancel()
            before_send()
            return self.request(path,token=token,**kwargs)
        except WechatError as e:
            if e.code in (40014,42001):self.token='';self.expires=0
            raise
    def check(self):
        try:
            r=self.call('draft/count')
            if type(r.get('total_count')) is not int:raise TransportError('微信没有返回有效草稿数量。')
        except (WechatError,TransportError) as error:
            self.checked={'time':time.time(),'draft_read':False,'message':str(error),
                          'code':getattr(error,'code',None),'observed_ip':getattr(error,'observed_ip','')}
            raise
        self.checked={'time':time.time(),'draft_read':True,'message':'已连接并可读取草稿数量。写入图片和草稿的权限仍以实际提交结果为准。'}
        return self.public()
    def close(self):self.config.clear();self.token='';self.expires=0


def image_file(path,limit=1_000_000):
    raw=path.read_bytes()
    if len(raw)<limit:return path.name,'image/png',raw
    with Image.open(io.BytesIO(raw)) as im:
        if im.width*im.height>25_000_000:raise ValueError('图片像素过大，请先在配图页重新裁剪。')
        image=im.convert('RGB')
        for quality in (94,88,82,76):
            buf=io.BytesIO();image.save(buf,'JPEG',quality=quality,optimize=True)
            if len(buf.getvalue())<limit:return path.stem+'.jpg','image/jpeg',buf.getvalue()
    raise ValueError('图片保持原尺寸后仍超过微信 1 MB 限制，请重新裁剪或压缩后再审核。')


def verify_image_url(url):
    p=urlsplit(str(url));host=p.hostname or ''
    if p.scheme not in ('http','https') or p.username or p.password or p.port not in (None,80,443) or not (host=='mmbiz.qpic.cn' or host.endswith('.qpic.cn') or host=='mmbiz.qlogo.cn'):
        raise TransportError('微信未返回受支持的图片地址。')
    return str(url)


class Contents(HTMLParser):
    def __init__(self,s):
        super().__init__(convert_charrefs=True);self.text=[];self.images=[];self.feed(s)
    def handle_data(self,t):self.text.append(t)
    def handle_starttag(self,t,attrs):
        if t=='img':
            value=dict(attrs).get('src') or dict(attrs).get('data-src') or ''
            self.images.append(re.sub(r'^https?:','',value))
    def plain(self):return ''.join(''.join(self.text).split())


def verify_draft(account,record,check_cancel=lambda:None):
    r=account.call('draft/get',payload={'media_id':record['media_id']},check_cancel=check_cancel)
    items=r.get('news_item',[])
    if not isinstance(items,list) or not items:raise ValueError('草稿已提交，但读回内容为空；请到公众号后台检查。')
    item=items[0];expected=record['payload'];actual=Contents(str(item.get('content','')));want=Contents(expected['content'])
    fields=('title','author','digest','content_source_url','thumb_media_id')
    if any(item.get(k,'')!=expected.get(k,'') for k in fields) or actual.plain()!=want.plain() or actual.images!=want.images:
        raise ValueError('草稿已提交，但读回资料、正文或图片与提交稿不完全一致。请在公众号后台检查；不会自动重发。')
    record.update(state='submitted',verified_at=time.time(),message='已提交公众号草稿箱并读回核对资料、正文文字、图片地址和封面。排版与正文外链仍请手机预览确认；尚未公开发表或群发。')
    return record


def submit_draft(folder,prepared,account,progress=lambda x:None):
    folder=Path(folder);require_approved(folder,prepared)
    return _submit_payload(folder,prepared,account,progress)


def submit_automated_draft(folder,prepared,account,progress=lambda x:None):
    """Separate draft-only authority. Never marks a draft as human reviewed."""
    folder=Path(folder)
    permit=read_json(folder/'automatic-draft-permit.json',{})
    if (permit.get('mode')!='automatic_draft_only' or permit.get('checks_passed') is not True
            or permit.get('snapshot')!=prepared or time.time()-permit.get('created_at',0)>3600):
        raise ValueError('自动投递授权不存在、已过期或稿件已变更。请重新运行检查或走人工审核。')
    return _submit_payload(folder,prepared,account,progress)


def _submit_payload(folder,prepared,account,progress):
    if prepared['account']['appid']!=account.config.get('appid'):raise ValueError('目标公众号已改变，请重新审核。')
    state_path=folder/'wechat-submission.json';old=read_json(state_path,{})
    if old.get('state') in {'submitted','submitted_unverified','unknown'}:
        raise ValueError('已有提交记录。请先查看公众号草稿箱，或使用“重新核对草稿”；不会重复创建。')
    record={'state':'uploading','started_at':time.time(),'account':prepared['account'],'message':'准备上传图片。'}
    write_json(state_path,record)
    try:
        # Prepare every image before remote changes, so over-limit images fail early.
        files={x['id']:image_file(asset_path(folder,x['image'])) for x in prepared['assets']}
        content=prepared['content'];index={x['id']:x for x in prepared['assets']}
        for i,ident in enumerate(prepared['inline_ids'],1):
            progress(f'上传正文图片 {i}/{len(prepared["inline_ids"])}…')
            url=verify_image_url(account.call('media/uploadimg',file=files[ident],check_cancel=lambda:progress(f'上传正文图片 {i}/{len(prepared["inline_ids"])}…')).get('url'))
            content=content.replace('src="'+escape(index[ident]['image'],quote=True)+'"','src="'+escape(url,quote=True)+'"')
        progress('上传封面…')
        cover=account.call('material/add_material',file=files[prepared['options']['cover_id']],check_cancel=lambda:progress('上传封面…')).get('media_id')
        if not isinstance(cover,str) or not cover or len(cover)>256:raise TransportError('微信未返回有效封面素材 ID。')
        if len(content)>=20000 or len(content.encode())>=1_000_000:raise ValueError('替换微信图片链接后正文超过 20,000 字符，请精简文章后重新审核。')
        o=prepared['options'];payload={'article_type':'news','title':o['title'],'author':o['author'],'digest':o['digest'],
            'content':content,'content_source_url':o['source_url'],'thumb_media_id':cover,'need_open_comment':0,'only_fans_can_comment':0}
        # Before the only create call, persist uncertainty. Timeout/crash must not resend.
        def mark_creating():
            record.update(state='unknown',payload=payload,message='已发起创建草稿；结果尚未确认，请勿重复提交。');write_json(state_path,record)
        progress('创建公众号草稿…')
        response=account.call('draft/add',payload={'articles':[payload]},check_cancel=lambda:progress('创建公众号草稿…'),before_send=mark_creating);media=response.get('media_id')
        if not isinstance(media,str) or not media or len(media)>256:raise TransportError('微信没有返回有效草稿 ID；请先检查公众号草稿箱。')
        record.update(state='submitted_unverified',media_id=media,message='草稿已创建，正在读回核对。');write_json(state_path,record)
        progress('读回核对标题、正文、图片和封面…')
        verify_draft(account,record,check_cancel=lambda:progress('读回核对标题、正文、图片和封面…'));write_json(state_path,record)
        return record
    except Exception as exc:
        if record['state']=='uploading' or (record['state']=='unknown' and isinstance(exc,WechatError)):
            record['state']='failed'
        record['message']=str(exc) if isinstance(exc,ValueError) else '提交未完成，请检查公众号草稿箱后重试。'
        write_json(state_path,record)
        raise ValueError(record['message']) from None


def recheck(folder,account):
    path=Path(folder)/'wechat-submission.json';record=read_json(path,{})
    if not record.get('media_id'):raise ValueError('没有已知草稿 ID，请先到公众号后台检查是否创建成功。')
    if record.get('account',{}).get('appid')!=account.config.get('appid'):raise ValueError('请切换回原提交公众号后核对。')
    try:verify_draft(account,record)
    except Exception as exc:
        record.update(state='submitted_unverified',message=str(exc) if isinstance(exc,ValueError) else '读回未完成，请在公众号后台检查。')
        write_json(path,record)
        raise ValueError(record['message']) from None
    write_json(path,record);return record


def reset_submission(folder,confirmed):
    if confirmed is not True:raise ValueError('请先确认已经检查公众号草稿箱；再次提交可能产生新草稿。')
    path=Path(folder)/'wechat-submission.json';old=read_json(path,{})
    if old:
        archive=Path(folder)/'history';archive.mkdir(exist_ok=True)
        write_json(archive/('wechat-submission-'+secrets.token_hex(8)+'.json'),old)
    write_json(path,{'state':'ready','message':'已由用户确认开始下一次提交；原公众号草稿未删除。'})
