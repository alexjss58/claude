"""Debit cards model v7 -> v8: rebuild the Control panel in Alex's new row order (from his Fast Free
draft on 'Control panel (2)') for all four tiers, re-point 'Model sept 26' to it, and drop the old sheet.

    python3 build_cp_v8.py <in.xlsx> <out.xlsx>

* 'Control panel (2)' keeps Alex's Free table as is (rows 6-26) and becomes 'Control panel'.
* Black / Premium / Elite are cloned from the Free table at +23 / +46 / +69 rows: labels, styles,
  row grouping (hidden / outline rows) and the Free formulas (ArCa ATM fee = half, EUR / RUB spread
  scaled from USD vs market mid, cap = market mid). Tier values (reference, parameters, benchmarks,
  notes) are carried over from the tier's old table by parameter.
* Outputs (J:N) follow the Free order with the model's block offset (+77 rows per tier).
* Every 'Control panel'!C/D reference in 'Model sept 26' is moved to the parameter's new row.
XML-only edit (the package carries pivots, comments, a connection and spill metadata).
"""
import copy
import re
import sys
import zipfile

from lxml import etree
from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.formula.translate import Translator
from openpyxl.utils import column_index_from_string

SRC, OUT = sys.argv[1:3]
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR = '{http://schemas.openxmlformats.org/package/2006/relationships}'
CTN = '{http://schemas.openxmlformats.org/package/2006/content-types}'

zin = zipfile.ZipFile(SRC)
parts = {n: zin.read(n) for n in zin.namelist()}


def colnum(ref):
    return column_index_from_string(re.match(r'\$?([A-Z]+)', ref).group(1))


def rownum(ref):
    return int(re.search(r'(\d+)$', ref).group(1))


class Sheet:
    def __init__(self, part):
        self.part = part
        self.root = etree.fromstring(parts[part])
        self.data = self.root.find(N + 'sheetData')
        self.rows = {int(r.get('r')): r for r in self.data}
        master = {}
        for c in self.data.iter(N + 'c'):
            f = c.find(N + 'f')
            if f is None or f.get('t') != 'shared':
                continue
            si = f.get('si')
            if f.text:
                master[si] = (c.get('r'), f.text); txt = f.text
            else:
                o, t0 = master[si]
                txt = Translator('=' + t0, origin=o).translate_formula(c.get('r'))[1:]
            for a in ('t', 'si', 'ref'):
                f.attrib.pop(a, None)
            f.text = txt

    def row(self, r):
        if r not in self.rows:
            el = etree.Element(N + 'row'); el.set('r', str(r))
            self.data.append(el); self.rows[r] = el
        return self.rows[r]

    def get(self, ref):
        r = self.rows.get(rownum(ref))
        if r is None:
            return None
        for c in r:
            if c.get('r') == ref:
                return c
        return None

    def put(self, ref, cell_el):
        old = self.get(ref)
        if old is not None:
            old.getparent().remove(old)
        cell_el.set('r', ref)
        self.row(rownum(ref)).append(cell_el)

    def save(self):
        ordered = sorted(self.data, key=lambda e: int(e.get('r')))
        for e in ordered:
            self.data.remove(e)
        for e in ordered:
            e.attrib.pop('spans', None)
            cells = sorted(e, key=lambda c: colnum(c.get('r')))
            for c in cells:
                e.remove(c)
            for c in cells:
                e.append(c)
            self.data.append(e)
        parts[self.part] = etree.tostring(self.root, xml_declaration=True, encoding='UTF-8', standalone=True)


def rewrite(formula, fn):
    out = []
    for t in Tokenizer('=' + formula).items:
        v = t.value
        if t.type == 'OPERAND' and t.subtype == 'RANGE':
            sheet, rng = (v.rsplit('!', 1) if '!' in v else (None, v))
            sname = sheet.strip("'") if sheet else None
            rng = re.sub(r'(\$?)([A-Z]{1,3})(\$?)(\d+)',
                         lambda m: '%s%s%s%d' % (m.group(1), m.group(2), m.group(3), fn(sname, int(m.group(4)))), rng)
            v = sheet + '!' + rng if sheet else rng
        out.append(v)
    return ''.join(out)


# ------------------------------------------------------------------ locate sheets
wb = etree.fromstring(parts['xl/workbook.xml'])
rels = etree.fromstring(parts['xl/_rels/workbook.xml.rels'])
rid2t = {r.get('Id'): r.get('Target') for r in rels}
sheets = wb.find(N + 'sheets')
byname = {s.get('name'): s for s in sheets}
OLD, NEW, MODEL = byname['Control panel'], byname['Control panel (2)'], byname['Model sept 26']
part = lambda s: 'xl/' + rid2t[s.get('{%s}id' % RNS)]           # noqa: E731
cp = Sheet(part(NEW))
model = Sheet(part(MODEL))

