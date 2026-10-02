"""Debit cards model v16 (30.09.2026), built from Alex's v15.

    python3 build_v16.py <v15.xlsx> <cd_new.pkl> <out.xlsx>

1. Tiers: Free = Visa Digital + ArCa; Black = Visa Classic + Visa Gold; Premium = MC World; Elite = MC World Elite + Infinite + Metal.
2. FX: margin set by Fast Bank's place in the market buy / sell ranking (new 'FX ranking' sheet, Control panel rows 99-111).
3. 'Cards dataset' enriched with 14 columns from final_report.xlsx (Sep 2026); Client profiles sections 6-8; tier model uses them.
4. Finance update 30.09.2026: interchange 0.5/0.6% domestic, 1.2/1.5% international; Visa cross-currency fee 2%;
   perks MC World 10 EUR a year, Infinite / World Elite 20k AMD a year.
"""
import re
import sys

import pandas as pd
from lxml import etree

from xmlbook import CTN, N, PKG, RNS, S, X, Book

IN, CDN, OUT = sys.argv[1:4]
book = Book(IN)
P = book.parts
EC = "'8 cards model (as is lineup)'"
CP = "'Control panel'"
CPR = "'Client profiles'"
FXR = "'FX ranking'"
ROWS = 96907                    # last data row of 'Cards dataset'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

sst_root = X(P['xl/sharedStrings.xml'])
sst = [''.join(t.text or '' for t in si.iter(N + 't')) for si in sst_root]


def text(c):
    if c is None:
        return None
    t, v = c.get('t'), c.find(N + 'v')
    if t == 's':
        return sst[int(v.text)]
    if t == 'inlineStr':
        return ''.join(x.text or '' for x in c.iter(N + 't'))
    return None if v is None else v.text


def val(sh, ref, v, s=None):
    """numeric constant"""
    c = sh.cell(ref)
    sh._reset(c, s if s is not None else c.get('s'))
    etree.SubElement(c, N + 'v').text = repr(float(v)) if not float(v).is_integer() else str(int(v))


def f(sh, ref, formula, s=None):
    sh.f(ref, formula, s if s is not None else sh.style(ref))


def t(sh, ref, txt, s=None):
    sh.t(ref, txt, s if s is not None else sh.style(ref))


def expect(sh, ref, want):
    got = sh.formula(ref) if want.startswith('=') else text(sh.get(ref))
    assert got == want.lstrip('=') if want.startswith('=') else got == want, (ref, got, want)


# ---------------------------------------------------------------- styles: add a 0.00 number and a 0.00 input style
sty = X(P['xl/styles.xml'])
xfs = sty.find(N + 'cellXfs')


def clone_xf(src, **attrs):
    x = etree.fromstring(etree.tostring(list(xfs)[src]))
    for k, v in attrs.items():
        x.set(k, v)
    x.set('applyNumberFormat', '1')
    xfs.append(x)
    xfs.set('count', str(len(xfs)))
    return len(xfs) - 1


S_DEC2 = clone_xf(909, numFmtId='2')             # 0.00
S_INT_IN = clone_xf(918, numFmtId='1')           # input, integer (red on yellow, as the Control panel inputs)
P['xl/styles.xml'] = S(sty)
S_HDR, S_SUB, S_LBL, S_NUM, S_MUL, S_NOTE, S_TIER, S_NOTEH = 896, 904, 894, 900, 906, 891, 898, 899
S_PCT, S_PCT_IN, S_INT = 810, 811, 807

# ================================================================ 1. TIERS
em = book.sheet('8 cards model (as is lineup)')
expect(em, 'H6', 'VisaGold')
expect(em, 'H148', 'Premium')
t(em, 'H148', 'Black')
for c, tier in zip('NOP', ('Black', 'Premium', 'Elite')):              # paid share by tier, mapping-based
    f(em, f'{c}39', f'IFERROR(SUMPRODUCT(($D$148:$K$148="{tier}")*$D$8:$K$8*$D$39:$K$39)/SUMIF($D$148:$K$148,"{tier}",$D$8:$K$8),0)')

tm = book.sheet('4 tiers model (to be lineup)')
expect(tm, 'F84', 'Fast Black (Visa Classic)')
expect(tm, 'F161', 'Fast Premium (Mastercard World, Visa Gold)')
t(tm, 'F84', 'Fast Black (Visa Classic, Visa Gold)')
t(tm, 'F161', 'Fast Premium (Mastercard World)')

cp = book.sheet('Control panel')
expect(cp, 'C49', f'={EC}!G39')
f(cp, 'C49', f'{EC}!N39')                                                   # Black = Visa Classic + Visa Gold
f(cp, 'C72', f'{EC}!O39')
f(cp, 'C95', f'{EC}!P39')
f(cp, 'C37', f'SUMPRODUCT(({EC}!$D$148:$K$148="Black")*{EC}!$D$37:$K$37*{EC}!$D$8:$K$8)/SUMIF({EC}!$D$148:$K$148,"Black",{EC}!$D$8:$K$8)')

