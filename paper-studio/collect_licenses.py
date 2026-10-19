"""Copy installed package license notices into a local binary distribution.

Only distribution metadata license/notice files are read; no application data
or user configuration is inspected. Dependencies keep their original terms.
"""
import argparse
from importlib.metadata import distributions
from pathlib import Path, PurePosixPath
import re
import shutil


def collect(output):
    output=Path(output);count=0;pdfium=False
    for dist in distributions():
        name=re.sub(r'[^A-Za-z0-9_.-]', '_', dist.metadata['Name'])
        for entry in dist.files or []:
            parts=PurePosixPath(str(entry)).parts
            if '..' in parts or not any(p.endswith(('.dist-info','.egg-info')) for p in parts):continue
            if not any(p.lower().startswith(('license','copying','notice','copyright','authors')) for p in parts):continue
            original=Path(dist.locate_file(entry))
            if not original.is_file():continue
            destination=output/name/Path(*parts)
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(original,destination);count+=1
            if name.lower()=='pypdfium2':pdfium=True
    if not pdfium:raise RuntimeError('PDFium dependency notices were not found; do not redistribute this build.')
    print(f'Collected {count} dependency notice files.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output');collect(parser.parse_args().output)
