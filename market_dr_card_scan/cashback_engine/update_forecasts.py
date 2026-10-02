"""Refresh market and bank forecasts from H21 'Market profit pools Armenia v5.1' (Alex, 24.09.2026).

    python3 update_forecasts.py extract <profit_pools_v5.1.xlsx> <out_extract.xlsx>
    python3 update_forecasts.py apply <model_with_extract.xlsx> <out.xlsx>

extract: builds a one-sheet workbook 'PP v5.1 extract' (values 2025-2030 + source cell for every line); it is
         then copied into the model with merge_into_model.py --after 'Market benchmarking' --no-wire.
apply:   * 'Market benchmarking': every hard-coded source row becomes a link to the extract; new columns
           H = 2029, I = 2030 (derived rows extended); notes move to column K.
         * 'Model sept 26': 2029 (column K) grows with 2029/2028 market growth instead of repeating 2028.
         * 'Planned KPIs': activated cards and new sales 2026-2030 from the Fast Bank plan in v5.1.
         * 'PnL all tiers': 2029 volumes from the plan (were extrapolated) + a cross-check block vs the plan.
XML-only edits; everything else in the package is untouched.
"""
import re
import sys
import zipfile

from lxml import etree
from openpyxl.formula.translate import Translator

M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
EXT = 'PP v5.1 extract'
XT = f"'{EXT}'"
YEARS = [2025, 2026, 2027, 2028, 2029, 2030]
YC = ['D', 'E', 'F', 'G', 'H', 'I']                       # year columns in the extract (and in Market benchmarking)

# (key, label, unit, v5.1 sheet, rows (summed), columns for 2025..2030)
MS = ['M', 'N', 'O', 'P', 'Q', 'R']
SEGP = ['L', 'N', 'O', 'P', 'Q', 'R']                      # 'Retail segmentation' population: 2025 = Sep column L
LINES = [
    ('h_mkt', 'MARKET (Armenia, retail)', None, None, None, None),
    ('pop', 'Bankarized population', 'people', 'Retail segmentation', [26], SEGP),
    ('pop_sp', '  Sub-prime (<100k)', 'people', 'Retail segmentation', [27], SEGP),
    ('pop_m', '  Mass (100k-400k)', 'people', 'Retail segmentation', [28], SEGP),
    ('pop_ma', '  Mass affluent (400k-975k)', 'people', 'Retail segmentation', [29], SEGP),
    ('pop_a', '  Affluent (975k+)', 'people', 'Retail segmentation', [30], SEGP),
    ('ca', 'Current accounts + demand deposits, retail', 'AMD mn', 'Retail segment pool', [56], MS),
    ('ca_sp', '  Sub-prime (<100k)', 'AMD mn', 'Retail segment pool', [57], MS),
    ('ca_m', '  Mass (100k-400k)', 'AMD mn', 'Retail segment pool', [58], MS),
    ('ca_ma', '  Mass affluent (400k-975k)', 'AMD mn', 'Retail segment pool', [59], MS),
    ('ca_a', '  Affluent (975k+)', 'AMD mn', 'Retail segment pool', [60], MS),
    ('ca_nr', '  Non-residents', 'AMD mn', 'Retail segment pool', [61], MS),
    ('pr', 'Retail payments revenue (after risk)', 'AMD mn', 'Retail segment pool', [262], MS),
    ('pr_sp', '  Sub-prime (<100k)', 'AMD mn', 'Retail segment pool', [263], MS),
    ('pr_m', '  Mass (100k-400k)', 'AMD mn', 'Retail segment pool', [264], MS),
    ('pr_ma', '  Mass affluent (400k-975k)', 'AMD mn', 'Retail segment pool', [265], MS),
    ('pr_a', '  Affluent (975k+)', 'AMD mn', 'Retail segment pool', [266], MS),
    ('nc', 'Non-cash payments (offline + online + C2G + utilities)', 'AMD mn', 'Market summary', [29, 30, 32, 33], MS),
    ('cash', 'Cash withdrawals', 'AMD mn', 'Market summary', [28], MS),
    ('c2c', 'C2C transfers', 'AMD mn', 'Market summary', [31], MS),
    ('fxdep', 'FX retail deposits + current accounts', 'AMD mn', 'Deposits', [12, 15], MS),
    ('fxrev', 'FX retail revenue', 'AMD mn', 'Market summary', [99], MS),
    ('h_bank', 'FAST BANK PLAN (v5.1 \'Bank model - main\')', None, None, None, None),
    ('cards', 'Activated debit cards, end of year', 'pcs', 'Bank model - main', [194], MS),
    ('sales', 'New sales, activated debit cards', 'pcs', 'Bank model - main', [200], MS),
    ('bal', 'Debit card balances (portfolio)', 'AMD mn', 'Bank model - main', [192], MS),
    ('balpc', 'Average balance per activated card', 'AMD', None, None, None),
    ('cb', 'Cashback paid (bank plan, cost)', 'AMD mn', 'Bank model - main', [98], MS),
    ('fee', 'Net fee income – retail payments', 'AMD mn', 'Bank model - main', [74], MS),
    ('clients', 'Clients', '#', 'Bank model - main', [113], MS),
    ('fca', 'Current accounts – retail (Fast Bank)', 'AMD mn', 'Bank model - main', [30], MS),
]
ROW = {k: 5 + i for i, (k, *_) in enumerate(LINES)}


