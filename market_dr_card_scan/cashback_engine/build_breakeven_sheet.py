"""Add a live 'Break-even curves' sheet (table + scatter chart) after the Control panel.

    python3 build_breakeven_sheet.py <model.xlsx> <out.xlsx>

For each paid tier the sheet finds the combinations of cashback target (% of eligible spend, Control panel
D42 / D65 / D88) and deposit rate uplift (p.p., D44 / D67 / D90) at which the 3-year operating profit per card
(2027-2029, Control panel N49 / N72 / N95) equals a target (0 = break-even). In the tier P&L both levers are pure
costs, so the break-even set is a straight line:

    OP(x, y) = OP before cashback and uplift + cap saving - x * A - y * B
    A = 3Y cashback cost per 1.00 of target   = (3Y cashback + 3Y cap saving) / current target
    B = 3Y deposit uplift cost per 1.00 p.p.  = sum of the deposited amount per card, 2027-2029

Everything is read live from the model, so the lines move when fees, balances, OpEx or the client profile change.
The deposit margin (input) is drawn as a dashed horizontal line. The file is edited at XML level (no openpyxl
round trip); calcChain is dropped and fullCalcOnLoad set, so Excel recalculates on open.
"""
import copy
import re
import sys
import zipfile

from lxml import etree

SRC, OUT = sys.argv[1:3]
NAME = 'Break-even curves'
AFTER = 'Control panel'
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'
CTN = '{http://schemas.openxmlformats.org/package/2006/content-types}'
X = lambda b: etree.fromstring(b)                                                          # noqa: E731
S = lambda e: etree.tostring(e, xml_declaration=True, encoding='UTF-8', standalone=True)   # noqa: E731
TM = "'4 tiers model (to be lineup)'!"
CP = "'Control panel'!"
Q = "'%s'!" % NAME

z = zipfile.ZipFile(SRC)
parts = {n: z.read(n) for n in z.namelist()}

# ------------------------------------------------------------------ styles (reuse the Control panel's, add a few)
st = X(parts['xl/styles.xml'])
xfs = st.find(N + 'cellXfs')
numfmts = st.find(N + 'numFmts')
fmt_red = max(int(n.get('numFmtId')) for n in numfmts) + 1
etree.SubElement(numfmts, N + 'numFmt', numFmtId=str(fmt_red), formatCode='0.00%;[Red]\\-0.00%')
numfmts.set('count', str(len(numfmts)))


def clone(base, fmt=None, align=None):
    x = copy.deepcopy(xfs[base])
    if fmt is not None:
        x.set('numFmtId', str(fmt)); x.set('applyNumberFormat', '1')
    if align:
        for a in x.findall(N + 'alignment'):
            x.remove(a)
        etree.SubElement(x, N + 'alignment', horizontal=align); x.set('applyAlignment', '1')
    xfs.append(x)
    return len(xfs) - 1


TITLE, NOTE, NOTE_I, HDR, LBL, IN_AMD, IN_PCT, NUM = 282, 827, 829, 815, 360, 808, 811, 809
PCT = clone(NUM, 10, 'right')
PCT_RED = clone(NUM, fmt_red, 'right')
PCT_B = clone(TITLE, 10, 'right')
NUM_B = clone(TITLE, 165)
LBL_B = clone(TITLE)
RATIO = clone(NUM, 2, 'right')
IN_RATIO = clone(IN_AMD, 2)
TXT_R = clone(LBL, None, 'right')
HDR_R = clone(HDR, None, 'right')
xfs.set('count', str(len(xfs)))
parts['xl/styles.xml'] = S(st)

# ------------------------------------------------------------------ cells
cells = {}          # ref -> (kind, value, style); kind: t text, f formula, n number


def t(ref, v, s=LBL): cells[ref] = ('t', v, s)          # noqa: E704
def f(ref, v, s=NUM): cells[ref] = ('f', v, s)          # noqa: E704
def n(ref, v, s=IN_AMD): cells[ref] = ('n', v, s)       # noqa: E704


T = dict(C=dict(x='D42', y='D44', src='D45', op='N49', cb='N43', dep='N44', nc=97, cs=138, dp=130, div=3),
         D=dict(x='D65', y='D67', src='D68', op='N72', cb='N66', dep='N67', nc=174, cs=215, dp=207, div=2.1),
         E=dict(x='D88', y='D90', src='D91', op='N95', cb='N89', dep='N90', nc=251, cs=292, dp=284, div=1.7))

