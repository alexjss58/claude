import copy, json
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR, MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_MARKER_STYLE, XL_LABEL_POSITION
from lxml import etree

prs = Presentation('deck.pptx')
s3, s6, s7 = prs.slides[2], prs.slides[5], prs.slides[6]
INK, GREY, LINE, PANEL, MAG = '2B2B2B', '606060', 'D9D9E0', 'F1F1F7', 'EC008C'
MJ, MN = 'Segoe UI Semibold', 'Segoe UI'
TC = {'Black': MSO_THEME_COLOR.ACCENT_1, 'Premium': MSO_THEME_COLOR.ACCENT_2, 'Elite': MSO_THEME_COLOR.ACCENT_6}
TCH = {'Black': 'EC008C', 'Premium': '2E41F3', 'Elite': 'D3A08D'}
rgb = lambda h: RGBColor.from_string(h)
C = json.load(open('coef.json'))
PROP = {'Black': 2.0, 'Premium': 2.5, 'Elite': 3.0}
ltv = lambda t, x: (C[t]['base'] + (C[t]['CS3'] if x > 0 else 0) - C[t]['A'] * x / 100) / 1000   # AMD K, x in %
be = {t: (C[t]['base'] + C[t]['CS3']) / C[t]['A'] * 100 for t in C}
XMAX, YMIN, YMAX = 4.0, -40.0, 100.0

def set_text(shape, text):
    tf = shape.text_frame; p = tf.paragraphs[0]
    for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]: r._r.getparent().remove(r._r)
    else: p.add_run().text = text

def tb(slide, x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name='Text', space_after=0):
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h)); box.name = name
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        if space_after: p.space_after = Pt(space_after)
        for t, sz, font, col in para:
            r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.name = font
            if isinstance(col, str): r.font.color.rgb = rgb(col)
            else: r.font.color.theme_color = col
    return box

def footnote(slide, text):
    fn3 = next(sh for sh in s3.shapes if sh.name == '4. Footnote')
    el = copy.deepcopy(fn3._element)
    for cd in el.xpath('.//p:custDataLst'): cd.getparent().remove(cd)
    slide.shapes._spTree.append(el)
    fn = slide.shapes[-1]; fn.top = Emu(6420640); fn.width = Emu(11082528)
    set_text(fn, text)

def drop(slide, pred):
    for sh in list(slide.shapes):
        if pred(sh): sh._element.getparent().remove(sh._element)

# ===================================================== slide 6
set_text(next(sh for sh in s6.shapes if sh.name == 'Title 3'), 'Debit cards proposal: set target cashback rates at 2% / 2.5% / 3% for Black / Premium / Elite')
set_text(next(sh for sh in s6.shapes if sh.name == 'Subtitle 1'), f'All three tiers stay profitable over 3 years; break-even is at {be["Black"]:.1f}% for Black and ~{be["Premium"]:.1f}% for Premium and Elite')

chart_shape = next(sh for sh in s6.shapes if sh.has_chart)
fx, fy, fw, fh = chart_shape.left, chart_shape.top, chart_shape.width, chart_shape.height
# old hand-drawn axis, proposal lines and placeholder labels go; legend connectors 175-177 + labels stay
drop(s6, lambda sh: sh.name in {f'Straight Connector {i}' for i in list(range(154, 166)) + [172, 173, 174]}
                    or sh.name in ('TextBox 123', 'TextBox 178', 'TextBox 180'))

# chart data: tier lines (Elite clipped at the top of the axis), proposal verticals, proposal points, break-even points
cd = XyChartData()
for t in ('Black', 'Premium', 'Elite'):
    s = cd.add_series(t)
    x0 = 0.0
    if ltv(t, 0) > YMAX:  # enter the plot where the line crosses the top of the axis
        x0 = (C[t]['base'] + C[t]['CS3'] - YMAX * 1000) / C[t]['A'] * 100
    for x in [x0, XMAX]: s.add_data_point(x, ltv(t, x))
for t in ('Black', 'Premium', 'Elite'):
    s = cd.add_series(f'{t} proposed level'); s.add_data_point(PROP[t], YMIN); s.add_data_point(PROP[t], YMAX)
for t in ('Black', 'Premium', 'Elite'):
    s = cd.add_series(f'{t} at proposal'); s.add_data_point(PROP[t], ltv(t, PROP[t]))