ci = book.sheet('CB Inputs')
expect(ci, 'B14', 'Visa Gold')
t(ci, 'C14', 'Black')
ci_note=None
t(ci, 'L7', "Model row 50 (v15: 1.5%). Finance 30.09.2026: 1.2% standard cards, 1.5% Visa Gold and above; the engine keeps 1.5%")
cv = book.sheet('CB Client view')
assert text(cv.get('V2')).startswith('Visa Gold') and text(cv.get('V3')) == 'Premium'
t(cv, 'V3', 'Black')
ci.save()
cv.save()

# ================================================================ 2. CARDS DATASET: tier + 14 new columns
cd = book.sheet('Cards dataset')
new = pd.read_pickle(CDN)
assert len(new) == ROWS - 1
NEWCOLS = [('O', 'Local non-cash volume, AMD / month', 'Local non-cash volume, AMD / month', 909),
           ('P', 'International non-cash volume, AMD / month', 'International non-cash volume, AMD / month', 909),
           ('Q', 'Non-cash payments, total, AMD / month', None, 909),
           ('R', 'Local non-cash payments, # / month', 'Local non-cash payments, # / month', 910),
           ('S', 'International non-cash payments, # / month', 'International non-cash payments, # / month', 910),
           ('T', 'Cashout at Fast Bank ATMs, AMD / month', 'Cashout at Fast Bank ATMs, AMD / month', 909),
           ('U', "Cashout at other Armenian banks' ATMs, AMD / month", 'Cashout at other Armenian ATMs, AMD / month', 909),
           ('V', 'Cashout abroad, AMD / month', 'Cashout abroad, AMD / month', 909),
           ('W', 'Cashout, total, AMD / month', None, 909),
           ('X', 'Cashouts, # / month', 'Cashouts, # / month', 910),
           ('Y', 'C2C to other banks, AMD / month', 'C2C to other banks, AMD / month', 909),
           ('Z', 'C2C to other banks, # / month', 'C2C to other banks, # / month', 910),
           ('AA', 'Service fee (tariff), AMD / year', 'Service fee (tariff), AMD / year', 909),
           ('AB', 'Card currency', 'Card currency', None)]
new['Non-cash payments, total, AMD / month'] = new['Local non-cash volume, AMD / month'] + new['International non-cash volume, AMD / month']
new['Cashout, total, AMD / month'] = (new['Cashout at Fast Bank ATMs, AMD / month'] + new['Cashout at other Armenian ATMs, AMD / month']
                                      + new['Cashout abroad, AMD / month'])
for col, hdr, src, s in NEWCOLS:
    if src is None:
        new[hdr] = new[hdr]
    else:
        new[hdr] = new[src]
sidx = {}


def sst_add(s):
    if s in sidx:
        return sidx[s]
    if s in sst:
        sidx[s] = sst.index(s)
        return sidx[s]
    si = etree.SubElement(sst_root, N + 'si')
    etree.SubElement(si, N + 't').text = s
    sst.append(s)
    sidx[s] = len(sst) - 1
    return sidx[s]


black_i = sst_add('Black')
moved = 0
hdr_row = cd.rows[1]
for col, hdr, src, s in NEWCOLS:
    c = etree.SubElement(hdr_row, N + 'c', r=f'{col}1', s='908', t='s')
    etree.SubElement(c, N + 'v').text = str(sst_add(hdr))
hdr_row.attrib.pop('spans', None)
cur_i = {v: sst_add(v) for v in new['Card currency'].fillna('').unique() if v}
for i in range(len(new)):
    rn = i + 2
    row = cd.rows[rn]
    row.attrib.pop('spans', None)
    cells = {c.get('r'): c for c in row}
    a = text(cells.get(f'A{rn}'))
    assert a == new.card_type_group.iat[i], (rn, a, new.card_type_group.iat[i])
    if a == 'Visa Gold':
        b = cells[f'B{rn}']
        assert text(b) == 'Premium'
        for ch in list(b):
            b.remove(ch)
        b.set('t', 's')
        etree.SubElement(b, N + 'v').text = str(black_i)
        moved += 1
    for col, hdr, src, s in NEWCOLS:
        v = new[hdr].iat[i]
        if col == 'AB':
            if v:
                c = etree.SubElement(row, N + 'c', r=f'{col}{rn}', t='s')
                etree.SubElement(c, N + 'v').text = str(cur_i[v])
            continue
        c = etree.SubElement(row, N + 'c', r=f'{col}{rn}', s=str(s))
        x = round(float(v), 0 if s == 909 else 2)
        etree.SubElement(c, N + 'v').text = str(int(x)) if x.is_integer() else repr(x)
