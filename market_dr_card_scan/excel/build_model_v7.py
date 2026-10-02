"""Debit cards model v6 -> v7: apply the Fast Free logic to Black / Premium / Elite, add a tier
mapping to 'Current cards' and a combined P&L tab ('PnL all tiers').

The workbook carries pivots, images, threaded comments, a data connection and dynamic-array
metadata that openpyxl would drop, so this edits only sheet XML (plus styles / workbook / content
types) and leaves every other part of the package byte-for-byte untouched.

    python3 build_model_v7.py <in.xlsx> <out.xlsx>

Layout decisions (agreed with Alex, 22.09.2026)
  * Tiers: Free = Visa Digital; Black = ArCa Classic + Visa Classic; Premium = MC World + Visa Gold;
    Elite = MC World Elite + Visa Infinite + Visa Infinite Metal.
  * Non-cash = local + international. Tier actuals are volume sums over the tier's cards
    ('Current cards' rows 146+), so AMD-only ArCa Classic carries no FX / international weight.
  * FX revenue converges to the segment benchmark x the tier's share of it (Free / Black split the
    'Fast Black' row by FX interest per card; Premium, Elite take 100% of their segment row).
  * Processing: ArCa fee on all volume, Visa/MC fee only on the non-ArCa share of volume.
  * First-year OPEX: plastic / delivery / embossing / ATM activation scaled by (1 - virtual share);
    plastic cost blends plastic and metal by the metal share (Control panel).
  * Volumes: 'Planned KPIs' totals (2029 extrapolated), split by today's activated mix (editable).
"""
import copy
import re
import sys
import zipfile

from lxml import etree
from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.formula.translate import Translator
from openpyxl.utils import column_index_from_string, get_column_letter

SRC, OUT = sys.argv[1:3]
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
CC_XML, EC_XML, CP_XML = 'xl/worksheets/sheet4.xml', 'xl/worksheets/sheet6.xml', 'xl/worksheets/sheet7.xml'
EC, CP, CC = "'Economics Sept26 Upd'", "'Control panel'", "'Current cards'"
PNL_NAME, PNL_XML = 'PnL all tiers', 'xl/worksheets/sheet35.xml'

zin = zipfile.ZipFile(SRC)
parts = {n: zin.read(n) for n in zin.namelist()}

# ------------------------------------------------------------------ styles
styles = etree.fromstring(parts['xl/styles.xml'])
xfs = styles.find(N + 'cellXfs')


def xf_like(base, numfmt=None, bold=None):
    x = copy.deepcopy(xfs[base])
    if numfmt is not None:
        x.set('numFmtId', str(numfmt)); x.set('applyNumberFormat', '1')
    xfs.append(x); xfs.set('count', str(len(xfs)))
    return len(xfs) - 1


S = dict(
    asm_pct=xf_like(904, 10), asm_num=xf_like(904, 165), asm_txt=904,     # 'Assumption' (input) look
    lnk_num=393, lnk_pct=567,                                                # 'Link to other sheet' look
    num=386, num_b=514, pct=394, pct1=439, txt=0, txt_b=388, ital=1106,
    num1=xf_like(386, 166), num1_b=xf_like(514, 166),
    hdr=1095, hdr_y=1097, hdr_sub=1096, title=1116,
    cc_hdr=462, cc_num=386, cc_pct=394, cc_lbl=0, cc_title=542,
)


# ------------------------------------------------------------------ sheet helpers
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
        # unshare shared formulas so every cell carries its own formula text
        master = {}
        for c in self.data.iter(N + 'c'):
            f = c.find(N + 'f')
            if f is None or f.get('t') != 'shared':
                continue
            si = f.get('si')
            if f.text:
                master[si] = (c.get('r'), f.text)
                txt = f.text
            else:
                o, t0 = master[si]
                txt = Translator('=' + t0, origin=o).translate_formula(c.get('r'))[1:]
            for a in ('t', 'si', 'ref'):
                f.attrib.pop(a, None)
            f.text = txt

    def row(self, r):
        if r not in self.rows:
            el = etree.Element(N + 'row'); el.set('r', str(r))
            before = [k for k in self.rows if k < r]
            if before:
                self.rows[max(before)].addnext(el)
            else:
                self.data.insert(0, el)
            self.rows[r] = el
        el = self.rows[r]
        el.attrib.pop('spans', None)
        return el

    def get(self, ref):
        r = self.rows.get(rownum(ref))
        if r is None:
            return None
        for c in r:
            if c.get('r') == ref:
                return c
        return None

    def cell(self, ref):
        c = self.get(ref)
        if c is not None:
            return c
        row = self.row(rownum(ref))
        c = etree.Element(N + 'c'); c.set('r', ref)
        k = colnum(ref)
        for i, other in enumerate(row):
            if colnum(other.get('r')) > k:
                row.insert(i, c); break
        else:
            row.append(c)
        return c

    @staticmethod
    def _reset(c, s):
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)
        if s is not None:
            c.set('s', str(s))

    def f(self, ref, formula, s=None):
        c = self.cell(ref); self._reset(c, s)
        etree.SubElement(c, N + 'f').text = formula.lstrip('=')

    def n(self, ref, value, s=None):
        c = self.cell(ref); self._reset(c, s)
        etree.SubElement(c, N + 'v').text = repr(float(value)) if isinstance(value, float) else str(value)

    def t(self, ref, text, s=None):
        c = self.cell(ref); self._reset(c, s)
        c.set('t', 'inlineStr')
        is_ = etree.SubElement(c, N + 'is'); tt = etree.SubElement(is_, N + 't'); tt.text = text
        if text != text.strip():
            tt.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

    def clear(self, ref):
        c = self.get(ref)
        if c is not None:
            c.getparent().remove(c)

    def formula(self, ref):
        c = self.get(ref)
        if c is None:
            return None
        f = c.find(N + 'f')
        return None if f is None else f.text

    def save(self):
        for r in list(self.data):
            if len(r) == 0 and not r.attrib.get('ht') and not r.attrib.get('hidden'):
                self.data.remove(r)
        # rows must be in order
        ordered = sorted(self.data, key=lambda e: int(e.get('r')))
        for e in ordered:
            self.data.remove(e)
        for e in ordered:
            self.data.append(e)
        for r in self.data:
            cells = sorted(r, key=lambda c: colnum(c.get('r')))
            for c in cells:
                r.remove(c)
            for c in cells:
                r.append(c)
        parts[self.part] = etree.tostring(self.root, xml_declaration=True, encoding='UTF-8', standalone=True)


# ------------------------------------------------------------------ formula rewriting
REF = re.compile(r'(\$?)([A-Z]{1,3})(\$?)(\d+)')


def rewrite(formula, fn):
    """Apply fn(sheet_or_None, col_abs, col, row_abs, row) -> (col, row) to every cell reference."""
    tok = Tokenizer('=' + formula)
    out = []
    for t in tok.items:
        v = t.value
        if t.type == 'OPERAND' and t.subtype == 'RANGE':
            if '!' in v:
                sheet, rng = v.rsplit('!', 1)
                sname = sheet.strip("'")
            else:
                sheet, rng, sname = None, v, None

            def sub(m):
                col, row = fn(sname, m.group(1), m.group(2), m.group(3), int(m.group(4)))
                return f'{m.group(1)}{col}{m.group(3)}{row}'
            rng = REF.sub(sub, rng)
            v = (sheet + '!' + rng) if sheet else rng
        out.append(v)
    return ''.join(out)


