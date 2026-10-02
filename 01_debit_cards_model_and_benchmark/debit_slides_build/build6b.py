import copy, json, math
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR, MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_MARKER_STYLE
from pptx.oxml.ns import qn
from lxml import etree

prs = Presentation('debit_slides_s4_fees.pptx')
s6 = prs.slides[5]
INK, GREY, LINE, MAG = '2B2B2B', '606060', 'D9D9E0', 'EC008C'
MJ, MN = 'Segoe UI Semibold', 'Segoe UI'
TC = {'Black': MSO_THEME_COLOR.ACCENT_1, 'Premium': MSO_THEME_COLOR.ACCENT_2, 'Elite': MSO_THEME_COLOR.ACCENT_6}
TCH = {'Black': 'EC008C', 'Premium': '2E41F3', 'Elite': 'D3A08D'}
rgb = lambda h: RGBColor.from_string(h)
C = json.load(open('coef.json'))
PROP = {'Black': 2.0, 'Premium': 2.5, 'Elite': 3.0}
# today's portfolio (activated cards, avg Oct-Dec 2025; '8 cards model (as is lineup)' rows 8 and 37; tiers as in row 148)
PORT = {'Black': [(11519.67, 2000)], 'Premium': [(17243, 4000), (1862, 12000)], 'Elite': [(995.67, 50000), (183.67, 50000), (110, 150000)]}
FCUR = {t: sum(n * f for n, f in v) / sum(n for n, f in v) for t, v in PORT.items()}
FMOD = {t: C[t]['fee'] for t in C}
K = 0.9 * 3          # 3Y service-fee revenue per AMD of annual fee (paid share 90%, 3 years)
XMIN, XMAX, YMIN, YMAX = 1.5, 4.0, 0.5, 2.0
def x_be(t, m):      # cashback % at which the 3Y LTV is zero when the fee is m x today's average
    return (C[t]['base'] + C[t]['CS3'] - K * (FMOD[t] - m * FCUR[t])) / C[t]['A'] * 100
def m_be(t, x):      # fee multiple needed to break even at cashback x %
    return (FMOD[t] - (C[t]['base'] + C[t]['CS3'] - C[t]['A'] * x / 100) / K) / FCUR[t]

def set_text(shape, text):
    tf = shape.text_frame; p = tf.paragraphs[0]
    for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]: r._r.getparent().remove(r._r)
    else: p.add_run().text = text
def tb(x, y, w, h, paras, align=PP_ALIGN.LEFT, name='Text'):
    box = s6.shapes.add_textbox(Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h))); box.name = name
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        for t, sz, font, col in para:
            r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.name = font; r.font.color.rgb = rgb(col)
    return box

# title as in the user's current version
title = next(sh for sh in s6.shapes if sh.name == 'Title 3')
set_text(title, 'Debit cards proposal:')
title.text_frame.paragraphs[0].runs[0].text = 'Debit cards proposal:\v2% | 2.5% | 3% cashback for Black | Premium | Elite'
sub = next(sh for sh in s6.shapes if sh.name == 'Subtitle 1')
set_text(sub, ''); sub.top = Emu(1050000)

# remove the LTV-specific labels and the left column (rebuilt below)
for sh in list(s6.shapes):
    if sh.name in ('Point label', 'Break-even label', 'Clip note', 'Proposed label', 'X title', 'Lead', 'Support', 'Rate', 'Tier'):
        sh._element.getparent().remove(sh._element)

chart_shape = next(sh for sh in s6.shapes if sh.has_chart)
fx, fy, fw, fh = chart_shape.left, chart_shape.top, chart_shape.width, chart_shape.height
cd = XyChartData()
ms = [YMIN * (YMAX / YMIN) ** (i / 60) for i in range(61)]
for t in ('Black', 'Premium', 'Elite'):
    s = cd.add_series(t)
    for m in ms:
        x = x_be(t, m)
        if XMIN - 1e-9 <= x <= XMAX + 1e-9: s.add_data_point(x, m)
for t in ('Black', 'Premium', 'Elite'):
    s = cd.add_series(f'{t} proposed level'); s.add_data_point(PROP[t], YMIN); s.add_data_point(PROP[t], YMAX)
