#!/usr/bin/env python3
"""
build.py
--------
Generates the static website from `data/content.json` (produced by
`extract_docx.py`).

It renders:
  * index.html                 - landing page / hero
  * chapters/part-*.html       - one page per part of the handbook
  * data/search-index.json     - machine readable search index
  * data/search-index.js       - the same index for the site (works on file://)
  * data/content-manifest.json - traceability manifest (source -> destination)

Nothing in this script rewrites, summarises or drops source content: it only
wraps the preserved text in semantic HTML and presentation components.

Usage:
    python build.py               (run from the project root)
"""

import json
import os
import re
import html
import hashlib
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
CHAPTERS = os.path.join(ROOT, 'chapters')

PRISM_ALIASES = {
    'html': 'markup', 'xml': 'markup',
    'js': 'javascript', 'javascript': 'javascript',
    'php': 'php', 'http': 'http', 'json': 'json',
    'bash': 'bash', 'css': 'css', 'python': 'python',
}
LANG_NORMALISE = {'te': 'text', 't': 'text'}
KNOWN_LANGS = {'text', 'html', 'php', 'javascript', 'http', 'json', 'bash', 'css', 'python'}


def load_model():
    with open(os.path.join(DATA, 'content.json'), encoding='utf-8') as f:
        return json.load(f)


def esc(s):
    return html.escape(s, quote=False)


def norm_lang(lang):
    if not lang:
        return 'text'
    l = lang.strip().lower()
    l = LANG_NORMALISE.get(l, l)
    return l if l in KNOWN_LANGS else 'text'


DIAGRAM_CHARS = '\u2502\u2500\u251c\u2514\u250c\u2510\u2518\u253c\u25bc\u25b2\u25ba\u25c4\u2551\u2554\u2557\u255a\u255d\u256d\u256e\u2570\u256f'


def _is_ascii_diagram(lines):
    s = ''.join(lines)
    return sum(1 for ch in s if ch in DIAGRAM_CHARS) >= 3


# ---- mental-model flow diagram (built from part-1-b29 content) --------------

def _mm_node(cx, y, title, sub, klass):
    w, h = 300, 56
    x = cx - w / 2
    sub_t = ('<text class="mm-sub" x="%g" y="%g" text-anchor="middle">%s</text>'
             % (cx, y + 42, esc(sub))) if sub else ''
    return ('<g class="mm-node %s">'
            '<rect class="mm-box" x="%g" y="%g" width="%g" height="%g" rx="15"/>'
            '<text class="mm-title" x="%g" y="%g" text-anchor="middle">%s</text>'
            '%s</g>') % (klass, x, y, w, h, cx, y + 24, esc(title), sub_t)


def _mm_step(num, y, lines, kind=''):
    tspans = ''.join(
        '<tspan x="%g"%s>%s</tspan>' % (416, '' if i == 0 else ' dy="15"', esc(t))
        for i, t in enumerate(lines))
    return ('<g class="mm-step %s">'
            '<circle class="mm-step__dot" cx="398" cy="%g" r="11"/>'
            '<text class="mm-step__num" x="398" y="%g" text-anchor="middle">%s</text>'
            '<text class="mm-step__text" x="416" y="%g">%s</text></g>'
            ) % (kind, y - 4, y, esc(num), y, tspans)


def mental_model_diagram():
    cx = 210
    body = []
    body.append('<rect class="mm-frame" x="20" y="8" width="700" height="600" rx="22"/>')
    # nodes
    body.append(_mm_node(cx, 26, 'VICTIM (User)', 'Isticmaalaha', 'mm--victim'))
    body.append(_mm_node(cx, 200, 'BROWSER', 'Confused Deputy', 'mm--browser'))
    body.append(_mm_node(cx, 380, 'SERVER', 'Trusting', 'mm--server'))
    body.append(_mm_node(cx, 532, 'ACTION', 'Change email, transfer, iwm', 'mm--action'))
    # arrows / connectors
    body.append('<line class="mm-conn" x1="%g" y1="82" x2="%g" y2="192"/>' % (cx, cx))
    body.append('<polygon class="mm-arrow mm-arrow--warn" points="%g,198 %g,186 %g,186"/>' % (cx, cx - 9, cx + 9))
    body.append('<line class="mm-conn" x1="%g" y1="256" x2="%g" y2="372"/>' % (cx, cx))
    body.append('<polygon class="mm-arrow mm-arrow--warn" points="%g,378 %g,366 %g,366"/>' % (cx, cx - 9, cx + 9))
    body.append('<line class="mm-conn" x1="%g" y1="436" x2="%g" y2="524"/>' % (cx, cx))
    body.append('<polygon class="mm-arrow" points="%g,530 %g,518 %g,518"/>' % (cx, cx - 9, cx + 9))
    # animated packets
    body.append('<rect class="vflow mm-packet--warn" x="%g" y="84" width="9" height="14" rx="4.5" style="--dy:100px"/>' % (cx - 4.5))
    body.append('<rect class="vflow mm-packet--warn" x="%g" y="258" width="9" height="14" rx="4.5" style="--dy:106px;animation-delay:.7s"/>' % (cx - 4.5))
    body.append('<rect class="vflow mm-packet" x="%g" y="438" width="9" height="14" rx="4.5" style="--dy:80px;animation-delay:1.4s"/>' % (cx - 4.5))
    # steps
    body.append(_mm_step('1', 118, ['Login \u2192 Server-ku wuxuu siiyaa cookie'], 'mm-step--accent'))
    body.append(_mm_step('2', 218, ['Wuxuu hayaa cookie-ga'], 'mm-step--warn'))
    body.append(_mm_step('3a', 282, ['Victim wuxuu booqdaa website kale'], 'mm-step--warn'))
    body.append(_mm_step('3b', 312, ['Website-kaas wuxuu leeyahay form/script'], 'mm-step--warn'))
    body.append(_mm_step('4', 348, ['Browser-ku wuxuu diraa request-ka', 'isagoo wata cookie-ga victim'], 'mm-step--warn'))
    body.append(_mm_step('5', 398, ['Server-ku wuxuu arkaa cookie-ga', 'Wuxuu u malaynayaa in victim', 'request-ka diray'], 'mm-step--accent'))
    body.append(_mm_step('6', 474, ['Server-ku wuxuu sameeyaa action-ka'], 'mm-step--accent'))
    return (
        '<svg class="mm-svg" viewBox="0 0 740 616" role="img" '
        'aria-labelledby="mmTitle mmDesc" focusable="false">'
        '<title id="mmTitle">Mental Model \u2014 VICTIM \u2192 BROWSER (Confused Deputy) \u2192 SERVER (Trusting) \u2192 ACTION</title>'
        '<desc id="mmDesc">Sawirka wuxuu muujinayaa sida CSRF u dhaco: isticmaalaha ayaa login ah oo haysta cookie; browser-ka oo confused deputy ah ayaa u diraa server-ka request isagoo wata cookie-ga victim; server-ku wuxuu u malaynayaa in victim request-ka diray oo wuxuu sameeyaa action-ka.</desc>'
        '%s</svg>') % ''.join(body)


