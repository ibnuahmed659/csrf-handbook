#!/usr/bin/env python3
"""
extract_docx.py
---------------
Extracts 100% of the content from the source Word document
(`csrf handbook.docx`) and produces a structured JSON content model
(`data/content.json`) used by `tools/build.py` to generate the website.

Design goals:
  * Preserve every paragraph, heading, list, code line and table cell.
  * Never summarise, rewrite or reorder source content.
  * Classify blocks using the paragraph styles that exist in the document:
      - Heading1/HORDHAC/QAYBTA  -> Part (chapter)
      - Heading3                 -> Section
      - Heading4                 -> Subsection
      - HTMLPreformatted / Consolas runs -> code block
      - w:numPr                  -> list item
      - fully bold short line    -> pseudo-heading (used in Part I)

Usage:
    python extract_docx.py "csrf handbook.docx" ../data/content.json
"""

import sys
import os
import re
import json
import zipfile
import argparse
from xml.etree import ElementTree as ET

WNS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
W = '{' + WNS + '}'
NS = {'w': WNS}

LANG_LABELS = {
    'text', 'html', 'php', 'javascript', 'http', 'te', 't',
    'json', 'bash', 'python', 'js', 'css', 'sql', 'xml',
}

# Paragraphs that begin with one of these labels are genuine notes/warnings
# in the source wording; they are rendered as callout panels (presentation
# only - the label text itself is always preserved).
CALLOUT_PREFIXES = (
    ('ogeysiis', 'note'),
    ('fiiro gaar ah', 'note'),
    ('digniin', 'warning'),
    ('warning', 'warning'),
    ('note:', 'note'),
)


def callout_kind(text):
    low = text.strip().lower()
    for prefix, kind in CALLOUT_PREFIXES:
        if low.startswith(prefix):
            return kind
    return None


