"""Transplant the cashback engine sheets into the tier model and wire the model's cashback line to it.

    python3 merge_into_model.py <model.xlsx> <sheets.xlsx> <out.xlsx> [--after "Sheet name"] [--no-wire]

--after: insert the sheets after this sheet (default 'PnL all tiers'); --no-wire: only copy sheets (used for
the profit-pools source sheet), skip the Control panel / 'Model sept 26' wiring.

* Engine sheets (built with build_workbook.py --in-model, names 'CB ...') are copied as XML: styles are
  appended to the model's style sheet and re-indexed, shared strings become inline strings.
* 'Control panel' gets one new line per tier (row 22 / 45 / 68 / 91): the engine's effective cashback rate
  (% of non-cash, from 'CB Results' row 18) and a switch Engine / Target (default Engine).
* 'Model sept 26' cashback rate rows use the engine rate when the switch says Engine; the model's own
  cap-saving logic is switched off in that case (the engine already applies caps per client).
Everything else in the model package is left untouched.
"""
import copy
import re
import sys
import zipfile

from lxml import etree

MODEL, ENGINE, OUT = sys.argv[1:4]
AFTER = sys.argv[sys.argv.index('--after') + 1] if '--after' in sys.argv else 'PnL all tiers'
WIRE = '--no-wire' not in sys.argv
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'
CTN = '{http://schemas.openxmlformats.org/package/2006/content-types}'
XMLNS = '{http://www.w3.org/XML/1998/namespace}'

zm, ze = zipfile.ZipFile(MODEL), zipfile.ZipFile(ENGINE)
parts = {n: zm.read(n) for n in zm.namelist()}
eparts = {n: ze.read(n) for n in ze.namelist()}
X = lambda b: etree.fromstring(b)                                             # noqa: E731
S = lambda e: etree.tostring(e, xml_declaration=True, encoding='UTF-8', standalone=True)   # noqa: E731


def sheet_map(wb_xml, rels_xml):
    rels = {r.get('Id'): r.get('Target') for r in X(rels_xml)}
    out = []
    for s in X(wb_xml).find(N + 'sheets'):
        t = rels[s.get('{%s}id' % RNS)]
        out.append((s.get('name'), 'xl/' + t.lstrip('/').replace('xl/', '')))
    return out


# ------------------------------------------------------------------ 1. styles
ms, es = X(parts['xl/styles.xml']), X(eparts['xl/styles.xml'])


def child(root, tag, create_before=None):
    el = root.find(N + tag)
    if el is None:
        el = etree.Element(N + tag)
        if create_before is not None:
            root.find(N + create_before).addprevious(el)
        else:
            root.insert(0, el)
    return el


m_numfmts = child(ms, 'numFmts')
code2id = {nf.get('formatCode'): int(nf.get('numFmtId')) for nf in m_numfmts}
next_id = max([163] + list(code2id.values())) + 1
e_nf = {int(nf.get('numFmtId')): nf.get('formatCode') for nf in (es.find(N + 'numFmts') if es.find(N + 'numFmts') is not None else [])}
nf_map = {}
for eid, code in e_nf.items():
    if code in code2id:
        nf_map[eid] = code2id[code]
    else:
        el = etree.SubElement(m_numfmts, N + 'numFmt', numFmtId=str(next_id), formatCode=code)
        code2id[code] = next_id; nf_map[eid] = next_id; next_id += 1
m_numfmts.set('count', str(len(m_numfmts)))
base = {}
for tag in ('fonts', 'fills', 'borders'):
    mt, et = ms.find(N + tag), es.find(N + tag)
    base[tag] = len(mt)
    for e in et:
        mt.append(copy.deepcopy(e))
    mt.set('count', str(len(mt)))
mx, ex = ms.find(N + 'cellXfs'), es.find(N + 'cellXfs')
xf_map = {}
for i, e in enumerate(ex):
    x = copy.deepcopy(e)
    x.set('fontId', str(base['fonts'] + int(e.get('fontId', 0))))
    x.set('fillId', str(base['fills'] + int(e.get('fillId', 0))))
    x.set('borderId', str(base['borders'] + int(e.get('borderId', 0))))
    nid = int(e.get('numFmtId', 0))
    x.set('numFmtId', str(nf_map.get(nid, nid)))
    x.set('xfId', '0')
    mx.append(x)
    xf_map[i] = len(mx) - 1
mx.set('count', str(len(mx)))
parts['xl/styles.xml'] = S(ms)

# ------------------------------------------------------------------ 2. engine sheets -> model parts
sst = []
if 'xl/sharedStrings.xml' in eparts:
    for si in X(eparts['xl/sharedStrings.xml']):
        sst.append(''.join(t.text or '' for t in si.iter(N + 't')))