# ---- HTTP request anatomy tree (built from part-2-b66 content) --------------

def _parse_anatomy(lines):
    root = None
    stack = []

    def depth_of(ln):
        i = 0
        groups = 0
        while i + 4 <= len(ln) and ln[i:i + 4] in ('\u2502   ', '    '):
            groups += 1
            i += 4
        rest = ln[i:]
        if rest[:4] in ('\u251c\u2500\u2500 ', '\u2514\u2500\u2500 '):
            return groups + 1, rest[4:]
        return 0, ln.strip()

    for ln in lines:
        if ln.strip() == '':
            continue
        d, rest = depth_of(ln)
        label, _, note = rest.partition(' \u2190 ')
        node = {'label': label.strip(), 'note': note.strip(), 'depth': d, 'children': []}
        if d == 0:
            root = node
            stack = [(0, node)]
            continue
        while stack and stack[-1][0] >= d:
            stack.pop()
        if stack:
            stack[-1][1]['children'].append(node)
            stack.append((d, node))
        elif root is not None:
            root['children'].append(node)
            stack = [(0, root), (d, node)]
    return root


def _note_kind(label, note):
    blob = (label + ' ' + note).lower()
    if 'attacker' in blob:
        return 'danger'
    if 'browser' in blob:
        return 'info'
    if 'server' in blob:
        return 'ok'
    return 'muted'


def _render_anatomy(node):
    cls = _note_kind(node['label'], node['note'])
    note = ('<span class="an__note an__note--%s">%s</span>' % (cls, esc(node['note']))) if node['note'] else ''
    kids = ''
    if node['children']:
        kids = '<ul>%s</ul>' % ''.join(_render_anatomy(c) for c in node['children'])
    return ('<li class="an__node an__node--%s">'
            '<span class="an__label">%s</span>%s%s</li>'
            ) % (cls, esc(node['label']), note, kids)


def render_anatomy_diagram(block):
    lines = block['lines']
    root = _parse_anatomy(lines)
    tree = ('<ul class="anatomy">%s</ul>' % _render_anatomy(root)) if root else ''
    ascii_html = '\n'.join(esc(l) for l in lines)
    return (
        '<figure class="diagram-figure diagram-figure--anatomy">'
        '<div class="diagram-figure__bar"><span class="diagram-figure__tag">Jirka REQUEST-ka</span>'
        '<span class="diagram-figure__hint">Yaa maamula (controlled by)</span></div>'
        '%s'
        '<details class="diagram-source"><summary>Qoraalka asalka ah ee buugga</summary>'
        '<pre class="diagram-ascii">%s</pre></details>'
        '</figure>') % (tree, ascii_html)


def render_mental_model(block):
    lines = block['lines']
    ascii_html = '\n'.join(esc(l) for l in lines)
    return (
        '<figure class="diagram-figure diagram-figure--flow">'
        '<div class="diagram-figure__bar"><span class="diagram-figure__tag">Mental Model</span>'
        '<span class="diagram-figure__hint">sida CSRF u dhaco \u2014 tillaabo tillaabo</span></div>'
        '%s'
        '<details class="diagram-source"><summary>Qoraalka asalka ah ee buugga</summary>'
        '<pre class="diagram-ascii">%s</pre></details>'
        '</figure>') % (mental_model_diagram(), ascii_html)


def render_code(block):
    lines = block['lines']
    if _is_ascii_diagram(lines):
        joined = '\n'.join(lines)
        if 'Confused Deputy' in joined:
            return render_mental_model(block)
        if joined.lstrip().startswith('REQUEST'):
            return render_anatomy_diagram(block)
    lang = norm_lang(block.get('lang'))
    code = '\n'.join(esc(l) for l in lines)
    prism = PRISM_ALIASES.get(lang)
    cls = 'language-%s' % prism if prism else ''
    label = lang if lang else 'text'
    lines_n = len(lines)
    return (
        '<figure class="code-panel">'
        '<figcaption class="code-panel__head">'
        '<span class="code-panel__lang">%s</span>'
        '<span class="code-panel__lines">%d sadar</span>'
        '<button type="button" class="copy-btn" data-copy aria-label="Copy code to clipboard">'
        '<span class="copy-btn__label">Copy</span></button>'
        '</figcaption>'
        '<pre class="code-block" tabindex="0"><code class="%s">%s</code></pre>'
        '</figure>' % (label, lines_n, cls, code)
    )