cd.root.find(N + 'dimension').set('ref', f'A1:AB{ROWS}')
cols = cd.root.find(N + 'cols')
etree.SubElement(cols, N + 'col', min='15', max='27', width='16', customWidth='1')
etree.SubElement(cols, N + 'col', min='28', max='28', width='12', customWidth='1')
cd.save()
sst_root.set('count', str(int(sst_root.get('count', '0')) + 0))
sst_root.set('uniqueCount', str(len(sst)))
print('Visa Gold rows moved to Black:', moved)

# ================================================================ 3. CLIENT PROFILES: sections 6-8 and multipliers
cpr = book.sheet('Client profiles')
R = lambda col: f"'Cards dataset'!${col}$2:${col}${ROWS}"                      # noqa: E731
TC = 'CDEF'


def avg(col, mode, c):
    if c == 'G':
        if mode == 1:
            return f'IFERROR(AVERAGE({R(col)}),0)'
        if mode == 2:
            return f'IFERROR(AVERAGEIFS({R(col)},{R("C")},"<>Gold loan",{R("F")},">0"),0)'
        return None
    crit = f'{R("B")},{c}$14'
    if mode >= 2:
        crit += f',{R("C")},"<>Gold loan",{R("F")},">0"'
    if mode == 3:
        crit += f',{R("I")},">="&{c}$21'
    return f'IFERROR(AVERAGEIFS({R(col)},{crit}),0)'


MET = [('Non-cash payments (local + international), AMD / month', 'Q'), ('  of which international', 'P'),
       ('Cashout at all ATMs, AMD / month', 'W'), ("  of which at other Armenian banks' ATMs", 'U'), ('  of which abroad', 'V'),
       ('C2C transfers to other banks, AMD / month', 'Y')]


def header(r, title):
    t(cpr, f'B{r}', title, S_HDR)
    for c, name in zip(TC, ('Free', 'Black', 'Premium', 'Elite')):
        t(cpr, f'{c}{r}', name, S_TIER)
    t(cpr, f'G{r}', 'All tiers', S_TIER)
    t(cpr, f'H{r}', 'Notes', S_NOTEH)


header(84, "6. Channel activity from the Sep 2026 card report (final_report.xlsx), per card, Jun–Aug 2026")
start = {}
r = 85
for mode, title in ((1, 'All 2026 cards (mode 1)'), (2, 'Active users (mode 2)'), (3, 'High engagement users (mode 3)')):
    t(cpr, f'B{r}', title, S_SUB)
    r += 1
    start[mode] = r
    for name, col in MET:
        t(cpr, f'B{r}', name, S_LBL)
        for c in TC + 'G':
            if c == 'G' and mode == 3:
                f(cpr, f'G{r}', f'IFERROR(SUMPRODUCT(C{r}:F{r},$C$22:$F$22)/$G$22,0)', S_NUM)
            else:
                f(cpr, f'{c}{r}', avg(col, mode, c), S_NUM)
        r += 1
t(cpr, f'H{start[1]}', "'Cards dataset' columns O–AB, joined by contract ID from final_report.xlsx (Sep 2026): same 96,906 cards", S_NOTE)
t(cpr, f'H{start[1] + 2}', 'Fast Bank ATMs + other Armenian ATMs + abroad', S_NOTE)
assert r == 106
header(106, '7. Multipliers from these fields (profile average ÷ all 2026 cards)')
MUL = {}
r = 107
for mode, title in ((2, 'Active users (mode 2)'), (3, 'High engagement users (mode 3)')):
    t(cpr, f'B{r}', title, S_SUB)
    r += 1
    for k, (name, off) in enumerate((('  Non-cash payments', 0), ('  Cashout', 2), ('  C2C transfers', 5))):
        t(cpr, f'B{r}', name, S_LBL)
        for c in TC + 'G':
            f(cpr, f'{c}{r}', f'IFERROR({c}{start[mode] + off}/{c}{start[1] + off},"")', S_MUL)
        MUL[(mode, k)] = r
        r += 1
assert r == 115
header(115, '8. Channel mix used by the tier model (mode in use)')
mix = [('International share of non-cash payments', '{c}{a1}/{c}{a0}', (1, 0)),
       ("Share of domestic cashout at other banks' ATMs", '{c}{a1}/({c}{a0}-{c}{a2})', (3, 2, 4)),
       ('Share of cashout made abroad (info)', '{c}{a1}/{c}{a0}', (4, 2))]