def build_extract(src, out):
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    wb_src = openpyxl.load_workbook(src, data_only=True, read_only=True)
    cache = {}

    def val(sheet, ref):
        if sheet not in cache:
            cache[sheet] = {(c.coordinate): c.value for row in wb_src[sheet].iter_rows() for c in row if c.value is not None and hasattr(c, 'coordinate')}
        return cache[sheet].get(ref)

    wb = openpyxl.Workbook(); ws = wb.active; ws.title = EXT
    F, B, BL = Font(name='Arial', size=10), Font(name='Arial', size=10, bold=True), Font(name='Arial', size=10, color='0000FF')
    H = Font(name='Arial', size=10, bold=True, color='FFFFFF'); FH = PatternFill('solid', fgColor='1F3864'); FS = PatternFill('solid', fgColor='D9E1F2')
    ws['B1'] = "H21 MARKET PROFIT POOLS ARMENIA v5.1 – EXTRACT USED BY THIS MODEL"; ws['B1'].font = Font(name='Arial', size=14, bold=True)
    ws['B2'] = ("Values copied from 'Market profit pools Armenia v5.1.xlsx' (24.09.2026) as an interim intelligence source until the bank's data request is answered. "
                "Column J names the v5.1 sheet and row. 'Market benchmarking' and 'Planned KPIs' link here.")
    ws['B2'].font = Font(name='Arial', size=9, italic=True, color='666666')
    for c, lab in zip(['B', 'C'] + YC + ['J'], ['Item', 'Unit'] + [str(y) for y in YEARS] + ['Source (v5.1 sheet, row)']):
        ws[f'{c}4'] = lab; ws[f'{c}4'].font = H; ws[f'{c}4'].fill = FH; ws[f'{c}4'].alignment = Alignment(horizontal='center')
    for key, lab, unit, sheet, rows, cols in LINES:
        r = ROW[key]
        ws[f'B{r}'] = lab
        ws[f'B{r}'].font = B if unit is None or not lab.startswith('  ') else F
        if unit is None:
            for c in ['B', 'C'] + YC + ['J']:
                ws[f'{c}{r}'].fill = FS
            continue
        ws[f'C{r}'] = unit; ws[f'C{r}'].font = F
        if key == 'balpc':
            for c in YC:
                ws[f'{c}{r}'] = f'=IFERROR({c}{ROW["bal"]}/{c}{ROW["cards"]}*10^6,0)'; ws[f'{c}{r}'].font = F; ws[f'{c}{r}'].number_format = '#,##0'
            ws[f'J{r}'] = 'Card balances ÷ activated cards'
            continue
        for c, sc in zip(YC, cols):
            v = sum((val(sheet, f'{sc}{rr}') or 0) for rr in rows)
            ws[f'{c}{r}'] = float(v); ws[f'{c}{r}'].font = BL; ws[f'{c}{r}'].number_format = '#,##0;(#,##0);-'
        ws[f'J{r}'] = f"'{sheet}' row {' + '.join(str(x) for x in rows)}, columns {cols[0]}–{cols[-1]}" + (" (2025 = 'Sep' column)" if cols[0] == 'L' else '')
        ws[f'J{r}'].font = Font(name='Arial', size=9, italic=True, color='666666')
    for c, w in zip(['A', 'B', 'C'] + YC + ['J'], [2, 52, 9] + [14] * 6 + [60]):
        ws.column_dimensions[c].width = w
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = 'D5'
    wb.save(out)
    print('extract rows', ROW)