s = cd.add_series('Break-even')
for t in ('Black', 'Premium', 'Elite'): s.add_data_point(be[t], 0)
ch = chart_shape.chart
ch.replace_data(cd)

ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart', 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
sers = list(ch.plots[0].series)
def line_fmt(se, theme=None, hexcol=None, w=25400, dash=None, none=False):
    ln = se.format.line
    if none: ln.fill.background(); return
    ln.width = Emu(w)
    if theme is not None: ln.color.theme_color = theme
    else: ln.color.rgb = rgb(hexcol)
    if dash: ln.dash_style = dash
for i, t in enumerate(('Black', 'Premium', 'Elite')):
    se = sers[i]; line_fmt(se, TC[t], w=28575); se.marker.style = XL_MARKER_STYLE.NONE; se.smooth = False
    v = sers[3 + i]; line_fmt(v, TC[t], w=9525, dash=MSO_LINE_DASH_STYLE.DASH); v.marker.style = XL_MARKER_STYLE.NONE; v.smooth = False
    p = sers[6 + i]; line_fmt(p, none=True)
    p.marker.style = XL_MARKER_STYLE.CIRCLE; p.marker.size = 9
    p.marker.format.fill.solid(); p.marker.format.fill.fore_color.theme_color = TC[t]
    p.marker.format.line.color.rgb = rgb('FFFFFF'); p.marker.format.line.width = Emu(12700)
b = sers[9]; line_fmt(b, none=True)
b.marker.style = XL_MARKER_STYLE.CIRCLE; b.marker.size = 8
b.marker.format.fill.solid(); b.marker.format.fill.fore_color.rgb = rgb('FFFFFF')
b.marker.format.line.color.rgb = rgb(INK); b.marker.format.line.width = Emu(12700)

# axes: x 0-4 %, y -40..100 K, labels low, light gridlines
cs = ch._chartSpace
axes = cs.findall('.//c:valAx', ns)
def ax_set(ax, mn, mx, major, fmt, pos_low=True, grid=False):
    sc = ax.find('c:scaling', ns)
    for tag in ('max', 'min'):
        el = sc.find(f'c:{tag}', ns)
        if el is not None: sc.remove(el)
    etree.SubElement(sc, f'{{{ns["c"]}}}max').set('val', str(mx)); etree.SubElement(sc, f'{{{ns["c"]}}}min').set('val', str(mn))
    # order inside scaling: orientation, max, min — orientation first already
    mu = ax.find('c:majorUnit', ns)
    if mu is None: mu = etree.SubElement(ax, f'{{{ns["c"]}}}majorUnit')
    mu.set('val', str(major))
    nf = ax.find('c:numFmt', ns)
    if nf is None:
        nf = etree.Element(f'{{{ns["c"]}}}numFmt'); ax.find('c:axPos', ns).addnext(nf)
    nf.set('formatCode', fmt); nf.set('sourceLinked', '0')
    tl = ax.find('c:tickLblPos', ns)
    if tl is not None and pos_low: tl.set('val', 'low')
    mg = ax.find('c:majorGridlines', ns)
    if grid and mg is None:
        mg = etree.Element(f'{{{ns["c"]}}}majorGridlines'); ax.find('c:axPos', ns).addnext(mg)
    if mg is not None and not grid: ax.remove(mg)
    if grid:
        for ch_ in list(mg): mg.remove(ch_)
        mg.append(etree.fromstring(f'<c:spPr xmlns:c="{ns["c"]}" xmlns:a="{ns["a"]}"><a:ln w="6350"><a:solidFill><a:srgbClr val="{LINE}"/></a:solidFill></a:ln></c:spPr>'))
xax = next(a for a in axes if a.find('c:axPos', ns).get('val') in ('b', 't'))
yax = next(a for a in axes if a.find('c:axPos', ns).get('val') in ('l', 'r'))
ax_set(xax, 0, XMAX, 0.5, '0.0"%"')
ax_set(yax, YMIN, YMAX, 20, '#,##0"K";−#,##0"K";0', grid=True)
for ax in (xax, yax):   # axis text: Segoe UI 11pt grey
    tx = ax.find('c:txPr', ns)
    if tx is not None: ax.remove(tx)
    tx = etree.fromstring(f'<c:txPr xmlns:c="{ns["c"]}" xmlns:a="{ns["a"]}"><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1100"><a:solidFill><a:srgbClr val="{GREY}"/></a:solidFill><a:latin typeface="Segoe UI"/></a:defRPr></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>')
    anchor = ax.find('c:crossAx', ns); anchor.addprevious(tx)