KEYS_OLD = ['fee', 'own', 'owna', 'oth', 'otha', 'c2c', 'amd', 'nonamd', 'virt', 'metal',
            'usd', 'eur', 'rub', 'cb', 'cap', 'up', 'paid']              # old table order (rows h+1..h+17)
REL = dict(amd=1, nonamd=2, own=3, owna=4, oth=5, otha=6, c2c=7, fee=8, usd=9, eur=10, rub=11,
           cb=13, cap=14, up=15, virt=18, metal=19, paid=20)               # new order (Alex's Free table)
NOTE_REL = dict(REL, cb=14, cap=None, virt=17, eur=None, rub=None)                   # where Free keeps each note
OLD_H = [6, 26, 46, 66]                                                    # headers on the old 'Control panel'
DRAFT_H = [None, 29, 49, 69]                                               # old-layout tables on the draft
NEW_H = [6, 29, 52, 75]
MODEL_OFF = 77
TITLE = ['FAST FREE CARD TERMS', 'FAST BLACK CARD TERMS', 'FAST PREMIUM CARD TERMS', 'FAST ELITE CARD TERMS']

# ------------------------------------------------------------------ 1. collect tier values from the draft's old tables
vals = {}                                   # (tier, key, col) -> cell element
for k in (1, 2, 3):
    h = DRAFT_H[k]
    for i, key in enumerate(KEYS_OLD):
        for col in 'CDFGHO':
            c = cp.get(f'{col}{h + 1 + i}')
            if c is not None and len(c):
                vals[(k, key, col)] = copy.deepcopy(c)
free_rows = {r: copy.deepcopy(cp.rows[r]) for r in range(6, 27) if r in cp.rows}

# clear everything below the Free table
for r in [r for r in cp.rows if r >= 28]:
    cp.data.remove(cp.rows.pop(r))

# ------------------------------------------------------------------ 2. build Black / Premium / Elite from the Free table
inv = {v: k for k, v in REL.items()}
note_inv = {v: k for k, v in NOTE_REL.items() if v}
report = []
for k in (1, 2, 3):
    off = NEW_H[k] - 6
    for r, src in free_rows.items():
        rel = r - 6
        dst = cp.row(r + off)
        for a, v in src.attrib.items():
            if a not in ('r', 'spans'):
                dst.set(a, v)
        key = inv.get(rel)
        for c in src:
            col = re.match(r'[A-Z]+', c.get('r')).group(0)
            new = copy.deepcopy(c)
            f = new.find(N + 'f')
            if col in 'JKLMN' and f is not None:          # outputs: shift model rows 9..22 by the block offset
                f.text = rewrite(f.text, lambda sn, row: row + MODEL_OFF * k if sn == 'Model sept 26' and 9 <= row <= 22 else row)
                for v in new.findall(N + 'v'):
                    new.remove(v)
            elif rel == 0 and col == 'B':
                new = etree.Element(N + 'c', s=c.get('s')); new.set('t', 'inlineStr')
                etree.SubElement(etree.SubElement(new, N + 'is'), N + 't').text = TITLE[k]
            elif col in 'CDFGH' and key:
                src_val = vals.get((k, key, col))
                if col == 'D' and f is not None:           # Free formula -> same formula, rows shifted
                    g = vals.get((k, key, 'G'))
                    g_txt = g is not None and g.get('t') in ('s', 'inlineStr')
                    if key == 'cap' and g_txt:              # cap: market mid is text ("Not published") -> keep typed value
                        new = copy.deepcopy(src_val); new.set('s', c.get('s'))
                        report.append(f'{TITLE[k]}: cap kept as typed value (market mid is text)')
                    else:
                        f.text = rewrite(f.text, lambda sn, row: row + off if sn is None else row)
                        for v in new.findall(N + 'v'):
                            new.remove(v)
                elif src_val is not None:
                    new = copy.deepcopy(src_val); new.set('s', c.get('s'))
                else:
                    new = etree.Element(N + 'c', s=c.get('s')) if c.get('s') else etree.Element(N + 'c')
            elif col == 'O':
                nk = note_inv.get(rel)
                src_val = vals.get((k, nk, 'O')) if nk else None
                new = copy.deepcopy(src_val) if src_val is not None else copy.deepcopy(c)
                if c.get('s'):
                    new.set('s', c.get('s'))
            cp.put(f'{col}{r + off}', new)
        # tier values that sit in a column where the Free row has no cell (e.g. benchmarks the Free table leaves blank)
        if key:
            for col in 'CDFGH':
                if cp.get(f'{col}{r + off}') is None and (k, key, col) in vals:
                    cp.put(f'{col}{r + off}', copy.deepcopy(vals[(k, key, col)]))
    # any note Free doesn't carry (only EUR / RUB) is dropped, as in Free