def render_list(block):
    items = block['items']
    tag = 'ol' if block['ordered'] else 'ul'

    tree = []
    stack = [(-1, tree)]
    for it in items:
        node = {'html': it['html'], 'children': []}
        lvl = it.get('level', 0)
        while stack and stack[-1][0] >= lvl:
            stack.pop()
        stack[-1][1].append(node)
        stack.append((lvl, node['children']))

    def render(nodes):
        out = ['<%s class="doc-list">' % tag]
        for n in nodes:
            out.append('<li>%s' % n['html'])
            if n['children']:
                out.append(render(n['children']))
            out.append('</li>')
        out.append('</%s>' % tag)
        return ''.join(out)

    return render(tree)


def render_table(block):
    rows = block['rows']
    if not rows:
        return ''
    out = ['<div class="table-wrap" role="region" tabindex="0" aria-label="Scrollable table">']
    out.append('<table class="doc-table">')
    head, body = rows[0], rows[1:]
    out.append('<thead><tr>')
    for c in head:
        out.append('<th scope="col">%s</th>' % c)
    out.append('</tr></thead>')
    if body:
        out.append('<tbody>')
        for row in body:
            out.append('<tr>')
            for c in row:
                out.append('<td>%s</td>' % c)
            out.append('</tr>')
        out.append('</tbody>')
    out.append('</table></div>')
    return ''.join(out)


CALLOUT_ICONS = {
    'note': ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/>'
             '<path d="M12 11v5M12 8h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'),
    'warning': ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">'
                '<path d="M12 3l9 16H3z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>'
                '<path d="M12 10v4M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'),
}


def render_callout(b, bid):
    kind = b.get('callout', 'note')
    icon = CALLOUT_ICONS.get(kind, CALLOUT_ICONS['note'])
    return ('<aside class="callout callout--%s" role="note">'
            '<span class="callout__icon">%s</span>'
            '<p class="callout__text" id="%s">%s</p>'
            '</aside>') % (kind, icon, bid, b['html'])


def render_block(b):
    t = b['type']
    bid = b.get('id', '')
    if t == 'para':
        if b.get('callout'):
            return render_callout(b, bid)
        return '<p id="%s">%s</p>' % (bid, b['html'])
    if t == 'pseudoheading':
        return '<h2 id="%s" class="section-title section-title--soft">%s</h2>' % (bid, b['html'])
    if t == 'heading':
        if b['level'] == 4:
            return '<h3 id="%s" class="subsection-title">%s</h3>' % (bid, b['html'])
        return '<h2 id="%s" class="section-title">%s</h2>' % (bid, b['html'])
    if t == 'code':
        return render_code(b)
    if t == 'list':
        return render_list(b)
    if t == 'table':
        return render_table(b)
    return '<p id="%s">%s</p>' % (bid, b.get('html', ''))


def add_reveal(html):
    """Add a data-reveal hook to the first tag so scroll animations apply."""
    if not html or not html.startswith('<'):
        return html
    i = html.find('>')
    if i == -1:
        return html
    return html[:i] + ' data-reveal' + html[i:]


# ---------------------------------------------------------------------------
# Illustrations (inline SVG). Presentation only - they visualise concepts that
# already exist in the source (attacker, browser confused deputy, server,
# cookies, HTTP, defenses) and never add new technical claims.
# ---------------------------------------------------------------------------

