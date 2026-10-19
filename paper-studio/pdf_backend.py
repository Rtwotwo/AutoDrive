"""Small PDF interface built on permissive dependencies, in top-left page points.

pdfplumber supplies layout, PDFium renders, and pypdf decodes image objects.
No OCR is performed. Callers must keep the document open while using its pages.
"""
from dataclasses import dataclass
from functools import cached_property
from io import BytesIO
from pathlib import Path
import threading
from types import SimpleNamespace

import pdfplumber
import pypdfium2 as pdfium
from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject, ArrayObject, NameObject, DictionaryObject

PDF_LOCK = threading.RLock()


class Rect:
    def __init__(self, *values):
        if len(values) == 1:
            values = tuple(values[0])
        self.x0, self.y0, self.x1, self.y1 = map(float, values)

    def __iter__(self): return iter((self.x0, self.y0, self.x1, self.y1))
    def __getitem__(self, index): return tuple(self)[index]
    @property
    def width(self): return max(0, self.x1 - self.x0)
    @property
    def height(self): return max(0, self.y1 - self.y0)
    @property
    def is_empty(self): return self.width <= 0 or self.height <= 0
    def __and__(self, other):
        other = Rect(other)
        return Rect(max(self.x0, other.x0), max(self.y0, other.y0), min(self.x1, other.x1), min(self.y1, other.y1))
    def __or__(self, other):
        other = Rect(other)
        return Rect(min(self.x0, other.x0), min(self.y0, other.y0), max(self.x1, other.x1), max(self.y1, other.y1))
    def __add__(self, offsets): return Rect(*(a + b for a, b in zip(self, offsets)))
    def intersects(self, other): return not (self & other).is_empty


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Matrix:
    x: float
    y: float


class Raster:
    def __init__(self, image):
        self.image = image.convert('RGB')
        self.width, self.height = self.image.size
    @property
    def samples(self): return self.image.tobytes()
    def save(self, path): self.image.save(path)


class Page:
    def __init__(self, doc, number):
        self.doc, self.number = doc, number
        self.layout = doc.layout.pages[number]
        self.rect = Rect(0, 0, self.layout.width, self.layout.height)

    def set_rotation(self, angle):
        if angle != 0: raise ValueError('The extraction interface uses unrotated pages.')

    @cached_property
    def _blocks(self):
        # pdfminer's text boxes preserve columns and multi-line captions. A
        # spatial merge of all words on a row would mix two-column papers.
        from pdfminer.layout import LTTextBox, LTTextLine, LTChar, LTContainer
        def text_boxes(container):
            for element in container:
                if isinstance(element, LTTextBox): yield element
                elif isinstance(element, LTContainer): yield from text_boxes(element)
        result = []
        for box in text_boxes(self.layout.layout):
            lines = []
            for line in box:
                if not isinstance(line, LTTextLine): continue
                all_chars = [char for char in line if isinstance(char, LTChar)]
                chars = [c for c in all_chars if 0 <= (c.x0+c.x1)/2 <= self.rect.width
                         and 0 <= (c.y0+c.y1)/2 <= self.rect.height]
                if not chars: continue
                if len(chars) == len(all_chars): text = line.get_text().strip()
                else:
                    visible = {id(c) for c in chars}
                    text = ''.join(c.get_text() for c in line if not isinstance(c, LTChar) or id(c) in visible).strip()
                if not text: continue
                bbox = (min(c.x0 for c in chars), self.rect.height-max(c.y1 for c in chars),
                        max(c.x1 for c in chars), self.rect.height-min(c.y0 for c in chars))
                direction = (0, 1) if chars and not chars[0].upright else (1, 0)
                lines.append({'dir': direction, 'spans': [{'text': text, 'bbox': bbox,
                    'size': max((c.size for c in chars), default=11)}]})
            if lines:
                bounds = Rect(lines[0]['spans'][0]['bbox'])
                for line in lines[1:]: bounds = bounds | line['spans'][0]['bbox']
                text = '\n'.join(line['spans'][0]['text'] for line in lines)
                result.append({'bbox': tuple(bounds), 'lines': lines, 'text': text})
        return sorted(result, key=lambda b: (round(b['bbox'][1], 1), b['bbox'][0]))

    def get_text(self, kind='text', sort=False):
        if kind == 'dict': return {'blocks': self._blocks}
        if kind == 'blocks':
            return [(*b['bbox'], b['text'], i, 0) for i, b in enumerate(self._blocks)]
        return '\n\n'.join(b['text'] for b in self._blocks)

    def get_links(self):
        links = []
        for ref in self.doc.reader.pages[self.number].get('/Annots', []):
            annotation = ref.get_object()
            action = annotation.get('/A', {})
            if hasattr(action, 'get_object'): action = action.get_object()
            uri = action.get('/URI')
            if uri: links.append({'uri': str(uri)})
        return links

    def get_image_info(self, xrefs=False):
        return [{'bbox': tuple(Rect(i['x0'], i['top'], i['x1'], i['bottom']) & self.rect),
                 'width': i['srcsize'][0], 'height': i['srcsize'][1]}
                for i in self.layout.images if Rect(i['x0'], i['top'], i['x1'], i['bottom']).intersects(self.rect)]

    def get_drawings(self):
        return [{'items': [('l', Point(e['x0'], e['top']), Point(e['x1'], e['bottom']))]}
                for e in self.layout.edges if e.get('orientation') == 'h' and 0 <= e['top'] <= self.rect.height]

    def cluster_drawings(self):
        boxes = [Rect(o['x0'], o['top'], o['x1'], o['bottom']) & self.rect
                 for o in self.layout.rects + self.layout.curves + self.layout.lines
                 if (Rect(o['x0'], o['top'], o['x1'], o['bottom']) + (-.1,-.1,.1,.1)).intersects(self.rect)]
        # Merge touching path fragments, leaving separated panels to the caller.
        groups = []
        for box in boxes:
            merged = box
            again = True
            while again:
                again = False
                for existing in list(groups):
                    if (merged + (-3, -3, 3, 3)).intersects(existing + (-.1, -.1, .1, .1)):
                        merged = merged | existing
                        groups.remove(existing)
                        again = True
            groups.append(merged)
        return [r for r in groups if r.width > 2 and r.height > 2]

    def find_tables(self):
        return SimpleNamespace(tables=[t for t in self.layout.find_tables() if Rect(t.bbox).intersects(self.rect)])

    def get_pixmap(self, matrix, clip=None, alpha=False):
        clip = Rect(clip) if clip is not None else self.rect
        clip = clip & self.rect
        if clip.is_empty: raise ValueError('Empty PDF crop')
        with PDF_LOCK:
            page = self.doc.renderer[self.number]
            try:
                # PDFium crop order: left, bottom, right, top (page units).
                bitmap = page.render(scale=matrix.x, crop=(clip.x0, self.rect.height-clip.y1,
                    self.rect.width-clip.x1, clip.y0))
                try: image = bitmap.to_pil().copy()
                finally: bitmap.close()
            finally: page.close()
        return Raster(image)

    def embedded_images(self):
        """Yield native-resolution images, with masks decoded by pypdf.

        Inspect dimensions before decoding to avoid unbounded decompression.
        Recursive Form XObjects and reused images are handled by pypdf.
        """
        images = self.doc.reader.pages[self.number].images
        visible_objects = {i['stream'].objid for i in self.layout.images
                           if i.get('stream') is not None and Rect(i['x0'],i['top'],i['x1'],i['bottom']).intersects(self.rect)}
        for key in images.keys():
            try:
                # pypdf's keys may identify images nested inside form XObjects.
                resources = self.doc.reader.pages[self.number]['/Resources']
                path = key if isinstance(key, list) else [key]
                if str(path[0]).startswith('~'): continue  # inline image, no stable object
                obj = None
                for part in path:
                    obj = resources['/XObject'][part].get_object()
                    resources = obj.get('/Resources', {})
                width, height = int(obj.get('/Width', 0)), int(obj.get('/Height', 0))
                if obj.indirect_reference and obj.indirect_reference.idnum not in visible_objects: continue
                if width < 96 or height < 64 or not 12000 <= width*height <= 40_000_000: continue
                item = images[key]
                image = item.image
                if image is None: continue
                stream = BytesIO()
                image.convert('RGBA' if 'A' in image.getbands() else 'RGB').save(stream, format='PNG')
                ref = item.indirect_reference
                yield {'data': stream.getvalue(), 'width': image.width, 'height': image.height,
                       'xref': ref.idnum if ref else 0}
            except (ValueError, KeyError, OSError, NotImplementedError):
                continue