def esc(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def run_font(rPr):
    if rPr is None:
        return None
    rf = rPr.find('w:rFonts', NS)
    if rf is None:
        return None
    return rf.get(W + 'ascii') or rf.get(W + 'hAnsi') or rf.get(W + 'cs')


def is_bold(rPr):
    if rPr is None:
        return False
    b = rPr.find('w:b', NS)
    if b is None:
        return False
    return b.get(W + 'val') not in ('0', 'false', 'none')


def is_ital(rPr):
    if rPr is None:
        return False
    b = rPr.find('w:i', NS)
    if b is None:
        return False
    return b.get(W + 'val') not in ('0', 'false', 'none')


def get_runs(p):
    out = []
    for r in p.iter(W + 'r'):
        rPr = r.find('w:rPr', NS)
        txt = ''.join(t.text or '' for t in r.iter(W + 't'))
        out.append({'text': txt, 'bold': is_bold(rPr), 'ital': is_ital(rPr), 'font': run_font(rPr)})
    return out


def runs_to_html(runs):
    parts = []
    for r in runs:
        t = r['text']
        if t == '':
            continue
        h = esc(t)
        if r['font'] and 'Consolas' in (r['font'] or ''):
            h = '<code>%s</code>' % h
        if r['bold']:
            h = '<strong>%s</strong>' % h
        if r['ital']:
            h = '<em>%s</em>' % h
        parts.append(h)
    return ''.join(parts)


class Numbering:
    def __init__(self, xml):
        root = ET.fromstring(xml)
        self.abs = {}
        self.num = {}
        for an in root.findall('w:abstractNum', NS):
            aid = an.get(W + 'abstractNumId')
            lvls = {}
            for lvl in an.findall('w:lvl', NS):
                il = lvl.get(W + 'ilvl')
                fmt = lvl.find('w:numFmt', NS)
                lvls[il] = fmt.get(W + 'val') if fmt is not None else 'bullet'
            self.abs[aid] = lvls
        for n in root.findall('w:num', NS):
            nid = n.get(W + 'numId')
            ab = n.find('w:abstractNumId', NS)
            self.num[nid] = ab.get(W + 'val') if ab is not None else None

    def fmt(self, num_id, ilvl):
        ab = self.num.get(num_id)
        if ab is None:
            return 'bullet'
        return self.abs.get(ab, {}).get(ilvl or '0', 'bullet')


def get_style(p):
    pPr = p.find('w:pPr', NS)
    if pPr is None:
        return None
    st = pPr.find('w:pStyle', NS)
    return st.get(W + 'val') if st is not None else None


def get_num(p):
    pPr = p.find('w:pPr', NS)
    if pPr is None:
        return None
    npr = pPr.find('w:numPr', NS)
    if npr is None:
        return None
    il = npr.find('w:ilvl', NS)
    ni = npr.find('w:numId', NS)
    return (il.get(W + 'val') if il is not None else '0',
            ni.get(W + 'val') if ni is not None else None)


def is_code_para(style, runs):
    if style == 'HTMLPreformatted':
        return True
    fonts = [r['font'] for r in runs if r['text'].strip() != '']
    return bool(fonts) and all(f and 'Consolas' in f for f in fonts)


def slugify(text, fallback):
    s = text.lower()
    s = re.sub(r'[^a-z0-9\u0600-\u06ff]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or fallback


def extract(docx_path):
    z = zipfile.ZipFile(docx_path)
    doc = ET.fromstring(z.read('word/document.xml').decode('utf-8'))
    body = doc.find('w:body', NS)
    numbering = Numbering(z.read('word/numbering.xml').decode('utf-8'))

    raw = []
    for child in body:
        tag = child.tag
        if tag == W + 'p':
            style = get_style(child)
            runs = get_runs(child)
            txt = ''.join(r['text'] for r in runs)
            raw.append(('p', {
                'style': style, 'runs': runs, 'text': txt,
                'num': get_num(child),
                'all_bold': bool(runs) and all(r['bold'] for r in runs if r['text'].strip() != ''),
            }))
        elif tag == W + 'tbl':
            rows = []
            for row in child.findall('w:tr', NS):
                cells = []
                for cell in row.findall('w:tc', NS):
                    cruns = []
                    for cp in cell.findall('w:p', NS):
                        cr = get_runs(cp)
                        if cruns and cr:
                            cruns.append({'text': ' ', 'bold': False, 'ital': False, 'font': None})
                        cruns.extend(cr)
                    cells.append(runs_to_html(cruns))
                rows.append(cells)
            raw.append(('tbl', {'rows': rows}))

    blocks = []
    i, n = 0, len(raw)
    while i < n:
        kind, d = raw[i]
        if kind == 'tbl':
            blocks.append({'type': 'table', 'rows': d['rows']})
            i += 1
            continue

        style = d['style']
        runs = d['runs']
        txt = d['text'].strip()
        if txt == '':
            i += 1
            continue

        if is_code_para(style, runs):
            lines = []
            j = i
            while j < n and raw[j][0] == 'p' and is_code_para(raw[j][1]['style'], raw[j][1]['runs']):
                lines.append(''.join(r['text'] for r in raw[j][1]['runs']))
                j += 1
            lang = None
            if lines and lines[0].strip().lower() in LANG_LABELS and len(lines[0].strip()) <= 12:
                lang = lines[0].strip()
                lines = lines[1:]
            while lines and lines[-1].strip() == '':
                lines.pop()
            if lines:
                blocks.append({'type': 'code', 'lang': lang, 'lines': lines})
            i = j
            continue

        multi = txt.count('QAYBTA') >= 2
        is_part = (style == 'Heading1'
                   or (not multi and re.match(r'^QAYBTA\s+[IVX]+\b', txt) and len(txt) < 90)
                   or re.match(r'^HORDHAC\b', txt))
        if is_part:
            blocks.append({'type': 'part', 'html': runs_to_html(runs), 'text': txt})
            i += 1
            continue

        if style in ('Heading2', 'Heading3', 'Heading4'):
            blocks.append({'type': 'heading', 'level': int(style[-1]),
                           'html': runs_to_html(runs), 'text': txt})
            i += 1
            continue

        if d['num'] is not None:
            ordered = numbering.fmt(d['num'][1], d['num'][0]) in (
                'decimal', 'decimalZero', 'lowerLetter', 'upperLetter',
                'lowerRoman', 'upperRoman')
            items = []
            j = i
            while j < n and raw[j][0] == 'p' and raw[j][1]['num'] is not None:
                items.append({
                    'html': runs_to_html(raw[j][1]['runs']),
                    'text': raw[j][1]['text'],
                    'level': int(raw[j][1]['num'][0]),
                })
                j += 1
            blocks.append({'type': 'list', 'ordered': ordered, 'items': items})
            i = j
            continue

        if d['all_bold'] and len(txt) <= 90 and not txt.endswith('.'):
            blocks.append({'type': 'pseudoheading', 'html': runs_to_html(runs), 'text': txt})
            i += 1
            continue

        block = {'type': 'para', 'html': runs_to_html(runs), 'text': txt}
        kind = callout_kind(txt)
        if kind:
            block['callout'] = kind
        blocks.append(block)
        i += 1

    # group into parts
    parts = []
    current = None
    for b in blocks:
        if b['type'] == 'part':
            current = {'title': b['text'], 'blocks': []}
            parts.append(current)
        else:
            if current is None:
                current = {'title': 'HORDHAC BUUGGA', 'blocks': []}
                parts.append(current)
            current['blocks'].append(b)

    # assign ids & anchors (every block receives a stable id)
    for pi, part in enumerate(parts):
        part['id'] = 'part-intro' if pi == 0 else 'part-%d' % pi
        part['index'] = pi
        for bi, b in enumerate(part['blocks']):
            b['id'] = '%s-b%d' % (part['id'], bi)
            if b['type'] in ('heading', 'pseudoheading'):
                b['slug'] = slugify(b['text'], 'section-%d' % bi)

    return parts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('out', nargs='?', default='data/content.json')
    args = ap.parse_args()

    parts = extract(args.docx)
    model = {
        'title': 'CSRF Handbook',
        'source': os.path.basename(args.docx),
        'parts': parts,
    }
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(model, f, ensure_ascii=False, indent=1)

    total = sum(len(p['blocks']) for p in parts)
    print('parts: %d  blocks: %d' % (len(parts), total))
    for p in parts:
        print('  [%s] %s  (%d blocks)' % (p['id'], p['title'], len(p['blocks'])))


if __name__ == '__main__':
    main()