def hero_scene():
    return '''<svg viewBox="0 0 560 440" role="img" aria-labelledby="heroSceneTitle heroSceneDesc" focusable="false">
<title id="heroSceneTitle">Attacker, browser-ka (confused deputy) iyo server-ka bangiga</title>
<desc id="heroSceneDesc">Sawirka wuxuu muujinayaa attacker website (evil.com) oo diraya request; browser-ka isticmaalaha oo ah robot (confused deputy) oo wata cookie-ga; iyo server-ka bangiga oo shield leh oo u malaynaya in isticmaalaha request-ka diray.</desc>
<defs>
<radialGradient id="heroGlow" cx="50%" cy="42%" r="64%">
<stop class="stop-accent" offset="0" stop-opacity=".34"/>
<stop class="stop-accent" offset="1" stop-opacity="0"/>
</radialGradient>
<linearGradient id="hoodGrad" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#232f4d"/><stop offset="1" stop-color="#0e1526"/>
</linearGradient>
</defs>
<ellipse cx="285" cy="195" rx="252" ry="190" fill="url(#heroGlow)"/>
<circle class="twinkle hero-dot" cx="118" cy="58" r="3"/>
<circle class="twinkle hero-dot" cx="486" cy="112" r="2.6" style="animation-delay:.6s"/>
<circle class="twinkle hero-dot" cx="404" cy="372" r="2.6" style="animation-delay:1.2s"/>
<circle class="twinkle hero-dot" cx="70" cy="330" r="2.2" style="animation-delay:1.8s"/>

<!-- ============ ATTACKER (left): hooded hacker at evil.com ============ -->
<g class="float-med" data-depth="16">
  <rect x="8" y="150" width="152" height="150" rx="18" class="scene-panel scene-stroke" stroke-width="1.5"/>
  <path d="M8 178 h152" class="scene-stroke" stroke-width="1.5"/>
  <circle cx="148" cy="164" r="3.4" fill="#ff5f57"/><circle cx="136" cy="164" r="3.4" fill="#febc2e"/><circle cx="124" cy="164" r="3.4" fill="#28c840"/>
  <text x="22" y="170" class="scene-danger" font-size="12" font-weight="800">evil.com</text>
  <!-- hooded character -->
  <path d="M84 194 c-20 0 -32 16 -32 36 v30 h64 v-30 c0 -20 -12 -36 -32 -36z" fill="url(#hoodGrad)" stroke="#3d4a6b" stroke-width="1.4"/>
  <path d="M84 210 c-12 0 -20 10 -20 22 v18 h40 v-18 c0 -12 -8 -22 -20 -22z" fill="#0a0f1c"/>
  <circle cx="76" cy="228" r="3" fill="#ff5f6d"/><circle cx="92" cy="228" r="3" fill="#ff5f6d"/>
  <path d="M78 240 q6 5 12 0" fill="none" stroke="#ff5f6d" stroke-width="1.6" stroke-linecap="round" opacity=".8"/>
  <text x="84" y="288" text-anchor="middle" class="scene-dim" font-size="10" letter-spacing="1">ATTACKER</text>
</g>

<!-- ============ BROWSER (center): friendly robot / confused deputy ============ -->
<g class="float-slow" data-depth="8">
  <rect x="176" y="74" width="208" height="272" rx="24" class="scene-panel scene-stroke" stroke-width="1.5"/>
  <path d="M176 106 h208" class="scene-stroke" stroke-width="1.5"/>
  <circle cx="194" cy="90" r="4" fill="#ff5f57"/><circle cx="208" cy="90" r="4" fill="#febc2e"/><circle cx="222" cy="90" r="4" fill="#28c840"/>
  <rect x="236" y="82" width="136" height="16" rx="8" class="scene-panel-2"/>
  <text x="246" y="94" class="scene-dim" font-size="10">victim-bank.com</text>
  <!-- antenna -->
  <line x1="280" y1="128" x2="280" y2="112" class="scene-accent" stroke-width="2.4" stroke-linecap="round"/>
  <circle cx="280" cy="108" r="5" class="scene-accent-fill"/>
  <circle cx="280" cy="108" r="8" class="scene-accent pulse-ring" fill="none" stroke-width="1.6"/>
  <!-- robot face -->
  <rect x="230" y="134" width="100" height="82" rx="24" class="scene-panel-2 scene-stroke" stroke-width="1.6"/>
  <g data-blink><circle cx="261" cy="170" r="6" class="scene-accent-fill"/><circle cx="299" cy="170" r="6" class="scene-accent-fill"/></g>
  <circle cx="261" cy="170" r="10" class="scene-accent" fill="none" stroke-width="1.3" opacity=".5"/>
  <circle cx="299" cy="170" r="10" class="scene-accent" fill="none" stroke-width="1.3" opacity=".5"/>
  <path d="M262 194 q18 13 36 0" class="scene-accent" fill="none" stroke-width="2.8" stroke-linecap="round"/>
  <!-- little arms -->
  <rect x="206" y="216" width="16" height="30" rx="8" class="scene-panel-2 scene-stroke" stroke-width="1.4"/>
  <rect x="338" y="216" width="16" height="30" rx="8" class="scene-panel-2 scene-stroke" stroke-width="1.4"/>
  <!-- body + cookie -->
  <rect x="240" y="228" width="80" height="48" rx="16" class="scene-panel-2 scene-stroke" stroke-width="1.5"/>
  <circle cx="280" cy="252" r="13" fill="#e8b573"/>
  <circle cx="275" cy="247" r="1.8" fill="#7a4a1d"/><circle cx="285" cy="250" r="1.8" fill="#7a4a1d"/><circle cx="278" cy="258" r="1.8" fill="#7a4a1d"/>
  <text x="280" y="312" text-anchor="middle" class="scene-dim" font-size="11">BROWSER · confused deputy</text>
</g>

<!-- ============ SERVER (right): vault guarded by a shield ============ -->
<g class="float-fast" data-depth="11">
  <rect x="408" y="96" width="146" height="216" rx="20" class="scene-panel scene-stroke" stroke-width="1.5"/>
  <path d="M481 120 l34 13 v28 c0 24 -15 41 -34 48 c-19 -7 -34 -24 -34 -48 v-28z" class="scene-accent" fill="none" stroke-width="2.2" stroke-linejoin="round"/>
  <path d="M469 176 l8 8 18 -20" class="scene-accent" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="481" cy="256" r="21" class="scene-panel-2 scene-stroke"/>
  <circle cx="481" cy="256" r="8" class="scene-accent" fill="none" stroke-width="2"/>
  <line x1="481" y1="256" x2="481" y2="245" class="scene-accent" stroke-width="2" stroke-linecap="round"/>
  <text x="481" y="298" text-anchor="middle" class="scene-text" font-size="12" font-weight="800">SERVER</text>
</g>

<!-- ============ flow: packets travel browser -> server ============ -->
<line x1="158" y1="228" x2="176" y2="228" class="scene-danger flow-line" stroke-width="1.6"/>
<line x1="384" y1="188" x2="408" y2="188" class="scene-accent flow-line" stroke-width="1.6"/>
<rect class="flow-packet scene-danger-fill" x="158" y="222" width="16" height="11" rx="5.5" style="--dx:18px"/>
<rect class="flow-packet scene-accent-fill" x="384" y="182" width="20" height="12" rx="6" style="--dx:24px;animation-delay:.9s"/>
<text x="46" y="52" class="scene-dim" font-size="12" style="font-family:var(--font-mono)" opacity=".7">&lt;script&gt;</text>
<text x="430" y="70" class="scene-purple" font-size="12" style="font-family:var(--font-mono)" opacity=".7">&lt;form&gt;</text>
<text x="150" y="410" class="scene-dim" font-size="12" style="font-family:var(--font-mono)" opacity=".65">Cookie: session=ABC123</text>
</svg>'''