t('B2', 'BREAK-EVEN LINES: CASHBACK vs DEPOSIT RATE UPLIFT', TITLE)
t('B3', "Each line joins the cashback targets (% of eligible spend) and deposit rate uplifts (p.p.) at which the tier's "
        "3-year operating profit per card (2027-2029) equals the target in row 7. Below the line: more profit.", NOTE)
t('B4', 'Everything comes live from the model: change fees, balances, OpEx or the client profile on the Control panel '
        'and the lines move. The dashed line is the deposit margin.', NOTE)
t('B6', 'Per card, 3 years 2027-2029, AMD', HDR)
for c, nm in zip('CDE', ['Black', 'Premium', 'Elite']):
    t(c + '6', nm, HDR_R)
t('F6', 'Source / note', HDR)

t('B7', 'Target 3Y operating profit per card')
t('B8', 'Deposit margin, p.p.')
t('F7', 'Input. 0 = break-even; e.g. 10,000 draws the line for that profit', NOTE)
n('C8', 0.0125, IN_PCT)
t('F8', 'Input, one value for all tiers; dashed line on the chart', NOTE)

t('B10', 'From the model (live)', NOTE_I)
rows = [(11, 'Cashback target now, % of eligible spend', PCT, lambda d: CP + '$' + d['x'][0] + '$' + d['x'][1:], 'Control panel D42 / D65 / D88'),
        (12, 'Deposit rate uplift now, p.p.', PCT, lambda d: CP + '$' + d['y'][0] + '$' + d['y'][1:], 'Control panel D44 / D67 / D90'),
        (13, 'P&L cashback source', TXT_R, lambda d: CP + '$' + d['src'][0] + '$' + d['src'][1:], 'Needs "Target"; with "Engine" the lines are only approximate'),
        (14, '3Y operating profit now', NUM, lambda d: CP + '$' + d['op'][0] + '$' + d['op'][1:], 'Control panel N49 / N72 / N95'),
        (15, '3Y cashback cost now', NUM, lambda d: CP + '$' + d['cb'][0] + '$' + d['cb'][1:], 'Control panel N43 / N66 / N89'),
        (16, '3Y deposit uplift cost now', NUM, lambda d: CP + '$' + d['dep'][0] + '$' + d['dep'][1:], 'Control panel N44 / N67 / N90'),
        (17, '3Y cashback saved by the cap now', NUM,
         lambda d: f"{TM}$I${d['cs']}+{TM}$J${d['cs']}+{TM}$K${d['cs']}", '4 tiers model rows 138 / 215 / 292; fixed once the target is above 0'),
        (19, '3Y non-cash spend per card', NUM,
         lambda d: f"SUM({TM}$E${d['nc']}:$H${d['nc']})+{TM}$J${d['nc']}+{TM}$K${d['nc']}", '4 tiers model rows 97 / 174 / 251 (2027 quarters, 2028, 2029)'),
        (20, '3Y deposited amount per card (sum of yearly balances)', NUM,
         lambda d: f"{TM}$I${d['dp']}+{TM}$J${d['dp']}+{TM}$K${d['dp']}", '4 tiers model rows 130 / 207 / 284')]
for r, label, s, fx, note in rows:
    t(f'B{r}', label)
    for c, d in T.items():
        f(f'{c}{r}', fx(d), s)
    t(f'F{r}', note, NOTE)
t('B18', '3Y operating profit before cashback and uplift', LBL_B)
t('F18', 'Rows 14 + 15 + 16', NOTE)

t('B22', 'Trade-off', NOTE_I)
t('B23', 'Cost of +1 p.p. cashback target')
t('F23', 'AMD per card over 3 years', NOTE)
t('B24', 'Cost of +1 p.p. deposit rate uplift')
t('F24', 'AMD per card over 3 years', NOTE)
t('B25', '1 p.p. of cashback costs as much as ... p.p. of uplift')
t('B26', 'Eligible to non-cash divisor used by the P&L')
t('F26', 'Read off the model (the rate rows divide the target by it)', NOTE)
t('B27', 'Divisor if the cashback target is 0')
t('F27', 'Input. Used only when the Control panel target is 0', NOTE)

t('B29', 'Break-even: 3Y operating profit = target', NOTE_I)
t('B30', 'Cashback target with no deposit uplift', LBL_B)
t('B31', 'Deposit uplift with no cashback', LBL_B)
t('B32', 'Max deposit uplift at the current cashback target')
t('F32', 'Red = already above the line', NOTE)
t('B33', 'Max cashback target at the current deposit uplift')
t('B34', 'Max cashback target with uplift at the deposit margin')
t('F34', 'Where the line crosses the dashed deposit-margin line', NOTE)
t('B35', 'Headroom: 3Y operating profit now minus target')

