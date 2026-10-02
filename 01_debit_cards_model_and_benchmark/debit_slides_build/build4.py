import copy
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree

SRC, OUT = 'deck.pptx', 'debit_slides_slide4.pptx'
prs = Presentation(SRC)
s3, s4 = prs.slides[2], prs.slides[3]
INK, GREY, MUTE, LINE, PANEL, MAG = '2B2B2B', '606060', 'B5B5B5', 'D9D9E0', 'F1F1F7', 'EC008C'
MJ, MN = 'Segoe UI Semibold', 'Segoe UI'
rgb = lambda h: RGBColor.from_string(h)

# ---- clear the draft: keep placeholders (title, subtitle, tracker) and the think-cell object
for sh in list(s4.shapes):
    if sh.is_placeholder or sh.shape_type == 7:
        continue
    sh._element.getparent().remove(sh._element)

def ph(idx_name):
    return next(sh for sh in s4.shapes if sh.is_placeholder and sh.name.startswith(idx_name))

def set_text(shape, text):
    tf = shape.text_frame
    p = tf.paragraphs[0]
    for extra in tf.paragraphs[1:]:
        extra._p.getparent().remove(extra._p)
    runs = p.runs
    if runs:
        runs[0].text = text
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    else:
        p.add_run().text = text

set_text(ph('Title'), 'Debit cards proposal: raise Black and Elite service fees to just below the market median')
set_text(ph('Subtitle'), 'Each Fast Bank card is benchmarked against like-for-like cards of six banks¹; annual service fee, AMD')

def tb(x, y, w, h, runs, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name='Text'):
    """runs: list of paragraphs, each a list of (text, size, font, color[, bold])"""
    box = s4.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        for t, sz, font, col in para:
            r = p.add_run(); r.text = t
            r.font.size = Pt(sz); r.font.name = font; r.font.color.rgb = rgb(col)
    return box

def rect(x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, name='Gfx', line=None):
    sp = s4.shapes.add_shape(shape, Emu(x), Emu(y), Emu(w), Emu(h))
    sp.name = name
    sp.fill.solid(); sp.fill.fore_color.rgb = rgb(fill)
    if line: sp.line.color.rgb = rgb(line); sp.line.width = Emu(12700)
    else: sp.line.fill.background()
    sp.shadow.inherit = False
    return sp

def hline(x1, y, x2, col=LINE, w=6350, name='Row line'):
    c = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y), Emu(x2), Emu(y))
    c.name = name; c.line.color.rgb = rgb(col); c.line.width = Emu(w)
    return c

def vline(x, y1, y2, col, w, name='Tick'):
    c = s4.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x), Emu(y1), Emu(x), Emu(y2))
    c.name = name; c.line.color.rgb = rgb(col); c.line.width = Emu(w)
    return c

fmt = lambda v: f'{v:,.0f}'.replace(',', ',')

