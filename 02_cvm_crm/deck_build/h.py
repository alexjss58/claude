"""Slide helpers in the debit_slides design system (Segoe UI, magenta / blue / navy, grey panels, thin row lines)."""
import copy
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

MAG, BLUE, NAVY, GREY, TAN, INK = 'EC008C', '2E41F3', '202A7D', '606060', 'D3A08D', '2B2B2B'
LINE, PANEL, WHITE, LIGHT = 'D9D9E0', 'F1F1F7', 'FFFFFF', 'B8B8C4'
PINK = 'FDE6F2'
MJ, MN = 'Segoe UI Semibold', 'Segoe UI'
L, CW = 554736, 11082528
R = L + CW
FOOT_BOTTOM = 6581511
rgb = RGBColor.from_string
AL = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}
AN = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}


def r(text, size=11, bold=False, color=INK):
    return (text, size, MJ if bold else MN, color)


def _strip_style(sh):
    st = sh._element.find(qn('p:style'))
    if st is not None:
        sh._element.remove(st)


def _bullet(p, char='•', mar=171450):
    pPr = p._p.get_or_add_pPr()
    pPr.set('marL', str(mar)); pPr.set('indent', str(-mar))
    for tag in ('a:buNone', 'a:buChar', 'a:buFont'):
        el = pPr.find(qn(tag))
        if el is not None:
            pPr.remove(el)
    bf = etree.SubElement(pPr, qn('a:buFont')); bf.set('typeface', 'Arial')
    bc = etree.SubElement(pPr, qn('a:buChar')); bc.set('char', char)


def fill_tf(tf, paras, align='l', anchor='t'):
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = AN[anchor]
    first = True
    for para in paras:
        if isinstance(para, dict):
            runs = para['runs']; opt = para
        else:
            runs = para; opt = {}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = AL[opt.get('align', align)]
        if opt.get('bullet'):
            _bullet(p, opt.get('char', '•'), opt.get('mar', 171450))
        if 'after' in opt:
            p.space_after = Pt(opt['after'])
        if 'before' in opt:
            p.space_before = Pt(opt['before'])
        for t, sz, font, col in runs:
            rr = p.add_run(); rr.text = t
            rr.font.size = Pt(sz); rr.font.name = font; rr.font.color.rgb = rgb(col)
            rr.font.bold = False


def tb(s, x, y, w, h, paras, align='l', anchor='t', name='Text'):
    box = s.shapes.add_textbox(Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h)))
    box.name = name
    fill_tf(box.text_frame, paras, align, anchor)
    return box


def rect(s, x, y, w, h, fill=PANEL, line=None, lw=9525, shape='rect', radius=0.04, name='Gfx', dash=False):
    kind = {'rect': MSO_SHAPE.RECTANGLE, 'round': MSO_SHAPE.ROUNDED_RECTANGLE, 'ellipse': MSO_SHAPE.OVAL,
            'chevron': MSO_SHAPE.CHEVRON, 'pentagon': MSO_SHAPE.PENTAGON, 'diamond': MSO_SHAPE.DIAMOND}[shape]
    sh = s.shapes.add_shape(kind, Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h)))
    _strip_style(sh); sh.name = name
    if shape == 'round':
        sh.adjustments[0] = radius
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = rgb(line); sh.line.width = Emu(lw)
        if dash:
            from pptx.enum.dml import MSO_LINE_DASH_STYLE
            sh.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    else:
        sh.line.fill.background()
    return sh


def shape_text(sh, paras, align='c', anchor='m', margins=(0, 0, 0, 0)):
    tf = sh.text_frame
    fill_tf(tf, paras, align, anchor)
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = [Emu(m) for m in margins]
    return sh


def hline(s, x, y, w, color=LINE, lw=6350, name='Row line'):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(int(x)), Emu(int(y)), Emu(int(x + w)), Emu(int(y)))
    _strip_style(c); c.name = name
    c.line.color.rgb = rgb(color); c.line.width = Emu(lw)
    return c


def vline(s, x, y, h, color=LINE, lw=6350, name='Col line', dash=False):
    c = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(int(x)), Emu(int(y)), Emu(int(x)), Emu(int(y + h)))
    _strip_style(c); c.name = name
    c.line.color.rgb = rgb(color); c.line.width = Emu(lw)
    if dash:
        from pptx.enum.dml import MSO_LINE_DASH_STYLE
        c.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    return c


def num(s, x, y, text, d=290000, fill=MAG, color=WHITE, size=11, name='Number'):
    sh = rect(s, x, y, d, d, fill=fill, shape='ellipse', name=name)
    shape_text(sh, [[r(str(text), size, True, color)]])
    return sh


def chip(s, x, y, w, h, text, fill=PANEL, color=INK, size=10, bold=False, line=None, name='Chip', align='c'):
    sh = rect(s, x, y, w, h, fill=fill, line=line, shape='round', radius=0.3, name=name)
    shape_text(sh, [[r(text, size, bold, color)]], align=align, margins=(45720, 0, 45720, 0))
    return sh


def band(s, x, y, w, text, color=GREY, size=9, h=160000, align='l', name='Band label'):
    return tb(s, x, y, w, h, [[r(text.upper(), size, True, color)]], align=align, name=name)


def footnote(s, lines, w=CW):
    h = 123111 * len(lines)
    box = tb(s, L, FOOT_BOTTOM - h, w, h, [[r(t, 8, False, INK)] for t in lines], anchor='b', name='4. Footnote')
    return box


def set_text(shape, text):
    tf = shape.text_frame; p = tf.paragraphs[0]
    for extra in tf.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    if p.runs:
        p.runs[0].text = text
        for rr in p.runs[1:]:
            rr._r.getparent().remove(rr._r)
    else:
        p.add_run().text = text


def new_slide(prs, title, subtitle=None, tracker=None):
    lay = next(l for l in prs.slide_layouts if l.name == 'Default')
    s = prs.slides.add_slide(lay)
    for ph in list(s.placeholders):
        idx = ph.placeholder_format.idx
        if idx == 0:
            ph.text_frame.text = title
            ph.name = 'Title 3'
        elif idx == 1:
            if subtitle:
                ph.text_frame.text = subtitle; ph.name = 'Subtitle 1'
            else:
                ph._element.getparent().remove(ph._element)
        elif idx == 10:
            if tracker:
                ph.text_frame.text = tracker; ph.name = 'Tracker'
            else:
                ph._element.getparent().remove(ph._element)
    return s