for c, d in T.items():
    f(f'{c}18', f'{c}14+{c}15+{c}16', NUM_B)
    n(f'{c}7', 0)
    n(f'{c}27', d['div'], IN_RATIO)
    f(f'{c}23', f'IF({c}11>0,({c}15+{c}17)/{c}11,{c}19/{c}27)/100')
    f(f'{c}24', f'{c}20/100')
    f(f'{c}25', f'{c}23/{c}24', RATIO)
    f(f'{c}26', f'IF({c}11>0,{c}19/({c}23*100),{c}27)', RATIO)
    f(f'{c}30', f'IF({c}18-{c}7<=0,"not reachable",({c}18+{c}17-{c}7)/({c}23*100))', PCT_B)
    f(f'{c}31', f'IF({c}18-{c}7<=0,"not reachable",({c}18-{c}7)/({c}24*100))', PCT_B)
    f(f'{c}32', f'({c}18+IF({c}11>0,{c}17,0)-{c}7-{c}23*100*{c}11)/({c}24*100)', PCT_RED)
    f(f'{c}33', f'({c}18+{c}17-{c}7-{c}24*100*{c}12)/({c}23*100)', PCT_RED)
    f(f'{c}34', f'({c}18+{c}17-{c}7-{c}24*100*$C$8)/({c}23*100)', PCT_RED)
    f(f'{c}35', f'{c}14-{c}7')

# grid: max deposit uplift by cashback target
t('B37', 'Max deposit uplift (p.p.) keeping 3Y operating profit at the target, by cashback target', NOTE_I)
t('B38', 'Cashback target, % of eligible spend', HDR)
for c, nm in zip('CDE', ['Black', 'Premium', 'Elite']):
    t(c + '38', nm, HDR_R)
for i, r in enumerate(range(39, 48)):
    n(f'B{r}', round(i * 0.005, 4), IN_PCT)
    for c in 'CDE':
        f(f'{c}{r}', f'({c}$18+IF($B{r}>0,{c}$17,0)-{c}$7-{c}$23*100*$B{r})/({c}$24*100)', PCT_RED)
t('F39', 'Input column: change the cashback steps if needed', NOTE)

# chart data
t('B49', 'Chart data', NOTE_I)
t('B50', 'Series point', HDR)
t('C50', 'Cashback', HDR_R)
t('D50', 'Uplift', HDR_R)
r = 51
series = []
for c, nm in zip('CDE', ['Black', 'Premium', 'Elite']):
    t(f'B{r}', f'{nm}: no uplift'); f(f'C{r}', f'IF(ISNUMBER({c}30),{c}30,NA())', PCT); f(f'D{r}', f'IF(ISNUMBER({c}30),0,NA())', PCT)
    t(f'B{r + 1}', f'{nm}: no cashback'); f(f'C{r + 1}', f'IF(ISNUMBER({c}31),0,NA())', PCT); f(f'D{r + 1}', f'IF(ISNUMBER({c}31),{c}31,NA())', PCT)
    t(f'B{r + 2}', f'{nm}: now'); f(f'C{r + 2}', f'{c}11', PCT); f(f'D{r + 2}', f'{c}12', PCT)
    series.append((c, nm, r))
    r += 3
t('B60', 'Deposit margin: start'); f('C60', '0', PCT); f('D60', '$C$8', PCT)
t('B61', 'Deposit margin: end'); f('C61', 'CEILING(MAX(C30:E30,C11:E11,0.01)*1.08,0.005)/1.06', PCT); f('D61', '$C$8', PCT)
f('B62', '"Deposit margin "&TEXT($C$8*100,"0.00")&" p.p."', LBL)
for c, nm, r0 in series:
    t(f'F{r0 + 2}', f'{nm} now', NOTE)


# ------------------------------------------------------------------ sheet XML
def col_idx(ref):
    letters = re.match(r'[A-Z]+', ref).group(0)
    v = 0
    for ch in letters:
        v = v * 26 + ord(ch) - 64
    return v