for k, (name, pat, idx) in enumerate(mix):
    rr = 116 + k
    t(cpr, f'B{rr}', name, S_LBL)
    for c in TC + 'G':
        parts = []
        for mode in (1, 2, 3):
            if k == 1:
                parts.append(pat.format(c=c, a1=start[mode] + 3, a0=start[mode] + 2, a2=start[mode] + 4))
            elif k == 0:
                parts.append(pat.format(c=c, a1=start[mode] + 1, a0=start[mode]))
            else:
                parts.append(pat.format(c=c, a1=start[mode] + 4, a0=start[mode] + 2))
        f(cpr, f'{c}{rr}', f'IFERROR(CHOOSE($C$5,{",".join(parts)}),0)', S_PCT)
t(cpr, 'H116', "4 tiers model Q4-26 share of international payments (rows 19 / 96 / 173 / 250); 2027+ keep the tier model's assumptions", S_NOTE)
t(cpr, 'H117', "4 tiers model Q4-26 share of cashout at other ATMs (rows 27 / 104 / 181 / 258); 2027+ keep the assumptions", S_NOTE)
t(cpr, 'H118', 'Not priced in the model yet (international ATM fees)', S_NOTE)
for row, (m2, m3), based, where in ((74, (0, 0), 'Non-cash payments (section 6)', "'4 tiers model' row 21 (Black 98, Premium 175, Elite 252)"),
                                     (76, (1, 1), 'Cashout at all ATMs (section 6)', 'row 30 / 107 / 184 / 261'),
                                     (77, (2, 2), 'C2C to other banks (section 6)', 'row 35 / 112 / 189 / 266')):
    for c in TC:
        f(cpr, f'{c}{row}', f'CHOOSE($C$5,1,IF(ISNUMBER({c}{MUL[(2, m2)]}),{c}{MUL[(2, m2)]},IFERROR(AVERAGE({c}55,{c}58,{c}59,{c}61,{c}62),1)),'
                             f'IF(ISNUMBER({c}{MUL[(3, m3)]}),{c}{MUL[(3, m3)]},IFERROR(AVERAGE({c}64,{c}67,{c}68,{c}70,{c}71),1)))')
    t(cpr, f'G{row}', based)
    t(cpr, f'H{row}', where)
cpr.root.find(N + 'dimension').set('ref', 'B1:H118')
cpr.save()
for base, c in zip((27, 50, 73, 96), TC):
    f(cp, f'C{base}', f'"Non-cash ×"&TEXT({CPR}!${c}$74,"0.00")&"   cashout ×"&TEXT({CPR}!${c}$76,"0.00")&"   C2C ×"&TEXT({CPR}!${c}$77,"0.00")'
                      f'&"   transactions ×"&TEXT({CPR}!${c}$75,"0.00")&"   card balance ×"&TEXT({CPR}!${c}$78,"0.00")'
                      f'&"   deposits ×"&TEXT({CPR}!${c}$80,"0.00")&"   FX ×"&TEXT({CPR}!${c}$79,"0.00")')

# ================================================================ 4. FINANCE UPDATE: interchange, Visa fee, perks
LOC = {'D': 0.005, 'E': 0.006, 'F': 0.006, 'G': 0.005, 'H': 0.006, 'I': 0.006, 'J': 0.006, 'K': 0.005}
INT = {'D': 0.012, 'E': 0.015, 'F': 0.015, 'G': 0.012, 'H': 0.015, 'I': 0.015, 'J': 0.015, 'K': 0.012}
for c in 'DEFGHIJK':
    val(em, f'{c}45', LOC[c])
    val(em, f'{c}50', INT[c])
t(em, 'B194', 'v16 (30.09.2026): rates by tier from the finance update', em.style('B170'))
t(em, 'B195', 'International interchange margin, weighted by international volume', em.style('B187'))
t(em, 'C195', '%')
t(em, 'B196', 'Visa share of international non-cash payments (2% cross-currency fee applies)', em.style('B187'))
t(em, 'C196', '%')
for c in 'NOPQ':
    f(em, f'{c}195', f'IFERROR(SUMPRODUCT(($D$148:$K$148={c}$148)*$D$50:$K$50*$D$154:$K$154)/{c}154,AVERAGEIF($D$148:$K$148,{c}$148,$D$50:$K$50))', 288)
    f(em, f'{c}196', f'IFERROR(SUMPRODUCT(($D$148:$K$148={c}$148)*(LEFT($D$6:$K$6,4)="Visa")*$D$154:$K$154)/{c}154,0)', 288)
t(em, 'B197', 'Finance 30.09.2026: interchange 0.5% domestic / 1.2% international on standard cards (ArCa, Visa Classic, Visa Digital); '
              '0.6% / 1.5% on Visa Gold and above (MC World, World Elite, Infinite, Metal). Visa settles in EUR: clients paying from a non-EUR account '
              'get the Visa cross rate + 2%; Mastercard settles in USD with no fee.', em.style('B193'))
em.save()