FREE0, FREE1 = 7, 75                     # Free block rows in 'Economics Sept26 Upd'
OFF = {'free': 0, 'black': 73, 'premium': 146, 'elite': 219}
TIERS = ['free', 'black', 'premium', 'elite']
TK = {t: i for i, t in enumerate(TIERS)}
MAPCOL = {'free': 'N', 'black': 'O', 'premium': 'P', 'elite': 'Q'}          # 'Current cards' tier columns
SEG = {'free': 0, 'black': 0, 'premium': 1, 'elite': 2}                     # 'Fast Black' / 'Fast Premium' / 'Fast Signature'
MB_SEG_ROWS = {56, 78, 94, 110, 130}
MAP0 = 146                                                                   # first mapping row in 'Current cards'


def clone_formula(formula, tier):
    off, k = OFF[tier], TK[tier]

    def fn(sname, ca, col, ra, row):
        if sname is None:                                   # same sheet: move with the block
            if FREE0 <= row <= FREE1:
                row += off
        elif sname == 'Control panel':
            if 5 <= row <= 22:
                row += 20 * k
        elif sname == 'Current cards':
            if row >= MAP0 and col == 'N':
                col = MAPCOL[tier]
        elif sname == 'Market benchmarking':
            if row in MB_SEG_ROWS:
                row += SEG[tier]
        return col, row
    return rewrite(formula, fn)


# ================================================================== 1. 'Current cards': tier mapping
cc = Sheet(CC_XML)
CARDS = list('DEFGHIJK')          # ArCa, MC World, MC World Elite, Visa Classic, Visa Gold, Infinite, Infinite Metal, Visa Digital
TIER_OF = dict(D='Black', E='Premium', F='Elite', G='Black', H='Premium', I='Elite', J='Elite', K='Free')
DB_ROW = dict(D=3, E=5, F=7, G=4, H=6, I=8, J=9, K=2)                    # Extract_client_DB pivot rows
TCOLS = ['N', 'O', 'P', 'Q']
TKEY = dict(N='Free', O='Black', P='Premium', Q='Elite')
TNAME = dict(N='Fast Free', O='Fast Black', P='Fast Premium', Q='Fast Elite')
R = {}                             # mapping row numbers by key


def tsel(tc):                     # SUMPRODUCT mask: cards belonging to the tier in column tc
    return f'($D${MAP0 + 2}:$K${MAP0 + 2}={tc}${MAP0 + 2})'


r = MAP0
cc.t(f'B{r}', "TIER MAPPING - Q4 2025 actuals by new tier (feeds 'Economics Sept26 Upd'; added 22.09.2026)", S['cc_title'])
r += 1; R['hdr'] = r
cc.t(f'B{r}', 'Metric', S['cc_hdr']); cc.t(f'C{r}', 'Units', S['cc_hdr'])
for c in CARDS:
    cc.f(f'{c}{r}', f'{c}$6', S['cc_hdr'])
cc.t(f'L{r}', 'Total', S['cc_hdr'])
for tc in TCOLS:
    cc.t(f'{tc}{r}', TNAME[tc], S['cc_hdr'])
r += 1; R['tier'] = r
cc.t(f'B{r}', 'New tier', S['cc_lbl'])
for c in CARDS:
    cc.t(f'{c}{r}', TIER_OF[c], S['asm_txt'])
for tc in TCOLS:
    cc.t(f'{tc}{r}', TKEY[tc], S['txt_b'])
r += 1; R['cur'] = r
cc.t(f'B{r}', 'Account currencies (tariff)', S['cc_lbl'])
for c in CARDS:
    cc.t(f'{c}{r}', 'AMD only' if c == 'D' else 'AMD, USD, EUR, RUB', S['cc_lbl'])
r += 1; R['fxcap'] = r
cc.t(f'B{r}', 'Holds FX balances and pays abroad (1 = yes)', S['cc_lbl'])
for c in CARDS:
    cc.n(f'{c}{r}', 0 if c == 'D' else 1, S['asm_num'])
r += 1; R['metal'] = r
cc.t(f'B{r}', 'Metal card (1 = yes)', S['cc_lbl'])
for c in CARDS:
    cc.n(f'{c}{r}', 1 if c == 'J' else 0, S['asm_num'])

SUMROWS = [  # key, label, unit, per-card formula template ({c} = card column)
    ('act', 'Activated cards', 'pcs', '{c}8'),
    ('loc', 'Non-cash payments, local, monthly total', 'AMD', '{c}47'),
    ('intl', 'Non-cash payments, international, monthly total', 'AMD', '{c}52'),
    ('nc', 'Non-cash payments, total (local + international)', 'AMD', None),
    ('trx', 'Transactions, monthly total', 'pcs', '{c}54'),
    ('cash', 'Cashout, monthly total', 'AMD', '{c}71'),
    ('cash_oth', "  of which at other banks' ATMs", 'AMD', '{c}69'),
    ('c2c', 'C2C transfers to other banks, monthly total', 'AMD', '{c}79'),
    ('proc', 'Processed volume (non-cash + cashout + C2C)', 'AMD', None),
    ('bal_amd', 'Card balances in AMD', 'AMD', '{c}92'),
    ('bal_fx', 'Card balances in FX', 'AMD', '{c}99'),
    ('fxrev', 'FX revenue, monthly total', 'AMD', '{c}83'),
    ('dep', 'Deposit balances of cardholders, monthly average (Aug-25 to Aug-26)', 'AMD', None),
]
for key, label, unit, tpl in SUMROWS:
    r += 1; R[key] = r
    cc.t(f'B{r}', label, S['cc_lbl']); cc.t(f'C{r}', unit, S['cc_lbl'])
    for c in CARDS:
        if key == 'nc':
            fml = f'{c}{R["loc"]}+{c}{R["intl"]}'
        elif key == 'proc':
            fml = f'{c}{R["nc"]}+{c}{R["cash"]}+{c}{R["c2c"]}'
        elif key == 'dep':
            fml = f'Extract_client_DB!$G${DB_ROW[c]}/13'
        else:
            fml = tpl.format(c=c)
        cc.f(f'{c}{r}', fml, S['lnk_num'] if tpl or key == 'dep' else S['cc_num'])
    cc.f(f'L{r}', f'SUM(D{r}:K{r})', S['cc_num'])
    for tc in TCOLS:
        cc.f(f'{tc}{r}', f'SUMIF($D${R["tier"]}:$K${R["tier"]},{tc}${R["tier"]},$D{r}:$K{r})', S['cc_num'])

PERCARD = [  # per-card rates / costs with a weighted tier value
    ('fxint', 'FX interest income per card, monthly', 'AMD', '{c}94', S['lnk_num']),
    ('icm', 'Local interchange margin', '%', '{c}45', S['lnk_pct']),
    ('plastic', 'Plastic / metal cost per card', 'AMD', '{c}109', S['lnk_num']),
    ('branch', 'Branch cost per new card (excluded from OPEX, as in Fast Free)', 'AMD', '{c}127', S['lnk_num']),
]
for key, label, unit, tpl, st in PERCARD:
    r += 1; R[key] = r
    cc.t(f'B{r}', label, S['cc_lbl']); cc.t(f'C{r}', unit, S['cc_lbl'])
    for c in CARDS:
        cc.f(f'{c}{r}', tpl.format(c=c), st)