dim = cp.root.find(N + 'dimension')
dim.set('ref', f'B2:O{NEW_H[3] + 20}')
cp.save()

# ------------------------------------------------------------------ 3. re-point 'Model sept 26'
rowmap = {}
for k in range(4):
    for i, key in enumerate(KEYS_OLD):
        rowmap[OLD_H[k] + 1 + i] = NEW_H[k] + REL[key]
n_ref = 0


def remap(sn, row):
    global n_ref
    if sn == 'Control panel':
        n_ref += 1
        if row not in rowmap:
            raise SystemExit(f'unmapped Control panel row {row}')
        return rowmap[row]
    return row


for c in model.data.iter(N + 'c'):
    f = c.find(N + 'f')
    if f is not None and f.text and 'Control panel' in f.text:
        f.text = rewrite(f.text, remap)
        for v in c.findall(N + 'v'):
            c.remove(v)
model.save()

# ------------------------------------------------------------------ 4. drop the old sheet, rename the draft
old_part = part(OLD)
old_idx = list(sheets).index(OLD)
old_rid = OLD.get('{%s}id' % RNS)
sheets.remove(OLD)
NEW.set('name', 'Control panel')
dn = wb.find(N + 'definedNames')
if dn is not None:
    for d in list(dn):
        lid = d.get('localSheetId')
        if lid is None:
            continue
        if int(lid) == old_idx:
            dn.remove(d)
        elif int(lid) > old_idx:
            d.set('localSheetId', str(int(lid) - 1))
for v in wb.find(N + 'bookViews'):
    for a in ('activeTab', 'firstSheet'):
        if v.get(a) and int(v.get(a)) > old_idx:
            v.set(a, str(int(v.get(a)) - 1))
wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
parts['xl/workbook.xml'] = etree.tostring(wb, xml_declaration=True, encoding='UTF-8', standalone=True)
for r in list(rels):
    if r.get('Id') == old_rid or 'calcChain' in r.get('Target'):
        rels.remove(r)
parts['xl/_rels/workbook.xml.rels'] = etree.tostring(rels, xml_declaration=True, encoding='UTF-8', standalone=True)

# the old sheet's own parts (comments / threaded comments / vml) go with it
drop = {old_part, 'xl/calcChain.xml'}
old_rels = old_part.replace('worksheets/', 'worksheets/_rels/') + '.rels'
if old_rels in parts:
    for r in etree.fromstring(parts[old_rels]):
        drop.add('xl/' + r.get('Target').replace('../', ''))
    drop.add(old_rels)
still_used = set()
for n, b in parts.items():
    if n.endswith('.rels') and n not in drop:
        for r in etree.fromstring(b):
            still_used.add(r.get('Target').split('/')[-1])
drop = {d for d in drop if d == old_part or d == old_rels or d == 'xl/calcChain.xml' or d.split('/')[-1] not in still_used}
for d in drop:
    parts.pop(d, None)
ct = etree.fromstring(parts['[Content_Types].xml'])
for o in list(ct):
    if o.get('PartName') and o.get('PartName').lstrip('/') in drop:
        ct.remove(o)
parts['[Content_Types].xml'] = etree.tostring(ct, xml_declaration=True, encoding='UTF-8', standalone=True)

app = parts['docProps/app.xml'].decode('utf-8')
app = app.replace('<vt:lpstr>Control panel</vt:lpstr>', '', 1).replace('<vt:lpstr>Control panel (2)</vt:lpstr>', '<vt:lpstr>Control panel</vt:lpstr>', 1)
app = re.sub(r'(<vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) - 1), app)
app = re.sub(r'<TitlesOfParts><vt:vector size="(\d+)"', lambda m: f'<TitlesOfParts><vt:vector size="{int(m.group(1)) - 1}"', app)
parts['docProps/app.xml'] = app.encode('utf-8')

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in [n for n in zin.namelist() if n in parts]:
        z.writestr(n, parts[n])

print('model references re-pointed:', n_ref)
print('dropped parts:', sorted(drop))
print('\n'.join(report))
