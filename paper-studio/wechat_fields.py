"""Adapt submission metadata without rewriting or truncating the original article."""
import json
import re
import time
import uuid
from pathlib import Path
from sources import write_json

TITLE_LIMIT = 32
DIGEST_LIMIT = 120


def normalized(text):
    return ' '.join(str(text or '').split())


def short_digest(text, title):
    """Keep a complete leading sentence sequence, never a clipped metric or token."""
    text = normalized(text)
    if len(text) <= DIGEST_LIMIT:
        return text, '已整理空白字符'
    best = ''
    # Decimal points do not end sentences. Keep closing quotes with the sentence.
    for match in re.finditer(r'[。！？][”’」』）)]*|[.!?]["\')]*(?=\s|$)', text):
        prefix = text[:match.end()].strip()
        if len(prefix) > DIGEST_LIMIT:
            break
        best = prefix
    if len(best) >= 16:
        return best, '保留开头的完整句子，详细结果仍在原稿和正文中'
    return title.rstrip('。.!?！？') + '。本文介绍研究问题、方法设计与实验证据。', '原摘要首句过长，采用简短导读；原摘要完整保留'


def adapt_fields(values, article):
    """Only title/digest are adapted. Author, figures and body remain untouched."""
    result = dict(values)
    changes = []
    for field in ('title', 'digest'):
        original = str(values.get(field, article.get(field, '')) or '').strip()
        value = normalized(original)
        reason = '已整理空白字符'
        if field == 'title' and (not value or len(value) > TITLE_LIMIT):
            candidates = article.get('title_options', [])
            candidates = candidates if isinstance(candidates, list) else []
            value = next((normalized(t) for t in candidates if isinstance(t, str) and 0 < len(normalized(t)) <= TITLE_LIMIT), '论文研读')
            reason = '改用合规备选标题' if value != '论文研读' else '原题过长且无合规备选，采用中性标题；原题完整保留'
        if field == 'digest':
            value, reason = short_digest(value, result['title'])
        result[field] = value
        if value != original:
            changes.append({'field': field, 'before': original, 'after': value, 'reason': reason})
    return result, changes


def validated_adjustments(values, article, proposed):
    """Recompute client preview provenance; never trust supplied reasons/results."""
    if not isinstance(proposed, list):
        return []
    originals = dict(values)
    for item in proposed:
        if not isinstance(item, dict):
            continue
        field = item.get('field')
        if field in ('title', 'digest') and isinstance(item.get('before'), str) and item.get('after') == values.get(field):
            originals[field] = item['before']
    _, changes = adapt_fields(originals, article)
    return [c for c in changes if c['after'] == values.get(c['field'])]


def record_adjustments(folder, changes):
    if not changes:
        return
    folder = Path(folder)
    path = folder / 'wechat-field-adjustments.json'
    old = {}
    if path.exists():
        old = json.loads(path.read_text(encoding='utf8'))
    merged = {c['field']: c for c in old.get('adjustments', [])}
    merged.update({c['field']: c for c in changes})
    changes = list(merged.values())
    if old.get('adjustments') == changes:
        return
    report = {'adjustments': changes, 'updated_at': time.time(), 'original_article_unchanged': True}
    if old:
        history = folder / 'history'
        history.mkdir(exist_ok=True)
        write_json(history / ('wechat-fields-' + uuid.uuid4().hex + '.json'), old)
    write_json(path, report)
