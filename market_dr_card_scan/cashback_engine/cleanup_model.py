"""Model v14 clean-up at XML level (agreed with Alex 24.09.2026).

    python3 cleanup_model.py <in.xlsx> <out.xlsx>

* deletes unused tabs (+ the old 'Client profiles' pivot tab and full 'Cards dataset', rebuilt by build_profiles.py)
* Extract_client_DB: keeps the summary block A1:G25 (values + share formulas), drops the 148k raw rows (N:Y)
* freezes every pivot table to plain values and removes all pivot caches and the OLAP connection (FC-DSS)
* drops broken / unused defined names, the calculation chain; Excel recalculates fully on open
"""
import re
import sys

from lxml import etree

from xmlbook import CTN, N, PKG, RNS, S, X, Book

IN, OUT = sys.argv[1:3]
DELETE = ['card trxn', 'Balances', 'Balancy cardtype', 'Cards by transactions activity', 'Total Cards Cashout Voulume',
          'Fast Bank ATM cashout', 'credit card income', 'FOR slides', 'Sheet1',          # unused (Alex: delete)
          'Client profiles', 'Cards dataset']                                            # replaced by build_profiles.py
book = Book(IN)
P = book.parts
wb = X(P['xl/workbook.xml'])
wrels = X(P['xl/_rels/workbook.xml.rels'])
ct = X(P['[Content_Types].xml'])
rid_t = {r.get('Id'): r for r in wrels}
sheets = wb.find(N + 'sheets')
old_names = [s.get('name') for s in sheets]
assert all(d in old_names for d in DELETE), [d for d in DELETE if d not in old_names]


def resolve(base_dir, target):
    parts = (base_dir + '/' + target).split('/')
    out = []
    for p in parts:
        if p == '..':
            out.pop()
        elif p and p != '.':
            out.append(p)
    return '/'.join(out)


def rels_of(part):
    d, f = part.rsplit('/', 1)
    return f'{d}/_rels/{f}.rels'


def drop_part(part):
    """Remove a part, its own relationships part and its content-type override (recursively for owned parts)."""
    if part not in P:
        return
    rp = rels_of(part)
    if rp in P:
        for r in X(P[rp]):
            if r.get('TargetMode') == 'External':
                continue
            t = resolve(part.rsplit('/', 1)[0], r.get('Target'))
            if any(k in t for k in ('pivotTables/', 'comments', 'threadedComments/', 'drawings/', 'printerSettings/')):
                drop_part(t)
        del P[rp]
    del P[part]
    for o in list(ct):
        if o.get('PartName') == '/' + part:
            ct.remove(o)


removed = []
# ---------------------------------------------------------------- 1. delete tabs
for s in list(sheets):
    if s.get('name') in DELETE:
        rid = s.get('{%s}id' % RNS)
        part = 'xl/' + rid_t[rid].get('Target').lstrip('/').replace('xl/', '')
        drop_part(part)
        wrels.remove(rid_t[rid])
        sheets.remove(s)
        removed.append(s.get('name'))
new_names = [s.get('name') for s in sheets]
name2part = {s.get('name'): 'xl/' + rid_t[s.get('{%s}id' % RNS)].get('Target').lstrip('/').replace('xl/', '') for s in sheets}

# ---------------------------------------------------------------- 2. pivots -> plain values; caches, connection out
for name, part in name2part.items():
    rp = rels_of(part)
    if rp not in P:
        continue
    rr = X(P[rp])
    hit = False
    for r in list(rr):
        if 'pivotTable' in r.get('Type'):
            drop_part(resolve('xl/worksheets', r.get('Target')))
            rr.remove(r)
            hit = True
            print('pivot frozen on', name)
    if hit:
        if len(rr):
            P[rp] = S(rr)
        else:
            del P[rp]
for r in list(wrels):
    t = r.get('Type')
    if t.endswith('/pivotCacheDefinition') or t.endswith('/connections') or t.endswith('/calcChain'):
        drop_part('xl/' + r.get('Target').lstrip('/').replace('xl/', ''))
        wrels.remove(r)
pc = wb.find(N + 'pivotCaches')
if pc is not None:
    wb.remove(pc)
