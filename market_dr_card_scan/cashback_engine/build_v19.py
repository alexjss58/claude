"""Debit cards model v19 (01.10.2026): cards P&L mapped into Alex's 'Bank PnL' structure.
    python3 build_v19.py <alex_v18.xlsx> <out.xlsx>
Bank PnL, new columns AX:BF – cards model 2027 / 2028 in bank lines (AMD '000), deltas vs Budget 2027 / 2028 and Ambitious 2028 on the
card-only lines, card share of each budget line, mapping note. Helper bridge below the P&L (rows 96+) with checks.
Decisions (Alex, 01.10.2026): card balance income gross – FTP income -> row 8, client interest -> row 13; allocated fixed card OPEX = memo,
not mapped; processing -> row 37 (fee & commission expense), card production + card database -> row 60, perks -> row 67,
marketing -> row 69; client profile = whatever the Control panel selects.
"""
import re
import sys

from lxml import etree

from xmlbook import N, S, X, Book

IN, OUT = sys.argv[1:3]
book = Book(IN)
P = book.parts
p = book.sheet('Bank PnL')
CP = "'Cards PnL all tiers'"
T4 = "'4 tiers model (to be lineup)'"
E8 = "'8 cards model (as is lineup)'"
OFF = [0, 77, 154, 231]
YR = {'AX': ('E', 'I', 'O', 'AE'), 'AY': ('F', 'J', 'P', 'AF')}   # cards PnL col, tier year col, tier summary col, budget col


def f(ref, fm, s):
    p.f(ref, fm, s)


def t(ref, txt, s='1060'):
    p.t(ref, txt, s)


# ---------------------------------------------------------------- helper bridge (rows 96+)
H = {}
r = 96
t(f'C{r}', "CARDS MODEL → BANK P&L BRIDGE (AMD '000 = cards model AMD × 1/1,000; follows the client profile selected on the Control panel)", p.style('C3'))
t(f'AX{r}', '2027', p.style('AE4')); t(f'AY{r}', '2028', p.style('AE4'))


def helper(key, label, fm_by_col, note=''):
    global r
    r += 1
    H[key] = r
    t(f'C{r}', label, '1060')
    for col, fm in fm_by_col.items():
        f(f'{col}{r}', fm, p.style('AE25'))
    if note:
        t(f'BF{r}', note)


def tiers(expr):
    """sum over the four tiers; expr(k, o) gives one tier's term"""
    return '(' + '+'.join(expr(k, o) for k, o in enumerate(OFF)) + ')/1000'


for col, (pc, yc, sc, bc) in YR.items():
    pass
helper('ftp', '1. Card balances: FTP income (AMD at 11.1%, FX at 7.1%)',
       {col: tiers(lambda k, o, pc=pc, sc=sc, yc=yc: f"{CP}!{pc}{24 + k}*{T4}!{sc}{10 + o}*IFERROR(((1-{T4}!{yc}{49 + o})*{E8}!$D$90+{T4}!{yc}{49 + o}*{E8}!$D$97)/{T4}!{yc}{44 + o},0)")
        for col, (pc, yc, sc, bc) in YR.items()},
       "Average active cards × interest per card × FTP rate ÷ margin ('4 tiers model' rows 10 / 44 / 49; FTP in '8 cards model' D90 / D97)")