# no chart legend (the slide carries its own)
lg = cs.find('.//c:legend', ns)
if lg is not None: lg.getparent().remove(lg)

# plot geometry from the chart's manual inner layout, to place labels
lay = cs.find('.//c:plotArea/c:layout/c:manualLayout', ns)
g = {k: float(lay.find(f'c:{k}', ns).get('val')) for k in ('x', 'y', 'w', 'h')}
PX0, PY0 = fx + g['x'] * fw, fy + g['y'] * fh
PW_, PH_ = g['w'] * fw, g['h'] * fh
X = lambda v: int(PX0 + v / XMAX * PW_)
Y = lambda v: int(PY0 + (YMAX - v) / (YMAX - YMIN) * PH_)

# labels at the proposal points and break-evens
for t, dy in (('Black', -300000), ('Premium', -300000), ('Elite', 90000)):
    v = ltv(t, PROP[t])
    tb(s6, X(PROP[t]) + 70000, Y(v) + dy, 900000, 200000, [[(f'{v:,.0f}K', 12, MJ, TCH[t])]], name='Point label')
tb(s6, X(be['Black']) - 950000, Y(0) + 60000, 900000, 190000, [[(f'break-even {be["Black"]:.1f}%', 10, MN, GREY)]], align=PP_ALIGN.RIGHT, name='Break-even label')
tb(s6, X(be['Premium']) + 90000, Y(0) + 60000, 1100000, 190000, [[(f'{be["Premium"]:.1f}%', 10, MN, GREY)]], name='Break-even label')
tb(s6, X(XMAX) - 1700000, Y(YMAX) + 40000, 1650000, 190000, [[(f'Elite starts at {ltv("Elite", 0):,.0f}K at 0%', 10, MN, GREY)]], align=PP_ALIGN.RIGHT, name='Clip note')
tb(s6, X(PROP['Black']) - 600000, Y(YMAX) - 260000, 3000000, 200000, [[('Proposed levels', 11, MJ, GREY)]], align=PP_ALIGN.LEFT, name='Proposed label')
# axis titles: y stays (TextBox 125), x title under the axis
tb(s6, int(PX0), fy + fh + 30000, int(PW_), 220000, [[('Target cashback rate on eligible spend', 12, MN, GREY)]], align=PP_ALIGN.CENTER, name='X title')
yt = next(sh for sh in s6.shapes if sh.name == 'TextBox 125')
set_text(yt, '3-year LTV per card, AMD')
for r in yt.text_frame.paragraphs[0].runs: r.font.size = Pt(12); r.font.bold = False; r.font.name = MJ

# left message column (replaces TextBox 180; same place and width)
LX, LW = 554735, 3350000
tb(s6, LX, 1500000, LW, 700000, [[('We can afford at most ~3% target cashback', 18, MJ, '000000')]], name='Lead')
tb(s6, LX, 2230000, LW, 480000, [[(f'3-year LTV per card turns negative above {be["Black"]:.1f}% (Black) and {be["Premium"]:.1f}% (Premium, Elite)', 12, MN, INK)]], name='Support')
tb(s6, LX, 2950000, LW, 300000, [[('To differentiate tiers, we propose', 14, MJ, '000000')]], name='Lead')
yy = 3330000
for t in ('Black', 'Premium', 'Elite'):
    tb(s6, LX, yy, 1000000, 400000, [[(f'{PROP[t]:g}%', 24, MJ, TCH[t])]], name='Rate')
    tb(s6, LX + 1050000, yy + 90000, 2300000, 300000, [[(t, 14, MJ, INK), (f'  ·  LTV {ltv(t, PROP[t]):,.0f}K AMD', 12, MN, GREY)]], name='Tier')
    yy += 480000
