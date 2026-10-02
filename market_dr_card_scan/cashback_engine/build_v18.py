"""Debit cards model v18 (30.09.2026), from v17.1A (Visa Gold in Black).
    python3 build_v18.py <v17.1A_raw.xlsx> <out.xlsx>
1. AMD-only new cards: per-tier switch (Control panel row 28 / 51 / 74 / 97); 0 = no international (non-AMD) card payments and no FX
   balances from 2027; the FX line = margin on cardholders' conversions on other accounts (branch / app).
2. Control panel output: cashout split into Fast Bank ATMs / other ATMs; one-off OpEx split into marketing / other.
3. 'v16 changes' deleted; new 'Eligible spend' tab (split by tier, excluded categories, excluded MCCs).
"""
import re
import sys
from lxml import etree
from xmlbook import CTN, N, PKG, RNS, S, X, Book

IN, OUT = sys.argv[1:3]
book = Book(IN)
P = book.parts
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'
NX = len(X(P['xl/styles.xml']).find(N + 'cellXfs'))
S_DEC2, S_INT_IN = NX - 2, NX - 1
S_HDR, S_SUB, S_LBL, S_NUM, S_NOTE, S_TIER, S_NOTEH = 896, 904, 894, 900, 891, 898, 899
S_PCT, S_PCT_IN, S_INT = 810, 811, 807
T4 = "'4 tiers model (to be lineup)'"
CPS = "'Control panel'"


def clear(sh, ref):
    c = sh.get(ref)
    if c is not None:
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)


def val(sh, ref, x, s):
    c = sh.cell(ref); sh._reset(c, s); etree.SubElement(c, N + 'v').text = str(int(x)) if float(x).is_integer() else repr(float(x))


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


# ================================================================ 1. tier model: AMD-only switch
tm = book.sheet('4 tiers model (to be lineup)')
SW = {0: 28, 77: 51, 154: 74, 231: 97}
for o, swr in SW.items():
    sw = f"{CPS}!$D${swr}"
    for c in 'EFGHIJK':
        for r in (19, 49):
            fm = tm.formula(f'{c}{r + o}')
            assert fm.startswith('(1-'), (c, r + o, fm)
            tm.f(f'{c}{r + o}', f'{fm}*{sw}', tm.style(f'{c}{r + o}'))
        fm = tm.formula(f'{c}{20 + o}')
        assert re.fullmatch(rf'{c}{21 + o}\*(3|12)', fm), fm
        tm.f(f'{c}{20 + o}', f'{fm}*(1-(1-{sw})*$D${19 + o})', tm.style(f'{c}{20 + o}'))
        fm = tm.formula(f'{c}{42 + o}')
        a = f'{c}{48 + o}*'
        assert fm.startswith(a), fm
        tm.f(f'{c}{42 + o}', fm.replace(a, f'{c}{48 + o}*(1-(1-{sw})*$D${49 + o})*', 1), tm.style(f'{c}{42 + o}'))
tm.save()

# ================================================================ 2. Control panel: switch rows, FX label, output re-layout
cp = book.sheet('Control panel')
BLK = [(6, 0, 'D9', 'D10'), (29, 77, 'D32', 'D33'), (52, 154, 'D55', 'D56'), (75, 231, 'D78', 'D79')]
for b, o, own, owna in BLK:
    swr = b + 22
    lbl = cp.style(f'B{b + 18}') or cp.style('B24')
    cp.t(f'B{swr}', 'Card supports non-AMD payments and FX balances (1 = yes, 0 = AMD-only card)', cp.style('B24'))
    val(cp, f'C{swr}', 1, S_INT)
    val(cp, f'D{swr}', 0, S_INT_IN)
    cp.t(f'O{swr}', "New cards are AMD-only (Alex 30.09.2026): 0 removes international card payments (today's share of non-cash) and FX card "
                    "balances from 2027. FX conversions move to branch / app accounts: see the FX line", 827)
    cp.t(f'B{b + 9}', "FX margin vs CBA on cardholders' conversions (card is AMD-only: branch / app accounts), %", cp.style(f'B{b + 9}'))
    cp.t(f'O{b + 9}', "Preferential rate for cardholders = set below today's. rate.am vs CBA 30.09.2026, 16 banks: low-end = thinnest (VTB 0.56%), "
                      "high-end = widest (Ameriabank 1.26%); Fast Bank 0.79%. 'FX ranking' tab", 827)
    lab_s, tot_s, val_s, op_l, op_v = 819, 818, 809, 821, 812
    lay = {1: ('Total revenue', 9, tot_s), 2: (' - interest', 10, lab_s), 3: (' - interchange', 11, lab_s),
           5: (' - cashout: Fast Bank ATMs', None, lab_s), 7: (' - cashout: other ATMs', None, lab_s),
           8: (' - transfers', 13, lab_s), 9: (' - service fee', 15, lab_s), 12: (' - FX', 14, lab_s),
           13: ('Total costs', 16, tot_s), 14: (' - cashback', 18, lab_s), 15: (' - deposit uplift', 17, lab_s),
           16: (' - recurring OpEx', 19, lab_s), 17: (' - one-off OpEx: marketing', None, lab_s), 18: (' - one-off OpEx: other', None, lab_s),
           19: (' - perks', 21, lab_s), 20: ('Operating profit', 22, op_l)}
    for k in range(1, 21):
        for c in 'JKLMN':
            clear(cp, f'{c}{b + k}')
    yr = {'K': ('I', 'O'), 'L': ('J', 'P'), 'M': ('K', 'Q')}
    for k, (name, srow, ls) in lay.items():
        r = b + k
        cp.t(f'J{r}', name, ls)
        vs = op_v if k == 20 else val_s
        if srow is not None:
            for c in 'KLMN':
                cp.f(f'{c}{r}', f"{T4}!{ {'K': 'O', 'L': 'P', 'M': 'Q', 'N': 'R'}[c] }{srow + o}", vs)
            continue
        for c, (ty, sc) in yr.items():
            if k == 5:
                fm = (f"{T4}!{ty}{29 + o}*(1-{T4}!{ty}{27 + o})*({CPS}!${owna[0]}${owna[1:]}*{T4}!{ty}{28 + o}"
                      f"+{CPS}!${own[0]}${own[1:]}*(1-{T4}!{ty}{28 + o}))")
            elif k == 7:
                fm = f"{T4}!{sc}{12 + o}-{c}{b + 5}"
            elif k == 17:
                fm = f"IFERROR({T4}!{sc}{20 + o}*{T4}!{ty}{75 + o}/{T4}!{ty}{73 + o},0)"
            else:
                fm = f"{T4}!{sc}{20 + o}-{c}{b + 17}"
            cp.f(f'{c}{r}', fm, vs)
        cp.f(f'N{r}', f'SUM(K{r}:M{r})', vs)