# ------------------------------------------------------------------ XML helpers for 'apply'
def colnum(c):
    n = 0
    for ch in c:
        n = n * 26 + ord(ch) - 64
    return n


class Sheet:
    def __init__(self, parts, part):
        self.parts, self.part = parts, part
        self.root = etree.fromstring(parts[part])
        self.data = self.root.find(N + 'sheetData')
        self.rows = {int(r.get('r')): r for r in self.data}
        master = {}
        for c in self.data.iter(N + 'c'):                           # unshare shared formulas
            f = c.find(N + 'f')
            if f is None or f.get('t') != 'shared':
                continue
            si = f.get('si')
            if f.text:
                master[si] = (c.get('r'), f.text); txt = f.text
            else:
                o, t0 = master[si]; txt = Translator('=' + t0, origin=o).translate_formula(c.get('r'))[1:]
            for a in ('t', 'si', 'ref'):
                f.attrib.pop(a, None)
            f.text = txt

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
        k = colnum(re.match(r'[A-Z]+', ref).group(0))
        for i, o in enumerate(row):
            if colnum(re.match(r'[A-Z]+', o.get('r')).group(0)) > k:
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
        c = self.cell(ref); self._reset(c, s); etree.SubElement(c, N + 'f').text = formula.lstrip('=')

    def n(self, ref, v, s=None):
        c = self.cell(ref); self._reset(c, s); etree.SubElement(c, N + 'v').text = repr(float(v))

    def t(self, ref, text, s=None):
        c = self.cell(ref); self._reset(c, s); c.set('t', 'inlineStr')
        etree.SubElement(etree.SubElement(c, N + 'is'), N + 't').text = text

    def text(self, ref, sst):
        c = self.get(ref)
        if c is None:
            return None
        if c.get('t') == 's':
            return sst[int(c.find(N + 'v').text)]
        if c.get('t') == 'inlineStr':
            return ''.join(x.text or '' for x in c.iter(N + 't'))
        v = c.find(N + 'v')
        return None if v is None else v.text

    def formula(self, ref):
        c = self.get(ref)
        f = None if c is None else c.find(N + 'f')
        return None if f is None else f.text

    def style(self, ref):
        c = self.get(ref)
        return None if c is None else c.get('s')

    def remove(self, ref):
        c = self.get(ref)
        if c is not None:
            c.getparent().remove(c)

    def save(self):
        dim = self.root.find(N + 'dimension')
        if dim is not None:
            dim.getparent().remove(dim)                              # Excel recomputes it
        self.parts[self.part] = etree.tostring(self.root, xml_declaration=True, encoding='UTF-8', standalone=True)


def sheet_parts(parts):
    wb = etree.fromstring(parts['xl/workbook.xml'])
    rels = {r.get('Id'): r.get('Target') for r in etree.fromstring(parts['xl/_rels/workbook.xml.rels'])}
    return {s.get('name'): 'xl/' + rels[s.get('{%s}id' % RNS)].lstrip('/').replace('xl/', '') for s in wb.find(N + 'sheets')}