tb(s6, LX, yy + 80000, LW, 480000, [[('Communicated to clients as the cashback rate for all payments', 12, MN, INK)]], name='Support')
footnote(s6, 'Source: debit cards model v14 (ArCa in Free), active-clients profile; LTV = 3-year operating profit per card, 2027–29, at the proposed fees (Black 4,000, Premium 12,000, Elite 90,000 AMD a year), no deposit uplift. Eligible spend = non-cash ÷3 / ÷2.1 / ÷1.7. Partly based on end-2025 data; update pending')

# ===================================================== slide 7
set_text(next(sh for sh in s7.shapes if sh.name == 'Subtitle 1'), 'Open questions for the shareholders and data we still need')
drop(s7, lambda sh: sh.name in ('TextBox 4', 'TextBox 5', 'TextBox 8'))
dep = {t: C[t]['D3'] / 100 for t in C}                      # AMD per card over 3 years per 1 p.p. of uplift
room = {t: ltv(t, PROP[t]) * 1000 / dep[t] for t in C}      # p.p. of uplift the proposed LTV could fund
QX, QW = 554736, 7100000
tb(s7, QX, 1480000, QW, 250000, [[('DECISIONS NEEDED', 10, MJ, GREY)]], name='Sub hdr')
qs = [
  ('1', 'Do we differentiate deposit rates by tier?',
   f'Fast Bank already pays the market’s top 1-year AMD rate (10.0% vs a peer median of 8.05%). At the proposed cashback, the 3-year LTV per card would fund only about {room["Black"]:.1f} / {room["Premium"]:.1f} / {room["Elite"]:.2f} p.p. of deposit uplift for Black / Premium / Elite.'),
  ('2', 'If yes, which P&L funds the uplift: deposits or cards?',
   'Deposit margin is 1.25 p.p.: an uplift above it loses money on the deposit itself, so the card P&L would have to carry the difference.'),
  ('3', 'Long term: model client response to the new card terms',
   'Add behaviour effects to the model: extra spend (TPV) from cashback and extra deposit volume from any uplift. Today both are held flat.'),
]
qy = 1830000
for n, lead, sup in qs:
    ov = s7.shapes.add_shape(MSO_SHAPE.OVAL, Emu(QX), Emu(qy), Emu(330000), Emu(330000)); ov.name = 'Num'
    ov.fill.solid(); ov.fill.fore_color.rgb = rgb(MAG); ov.line.fill.background(); ov.shadow.inherit = False
    tf = ov.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = n
    r.font.size = Pt(13); r.font.name = MJ; r.font.color.rgb = rgb('FFFFFF'); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tb(s7, QX + 500000, qy + 20000, QW - 500000, 300000, [[(lead, 15, MJ, '000000')]], name='Q lead')
    tb(s7, QX + 500000, qy + 380000, QW - 500000, 700000, [[(sup, 12, MN, INK)]], name='Q support')
    qy += 1330000
    if n != '3':
        c = s7.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(QX), Emu(qy - 170000), Emu(QX + QW), Emu(qy - 170000))
        c.name = 'Row line'; c.line.color.rgb = rgb(LINE); c.line.width = Emu(6350)
# right panel: data pending (keeps TextBox 7 heading)
pan = next(sh for sh in s7.shapes if sh.name == 'Gfx')
px, pw = pan.left + 245763, pan.width - 491526
items = [
  ('2026 card transactions', 'Replace the end-2025 inputs with 2026 year-to-date card data'),
  ('Spend by merchant category per tier', 'Eligible share of non-cash is set at 1/3, 1/2.1 and 1/1.7; data would confirm it (sample suggests 27% for Black)'),
  ('Cardholders’ deposit balances by tier', 'Needed to cost a tiered deposit rate'),
  ('Client response to cashback and rates', 'Spend and deposit uplift from comparable launches, for the long-term view'),
]
iy = 1943113
for lead, sup in items:
    tb(s7, px, iy, pw, 260000, [[(lead, 13, MJ, INK)]], name='Ctx lead')
    tb(s7, px, iy + 280000, pw, 560000, [[(sup, 11, MN, INK)]], name='Ctx support')
    iy += 1000000
footnote(s7, 'Source: debit cards model v14 (ArCa in Free), active-clients profile; deposit rates from fininfo.am and bank pages, 29 Sep 2026 (1m AMD, 12 months)')
prs.save('debit_slides_s6-7.pptx'); print('saved', be, {t: round(ltv(t, PROP[t]), 1) for t in C}, room)