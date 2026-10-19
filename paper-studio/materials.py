"""Local raster material extraction; candidates never imply complete scientific figures."""
from io import BytesIO
from pathlib import Path
import json
import uuid
import warnings
import pdf_backend as pdf
from PIL import Image, ImageOps
from sources import serialized_pdf, write_json, next_figure_id

MAX_UPLOAD = 20 * 1024 * 1024
MAX_PIXELS = 40_000_000


def normalize_image(data, max_bytes=MAX_UPLOAD):
    if len(data) > max_bytes:
        raise ValueError('图片不能超过 20 MB。')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as im:
                if im.format not in {'PNG','JPEG'} or im.width*im.height > MAX_PIXELS:
                    raise ValueError('仅支持 PNG/JPEG，最多 4000 万像素。')
                im.load()
                im = ImageOps.exif_transpose(im).convert('RGBA' if im.mode in {'RGBA','LA'} or 'transparency' in im.info else 'RGB')
                # Clear EXIF / GPS / text chunks, retaining visual pixels and transparency.
                clean = Image.new(im.mode, im.size); clean.paste(im)
                out = BytesIO(); clean.save(out,format='PNG')
                return out.getvalue(), list(im.size)
    except (OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('无法读取图片，或图片尺寸过大。') from None


def catalog(folder):
    path=Path(folder)/'materials.json'
    return json.loads(path.read_text(encoding='utf8')) if path.exists() else {'items':[],'notes':[]}


@serialized_pdf
def extract_embedded(folder, progress=lambda *_:None):
    folder=Path(folder); target=folder/'materials'; target.mkdir(exist_ok=True)
    items=[]; seen={}; skipped=0; total=0; limited=False
    with pdf.open(folder/'source.pdf') as doc:
        for page in doc:
            progress(f'提取第 {page.number+1}/{len(doc)} 页 PDF 内嵌图片…')
            for info in page.embedded_images():
                xref=info['xref']; key=(xref,0)
                if key in seen:
                    if page.number+1 not in seen[key]['pages']:seen[key]['pages'].append(page.number+1)
                    continue
                if len(items)>=120:limited=True;break
                data=info['data']
                if total+len(data)>200*1024*1024:limited=True;break
                mid=f'pdf-{xref}-{key[1]}'
                name='materials/'+mid+'.png'
                (folder/name).write_bytes(data);total+=len(data)
                item={'id':mid,'image':name,'pages':[page.number+1],'width':info['width'],'height':info['height'],
                      'xref':xref,'smask':key[1],'caption':f'PDF 内嵌图片 · 对象 {xref}', 'origin':'pdf_embedded'}
                items.append(item);seen[key]=item
            if limited:break
    notes=['内嵌图片可能只是子图，图例、箭头和文字可能由 PDF 矢量对象绘制。请对照原页，完整图表优先使用图注裁剪。',
           '图片按原始像素提取，不自动旋转或合并子图；扫描页也可能被提取为整页图片。']
    if skipped:notes.append(f'跳过 {skipped} 个过小、内联、过大或无法解码的图像对象。')
    if limited:notes.append('达到 120 个候选或 200 MB 素材上限，后续页面未继续提取。')
    result={'items':items,'notes':notes};write_json(folder/'materials.json',result);return result


def accept_image(folder, manifest, data, *, replace_id=None, caption='', page=None, origin='local_image', filename='', provenance=None):
    folder=Path(folder)
    old=next((f for f in manifest['figures'] if f['id']==replace_id),None)
    if replace_id and not old:raise ValueError('要替换的配图不存在。')
    if not old and len(manifest['figures'])>=100:raise ValueError('每篇论文最多保留 100 张配图。')
    if page is not None and (type(page) is not int or not 1<=page<=len(manifest['pages'])):raise ValueError('关联页码无效。')
    png,size=normalize_image(data,max_bytes=200*1024*1024 if origin=='pdf_embedded' else MAX_UPLOAD)
    fid=old['id'] if old else next_figure_id(manifest)
    image='images/'+fid+'.png'
    previous=(folder/image)
    # A replaced crop remains recoverable privately; never archive raw upload metadata.
    if previous.exists():
        history=folder/'image-history';history.mkdir(exist_ok=True)
        (history/(fid+'-'+uuid.uuid4().hex+'.png')).write_bytes(previous.read_bytes())
    previous.write_bytes(png)
    figure={'id':fid,'image':image,'caption':str(caption).strip()[:1800] or (old or {}).get('caption','导入配图'),
            'page':page,'kind':'table' if (old or {}).get('kind')=='table' else 'figure','origin':origin,'crop_status':'imported',
            'reviewed':False,'selected':(old or {}).get('selected',False),'pixel_size':size,
            'source_filename':Path(filename).name[:200],'provenance':provenance or {}}
    # Retain the replaced PDF caption anchor for rescan deduplication. These
    # original_* fields describe the earlier crop, not the new upload's evidence.
    if old:
        for key in ('original_page','original_caption','original_bbox'):
            if key in old:figure[key]=old[key]
    if old:manifest['figures'][manifest['figures'].index(old)]=figure
    else:manifest['figures'].append(figure)
    write_json(folder/'source.json',manifest)
    return manifest


def accept_candidate(folder,manifest,body):
    item=next((i for i in catalog(folder)['items'] if i['id']==body.get('id')),None)
    if not item:raise ValueError('素材不存在，请重新扫描。')
    return accept_image(folder,manifest,(Path(folder)/item['image']).read_bytes(),replace_id=body.get('replace_id'),
        caption=body.get('caption') or ('' if body.get('replace_id') else item['caption']),page=item['pages'][0],origin='pdf_embedded',
        provenance={'xref':item['xref'],'smask':item['smask'],'pages':item['pages']})