cp.save()

# ================================================================ 3. 'Eligible spend' tab
MAP = "'CB MCC_map'"
rng = lambda col: f"{MAP}!${col}$5:${col}$397"                        # noqa: E731
cells = [('B1', 't', 'ELIGIBLE SPEND – what counts for cashback and what is excluded', S_HDR),
         ('B2', 't', "Section 1: cashback engine, monthly, scaled to all clients with card spend in Aug 2026 ('CB Results'). Sections 2–3: full MCC "
                     "extract, all clients ('CB MCC_map'; change column D there to regroup an MCC). Eligible = card purchases in the cashback categories; "
                     "non-cash (the P&L basis) = everything except ATM and counter cash.", S_NOTE)]
cells += [('B4', 't', '1. Spend split by tier, AMD a month', S_HDR)] + [(f'{c}4', 't', h, S_TIER) for c, h in zip('CDEFG', ('Free', 'Black', 'Premium', 'Elite', 'Total'))]
sec1 = [('Total card spend', 6, S_NUM), ('  cash withdrawals (ATM and bank counter)', 7, S_NUM), ('  gambling and betting', 8, S_NUM),
        ('  other excluded: transfers, e-wallets, quasi-cash, government, utilities, telecom, insurance, charity, rent', 9, S_NUM),
        ('Eligible spend', 10, S_NUM), ('Non-cash spend (P&L basis: all except cash withdrawals)', 11, S_NUM),
        ('Eligible share of non-cash spend, all clients', 12, S_PCT)]
r = 5
for name, src, s in sec1:
    cells.append((f'B{r}', 't', name, 892 if name.startswith(('Total', 'Eligible spend')) else S_LBL))
    for c, rc in zip('CDEFG', 'DEFGH'):
        cells.append((f'{c}{r}', 'f', f"'CB Results'!{rc}{src}", s))
    r += 1
cells.append((f'B{r}', 't', 'Eligible share of total card spend', S_LBL))
for c in 'CDEFG':
    cells.append((f'{c}{r}', 'f', f'IFERROR({c}9/{c}5,0)', S_PCT))
r += 1
cells.append((f'B{r}', 't', 'Eligible share of non-cash spend, excluding gold-loan clients', S_LBL))
for c in 'CDEF':
    cells.append((f'{c}{r}', 'f', f"'Client profiles'!{c}121", S_PCT))
r += 1
cells.append((f'B{r}', 't', 'Share used by the P&L to convert the cashback target (profile mode in use)', 892))
for c in 'CDEF':
    cells.append((f'{c}{r}', 'f', f"'Client profiles'!{c}122", S_PCT))
cells.append((f'H{r}', 't', 'Cashback cost = target on eligible spend × this share × non-cash spend', S_NOTE))
CATS = [('X_CASH', 'Cash withdrawals'), ('X_GAMB', 'Gambling and lotteries'), ('X_FIN', 'Transfers, e-wallets, financial services'),
        ('X_QCASH', 'Quasi-cash, FX, crypto, pawn'), ('X_GOV', 'Government, taxes and fines'), ('X_UTIL', 'Utilities'),
        ('X_TEL', 'Telecom and internet'), ('X_INS', 'Insurance'), ('X_CHAR', 'Charity, religious and political'), ('X_OTH', 'Rent, intra-company, adult')]