class Document:
    def __init__(self, data):
        self.layout = self.renderer = None
        self.reader = PdfReader(BytesIO(data))
        self.needs_pass = bool(self.reader.is_encrypted and not self.reader.decrypt(''))
        self._pages = {}
        if self.needs_pass: return
        if len(self.reader.pages) > 120: raise ValueError('PDF exceeds 120 pages')
        writer = PdfWriter()
        for page in self.reader.pages:
            # One coordinate system for extraction, rendering and saved crop boxes.
            page.rotation = 0
            media=Rect(page.mediabox);visible=Rect(page.cropbox) & media
            if visible.is_empty:raise ValueError('PDF has an empty visible page box')
            x,y=visible.x0,visible.y0
            width,height=visible.width,visible.height
            if x or y: page.add_transformation(Transformation().translate(-float(x), -float(y)))
            annotations=ArrayObject()
            for ref in page.get('/Annots',[]):
                annotation=ref.get_object()
                if '/Rect' not in annotation:continue
                area=Rect(annotation['/Rect']) & visible
                if area.is_empty:continue
                adjusted=DictionaryObject(annotation)
                adjusted[NameObject('/Rect')]=RectangleObject((area.x0-x,area.y0-y,area.x1-x,area.y1-y))
                annotations.append(adjusted)
            page[NameObject('/Annots')]=annotations
            page.mediabox = RectangleObject((0, 0, width, height))
            page.cropbox = RectangleObject((0, 0, width, height))
            writer.add_page(page)
        normalized = BytesIO()
        writer.write(normalized)
        self.data = normalized.getvalue()
        self.reader = PdfReader(BytesIO(self.data))
        try:
            self.layout = pdfplumber.open(BytesIO(self.data), laparams={'detect_vertical': True, 'all_texts': True})
            with PDF_LOCK: self.renderer = pdfium.PdfDocument(self.data)
        except Exception:
            self.close()
            raise

    def __len__(self): return len(self.reader.pages)
    def __iter__(self): return (self[i] for i in range(len(self)))
    def __getitem__(self, index):
        if index not in self._pages: self._pages[index] = Page(self, index)
        return self._pages[index]
    def __enter__(self): return self
    def __exit__(self, *args): self.close()
    def close(self):
        self._pages.clear()
        if self.renderer is not None:
            with PDF_LOCK: self.renderer.close()
            self.renderer = None
        if self.layout is not None:
            self.layout.close()
            self.layout = None


def open(path=None, *, stream=None, filetype='pdf'):
    return Document(bytes(stream) if stream is not None else Path(path).read_bytes())
