"""v17 (30.09.2026): two tier splits from v16.3.
    python3 build_v17.py <v16.3_raw.xlsx> <out.xlsx> A|B
A = current split (Black = Visa Classic + Visa Gold, Premium = MC World).
B = previous split (Black = Visa Classic, Premium = MC World + Visa Gold).
Both: Premium perks = 10 EUR a year on Mastercard World cards only (weighted by their share of the tier's activated cards).
"""
import sys
from lxml import etree
from xmlbook import N, S, X, Book
IN, OUT, OPT = sys.argv[1:4]
book = Book(IN)
P = book.parts
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


tm = book.sheet('4 tiers model (to be lineup)')
for c in 'OPQ':
    tm.f(f'{c}175', "10*'FX ranking'!$F$23*'8 cards model (as is lineup)'!$E$8/'8 cards model (as is lineup)'!$P$152", tm.style(f'{c}175'))
split = {'A': ('Black = Visa Classic + Visa Gold; Premium = Mastercard World', 'Fast Black (Visa Classic, Visa Gold)', 'Fast Premium (Mastercard World)'),
         'B': ('Black = Visa Classic; Premium = Mastercard World + Visa Gold', 'Fast Black (Visa Classic)', 'Fast Premium (Mastercard World, Visa Gold)')}[OPT]
tm.t('F84', split[1], tm.style('F84'))
tm.t('F161', split[2], tm.style('F161'))
tm.save()

if OPT == 'B':
    em = book.sheet('8 cards model (as is lineup)')
    assert text(em.get('H6')) == 'VisaGold' and text(em.get('H148')) == 'Black'
    em.t('H148', 'Premium', em.style('H148'))
    em.save()
    ci = book.sheet('CB Inputs')
    assert text(ci.get('B14')) == 'Visa Gold'
    ci.t('C14', 'Premium', ci.style('C14'))
    ci.save()
    cv = book.sheet('CB Client view')
    cv.t('V3', 'Premium', cv.style('V3'))
    cv.save()
    cd = book.sheet('Cards dataset')
    if 'Premium' in sst:
        pi = sst.index('Premium')
    else:
        si = etree.SubElement(sst_root, N + 'si'); etree.SubElement(si, N + 't').text = 'Premium'
        sst.append('Premium'); pi = len(sst) - 1
        sst_root.set('uniqueCount', str(len(sst)))
        P['xl/sharedStrings.xml'] = S(sst_root)
    moved = 0
    for rn, row in cd.rows.items():
        if rn < 2:
            continue
        cells = {c.get('r'): c for c in row}
        if text(cells.get(f'A{rn}')) == 'Visa Gold':
            b = cells[f'B{rn}']
            assert text(b) == 'Black'
            for ch in list(b):
                b.remove(ch)
            b.set('t', 's')
            etree.SubElement(b, N + 'v').text = str(pi)
            moved += 1
    cd.save()
    print('Visa Gold rows back to Premium:', moved)

chg = book.sheet('v16 changes')
chg.t('B1', f'DEBIT CARDS MODEL v17 option {OPT} – {split[0]} – CHANGES vs v15 (30.09.2026)', chg.style('B1'))
chg.t('B3', ('1. Tiers (option A): Free = Visa Digital + ArCa Classic; Black = Visa Classic + Visa Gold; Premium = Mastercard World; Elite = MC World Elite + '
             'Visa Infinite + Infinite Metal.' if OPT == 'A' else
             '1. Tiers (option B, the v15 split for Visa Gold): Free = Visa Digital + ArCa Classic; Black = Visa Classic; Premium = Mastercard World + '
             'Visa Gold; Elite = MC World Elite + Visa Infinite + Infinite Metal.') +
      ' The mapping sits in 8 cards model row 148, CB Inputs C14 and the Cards dataset tier column; everything else (paid shares, fees, '
      'client profiles, cashback divisors from the engine) follows it. Premium perks = 10 EUR a year on Mastercard World cards only.', chg.style('B3'))
chg.save()
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