r += 2
cc.t(f'B{r}', 'Per-card actuals and weights by tier', S['cc_title'])
TIERROWS = [  # key, label, unit, formula template ({t} = tier column), pct?
    ('nc_pc', 'Non-cash payments per card, monthly', 'AMD', '{t}{nc}/{t}{act}', 0),
    ('trx_pc', 'Transactions per card, monthly', 'pcs', '{t}{trx}/{t}{act}', 0),
    ('cash_pc', 'Cashout per card, monthly', 'AMD', '{t}{cash}/{t}{act}', 0),
    ('c2c_pc', 'C2C transfers per card, monthly', 'AMD', '{t}{c2c}/{t}{act}', 0),
    ('bal_pc', 'Card balance per card (AMD + FX)', 'AMD', '({t}{bal_amd}+{t}{bal_fx})/{t}{act}', 0),
    ('fx_pc', 'FX revenue per card, monthly', 'AMD', '{t}{fxrev}/{t}{act}', 0),
    ('dep_pc', 'Deposit balances per card', 'AMD', '{t}{dep}/{t}{act}', 0),
    ('intl_sh', 'International share of non-cash payments', '%', '{t}{intl}/{t}{nc}', 1),
    ('fxbal_sh', 'FX share of card balances', '%', '{t}{bal_fx}/({t}{bal_amd}+{t}{bal_fx})', 1),
    ('oth_sh', "Share of cashout at other banks' ATMs", '%', '{t}{cash_oth}/{t}{cash}', 1),
    ('arca_nc', 'ArCa Classic (AMD-only) share of non-cash payments', '%', 'SUMPRODUCT({m}*($D${fxcap}:$K${fxcap}=0)*$D${nc}:$K${nc})/{t}{nc}', 1),
    ('arca_cash', 'ArCa Classic share of cashout', '%', 'SUMPRODUCT({m}*($D${fxcap}:$K${fxcap}=0)*$D${cash}:$K${cash})/{t}{cash}', 1),
    ('arca_proc', 'ArCa Classic share of processed volume', '%', 'SUMPRODUCT({m}*($D${fxcap}:$K${fxcap}=0)*$D${proc}:$K${proc})/{t}{proc}', 1),
    ('arca_bal', 'ArCa Classic share of card balances', '%', 'SUMPRODUCT({m}*($D${fxcap}:$K${fxcap}=0)*($D${bal_amd}:$K${bal_amd}+$D${bal_fx}:$K${bal_fx}))/({t}{bal_amd}+{t}{bal_fx})', 1),
    ('intl_cap', 'International share of non-cash on FX-capable cards', '%', 'IFERROR({t}{intl}/({t}{nc}*(1-{t}{arca_nc})),0)', 1),
    ('fxbal_cap', 'FX share of balances on FX-capable cards', '%', 'IFERROR({t}{bal_fx}/(({t}{bal_amd}+{t}{bal_fx})*(1-{t}{arca_bal})),0)', 1),
    ('icm_t', 'Local interchange margin, weighted by local volume', '%', 'SUMPRODUCT({m}*$D${icm}:$K${icm}*$D${loc}:$K${loc})/{t}{loc}', 1),
    ('plastic_t', 'Plastic cost per non-metal physical card, weighted by cards', 'AMD',
     'IFERROR(SUMPRODUCT({m}*($D${metal}:$K${metal}=0)*$D${plastic}:$K${plastic}*$D${act}:$K${act})/SUMPRODUCT({m}*($D${metal}:$K${metal}=0)*$D${act}:$K${act}),0)', 0),
    ('branch_t', 'Branch cost per new card, weighted by cards', 'AMD', 'SUMPRODUCT({m}*$D${branch}:$K${branch}*$D${act}:$K${act})/{t}{act}', 0),
]
for key, label, unit, tpl, is_pct in TIERROWS:
    r += 1; R[key] = r
    cc.t(f'B{r}', label, S['cc_lbl']); cc.t(f'C{r}', unit, S['cc_lbl'])
    for tc in TCOLS:
        cc.f(f'{tc}{r}', tpl.format(t=tc, m=tsel(tc), **R), S['cc_pct'] if is_pct else S['cc_num'])
r += 1; R['fxseg'] = r
cc.t(f'B{r}', "Share of the segment's market FX revenue per card (Free / Black split 'Fast Black' by FX interest per card)", S['cc_lbl'])
cc.t(f'C{r}', '%', S['cc_lbl'])
cc.f(f'N{r}', '$K$94/SUM($K$94,$G$94,$D$94)', S['cc_pct'])
cc.f(f'O{r}', 'SUM($D$94,$G$94)/SUM($K$94,$G$94,$D$94)', S['cc_pct'])
cc.n(f'P{r}', 1, S['asm_pct']); cc.n(f'Q{r}', 1, S['asm_pct'])
r += 1; R['seg'] = r
cc.t(f'B{r}', "Market segment used for growth ('Market benchmarking')", S['cc_lbl'])
for tc, txt in zip(TCOLS, ['Fast Black', 'Fast Black', 'Fast Premium', 'Fast Signature']):
    cc.t(f'{tc}{r}', txt, S['cc_lbl'])
r += 2
cc.t(f'B{r}', 'Notes: ArCa Classic is AMD-only and domestic (no FX balances, no payments abroad). Visa Infinite Metal may hold FX '
     'accounts under the tariff but shows no FX balances in Q4-25, so it adds no FX weight. Deposit balances come from Extract_client_DB '
     '(sum Aug-25 to Aug-26 / 13 months); a client holding two card types is counted under each.', S['ital'])
MAPEND = r

# widen tier columns N:Q
cols = cc.root.find(N + 'cols')
for col in list(cols):
    if int(col.get('min')) >= 14:
        cols.remove(col)
e = etree.SubElement(cols, N + 'col'); e.set('min', '14'); e.set('max', '17'); e.set('width', '16'); e.set('customWidth', '1')
cc.root.find(N + 'dimension').set('ref', f'B1:R{MAPEND}')
cc.save()


def mp(key, tier='free', absolute=True):
    """Reference to a tier value in the mapping (Free column; clone_formula shifts N -> O/P/Q)."""
    col = MAPCOL[tier]
    return f"{CC}!${col}${R[key]}" if absolute else f"{CC}!{col}{R[key]}"


# ================================================================== 2. 'Economics Sept26 Upd'
ec = Sheet(EC_XML)
QCOLS = list('EFGH')                       # Q1..Q4 2027
YCOLS = list('IJK')                        # 2027, 2028, 2029
ALL = ['D'] + QCOLS + YCOLS
CPD = lambda row: f"{CP}!$D${row}"         # Free's Control panel parameter
free_changes = []


def fset(ref, formula, s=None, note=None):
    old = ec.formula(ref)
    c = ec.get(ref)
    if s is None and c is not None:
        s = c.get('s')
    ec.f(ref, formula, s)
    if note:
        free_changes.append((ref, old, formula, note))


# ---- 2a. Fast Free fixes and mapping links (row numbers are the Free block's)
fset('D19', mp('intl_sh'), note='actual intl share from tier mapping (same value)')
for c in ['D'] + QCOLS + YCOLS:
    fset(f'D18' if c == 'D' else f'{c}18', f"1.5%*{c}19+{mp('icm_t')}*(1-{c}19)", note='local interchange from tier mapping (same value for Free)' if c == 'D' else None)
for c in QCOLS + YCOLS:
    fset(f'{c}19', f"(1-{mp('arca_nc')})*{c}23", note='intl share = FX-capable weight x row 23 assumption' if c == 'E' else None)