s = cd.add_series('Break-even at the proposed level')
for t in ('Premium', 'Elite'): s.add_data_point(PROP[t], m_be(t, PROP[t]))
s = cd.add_series('Break-even at today’s fee')
for t in ('Black', 'Premium', 'Elite'): s.add_data_point(x_be(t, 1.0), 1.0)
ch = chart_shape.chart
ch.replace_data(cd)
ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
sers = list(ch.plots[0].series)
for i, t in enumerate(('Black', 'Premium', 'Elite')):
    se = sers[i]; se.format.line.width = Emu(28575); se.format.line.color.theme_color = TC[t]; se.marker.style = XL_MARKER_STYLE.NONE; se.smooth = True
    v = sers[3 + i]; v.format.line.width = Emu(9525); v.format.line.color.theme_color = TC[t]; v.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    v.marker.style = XL_MARKER_STYLE.NONE; v.smooth = False
for j, (se, fill, line) in enumerate(((sers[6], INK, 'FFFFFF'), (sers[7], 'FFFFFF', INK))):
    se.format.line.fill.background(); se.smooth = False
    se.marker.style = XL_MARKER_STYLE.CIRCLE; se.marker.size = 8
    se.marker.format.fill.solid(); se.marker.format.fill.fore_color.rgb = rgb(fill)
    se.marker.format.line.color.rgb = rgb(line); se.marker.format.line.width = Emu(12700)

cs = ch._chartSpace
axes = cs.findall('.//c:valAx', ns)
xax = next(a for a in axes if a.find('c:axPos', ns).get('val') in ('b', 't'))
yax = next(a for a in axes if a.find('c:axPos', ns).get('val') in ('l', 'r'))
def scaling(ax, mn, mx, log=None):
    sc = ax.find('c:scaling', ns)
    for tag in ('logBase', 'max', 'min'):
        el = sc.find(f'c:{tag}', ns)
        if el is not None: sc.remove(el)
    if log: sc.insert(0, etree.fromstring(f'<c:logBase xmlns:c="{ns["c"]}" val="{log}"/>'))
    etree.SubElement(sc, qn('c:max')).set('val', str(mx)); etree.SubElement(sc, qn('c:min')).set('val', str(mn))
def crossing(ax, val):
    for tag in ('crosses', 'crossesAt'):
        el = ax.find(f'c:{tag}', ns)
        if el is not None: ax.remove(el)
    el = etree.Element(qn('c:crossesAt')); el.set('val', str(val)); ax.find('c:crossAx', ns).addnext(el)
scaling(xax, XMIN, XMAX); scaling(yax, YMIN, YMAX, log=2)
crossing(xax, 1)          # the x axis runs through 1X, the middle of the chart
crossing(yax, XMIN)
xax.find('c:numFmt', ns).set('formatCode', '0.0"%"'); yax.find('c:numFmt', ns).set('formatCode', '0.0"X"')
mu = yax.find('c:majorUnit', ns)
if mu is not None: yax.remove(mu)    # log axis: one gridline per doubling (0.5X, 1X, 2X)
xax.find('c:majorUnit', ns).set('val', '0.5')
# x axis line at 1X in dark ink so the middle reads as "today"
sp = xax.find('c:spPr', ns)
if sp is not None: xax.remove(sp)
xax.find('c:tickLblPos', ns).addnext(etree.fromstring(f'<c:spPr xmlns:c="{ns["c"]}" xmlns:a="{ns["a"]}"><a:ln w="12700"><a:solidFill><a:srgbClr val="{INK}"/></a:solidFill></a:ln></c:spPr>'))

lay = cs.find('.//c:plotArea/c:layout/c:manualLayout', ns)
g = {k: float(lay.find(f'c:{k}', ns).get('val')) for k in ('x', 'y', 'w', 'h')}
PX0, PY0, PW_, PH_ = fx + g['x'] * fw, fy + g['y'] * fh, g['w'] * fw, g['h'] * fh
X = lambda v: int(PX0 + (v - XMIN) / (XMAX - XMIN) * PW_)
Y = lambda m: int(PY0 + (math.log2(YMAX) - math.log2(m)) / (math.log2(YMAX) - math.log2(YMIN)) * PH_)

