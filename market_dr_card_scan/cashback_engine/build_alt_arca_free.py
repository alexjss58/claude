"""Alternative model: ArCa Classic in Fast Free instead of Fast Black (Alex, 25.09.2026).

    python3 build_alt_arca_free.py <v14.xlsx> <out.xlsx>

Every card-type -> tier mapping in the model moves ArCa to Free:
* '8 cards model (as is lineup)' D148 (drives the tier aggregation rows 152-191, hence both tier models and the P&L tier mix);
  N190/O190 (segment FX share) become mapping-based instead of hard-coded card columns;
* 'CB Inputs' C12 (cashback engine: ArCa clients move to Free, 0% cashback), CB Client view persona Anna (ArCa) -> Free;
* 'Cards dataset' tier column (client profiles and their multipliers);
* Control panel as-is references that depend on the mix: Free virtual share C24 and paid share C26, Black paid share C49.
The to-be parameters (Control panel column D) are left as they are.
"""
import sys

from lxml import etree

from xmlbook import CTN, N, S, X, Book

IN, OUT = sys.argv[1:3]
EC = "'8 cards model (as is lineup)'"
book = Book(IN)
P = book.parts
ss = [''.join(t.text or '' for t in si.iter(N + 't')) for si in X(P['xl/sharedStrings.xml'])]


def text(c):
    if c is None:
        return None
    t, v = c.get('t'), c.find(N + 'v')
    if t == 's':
        return ss[int(v.text)]
    if t == 'inlineStr':
        return ''.join(x.text or '' for x in c.iter(N + 't'))
    return None if v is None else v.text


def expect(sh, ref, val):
    got = text(sh.get(ref)) if val is not None and not val.startswith('=') else sh.formula(ref)
    assert got == (val.lstrip('=') if val and val.startswith('=') else val), (ref, got, val)


# ---------------------------------------------------------------- '8 cards model': tier mapping
em = book.sheet('8 cards model (as is lineup)')
expect(em, 'D147', '=D$6')
expect(em, 'D148', 'Black')
em.t('D148', 'Free', em.style('D148'))
seg = '(SUMIF($D$148:$K$148,"Free",$D$94:$K$94)+SUMIF($D$148:$K$148,"Black",$D$94:$K$94))'
for c in 'NO':
    em.f(f'{c}190', f'SUMIF($D$148:$K$148,{c}$148,$D$94:$K$94)/{seg}', em.style(f'{c}190'))
em.save()

# ---------------------------------------------------------------- '4 tiers model': block titles
tm = book.sheet('4 tiers model (to be lineup)')
expect(tm, 'F7', 'Fast Free (Visa Digital)')
expect(tm, 'F84', 'Fast Black (ArCa Classic, Visa Classic)')
tm.t('F7', 'Fast Free (Visa Digital, ArCa Classic)', tm.style('F7'))
tm.t('F84', 'Fast Black (Visa Classic)', tm.style('F84'))
tm.save()

# ---------------------------------------------------------------- Control panel: title + as-is references that depend on the mix
cp = book.sheet('Control panel')
cp.t('B2', 'DEBIT CARD ECONOMICS - CONTROL PANEL (alternative: ArCa Classic in Fast Free)', cp.style('B2'))
expect(cp, 'C49', f"={EC}!N39")
cp.f('C24', f'{EC}!K8/({EC}!D8+{EC}!K8)', cp.style('C24'))                            # Visa Digital is the virtual card
cp.f('C26', f'({EC}!D8*{EC}!D39+{EC}!K8*{EC}!K39)/({EC}!D8+{EC}!K8)', cp.style('C26'))
cp.f('C49', f'{EC}!G39', cp.style('C49'))                                               # Black = Visa Classic only
cp.save()

# ---------------------------------------------------------------- cashback engine
ci = book.sheet('CB Inputs')
expect(ci, 'B12', 'Arca')
expect(ci, 'C12', 'Black')
ci.t('C12', 'Free', ci.style('C12'))
ci.save()
cv = book.sheet('CB Client view')
assert text(cv.get('T2')).startswith('ArCa Classic') and text(cv.get('T3')) == 'Black', (text(cv.get('T2')), text(cv.get('T3')))   # Anna's persona
cv.t('T3', 'Free', cv.style('T3'))
cv.save()

# ---------------------------------------------------------------- Cards dataset: tier column
cd = book.sheet('Cards dataset')
assert text(cd.get('A1')) == 'Card type' and text(cd.get('B1')) == 'Tier'
moved = 0
for rn, row in cd.rows.items():
    if rn < 2:
        continue
    a = next((c for c in row if c.get('r') == f'A{rn}'), None)
    if text(a) == 'Arca':
        b = next(c for c in row if c.get('r') == f'B{rn}')
        assert text(b) == 'Black'
        cd.t(f'B{rn}', 'Free', b.get('s'))
        moved += 1
cd.save()

# ---------------------------------------------------------------- recalc on open, drop the stale calc chain
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
rels = X(P['xl/_rels/workbook.xml.rels'])
for r in list(rels):
    if r.get('Type').endswith('/calcChain'):
        rels.remove(r)
P['xl/_rels/workbook.xml.rels'] = S(rels)
P.pop('xl/calcChain.xml', None)
ct = X(P['[Content_Types].xml'])
for o in list(ct):
    if o.get('PartName') == '/xl/calcChain.xml':
        ct.remove(o)
P['[Content_Types].xml'] = S(ct)
book.write(OUT)
print('ArCa cards moved to Free in Cards dataset:', moved)