for n in [n for n in P if n.startswith('xl/pivotCache/') or n.startswith('xl/pivotTables/')]:
    drop_part(n) if n in P else None

# ---------------------------------------------------------------- 3. Extract_client_DB: keep the summary block only
part = name2part['Extract_client_DB']
root = X(P[part])
data = root.find(N + 'sheetData')
kept_rows = 0
for row in list(data):
    rn = int(row.get('r'))
    if rn > 25:
        data.remove(row)
        continue
    for c in list(row):
        col = re.match(r'[A-Z]+', c.get('r')).group(0)
        if len(col) > 1 or col >= 'N':
            row.remove(c)
    row.attrib.pop('spans', None)
    kept_rows += 1
root.find(N + 'dimension').set('ref', 'A1:G25')
for sv in root.iter(N + 'sheetView'):
    sv.set('topLeftCell', 'A1')
P[part] = S(root)
print('Extract_client_DB rows kept', kept_rows)

# ---------------------------------------------------------------- 4. defined names
used = set()
ident = re.compile(r"(?<![\w.$\\])([A-Za-z_\\][\w.\\]*)(?![\w.\\])(?!\s*[(!])(?!\$?\d)")
for name, part in name2part.items():
    txt = P[part].decode('utf-8', 'ignore')
    for m in re.finditer(r'<f[^>]*>([^<]*)</f>|<formula1?>([^<]*)</formula1?>|<xm:f>([^<]*)</xm:f>', txt):
        f = m.group(1) or m.group(2) or m.group(3) or ''
        f = re.sub(r"'(?:[^']|'')*'!", '', f.replace('&quot;', '"'))          # quoted sheet names
        f = re.sub(r'"[^"]*"', '""', f)                                        # string literals
        for tok in ident.findall(f):
            used.add(tok.lower())
dn = wb.find(N + 'definedNames')
kept, dropped = [], 0
old_idx = {n: i for i, n in enumerate(old_names)}
new_idx = {n: i for i, n in enumerate(new_names)}
for d in list(dn):
    nm, ref, lid = d.get('name'), d.text or '', d.get('localSheetId')
    sheet_name = old_names[int(lid)] if lid is not None else None
    ok = '#REF!' not in ref and '#NAME?' not in ref and (sheet_name is None or sheet_name in new_idx)
    builtin = nm.startswith('_xlnm.')
    if ok and (builtin or nm.lower() in used):
        if lid is not None:
            d.set('localSheetId', str(new_idx[sheet_name]))
        kept.append(nm)
    else:
        dn.remove(d)
        dropped += 1
if not len(dn):
    wb.remove(dn)
print('defined names kept', kept, 'dropped', dropped)

# ---------------------------------------------------------------- 5. workbook settings, views, metadata
calc = wb.find(N + 'calcPr')
calc.set('fullCalcOnLoad', '1')
cp = new_names.index('Control panel')
for v in wb.find(N + 'bookViews'):
    v.set('activeTab', str(cp))
    v.attrib.pop('firstSheet', None)
for name, part in name2part.items():
    if part not in P:
        continue
    r = X(P[part])
    changed = False
    for sv in r.iter(N + 'sheetView'):
        if name == 'Control panel':
            sv.set('tabSelected', '1'); changed = True
        elif sv.get('tabSelected'):
            sv.attrib.pop('tabSelected'); changed = True
    if changed:
        P[part] = S(r)
P['xl/workbook.xml'] = S(wb)
P['xl/_rels/workbook.xml.rels'] = S(wrels)
P['[Content_Types].xml'] = S(ct)
app = P['docProps/app.xml'].decode('utf-8')
esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')           # noqa: E731
app = re.sub(r'<HeadingPairs>.*</TitlesOfParts>',
             '<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>'
             f'<vt:variant><vt:i4>{len(new_names)}</vt:i4></vt:variant></vt:vector></HeadingPairs>'
             f'<TitlesOfParts><vt:vector size="{len(new_names)}" baseType="lpstr">'
             + ''.join(f'<vt:lpstr>{esc(n)}</vt:lpstr>' for n in new_names) + '</vt:vector></TitlesOfParts>', app, flags=re.S)
P['docProps/app.xml'] = app.encode('utf-8')
book.write(OUT)
print('removed tabs', removed)
print('tabs now', len(new_names))
