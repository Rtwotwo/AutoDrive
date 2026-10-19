"""Local editorial cover composition; never presented as scientific evidence."""
from pathlib import Path
import uuid
from PIL import Image, ImageDraw, ImageFont
from publication import paper_details
from sources import write_json

PALETTES={'ink':('#edf2e8','#153e35','#e66c39'), 'orange':('#fbefe4','#532c22','#dc5426'), 'blue':('#e8eef6','#153354','#3077d4')}


def font(size, bold=False):
    for name in (('msyhbd.ttc' if bold else 'msyh.ttc'), 'simhei.ttf', 'arial.ttf'):
        path=Path('C:/Windows/Fonts')/name
        if path.is_file():return ImageFont.truetype(str(path),size)
    return ImageFont.load_default(size=size)


def wrap(draw,text,face,width):
    lines=[];line=''
    for ch in text:
        if ch=='\n' or (line and draw.textlength(line+ch,font=face)>width):
            lines.append(line);line='' if ch=='\n' else ch
        else:line+=ch
    if line:lines.append(line)
    return lines


def generate_cover(folder,source,article,values):
    title=str(values.get('title') or article.get('title') or source['title']).strip()
    if not title or len(title)>100:raise ValueError('封面标题需为 1–100 字，可单独调整，不影响正文。')
    theme=values.get('theme','ink')
    if theme not in PALETTES:raise ValueError('无效封面主题。')
    label=str(values.get('label') or '论文研读 · Paper Studio').strip()[:50]
    background,foreground,accent=PALETTES[theme]
    info=paper_details(article,source);paper_title=info['title']
    assets=[];folder=Path(folder);(folder/'covers').mkdir(exist_ok=True)
    for width,height,shape in [(1200,510,'横版'),(800,800,'方形')]:
        im=Image.new('RGB',(width,height),background);d=ImageDraw.Draw(im)
        # Geometric decoration belongs to the cover design, not the paper.
        for r in (110,170,230): d.arc((width-r,height-r,width+r,height+r),180,270,fill=accent,width=3)
        margin=64;available=width-margin*2
        d.rounded_rectangle((margin,48,margin+64,55),radius=3,fill=accent)
        d.text((margin,78),label,font=font(22),fill=foreground)
        for size in range(58,23,-2):
            face=font(size,True);lines=wrap(d,title,face,available)
            if len(lines)*(size+18)<height*.46:break
        y=139
        for line in lines:d.text((margin,y),line,font=face,fill=foreground);y+=size+18
        subtitle=wrap(d,paper_title,font(20),available)
        # Complete original title is available in article metadata; cover uses a preview.
        if len(subtitle)>3:subtitle=subtitle[:3];subtitle[-1]=subtitle[-1][:-3]+'…'
        sy=max(y+20,height-145)
        for line in subtitle:d.text((margin,sy),line,font=font(20),fill=foreground);sy+=29
        ident='cover-'+uuid.uuid4().hex[:16];name='covers/'+ident+'.png';im.save(folder/name)
        assets.append({'id':ident,'image':name,'caption':shape+' · '+title,'kind':'designed_cover','title':title,'theme':theme,'width':width,'height':height})
    source.setdefault('covers',[]).extend(assets)
    write_json(folder/'source.json',source)
    return assets