ws = etree.Element(N + 'worksheet', nsmap={None: M, 'r': RNS})
pr = etree.SubElement(ws, N + 'sheetPr'); etree.SubElement(pr, N + 'tabColor', rgb='FFC00000')
etree.SubElement(pr, N + 'pageSetUpPr', fitToPage='1')
etree.SubElement(ws, N + 'dimension', ref='B2:F62')
svs = etree.SubElement(ws, N + 'sheetViews')
etree.SubElement(svs, N + 'sheetView', showGridLines='0', zoomScale='100', workbookViewId='0')
etree.SubElement(ws, N + 'sheetFormatPr', baseColWidth='10', defaultRowHeight='16')
cols = etree.SubElement(ws, N + 'cols')
for a, b, w in [(1, 1, 3), (2, 2, 52), (3, 5, 13), (6, 6, 60)]:
    etree.SubElement(cols, N + 'col', min=str(a), max=str(b), width=str(w), customWidth='1')
sd = etree.SubElement(ws, N + 'sheetData')
byrow = {}
for ref, v in cells.items():
    byrow.setdefault(int(re.search(r'\d+', ref).group(0)), []).append((ref, v))
for rn in sorted(byrow):
    row = etree.SubElement(sd, N + 'row', r=str(rn))
    for ref, (kind, val, s) in sorted(byrow[rn], key=lambda kv: col_idx(kv[0])):
        c = etree.SubElement(row, N + 'c', r=ref, s=str(s))
        if kind == 't':
            c.set('t', 'inlineStr')
            etree.SubElement(etree.SubElement(c, N + 'is'), N + 't').text = val
        elif kind == 'f':
            etree.SubElement(c, N + 'f').text = val
        else:
            etree.SubElement(c, N + 'v').text = repr(val)
etree.SubElement(ws, N + 'pageMargins', left='0.4', right='0.4', top='0.5', bottom='0.5', header='0.3', footer='0.3')
etree.SubElement(ws, N + 'pageSetup', paperSize='9', orientation='landscape', fitToWidth='1', fitToHeight='1')
etree.SubElement(ws, N + 'drawing', {'{%s}id' % RNS: 'rId1'})

# ------------------------------------------------------------------ chart
C_NS = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
A_NS = 'http://schemas.openxmlformats.org/drawingml/2006/main'
COL = {'Black': '262626', 'Premium': 'BF8F00', 'Elite': '2E75B6'}


def rich(text, sz=1000, b=0, rot=None):
    bp = f'<a:bodyPr rot="{rot}" vert="horz"/>' if rot else '<a:bodyPr/>'
    return (f'<c:tx><c:rich>{bp}<a:lstStyle/><a:p><a:pPr><a:defRPr sz="{sz}" b="{b}"/></a:pPr>'
            f'<a:r><a:rPr lang="en-US" sz="{sz}" b="{b}"/><a:t>{text}</a:t></a:r></a:p></c:rich></c:tx>')


def ser(i, name_ref, xr, yr, color, line=True, dash=None, marker=None, w=28575, label=None):
    ln = (f'<a:ln w="{w}" cap="rnd"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
          + (f'<a:prstDash val="{dash}"/>' if dash else '') + '<a:round/></a:ln>') if line else '<a:ln w="19050"><a:noFill/></a:ln>'
    mk = ('<c:marker><c:symbol val="none"/></c:marker>' if not marker else
          f'<c:marker><c:symbol val="{marker}"/><c:size val="10"/><c:spPr><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
          f'<a:ln w="12700"><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill></a:ln></c:spPr></c:marker>')
    dl = ('' if not label else
          f'<c:dLbls><c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr><c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr>'
          f'<a:defRPr sz="900" b="1"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:defRPr></a:pPr>'
          f'<a:endParaRPr lang="en-US"/></a:p></c:txPr><c:dLblPos val="{label}"/><c:showLegendKey val="0"/><c:showVal val="0"/>'
          f'<c:showCatName val="0"/><c:showSerName val="1"/><c:showPercent val="0"/><c:showBubbleSize val="0"/></c:dLbls>')
    return (f'<c:ser><c:idx val="{i}"/><c:order val="{i}"/><c:tx><c:strRef><c:f>{name_ref}</c:f></c:strRef></c:tx>'
            f'<c:spPr>{ln}</c:spPr>{mk}{dl}'
            f'<c:xVal><c:numRef><c:f>{xr}</c:f></c:numRef></c:xVal><c:yVal><c:numRef><c:f>{yr}</c:f></c:numRef></c:yVal>'
            f'<c:smooth val="0"/></c:ser>')