# ---- data (fees, AMD a year; resident current cards, Sep 2026)
ROWS = [
  ('BLACK', None),
  (dict(card='ArCa Classic', peer='vs 6 ArCa Classic cards', peers=[3500, 5000, 4800, 2500, 1500, 2500], cur=1500, prop=3000), None),
  (dict(card='Visa Classic', peer='vs 11 Visa Classic / MC Standard cards', peers=[4500, 4500, 5000, 5000, 4800, 4800, 3000, 3000, 5000, 5000, 3000], cur=2000, prop=4000), None),
  ('ELITE', None),
  (dict(card='Visa Infinite', peer='vs 5 Visa Infinite / MC World Elite cards', peers=[65000, 120000, 120000, 100000, 99900], cur=50000, prop=90000), None),
  (dict(card='Mastercard World Elite', peer='vs the same 5 Infinite / World Elite cards', peers=[65000, 120000, 120000, 100000, 99900], cur=50000, prop=90000), None),
  (dict(card='Visa Infinite Metal', peer='vs IDBank Visa Infinite Special Edition', peers=[150000], cur=150000, prop=150000), None),
]
def median(a):
    a = sorted(a); n = len(a); return a[n // 2] if n % 2 else (a[n // 2 - 1] + a[n // 2]) / 2

L = 554736
C_CARD, W_CARD = L, 2300000
C_STRIP, W_STRIP = 2950000, 2350000
C_CUR, W_CUR = 5420000, 820000
C_MED, W_MED = 6330000, 900000
C_PRO, W_PRO = 7330000, 1000000
TABLE_R = C_PRO + W_PRO
PX, PW = 8580000, 11637264 - 8580000

TOP = 1950000
hdr = [(C_CARD, W_CARD, 'CARD · PEER GROUP', PP_ALIGN.LEFT), (C_STRIP, W_STRIP, 'PEER FEES', PP_ALIGN.LEFT),
       (C_CUR, W_CUR, 'CURRENT', PP_ALIGN.RIGHT), (C_MED, W_MED, 'PEER MEDIAN', PP_ALIGN.RIGHT), (C_PRO, W_PRO, 'PROPOSED', PP_ALIGN.RIGHT)]
for x, w, t, al in hdr:
    tb(x, TOP, w, 180000, [[(t, 10, MJ, GREY)]], align=al, name='Hdr')
hline(L, TOP + 250000, TABLE_R, col=GREY, w=9525, name='Header line')

y = TOP + 330000
RH, GH = 610000, 300000
for item, _ in ROWS:
    if isinstance(item, str):
        tb(C_CARD, y + 40000, W_CARD, 220000, [[(item, 12, MJ, '000000')]], name='Tier label')
        y += GH
        continue
    d = item
    med = median(d['peers'])
    # card + peer group
    tb(C_CARD, y + 90000, W_CARD, 230000, [[(d['card'], 14, MJ, INK)]], name='Card')
    tb(C_CARD, y + 330000, W_CARD, 200000, [[(d['peer'], 11, MN, GREY)]], name='Peer group')
    # strip: peers (grey dots), median (tick), Fast Bank now (hollow), proposed (magenta diamond)
    allv = d['peers'] + [d['cur'], d['prop']]
    lo, hi = min(allv), max(allv)
    if hi == lo: lo, hi = lo * 0.8, hi * 1.2
    sx0, sx1 = C_STRIP + 60000, C_STRIP + W_STRIP - 60000
    X = lambda v: sx0 + (v - lo) / (hi - lo) * (sx1 - sx0)
    ay = y + 250000
    hline(sx0, ay, sx1, col=LINE, w=9525, name='Strip axis')
    counts = {}
    for v in d['peers']: counts[v] = counts.get(v, 0) + 1
    D = 110000
    for v, k in counts.items():
        dd = D + (k - 1) * 18000
        rect(int(X(v) - dd / 2), int(ay - dd / 2), dd, dd, MUTE, shape=MSO_SHAPE.OVAL, name='Peer dot')
        if k > 1:
            tb(int(X(v) - 150000), ay - 250000, 300000, 130000, [[(f'×{k}', 9, MJ, GREY)]], align=PP_ALIGN.CENTER, name='Count')
    vline(int(X(med)), ay - 110000, ay + 110000, GREY, 19050, name='Median tick')
    if d['cur'] != d['prop']:
        o = rect(int(X(d['cur']) - 62000), int(ay - 62000), 124000, 124000, 'FFFFFF', shape=MSO_SHAPE.OVAL, name='Fast Bank now', line=INK)
    dm = 170000
    rect(int(X(d['prop']) - dm / 2), int(ay - dm / 2), dm, dm, MAG, shape=MSO_SHAPE.DIAMOND, name='Proposed')
    tb(sx0 - 60000, ay + 120000, 900000, 150000, [[(fmt(lo), 9, MN, GREY)]], name='Min')
    tb(sx1 - 840000, ay + 120000, 900000, 150000, [[(fmt(hi), 9, MN, GREY)]], align=PP_ALIGN.RIGHT, name='Max')
    # numbers
    vy = y + 150000
    tb(C_CUR, vy, W_CUR, 280000, [[(fmt(d['cur']), 16, MJ, INK)]], align=PP_ALIGN.RIGHT, name='Current')
    tb(C_MED, vy, W_MED, 280000, [[(fmt(med), 16, MJ, INK)]], align=PP_ALIGN.RIGHT, name='Median')
    if d['prop'] != d['cur']:
        tb(C_PRO, vy, W_PRO, 280000, [[(fmt(d['prop']), 16, MJ, MAG)]], align=PP_ALIGN.RIGHT, name='Proposed fee')
        tb(C_PRO, vy + 290000, W_PRO, 170000, [[(f'×{d["prop"] / d["cur"]:.1f} · {d["prop"] / med - 1:+.0%} vs median'.replace('+0%', 'at median'), 10, MN, GREY)]], align=PP_ALIGN.RIGHT, name='Change')
    else:
        tb(C_PRO, vy, W_PRO, 280000, [[(fmt(d['prop']), 16, MJ, INK)]], align=PP_ALIGN.RIGHT, name='Proposed fee')
        tb(C_PRO, vy + 290000, W_PRO, 170000, [[('keep · at peer level', 10, MN, GREY)]], align=PP_ALIGN.RIGHT, name='Change')
    y += RH
    hline(L, y - 20000, TABLE_R, name='Row line')
TABLE_B = y - 20000

# legend under the table
ly = TABLE_B + 110000
lx = C_STRIP + 60000
rect(lx, ly + 20000, 90000, 90000, MUTE, shape=MSO_SHAPE.OVAL, name='Legend dot')
tb(lx + 140000, ly, 500000, 140000, [[('peer card', 9, MN, GREY)]], name='Legend')
vline(lx + 700000, ly - 5000, ly + 135000, GREY, 19050, name='Legend tick')
tb(lx + 760000, ly, 500000, 140000, [[('median', 9, MN, GREY)]], name='Legend')
rect(lx + 1260000, ly + 15000, 100000, 100000, 'FFFFFF', shape=MSO_SHAPE.OVAL, name='Legend now', line=INK)
tb(lx + 1410000, ly, 600000, 140000, [[('Fast Bank now', 9, MN, GREY)]], name='Legend')
rect(lx + 2090000, ly + 5000, 120000, 120000, MAG, shape=MSO_SHAPE.DIAMOND, name='Legend proposed')
tb(lx + 2260000, ly, 600000, 140000, [[('proposed', 9, MN, GREY)]], name='Legend')

# ---- right panel: what we propose
pan = rect(PX, TOP, PW, TABLE_B - TOP, PANEL, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name='Gfx')
pan.adjustments[0] = 0.04
ix, iw = PX + 190000, PW - 380000
tb(ix, TOP + 150000, iw, 250000, [[('What we propose', 16, MJ, '000000')]], name='Panel title')
items = [
  ('Black: Visa Classic 2,000 → 4,000', INK, 'Doubles the fee, still 800 below the 4,800 peer median'),
  ('Black: ArCa Classic 1,500 → 3,000', INK, 'Priced against ArCa cards only; ArCa peers are cheaper, so 3,000 matches their median rather than 4,000'),
  ('Elite: Infinite and World Elite 50,000 → 90,000', INK, '10% below the 100,000 median of Infinite / World Elite peers'),
  ('Keep Infinite Metal at 150,000', INK, 'Already level with the only comparable card'),
  ('Deposit-based fee waivers stay', MAG, 'Free cards for depositors: 50k+ AMD in deposits on Visa Classic, 50m+ AMD on Elite cards'),
]
iy = TOP + 560000
for lead, col, sup in items:
    tb(ix, iy, iw, 230000, [[(lead, 13, MJ, col)]], name='Ctx lead')
    tb(ix, iy + 235000, iw, 380000, [[(sup, 11, MN, INK)]], name='Ctx support')
    iy += 680000

# ---- footnote: reuse slide 3's footnote shape for style
fn3 = next(sh for sh in s3.shapes if sh.name == '4. Footnote')
el = copy.deepcopy(fn3._element)
s4.shapes._spTree.append(el)
fn = s4.shapes[-1]
fn.top = Emu(6420640)
fn.width = Emu(11082528)
set_text(fn, '1. Current resident cards of Acba, Ameriabank, Ardshinbank, Converse Bank, Evocabank and IDBank at the same card level; non-resident duplicates and special-purpose cards (transfer, co-badge, sticker) excluded. Source: bank tariffs, Sep 2026; Fast Bank card tariff TC 04 01#12')
prs.save(OUT)
print('saved', OUT)