e_sheets = sheet_map(eparts['xl/workbook.xml'], eparts['xl/_rels/workbook.xml.rels'])
m_wb = X(parts['xl/workbook.xml'])
m_rels = X(parts['xl/_rels/workbook.xml.rels'])
m_sheets = m_wb.find(N + 'sheets')
existing = [n for n in parts if re.match(r'xl/worksheets/sheet\d+\.xml$', n)]
next_sheet = max(int(re.search(r'(\d+)', n.split('/')[-1]).group(1)) for n in existing) + 1
next_rid = max(int(r.get('Id')[3:]) for r in m_rels) + 1
next_sid = max(int(s.get('sheetId')) for s in m_sheets) + 1
anchor = [s for s in m_sheets if s.get('name') == AFTER][0]
pos = list(m_sheets).index(anchor) + 1
ct = X(parts['[Content_Types].xml'])
new_names = []
after = anchor
for name, epart in e_sheets:
    root = X(eparts[epart])
    for c in root.iter(N + 'c'):
        if c.get('s') is not None:
            c.set('s', str(xf_map[int(c.get('s'))]))
        if c.get('t') == 's':
            v = c.find(N + 'v')
            txt = sst[int(v.text)]
            c.remove(v)
            c.set('t', 'inlineStr')
            is_ = etree.SubElement(c, N + 'is')
            t = etree.SubElement(is_, N + 't'); t.text = txt
            if txt != txt.strip():
                t.set(XMLNS + 'space', 'preserve')
    for r in root.iter(N + 'row'):
        if r.get('s') is not None:
            r.set('s', str(xf_map[int(r.get('s'))]))
    for col in root.iter(N + 'col'):
        if col.get('style') is not None:
            col.set('style', str(xf_map[int(col.get('style'))]))
    for sv in root.iter(N + 'sheetView'):
        sv.attrib.pop('tabSelected', None)
    part = f'xl/worksheets/sheet{next_sheet}.xml'
    parts[part] = S(root)
    rid = f'rId{next_rid}'
    etree.SubElement(m_rels, PKG + 'Relationship', Id=rid,
                     Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet',
                     Target=f'worksheets/sheet{next_sheet}.xml')
    el = etree.Element(N + 'sheet'); el.set('name', name); el.set('sheetId', str(next_sid)); el.set('{%s}id' % RNS, rid)
    after.addnext(el); after = el
    etree.SubElement(ct, CTN + 'Override', PartName='/' + part,
                     ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
    new_names.append(name)
    next_sheet += 1; next_rid += 1; next_sid += 1
k = len(new_names)
dn = m_wb.find(N + 'definedNames')
if dn is not None:
    for d in dn:
        lid = d.get('localSheetId')
        if lid is not None and int(lid) >= pos:
            d.set('localSheetId', str(int(lid) + k))
for v in m_wb.find(N + 'bookViews'):
    for a in ('activeTab', 'firstSheet'):
        if v.get(a) and int(v.get(a)) >= pos:
            v.set(a, str(int(v.get(a)) + k))
m_wb.find(N + 'calcPr').set('fullCalcOnLoad', '1')
parts['xl/workbook.xml'] = S(m_wb)
for r in list(m_rels):
    if 'calcChain' in r.get('Target'):
        m_rels.remove(r)
parts['xl/_rels/workbook.xml.rels'] = S(m_rels)
parts.pop('xl/calcChain.xml', None)
for o in list(ct):
    if o.get('PartName') == '/xl/calcChain.xml':
        ct.remove(o)
parts['[Content_Types].xml'] = S(ct)
app = parts['docProps/app.xml'].decode('utf-8')
app = re.sub(r'(<vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + k), app)
app = re.sub(r'<TitlesOfParts><vt:vector size="(\d+)"', lambda m: f'<TitlesOfParts><vt:vector size="{int(m.group(1)) + k}"', app)
app = app.replace(f'<vt:lpstr>{AFTER}</vt:lpstr>', f'<vt:lpstr>{AFTER}</vt:lpstr>' + ''.join(f'<vt:lpstr>{n}</vt:lpstr>' for n in new_names), 1)
parts['docProps/app.xml'] = app.encode('utf-8')


# ------------------------------------------------------------------ 3. wire the model
class Sheet:
    def __init__(self, part):
        self.part, self.root = part, X(parts[part])
        self.data = self.root.find(N + 'sheetData')
        self.rows = {int(r.get('r')): r for r in self.data}

    def get(self, ref):
        r = self.rows.get(int(re.search(r'\d+', ref).group(0)))
        return None if r is None else next((c for c in r if c.get('r') == ref), None)

    def cell(self, ref):
        c = self.get(ref)
        if c is not None:
            return c
        rn = int(re.search(r'\d+', ref).group(0))
        row = self.rows.get(rn)
        if row is None:
            row = etree.Element(N + 'row', r=str(rn))
            prev = [x for x in self.rows if x < rn]
            (self.rows[max(prev)].addnext(row) if prev else self.data.insert(0, row))
            self.rows[rn] = row
        row.attrib.pop('spans', None)
        c = etree.Element(N + 'c', r=ref)
        key = lambda rf: (len(re.match(r'[A-Z]+', rf).group(0)), re.match(r'[A-Z]+', rf).group(0))   # noqa: E731
        for i, o in enumerate(row):
            if key(o.get('r')) > key(ref):
                row.insert(i, c); break
        else:
            row.append(c)
        return c

    def _reset(self, c, s):
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)
        if s is not None:
            c.set('s', str(s))

    def f(self, ref, formula, s=None):
        c = self.cell(ref); self._reset(c, s); etree.SubElement(c, N + 'f').text = formula

    def t(self, ref, text, s=None):
        c = self.cell(ref); self._reset(c, s); c.set('t', 'inlineStr')
        etree.SubElement(etree.SubElement(c, N + 'is'), N + 't').text = text

    def formula(self, ref):
        c = self.get(ref)
        f = None if c is None else c.find(N + 'f')
        return None if f is None else f.text

    def style(self, ref):
        c = self.get(ref)
        return None if c is None else c.get('s')

    def save(self):
        parts[self.part] = S(self.root)


msheets = dict(sheet_map(parts['xl/workbook.xml'], parts['xl/_rels/workbook.xml.rels']))
if not WIRE:
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in [n for n in zm.namelist() if n in parts] + [n for n in parts if n not in zm.namelist()]:
            z.writestr(n, parts[n])
    print('inserted sheets:', new_names, 'after', AFTER)
    sys.exit(0)
cp = Sheet(msheets['Control panel'])
md = Sheet(msheets['Model sept 26'])
TIERS = ['Free', 'Black', 'Premium', 'Elite']
HDR = {'Free': 6, 'Black': 29, 'Premium': 52, 'Elite': 75}
RES_COL = {'Free': 'D', 'Black': 'E', 'Premium': 'F', 'Elite': 'G'}
changes = []
for k_, t in enumerate(TIERS):
    h = HDR[t]
    tgt, cap, sw = h + 13, h + 14, h + 16
    assert cp.get(f'B{sw}') is None or not cp.get(f'B{sw}').findall(N + 'v'), f'Control panel B{sw} not empty'
    cp.t(f'B{sw}', 'Cashback rate from the engine at the target above, % of non-cash (CB Results)', cp.style(f'B{tgt}'))
    cp.f(f'C{sw}', f"'CB Results'!{RES_COL[t]}$18", cp.style(f'C{tgt}'))
    cp.t(f'D{sw}', 'Engine', cp.style(f'D{tgt}'))
    cp.t(f'O{sw}', 'P&L cashback source. Engine (default) = the engine scales its menu rates so bank cost = the target above '
                   '(column C; caps applied per client, so C can stay below the target only if caps bind - see CB Results "target reached?"). '
                   'Target = target rate above with the model\'s own cap logic', cp.style(f'O{cap}'))
    off = 77 * k_
    r_rate, r_save = 59 + off, 61 + off
    for col in 'EFGHIJK':
        old = md.formula(f'{col}{r_rate}')
        assert old == f"'Control panel'!$D${tgt}", (t, col, old)
        md.f(f'{col}{r_rate}', f"IF('Control panel'!$D${sw}=\"Engine\",'Control panel'!$C${sw},'Control panel'!$D${tgt})", md.style(f'{col}{r_rate}'))
        if col != 'I':
            f = md.formula(f'{col}{r_save}')
            nf = f.replace(f'IF({col}{r_rate}>0,', f"IF(AND({col}{r_rate}>0,'Control panel'!$D${sw}<>\"Engine\"),", 1)
            assert nf != f, (t, col, f)
            md.f(f'{col}{r_save}', nf, md.style(f'{col}{r_save}'))
    md.t(f'B{r_rate}', 'Cashback rate, % of non-cash payments (engine or Control panel target)', md.style(f'B{r_rate}'))
    changes.append((t, sw, r_rate, r_save))
# data validation for the switch
dvs = cp.root.find(N + 'dataValidations')
if dvs is None:
    dvs = etree.Element(N + 'dataValidations')
    anchor_el = None
    for tag in ('hyperlinks', 'printOptions', 'pageMargins'):
        anchor_el = cp.root.find(N + tag)
        if anchor_el is not None:
            break
    anchor_el.addprevious(dvs)
dv = etree.SubElement(dvs, N + 'dataValidation', type='list', allowBlank='1', showErrorMessage='1',
                      sqref=' '.join(f'D{HDR[t] + 16}' for t in TIERS))
etree.SubElement(dv, N + 'formula1').text = '"Engine,Target"'
dvs.set('count', str(len(dvs)))
cp.save(); md.save()

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in [n for n in zm.namelist() if n in parts] + [n for n in parts if n not in zm.namelist()]:
        z.writestr(n, parts[n])
print('inserted sheets:', new_names, 'at position', pos)
print('wired:', changes)