sers, i = [], 0
for c, nm, r0 in series:
    sers.append(ser(i, f"{Q}${c}$6", f"{Q}$C${r0}:$C${r0 + 1}", f"{Q}$D${r0}:$D${r0 + 1}", COL[nm])); i += 1
for c, nm, r0 in series:
    sers.append(ser(i, f"{Q}$F${r0 + 2}", f"{Q}$C${r0 + 2}", f"{Q}$D${r0 + 2}", COL[nm], line=False, marker='circle',
                    label='r' if nm == 'Premium' else 't')); i += 1
sers.append(ser(i, f"{Q}$B$62", f"{Q}$C$60:$C$61", f"{Q}$D$60:$D$61", 'C00000', dash='dash', w=19050))

axis_txt = ('<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="900"><a:solidFill><a:srgbClr val="595959"/>'
            '</a:solidFill></a:defRPr></a:pPr><a:endParaRPr lang="en-US"/></a:p></c:txPr>')
axis_ln = '<c:spPr><a:ln w="9525"><a:solidFill><a:srgbClr val="BFBFBF"/></a:solidFill></a:ln></c:spPr>'
chart = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         f'<c:chartSpace xmlns:c="{C_NS}" xmlns:a="{A_NS}" xmlns:r="{RNS}"><c:roundedCorners val="0"/><c:chart>'
         f'<c:title>{rich("Break-even: 3Y operating profit per card = target", 1200, 1)}<c:overlay val="0"/></c:title>'
         f'<c:autoTitleDeleted val="0"/><c:plotArea><c:layout/>'
         f'<c:scatterChart><c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>{"".join(sers)}'
         f'<c:axId val="500000001"/><c:axId val="500000002"/></c:scatterChart>'
         f'<c:valAx><c:axId val="500000001"/><c:scaling><c:orientation val="minMax"/><c:min val="0"/></c:scaling>'
         f'<c:delete val="0"/><c:axPos val="b"/><c:title>{rich("Cashback target, % of eligible spend")}<c:overlay val="0"/></c:title>'
         f'<c:numFmt formatCode="0.0%" sourceLinked="0"/><c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
         f'<c:tickLblPos val="nextTo"/>{axis_ln}{axis_txt}<c:crossAx val="500000002"/><c:crosses val="autoZero"/>'
         f'<c:crossBetween val="midCat"/></c:valAx>'
         f'<c:valAx><c:axId val="500000002"/><c:scaling><c:orientation val="minMax"/><c:min val="0"/></c:scaling>'
         f'<c:delete val="0"/><c:axPos val="l"/><c:majorGridlines><c:spPr><a:ln w="9525"><a:solidFill><a:srgbClr val="E7E6E6"/>'
         f'</a:solidFill></a:ln></c:spPr></c:majorGridlines>'
         f'<c:title>{rich("Deposit rate uplift, p.p.", rot="-5400000")}<c:overlay val="0"/></c:title>'
         f'<c:numFmt formatCode="0.0%" sourceLinked="0"/><c:majorTickMark val="out"/><c:minorTickMark val="none"/>'
         f'<c:tickLblPos val="nextTo"/>{axis_ln}{axis_txt}<c:crossAx val="500000001"/><c:crosses val="autoZero"/>'
         f'<c:crossBetween val="midCat"/></c:valAx></c:plotArea>'
         f'<c:legend><c:legendPos val="b"/><c:overlay val="0"/>{axis_txt}</c:legend><c:plotVisOnly val="1"/>'
         f'<c:dispBlanksAs val="gap"/></c:chart>'
         f'<c:spPr><a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr></c:chartSpace>')

XDR = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
drawing = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<xdr:wsDr xmlns:xdr="{XDR}" xmlns:a="{A_NS}"><xdr:twoCellAnchor editAs="oneCell">'
           f'<xdr:from><xdr:col>6</xdr:col><xdr:colOff>152400</xdr:colOff><xdr:row>5</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from>'
           f'<xdr:to><xdr:col>17</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>35</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:to>'
           f'<xdr:graphicFrame macro=""><xdr:nvGraphicFramePr><xdr:cNvPr id="2" name="Break-even chart"/><xdr:cNvGraphicFramePr/>'
           f'</xdr:nvGraphicFramePr><xdr:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/></xdr:xfrm><a:graphic>'
           f'<a:graphicData uri="{C_NS}"><c:chart xmlns:c="{C_NS}" xmlns:r="{RNS}" r:id="rId1"/></a:graphicData></a:graphic>'
           f'</xdr:graphicFrame><xdr:clientData/></xdr:twoCellAnchor></xdr:wsDr>')