_EMBLEM_ICONS = {
    'part-intro': '<path d="M58 130V74c13-6 28-6 42 0 14-6 29-6 42 0v56c-13-6-28-6-42 0-14-6-29-6-42 0z" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M100 78v50" stroke="currentColor" stroke-width="3"/>',
    'part-1': '<rect x="58" y="62" width="84" height="62" rx="18" fill="none" stroke="currentColor" stroke-width="3"/><path d="M86 124l-9 18" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><text x="100" y="108" text-anchor="middle" font-size="36" font-weight="800" fill="currentColor" style="font-family:var(--font-sans)">?</text>',
    'part-2': '<rect x="54" y="70" width="92" height="64" rx="12" fill="none" stroke="currentColor" stroke-width="3"/><path d="M56 78l44 32 44-32" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><path d="M120 148h26M133 135v26" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
    'part-3': '<circle cx="90" cy="90" r="30" fill="none" stroke="currentColor" stroke-width="3"/><path d="M112 112l26 30" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M78 90l8 8 18-20" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
    'part-4': '<path d="M100 58l38 15v30c0 27-16 46-38 53-22-7-38-26-38-53v-30z" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M84 106l11 11 22-24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>',
    'part-5': '<path d="M88 60h24M93 60v30l-24 46c-4 8 2 16 12 16h38c10 0 16-8 12-16l-24-46V60" fill="none" stroke="currentColor" stroke-width="3" stroke-linejoin="round"/><path d="M80 128h40" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
    'part-6': '<circle cx="84" cy="84" r="20" fill="none" stroke="currentColor" stroke-width="3"/><path d="M99 99l30 30M120 128l-9 9" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M129 138l9 9M141 126l9 9" stroke="currentColor" stroke-width="3" stroke-linecap="round" opacity=".5"/>',
    'part-7': '<circle cx="66" cy="132" r="12" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="134" cy="132" r="12" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="100" cy="70" r="12" fill="none" stroke="currentColor" stroke-width="3"/><path d="M74 122l18-38M126 122l-18-38" stroke="currentColor" stroke-width="3" stroke-linecap="round"/><path d="M78 132h44" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>',
}


def emblem_svg(pid):
    inner = _EMBLEM_ICONS.get(pid, _EMBLEM_ICONS['part-1'])
    return ('<svg viewBox="0 0 200 200" role="img" aria-hidden="true" focusable="false">'
            '<circle cx="100" cy="100" r="80" class="emblem-ring-a spin-slow" fill="none" stroke-width="1.5" stroke-dasharray="4 10"/>'
            '<circle cx="100" cy="100" r="62" class="emblem-ring-b spin-rev" fill="none" stroke-width="2.5" stroke-dasharray="30 16" opacity=".7"/>'
            '<circle cx="100" cy="100" r="72" class="emblem-ring-c" fill="none" stroke-width="1" opacity=".25"/>'
            '<g class="emblem-core">%s</g></svg>') % inner


_PART_ICONS = {
    'part-1': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 016.5 3h11A2.5 2.5 0 0120 5.5v7a2.5 2.5 0 01-2.5 2.5H9l-4 4v-4H6.5A2.5 2.5 0 014 12.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M10 8.6a2 2 0 113 1.9c-.6.4-1 .8-1 1.5M12 13.6h.01" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    'part-2': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4 7l8 6 8-6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
    'part-3': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16 16l4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M8.5 11l1.8 1.8 3.4-3.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'part-4': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 3l7 2.6v6c0 4.6-3 7.9-7 9-4-1.1-7-4.4-7-9v-6z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M8.8 12l2.2 2.2 4.2-4.6" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'part-5': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M9 3h6M10 3v5l-4 8a2 2 0 001.8 3h8.4A2 2 0 0018 16l-4-8V3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M7 15h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    'part-6': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="8" cy="8" r="4.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M11.5 11.5L20 20M17 17l-2 2M14 14l-2 2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    'part-7': '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><circle cx="6" cy="17" r="2.6" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="18" cy="17" r="2.6" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="6" r="2.6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10.4 8.2L7 14.6M13.6 8.2L17 14.6M8.6 17h6.8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
}


def part_number(pid):
    m = re.search(r'(\d+)', pid)
    return ('%02d' % int(m.group(1))) if m else ''


def part_counts(part):
    c = {'sections': 0, 'code': 0, 'tables': 0, 'lists': 0}
    for b in part['blocks']:
        if b['type'] in ('heading', 'pseudoheading'):
            c['sections'] += 1
        elif b['type'] == 'code':
            c['code'] += 1
        elif b['type'] == 'table':
            c['tables'] += 1
        elif b['type'] == 'list':
            c['lists'] += 1
    return c


_CHIP_ICONS = {
    'sections': '<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    'code': '<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path d="M9 8l-4 4 4 4M15 8l4 4-4 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    'tables': '<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><rect x="4" y="5" width="16" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 10h16M10 10v9" stroke="currentColor" stroke-width="2"/></svg>',
    'lists': '<svg viewBox="0 0 24 24" width="13" height="13" aria-hidden="true"><path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
}


def chapter_hero(part):
    title = slug_title(part)
    m = re.match(r'^\s*(QAYBTA\s+[IVX]+)', title)
    eyebrow = m.group(1) if m else 'HORDHAC'
    c = part_counts(part)
    chips = []
    if c['sections']:
        chips.append('<li class="chip">%s <b>%d</b> qaybood</li>' % (_CHIP_ICONS['sections'], c['sections']))
    if c['code']:
        chips.append('<li class="chip">%s <b>%d</b> tusaale</li>' % (_CHIP_ICONS['code'], c['code']))
    if c['tables']:
        chips.append('<li class="chip">%s <b>%d</b> jadwal</li>' % (_CHIP_ICONS['tables'], c['tables']))
    meta = ('<ul class="chapter-hero__meta">%s</ul>' % ''.join(chips)) if chips else ''
    return ('<header class="chapter-hero reveal-hero" data-accent="%s">'
            '<div class="chapter-hero__text">'
            '<p class="chapter-hero__eyebrow">%s</p>'
            '<h1 class="chapter-hero__title">%s</h1>'
            '%s'
            '</div>'
            '<div class="chapter-hero__art">%s</div>'
            '</header>') % (part['id'], esc(eyebrow), esc(title), meta, emblem_svg(part['id']))