helper('nii', '   net interest margin on card balances (cards model)', {col: f"{CP}!{pc}39*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('cli', '   client interest paid on card balances', {col: f"{col}{H['ftp']}-{col}{H['nii']}" for col in YR})
helper('proc', '2. Card processing: ArCa, Visa / Mastercard',
       {col: tiers(lambda k, o, pc=pc, yc=yc: f"{CP}!{pc}{24 + k}*{T4}!{yc}{67 + o}") for col, (pc, yc, sc, bc) in YR.items()})
helper('db', '3. Card database',
       {col: tiers(lambda k, o, pc=pc, yc=yc: f"{CP}!{pc}{24 + k}*{T4}!{yc}{70 + o}") for col, (pc, yc, sc, bc) in YR.items()})
helper('fix', '4. Allocated fixed card OPEX (memo – share of existing bank OPEX, not mapped)',
       {col: tiers(lambda k, o, pc=pc, yc=yc: f"{CP}!{pc}{24 + k}*{T4}!{yc}{71 + o}") for col, (pc, yc, sc, bc) in YR.items()},
       'Not added to bank lines: these costs already sit in staff, operations and admin lines of the bank budget')
helper('recm', '   check: recurring OPEX in the cards model', {col: f"{CP}!{pc}49*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('recd', '   difference (should be 0)', {col: f"{col}{H['proc']}+{col}{H['db']}+{col}{H['fix']}-{col}{H['recm']}" for col in YR})
helper('mkt', '5. Marketing for new cards',
       {col: tiers(lambda k, o, pc=pc: f"{CP}!{pc}{31 + k}*{T4}!$I${75 + o}") for col, (pc, yc, sc, bc) in YR.items()})
helper('prod', '6. Card production: plastic, delivery, embossing, activation',
       {col: tiers(lambda k, o, pc=pc: f"{CP}!{pc}{31 + k}*({T4}!$I${76 + o}+{T4}!$I${77 + o}+{T4}!$I${78 + o}+{T4}!$I${79 + o})")
        for col, (pc, yc, sc, bc) in YR.items()})
helper('onem', '   check: first-year OPEX in the cards model', {col: f"{CP}!{pc}50*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('oned', '   difference (should be 0)', {col: f"{col}{H['mkt']}+{col}{H['prod']}-{col}{H['onem']}" for col in YR})
helper('perk', '7. Perks', {col: f"{CP}!{pc}48*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('cb', '8. Cashback', {col: f"{CP}!{pc}46*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('upl', '9. Deposit-rate uplift', {col: f"{CP}!{pc}47*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('opm', 'Card operating profit, cards model (incl. allocated fixed OPEX)', {col: f"{CP}!{pc}51*1000" for col, (pc, yc, sc, bc) in YR.items()})
helper('opb', 'Card operating profit in bank structure (row 85)', {col: f"{col}85" for col in YR})
helper('opd', '   difference = allocated fixed card OPEX; check (should be 0)', {col: f"{col}{H['opb']}-{col}{H['opm']}-{col}{H['fix']}" for col in YR})

# ---------------------------------------------------------------- mapping into the bank rows
MAP = {  # row: (formula template with {c}, kind, note)
    8: ("{c}%d" % H['ftp'], 'bank', 'FTP income on card balances (gross)'),
    5: ('SUM({c}6:{c}8)', 'bank', ''),
    11: ("-{c}%d" % H['upl'], 'bank', 'Deposit-rate uplift for cardholders'),
    13: ("-{c}%d" % H['cli'], 'bank', 'Interest paid to clients on card balances'),
    10: ('SUM({c}11:{c}13)', 'bank', ''),
    9: ('SUM({c}10,{c}14:{c}20)', 'bank', ''),
    21: ('SUM({c}5,{c}9)', 'bank', 'Equals the cards model net interest margin on card balances'),
    26: (None, 'card', 'Not in the cards model (POS acquiring)'),
    27: ("%s!{p}44*1000" % CP, 'card', 'Service fees'),
    28: ("%s!{p}40*1000" % CP, 'card', 'Interchange'),
    29: ("%s!{p}41*1000" % CP, 'card', 'Cashout fees (Fast Bank and other ATMs)'),
    30: ("%s!{p}42*1000" % CP, 'card', 'C2C transfer fees'),
    31: ("%s!{p}43*1000" % CP, 'card', "FX: cardholders' conversions (card is AMD-only)"),
    32: ("-{c}%d" % H['cb'], 'card', 'Cashback'),
    25: ('SUM({c}26:{c}32)', 'card', ''),
    23: ('SUM({c}24:{c}25,{c}33:{c}35)', 'bank', ''),
    37: ("-{c}%d" % H['proc'], 'bank', 'Card processing: ArCa, Visa / Mastercard'),
    36: ('SUM({c}37:{c}40)', 'bank', ''),
    22: ('SUM({c}23,{c}36,{c}41:{c}43)', 'bank', ''),
    44: ('SUM({c}21:{c}22)', 'bank', ''),
    60: ("-{c}%d-{c}%d" % (H['prod'], H['db']), 'bank', 'Card production for new cards + card database'),
    67: ("-{c}%d" % H['perk'], 'bank', 'Perks'),
    59: ('SUM({c}60:{c}67)', 'bank', ''),
    69: ("-{c}%d" % H['mkt'], 'bank', 'Marketing for new cards'),
    68: ('SUM({c}69:{c}70)', 'bank', ''),
    46: ('+SUM({c}47,{c}59,{c}68,{c}71,{c}78:{c}80,{c}82:{c}84)', 'bank', 'Allocated fixed card OPEX excluded (memo, helper row %d)' % H['fix']),
    85: ('SUM({c}44,{c}46)', 'bank', 'Card contribution before allocated overhead'),
    87: ('SUM({c}86,{c}44,{c}46)', 'bank', ''),
    88: ('{c}87*-18%', 'bank', 'Same 18% as the budget'),
    89: ('SUM({c}87:{c}88)', 'bank', ''),
}
for row, (tmpl, kind, note) in MAP.items():
    vs = p.style(f'AE{row}') or p.style('AE25')
    ps = p.style(f'AH{row}') or '1118'
    for col, (pc, yc, sc, bc) in YR.items():
        if tmpl:
            f(f'{col}{row}', tmpl.format(c=col, p=pc), vs)
    if tmpl:
        if kind == 'card':
            f(f'AZ{row}', f'AX{row}-AE{row}', vs)
            f(f'BA{row}', f'AY{row}-AF{row}', vs)
            f(f'BB{row}', f'AY{row}-AS{row}', vs)
        f(f'BC{row}', f'IFERROR(AX{row}/AE{row},"")', ps)
        f(f'BD{row}', f'IFERROR(AY{row}/AF{row},"")', ps)
        f(f'BE{row}', f'IFERROR(AY{row}/AS{row},"")', ps)
    if note:
        t(f'BF{row}', note)

# headers
t('AX2', 'CARDS MODEL IN BANK P&L STRUCTURE', p.style('AR2'))
for col, h3, h4 in (('AX', 'Cards model', '2027'), ('AY', 'Cards model', '2028'), ('AZ', 'Δ model − budget', '2027'),
                    ('BA', 'Δ model − budget', '2028'), ('BB', 'Δ model − ambitious', '2028'), ('BC', 'Cards % of budget', '2027'),
                    ('BD', 'Cards % of budget', '2028'), ('BE', 'Cards % of ambitious', '2028'), ('BF', 'Cards model source / note', '')):
    t(f'{col}3', h3, p.style('AE3'))
    t(f'{col}4', h4, p.style('AE4'))
t('BF2', "Δ only on card-only lines (rows 25–32); bank-wide lines show the cards share. Cards = whole planned card base ('Planned KPIs').", '1060')

# column widths
s_cols = p.root.find(N + 'cols')
last = s_cols[-1]
assert int(last.get('min')) <= 50 and last.get('max') == '16384', last.attrib
tail = dict(last.attrib)
last.set('max', '49')
for mn, mx, w in ((50, 57, '14'), (58, 58, '70')):
    etree.SubElement(s_cols, N + 'col', min=str(mn), max=str(mx), width=w, style='1060', customWidth='1')
tail['min'] = '59'
etree.SubElement(s_cols, N + 'col', **tail)
p.root.find(N + 'dimension').set('ref', f'B2:BF{r}')
p.save()

wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT, 'helper rows', H)