# row 23: international share on FX-capable cards (Free's former row-19 assumptions move here)
ec.t('B23', 'Share of international payments on FX-capable cards (assumption)', None); ec.t('C23', '%', None)
ec.f('D23', mp('intl_cap'), S['lnk_pct'])
ec.n('E23', 0.15, S['asm_pct']); ec.f('F23', 'E23+1%', S['asm_pct']); ec.f('G23', 'AVERAGE(F23,H23)', S['asm_pct'])
ec.n('H23', 0.15, S['asm_pct']); ec.f('I23', 'AVERAGE(E23:H23)', S['pct']); ec.n('J23', 0.15, S['asm_pct']); ec.n('K23', 0.15, S['asm_pct'])
free_changes.append(('B23:K23', None, 'new row', "international share on FX-capable cards; Free's former E19:K19 values (15% / +1% / 15%)"))
fset('E20', 'E21*3', note='was H21*3 (Q1 used the Q4 volume)')
fset('D21', mp('nc_pc'), note='non-cash = local + international (was local only, K47/K8)')
fset('D22', mp('trx_pc'), note='from tier mapping (same value)')
for c, nxt in zip(['E', 'F', 'G'], ['F', 'G', 'H']):
    fset(f'{c}29', f'{nxt}29-($H$29-$D$29)/4', note='interpolation used row 21 deltas' if c != 'E' else None)
    fset(f'{c}34', f'{nxt}34-($H$34-$D$34)/4', note='interpolation used row 21 / 29 deltas')
    fset(f'{c}47', f'{nxt}47-($H$47-$D$47)/4', note='interpolation used row 21 / 29 deltas')
fset('D27', mp('arca_cash'), note='ArCa share of cashout from tier mapping (0 for Free)')
fset('D29', mp('cash_pc'), note='from tier mapping (same value)')
fset('D34', mp('c2c_pc'), note='from tier mapping (same value)')
fset('D38', mp('fx_pc'), note='from tier mapping (same value)')
for c in ['F', 'G', 'H', 'J', 'K']:
    old = ec.formula(f'{c}38')
    new = old.replace(f"{CC}!$K$94/SUM({CC}!$K$94,{CC}!$G$94,{CC}!$D$94)", mp('fxseg'))
    assert new != old, (c, old)
    fset(f'{c}38', new, note='segment share from tier mapping (same value)' if c == 'F' else None)
fset('D47', mp('bal_pc'), note='from tier mapping (same value)')
fset('D48', mp('fxbal_sh'), note='from tier mapping (same value)')
for c in QCOLS + YCOLS:
    fset(f'{c}48', f"(1-{mp('arca_bal')})*{c}49", note='FX-balance share = FX-capable weight x row 49 assumption' if c == 'E' else None)
ec.t('B49', 'Share of FX balance on FX-capable cards (assumption)', None); ec.t('C49', '%', None)
ec.f('D49', mp('fxbal_cap'), S['lnk_pct'])
ec.n('E49', 0.15, S['asm_pct'])
for p, c in zip('EFGHIJ', 'FGHIJK'):
    ec.f(f'{c}49', f'{p}49', S['asm_pct'])
free_changes.append(('B49:K49', None, 'new row', "FX-balance share on FX-capable cards; Free's former 15% flat"))
fset('D51', mp('dep_pc'), note='from tier mapping (same value)')
for c in QCOLS + YCOLS:
    fset(f'{c}13', f'{c}14*{c}15*' + ('3' if c in QCOLS else '12'), note='annual service fee x12 (was x3)' if c == 'I' else None)
for c in ['F', 'G', 'H'] + YCOLS:
    fset(f'{c}15', f"{CPD(22)}", note='share of paid cards linked (was hard-coded 0)' if c == 'F' else None)
# cashback: the cap trims cost. Capped clients spend S (row 59) a month; each is paid the cap instead
# of rate x S, so the saving is share x max(0, rate x S - cap) per month. Row 54 checks feasibility.
cap, rate = CPD(20), CPD(19)
ec.t('B54', "Check: capped clients' share of non-cash volume (keep well below 100%)", None); ec.t('C54', '%', None)
ec.t('B55', 'Cashback for the period (rate x non-cash, less the saving from the cap)', ec.get('B55').get('s') if ec.get('B55') is not None else None)
ec.t('B57', 'Share of capped clients (assumption)', None)
ec.t('B58', 'Cashback saved by the cap', None); ec.t('C58', 'AMD', None)
ec.t('B59', 'Monthly spend of a capped client (default: 2x the spend at which the cap starts)', None); ec.t('C59', 'AMD', None)
for c in QCOLS + YCOLS:
    months = '3' if c in QCOLS else '12'
    ec.f(f'{c}59', f'IFERROR(2*{cap}/{rate},0)', S['asm_num'])
    ec.f(f'{c}54', f'IFERROR({c}57*{c}59*{months}/{c}20,0)', S['pct'])
    if c == 'I':
        fset('I58', 'SUM(E58:H58)', S['num'], note='annual saving = sum of quarters')
        fset('I55', 'SUM(E55:H55)', note='was SUM(G55:H55)')
    else:
        fset(f'{c}58', f"IF({c}56>0,{c}57*MAX(0,{c}56*{c}59-{cap})*{months},0)", S['num'],
             note='cap saving (was: capped clients paid the cap on top)' if c == 'E' else None)
        fset(f'{c}55', f'MAX(0,{c}56*{c}20-{c}58)', note='cashback = rate x non-cash - cap saving, every period' if c == 'E' else None)
free_changes.append(('B54:K54, B59:K59', None, 'new rows', 'capped-client spend (assumption) and feasibility check'))
for c in ALL:
    vol = f'({c}20+{c}28+{c}33)'
    fset(f'{c}64', f"{vol}*{CC}!$D$106", note='ArCa rate from Current cards D106 (was Economics L132, overwritten by the Black rebuild)' if c == 'E' else None)
    fset(f'{c}65', f"{vol}*(1-{mp('arca_proc')})*{CC}!$E$103", note='Visa/MC fee only on non-ArCa volume' if c == 'D' else None)
for c in QCOLS + ['I']:
    fset(f'{c}70', mp('branch_t'), note='branch cost of the tier (excluded from the total, as before)' if c == 'E' else None)
    fset(f'{c}72', f"(1-{CPD(14)})*((1-{CPD(15)})*{mp('plastic_t')}+{CPD(15)}*{CC}!$J$109)", note='plastic / metal by Control panel shares' if c == 'E' else None)
    fset(f'{c}73', f"(1-{CPD(14)})*{CC}!$D$111", note='delivery x (1 - virtual share)' if c == 'E' else None)
    fset(f'{c}74', f"(1-{CPD(14)})*{CC}!$D$110", note='embossing x (1 - virtual share)' if c == 'E' else None)
    fset(f'{c}75', f"(1-{CPD(14)})*{CC}!$D$112", note='ATM activation x (1 - virtual share)' if c == 'E' else None)
# summary: service fee and perks lines
ec.t('N15', ' - service fee', None)
for c, src in zip('OPQ', 'IJK'):
    ec.f(f'{c}15', f'{src}13', S['num'])
ec.f('R15', 'SUM(O15:Q15)', S['num'])
ec.t('N21', ' - perks', None)
for c in 'OPQ':
    ec.n(f'{c}21', 0, S['num'])
ec.f('R21', 'SUM(O21:Q21)', S['num'])
for c in 'OPQ':
    fset(f'{c}9', f'SUM({c}10:{c}15)', note='total revenue includes the service fee line' if c == 'O' else None)
    fset(f'{c}16', f'SUM({c}17:{c}21)', note='total costs include the perks line' if c == 'O' else None)
free_changes.append(('N15:R15, N21:R21', None, 'new lines', 'service fee (revenue) and perks (cost) lines in the per-card summary'))

# ---- 2b. clear the old Black / Premium / Elite blocks (columns A:R, rows 76+), keep side calcs in W:Y
for rnum, row in list(ec.rows.items()):
    if rnum >= 76:
        for c in list(row):
            if colnum(c.get('r')) <= 18:
                row.remove(c)
        for a in ('hidden', 'ht', 'customHeight', 'outlineLevel', 'collapsed', 's', 'customFormat'):
            row.attrib.pop(a, None)