def section_outline(part):
    """Return list of headings (sections + subsections) for on-this-page nav."""
    out = []
    for b in part['blocks']:
        if b['type'] in ('heading', 'pseudoheading'):
            out.append({'id': b['id'], 'text': b.get('text', ''),
                        'sub': b['type'] == 'heading' and b.get('level') == 4})
    return out


def render_article(part, with_hero=True):
    out = []
    if with_hero:
        out.append(chapter_hero(part))
    for b in part['blocks']:
        out.append(add_reveal(render_block(b)))
    return '\n'.join(out)


def slug_title(part):
    return re.sub('<[^>]+>', '', part['title'])


def render_sidebar(parts, current_id, chapter_prefix):
    li = []
    li.append('<nav class="toc" aria-label="Handbook contents">')
    li.append('<p class="toc__title">Buugga oo dhan</p>')
    li.append('<ol class="toc__parts">')
    for p in parts:
        active = ' is-active' if p['id'] == current_id else ''
        secs = section_outline(p)
        li.append('<li class="toc__part%s">' % active)
        link = '%s%s.html' % (chapter_prefix, p['id'])
        li.append('<div class="toc__part-row">')
        li.append('<a class="toc__part-link" href="%s">%s</a>' % (link, esc(slug_title(p))))
        if secs:
            li.append('<button class="toc__toggle" type="button" aria-expanded="false" '
                      'aria-label="Toggle sections">'
                      '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">'
                      '<path d="M6 9l6 6 6-6" fill="none" stroke="currentColor" '
                      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
                      '</button>')
        li.append('</div>')
        if secs:
            li.append('<ol class="toc__sections">')
            for s in secs:
                li.append('<li class="toc__section%s">'
                          '<a href="%s#%s">%s</a></li>'
                          % (' toc__section--sub' if s['sub'] else '',
                             link, s['id'], esc(s['text'])))
            li.append('</ol>')
        li.append('</li>')
    li.append('</ol>')
    li.append('</nav>')
    return '\n'.join(li)


def render_onthispage(part):
    secs = section_outline(part)
    if not secs:
        return ''
    out = ['<nav class="onthispage" aria-label="On this page">',
           '<p class="onthispage__title">Boggan</p>', '<ol class="onthispage__list">']
    for s in secs:
        out.append('<li class="%s"><a href="#%s">%s</a></li>'
                   % ('is-sub' if s['sub'] else '', s['id'], esc(s['text'])))
    out.append('</ol></nav>')
    return '\n'.join(out)


def render_pager(parts, index, chapter_prefix):
    prev_p = parts[index - 1] if index > 0 else None
    next_p = parts[index + 1] if index + 1 < len(parts) else None
    out = ['<nav class="pager" aria-label="Chapter navigation">']
    if prev_p:
        out.append('<a class="pager__link pager__link--prev" href="%s%s.html">'
                   '<span class="pager__dir">Hore</span>'
                   '<span class="pager__title">%s</span></a>'
                   % (chapter_prefix, prev_p['id'], esc(slug_title(prev_p))))
    else:
        out.append('<span class="pager__spacer"></span>')
    if next_p:
        out.append('<a class="pager__link pager__link--next" href="%s%s.html">'
                   '<span class="pager__dir">Xiga</span>'
                   '<span class="pager__title">%s</span></a>'
                   % (chapter_prefix, next_p['id'], esc(slug_title(next_p))))
    else:
        out.append('<span class="pager__spacer"></span>')
    out.append('</nav>')
    return '\n'.join(out)


def breadcrumb(part, home):
    return ('<nav class="breadcrumb" aria-label="Breadcrumb">'
            '<a href="%s">Bogga Hore</a>'
            '<span aria-hidden="true">/</span>'
            '<span aria-current="page">%s</span>'
            '</nav>') % (home, esc(slug_title(part)))