r = 16
cells += [(f'B{r}', 't', '2. Excluded categories, all clients', S_HDR)] + [(f'{c}{r}', 't', h, S_TIER) for c, h in zip('CDEFG', ('Code', 'MCCs', 'Aug-26, AMD', 'Avg a month Mar–Aug 26, AMD', 'Share of Aug-26 card spend'))]
r0 = r + 1
for code, name in CATS:
    r += 1
    cells += [(f'B{r}', 't', name, S_LBL), (f'C{r}', 't', code, S_LBL),
              (f'D{r}', 'f', f'COUNTIF({rng("D")},C{r})', S_NUM),
              (f'E{r}', 'f', f'SUMIF({rng("D")},C{r},{rng("J")})', S_NUM),
              (f'F{r}', 'f', f'SUMIF({rng("D")},C{r},{rng("I")})', S_NUM),
              (f'G{r}', 'f', f'IFERROR(E{r}/SUM({rng("J")}),0)', S_PCT)]
r += 1
cells += [(f'B{r}', 't', 'Total excluded', 892), (f'D{r}', 'f', f'SUM(D{r0}:D{r - 1})', S_NUM), (f'E{r}', 'f', f'SUM(E{r0}:E{r - 1})', S_NUM),
          (f'F{r}', 'f', f'SUM(F{r0}:F{r - 1})', S_NUM), (f'G{r}', 'f', f'SUM(G{r0}:G{r - 1})', S_PCT)]
r += 1
cells += [(f'B{r}', 't', 'Eligible categories (all other MCCs)', 892), (f'D{r}', 'f', f'COUNTIF({rng("G")},"Yes")', S_NUM),
          (f'E{r}', 'f', f'SUMIF({rng("G")},"Yes",{rng("J")})', S_NUM), (f'F{r}', 'f', f'SUMIF({rng("G")},"Yes",{rng("I")})', S_NUM),
          (f'G{r}', 'f', f'IFERROR(E{r}/SUM({rng("J")}),0)', S_PCT)]
EXCL = [268, 355, 269, 285, 271, 392, 134, 267, 393, 129, 270, 273, 379, 275, 272, 130, 133, 380, 381, 131, 395, 298, 396, 382, 284, 132,
        227, 241, 274, 276, 277, 278, 279, 280, 281, 282, 283, 339, 340, 341, 389, 390, 391, 394, 397]
r += 2
cells += [(f'B{r}', 't', f'3. Excluded MCCs ({len(EXCL)}), by Aug-26 volume', S_HDR)] + \
         [(f'{c}{r}', 't', h, S_TIER) for c, h in zip('CDEFG', ('MCC', 'Category', 'Aug-26, AMD', 'Avg a month Mar–Aug 26, AMD', 'Official name'))]
for mr in EXCL:
    r += 1
    cells += [(f'B{r}', 'f', f"{MAP}!C{mr}", S_LBL), (f'C{r}', 'f', f"{MAP}!A{mr}", S_LBL), (f'D{r}', 'f', f"{MAP}!D{mr}", S_LBL),
              (f'E{r}', 'f', f"{MAP}!J{mr}", S_NUM), (f'F{r}', 'f', f"{MAP}!I{mr}", S_NUM), (f'G{r}', 'f', f"{MAP}!B{mr}", S_NOTE)]
ELIG_XML = ws_xml(cells, [(1, 2), (2, 70), (3, 12), (4, 14), (5, 16), (6, 16), (7, 26), (8, 60)])


# ================================================================ 4. sheets: delete 'v16 changes', add 'Eligible spend'
def app_titles(fn):
    app = P['docProps/app.xml'].decode('utf-8')
    P['docProps/app.xml'] = fn(app).encode('utf-8')


wb = X(P['xl/workbook.xml'])
rels = X(P['xl/_rels/workbook.xml.rels'])
shs = wb.find(N + 'sheets')
ct = X(P['[Content_Types].xml'])
old = next(s for s in shs if s.get('name') == 'v16 changes')
pos = list(shs).index(old)
rid = old.get('{%s}id' % RNS)
rel = next(r for r in rels if r.get('Id') == rid)
part = 'xl/' + rel.get('Target').lstrip('/').replace('xl/', '')
# reuse the same position, relationship and part for the new tab (sheet order and localSheetIds stay as they are)
old.set('name', 'Eligible spend')
P[part] = ELIG_XML
for o_ in ct:
    if o_.get('PartName') == '/' + part:
        pass
P['xl/workbook.xml'] = S(wb)
app_titles(lambda a: a.replace('<vt:lpstr>v16 changes</vt:lpstr>', '<vt:lpstr>Eligible spend</vt:lpstr>'))
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