# ---- 2c. clone Free into the three tiers
TITLE = dict(black='Fast Black (ArCa Classic, Visa Classic)', premium='Fast Premium (Mastercard World, Visa Gold)',
             elite='Fast Elite (Mastercard World Elite, Visa Infinite, Visa Infinite Metal)')
free_rows = {rn: ec.rows[rn] for rn in range(FREE0, FREE1 + 1) if rn in ec.rows}
for tier in ['black', 'premium', 'elite']:
    off = OFF[tier]
    for rn, src_row in free_rows.items():
        dst = ec.row(rn + off)
        for a, v in src_row.attrib.items():
            if a not in ('r', 'spans'):
                dst.set(a, v)
        for c in src_row:
            col = re.match(r'[A-Z]+', c.get('r')).group(0)
            k = column_index_from_string(col)
            if col == 'L' or k > 18:                      # skip to-do notes (L) and anything right of R
                continue
            if col == 'N' and not (8 <= rn <= 22):        # skip loose notes in N outside the summary
                continue
            if col in 'OPQR' and not (8 <= rn <= 22):
                continue
            nc = copy.deepcopy(c)
            nc.set('r', f'{col}{rn + off}')
            f = nc.find(N + 'f')
            if f is not None:
                if f.get('t') == 'array':                 # the deposit-rate spill stays in Free; linked below
                    for a in ('t', 'ref'):
                        f.attrib.pop(a, None)
                    nc.attrib.pop('cm', None)
                f.text = clone_formula(f.text, tier)
            existing = ec.get(f'{col}{rn + off}')
            if existing is not None:
                existing.getparent().remove(existing)
            ec.cell(f'{col}{rn + off}')                   # position placeholder
            ph = ec.get(f'{col}{rn + off}')
            ph.getparent().replace(ph, nc)
    o = lambda row: row + off                          # noqa: E731
    ec.t(f'F{o(7)}', TITLE[tier], ec.get('F7').get('s'))
    # tier-specific assumptions
    tgt_intl = dict(black=0.15, premium=0.20, elite=0.40)[tier]
    for c in ['E', 'H', 'J', 'K']:
        ec.n(f'{c}{o(23)}', tgt_intl, S['asm_pct'])
    if tier == 'elite':
        ec.f(f'E{o(49)}', f'D{o(49)}', S['asm_pct'])     # hold today's FX-balance share (28%)
    else:
        ec.n(f'E{o(49)}', dict(black=0.15, premium=0.20)[tier], S['asm_pct'])
    # other-ATM share: today's actual, held flat
    ec.f(f'D{o(26)}', clone_formula(mp('oth_sh'), tier), S['lnk_pct'])
    for p, c in zip('DEFG', 'EFGH'):
        ec.f(f'{c}{o(26)}', f'{p}{o(26)}', S['asm_pct'])
    ec.f(f'I{o(26)}', f'AVERAGE(E{o(26)}:H{o(26)})', S['pct'])
    ec.f(f'J{o(26)}', f'I{o(26)}', S['asm_pct']); ec.f(f'K{o(26)}', f'J{o(26)}', S['asm_pct'])
    # capped clients: ~10% of the tier's spend at the default capped-client spend (Free keeps Alex's 2-5%)
    ec.n(f'E{o(57)}', dict(black=0.0025, premium=0.0015, elite=0.004)[tier], S['asm_pct'])
    ec.f(f'F{o(57)}', f'E{o(57)}', S['asm_pct']); ec.f(f'G{o(57)}', f'F{o(57)}', S['asm_pct'])
    # deposit rates: link to Free's projection (the spill array lives in Free)
    ec.f(f'D{o(52)}', '$D$52', S['lnk_pct'])
    for c in QCOLS + YCOLS:
        ec.f(f'{c}{o(52)}', f'{c}$52', S['lnk_pct'])
    ec.f(f'D{o(53)}', f'D{o(52)}', S['pct'])
    # recurring branch OPEX reference (excluded from the total, as in Free)
    ec.f(f'D{o(62)}', f"{CC}!$D$130*3", ec.get(f'D{o(62)}').get('s') if ec.get(f'D{o(62)}') is not None else S['num'])

# Elite perks (kept from v6; full years now that launch is Q1 2027)
pr = OFF['elite'] + 77          # 296
ec.t(f'B{pr}', 'Additional perks (per card per year)', 870)
for c in YCOLS:
    ec.f(f'{c}{pr}', f'{c}{pr + 1}+{c}{pr + 2}', 870)
ec.t(f'B{pr + 1}', 'VISA card perks (concierge, lounges)', None); ec.t(f'C{pr + 1}', 'AMD', None)
ec.t(f'B{pr + 2}', '2 free taxi rides per month (50% utilization)', None); ec.t(f'C{pr + 2}', 'AMD', None)
for c in YCOLS:
    ec.n(f'{c}{pr + 1}', 20000, S['asm_num'])
    ec.f(f'{c}{pr + 2}', '2500*2*12*50%', S['asm_num'])
e21 = 21 + OFF['elite']
for c, src in zip('OPQ', 'IJK'):
    ec.f(f'{c}{e21}', f'{src}{pr}', S['num'])

# side calc in W88:Y92 pointed at the old per-tier fee lines; repoint to 2027 fee income per card
for x, tier in zip(['X89', 'X90', 'X91'], ['black', 'premium', 'elite']):
    if ec.get(x) is not None:
        ec.f(x, f'I{10 + OFF[tier]}', ec.get(x).get('s'))

ec.root.find(N + 'dimension').set('ref', f'B1:AA{pr + 2}')
ec.save()

# ================================================================== 3. Control panel outputs
cp = Sheet(CP_XML)
for k, tier in enumerate(TIERS):
    base = 5 + 20 * k
    for c in 'IJK':
        cp.f(f'{c}{base}', f"{EC}!{chr(ord(c) + 6)}$8", cp.get(f'{c}5').get('s'))   # I->O, J->P, K->Q
    if tier == 'free':
        continue
    for rr in range(base + 1, base + 18):
        for c in 'HIJKL':
            cp.clear(f'{c}{rr}')
    for rr in range(6, 20):
        for c in 'HIJKL':
            src = cp.get(f'{c}{rr}')
            if src is None:
                continue
            nc = copy.deepcopy(src); nc.set('r', f'{c}{rr + 20 * k}')
            f = nc.find(N + 'f')
            if f is not None:
                f.text = rewrite(f.text, lambda sn, ca, col, ra, row: (col, row + OFF[tier]) if sn == 'Economics Sept26 Upd' and 8 <= row <= 22 else (col, row))
            cp.cell(f'{c}{rr + 20 * k}')
            ph = cp.get(f'{c}{rr + 20 * k}')
            ph.getparent().replace(ph, nc)
# Free output rows 12 and 18 were blank; wire service fee and perks for all four tables
for k, tier in enumerate(TIERS):
    for rr, er in ((12, 15), (18, 21)):
        row_cp, row_ec = rr + 20 * k, er + OFF[tier]
        cp.f(f'H{row_cp}', f"{EC}!N{row_ec}", cp.get('H11').get('s'))
        for c, ecol in zip('IJKL', 'OPQR'):
            cp.f(f'{c}{row_cp}', f"{EC}!{ecol}{row_ec}", cp.get('I11').get('s'))
cp.save()