BLK = [(0, 'N'), (77, 'O'), (154, 'P'), (231, 'Q')]
for off, tc in BLK:
    for c in 'DEFGHIJK':
        r18 = 18 + off
        old = tm.formula(f'{c}{r18}')
        assert old.startswith('1.5%*'), (c, r18, old)
        f(tm, f'{c}{r18}', old.replace('1.5%*', f"{EC}!${tc}$195*", 1))
        r37, r38, r20, r19 = 37 + off, 38 + off, 20 + off, 19 + off
        f(tm, f'{c}{r37}', f"{c}{r38}+{c}{r20}*{c}{r19}*{EC}!${tc}$196*{CP}!$D$111*{CP}!$D$110")
    cpc = {'N': 'C', 'O': 'D', 'P': 'E', 'Q': 'F'}[tc]
    f(tm, f'D{19 + off}', f"{CPR}!${cpc}$116")
    f(tm, f'D{23 + off}', f"IFERROR(D{19 + off}/(1-{EC}!${tc}$181),0)")
    f(tm, f'D{27 + off}', f"{CPR}!${cpc}$117")
t(tm, 'B37', 'FX conversion fee for the period (incl. Visa 2% cross-currency fee, v16)')
for c in 'OPQ':
    f(tm, f'{c}175', f"10*{FXR}!$F$25")                                           # Mastercard World perks, 10 EUR a year
expect(tm, 'I313', '20000')
t(tm, 'B313', 'Visa Infinite / World Elite perks (finance 30.09.2026: 20k AMD a year)')
tm.save()

pn = book.sheet('PnL all tiers')
t(pn, 'J48', 'Premium: Mastercard World perks, 10 EUR a year. Elite: Infinite / World Elite perks 20k AMD a year plus taxi rides.')
pn.save()

# ================================================================ 5. FX: price position block on the Control panel
Q = {'USD': ('D', 'E', 'D'), 'EUR': ('F', 'G', 'F'), 'RUB': ('H', 'I', 'H')}    # buy col, sell col, mid col on 'FX ranking'
rng = lambda col: f"{FXR}!${col}$5:${col}$21"                                    # noqa: E731
t(cp, 'B99', 'FX PRICE POSITION (all tiers)', 813)
for c, h in zip('CDFGH', ('Fast Bank today', 'Parameters', 'Low-end', 'Mid-point', 'High-end')):
    t(cp, f'{c}99', h, 813 if c in 'CD' else 816)
t(cp, 'O99', 'BENCHMARK BASIS', 816)
r = 100
for cur in ('USD', 'EUR', 'RUB'):
    bcol, scol, mcol = Q[cur]
    for side, col, lab in (('buy', bcol, 'lowest buy rate'), ('sell', scol, 'highest sell rate')):
        t(cp, f'B{r}', f'{cur} {side} rate: place in the market ranking (1 = {lab}, most profitable for the bank)', 360)
        f(cp, f'C{r}', f"{FXR}!{col}27", S_INT)
        fb_now = {'USD': (11, 15), 'EUR': (12, 13), 'RUB': (13, 13)}[cur][0 if side == 'buy' else 1]
        val(cp, f'D{r}', fb_now, S_INT_IN)
        f(cp, f'F{r}', f"{FXR}!{col}23", S_INT)
        f(cp, f'G{r}', f"ROUND(({FXR}!{col}23+1)/2,0)", S_INT)
        val(cp, f'H{r}', 1, S_INT)
        t(cp, f'O{r}', f"rate.am 30.09.2026 14:45: Fast Bank {side}s {cur} at place " + str(fb_now) + " of the banks quoting; low-end = last place", 827)
        r += 1
assert r == 106
t(cp, 'B106', 'Share of FX turnover where clients buy FX from the bank, %', 360)
val(cp, 'C106', 0.5, S_PCT)
val(cp, 'D106', 0.5, S_PCT_IN)
t(cp, 'O106', 'Weights the sell-side and buy-side margins; no split in the data, 50/50 assumed', 827)
for k, cur in enumerate(('USD', 'EUR', 'RUB')):
    rr = 107 + k
    bcol, scol, mcol = Q[cur]
    mid = f"{FXR}!${mcol}$25"
    t(cp, f'B{rr}', f'{cur} FX margin vs market mid-rate, %', 360)
    for c in 'CDFGH':
        rb, rs = 100 + 2 * k, 101 + 2 * k
        f(cp, f'{c}{rr}', f"$D$106*(LARGE({rng(scol)},{c}{rs})-{mid})/{mid}+(1-$D$106)*({mid}-SMALL({rng(bcol)},{c}{rb}))/{mid}",
          S_PCT if c != 'D' else S_PCT)
    t(cp, f'O{rr}', "Margin at the chosen places vs the market mid-rate ((median buy + median sell) / 2); feeds the tier FX rows", 827)
