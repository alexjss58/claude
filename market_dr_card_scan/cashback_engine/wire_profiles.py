"""Wire the client-profile mode into the tier model (model v14).

    python3 wire_profiles.py <in.xlsx> <out.xlsx> <profiles_layout.json>

* 'Control panel' D3: mode selector (1. All client base / 2. Active users / 3. High engagement users), one for all tiers;
  rows 27 / 50 / 73 / 96: the multipliers in use for the tier (text line, from 'Client profiles').
* '4 tiers model (to be lineup)': the Q4-26 per-card starting values taken from '8 cards model' rows 171-177 are multiplied
  by the tier's multiplier in use; FX revenue is scaled in every period (the market-based years use row 190).
"""
import html
import json
import re
import sys

from lxml import etree

from xmlbook import N, S, X, Book

IN, OUT, LAYOUT = sys.argv[1:4]
lay = json.load(open(LAYOUT))
DRV = lay['drivers']
TCOL = lay['tier_cols']
TIERS = ['Free', 'Black', 'Premium', 'Elite']
SRC = {'Free': 'N', 'Black': 'O', 'Premium': 'P', 'Elite': 'Q'}          # tier columns in '8 cards model' rows 146-191
MODES = ['1. All client base', '2. Active users', '3. High engagement users']
EC = "'8 cards model (as is lineup)'"
CPN = "'Client profiles'"
book = Book(IN)

# ---------------------------------------------------------------- 4 tiers model
tm = book.sheet('4 tiers model (to be lineup)')
n_edit = 0
for k, t in enumerate(TIERS):
    o, s, pc = 77 * k, SRC[t], TCOL[t]
    use = lambda key: f"{CPN}!${pc}${DRV[key]}"                          # noqa: E731
    for row, src_row, key in [(21, 171, 'noncash'), (22, 172, 'txn'), (30, 173, 'cashout'), (35, 174, 'c2c'),
                              (48, 175, 'balance'), (39, 176, 'fx'), (53, 177, 'deposit')]:
        ref = f'D{row + o}'
        old = tm.formula(ref)
        assert old == f'{EC}!${s}${src_row}', (ref, old)
        tm.f(ref, f'{old}*{use(key)}', tm.style(ref))
        n_edit += 1
    for c in 'FGHJK':                                                     # FX revenue: market-based periods
        ref = f'{c}{39 + o}'
        old = tm.formula(ref)
        needle = f'{EC}!${s}$190'
        assert old.count(needle) == 1, (ref, old)
        tm.f(ref, old.replace(needle, f'{needle}*{use("fx")}'), tm.style(ref))
        n_edit += 1
tm.save()

# ---------------------------------------------------------------- Control panel
cp = book.sheet('Control panel')
assert cp.get('D3') is None and cp.get('B3') is None, 'Control panel row 3 is not empty'
cp.t('B3', 'CLIENT PROFILE (all tiers)', 388)
cp.t('D3', MODES[0], 978)
cp.t('J3', "Mode 1 = today's per-card figures. 2 and 3 scale per-card activity by tier: see 'Client profiles'.", 949)
for k, t in enumerate(TIERS):
    r = 27 + 23 * k
    assert cp.get(f'B{r}') is None and cp.get(f'C{r}') is None, f'Control panel row {r} is not empty'
    pc = TCOL[t]
    v = lambda key: f"TEXT({CPN}!${pc}${DRV[key]},\"0.00\")"             # noqa: E731
    cp.t(f'B{r}', 'Client profile multipliers in use', 515)
    cp.f(f'C{r}', f'="Non-cash, cashout, C2C ×"&{v("noncash")}&"   transactions ×"&{v("txn")}&"   card balance ×"&{v("balance")}'
                  f'&"   deposits ×"&{v("deposit")}&"   FX ×"&{v("fx")}', 949)
dvs = cp.root.find(N + 'dataValidations')
dv = etree.SubElement(dvs, N + 'dataValidation', type='list', allowBlank='0', showErrorMessage='1', sqref='D3')
etree.SubElement(dv, N + 'formula1').text = '"' + ','.join(MODES) + '"'
dvs.set('count', str(len(dvs)))
cp.save()

# ---------------------------------------------------------------- app.xml: sheet list as it is now
names = [n for n, _ in book.sheet_map()]
app = book.parts['docProps/app.xml'].decode('utf-8')
app = re.sub(r'<HeadingPairs>.*</TitlesOfParts>',
             '<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>'
             f'<vt:variant><vt:i4>{len(names)}</vt:i4></vt:variant></vt:vector></HeadingPairs>'
             f'<TitlesOfParts><vt:vector size="{len(names)}" baseType="lpstr">'
             + ''.join(f'<vt:lpstr>{html.escape(n, quote=False)}</vt:lpstr>' for n in names) + '</vt:vector></TitlesOfParts>',
             app, flags=re.S)
book.parts['docProps/app.xml'] = app.encode('utf-8')
book.write(OUT)
print('4 tiers model cells rewired', n_edit, '| tabs', len(names))
