"""Plan real figure coverage; never invent images or scientific descriptions."""
import re
from pathlib import Path
from PIL import Image

ROLES = {
    'method': r'architecture|framework|pipeline|overview|overall|illustration of.*(?:model|method)|结构|框架',
    'results': r'result|comparison|performance|benchmark|ablation|efficiency|scaling|accuracy|结果|消融',
    'qualitative': r'qualitative|visuali[sz]|rollout|generated (?:samples|images|videos|examples)|generation examples|failure (?:case|example)|case stud|定性|可视化',
}

def roles(figure):
    text=figure.get('original_caption') or figure.get('caption','')
    found=[role for role,pattern in ROLES.items() if re.search(pattern,text,re.I)]
    if figure.get('kind')=='table' and 'results' not in found: found.append('results')
    return found

def usable(figure,folder=None):
    if figure.get('crop_status')=='page_fallback': return False
    if figure.get('origin') in {'local_image','pdf_embedded'} and not figure.get('reviewed'): return False
    if figure.get('animation_note'): return False
    if folder:
        try:
            with Image.open(Path(folder)/figure['image']) as im:
                if im.width<200 or im.height<70: return False
        except (OSError,KeyError): return False
    return True

def build_plan(manifest,folder=None,selected=None):
    candidates=[f for f in manifest.get('figures',[]) if usable(f,folder) and (selected is None or f['id'] in selected)]
    chosen=[]; requirements={}
    for role in ROLES:
        match=next((f for f in candidates if role in roles(f)),None)
        if match:
            requirements[role]=match['id']
            if match not in chosen: chosen.append(match)
    # Do not let early architecture/table figures crowd out later qualitative cases.
    for role in ROLES:
        match=next((f for f in candidates if role in roles(f) and f not in chosen),None)
        if match:chosen.append(match)
    failure=next((f for f in candidates if 'qualitative' in roles(f) and re.search(r'failure|失败',f.get('original_caption') or f.get('caption',''),re.I)),None)
    if failure and failure not in chosen:chosen.append(failure)
    for f in candidates:
        if len(chosen)>=8: break
        if f not in chosen: chosen.append(f)
    return {'ids':[f['id'] for f in chosen], 'required':requirements,
            'available_roles':list(requirements),'missing_source_roles':[r for r in ROLES if r not in requirements],
            'note':'按原图注安排配图；缺少某类图不代表论文没有对应内容。无法确定的裁剪需人工复核。'}

def coverage(article,plan):
    placed={f['id']:f for s in article.get('sections',[]) for f in s.get('figures',[])}
    missing=[f'{role}: {ident}' for role,ident in plan['required'].items()
             if ident not in placed or not placed[ident].get('caption','').strip() or not placed[ident].get('explanation','').strip()]
    if plan['ids'] and not placed: missing.append('正文没有插入任何原图')
    return missing

def adaptive_style(manifest):
    text=manifest.get('title','')+' '+str(manifest.get('abstract',''))
    if re.search(r'benchmark|dataset|evaluation|survey',text,re.I): return 'benchmark','default','blue'
    if re.search(r'serving|cache|kernel|distributed|parallel|inference engine|infra',text,re.I): return 'systems','simple','blue'
    if re.search(r'world|embodied|robot|video|humanoid',text,re.I): return 'world','grace','ink'
    return 'technical','modern','orange'
