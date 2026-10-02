"""v16.1 patch on top of build_v16.py output (Alex's review, 30.09.2026).

    python3 build_v16b.py <v16_raw.xlsx> <out.xlsx>

* FX: rating orientation flipped (place 1 = best for clients = thinnest margin); margin measured vs the CBA official rate;
  new capture parameter (share of the quoted margin that shows up as card FX income); controls sit in each tier's rows
  (Control panel rows 15-18 / 38-41 / 61-64 / 84-87 plus row 28 / 51 / 74 / 97); the block at rows 99-111 is removed.
* Cashback eligible-spend divisors (4 tiers model rows 136 / 213 / 290) now = the engine's eligible share for the new tiers.
"""
import re
import sys

from lxml import etree

from xmlbook import N, S, X, Book

IN, OUT = sys.argv[1:3]
book = Book(IN)
P = book.parts
EC = "'8 cards model (as is lineup)'"
FXR = "'FX ranking'"
ROWS = 96907
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
sty = X(P['xl/styles.xml'])
NX = len(sty.find(N + 'cellXfs'))
S_DEC2, S_INT_IN = NX - 2, NX - 1                      # added by build_v16.py
S_HDR, S_SUB, S_LBL, S_NUM, S_NOTE, S_TIER = 896, 904, 894, 900, 891, 898
S_PCT, S_PCT_IN, S_INT = 810, 811, 807


def f(sh, ref, formula, s=None):
    sh.f(ref, formula, s if s is not None else sh.style(ref))


def t(sh, ref, txt, s=None):
    sh.t(ref, txt, s if s is not None else sh.style(ref))


def val(sh, ref, v, s=None):
    c = sh.cell(ref)
    sh._reset(c, s if s is not None else c.get('s'))
    etree.SubElement(c, N + 'v').text = str(int(v)) if float(v).is_integer() else repr(float(v))


def clear(sh, ref):
    c = sh.get(ref)
    if c is not None:
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)



BANKS = [('Amio Bank', 34, 360, 365, 407, 419, 4.20, 4.41), ('AraratBank', 50, 360, 364.5, 405, 417, 4.23, 4.45),
         ('Acba bank', 62, 360.5, 365.5, 407, 417, 4.23, 4.41), ('Ameriabank', 26, 360.5, 365.5, 404.5, 418.5, 4.16, 4.41),
         ('Ardshinbank', 70, 360.5, 365.5, 405, 418, 4.17, 4.50), ('Armeconombank', 52, 360.5, 365.5, 406, 417, 4.22, 4.42),
         ('Evocabank', 16, 360.5, 365.5, 406, 417, 4.22, 4.40), ('ID Bank', 20, 360.5, 365, 405, 416, 4.20, 4.43),
         ('Inecobank', 23, 360.5, 365, 407, 418, 4.17, 4.43), ('Unibank', 57, 360.5, 365, 405, 417, 4.20, 4.45),
         ('ArmSwissBank', 1, 361, 365, 408.5, 415, 4.24, 4.42), ('Artsakhbank', 9, 362, 365.5, 408, 418, 4.18, 4.40),
         ('Byblos Bank Armenia', 5, 361, 366, 406, 418, None, None), ('Converse Bank', 34, 361.5, 365.5, 408, 418, 4.26, 4.47),
         ('Fast Bank', 39, 361, 364.5, 407.5, 416, 4.24, 4.40), ('VTB Bank (Armenia)', 53, 361.5, 365, 408, 413, 4.18, 4.44),
         ('Mellat Bank', 1, None, None, None, None, None, None)]
CBA = {'D': 363.18, 'F': 412.14, 'H': 4.3187}

