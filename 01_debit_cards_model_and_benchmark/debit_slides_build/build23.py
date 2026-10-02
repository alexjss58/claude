import copy, json
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
prs = Presentation('base.pptx')
s3, sl = prs.slides[2], prs.slides[3]
T = json.load(open('tiers.json'))
INK, GREY, LINE, BAND, MAG, MAGSOFT, NEUSOFT = '2B2B2B', '606060', 'D9D9E0', 'F1F1F7', 'EC008C', 'FCE4F1', 'ECECEC'
MJ, MN = 'Segoe UI Semibold', 'Segoe UI'
rgb = lambda h: RGBColor.from_string(h)
fmt = lambda v: 'Free' if v == 0 else f'{v:,.0f}'

for sh in list(sl.shapes):
    if sh.is_placeholder or sh.shape_type == 7: continue
    sh._element.getparent().remove(sh._element)
def set_text(shape, text):
    tf = shape.text_frame; p = tf.paragraphs[0]
    for extra in tf.paragraphs[1:]: extra._p.getparent().remove(extra._p)
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]: r._r.getparent().remove(r._r)
    else: p.add_run().text = text
ph = lambda n: next(sh for sh in sl.shapes if sh.is_placeholder and sh.name.startswith(n))
set_text(ph('Title'), 'Debit cards: Black and Elite service fees are below the market median')
sub = ph('Subtitle'); set_text(sub, 'Potentially increase Black and Elite fees to the market median benchmark while keeping today’s free-service conditions')
sub.top, sub.height = Emu(919250), Emu(246221)

def tb(x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, name='Text'):
    box = sl.shapes.add_textbox(Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h))); box.name = name
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        for t, sz, font, col in para:
            r = p.add_run(); r.text = t; r.font.size = Pt(sz); r.font.name = font; r.font.color.rgb = rgb(col)
    return box
def rect(x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, name='Gfx', line=None):
    sp = sl.shapes.add_shape(shape, Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h))); sp.name = name
    if fill: sp.fill.solid(); sp.fill.fore_color.rgb = rgb(fill)
    else: sp.fill.background()
    if line: sp.line.color.rgb = rgb(line); sp.line.width = Emu(12700)
    else: sp.line.fill.background()
    sp.shadow.inherit = False
    return sp
def hline(x1, y, x2, col=LINE, w=6350, name='Row line'):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(int(x1)), Emu(int(y)), Emu(int(x2)), Emu(int(y))); c.name = name
    c.line.color.rgb = rgb(col); c.line.width = Emu(w); return c
def vline(x, y1, y2, col, w, name='Tick'):
    c = sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(int(x)), Emu(int(y1)), Emu(int(x)), Emu(int(y2))); c.name = name
    c.line.color.rgb = rgb(col); c.line.width = Emu(w); return c
def chip(x, y, text, fill, col):
    w = 110000 + len(text) * 62000
    c = rect(x, y, w, 210000, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, name='Chip'); c.adjustments[0] = 0.5
    tf = c.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = text
    r.font.size = Pt(10); r.font.name = MJ; r.font.color.rgb = rgb(col)
    return c

L, LW = 554736, 1560000
X0 = L + LW; TW = (11637264 - X0) / 4
TIERS = [('free', 'FREE', '5F7388'), ('plus', 'BLACK', '22252A'), ('premium', 'PREMIUM', '9A6F14'), ('elite', 'ELITE', '54467F')]
FBCARDS = {'free': ['Visa_Digital'], 'plus': ['Arca_Classic', 'VISA_Classic'], 'premium': ['VISA_Gold', 'Mastercard_World'],
           'elite': ['VISA_INFINITE', 'Mastercard_World_Elite', 'Visa_Infinite_Metal']}
FBNAMES = {'free': 'Visa Digital', 'plus': 'ArCa Classic, Visa Classic', 'premium': 'Visa Gold, Mastercard World',
           'elite': 'Visa Infinite, MC World Elite, Visa Infinite Metal'}
PAD = 110000
cx = lambda i: X0 + i * TW + PAD
CW = TW - 2 * PAD

