"""v16.3: remove the Visa 2% cross-currency fee (already inside the 8 cards model FX revenue, Alex 30.09.2026)."""
import sys
from xmlbook import N, S, X, Book
IN, OUT = sys.argv[1:3]
book = Book(IN)
P = book.parts


def clear(sh, ref):
    c = sh.get(ref)
    if c is not None:
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)


tm = book.sheet('4 tiers model (to be lineup)')
for off in (0, 77, 154, 231):
    for c in 'DEFGHIJK':
        old = tm.formula(f'{c}{37 + off}')
        assert old.startswith(f'{c}{38 + off}+'), (c, off, old)
        tm.f(f'{c}{37 + off}', f'{c}{38 + off}', tm.style(f'{c}{37 + off}'))
tm.t('B37', 'FX conversion fee for the period', tm.style('B37'))
tm.save()
cp = book.sheet('Control panel')
for rn in (28, 51, 74, 97):
    for c in 'BCDFGHO':
        clear(cp, f'{c}{rn}')
cp.save()
em = book.sheet('8 cards model (as is lineup)')
for ref in ('B196', 'C196', 'N196', 'O196', 'P196', 'Q196'):
    clear(em, ref)
em.t('B197', 'Finance 30.09.2026: interchange 0.5% domestic / 1.2% international on standard cards (ArCa, Visa Classic, Visa Digital); '
             '0.6% / 1.5% on Visa Gold and above (MC World, World Elite, Infinite, Metal). The Visa 2% cross-currency fee is already inside the '
             'FX revenue in row 81-83.', em.style('B197'))
em.save()
chg = book.sheet('v16 changes')
chg.t('B1', 'DEBIT CARDS MODEL v16.3 – CHANGES vs v15 (30.09.2026)', chg.style('B1'))
chg.t('B4', '2. FX: one line per tier on the Control panel (row 15 / 38 / 61 / 84): FX margin vs the CBA official rate, buy and sell sides, weighted '
            'by currency. Today Fast Bank = 0.79% (USD 0.48%, EUR 1.03%, RUB 1.85%), market 0.56–1.26%, median 1.04% (\'FX ranking\' tab, rate.am '
            '30.09.2026). FX revenue = today\'s revenue from the 8 cards model (unchanged) × parameter ÷ today\'s margin.', chg.style('B4'))
chg.t('B6', '4. Finance update: interchange 0.5% domestic / 1.2% international on standard cards, 0.6% / 1.5% on Visa Gold and above (8 cards model rows '
            '45 / 50, tier row 195). Perks: Premium (MC World) 10 EUR a year; Elite Visa Infinite / World Elite 20k AMD a year (unchanged). C2C 0.5% '
            'confirmed. The Visa 2% cross-currency fee is already in the FX revenue, so it is not added separately.', chg.style('B6'))
chg.save()
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