# ================================================================== 4. new tab: PnL all tiers
pn_root = etree.fromstring(
    f'<worksheet xmlns="{M}" xmlns:r="{RNS}"><sheetPr><tabColor theme="5"/></sheetPr><dimension ref="B2:J100"/>'
    '<sheetViews><sheetView showGridLines="0" workbookViewId="0"><pane xSplit="3" ySplit="4" topLeftCell="D5" activePane="bottomRight" state="frozen"/>'
    '<selection pane="bottomRight" activeCell="E6" sqref="E6"/></sheetView></sheetViews>'
    '<sheetFormatPr baseColWidth="10" defaultRowHeight="16"/>'
    '<cols><col min="1" max="1" width="3" customWidth="1"/><col min="2" max="2" width="58" customWidth="1"/>'
    '<col min="3" max="3" width="9" customWidth="1"/><col min="4" max="8" width="14" customWidth="1"/>'
    '<col min="9" max="9" width="3" customWidth="1"/><col min="10" max="10" width="90" customWidth="1"/></cols>'
    '<sheetData/><pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/></worksheet>')
parts[PNL_XML] = etree.tostring(pn_root, xml_declaration=True, encoding='UTF-8', standalone=True)
pn = Sheet(PNL_XML)
YR = dict(D='2026', E='2027', F='2028', G='2029')
ECOL = dict(E='O', F='P', G='Q')          # per-card summary columns in Economics
EYC = dict(E='I', F='J', G='K')           # annual block columns in Economics
TL = [('free', 'Fast Free'), ('black', 'Fast Black'), ('premium', 'Fast Premium'), ('elite', 'Fast Elite')]


def hdr(r, title, unit, years=('E', 'F', 'G'), total='3Y total', first=None):
    pn.t(f'B{r}', title, S['hdr']); pn.t(f'C{r}', unit, S['hdr'])
    for c in 'DEFGH':
        pn.t(f'{c}{r}', '', S['hdr_y'])
    if first:
        pn.t(f'D{r}', first, S['hdr_y'])
    for c in years:
        pn.t(f'{c}{r}', YR[c], S['hdr_y'])
    if total:
        pn.t(f'H{r}', total, S['hdr_y'])


pn.t('B2', 'DEBIT CARDS P&L - FOUR TIERS COMBINED', S['title'])
pn.t('B3', "AMD mn unless stated. Per-card economics from 'Economics Sept26 Upd' (per-card summary, cols O-Q) x card volumes in section 1. "
     "Inputs live on 'Control panel'; orange cells here are editable.", S['ital'])

r = 5
hdr(r, '1. CARD VOLUMES', 'Unit', years=('D', 'E', 'F', 'G'), total='3Y total')
r = 6; ROW = {}
pn.t(f'B{r}', 'Activated cards, end of year (plan)', S['txt']); pn.t(f'C{r}', 'pcs', S['txt'])
for c, src in zip('DEF', 'JKL'):
    pn.f(f'{c}{r}', f"'Planned KPIs'!{src}7", S['lnk_num'])
pn.f(f'G{r}', f'F{r}*F{r}/E{r}', S['asm_num'])
pn.t(f'J{r}', "'Planned KPIs' row 7 (H21 bank financial model 2026-2030). 2029 = 2028 x (2028 / 2027 growth).", S['ital'])
ROW['act_plan'] = r
r = 7
pn.t(f'B{r}', 'New cards sold (plan)', S['txt']); pn.t(f'C{r}', 'pcs', S['txt'])
for c, src in zip('DEF', 'JKL'):
    pn.f(f'{c}{r}', f"'Planned KPIs'!{src}12", S['lnk_num'])
pn.f(f'G{r}', f'F{r}*F{r}/E{r}', S['asm_num'])
pn.f(f'H{r}', f'SUM(E{r}:G{r})', S['num'])
pn.t(f'J{r}', "'Planned KPIs' row 12. 2029 extrapolated the same way.", S['ital'])
ROW['sales_plan'] = r

r = 9
pn.t(f'B{r}', 'Tier mix (share of active cards and of new sales)', S['txt_b']); pn.t(f'C{r}', '%', S['txt_b'])
pn.t(f'D{r}', 'Today (Q4-25)', S['hdr_sub'])
for c in 'EFG':
    pn.t(f'{c}{r}', YR[c], S['hdr_sub'])
MIX = {}
for i, (tier, name) in enumerate(TL):
    r = 10 + i; MIX[tier] = r
    pn.t(f'B{r}', name, S['txt']); pn.t(f'C{r}', '%', S['txt'])
    tc = MAPCOL[tier]
    pn.f(f'D{r}', f"{CC}!{tc}{R['act']}/SUM({CC}!$N${R['act']}:$Q${R['act']})", S['lnk_pct'])
    pn.f(f'E{r}', f'$D{r}', S['asm_pct']); pn.f(f'F{r}', f'E{r}', S['asm_pct']); pn.f(f'G{r}', f'F{r}', S['asm_pct'])
r = 14
pn.t(f'B{r}', 'Total (should be 100%)', S['txt_b']); pn.t(f'C{r}', '%', S['txt'])
for c in 'DEFG':
    pn.f(f'{c}{r}', f'SUM({c}10:{c}13)', S['pct'])
pn.t('J10', "Today = activated cards by new tier ('Current cards' tier mapping). Overwrite E:G to change the mix by year.", S['ital'])

END, AVG, NEW = {}, {}, {}
r = 16
pn.t(f'B{r}', 'Active cards, end of year', S['txt_b']); pn.t(f'C{r}', 'pcs', S['txt_b'])
for i, (tier, name) in enumerate(TL):
    r = 17 + i; END[tier] = r
    pn.t(f'B{r}', name, S['txt']); pn.t(f'C{r}', 'pcs', S['txt'])
    for c in 'DEFG':
        pn.f(f'{c}{r}', f'{c}${ROW["act_plan"]}*{c}{MIX[tier]}', S['num'])
r = 21
pn.t(f'B{r}', 'Total', S['txt_b'])
for c in 'DEFG':
    pn.f(f'{c}{r}', f'SUM({c}17:{c}20)', S['num_b'])
ROW['end_tot'] = r

r = 23
pn.t(f'B{r}', 'Average active cards', S['txt_b']); pn.t(f'C{r}', 'pcs', S['txt_b'])
pn.t(f'J{r}', 'Average of opening and closing active cards; 3Y total = card-years.', S['ital'])
for i, (tier, name) in enumerate(TL):
    r = 24 + i; AVG[tier] = r
    pn.t(f'B{r}', name, S['txt']); pn.t(f'C{r}', 'pcs', S['txt'])
    for p, c in zip('DEF', 'EFG'):
        pn.f(f'{c}{r}', f'AVERAGE({p}{END[tier]},{c}{END[tier]})', S['num'])
    pn.f(f'H{r}', f'SUM(E{r}:G{r})', S['num'])
r = 28
pn.t(f'B{r}', 'Total', S['txt_b'])
for c in 'EFGH':
    pn.f(f'{c}{r}', f'SUM({c}24:{c}27)', S['num_b'])
ROW['avg_tot'] = r

r = 30
pn.t(f'B{r}', 'New cards sold', S['txt_b']); pn.t(f'C{r}', 'pcs', S['txt_b'])
pn.t(f'J{r}', 'Sales split by the same tier mix.', S['ital'])
for i, (tier, name) in enumerate(TL):
    r = 31 + i; NEW[tier] = r
    pn.t(f'B{r}', name, S['txt']); pn.t(f'C{r}', 'pcs', S['txt'])
    for c in 'EFG':
        pn.f(f'{c}{r}', f'{c}${ROW["sales_plan"]}*{c}{MIX[tier]}', S['num'])
    pn.f(f'H{r}', f'SUM(E{r}:G{r})', S['num'])
