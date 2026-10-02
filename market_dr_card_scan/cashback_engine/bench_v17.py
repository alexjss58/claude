"""Refresh Control panel market benchmarks (columns F-H + basis notes) for a v17 option from the tier dashboard statistics.
    python3 bench_v17.py <in.xlsx> <out.xlsx> A|B
A = dashboard v13 tiers (ArCa -> Free, Gold -> Black); B = dashboard v12 tiers (ArCa in Black, Gold in Premium). Every card counted, Fast Bank excluded.
"""
import json, sys
from xmlbook import N, S, X, Book
IN, OUT, OPT = sys.argv[1:4]
ST = {'A': json.loads('{"free":{"fee":[0,1000,5000,23],"int":[0,0,4,21],"c2cout":[0.5,0.5,1.5,16],"atmown":[0,0.2,2,22],"atmoth":[0,1,3,21],"cb":[0,0,1.17,23],"uplift":[0,0,0,23],"cap":[5000,5000,5000,1]},"plus":{"fee":[0,5000,24000,37],"int":[0,0,4,36],"c2cout":[0.5,0.5,0.75,27],"atmown":[0,0,1,36],"atmoth":[0,1,1.5,36],"cb":[0,0,0.2675,37],"uplift":[0,0,0.25,37],"cap":[5000,5000,5000,1]},"premium":{"fee":[1000,20000,36000,12],"int":[0,0,0,12],"c2cout":[0.5,0.5,0.75,10],"atmown":[0,0.25,2,12],"atmoth":[0.75,1,2.5,12],"cb":[0,0,1.12,12],"uplift":[0,0,0.25,12],"cap":[8000,14000,20000,2]},"elite":{"fee":[40000,96000,150000,16],"int":[0,0,3,16],"c2cout":[0.5,0.75,4,9],"atmown":[0,0.25,4,16],"atmoth":[0,1,1.5,14],"cb":[0,0,1,16],"uplift":[0,0,0.25,16],"cap":null}}'),
      'B': json.loads('{"free":{"fee":[0,0,2000,13],"int":[0,0,4,12],"c2cout":[0.5,0.5,1.5,9],"atmown":[0,0.3,2,12],"atmoth":[1,1,3,11],"cb":[0,0,1.17,13],"uplift":[0,0,0,13],"cap":[5000,5000,5000,1]},"plus":{"fee":[1000,4500,8400,30],"int":[0,0,4,28],"c2cout":[0.5,0.5,0.75,21],"atmown":[0,0,1,29],"atmoth":[0,1,1.5,29],"cb":[0,0,0.2675,30],"uplift":[0,0,0,30],"cap":[5000,5000,5000,1]},"premium":{"fee":[0,15000,36000,29],"int":[0,0,4,29],"c2cout":[0.5,0.5,0.75,23],"atmown":[0,0.25,2,29],"atmoth":[0,1,2.5,29],"cb":[0,0,1.12,29],"uplift":[0,0,0.25,29],"cap":[8000,14000,20000,2]},"elite":{"fee":[40000,96000,150000,16],"int":[0,0,3,16],"c2cout":[0.5,0.75,4,9],"atmown":[0,0.25,4,16],"atmoth":[0,1,1.5,14],"cb":[0,0,1,16],"uplift":[0,0,0.25,16],"cap":null}}')}[OPT]
SCOPE = {'A': {'free': 'digital, virtual and no-fee cards plus all ArCa cards', 'plus': 'Classic / Standard / Gold cards',
               'premium': 'Platinum / World cards', 'elite': 'Signature / Infinite / World Elite / Black Edition / Metal'},
         'B': {'free': 'digital, virtual and no-fee cards', 'plus': 'Classic / Standard / ArCa plastic',
               'premium': 'Gold / Platinum / World cards', 'elite': 'Signature / Infinite / World Elite / Black Edition / Metal'}}[OPT]
SRC = {'A': 'tier dashboard v13', 'B': 'tier dashboard v12 (previous split)'}[OPT]
book = Book(IN)
cp = book.sheet('Control panel')


def val(ref, v, s=None):
    c = cp.cell(ref)
    cp._reset(c, s if s is not None else c.get('s'))
    from lxml import etree
    etree.SubElement(c, N + 'v').text = str(int(v)) if float(v).is_integer() else repr(float(v))


def clear(ref):
    c = cp.get(ref)
    if c is not None:
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)


def note(ref, txt):
    cp.t(ref, txt, cp.style(ref) or 827)


for tier, b in (('free', 0), ('plus', 23), ('premium', 46), ('elite', 69)):
    d = ST[tier]
    for row, key, scale in ((7, 'int', 100), (9, 'atmown', 100), (11, 'atmoth', 100), (13, 'c2cout', 100), (14, 'fee', 1),
                            (19, 'cb', 100), (21, 'uplift', 100)):
        lo, md, hi, n = d[key]
        for c, v in zip('FGH', (lo, md, hi)):
            val(f'{c}{row + b}', v / scale)
    lo, md, hi, n = d['int']; note(f'O{7 + b}', f"Rate earned on the tier's typical AMD balance (thresholds applied) (n={n})")
    for row, key in ((9, 'atmown'), (11, 'atmoth')):
        note(f'O{row + b}', f"Effective % on the tier's monthly cash (free allowances applied) (n={d[key][3]})")
    note(f'O{13 + b}', f"Card-to-card to other banks, published % (n={d['c2cout'][3]})")
    note(f'O{14 + b}', f"Annual fee, other banks' cards in the tier (n={d['fee'][3]})")
    note(f'O{19 + b}', f"Bank-funded cashback (cash + points), effective on the tier's typical spend basket (n={d['cb'][3]})")
    if d['cap']:
        for c in 'FH':
            clear(f'{c}{20 + b}')
        val(f'G{20 + b}', d['cap'][1])
        note(f'O{20 + b}', f"Monthly cashback cap, cards that publish one (n={d['cap'][3]}; range {d['cap'][0]:,}–{d['cap'][2]:,} AMD)")
    else:
        cp.t(f'G{20 + b}', 'Not published', cp.style(f'G{20 + b}'))
        note(f'O{20 + b}', 'No card in the tier publishes a monthly cap')
    note(f'O{21 + b}', f"Deposit-rate boost via the card: Ameriabank Premium / Partner packages +0.25 / +0.35 p.p. (need 40m / 120m AMD balances); "
                       f"IDBank VISAGOLD +0.5 p.p. on savings only, not counted (n={d['uplift'][3]})")
    for c in 'FGH':
        clear(f'{c}{26 + b}')
    note(f'O{6 + b}', f"Market benchmark: {SRC}, 30.09.2026 – {SCOPE[tier]}; every card counted, Fast Bank excluded; FX row: 'FX ranking' tab")
cp.save()
P = book.parts
wb = X(P['xl/workbook.xml'])
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
P['xl/workbook.xml'] = S(wb)
book.write(OUT)
print('written', OUT)
