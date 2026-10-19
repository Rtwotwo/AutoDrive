"""Prefer complete single-image figures from official arXiv HTML over PDF crops."""
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
import io,re,shutil,uuid
from pathlib import Path
from PIL import Image,ImageOps
from sources import parse_arxiv,fetch_arxiv_bytes,write_json

class Figures(HTMLParser):
    def __init__(self,html):
        super().__init__();self.items=[];self.current=None;self.depth=0;self.feed(html)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='figure':
            if self.current is None:self.current={'images':[],'text':[]};self.depth=1
            else:self.depth+=1
        if self.current is not None and tag=='img' and a.get('src'):self.current['images'].append(a['src'])
    def handle_data(self,text):
        if self.current is not None:self.current['text'].append(text)
    def handle_endtag(self,tag):
        if tag=='figure' and self.current is not None:
            self.depth-=1
            if self.depth==0:self.items.append(self.current);self.current=None

def label(text):
    m=re.search(r'\b(?:Figure|Fig\.)\s*(\d+)\b',text,re.I)
    return m.group(1) if m else ''

def improve_native_figures(source,folder,progress=lambda x:None,fetch=None):
    if not source.get('arxiv_id') or source.get('native_figures_checked'):return source
    folder=Path(folder)
    def check():progress('正在读取当前论文原图；停止后不会请求下一张素材。')
    supplied=fetch
    def fetch(url,limit):
        check()
        raw=supplied(url,limit) if supplied else fetch_arxiv_bytes(url,limit,check_cancel=check)
        check()
        return raw
    try:
        aid=parse_arxiv(source['arxiv_id']);base='https://arxiv.org/html/'+aid
        progress('尝试读取 arXiv HTML 原始图像，减少 PDF 截图空白与裁切…')
        html=fetch(base,8_000_000).decode('utf8',errors='replace');items=Figures(html).items
        replaced=[]
        for item in items:
            if len(replaced)>=12:break
            # Multiple panels require layout knowledge: retain the PDF composition.
            if len(item['images'])!=1:continue
            number=label(' '.join(item['text']))
            if not number:continue
            matches=[f for f in source['figures'] if label(f.get('original_caption') or f.get('caption',''))==number and not f.get('reviewed') and not f.get('origin')]
            if len(matches)!=1:continue
            f=matches[0];url=urljoin(base+'/',item['images'][0]);p=urlsplit(url)
            if p.scheme!='https' or p.hostname!='arxiv.org' or p.username or p.password:continue
            try:
                raw=fetch(url,20_000_000)
                with Image.open(io.BytesIO(raw)) as im:
                    if im.width*im.height>25_000_000 or im.width<200 or im.height<70 or getattr(im,'is_animated',False):continue
                    image=ImageOps.exif_transpose(im).convert('RGB')
                    # Preserve the old PDF render for manual comparison/recovery.
                    history=folder/'image-history';history.mkdir(exist_ok=True)
                    shutil.copyfile(folder/f['image'],history/(f['id']+'-'+uuid.uuid4().hex+'.png'))
                    image.save(folder/f['image'])
                f.update(origin='arxiv_html',source_url=url,bbox=[],crop_status='arxiv_original',selected=True)
                replaced.append(f['id'])
            except (ValueError,OSError):continue
        source['native_figures_checked']={'replaced':replaced,'note':'仅替换与 PDF 图号唯一对应的单图素材；多面板保留 PDF 布局。原始 PDF 裁图保存在 image-history。'}
        write_json(folder/'source.json',source)
    except Exception:
        # HTML is optional; retain existing figure source and retry on a later generation.
        pass
    check()
    return source
