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


# ================================================================ 'FX ranking' sheet (rebuilt)
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
CUR = [('USD', 'D', 'E'), ('EUR', 'F', 'G'), ('RUB', 'H', 'I')]
cells = [('B1', 't', 'FX RATES BY BANK – drives the FX rows of each tier on the Control panel (rows 15–18, 38–41, 61–64, 84–87)', S_HDR),
         ('B2', 't', 'Quotes: rate.am, 30 Sep 2026 14:45 (screenshots from Alex). Buy = the bank buys the currency from the client; sell = the bank '
                     'sells it. Reference: Central Bank of Armenia official rate set on 29 Sep 2026 for 30 Sep 2026 (api.cba.am).', S_NOTE)]
for c, h in zip('BCDEFGHI', ('Bank', 'Branches', 'USD buy', 'USD sell', 'EUR buy', 'EUR sell', 'RUB buy', 'RUB sell')):
    cells.append((f'{c}4', 't', h, S_TIER))
for i, row in enumerate(BANKS):
    rn = 5 + i
    cells.append((f'B{rn}', 't', row[0], 892 if row[0] == 'Fast Bank' else S_LBL))
    cells.append((f'C{rn}', 'v', row[1], S_NUM))
    for c, v in zip('DEFGHI', row[2:]):
        if v is not None:
            cells.append((f'{c}{rn}', 'v', v, S_DEC2))
lab = {23: 'CBA official rate (set 29.09.2026 for 30.09.2026)', 24: 'Banks quoting, n', 25: 'Fast Bank quote',
       26: 'Fast Bank place (1 = best for clients: highest buy / lowest sell rate)', 27: 'Fast Bank margin vs CBA rate, %',
       28: 'Currency weight in card FX turnover (mix of card FX balances)', 29: 'Share of FX turnover where clients buy FX from the bank',
       30: 'Quoted margin today vs CBA, weighted by currency and side', 31: 'Card FX turnover, all 2026 cards, AMD / month (Jun–Aug 2026)',
       32: 'Cross-check: retail FX dealing income a month (2025) ÷ (card FX turnover × quoted margin)'}
for rn, s in lab.items():
    cells.append((f'B{rn}', 't', s, S_LBL))
wsum = "(SUMIF('Portfolios by cur'!$B$94:$B$119,\"USD\",'Portfolios by cur'!$D$94:$D$119)+SUMIF('Portfolios by cur'!$B$94:$B$119,\"EUR\",'Portfolios by cur'!$D$94:$D$119)+SUMIF('Portfolios by cur'!$B$94:$B$119,\"RUB\",'Portfolios by cur'!$D$94:$D$119))"
for cur, b, s in CUR:
    cells += [(f'{b}23', 'v', CBA[b], S_DEC2), (f'{s}23', 'f', f'{b}23', S_DEC2)]
    for c in (b, s):
        cells.append((f'{c}24', 'f', f'COUNT({c}5:{c}21)', S_NUM))
        cells.append((f'{c}25', 'f', f'INDEX({c}5:{c}21,MATCH("Fast Bank",$B$5:$B$21,0))', S_DEC2))
    cells.append((f'{b}26', 'f', f'1+COUNTIF({b}5:{b}21,">"&{b}25)', S_NUM))
    cells.append((f'{s}26', 'f', f'1+COUNTIF({s}5:{s}21,"<"&{s}25)', S_NUM))
    cells.append((f'{b}27', 'f', f'({b}23-{b}25)/{b}23', S_PCT))
    cells.append((f'{s}27', 'f', f'({s}25-{s}23)/{s}23', S_PCT))
    cells.append((f'{b}28', 'f', f"IFERROR(SUMIF('Portfolios by cur'!$B$94:$B$119,\"{cur}\",'Portfolios by cur'!$D$94:$D$119)/{wsum},0)", S_PCT))