def rels(target, typ):
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/'
            f'package/2006/relationships"><Relationship Id="rId1" Type="{RNS}/{typ}" Target="{target}"/></Relationships>').encode()


existing = [p for p in parts if re.match(r'xl/worksheets/sheet\d+\.xml$', p)]
k_sheet = max(int(re.search(r'(\d+)\.xml', p).group(1)) for p in existing) + 1
k_draw = max([int(m.group(1)) for p in parts for m in [re.match(r'xl/drawings/drawing(\d+)\.xml$', p)] if m] + [0]) + 1
k_chart = max([int(m.group(1)) for p in parts for m in [re.match(r'xl/charts/chart(\d+)\.xml$', p)] if m] + [0]) + 1
sheet_part = f'xl/worksheets/sheet{k_sheet}.xml'
parts[sheet_part] = S(ws)
parts[f'xl/worksheets/_rels/sheet{k_sheet}.xml.rels'] = rels(f'../drawings/drawing{k_draw}.xml', 'drawing')
parts[f'xl/drawings/drawing{k_draw}.xml'] = drawing.encode()
parts[f'xl/drawings/_rels/drawing{k_draw}.xml.rels'] = rels(f'../charts/chart{k_chart}.xml', 'chart')
parts[f'xl/charts/chart{k_chart}.xml'] = chart.encode()

# ------------------------------------------------------------------ register the sheet
wb = X(parts['xl/workbook.xml'])
wrels = X(parts['xl/_rels/workbook.xml.rels'])
sheets = wb.find(N + 'sheets')
rid = 'rId%d' % (max(int(r.get('Id')[3:]) for r in wrels) + 1)
etree.SubElement(wrels, PKG + 'Relationship', Id=rid, Type=RNS + '/worksheet', Target=f'worksheets/sheet{k_sheet}.xml')
anchor = [s for s in sheets if s.get('name') == AFTER][0]
pos = list(sheets).index(anchor) + 1
el = etree.Element(N + 'sheet'); el.set('name', NAME)
el.set('sheetId', str(max(int(s.get('sheetId')) for s in sheets) + 1)); el.set('{%s}id' % RNS, rid)
anchor.addnext(el)
dn = wb.find(N + 'definedNames')
for d in (dn if dn is not None else []):
    if d.get('localSheetId') is not None and int(d.get('localSheetId')) >= pos:
        d.set('localSheetId', str(int(d.get('localSheetId')) + 1))
for v in wb.find(N + 'bookViews'):
    for a in ('activeTab', 'firstSheet'):
        if v.get(a) and int(v.get(a)) >= pos:
            v.set(a, str(int(v.get(a)) + 1))
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
for r in list(wrels):
    if 'calcChain' in r.get('Target'):
        wrels.remove(r)
parts.pop('xl/calcChain.xml', None)
parts['xl/workbook.xml'] = S(wb)
parts['xl/_rels/workbook.xml.rels'] = S(wrels)

ct = X(parts['[Content_Types].xml'])
for o in list(ct):
    if o.get('PartName') == '/xl/calcChain.xml':
        ct.remove(o)
for part, typ in [(sheet_part, 'spreadsheetml.worksheet+xml'), (f'xl/drawings/drawing{k_draw}.xml', 'drawing+xml'),
                  (f'xl/charts/chart{k_chart}.xml', 'drawingml.chart+xml')]:
    etree.SubElement(ct, CTN + 'Override', PartName='/' + part, ContentType='application/vnd.openxmlformats-officedocument.' + typ)
parts['[Content_Types].xml'] = S(ct)

app = parts['docProps/app.xml'].decode('utf-8')
app = re.sub(r'(<vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1), app)
app = re.sub(r'<TitlesOfParts><vt:vector size="(\d+)"', lambda m: f'<TitlesOfParts><vt:vector size="{int(m.group(1)) + 1}"', app)
app = app.replace(f'<vt:lpstr>{AFTER}</vt:lpstr>', f'<vt:lpstr>{AFTER}</vt:lpstr><vt:lpstr>{NAME}</vt:lpstr>', 1)
parts['docProps/app.xml'] = app.encode('utf-8')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as out:
    for name in z.namelist():
        if name in parts:
            out.writestr(name, parts[name])
    for name in parts:
        if name not in z.namelist():
            out.writestr(name, parts[name])
print('wrote', OUT, '| sheet', sheet_part, '| drawing', k_draw, '| chart', k_chart, '| position', pos)