def apply(src, out):
    z = zipfile.ZipFile(src)
    parts = {n: z.read(n) for n in z.namelist()}
    sst = [''.join(t.text or '' for t in si.iter(N + 't')) for si in etree.fromstring(parts['xl/sharedStrings.xml'])]
    sp = sheet_parts(parts)
    log = []

    # ---------------- Market benchmarking
    mb = Sheet(parts, sp['Market benchmarking'])
    MAP = {15: 'pop', 23: 'ca', 24: 'ca_sp', 25: 'ca_m', 26: 'ca_ma', 27: 'ca_a', 28: 'ca_nr', 38: 'pop', 39: 'pop_sp', 40: 'pop_m',
           41: 'pop_ma', 42: 'pop_a', 60: 'pr', 61: 'pr_sp', 62: 'pr_m', 63: 'pr_ma', 64: 'pr_a', 66: 'nc', 82: 'cash', 98: 'c2c',
           114: 'fxdep', 117: 'fxrev'}
    rows = sorted(mb.rows)
    for r in rows:                                                   # move notes H -> K
        txt = mb.text(f'H{r}', sst)
        if txt is not None and mb.formula(f'H{r}') is None and not re.match(r'^-?[\d.E+-]+$', str(txt)):
            s = mb.style(f'H{r}')
            mb.remove(f'H{r}')
            mb.t(f'K{r}', txt, s)
    for r in (14, 21):
        s = mb.style(f'G{r}')
        mb.n(f'H{r}', 2029, s); mb.n(f'I{r}', 2030, s)
    for r, key in MAP.items():
        s = mb.style(f'G{r}') or mb.style(f'D{r}')
        for c in YC:
            before = mb.text(f'{c}{r}', sst)
            mb.f(f'{c}{r}', f"{XT}!{c}{ROW[key]}", s)
        mb.t(f'K{r}', f"Source: H21 profit pools v5.1 – '{EXT}' row {ROW[key]} (was typed from the earlier version)", mb.style(f'K{r}'))
        log.append(('MB', r, key))
    for r, vals in ((17, (3.3, 3.45)), (29, (0.5, 0.5))):
        s = mb.style(f'G{r}')
        mb.n(f'H{r}', vals[0], s); mb.n(f'I{r}', vals[1], s)
    mb.t('K17', 'Assumption: 2029–2030 continue +0.15 cards per person a year', mb.style('K15'))
    for r in rows:                                                   # extend derived formulas G -> H, I
        if r in MAP or r in (14, 17, 21, 29):
            continue
        fg = mb.formula(f'G{r}')
        if fg is None:
            continue
        s = mb.style(f'G{r}')
        for c in ('H', 'I'):
            mb.f(f'{c}{r}', Translator('=' + fg, origin=f'G{r}').translate_formula(f'{c}{r}')[1:], s)
    cols = mb.root.find(N + 'cols')
    if cols is not None:
        for c in list(cols):
            if int(c.get('max')) >= 8:
                if int(c.get('min')) >= 8:
                    cols.remove(c)
                else:
                    c.set('max', '7')
        for mn, mx, w in ((8, 9, '12.83203125'), (11, 11, '70')):
            e = etree.SubElement(cols, N + 'col'); e.set('min', str(mn)); e.set('max', str(mx)); e.set('width', w); e.set('customWidth', '1')
        ordered = sorted(cols, key=lambda e: int(e.get('min')))
        for e in ordered:
            cols.remove(e)
        for e in ordered:
            cols.append(e)
    mb.save()

    # ---------------- Model sept 26: 2029 grows with 2029/2028 market growth
    md = Sheet(parts, sp['Model sept 26'])
    n_k = 0
    for blk in range(4):
        for base in (21, 30, 35, 39, 48):
            ref = f'K{base + 77 * blk}'
            f = md.formula(ref)
            if f is None or 'Market benchmarking' not in f:
                continue
            nf = re.sub(r"'Market benchmarking'!\$G\$(\d+)/'Market benchmarking'!\$F\$(\d+)",
                        lambda m: f"'Market benchmarking'!$H${m.group(1)}/'Market benchmarking'!$G${m.group(2)}", f)
            nf = re.sub(r"'Market benchmarking'!G(\d+)", r"'Market benchmarking'!H\1", nf)
            if nf != f:
                md.f(ref, nf, md.style(ref)); n_k += 1
    md.save()
    log.append(('Model K formulas re-pointed', n_k))

    # ---------------- Planned KPIs
    pk = Sheet(parts, sp['Planned KPIs'])
    for r in (7, 12):
        note = pk.text(f'M{r}', sst)
        s = pk.style(f'M{r}')
        pk.remove(f'M{r}')
        pk.t(f'O{r}', "Source: Fast Bank plan in H21 profit pools v5.1 ('Bank model - main'), via 'PP v5.1 extract'" + (f' (was: {note})' if note else ''), s)
    s6 = pk.style('L6')
    pk.n('M6', 2029, s6); pk.n('N6', 2030, s6)
    for r, key in ((7, 'cards'), (12, 'sales')):
        s = pk.style(f'L{r}')
        for c, xc in zip(['J', 'K', 'L', 'M', 'N'], ['E', 'F', 'G', 'H', 'I']):
            pk.f(f'{c}{r}', f"{XT}!{xc}{ROW[key]}", s)
    for r in (8, 9, 10, 13, 14, 15):
        fl = pk.formula(f'L{r}')
        s = pk.style(f'L{r}')
        for c in ('M', 'N'):
            pk.f(f'{c}{r}', Translator('=' + fl, origin=f'L{r}').translate_formula(f'{c}{r}')[1:], s)
    pk.save()

    # ---------------- PnL all tiers
    pn = Sheet(parts, sp['PnL all tiers'])
    assert pn.formula('G6') and pn.formula('G7'), 'unexpected PnL layout'
    pn.f('G6', "'Planned KPIs'!M7", pn.style('F6'))
    pn.f('G7', "'Planned KPIs'!M12", pn.style('F7'))
    pn.t('J6', "'Planned KPIs' row 7 – Fast Bank plan from H21 profit pools v5.1 ('Bank model - main'); 2029 now from the plan (was extrapolated).", pn.style('J6'))
    pn.t('J7', "'Planned KPIs' row 12 – new sales from the same plan.", pn.style('J7'))
    r0 = 101
    hs, hy = pn.style('B80'), pn.style('E80')
    pn.t(f'B{r0}', "5. CROSS-CHECK VS THE BANK PLAN (H21 profit pools v5.1, 'Bank model - main')", hs)
    pn.t(f'C{r0}', 'Unit', pn.style('C80'))
    for c, y in zip('EFG', (2027, 2028, 2029)):
        pn.n(f'{c}{r0}', y, hy)
    pn.t(f'H{r0}', '3Y total', pn.style('H80'))
    lab_s, num_s, unit_s, note_s = pn.style('B83'), pn.style('E90'), pn.style('C83'), pn.style('J92')
    checks = [
        ('Debit card balances – bank plan', 'AMD mn', lambda c, x: f"{XT}!{x}{ROW['bal']}", 'avg'),
        ('Average card balances – this model', 'AMD mn', lambda c, x: f'{c}92', 'avg'),
        ('Cashback – bank plan', 'AMD mn', lambda c, x: f"-{XT}!{x}{ROW['cb']}", 'sum'),
        ('Cashback – this model', 'AMD mn', lambda c, x: f'{c}46', 'sum'),
        ('Net fee income, retail payments – bank plan', 'AMD mn', lambda c, x: f"{XT}!{x}{ROW['fee']}", 'sum'),
        ('Fee and commission income – this model (interchange, cash-out, transfers, FX, service fees)', 'AMD mn', lambda c, x: f'SUM({c}40:{c}44)', 'sum'),
    ]
    for i, (lab, unit, fn, tot) in enumerate(checks):
        r = r0 + 1 + i
        pn.t(f'B{r}', lab, lab_s); pn.t(f'C{r}', unit, unit_s)
        for c, x in zip('EFG', 'FGH'):
            pn.f(f'{c}{r}', fn(c, x), num_s)
        pn.f(f'H{r}', f'SUM(E{r}:G{r})' if tot == 'sum' else f'AVERAGE(E{r}:G{r})', num_s)
    pn.t(f'J{r0 + 1}', 'Plan balances are year-end; the model shows the yearly average of active cards × balance per card.', note_s)
    pn.t(f'J{r0 + 3}', "The plan's cashback budget is bank-wide (all cards); this model counts debit-card cashback from the engine.", note_s)
    pn.t(f'J{r0 + 5}', "The plan's line is net of payment costs; the model's line is gross revenue.", note_s)
    pn.save()

    parts['xl/workbook.xml'] = parts['xl/workbook.xml'].replace(b'<calcPr ', b'<calcPr fullCalcOnLoad="1" ', 1) \
        if b'fullCalcOnLoad' not in parts['xl/workbook.xml'] else parts['xl/workbook.xml']
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in z.namelist():
            zo.writestr(n, parts[n])
    for l in log:
        print(l)


if __name__ == '__main__':
    if sys.argv[1] == 'extract':
        build_extract(sys.argv[2], sys.argv[3])
    else:
        apply(sys.argv[2], sys.argv[3])