# labels: break-even multiple at the proposed level, and max cashback at today's fee
mB = m_be('Black', PROP['Black'])
tb(X(PROP['Black']) - 1250000, Y(YMIN) - 420000, 1200000, 380000, [[('Black at 2%: profitable at any fee ≥ 0.5X', 10, MJ, TCH['Black'])]], align=PP_ALIGN.RIGHT, name='Point label')
for t, dx, dy in (('Premium', 90000, -60000), ('Elite', 90000, -60000)):
    m = m_be(t, PROP[t])
    tb(X(PROP[t]) + dx, Y(m) + dy, 1100000, 200000, [[(f'≥ {m:.1f}X', 12, MJ, TCH[t])]], name='Point label')
tb(X(x_be('Black', 1)) - 800000, Y(1) + 70000, 1600000, 190000,
   [[(f'at today’s fees: {x_be("Premium", 1):.1f}–{x_be("Elite", 1):.1f}%', 10, MN, GREY)]], align=PP_ALIGN.CENTER, name='Today label')
tb(X(XMAX) - 1500000, Y(YMAX) + 40000, 1450000, 200000, [[('Profitable ↑', 10, MJ, GREY)]], align=PP_ALIGN.RIGHT, name='Zone label')
tb(X(XMAX) - 1500000, Y(YMIN) - 240000, 1450000, 200000, [[('Loss-making ↓', 10, MJ, GREY)]], align=PP_ALIGN.RIGHT, name='Zone label')
tb(X(PROP['Black']) - 600000, Y(YMAX) - 260000, 3000000, 200000, [[('Proposed target cashback levels', 11, MJ, GREY)]], name='Proposed label')
tb(int(PX0), fy + fh + 30000, int(PW_), 220000, [[('Target cashback rate on eligible spend', 12, MN, GREY)]], align=PP_ALIGN.CENTER, name='X title')
yt = next(sh for sh in s6.shapes if sh.name == 'TextBox 125')
set_text(yt, 'Service fee at break-even, × today’s average fee in the tier'); yt.width = Emu(5200000)
for r in yt.text_frame.paragraphs[0].runs: r.font.size = Pt(12); r.font.bold = False; r.font.name = MJ

# left column
LX, LW = 554735, 3350000
tb(LX, 1500000, LW, 700000, [[(f'At today’s fees, ~{min(x_be(t, 1) for t in C):.1f}–{max(x_be(t, 1) for t in C):.1f}% cashback breaks even', 18, MJ, '000000')]], name='Lead')
tb(LX, 2250000, LW, 700000, [[('Each line is the fee level at which the tier’s 3-year LTV per card is zero; above it the tier makes money. 1X = today’s average fee (Black 2,000 · Premium 4,780 · Elite 58,533 AMD)', 11, MN, INK)]], name='Support')
tb(LX, 3100000, LW, 300000, [[('To differentiate tiers, we propose', 14, MJ, '000000')]], name='Lead')
yy = 3470000
need = {'Black': 'profitable at any fee', 'Premium': f'fee ≥ {m_be("Premium", 2.5):.1f}X today', 'Elite': f'fee ≥ {m_be("Elite", 3.0):.1f}X today'}
for t in ('Black', 'Premium', 'Elite'):
    tb(LX, yy, 1000000, 400000, [[(f'{PROP[t]:g}%', 24, MJ, TCH[t])]], name='Rate')
    tb(LX + 1050000, yy + 90000, 2300000, 300000, [[(t, 14, MJ, INK), (f'  ·  {need[t]}', 12, MN, GREY)]], name='Tier')
    yy += 480000
tb(LX, yy + 80000, LW, 480000, [[('Communicated to clients as the cashback rate for all payments', 12, MN, INK)]], name='Support')

fn = next(sh for sh in s6.shapes if sh.name == '4. Footnote')
set_text(fn, 'Source: debit cards model v14 (ArCa in Free), active-clients profile; break-even = 3-year operating profit per card 2027–29 of zero, 90% of cards paying the fee, no deposit uplift. Today’s average fee: activated cards Oct–Dec 2025 at current tariffs. Model fees 4,000 / 12,000 / 90,000 AMD = 2.0X / 2.5X / 1.5X. Partly based on end-2025 data; update pending')
prs.save('debit_slides_s4_s6.pptx')
print('FCUR', {t: round(v) for t, v in FCUR.items()}, 'x at 1X', {t: round(x_be(t, 1), 2) for t in C}, 'm at prop', {t: round(m_be(t, PROP[t]), 2) for t in C},
      'x range', {t: (round(x_be(t, .5), 2), round(x_be(t, 2), 2)) for t in C})