cells.append(('D29', 'v', 0.5, S_PCT_IN))
cells.append(('D30', 'f', 'SUMPRODUCT((D28,F28,H28),($D$29*(E27,G27,I27)+(1-$D$29)*(D27,F27,H27)))', S_PCT))
cells[-1] = ('D30', 'f', 'D28*($D$29*E27+(1-$D$29)*D27)+F28*($D$29*G27+(1-$D$29)*F27)+H28*($D$29*I27+(1-$D$29)*H27)', S_PCT)
cells.append(('D31', 'f', f"SUM('Cards dataset'!$N$2:$N${ROWS})", S_NUM))
cells.append(('D32', 'f', "IFERROR('FX income'!$C$7/11/(D31*D30),0)", S_PCT))
cells.append(('B34', 't', 'Margin by tier (places and capture are set on the Control panel)', S_HDR))
for c, h in zip('BCDEFGHIJK', ('Tier', 'Buy place', 'Sell place', 'USD margin at the places', 'USD margin today', 'Quoted margin at the places',
                                'Capture (parameter)', 'Booked margin at the places', 'Booked margin today', 'FX revenue factor vs today')):
    cells.append((f'{c}35', 't', h, S_TIER))
TIERS = [('Free', 15), ('Black', 38), ('Premium', 61), ('Elite', 84)]
for k, (tier, base) in enumerate(TIERS):
    rn = 36 + k
    cells += [(f'B{rn}', 't', tier, S_LBL),
              (f'C{rn}', 'f', f"'Control panel'!$D${base}", S_NUM),
              (f'D{rn}', 'f', f"'Control panel'!$D${base + 1}", S_NUM),
              (f'E{rn}', 'f', f'$D$29*(SMALL($E$5:$E$21,MIN(D{rn},$E$24))-$E$23)/$E$23+(1-$D$29)*($D$23-LARGE($D$5:$D$21,MIN(C{rn},$D$24)))/$D$23', S_PCT),
              (f'F{rn}', 'f', '$D$29*$E$27+(1-$D$29)*$D$27', S_PCT),
              (f'G{rn}', 'f', f'IFERROR($D$30*E{rn}/F{rn},0)', S_PCT),
              (f'H{rn}', 'f', f"'Control panel'!$D${base + 2}", S_PCT),
              (f'I{rn}', 'f', f'G{rn}*H{rn}', S_PCT),
              (f'J{rn}', 'f', f"$D$30*'Control panel'!$C${base + 2}", S_PCT),
              (f'K{rn}', 'f', f'IFERROR(I{rn}/J{rn},1)', 906)]
notes = ["How it works: place 1 is the best rate for clients (highest buy, lowest sell) and therefore the thinnest margin for the bank. The margin vs "
         "the CBA rate at the chosen places (USD ranking; EUR and RUB move in proportion) × the capture share = the FX margin the card P&L books. "
         "The tier FX revenue = today's revenue × (booked margin at the places ÷ booked margin today).",
         "Capture today = the model's card FX income (8 cards model row 176, Q4-25) ÷ (card FX turnover per card, Client profiles row 33 × quoted "
         "margin today). It is ~1% or less: the card P&L books almost none of the quoted margin, because 'FX income' is allocated to cards by their "
         "share of FX balances (0.38%), not by conversions. Row 32 shows the other extreme: all retail FX dealing income over card turnover.",
         "Fast Bank today (30.09.2026): USD 4th of 16 on buy and 1st of 16 on sell, i.e. among the best rates for clients and the thinnest margins; "
         "quoted margin vs CBA 0.60% when buying USD, 0.36% when selling."]
for i, s in enumerate(notes):
    cells.append((f'B{41 + i}', 't', s, S_NOTE))


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


smap = dict(book.sheet_map())
P[smap['FX ranking']] = ws_xml(cells, [(1, 2), (2, 60), (3, 11)] + [(i, 13) for i in range(4, 12)])

# ================================================================ Control panel: FX controls in each tier's rows
cp = book.sheet('Control panel')
for rn in range(99, 112):                               # old block at the bottom
    row = cp.rows.get(rn)
    if row is not None:
        for c in list(row):
            row.remove(c)