t(cp, 'B110', 'Visa cross-currency fee charged to the client, %', 360)
val(cp, 'C110', 0.02, S_PCT)
val(cp, 'D110', 0.02, S_PCT_IN)
t(cp, 'O110', 'Finance 30.09.2026: Visa settles in EUR; paying from a non-EUR account = Visa cross rate + 2%. Mastercard (USD): no fee', 827)
t(cp, 'B111', 'Share of Visa international spend charged the fee, %', 360)
share = (f"1-IFERROR(SUMIFS('Cards dataset'!$P$2:$P${ROWS},'Cards dataset'!$AB$2:$AB${ROWS},\"Euro\",'Cards dataset'!$A$2:$A${ROWS},\"Visa*\")"
         f"/SUMIFS('Cards dataset'!$P$2:$P${ROWS},'Cards dataset'!$A$2:$A${ROWS},\"Visa*\"),0)")
f(cp, 'C111', share, S_PCT)
f(cp, 'D111', 'C111', S_PCT_IN)
t(cp, 'O111', "1 − EUR-account share of Visa international spend ('Cards dataset' columns P and AB, Jun–Aug 2026)", 827)
for base in (15, 38, 61, 84):
    for k, cur in enumerate(('USD', 'EUR', 'RUB')):
        rr = base + k
        t(cp, f'B{rr}', f'{cur} FX margin vs market mid (set by price position, row {107 + k}), %')
        for c in 'CDFGH':
            f(cp, f'{c}{rr}', f'${c}${107 + k}')
    t(cp, f'O{base}', 'rate.am 30.09.2026 (16 banks): margin at our place in the buy / sell ranking, rows 99–111. Low-end = last place, high-end = place 1')
cp.save()

# ================================================================ 6. new sheets: 'FX ranking' and 'v16 changes'
BANKS = [('Amio Bank', 34, 360, 365, 407, 419, 4.20, 4.41), ('AraratBank', 50, 360, 364.5, 405, 417, 4.23, 4.45),
         ('Acba bank', 62, 360.5, 365.5, 407, 417, 4.23, 4.41), ('Ameriabank', 26, 360.5, 365.5, 404.5, 418.5, 4.16, 4.41),
         ('Ardshinbank', 70, 360.5, 365.5, 405, 418, 4.17, 4.50), ('Armeconombank', 52, 360.5, 365.5, 406, 417, 4.22, 4.42),
         ('Evocabank', 16, 360.5, 365.5, 406, 417, 4.22, 4.40), ('ID Bank', 20, 360.5, 365, 405, 416, 4.20, 4.43),
         ('Inecobank', 23, 360.5, 365, 407, 418, 4.17, 4.43), ('Unibank', 57, 360.5, 365, 405, 417, 4.20, 4.45),
         ('ArmSwissBank', 1, 361, 365, 408.5, 415, 4.24, 4.42), ('Artsakhbank', 9, 362, 365.5, 408, 418, 4.18, 4.40),
         ('Byblos Bank Armenia', 5, 361, 366, 406, 418, None, None), ('Converse Bank', 34, 361.5, 365.5, 408, 418, 4.26, 4.47),
         ('Fast Bank', 39, 361, 364.5, 407.5, 416, 4.24, 4.40), ('VTB Bank (Armenia)', 53, 361.5, 365, 408, 413, 4.18, 4.44),
         ('Mellat Bank', 1, None, None, None, None, None, None)]


def ws_xml(cells, widths, freeze=None):
    ws = etree.Element(N + 'worksheet', nsmap={None: N[1:-1], 'r': RNS})
    views = etree.SubElement(ws, N + 'sheetViews')
    etree.SubElement(views, N + 'sheetView', showGridLines='0', workbookViewId='0')
    etree.SubElement(ws, N + 'sheetFormatPr', defaultRowHeight='16')
    cl = etree.SubElement(ws, N + 'cols')
    for i, w in widths:
        etree.SubElement(cl, N + 'col', min=str(i), max=str(i), width=str(w), customWidth='1')
    sd = etree.SubElement(ws, N + 'sheetData')
    byrow = {}
    for ref, kind, v, s in cells:
        byrow.setdefault(int(re.search(r'\d+', ref).group()), []).append((ref, kind, v, s))
    key = lambda ref: (len(re.match('[A-Z]+', ref).group()), re.match('[A-Z]+', ref).group())   # noqa: E731
    for rn in sorted(byrow):
        row = etree.SubElement(sd, N + 'row', r=str(rn))
        for ref, kind, v, s in sorted(byrow[rn], key=lambda x: key(x[0])):
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
                etree.SubElement(c, N + 'v').text = repr(float(v)) if not float(v).is_integer() else str(int(v))
    etree.SubElement(ws, N + 'pageMargins', left='0.7', right='0.7', top='0.75', bottom='0.75', header='0.3', footer='0.3')
    return S(ws)


