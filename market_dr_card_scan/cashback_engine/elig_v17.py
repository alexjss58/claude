"""Eligible-to-non-cash conversion by tier, excluding gold-loan clients (Alex 30.09.2026).
    python3 elig_v17.py <in.xlsx> <out.xlsx> A|B
Client profiles section 9 (rows 119-122): mode 1 = all engine clients ('CB Results' row 12); modes 2-3 = excluding gold-loan clients
(static, from the engine sample joined to the v13 card data). 4 tiers model rows 59 / 136 / 213 / 290 and Break-even curves row 27 use row 122.
"""
import json, sys
from lxml import etree
from xmlbook import N, S, X, Book
IN, OUT, OPT = sys.argv[1:4]
R = json.load(open('elig_excl_gold.json'))[OPT]
book = Book(IN)
cpr = book.sheet('Client profiles')


def t(sh, ref, txt, s):
    sh.t(ref, txt, s)


def f(sh, ref, fm, s=None):
    sh.f(ref, fm, s if s is not None else sh.style(ref))


def v(sh, ref, x, s):
    c = sh.cell(ref); sh._reset(c, s); etree.SubElement(c, N + 'v').text = repr(float(x))


TC = [('C', 'Free', 'D'), ('D', 'Black', 'E'), ('E', 'Premium', 'F'), ('F', 'Elite', 'G')]
t(cpr, 'B119', '9. Eligible share of non-cash spend – converts the cashback target on eligible spend into the P&L\'s non-cash basis', 896)
for c, name, _ in TC:
    t(cpr, f'{c}119', name, 898)
t(cpr, 'H119', 'Notes', 899)
t(cpr, 'B120', '  All engine clients with card spend in Aug 2026 (mode 1)', 894)
t(cpr, 'B121', '  Excluding gold-loan clients (modes 2 and 3)', 894)
t(cpr, 'B122', 'Used by the tier model (mode in use)', 892)
for c, name, rc in TC:
    f(cpr, f'{c}120', f"'CB Results'!{rc}$12", 810)
    v(cpr, f'{c}121', R[name][0], 810)
    f(cpr, f'{c}122', f'CHOOSE($C$5,{c}120,{c}121,{c}121)', 810)
kept = ', '.join(f"{n} {R[n][2]:.0%}" for n in ('Free', 'Black', 'Premium', 'Elite'))
t(cpr, 'H120', "'CB Results' row 12 (live)", 891)
t(cpr, 'H121', f"Engine sample (7,640 clients, Aug 2026) joined to the v13 card data by client ID; gold-loan client = holds a gold-backed loan or a "
               f"gold-loan card. Clients kept: {kept}. Dormant clients are already outside the engine (card spend in the month required). "
               f"Static – refresh if the engine data or the tier split changes.", 891)
t(cpr, 'H122', "4 tiers model rows 59 / 136 / 213 / 290; Break-even curves row 27", 891)
cpr.root.find(N + 'dimension').set('ref', 'B1:H122')
cpr.save()

tm = book.sheet('4 tiers model (to be lineup)')
old59 = "IF('Control panel'!$D$22=\"Engine\",'Control panel'!$C$22,'Control panel'!$D$19)"
for c in 'EFGHIJK':
    assert tm.formula(f'{c}59') == old59, tm.formula(f'{c}59')
    f(tm, f'{c}59', "IF('Control panel'!$D$22=\"Engine\",'Control panel'!$C$22,'Control panel'!$D$19*'Client profiles'!$C$122)")
    for row, rc, pc in ((136, 'E', 'D'), (213, 'F', 'E'), (290, 'G', 'F')):
        fm = tm.formula(f'{c}{row}')
        a = f"'CB Results'!${rc}$12"
        assert a in fm, (c, row, fm)
        f(tm, f'{c}{row}', fm.replace(a, f"'Client profiles'!${pc}$122"))
tm.save()
be = book.sheet('Break-even curves')
for c, pc in (('C', 'D'), ('D', 'E'), ('E', 'F')):
    f(be, f'{c}27', f"IFERROR(1/'Client profiles'!${pc}$122,1)")
be.save()
chg = book.sheet('v16 changes')
chg.t('B7', "5. Cashback: the eligible-spend divisors are the engine's eligible share of non-cash spend for the tier split, excluding gold-loan "
            "clients in profile modes 2–3 (Client profiles section 9: " + ', '.join(f"{n} {R[n][0]:.0%}" for n in ('Free', 'Black', 'Premium', 'Elite')) +
            "); mode 1 uses all engine clients ('CB Results' row 12). In Engine mode the engine rate is used as is.", chg.style('B7'))
chg.save()
P = book.parts
wb = X(P['xl/workbook.xml']); wb.find(N + 'calcPr').set('fullCalcOnLoad', '1'); P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