AUX = {15: 28, 38: 51, 61: 74, 84: 97}
TC = {15: ('N', 'C', 'Free'), 38: ('O', 'D', 'Black'), 61: ('P', 'E', 'Premium'), 84: ('Q', 'F', 'Elite')}
for base, aux in AUX.items():
    ec, pc, tier = TC[base]
    for rn in (base + 1, base + 2):
        row = cp.rows[rn]
        for a in ('hidden', 'outlineLevel'):
            row.attrib.pop(a, None)
    cp.rows[base + 3].attrib.pop('collapsed', None)
    for c in 'CDFGHO':
        for rn in range(base, base + 4):
            clear(cp, f'{c}{rn}')
    lbl = cp.style(f'B{base}')
    t(cp, f'B{base}', 'FX buy rate: place in the market rating (1 = best for clients: highest buy rate)', lbl)
    f(cp, f'C{base}', f'{FXR}!$D$26', S_INT)
    val(cp, f'D{base}', 4, S_INT_IN)
    val(cp, f'F{base}', 1, S_INT)
    f(cp, f'G{base}', f'ROUND(({FXR}!$D$24+1)/2,0)', S_INT)
    f(cp, f'H{base}', f'{FXR}!$D$24', S_INT)
    t(cp, f'O{base}', 'rate.am 30.09.2026, USD, 16 banks: Fast Bank 4th on buy (361 vs CBA 363.18 = 0.60% margin). EUR / RUB move in proportion', 827)
    t(cp, f'B{base + 1}', 'FX sell rate: place in the market rating (1 = best for clients: lowest sell rate)', lbl)
    f(cp, f'C{base + 1}', f'{FXR}!$E$26', S_INT)
    val(cp, f'D{base + 1}', 1, S_INT_IN)
    val(cp, f'F{base + 1}', 1, S_INT)
    f(cp, f'G{base + 1}', f'ROUND(({FXR}!$E$24+1)/2,0)', S_INT)
    f(cp, f'H{base + 1}', f'{FXR}!$E$24', S_INT)
    t(cp, f'O{base + 1}', 'Fast Bank 1st on sell (364.5 vs CBA 363.18 = 0.36% margin): the best rate for clients, the thinnest margin', 827)
    t(cp, f'B{base + 2}', 'FX margin captured: share of the quoted margin (vs CBA) booked as card FX income, %', lbl)
    f(cp, f'C{base + 2}', f"IFERROR({EC}!{ec}176/('Client profiles'!{pc}33*{FXR}!$D$30),0)", S_PCT)
    f(cp, f'D{base + 2}', f'C{base + 2}', S_PCT_IN)
    t(cp, f'O{base + 2}', "Today = model card FX income ÷ (card FX turnover × quoted margin). Upper bound: retail dealing ÷ card turnover, 'FX ranking' D32", 827)
    t(cp, f'B{base + 3}', 'Visa cross-currency fee charged to the client (international Visa payments), %', lbl)
    val(cp, f'C{base + 3}', 0.02, S_PCT)
    val(cp, f'D{base + 3}', 0.02, S_PCT_IN)
    t(cp, f'O{base + 3}', 'Finance 30.09.2026: Visa settles in EUR; paying from a non-EUR account = Visa cross rate + 2%. Mastercard (USD): no fee', 827)
    t(cp, f'B{aux}', 'Share of Visa international spend charged the cross-currency fee, %', cp.style('B24') or lbl)
    f(cp, f'C{aux}', f"1-IFERROR(SUMIFS('Cards dataset'!$P$2:$P${ROWS},'Cards dataset'!$AB$2:$AB${ROWS},\"Euro\",'Cards dataset'!$A$2:$A${ROWS},\"Visa*\","
                     f"'Cards dataset'!$B$2:$B${ROWS},\"{tier}\")/SUMIFS('Cards dataset'!$P$2:$P${ROWS},'Cards dataset'!$A$2:$A${ROWS},\"Visa*\","
                     f"'Cards dataset'!$B$2:$B${ROWS},\"{tier}\"),0)", S_PCT)
    f(cp, f'D{aux}', f'C{aux}', S_PCT_IN)
    t(cp, f'O{aux}', "1 − EUR-account share of the tier's Visa international spend ('Cards dataset' columns P, AB; Jun–Aug 2026)", 827)
cp.save()