r = 35
pn.t(f'B{r}', 'Total', S['txt_b'])
for c in 'EFGH':
    pn.f(f'{c}{r}', f'SUM({c}31:{c}34)', S['num_b'])
ROW['new_tot'] = r


def per_card_sum(c, ec_row, weight='avg'):
    """sum over tiers of cards x per-card value in Economics summary row (Free row number), in AMD mn."""
    terms = []
    for tier, _ in TL:
        w = AVG[tier] if weight == 'avg' else NEW[tier]
        terms.append(f"{c}{w}*{EC}!{ECOL[c]}{ec_row + OFF[tier]}")
    return '(' + '+'.join(terms) + ')/10^6'


r = 37
hdr(r, '2. COMBINED P&L', 'AMD mn')
PL = {}
lines = [
    ('rev', 'Total revenue', None, True),
    ('int', ' - interest income on card balances', 10, False),
    ('icf', ' - interchange', 11, False),
    ('cash', ' - cashout fees', 12, False),
    ('c2c', ' - transfer fees', 13, False),
    ('fx', ' - FX conversion', 14, False),
    ('fee', ' - service fees', 15, False),
    ('cost', 'Total costs', None, True),
    ('cb', ' - cashback', 18, False),
    ('up', ' - deposit-rate uplift', 17, False),
    ('perk', ' - perks', 21, False),
    ('rop', ' - recurring OPEX', 19, False),
    ('fyo', ' - first-year OPEX on new cards (acquisition)', 20, False),
    ('op', 'Operating profit', None, True),
    ('opm', 'Operating margin', None, False),
]
for key, label, er, bold in lines:
    r += 1; PL[key] = r
    pn.t(f'B{r}', label, S['txt_b'] if bold else S['txt'])
    pn.t(f'C{r}', '%' if key == 'opm' else 'AMD mn', S['txt'])
for c in 'EFG':
    for key, label, er, bold in lines:
        rr = PL[key]
        if key == 'rev':
            fml = f'SUM({c}{PL["int"]}:{c}{PL["fee"]})'
        elif key == 'cost':
            fml = f'SUM({c}{PL["cb"]}:{c}{PL["fyo"]})'
        elif key == 'op':
            fml = f'{c}{PL["rev"]}-{c}{PL["cost"]}'
        elif key == 'opm':
            fml = f'IFERROR({c}{PL["op"]}/{c}{PL["rev"]},0)'
        elif key == 'fyo':      # first-year OPEX per new card = Economics I69 (block annual column, 2027 values)
            fml = '(' + '+'.join(f"{c}{NEW[t]}*{EC}!$I${69 + OFF[t]}" for t, _ in TL) + ')/10^6'
        else:
            fml = per_card_sum(c, er)
        pn.f(f'{c}{rr}', fml, S['pct'] if key == 'opm' else (S['num1_b'] if bold else S['num1']))
for key, *_ in lines:
    rr = PL[key]
    if key == 'opm':
        pn.f(f'H{rr}', f'IFERROR(H{PL["op"]}/H{PL["rev"]},0)', S['pct'])
    else:
        pn.f(f'H{rr}', f'SUM(E{rr}:G{rr})', S['num1_b'] if key in ('rev', 'cost', 'op') else S['num1'])
pn.t(f'J{PL["fyo"]}', "New cards x first-year OPEX per card ('Economics Sept26 Upd' I69 / I142 / I215 / I288: marketing, plastic, delivery, embossing, ATM activation).", S['ital'])
pn.t(f'J{PL["rev"]}', 'Average active cards x per-card revenue of that year.', S['ital'])
pn.t(f'J{PL["perk"]}', 'Elite only: Visa perks and taxi rides.', S['ital'])

r = PL['opm'] + 2
hdr(r, '3. BY TIER', 'AMD mn')
BT = {}
blocks = [('rev', 'Total revenue'), ('cost', 'Total costs (incl. first-year OPEX)'), ('op', 'Operating profit'), ('opm', 'Operating margin')]
for key, label in blocks:
    r += 1
    pn.t(f'B{r}', label, S['txt_b']); pn.t(f'C{r}', '%' if key == 'opm' else 'AMD mn', S['txt_b'])
    for tier, name in TL:
        r += 1; BT[(key, tier)] = r
        pn.t(f'B{r}', name, S['txt']); pn.t(f'C{r}', '%' if key == 'opm' else 'AMD mn', S['txt'])
    r += 1; BT[(key, 'total')] = r
    pn.t(f'B{r}', 'Total', S['txt_b'])
for c in 'EFG':
    for tier, _ in TL:
        o = OFF[tier]
        pn.f(f'{c}{BT[("rev", tier)]}', f"{c}{AVG[tier]}*{EC}!{ECOL[c]}{9 + o}/10^6", S['num1'])
        pn.f(f'{c}{BT[("cost", tier)]}', f"({c}{AVG[tier]}*({EC}!{ECOL[c]}{16 + o}-{EC}!{ECOL[c]}{20 + o})+{c}{NEW[tier]}*{EC}!$I${69 + o})/10^6", S['num1'])
        pn.f(f'{c}{BT[("op", tier)]}', f'{c}{BT[("rev", tier)]}-{c}{BT[("cost", tier)]}', S['num1'])
        pn.f(f'{c}{BT[("opm", tier)]}', f'IFERROR({c}{BT[("op", tier)]}/{c}{BT[("rev", tier)]},0)', S['pct'])
for key, _ in blocks:
    for tier in [t for t, _ in TL] + ['total']:
        rr = BT[(key, tier)]
        if tier == 'total':
            for c in 'EFGH':
                if key == 'opm':
                    pn.f(f'{c}{rr}', f'IFERROR({c}{BT[("op", "total")]}/{c}{BT[("rev", "total")]},0)', S['pct'])
                else:
                    first, last = BT[(key, 'free')], BT[(key, 'elite')]
                    pn.f(f'{c}{rr}', f'SUM({c}{first}:{c}{last})', S['num1_b'])
        elif key == 'opm':
            pn.f(f'H{rr}', f'IFERROR(H{BT[("op", tier)]}/H{BT[("rev", tier)]},0)', S['pct'])
        else:
            pn.f(f'H{rr}', f'SUM(E{rr}:G{rr})', S['num1'])
pn.t(f'J{BT[("op", "total")]}', 'Ties to the combined operating profit in section 2.', S['ital'])

r = BT[('opm', 'total')] + 2
hdr(r, '4. KEY METRICS', 'Unit')
KM = {}
metrics = [
    ('cards', 'Average active cards', 'pcs'),
    ('new', 'New cards sold', 'pcs'),
    ('rev_pc', 'Revenue per average active card', 'AMD'),
    ('cost_pc', 'Total costs per average active card', 'AMD'),
    ('op_pc', 'Operating profit per average active card', 'AMD'),
    ('cti', 'Cost-to-income ratio', '%'),
    ('fee_sh', 'Fee and commission income, share of revenue', '%'),
    ('int_sh', 'Interest income, share of revenue', '%'),
    ('cb_sh', 'Cashback, share of revenue', '%'),
    ('nc', 'Non-cash payment volume', 'AMD bn'),
    ('cb_eff', 'Effective cashback rate on non-cash volume', '%'),
    ('bal', 'Average card balances', 'AMD mn'),
    ('acq', 'First-year OPEX per new card (weighted)', 'AMD'),
]
for key, label, unit in metrics:
    r += 1; KM[key] = r
    pn.t(f'B{r}', label, S['txt']); pn.t(f'C{r}', unit, S['txt'])
