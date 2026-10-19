"""Reader-facing article conventions; evidence remains in the structured draft."""
import copy
import re
from urllib.parse import urlsplit


def resource_url(value):
    if not isinstance(value, str) or len(value) > 2000 or re.search(r'[\s<>"\x00-\x1f]', value):
        return ''
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in {'https', 'http'} and parsed.hostname and not parsed.username and not parsed.password else ''
    except ValueError:
        return ''


def clean_public_text(value):
    # Strip only a trailing leaked schema annotation, not ordinary bracketed numbers.
    return re.sub(r'(?:\s*[（(]?(?:pages?|页码)\s*[:：]\s*\[\s*\d+(?:\s*[,，-]\s*\d+)*\s*\][）)]?[.。]?)+\s*$',
                  '', str(value), flags=re.I).strip()


def clean_article(article):
    result = copy.deepcopy(article)
    for key in ('title', 'digest', 'lead'):
        if isinstance(result.get(key), str): result[key] = clean_public_text(result[key])
    for key in ('title_options', 'takeaways'):
        if isinstance(result.get(key), list):
            result[key] = [clean_public_text(v) if isinstance(v, str) else v for v in result[key]]
    for section in result.get('sections', []) if isinstance(result.get('sections'), list) else []:
        if not isinstance(section, dict): continue
        if isinstance(section.get('heading'), str): section['heading'] = clean_public_text(section['heading'])
        for paragraph in section.get('paragraphs', []) if isinstance(section.get('paragraphs'), list) else []:
            if isinstance(paragraph, dict) and isinstance(paragraph.get('text'), str):
                paragraph['text'] = clean_public_text(paragraph['text'])
        for figure in section.get('figures', []) if isinstance(section.get('figures'), list) else []:
            if not isinstance(figure, dict): continue
            for key in ('caption', 'explanation'):
                if isinstance(figure.get(key), str): figure[key] = clean_public_text(figure[key])
    return result


def validate_paper_info(value):
    if not isinstance(value, dict): raise ValueError('论文资料需要 JSON 对象。')
    result = {}
    for key in ('title', 'venue', 'version_note', 'verified_on'):
        text = value.get(key, '')
        if not isinstance(text, str) or len(text) > 800: raise ValueError('论文资料文字格式不正确。')
        result[key] = clean_public_text(text)
    for key in ('authors', 'affiliations'):
        entries = value.get(key, [])
        if not isinstance(entries, list) or len(entries) > 200 or not all(isinstance(v, str) and len(v) <= 500 for v in entries):
            raise ValueError('作者和机构需要文字列表。')
        result[key] = [v.strip() for v in entries if v.strip()]
    for key in ('paper_url', 'project_url', 'code_url'):
        url = value.get(key, '')
        if url and not resource_url(url): raise ValueError('论文、项目和代码链接需要完整的 HTTP(S) 地址。')
        result[key] = url or ''
    return result


def paper_details(article, manifest):
    base = {'title': manifest.get('title', ''), 'authors': manifest.get('authors', []),
            'paper_url': manifest.get('source_url', ''), 'affiliations': [], 'project_url': '',
            'code_url': '', 'venue': '', 'version_note': '', 'verified_on': ''}
    generated = article.get('paper') if isinstance(article.get('paper'), dict) else {}
    known_links = {manifest.get('source_url', ''), *manifest.get('resource_links', [])}
    for key, value in generated.items():
        if key not in base or not value: continue
        if key in {'title', 'authors'} and base.get(key): continue
        if key.endswith('_url') and value not in known_links: continue
        base[key] = value
    # User-confirmed metadata takes priority, including explicit cleared fields.
    base.update({k: v for k, v in manifest.get('paper_info', {}).items() if k in base})
    return base
def layout_sections(article):
    """Place figures/tables next to the paragraph that explains them."""
    result=[]
    for index, section in enumerate(article['sections']):
        paragraphs=section['paragraphs'];count=len(paragraphs)
        for offset in range(max(1,count)):
            number=offset+1
            part={'heading':section['heading'] if offset==0 else '', 'display_number':index+1,
                  'paragraphs':paragraphs[offset:offset+1], 'figures':[], 'tables':[]}
            for kind in ('figures','tables'):
                for item in section.get(kind,[]):
                    location=item.get('after_paragraph',count or 1)
                    if location==number:part[kind].append(item)
            result.append(part)
    return result