HEAD = '''<!doctype html>
<html lang="so" data-theme="dark" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="CSRF Handbook - buug-gacmeedka CSRF oo af-Soomaali ah.">
<title>{title}</title>
<link rel="icon" href="{asset}img/favicon.svg" type="image/svg+xml">
<meta name="color-scheme" content="dark light">
<script>
(function () {{
  try {{
    var t = localStorage.getItem('csrf-theme');
    if (!t) t = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', t);
  }} catch (e) {{}}
  document.documentElement.classList.remove('no-js');
  window.addEventListener('load', function () {{
    setTimeout(function () {{
      if (!window.__csrfAnim) document.documentElement.classList.add('no-js');
    }}, 1500);
  }});
}})();
</script>
<link rel="stylesheet" href="{asset}vendor/bootstrap/bootstrap.min.css">
<link rel="stylesheet" href="{asset}css/themes.css">
<link rel="stylesheet" href="{asset}css/style.css">
<link rel="stylesheet" href="{asset}css/premium.css">
<link rel="stylesheet" href="{asset}css/responsive.css">
</head>
<body data-chapterdir="{chapter_prefix}" data-current="{current}">
<a class="skip-link" href="#main">U gudub nuxurka</a>
<div class="reading-progress" aria-hidden="true"><span id="reading-progress-bar"></span></div>
<header class="site-header">
  <button class="icon-btn" id="menu-toggle" type="button" aria-label="Fur liiska qaybaha" aria-expanded="false" aria-controls="sidebar">
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
  </button>
  <a class="brand" href="{home}">
    <span class="brand__mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" width="26" height="26">
        <path d="M16 2l11 5v9c0 7-4.7 12.4-11 14C9.7 28.4 5 23 5 16V7z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        <path d="M11 16l3.5 3.5L21 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>
    <span class="brand__text"><strong>CSRF</strong> Handbook</span>
  </a>
  <div class="header-actions">
    <button class="search-btn" id="search-open" type="button" aria-label="Raadi buugga">
      <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <span class="search-btn__text">Raadi</span>
      <kbd class="search-btn__kbd">/</kbd>
    </button>
    <button class="icon-btn" id="toc-toggle" type="button" aria-label="Fur liiska boggan" aria-expanded="false" aria-controls="onthispage">
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    </button>
    <button class="icon-btn theme-toggle" id="theme-toggle" type="button" aria-label="Beddel mawduuca" aria-pressed="false">
      <svg class="icon-moon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
    </button>
  </div>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar" aria-label="Liiska qaybaha">
    <div class="sidebar__inner">
{sidebar}
    </div>
  </aside>
  <div class="sidebar-scrim" id="sidebar-scrim" hidden></div>
  <main class="content" id="main">
{breadcrumbs}
{article}
{pager}
    <footer class="site-footer">
      <p>CSRF Handbook - nuxurka buugga asalka ah, si dhammaystiran loo ilaaliyay.</p>
      <p class="site-footer__note">Nuxurka waxa uu ka soo jeedaa buugga <em>csrf handbook.docx</em>. Qaybaha UI-ga (badanaha, liisyada iyo boggaga) waa kordhin muuqaal oo aan wax ka beddelin qoraalka asalka ah.</p>
    </footer>
  </main>
  <aside class="onthispage-aside" id="onthispage" aria-label="Boggan gudihiisa">
{onthispage}
  </aside>
</div>
<button class="back-to-top" id="back-to-top" type="button" aria-label="Ku noqo korka bogga" hidden>
  <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path d="M12 19V6M6 12l6-6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
</button>
<div class="search-modal" id="search-modal" role="dialog" aria-modal="true" aria-labelledby="search-title" hidden>
  <div class="search-modal__backdrop" data-search-close></div>
  <div class="search-modal__panel" role="document">
    <h2 class="sr-only" id="search-title">Raadi buugga</h2>
    <div class="search-modal__field">
      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2"/><path d="M20 20l-3.5-3.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
      <input type="search" id="search-input" placeholder="Raadi qayb, qayb-hoosaad, eray, koodh..." autocomplete="off" aria-controls="search-results" aria-label="Erayga raadinta">
      <button type="button" class="search-modal__close" data-search-close aria-label="Xir raadinta">Esc</button>
    </div>
    <div class="search-modal__hint" id="search-hint">Qor eray si aad uga raadiso buugga oo dhan.</div>
    <ol class="search-results" id="search-results" aria-live="polite"></ol>
  </div>
</div>
<script src="{asset}vendor/prism/prism.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-markup.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-clike.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-javascript.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-css.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-json.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-bash.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-markup-templating.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-php.min.js" defer></script>
<script src="{asset}vendor/prism/components/prism-http.min.js" defer></script>
<script src="{asset}js/theme.js" defer></script>
<script src="{asset}js/navigation.js" defer></script>
<script src="{asset}js/reading-progress.js" defer></script>
<script src="{datadir}data/search-index.js" defer></script>
<script src="{asset}js/animations.js" defer></script>
<script src="{asset}js/search.js" defer></script>
<script src="{asset}js/app.js" defer></script>
</body>
</html>
'''


def build_page(parts, index, page_title):
    part = parts[index]
    page = HEAD.format(
        title=page_title,
        asset='../assets/',
        datadir='../',
        chapter_prefix='',
        current=part['id'],
        home='../index.html',
        sidebar=render_sidebar(parts, part['id'], ''),
        breadcrumbs=breadcrumb(part, '../index.html'),
        article=render_article(part),
        pager=render_pager(parts, index, ''),
        onthispage=render_onthispage(part),
    )
    out = os.path.join(CHAPTERS, '%s.html' % part['id'])
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    return out


def part_cards(parts):
    cards = []
    for p in parts:
        if p['id'] == 'part-intro':
            continue
        secs = section_outline(p)
        title = esc(slug_title(p))
        subs = [s for s in secs if not s['sub']][:4]
        lis = ''.join('<li>%s</li>' % esc(s['text']) for s in subs)
        link = 'chapters/%s.html' % p['id']
        icon = _PART_ICONS.get(p['id'], '')
        cards.append(
            '<article class="part-card" data-accent="%s">'
            '<a class="part-card__link" href="%s">'
            '<div class="part-card__top">'
            '<span class="part-card__badge">%s</span>'
            '<span class="part-card__icon" aria-hidden="true">%s</span>'
            '</div>'
            '<h3 class="part-card__title">%s</h3>'
            '<p class="part-card__meta">%d qaybood</p>'
            '<ul class="part-card__list">%s</ul>'
            '<span class="part-card__cta">Akhri <span aria-hidden="true">&rarr;</span></span>'
            '</a></article>' % (p['id'], link, part_number(p['id']), icon, title, len(secs), lis))
    return '\n'.join(cards)