fx = [('B1', 't', 'FX RATES BY BANK – buy / sell quotes used for the FX price position (Control panel rows 99–111)', S_HDR),
      ('B2', 't', 'Source: rate.am, 30 Sep 2026 14:45 (screenshots from Alex). Buy = the bank buys the currency from the client; sell = the bank sells it.', S_NOTE)]
for c, h in zip('BCDEFGHI', ('Bank', 'Branches', 'USD buy', 'USD sell', 'EUR buy', 'EUR sell', 'RUB buy', 'RUB sell')):
    fx.append((f'{c}4', 't', h, S_TIER))
for i, row in enumerate(BANKS):
    rn = 5 + i
    fx.append((f'B{rn}', 't', row[0], S_LBL if row[0] != 'Fast Bank' else 892))
    fx.append((f'C{rn}', 'v', row[1], S_NUM))
    for c, v in zip('DEFGHI', row[2:]):
        if v is not None:
            fx.append((f'{c}{rn}', 'v', v, S_DEC2))
labels = {23: 'Banks quoting, n', 24: 'Median quote', 25: 'Market mid-rate: (median buy + median sell) / 2',
          26: 'Fast Bank quote', 27: 'Fast Bank place (1 = most profitable: lowest buy / highest sell)', 28: 'Fast Bank margin vs mid-rate, %'}
for rn, lab in labels.items():
    fx.append((f'B{rn}', 't', lab, S_LBL))
for cur, (bc, sc, mc) in Q.items():
    for c in (bc, sc):
        fx.append((f'{c}23', 'f', f'COUNT({c}5:{c}21)', S_NUM))
        fx.append((f'{c}24', 'f', f'MEDIAN({c}5:{c}21)', S_DEC2))
        fx.append((f'{c}26', 'f', f'INDEX({c}5:{c}21,MATCH("Fast Bank",$B$5:$B$21,0))', S_DEC2))
    fx.append((f'{bc}25', 'f', f'({bc}24+{sc}24)/2', S_DEC2))
    fx.append((f'{bc}27', 'f', f'1+COUNTIF({bc}5:{bc}21,"<"&{bc}26)', S_NUM))
    fx.append((f'{sc}27', 'f', f'1+COUNTIF({sc}5:{sc}21,">"&{sc}26)', S_NUM))
    fx.append((f'{bc}28', 'f', f'({mc}25-{bc}26)/{mc}25', S_PCT))
    fx.append((f'{sc}28', 'f', f'({sc}26-{mc}25)/{mc}25', S_PCT))
fx.append(('B30', 't', "How the model uses it: the Control panel sets Fast Bank's place for each side (rows 100–105). The margin at that place vs the "
                       "mid-rate, weighted by the buy / sell mix (row 106), replaces v15's 'half of the bid-ask spread'. The tier FX revenue scales "
                       "with (parameter margin ÷ today's margin), as before.", S_NOTE))
fx.append(('B31', 't', "Fast Bank today: USD buy 11th / sell 15th of 16, EUR 12th / 13th of 16, RUB 13th / 13th of 15 – near the bottom by margin: "
                       "we pay clients more when buying and charge them less when selling.", S_NOTE))
fx_part = ws_xml(fx, [(1, 2), (2, 44), (3, 10)] + [(i, 11) for i in range(4, 10)])

