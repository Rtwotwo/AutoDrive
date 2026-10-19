"""Synthetic PDF builder for regression tests, using ReportLab (BSD).

The small drawing vocabulary intentionally matches the extraction fixtures.
Reading is always delegated to the production backend, never faked.
"""
from io import BytesIO
from pathlib import Path
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
import pdf_backend
from pdf_backend import Rect

LINK_URI = 2


class Page:
    def __init__(self, doc, width, height):
        self.doc, self.width, self.height = doc, width, height
        self.ops = []
        self.rect = Rect(0, 0, width, height)

    def _op(self, func): self.ops.append(func); self.doc.invalidate()
    def insert_text(self, point, text, fontsize=11, rotate=0):
        def draw(canvas):
            canvas.saveState(); canvas.translate(point[0], self.height-point[1]); canvas.rotate(rotate)
            canvas.setFont('Helvetica', fontsize); canvas.drawString(0, 0, text); canvas.restoreState()
        self._op(draw)
    def insert_textbox(self, box, text, fontsize=11):
        box = Rect(box); lines = []; current = ''
        for word in text.split():
            candidate = (current+' '+word).strip()
            if current and stringWidth(candidate, 'Helvetica', fontsize) > box.width:
                lines.append(current); current = word
            else: current = candidate
        if current: lines.append(current)
        for i, line in enumerate(lines):
            y = box.y0+fontsize+i*fontsize*1.2
            if y <= box.y1: self.insert_text((box.x0, y), line, fontsize)
    def draw_rect(self, box, color=(0, 0, 0), fill=None):
        box = Rect(box)
        def draw(canvas):
            canvas.saveState(); canvas.setStrokeColorRGB(*color)
            if fill is not None: canvas.setFillColorRGB(*fill)
            canvas.rect(box.x0, self.height-box.y1, box.width, box.height, fill=fill is not None)
            canvas.restoreState()
        self._op(draw)
    def draw_line(self, a, b):
        self._op(lambda c: c.line(a[0], self.height-a[1], b[0], self.height-b[1]))
    def insert_image(self, box, stream=None, xref=None):
        box = Rect(box)
        if xref is None:
            xref = len(self.doc.images)+1; self.doc.images[xref] = stream
        data = self.doc.images[xref]
        self._op(lambda c: c.drawImage(ImageReader(BytesIO(data)), box.x0, self.height-box.y1, box.width, box.height, mask='auto'))
        return xref
    def insert_link(self, link):
        box = Rect(link['from'])
        self._op(lambda c: c.linkURL(link['uri'], (box.x0, self.height-box.y1, box.x1, self.height-box.y0)))
    def __getattr__(self, name):
        page = self.doc.reader()[self.doc.pages.index(self)]
        return getattr(page, name)


class Document:
    def __init__(self): self.pages = []; self.images = {}; self._reader = None
    def invalidate(self):
        if self._reader: self._reader.close(); self._reader = None
    def new_page(self, width=595, height=842):
        page = Page(self, width, height); self.pages.append(page); self.invalidate(); return page
    def tobytes(self):
        buffer = BytesIO(); canvas = Canvas(buffer)
        for page in self.pages:
            canvas.setPageSize((page.width, page.height))
            for operation in page.ops: operation(canvas)
            canvas.showPage()
        canvas.save(); return buffer.getvalue()
    def reader(self):
        if self._reader is None: self._reader = pdf_backend.open(stream=self.tobytes())
        return self._reader
    def __enter__(self): return self
    def __exit__(self, *args): self.close()
    def close(self): self.invalidate()


def open(): return Document()


def add_uri(path, uri):
    from pypdf import PdfReader, PdfWriter
    from pypdf.annotations import Link
    reader = PdfReader(BytesIO(Path(path).read_bytes()))
    writer = PdfWriter(); writer.append(reader)
    writer.add_annotation(0, Link(rect=(20, 20, 150, 40), url=uri))
    with Path(path).open('wb') as output: writer.write(output)