def ws_xml(cells, widths):
    ws = etree.Element(N + 'worksheet', nsmap={None: N[1:-1], 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'})
    views = etree.SubElement(ws, N + 'sheetViews')
    etree.SubElement(views, N + 'sheetView', showGridLines='0', workbookViewId='0')
    etree.SubElement(ws, N + 'sheetFormatPr', defaultRowHeight='16')
    cl = etree.SubElement(ws, N + 'cols')
    for i, w in widths:
        etree.SubElement(cl, N + 'col', min=str(i), max=str(i), width=str(w), customWidth='1')
    sd = etree.SubElement(ws, N + 'sheetData')
    byrow = {}
    for ref, kind, v, s in cells:
        byrow.setdefault(int(re.search(r'\d+', ref).group()), {})[ref] = (kind, v, s)
    key = lambda ref: (len(re.match('[A-Z]+', ref).group()), re.match('[A-Z]+', ref).group())   # noqa: E731
    for rn in sorted(byrow):
        row = etree.SubElement(sd, N + 'row', r=str(rn))
        for ref in sorted(byrow[rn], key=key):
            kind, v, s = byrow[rn][ref]
            c = etree.SubElement(row, N + 'c', r=ref)
            if s is not None:
                c.set('s', str(s))
            if kind == 't':
                c.set('t', 'inlineStr')
                tt = etree.SubElement(etree.SubElement(c, N + 'is'), N + 't')
                tt.text = v
                tt.set(XML_SPACE, 'preserve')
            elif kind == 'f':
                etree.SubElement(c, N + 'f').text = v
            else:
                etree.SubElement(c, N + 'v').text = str(int(v)) if float(v).is_integer() else repr(float(v))
    etree.SubElement(ws, N + 'pageMargins', left='0.7', right='0.7', top='0.75', bottom='0.75', header='0.3', footer='0.3')
    return S(ws)



# ================================================================ v16.2: FX = one line per tier (margin vs CBA)
CUR = [('USD', 'D', 'E', 'J'), ('EUR', 'F', 'G', 'K'), ('RUB', 'H', 'I', 'L')]
cells = [('B1', 't', "FX MARGIN VS THE CENTRAL BANK RATE – drives the one FX line of each tier on the Control panel (rows 15 / 38 / 61 / 84)", S_HDR),
         ('B2', 't', 'Quotes: rate.am, 30 Sep 2026 14:45 (screenshots from Alex). Buy = the bank buys the currency from the client; sell = the bank '
                     'sells it. Reference: Central Bank of Armenia official rate set on 29 Sep 2026 for 30 Sep 2026 (api.cba.am). Margin = distance of '
                     'the bank\'s rate from the CBA rate, buy and sell sides mixed by row 25, currencies weighted by row 24.', S_NOTE)]
for c, h in zip('BCDEFGHIJKLM', ('Bank', 'Branches', 'USD buy', 'USD sell', 'EUR buy', 'EUR sell', 'RUB buy', 'RUB sell',
                                  'USD margin vs CBA', 'EUR margin vs CBA', 'RUB margin vs CBA', 'Weighted margin vs CBA')):
    cells.append((f'{c}4', 't', h, S_TIER))
for i, row in enumerate(BANKS):
    rn = 5 + i
    cells.append((f'B{rn}', 't', row[0], 892 if row[0] == 'Fast Bank' else S_LBL))
    cells.append((f'C{rn}', 'v', row[1], S_NUM))
    for c, v in zip('DEFGHI', row[2:]):
        if v is not None:
            cells.append((f'{c}{rn}', 'v', v, S_DEC2))
    for cur, b, s_, m in CUR:
        cells.append((f'{m}{rn}', 'f', f'IF(COUNT({b}{rn}:{s_}{rn})=2,$D$25*({s_}{rn}-{b}$23)/{b}$23+(1-$D$25)*({b}$23-{b}{rn})/{b}$23,"")', S_PCT))
    num = f'IF(ISNUMBER(J{rn}),$D$24*J{rn},0)+IF(ISNUMBER(K{rn}),$F$24*K{rn},0)+IF(ISNUMBER(L{rn}),$H$24*L{rn},0)'
    den = f'IF(ISNUMBER(J{rn}),$D$24,0)+IF(ISNUMBER(K{rn}),$F$24,0)+IF(ISNUMBER(L{rn}),$H$24,0)'
    cells.append((f'M{rn}', 'f', f'IFERROR(({num})/({den}),"")', S_PCT))
wsum = ("(SUMIF('Portfolios by cur'!$B$94:$B$119,\"USD\",'Portfolios by cur'!$D$94:$D$119)+SUMIF('Portfolios by cur'!$B$94:$B$119,\"EUR\","
        "'Portfolios by cur'!$D$94:$D$119)+SUMIF('Portfolios by cur'!$B$94:$B$119,\"RUB\",'Portfolios by cur'!$D$94:$D$119))")
lab = {23: 'CBA official rate (set 29.09.2026 for 30.09.2026)', 24: 'Currency weight (mix of card FX balances)',
       25: 'Share of FX turnover where clients buy FX from the bank (sell side)', 26: 'Fast Bank margin vs CBA, weighted',
       27: 'Market: thinnest margin', 28: 'Market: median margin', 29: 'Market: widest margin',
       30: 'Fast Bank place by margin (1 = thinnest = best for clients)'}
for rn, s_ in lab.items():
    cells.append((f'B{rn}', 't', s_, S_LBL))
CBA = {'D': 363.18, 'F': 412.14, 'H': 4.3187}
for cur, b, s_, m in CUR:
    cells.append((f'{b}23', 'v', CBA[b], S_DEC2))
    cells.append((f'{b}24', 'f', f"IFERROR(SUMIF('Portfolios by cur'!$B$94:$B$119,\"{cur}\",'Portfolios by cur'!$D$94:$D$119)/{wsum},0)", S_PCT))
cells.append(('D25', 'v', 0.5, S_PCT_IN))
for c in 'JKLM':
    cells.append((f'{c}26', 'f', f'INDEX({c}5:{c}21,MATCH("Fast Bank",$B$5:$B$21,0))', S_PCT))
    cells.append((f'{c}27', 'f', f'MIN({c}5:{c}21)', S_PCT))
    cells.append((f'{c}28', 'f', f'MEDIAN({c}5:{c}21)', S_PCT))
    cells.append((f'{c}29', 'f', f'MAX({c}5:{c}21)', S_PCT))
    cells.append((f'{c}30', 'f', f'1+COUNTIF({c}5:{c}21,"<"&{c}26)', S_NUM))
cells.append(('D26', 'f', 'M26', S_PCT))
notes = ["Fast Bank today: 0.48% on USD (0.60% when buying at 361, 0.36% when selling at 364.5), 1.03% on EUR, 1.85% on RUB; 0.79% weighted – "
         "3rd thinnest of 16 banks (VTB 0.56%, ArmSwissBank 0.69%); market median 1.04%, widest Ameriabank 1.26%.",
         "No liquid AMD perpetuals or futures exist, so the CBA official rate (the weighted interbank average) is the reference. With a 50/50 buy / sell "
         "mix the margin equals half the spread over the CBA rate; set row 25 if card conversions lean to one side (e.g. spend abroad from AMD "
         "accounts = clients buying FX)."]
for i, s_ in enumerate(notes):
    cells.append((f'B{32 + i}', 't', s_, S_NOTE))
smap = dict(book.sheet_map())
P[smap['FX ranking']] = ws_xml(cells, [(1, 2), (2, 60), (3, 10)] + [(i, 11) for i in range(4, 10)] + [(i, 14) for i in range(10, 14)])

cp = book.sheet('Control panel')
AUX = {15: 28, 38: 51, 61: 74, 84: 97}
TIER = {15: 'Free', 38: 'Black', 61: 'Premium', 84: 'Elite'}
for base, aux in AUX.items():
    for c in 'BCDFGHO':
        for rn in (base, base + 1, base + 2, base + 3, aux):
            clear(cp, f'{c}{rn}')
    for rn in (base + 1, base + 2):                     # spare rows, hidden as in v15
        cp.rows[rn].set('hidden', '1')
        cp.rows[rn].set('outlineLevel', '1')
    cp.rows[base + 3].set('collapsed', '1')
    t(cp, f'B{base}', 'FX margin vs CBA official rate, % (buy and sell, weighted by currency)')
    f(cp, f'C{base}', f"'FX ranking'!$D$26", S_PCT)
    f(cp, f'D{base}', f'C{base}', S_PCT_IN)
    f(cp, f'F{base}', "'FX ranking'!$M$27", S_PCT)
    f(cp, f'G{base}', "'FX ranking'!$M$28", S_PCT)
    f(cp, f'H{base}', "'FX ranking'!$M$29", S_PCT)
    t(cp, f'O{base}', "rate.am vs CBA, 30.09.2026, 16 banks: low-end = thinnest margin (VTB), high-end = widest (Ameriabank). Fast Bank 0.79%, 3rd thinnest. 'FX ranking' tab", 827)
    tier = TIER[base]
    share = (f"(1-IFERROR(SUMIFS('Cards dataset'!$P$2:$P${ROWS},'Cards dataset'!$AB$2:$AB${ROWS},\"Euro\",'Cards dataset'!$A$2:$A${ROWS},\"Visa*\","
             f"'Cards dataset'!$B$2:$B${ROWS},\"{tier}\")/SUMIFS('Cards dataset'!$P$2:$P${ROWS},'Cards dataset'!$A$2:$A${ROWS},\"Visa*\","
             f"'Cards dataset'!$B$2:$B${ROWS},\"{tier}\"),0))")
    t(cp, f'B{aux}', 'Visa cross-currency fee income, % of Visa international spend', cp.style('B24'))
    f(cp, f'C{aux}', f'2%*{share}', S_PCT)
    f(cp, f'D{aux}', f'C{aux}', S_PCT_IN)
    t(cp, f'O{aux}', 'Finance 30.09.2026: 2% on Visa payments abroad paid from non-EUR accounts × the non-EUR share of the tier\'s Visa international spend', 827)
cp.save()

tm = book.sheet('4 tiers model (to be lineup)')
for off, base, aux in ((0, 15, 28), (77, 38, 51), (154, 61, 74), (231, 84, 97)):
    for c in 'EFGHIJK':
        f(tm, f'{c}{40 + off}', f"IFERROR('Control panel'!$D${base}/'Control panel'!$C${base},1)")
    for c in 'DEFGHIJK':
        old = tm.formula(f'{c}{37 + off}')
        a = f"'Control panel'!$D${aux}*'Control panel'!$D${base + 3}"
        assert a in old, (c, 37 + off, old)
        f(tm, f'{c}{37 + off}', old.replace(a, f"'Control panel'!$D${aux}"))
for c in 'OPQ':
    f(tm, f'{c}175', "10*'FX ranking'!$F$23")
t(tm, 'B40', 'FX revenue factor vs today (Control panel FX margin vs CBA: parameter ÷ today)')
tm.save()

CHG_2 = ('2. FX: one line per tier on the Control panel (row 15 / 38 / 61 / 84): FX margin vs the CBA official rate, buy and sell sides, weighted '
         'by currency. Today Fast Bank = 0.79% (USD 0.48%, EUR 1.03%, RUB 1.85%), market 0.56–1.26%, median 1.04% (\'FX ranking\' tab, rate.am '
         '30.09.2026). FX revenue = today\'s × parameter ÷ today. The Visa 2% cross-currency fee is one line in the aux section (row 28 / 51 / 74 / 97): '
         '2% × the non-EUR share of the tier\'s Visa spend abroad.')
chg = book.sheet('v16 changes')
t(chg, 'B4', CHG_2)
t(chg, 'B1', 'DEBIT CARDS MODEL v16.2 – CHANGES vs v15 (30.09.2026)')
chg.save()
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