CHG = ['DEBIT CARDS MODEL v16 – CHANGES vs v15 (30.09.2026)', '',
       '1. Tiers: Free = Visa Digital + ArCa Classic; Black = Visa Classic + Visa Gold (Visa Gold moved from Premium); Premium = Mastercard World; '
       'Elite = MC World Elite + Visa Infinite + Infinite Metal. Changed: 8 cards model H148, paid-share N39:P39 (now mapping-based), Control panel '
       'C37 (Black as-is fee = weighted Classic/Gold) / C49 / C72 / C95, block titles, Cards dataset tier of 17,765 Visa Gold cards, CB Inputs C14, '
       'CB Client view persona (Petrosyan family).',
       '2. FX: the benchmark is no longer the half bid-ask spread. New sheet \'FX ranking\' (rate.am 30.09.2026, 17 banks) and Control panel rows '
       '99–111: our place in the buy and sell rankings sets the margin vs the market mid-rate. Tier FX rows 15–17 / 38–40 / 61–63 / 84–86 now link '
       'to that block. Defaults = today\'s places, so the FX factor is 1.',
       '3. New data: \'Cards dataset\' gets 14 columns (O–AB) from final_report.xlsx, joined by contract ID (96,895 of 96,906 cards matched; the '
       'other 11 are 0): local / international non-cash volume and count, cashout at Fast Bank / other Armenian / foreign ATMs, cashout count, '
       'C2C to other banks volume and count, tariff service fee, card currency. Client profiles sections 6–8 use them: the non-cash, cashout and '
       'C2C multipliers (rows 74 / 76 / 77) now come from their own fields instead of total outflow; Q4-26 international share and other-ATM '
       'share in the tier model (rows 19 / 27 and equivalents) come from section 8.',
       '4. Finance update: interchange 0.5% domestic / 1.2% international on standard cards, 0.6% / 1.5% on Visa Gold and above (8 cards model rows '
       '45 / 50; new tier row 195 replaces the hard-coded 1.5%). Visa 2% cross-currency fee added to FX revenue (tier row 37, Control panel D110 / '
       'D111, 8 cards model row 196). Perks: Premium (MC World) 10 EUR a year, Elite Visa Infinite / World Elite 20k AMD a year (unchanged). '
       'C2C 0.5% confirmed (unchanged).',
       '', 'Open from the finance list: marketing spend Mar–Aug 2026 and cards sold (Zhanna Mkrtumyan); fee-waiver rules by card type (8.3); '
       'ArCa Pay / SBP transfers are free until 31 Dec 2026 – not modelled (share of C2C via these channels unknown).',
       'Tier eligible-spend divisors (4 tiers model rows 136 / 213 / 290: 3 / 2.1 / 1.7) were not changed after the tier move – check them.']
chg_part = ws_xml([(f'B{i + 1}', 't', s, S_HDR if i == 0 else S_LBL) for i, s in enumerate(CHG) if s], [(1, 2), (2, 180)])


def add_sheet(name, xml, after):
    wb = X(P['xl/workbook.xml'])
    rels = X(P['xl/_rels/workbook.xml.rels'])
    shs = wb.find(N + 'sheets')
    nums = [int(re.search(r'(\d+)\.xml$', n).group(1)) for n in P if re.match(r'xl/worksheets/sheet\d+\.xml$', n)]
    part = f'xl/worksheets/sheet{max(nums) + 1}.xml'
    P[part] = xml
    rid = 'rId%d' % (max(int(r.get('Id')[3:]) for r in rels) + 1)
    etree.SubElement(rels, PKG + 'Relationship', Id=rid, Target=part[3:],
                     Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet')
    anchor = next(s for s in shs if s.get('name') == after)
    pos = list(shs).index(anchor) + 1
    el = etree.Element(N + 'sheet', name=name, sheetId=str(max(int(s.get('sheetId')) for s in shs) + 1))
    el.set('{%s}id' % RNS, rid)
    anchor.addnext(el)
    dn = wb.find(N + 'definedNames')
    if dn is not None:
        for d in dn:
            if d.get('localSheetId') is not None and int(d.get('localSheetId')) >= pos:
                d.set('localSheetId', str(int(d.get('localSheetId')) + 1))
    for v in wb.find(N + 'bookViews'):
        for a in ('activeTab', 'firstSheet'):
            if v.get(a) and int(v.get(a)) >= pos:
                v.set(a, str(int(v.get(a)) + 1))
    P['xl/workbook.xml'] = S(wb)
    P['xl/_rels/workbook.xml.rels'] = S(rels)
    ct = X(P['[Content_Types].xml'])
    etree.SubElement(ct, CTN + 'Override', PartName='/' + part,
                     ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
    P['[Content_Types].xml'] = S(ct)
    app = P['docProps/app.xml'].decode('utf-8')
    app = re.sub(r'(<vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1), app)
    app = re.sub(r'<TitlesOfParts><vt:vector size="(\d+)"', lambda m: f'<TitlesOfParts><vt:vector size="{int(m.group(1)) + 1}"', app)
    app = app.replace(f'<vt:lpstr>{after}</vt:lpstr>', f'<vt:lpstr>{after}</vt:lpstr><vt:lpstr>{name}</vt:lpstr>', 1)
    P['docProps/app.xml'] = app.encode('utf-8')


P['xl/sharedStrings.xml'] = S(sst_root)
add_sheet('FX ranking', fx_part, 'Market benchmarking')
add_sheet('v16 changes', chg_part, 'Control panel')

# ---------------------------------------------------------------- recalc on open, drop the calc chain
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
rels = X(P['xl/_rels/workbook.xml.rels'])
for r_ in list(rels):
    if r_.get('Type').endswith('/calcChain'):
        rels.remove(r_)
P['xl/_rels/workbook.xml.rels'] = S(rels)
P.pop('xl/calcChain.xml', None)
ct = X(P['[Content_Types].xml'])
for o in list(ct):
    if o.get('PartName') == '/xl/calcChain.xml':
        ct.remove(o)
P['[Content_Types].xml'] = S(ct)
book.write(OUT)
print('written', OUT)