for c in 'EFGH':
    pct = S['pct']
    pn.f(f'{c}{KM["cards"]}', f'{c}{ROW["avg_tot"]}', S['num'])
    pn.f(f'{c}{KM["new"]}', f'{c}{ROW["new_tot"]}', S['num'])
    pn.f(f'{c}{KM["rev_pc"]}', f'IFERROR({c}{PL["rev"]}*10^6/{c}{KM["cards"]},0)', S['num'])
    pn.f(f'{c}{KM["cost_pc"]}', f'IFERROR({c}{PL["cost"]}*10^6/{c}{KM["cards"]},0)', S['num'])
    pn.f(f'{c}{KM["op_pc"]}', f'IFERROR({c}{PL["op"]}*10^6/{c}{KM["cards"]},0)', S['num'])
    pn.f(f'{c}{KM["cti"]}', f'IFERROR({c}{PL["cost"]}/{c}{PL["rev"]},0)', pct)
    pn.f(f'{c}{KM["fee_sh"]}', f'IFERROR(SUM({c}{PL["icf"]}:{c}{PL["fee"]})/{c}{PL["rev"]},0)', pct)
    pn.f(f'{c}{KM["int_sh"]}', f'IFERROR({c}{PL["int"]}/{c}{PL["rev"]},0)', pct)
    pn.f(f'{c}{KM["cb_sh"]}', f'IFERROR({c}{PL["cb"]}/{c}{PL["rev"]},0)', pct)
    if c == 'H':
        pn.f(f'H{KM["nc"]}', f'SUM(E{KM["nc"]}:G{KM["nc"]})', S['num1'])
        pn.f(f'H{KM["bal"]}', f'AVERAGE(E{KM["bal"]}:G{KM["bal"]})', S['num1'])
    else:
        pn.f(f'{c}{KM["nc"]}', '(' + '+'.join(f"{c}{AVG[t]}*{EC}!{EYC[c]}{20 + OFF[t]}" for t, _ in TL) + ')/10^9', S['num1'])
        pn.f(f'{c}{KM["bal"]}', '(' + '+'.join(f"{c}{AVG[t]}*{EC}!{EYC[c]}{47 + OFF[t]}" for t, _ in TL) + ')/10^6', S['num1'])
    pn.f(f'{c}{KM["cb_eff"]}', f'IFERROR({c}{PL["cb"]}/({c}{KM["nc"]}*1000),0)', pct)
    pn.f(f'{c}{KM["acq"]}', f'IFERROR({c}{PL["fyo"]}*10^6/{c}{KM["new"]},0)', S['num'])
pn.t(f'J{KM["fee_sh"]}', 'Interchange + cashout + transfer + FX + service fees.', S['ital'])
pn.t(f'J{KM["bal"]}', 'Average active cards x average balance per card (Economics row 47 / 120 / 193 / 266); 3Y = average of the years.', S['ital'])

r = KM['acq'] + 2
pn.t(f'B{r}', 'Operating profit per card by tier (first year carries acquisition cost)', S['txt_b']); pn.t(f'C{r}', 'AMD', S['txt_b'])
for c in 'EFG':
    pn.t(f'{c}{r}', YR[c], S['hdr_sub'])
pn.t(f'H{r}', '3Y LTV', S['hdr_sub'])
for tier, name in TL:
    r += 1
    pn.t(f'B{r}', name, S['txt']); pn.t(f'C{r}', 'AMD', S['txt'])
    for c in 'EFG':
        pn.f(f'{c}{r}', f"{EC}!{ECOL[c]}{22 + OFF[tier]}", S['lnk_num'])
    pn.f(f'H{r}', f"{EC}!R{22 + OFF[tier]}", S['lnk_num'])
pn.root.find(N + 'dimension').set('ref', f'B2:J{r}')
pn.save()

# ================================================================== 5. workbook plumbing
wb = etree.fromstring(parts['xl/workbook.xml'])
sheets = wb.find(N + 'sheets')
rels = etree.fromstring(parts['xl/_rels/workbook.xml.rels'])
rid = 'rId%d' % (max(int(x.get('Id')[3:]) for x in rels) + 1)
rel = etree.SubElement(rels, '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship')
rel.set('Id', rid); rel.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet'); rel.set('Target', 'worksheets/sheet35.xml')
new_sheet = etree.Element(N + 'sheet'); new_sheet.set('name', PNL_NAME)
new_sheet.set('sheetId', str(max(int(s.get('sheetId')) for s in sheets) + 1)); new_sheet.set('{%s}id' % RNS, rid)
cp_el = [s for s in sheets if s.get('name') == 'Control panel'][0]
cp_el.addnext(new_sheet)
# keep local sheet-scoped defined names pointing at the right sheet index (inserted after Control panel)
pos = list(sheets).index(new_sheet)
dn = wb.find(N + 'definedNames')
if dn is not None:
    for d in dn:
        if d.get('localSheetId') is not None and int(d.get('localSheetId')) >= pos:
            d.set('localSheetId', str(int(d.get('localSheetId')) + 1))
bv = wb.find(N + 'bookViews')
if bv is not None:
    for v in bv:
        if v.get('activeTab') and int(v.get('activeTab')) >= pos:
            v.set('activeTab', str(int(v.get('activeTab')) + 1))
        if v.get('firstSheet') and int(v.get('firstSheet')) >= pos:
            v.set('firstSheet', str(int(v.get('firstSheet')) + 1))
calc = wb.find(N + 'calcPr')
calc.set('fullCalcOnLoad', '1')
parts['xl/workbook.xml'] = etree.tostring(wb, xml_declaration=True, encoding='UTF-8', standalone=True)

# calcChain: drop it so Excel rebuilds
for x in list(rels):
    if 'calcChain' in x.get('Target'):
        rels.remove(x)
parts['xl/_rels/workbook.xml.rels'] = etree.tostring(rels, xml_declaration=True, encoding='UTF-8', standalone=True)
parts.pop('xl/calcChain.xml', None)

ct = etree.fromstring(parts['[Content_Types].xml'])
CTN = '{http://schemas.openxmlformats.org/package/2006/content-types}'
for o in list(ct):
    if o.get('PartName') == '/xl/calcChain.xml':
        ct.remove(o)
ov = etree.SubElement(ct, CTN + 'Override'); ov.set('PartName', '/' + PNL_XML)
ov.set('ContentType', 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
parts['[Content_Types].xml'] = etree.tostring(ct, xml_declaration=True, encoding='UTF-8', standalone=True)

app = parts['docProps/app.xml'].decode('utf-8')
app = re.sub(r'(<vt:lpstr>Worksheets</vt:lpstr></vt:variant><vt:variant><vt:i4>)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1), app)
app = re.sub(r'<TitlesOfParts><vt:vector size="(\d+)"', lambda m: f'<TitlesOfParts><vt:vector size="{int(m.group(1)) + 1}"', app)
app = app.replace('<vt:lpstr>Control panel</vt:lpstr>', f'<vt:lpstr>Control panel</vt:lpstr><vt:lpstr>{PNL_NAME}</vt:lpstr>', 1)
parts['docProps/app.xml'] = app.encode('utf-8')

parts['xl/styles.xml'] = etree.tostring(styles, xml_declaration=True, encoding='UTF-8', standalone=True)

order = [n for n in zin.namelist() if n in parts] + [n for n in parts if n not in zin.namelist()]
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in order:
        z.writestr(n, parts[n])

print('mapping rows', R)
print('Free changes:')
for ref, old, new, note in free_changes:
    print(f'  {ref}: {note}')