# ---- header row
y = 1330000
for i, (tid, name, col) in enumerate(TIERS):
    tb(cx(i), y, CW, 220000, [[(name, 14, MJ, col)]], name='Tier')
    tb(cx(i), y + 230000, CW, 330000, [[('Fast Bank: ' + FBNAMES[tid], 10, MN, GREY)]], name='Tier cards')
    hline(X0 + i * TW + 30000, y + 600000, X0 + (i + 1) * TW - 30000, col=col, w=19050, name='Tier line')
y += 640000

def band(y, text):
    rect(L, y, 11637264 - L, 230000, BAND, name='Band')
    tb(L + 90000, y + 45000, 4000000, 150000, [[(text, 10, MJ, GREY)]], name='Band label')
    return y + 230000
def label(y, t1, t2=None):
    tb(L, y + 90000, LW - 100000, 230000, [[(t1, 12, MJ, INK)]], name='Row label')
    if t2: tb(L, y + 330000, LW - 100000, 420000, [[(t2, 10, MN, GREY)]], name='Row sub')

# ---- cards on offer
y = band(y, 'CARDS')
label(y, 'Cards on offer')
for i, (tid, _, _) in enumerate(TIERS):
    t = T[tid]; n = len(FBCARDS[tid])
    tb(cx(i), y + 70000, CW, 230000, [[(str(n), 16, MJ, MAG), (f'   market median {t["cnt_med"]:g} per bank (range {t["cnt_rng"][0]}–{t["cnt_rng"][1]})', 10, MN, GREY)]], name='Count')
    ch_w, ch_h = 560000, 355000
    for j, c in enumerate(FBCARDS[tid]):
        sl.shapes.add_picture(f'card_{c}.png', Emu(int(cx(i) + j * (ch_w + 70000))), Emu(int(y + 360000)), Emu(ch_w), Emu(ch_h))
y += 800000
hline(L, y, 11637264)

# ---- annual service fee
y = band(y, 'SERVICE COST')
RY = y; RH = 1620000
label(y, 'Annual service fee', 'AMD a year; logos = each bank’s average across its cards in the tier')
MED_TARGET = {'plus', 'elite'}
LOGO = 185000
for i, (tid, _, _) in enumerate(TIERS):
    t = T[tid]; x = cx(i)
    rng = [f[1] for f in t['fb']]
    head = [(fmt(t['fbv']), 18, MJ, MAG)]
    if len(set(rng)) > 1: head.append((f'   range {fmt(min(rng))}–{fmt(max(rng))}', 10, MN, GREY))
    tb(x, y + 60000, CW, 300000, [head], name='FB fee')
    below = t['fbv'] < t['md'] - 1e-9
    if tid in MED_TARGET: chip(x, y + 390000, 'Below market median', MAGSOFT, MAG)
    elif below: chip(x, y + 390000, 'Below median', NEUSOFT, GREY)
    else: chip(x, y + 390000, 'At median', NEUSOFT, GREY)
    # strip with bank logos
    vals = list(t['bank_avg'].values()) + [t['fbv'], t['mn'], t['mx']]
    lo, hi = min(vals), max(vals)
    sx0, sx1 = x + LOGO / 2, x + CW - LOGO / 2
    X = lambda v: sx0 + (v - lo) / (hi - lo) * (sx1 - sx0)
    ay = y + 1010000
    hline(sx0, ay, sx1, col='B5B5B5', w=9525, name='Strip axis')
    lanes = []  # right edge of the last logo in each lane
    for b, v in sorted(t['bank_avg'].items(), key=lambda kv: kv[1]):
        px = X(v)
        k = next((k for k, edge in enumerate(lanes) if px - LOGO / 2 >= edge + 15000), len(lanes))
        if k == len(lanes): lanes.append(-10**12)
        lanes[k] = px + LOGO / 2
        if k: vline(px, ay - k * (LOGO + 30000) + LOGO / 2, ay, 'B5B5B5', 6350, name='Stem')
        sl.shapes.add_picture(f'logos/L_{b}.png', Emu(int(px - LOGO / 2)), Emu(int(ay - LOGO / 2 - k * (LOGO + 30000))), Emu(LOGO), Emu(LOGO))
    vline(X(t['md']), ay - 130000, ay + 130000, INK, 19050, name='Median tick')
    dm = 170000
    rect(X(t['fbv']) - dm / 2, ay - dm / 2, dm, dm, MAG, shape=MSO_SHAPE.DIAMOND, name='Fast Bank')
    tb(sx0 - LOGO / 2, ay + 150000, 900000, 150000, [[(fmt(lo), 9, MN, GREY)]], name='Min')
    tb(sx1 + LOGO / 2 - 900000, ay + 150000, 900000, 150000, [[(fmt(hi), 9, MN, GREY)]], align=PP_ALIGN.RIGHT, name='Max')
    tb(x, ay + 320000, CW, 170000, [[('min ', 10, MN, GREY), (fmt(t['mn']), 10, MJ, INK), ('  ·  median ', 10, MN, GREY), (fmt(t['md']), 10, MJ, INK),
                                       ('  ·  max ', 10, MN, GREY), (fmt(t['mx']), 10, MJ, INK), (f'   ({t["mk_n"]} cards)', 10, MN, GREY)]], name='Stats')
    if tid in MED_TARGET:
        tb(x, ay + 520000, CW, 180000, [[(f'→ potentially increase fee to the {fmt(t["md"])} median benchmark', 10, MJ, MAG)]], name='Message')