# ================================================================ 4 tiers model: FX factor, Visa fee refs, cashback divisors
tm = book.sheet('4 tiers model (to be lineup)')
for k, (off, fee, share) in enumerate(((0, 18, 28), (77, 41, 51), (154, 64, 74), (231, 87, 97))):
    for c in 'EFGHIJK':
        f(tm, f'{c}{40 + off}', f'{FXR}!$K${36 + k}')
    for c in 'DEFGHIJK':
        old = tm.formula(f'{c}{37 + off}')
        assert "'Control panel'!$D$111*'Control panel'!$D$110" in old, (c, 37 + off, old)
        f(tm, f'{c}{37 + off}', old.replace("'Control panel'!$D$111*'Control panel'!$D$110", f"'Control panel'!$D${share}*'Control panel'!$D${fee}"))
t(tm, 'B40', 'FX revenue factor vs today (place in the FX rating and capture share, see FX ranking rows 36–39)')
for row, sw, tg, col, old_div in ((136, 45, 42, 'E', '/3'), (213, 68, 65, 'F', '/2.1'), (290, 91, 88, 'G', '/1.7')):
    for c in 'EFGHIJK':
        old = tm.formula(f'{c}{row}')
        assert old.endswith(old_div), (c, row, old)
        f(tm, f'{c}{row}', f"IF('Control panel'!$D${sw}=\"Engine\",'Control panel'!$C${sw},'Control panel'!$D${tg}*'CB Results'!${col}$12)")
tm.save()

# ================================================================ 'v16 changes' sheet: rewrite items 2 and 5
CHG = ['DEBIT CARDS MODEL v16.1 – CHANGES vs v15 (30.09.2026)', '',
       '1. Tiers: Free = Visa Digital + ArCa Classic; Black = Visa Classic + Visa Gold (moved from Premium); Premium = Mastercard World; Elite = '
       'MC World Elite + Visa Infinite + Infinite Metal. Changed: 8 cards model H148, paid share N39:P39 (mapping-based), Control panel C37 / C49 / '
       'C72 / C95, block titles, Cards dataset tier of 17,765 Visa Gold cards, CB Inputs C14, CB Client view persona.',
       '2. FX: new sheet \'FX ranking\' (rate.am 30.09.2026, 17 banks; CBA official rate). Each tier\'s rows on the Control panel set: our place in '
       'the buy rating and the sell rating (1 = best for clients = thinnest margin), the capture share (how much of the quoted margin vs CBA the '
       'card P&L books; today calculated from the model\'s card FX income, ~1% or less) and the Visa 2% cross-currency fee (row 18 / 41 / 64 / 87; '
       'share of Visa spend charged in row 28 / 51 / 74 / 97). FX revenue = today\'s × booked margin at the places ÷ booked margin today. '
       'Defaults = today, so the factor is 1.',
       '3. New data: \'Cards dataset\' columns O–AB from final_report.xlsx, joined by contract ID (96,895 of 96,906 cards; 11 unmatched = 0): '
       'local / international non-cash volume and count, cashout at Fast Bank / other Armenian / foreign ATMs, cashouts, C2C to other banks, '
       'tariff service fee, card currency. Client profiles sections 6–8: non-cash, cashout and C2C multipliers (rows 74 / 76 / 77) now come from '
       'their own fields; Q4-26 international share and other-ATM share in the tier model come from section 8.',
       '4. Finance update: interchange 0.5% domestic / 1.2% international on standard cards, 0.6% / 1.5% on Visa Gold and above (8 cards model rows '
       '45 / 50, tier row 195). Visa 2% cross-currency fee in FX revenue (tier row 37). Perks: Premium (MC World) 10 EUR a year; Elite Visa '
       'Infinite / World Elite 20k AMD a year (unchanged). C2C 0.5% confirmed.',
       '5. Cashback: the eligible-spend divisors (were 3 / 2.1 / 1.7) are now the engine\'s eligible share of non-cash spend for the new tiers '
       "('CB Results' row 12: Black 39%, Premium 64%, Elite 59%), live. In Engine mode the engine rate is used as is (no divisor).",
       '', 'Open from the finance list: marketing spend Mar–Aug 2026 and cards sold (Zhanna Mkrtumyan); fee-waiver rules by card type (8.3); card FX '
       'income vs card FX turnover (to set the capture share properly); ArCa Pay / SBP transfers free until 31 Dec 2026 – not modelled.']
P[smap['v16 changes']] = ws_xml([(f'B{i + 1}', 't', s, S_HDR if i == 0 else S_LBL) for i, s in enumerate(CHG) if s], [(1, 2), (2, 180)])

wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