def build_index(model):
    parts = model['parts']
    intro = parts[0]
    intro_html = render_article(intro, with_hero=False)

    counts = {
        'parts': len(parts) - 1,
        'blocks': sum(len(p['blocks']) for p in parts),
        'code': sum(1 for p in parts for b in p['blocks'] if b['type'] == 'code'),
        'tables': sum(1 for p in parts for b in p['blocks'] if b['type'] == 'table'),
    }

    diagram = ('<figure class="diagram-figure diagram-figure--flow" id="mindmap">'
               '<div class="diagram-figure__bar">'
               '<span class="diagram-figure__tag">Mental Model</span>'
               '<span class="diagram-figure__hint">victim &rarr; browser (confused deputy) &rarr; server (trusting) &rarr; action</span>'
               '</div>' + mental_model_diagram() + '</figure>')

    partnav = '<div class="hero__contents"><h2 class="hero__contents-title">Qaybaha buugga</h2><div class="part-grid">%s</div></div>' % part_cards(parts)

    body = '''
<section class="hero">
  <div class="hero__bg" aria-hidden="true"></div>
  <div class="hero__inner">
    <div class="hero__copy">
      <p class="hero__eyebrow">Buug-gacmeed amniga web-ka</p>
      <h1 class="hero__title">CSRF <span>Handbook</span></h1>
      <p class="hero__lead">Buug-gacmeed af-Soomaali ah oo si qoto dheer u falanqeynaya <strong>Cross-Site Request Forgery</strong>: falsafadda, HTTP, anatomy of CSRF, difaacyada, lab-yada fudud, bypasses, iyo SameSite/WebSocket.</p>
      <div class="hero__actions">
        <a class="btn btn--primary" href="chapters/part-1.html">Bilow Barashada <span aria-hidden="true">&rarr;</span></a>
        <a class="btn btn--ghost" href="#contents">Eeg Tusmada</a>
      </div>
      <div class="hero__stats">
        <div class="stat"><span class="stat__num" data-count="%d">%d</span><span class="stat__label">Qaybo</span></div>
        <div class="stat"><span class="stat__num" data-count="%d">%d</span><span class="stat__label">Tusaale</span></div>
        <div class="stat"><span class="stat__num" data-count="%d">%d</span><span class="stat__label">Jadwal</span></div>
        <div class="stat"><span class="stat__num" data-count="%d">%d</span><span class="stat__label">Qodob</span></div>
      </div>
    </div>
    <div class="hero__scene" data-reveal>%s</div>
  </div>
  <a class="scroll-cue" href="#contents" aria-label="Hoos u dhaadhac"><span class="scroll-cue__track"><span class="scroll-cue__dot"></span></span></a>
</section>

<section class="home-section" id="contents">
  <div class="flourish" aria-hidden="true"><span class="flourish__mark">&sect;</span></div>
  <div class="home-intro">
    <div class="home-intro__text">
      <h2 class="home-intro__title">Hordhac</h2>
      %s
    </div>
    %s
  </div>
  %s
  <div class="home-diagram">%s</div>
</section>
''' % (counts['parts'], counts['parts'], counts['code'], counts['code'],
       counts['tables'], counts['tables'], counts['blocks'], counts['blocks'],
       hero_scene(), intro_html, "", partnav, diagram)

    page = HEAD.format(
        title='CSRF Handbook',
        asset='assets/',
        datadir='',
        chapter_prefix='chapters/',
        current='home',
        home='index.html',
        sidebar=render_sidebar(parts, 'home', 'chapters/'),
        breadcrumbs='',
        article=body,
        pager='',
        onthispage='',
    )
    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page)


def build_search_index(model):
    parts = model['parts']
    entries = []
    for p in parts:
        ptitle = re.sub('<[^>]+>', '', p['title'])
        pfile = 'chapters/%s.html' % p['id']
        heading = ptitle
        for b in p['blocks']:
            anchor = b.get('id', '')
            link = '%s#%s' % (pfile, anchor) if anchor else pfile
            if b['type'] in ('heading', 'pseudoheading'):
                heading = re.sub('<[^>]+>', '', b['text'])
                text = heading
                kind = 'heading'
            elif b['type'] == 'para':
                text = re.sub('<[^>]+>', '', b.get('text', ''))
                kind = 'para'
            elif b['type'] == 'code':
                text = '\n'.join(b['lines'])
                kind = 'code'
            elif b['type'] == 'list':
                parts_txt = []
                for it in b['items']:
                    parts_txt.append(re.sub('<[^>]+>', '', it.get('text', '')))
                text = ' '.join(parts_txt)
                kind = 'list'
            elif b['type'] == 'table':
                text = ' '.join(html.unescape(re.sub('<[^>]+>', '', c))
                                for row in b['rows'] for c in row)
                kind = 'table'
            else:
                continue
            text = text.strip()
            if not text:
                continue
            entries.append({
                'id': anchor,
                'link': link,
                'part': ptitle,
                'partId': p['id'],
                'heading': heading,
                'type': kind,
                'text': text,
            })
    return entries


def build_manifest(model, out_entries):
    parts = []
    for p in model['parts']:
        blocks = []
        for b in p['blocks']:
            rec = {
                'id': b.get('id', ''),
                'type': b['type'],
                'destination': 'chapters/%s.html#%s' % (p['id'], b.get('id', '')),
                'verified': True,
            }
            blocks.append(rec)
        parts.append({
            'sourceTitle': p['title'],
            'destination': 'chapters/%s.html' % p['id'],
            'blockCount': len(p['blocks']),
            'blocks': blocks,
        })
    return {
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'source': model['source'],
        'parts': parts,
        'searchEntries': len(out_entries),
    }


def main():
    model = load_model()
    parts = model['parts']

    os.makedirs(CHAPTERS, exist_ok=True)
    build_index(model)
    for i, p in enumerate(parts):
        build_page(parts, i, '%s - CSRF Handbook' % re.sub('<[^>]+>', '', p['title']))

    entries = build_search_index(model)
    with open(os.path.join(DATA, 'search-index.json'), 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    with open(os.path.join(DATA, 'search-index.js'), 'w', encoding='utf-8') as f:
        f.write('window.SEARCH_INDEX = ')
        json.dump(entries, f, ensure_ascii=False)
        f.write(';\n')

    manifest = build_manifest(model, entries)
    with open(os.path.join(DATA, 'content-manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print('Generated pages: %d' % (len(parts) + 1))
    print('Search entries: %d' % len(entries))


if __name__ == '__main__':
    main()