y += RH
hline(L, y, 11637264)

# ---- free-service conditions (today, keep)
y = band(y, 'FREE SERVICE TODAY: KEEP AS IS')
label(y, 'Card free when…', 'Fast Bank tariff TC 04 01#12, effective 26 Jun 2026')
COND = {'free': [('No service fee', INK)],
        'plus': [('Deposits / bonds¹ of 50,000–5m AMD', INK), ('ArCa Classic also free when ordered in the app (offer to 30 Sep 2026, one card)', GREY)],
        'premium': [('Visa Gold: deposits / bonds¹ of 5–20m AMD', INK), ('Mastercard World: 20–50m AMD', INK)],
        'elite': [('Visa Infinite, MC World Elite: deposits / bonds¹ of 50–100m AMD', INK), ('Infinite Metal: not in the deposit schedule', GREY)]}
for i, (tid, _, _) in enumerate(TIERS):
    t = T[tid]; x = cx(i)
    paras = [[(txt, 11, MJ if col == INK else MN, col)] for txt, col in COND[tid]]
    tb(x, y + 80000, CW, 560000, paras, name='Condition')
    w_, n_ = t['waiv']
    mk = 'Market: no paid cards' if n_ == 0 else f'Market: fee can be waived on {w_} of {n_} paid cards ({w_ / n_:.0%})'
    tb(x, y + 700000, CW, 170000, [[(mk, 10, MN, GREY)]], name='Market waiver')
y += 900000
hline(L, y, 11637264)
TABLE_B = y
# legend
ly = TABLE_B + 70000
lx = X0 + PAD
rect(lx, ly + 10000, 120000, 120000, MAG, shape=MSO_SHAPE.DIAMOND, name='Legend FB')
tb(lx + 170000, ly, 900000, 140000, [[('Fast Bank (median of its cards)', 9, MN, GREY)]], name='Legend')
vline(lx + 2100000, ly - 5000, ly + 135000, INK, 19050, name='Legend tick')
tb(lx + 2160000, ly, 1500000, 140000, [[('market median (all cards)', 9, MN, GREY)]], name='Legend')
sl.shapes.add_picture('logos/L_Acba.png', Emu(int(lx + 3700000)), Emu(int(ly - 5000)), Emu(140000), Emu(140000))
tb(lx + 3890000, ly, 3000000, 140000, [[('bank’s average fee in the tier', 9, MN, GREY)]], name='Legend')

# footnote (style from slide 3)
fn3 = next(sh for sh in s3.shapes if sh.name == '4. Footnote')
el = copy.deepcopy(fn3._element)
for cd in el.xpath('.//p:custDataLst'): cd.getparent().remove(cd)
sl.shapes._spTree.append(el)
fn = sl.shapes[-1]; fn.top = Emu(6420640); fn.width = Emu(11082528)
set_text(fn, '1. Deposits / bonds with a contractual term of 181+ days, total across currencies when applying for the card; one free card per client for the card’s validity, a lower-tier card on request. Market: current cards of Acba, Ameriabank, Ardshinbank, Converse Bank, Evocabank and IDBank (tariffs, Sep 2026), placed in tiers by card level')
prs.save('debit_slides_s4_fees.pptx'); print('saved; table bottom', TABLE_B)