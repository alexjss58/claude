"""Economics v3 -> v4: Control panel with four card tables wired to 'Economics Sept26 Upd'.

The workbook carries pivots, an image, threaded comments and dynamic-array metadata that openpyxl
would drop, so this edits only the two sheets' XML (plus styles/workbook calc flags) and leaves every
other part of the package untouched.

    python3 build_economics_v4.py <in.xlsx> <out.xlsx> <bench.json>
"""
import copy
import json
import re
import sys
import zipfile

import openpyxl
from lxml import etree
from openpyxl.formula.tokenizer import Tokenizer
from openpyxl.utils import column_index_from_string, get_column_letter

SRC, OUT, BENCH = sys.argv[1:4]
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
ECON, CPNL = 'xl/worksheets/sheet6.xml', 'xl/worksheets/sheet7.xml'
EC, CP, CC, MB, PC = "'Economics Sept26 Upd'", "'Control panel'", "'Current cards'", "'Market benchmarking'", "'Portfolios by cur'"
bench = json.load(open(BENCH))

zin = zipfile.ZipFile(SRC)
parts = {n: zin.read(n) for n in zin.namelist()}
wf = openpyxl.load_workbook(SRC)          # expanded (unshared) formula text


# ------------------------------------------------------------------ styles
styles = etree.fromstring(parts['xl/styles.xml'])
xfs = styles.find(N + 'cellXfs')


def xf_like(base, numfmt=None):
    x = copy.deepcopy(xfs[base])
    if numfmt is not None:
        x.set('numFmtId', str(numfmt)); x.set('applyNumberFormat', '1')
    xfs.append(x); xfs.set('count', str(len(xfs)))
    return len(xfs) - 1


S = dict(
    asm_pct=xf_like(904, 10), asm_amd=xf_like(904, 165), asm_txt=904,          # 'Assumption' look (inputs / placeholders)
    lnk_pct=xf_like(567, 10), lnk_amd=393, lnk_x=xf_like(567, 2),              # 'Link to other sheet' look
    cp_ref_pct=1089, cp_ref_amd=xf_like(875, 165), cp_ref_txt=875,
    cp_bm_pct=xf_like(862, 10), cp_bm_amd=xf_like(862, 165), cp_bm_txt=862,
    cp_lbl=1087, cp_hdr=1097, cp_hdr_d=1098, cp_hdr_bm=859, cp_hdr_out=934,
    cp_out_b=1091, cp_out_lbl_b=934, cp_out_lbl=1092, cp_note=0,
    lbl=0, lbl_b=870, num=386, pct=394, amd_b=877, sumlbl=0, sumnum=389, sumnum_b=514, sumlbl_b=388,
)


# ------------------------------------------------------------------ sheet editing helpers
def colnum(ref):
    return column_index_from_string(re.match(r'[A-Z]+', ref).group(0))


class Sheet:
    def __init__(self, part, title):
        self.part, self.title = part, title
        self.root = etree.fromstring(parts[part])
        self.data = self.root.find(N + 'sheetData')
        self.rows = {int(r.get('r')): r for r in self.data}
        self.ws = wf[title]
        # unshare every shared formula (so editing one cell never orphans its dependants)
        for c in self.data.iter(N + 'c'):
            f = c.find(N + 'f')
            if f is not None and f.get('t') == 'shared':
                txt = self.ws[c.get('r')].value
                c.remove(f)
                nf = etree.SubElement(c, N + 'f'); nf.text = txt[1:] if isinstance(txt, str) and txt.startswith('=') else str(txt)
                c.insert(0, nf)
                for v in c.findall(N + 'v'):
                    c.remove(v); c.append(v)

    def row(self, r):
        if r not in self.rows:
            el = etree.Element(N + 'row'); el.set('r', str(r))
            after = [k for k in self.rows if k < r]
            if after:
                self.rows[max(after)].addnext(el)
            else:
                self.data.insert(0, el)
            self.rows[r] = el
        el = self.rows[r]
        if 'spans' in el.attrib:
            del el.attrib['spans']
        return el

    def cell(self, ref):
        r = int(re.search(r'\d+', ref).group(0)); row = self.row(r)
        for c in row:
            if c.get('r') == ref:
                return c
        c = etree.Element(N + 'c'); c.set('r', ref)
        k = colnum(ref)
        for i, other in enumerate(row):
            if colnum(other.get('r')) > k:
                row.insert(i, c); break
        else:
            row.append(c)
        return c

    def _reset(self, c, s):
        for ch in list(c):
            c.remove(ch)
        if 't' in c.attrib:
            del c.attrib['t']
        if s is not None:
            c.set('s', str(s))

    def f(self, ref, formula, s=None):
        c = self.cell(ref); self._reset(c, s)
        etree.SubElement(c, N + 'f').text = formula.lstrip('=')

    def n(self, ref, value, s=None):
        c = self.cell(ref); self._reset(c, s)
        etree.SubElement(c, N + 'v').text = repr(float(value)) if not float(value).is_integer() else str(int(value))

    def t(self, ref, text, s=None):
        c = self.cell(ref); self._reset(c, s); c.set('t', 'inlineStr')
        is_ = etree.SubElement(c, N + 'is'); tt = etree.SubElement(is_, N + 't'); tt.text = text
        tt.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

    def blank(self, ref, s=None):
        c = self.cell(ref); self._reset(c, s)

    def drop(self, ref):
        r = int(re.search(r'\d+', ref).group(0))
        if r in self.rows:
            for c in self.rows[r]:
                if c.get('r') == ref:
                    self.rows[r].remove(c)

    def src(self, ref):
        """(formula-or-value, style, is_formula, is_text) of an existing cell, reading the unshared XML."""
        r = int(re.search(r'\d+', ref).group(0))
        for c in self.rows.get(r, []):
            if c.get('r') == ref:
                fe = c.find(N + 'f'); s = c.get('s')
                if fe is not None:
                    return fe.text, s, True, False
                if c.get('t') == 'inlineStr':
                    return ''.join(c.find(N + 'is').itertext()), s, False, True
                if c.get('t') == 's':
                    v = self.ws[ref].value
                    return v, s, False, True
                ve = c.find(N + 'v')
                if ve is None:
                    return None, s, False, False
                return float(ve.text), s, False, False
        return None, None, False, False

    def dimension(self, ref):
        d = self.root.find(N + 'dimension')
        if d is not None:
            d.set('ref', ref)

    def save(self):
        parts[self.part] = etree.tostring(self.root, xml_declaration=True, encoding='UTF-8', standalone=True)


def shift_rows(formula, dr):
    """Shift same-sheet relative row references by dr (cross-sheet references are left alone)."""
    tok = Tokenizer('=' + formula)
    out = []
    for t in tok.items:
        v = t.value
        if t.type == 'OPERAND' and t.subtype == 'RANGE' and '!' not in v:
            v = re.sub(r'(\$?[A-Z]{1,3})(\$?)(\d+)', lambda m: m.group(1) + m.group(2) + (m.group(3) if m.group(2) else str(int(m.group(3)) + dr)), v)
        out.append(v)
    return ''.join(out)


E = Sheet(ECON, 'Economics Sept26 Upd')
C = Sheet(CPNL, 'Control panel')

# ------------------------------------------------------------------ Control panel layout
TIERS = ['free', 'black', 'premium', 'elite']
BASE = {'free': 5, 'black': 20, 'premium': 35, 'elite': 50}
NAMES = {'free': 'FAST FREE CARD TERMS', 'black': 'FAST BLACK CARD TERMS', 'premium': 'FAST PREMIUM CARD TERMS', 'elite': 'FAST ELITE CARD TERMS'}
KEYS = ['fee', 'own', 'oth', 'c2c', 'amd', 'fxr', 'type', 'usd', 'eur', 'rub', 'cb', 'up']


def cp(tier, key, col='D'):
    return f"{CP}!${col}${BASE[tier] + 1 + KEYS.index(key)}"


def card_factor(tier):
    t = cp(tier, 'type')
    return f'IF({t}="Virtual",0,IF({t}="Metal",{CC}!$J$109/{CC}!$I$109,1))'


def fx_factor(tier):
    w = lambda cur: f'SUMIF({PC}!$B$94:$B$119,"{cur}",{PC}!$D$94:$D$119)'
    body = '+'.join(f"{w(cur)}*{cp(tier, k)}/{cp(tier, k, 'C')}" for cur, k in (('USD', 'usd'), ('EUR', 'eur'), ('RUB', 'rub')))
    return f"IFERROR(({body})/({w('USD')}+{w('EUR')}+{w('RUB')}),1)"


# ------------------------------------------------------------------ model blocks
BLK = {
    'black':   dict(fee=13, paid=14, atm=24, oshare=25, arca=26, c2c=31, fx=37, fxf=38, mb_fx=130, amd=42, fxm=43,
                    plastic=60, deliv=61, emb=62, act=63, cb=65, nc=19, fee_period=12,
                    sm=dict(tot=8, fee=9, int=10, fy=12, rec=13, net=15, cb=17, up=18, after=19)),
    'premium': dict(fee=82, paid=83, atm=93, oshare=94, arca=95, c2c=100, fx=106, fxf=107, mb_fx=131, amd=111, fxm=112,
                    plastic=129, deliv=130, emb=131, act=132, cb=134, nc=88, fee_period=81,
                    sm=dict(tot=77, fee=78, int=79, fy=81, rec=82, net=84, cb=86, up=87, after=88)),
    'elite':   dict(fee=157, paid=158, atm=168, oshare=169, arca=170, c2c=175, fx=181, fxf=182, mb_fx=132, amd=186, fxm=187,
                    plastic=204, deliv=205, emb=206, act=207, cb=209, nc=163, fee_period=156,
                    sm=dict(tot=152, fee=153, int=154, fy=156, rec=157, net=159, cb=161, up=162, after=163)),
}
OFF = 220                                   # Fast Free block = Fast Black rows 6-73 shifted to 226-293
BLK['free'] = {k: (v + OFF if isinstance(v, int) and k != 'mb_fx' else v) for k, v in BLK['black'].items() if k != 'sm'}
BLK['free']['mb_fx'] = 130
BLK['free']['sm'] = {k: v + OFF for k, v in BLK['black']['sm'].items()}

NEW = ['G', 'H', 'J', 'K']                  # quarters / years on the new line-up (launch Q3 2026)


def write_terms(tier):
    b = BLK[tier]; s = E
    # service fee per card per month (all blocks monthly; Black was per period, fixed here)
    for col in NEW:
        s.f(f'{col}{b["fee"]}', f"{cp(tier, 'fee')}/12", S['lnk_amd'])
    s.f(f'I{b["fee"]}', f'G{b["fee"]}', S['lnk_amd'])
    s.t(f'B{b["fee"]}', 'Service fee per card per month', S['lbl'])
    fp = b['fee_period']
    for col in ('G', 'H'):
        s.f(f'{col}{fp}', f'{col}{b["fee"]}*{col}{b["paid"]}*3')
    for col in ('J', 'K'):
        s.f(f'{col}{fp}', f'{col}{b["fee"]}*{col}{b["paid"]}*12')
    # cash-out margin: own-ATM fee + (other-ATM fee - acquiring cost paid to the other bank)
    a, o, r = b['atm'], b['oshare'], b['arca']
    for col in NEW:
        s.f(f'{col}{a}', f"{cp(tier, 'own')}*(1-{col}{o})+({cp(tier, 'oth')}-(0.25%*{col}{r}+0.5%*(1-{col}{r})))*{col}{o}", S['pct'])
    s.f(f'I{a}', f'AVERAGE(E{a}:H{a})', S['pct'])
    s.t(f'B{a}', 'Margin (own-ATM fee + other-ATM fee less acquiring cost 0.25% ArCa / 0.5% Visa-MC)', S['lbl'])
    # C2C to other banks: fee less 0.25% interbank cost
    for col in NEW:
        s.f(f'{col}{b["c2c"]}', f"{cp(tier, 'c2c')}-0.25%", S['pct'])
    s.f(f'I{b["c2c"]}', f'AVERAGE(E{b["c2c"]}:H{b["c2c"]})', S['pct'])
    s.t(f'B{b["c2c"]}', 'Margin (transfer fee less 0.25% interbank cost)', S['lbl'])
    # FX: revenue at today's spreads x (new spread / current spread), weighted by card FX balances
    x = b['fxf']
    s.t(f'B{x}', 'FX spread factor vs current (weighted by card FX balances USD/EUR/RUB)', S['lbl']); s.t(f'C{x}', 'x', S['lbl'])
    for col in NEW:
        s.f(f'{col}{x}', fx_factor(tier), S['lnk_x'])
    fx, mbr = b['fx'], b['mb_fx']
    scale = '' if tier != 'free' else f'*$D${BLK["free"]["nc"] + 1}/$D${BLK["black"]["nc"] + 1}'
    s.f(f'G{fx}', f"AVERAGE(F{fx},{MB}!E{mbr}{scale})*G{x}", S['num'])
    s.f(f'H{fx}', f"{MB}!E{mbr}{scale}*H{x}", S['num'])
    s.f(f'J{fx}', f"{MB}!F{mbr}{scale}*J{x}", S['num'])
    s.f(f'K{fx}', f"{MB}!G{mbr}{scale}*K{x}", S['num'])
    # balance margins: funding reference rate less the client rate from the Control panel
    for col in NEW:
        s.f(f'{col}{b["amd"]}', f"{CC}!$D$90-{cp(tier, 'amd')}", S['pct'])
        s.f(f'{col}{b["fxm"]}', f"{CC}!$D$97-{cp(tier, 'fxr')}", S['pct'])
    s.f(f'I{b["amd"]}', f'AVERAGE(E{b["amd"]}:H{b["amd"]})', S['pct'])
    s.f(f'I{b["fxm"]}', f'AVERAGE(E{b["fxm"]}:H{b["fxm"]})', S['pct'])
    # first-year card cost by card type (Virtual / Plastic / Metal)
    base = {'black': f"AVERAGE({CC}!D109,{CC}!G109)", 'premium': f"AVERAGE({CC}!H109,{CC}!E109)",
            'elite': f"AVERAGE({CC}!F109,{CC}!I109)", 'free': f"{CC}!G109"}[tier]
    s.f(f'I{b["plastic"]}', f"{base}*{card_factor(tier)}", S['num'])
    s.t(f'B{b["plastic"]}', 'Card plastic cost (x0 virtual, x73 metal)', S['lbl'])
    virt = f'{cp(tier, "type")}="Virtual"'
    for key in ('deliv', 'emb', 'act'):
        ref = f'I{b[key]}'
        orig, _, isf, _ = s.src(ref)                        # Free's cells are untouched copies of Black's originals
        orig = orig if isf else str(orig)
        s.f(ref, f'IF({virt},0,{orig})', S['num'])
    # cashback at a target rate on non-cash payments + deposit-uplift placeholders
    r, nc = b['cb'], b['nc']
    for rr in range(r + 1, r + 9):
        for col in 'BCDEFGHIJKLM':
            s.drop(f'{col}{rr}')
    s.t(f'B{r}', 'Cashback for the period', S['lbl_b'])
    for col in ('G', 'H', 'J', 'K'):
        s.f(f'{col}{r}', f'{col}{r + 1}*{col}{nc}', S['amd_b'])
    s.f(f'I{r}', f'SUM(G{r}:H{r})', S['amd_b'])
    s.t(f'B{r + 1}', 'Cashback target rate (share of non-cash payments)', S['lbl']); s.t(f'C{r + 1}', '%', S['lbl'])
    for col in ('G', 'H', 'I', 'J', 'K'):
        s.f(f'{col}{r + 1}', cp(tier, 'cb'), S['lnk_pct'])
    s.t(f'B{r + 2}', 'Deposit uplift cost for the period', S['lbl_b']); s.t(f'C{r + 2}', 'AMD', S['lbl'])
    for col in ('G', 'H'):
        s.f(f'{col}{r + 2}', f'{col}{r + 3}*{col}{r + 4}*({col}{r + 6}-{col}{r + 5})/4', S['amd_b'])
    for col in ('J', 'K'):
        s.f(f'{col}{r + 2}', f'{col}{r + 3}*{col}{r + 4}*({col}{r + 6}-{col}{r + 5})', S['amd_b'])
    s.f(f'I{r + 2}', f'SUM(G{r + 2}:H{r + 2})', S['amd_b'])
    for k, (label, unit, st) in enumerate([
            ('Share of cardholders with a term deposit (fill in)', '%', S['asm_pct']),
            ('Average term deposit per depositor (fill in)', 'AMD', S['asm_amd']),
            ('Baseline deposit rate (fill in)', '%', S['asm_pct'])]):
        s.t(f'B{r + 3 + k}', label, S['lbl']); s.t(f'C{r + 3 + k}', unit, S['lbl'])
        for col in ('G', 'H', 'J', 'K'):
            s.blank(f'{col}{r + 3 + k}', st)
    s.t(f'B{r + 6}', 'Uplifted deposit rate (baseline + Control panel uplift)', S['lbl']); s.t(f'C{r + 6}', '%', S['lbl'])
    for col in ('G', 'H', 'J', 'K'):
        s.f(f'{col}{r + 6}', f"{col}{r + 5}+{cp(tier, 'up')}", S['lnk_pct'])
    # summary: add the uplift line and net it out
    sm = b['sm']
    s.t(f'N{sm["cb"]}', 'Cashback + perks', S['sumlbl'])
    s.t(f'N{sm["up"]}', 'Deposit uplift cost', S['sumlbl'])
    for col, src in zip('OPQ', 'IJK'):
        s.f(f'{col}{sm["up"]}', f'{src}{r + 2}', S['sumnum'])
        s.f(f'{col}{sm["after"]}', f'{col}{sm["net"]}-{col}{sm["cb"]}-{col}{sm["up"]}', S['sumnum_b'])
    s.f(f'R{sm["up"]}', f'SUM(O{sm["up"]}:Q{sm["up"]})', S['sumnum'])
    s.f(f'R{sm["after"]}', f'R{sm["net"]}-R{sm["cb"]}-R{sm["up"]}', S['sumnum_b'])
    s.t(f'N{sm["after"]}', 'Net income after cashback & deposit uplift', S['sumlbl_b'])


# --- Fast Black: take Visa Digital (Current cards col K) out of the actuals - it is now Fast Free
E.t('F6', 'Fast Black (ArCa Classic, Visa Classic, Visa Gold)')
for ref, fml in {
    'D12': f"({CC}!D34*{CC}!D8+{CC}!G34*{CC}!G8)/SUM({CC}!D8,{CC}!G8)*3",
    'D18': f"({CC}!G52+{CC}!H52)/SUM({CC}!D47,{CC}!G52,{CC}!G47,{CC}!H52,{CC}!H47)",
    'D20': f"SUM({CC}!D47,{CC}!G47:H47)/SUM({CC}!D8,{CC}!G8:H8)",
    'D21': f"SUM({CC}!D54,{CC}!G54:H54)/SUM({CC}!D8,{CC}!G8:H8)",
    'D26': f"{CC}!D71/SUM({CC}!D71,{CC}!G71:H71)",
    'D28': f"SUM({CC}!D71,{CC}!G71:H71)/SUM({CC}!D8,{CC}!G8:H8)",
    'D33': f"SUM({CC}!D79,{CC}!G79)/SUM({CC}!D8,{CC}!G8)",
    'D45': f"SUM({CC}!D92,{CC}!G92:H92,{CC}!D99,{CC}!G99:H99)/SUM({CC}!D8,{CC}!G8:H8)",
    'D46': f"1-SUM({CC}!D92,{CC}!G92:H92)/SUM({CC}!D99,{CC}!G99:H99,{CC}!D92,{CC}!G92:H92)",
}.items():
    _, st, _, _ = E.src(ref)
    E.f(ref, fml, st)

# --- Fast Free: copy Fast Black rows 6-73 (cols B..R) down by OFF rows, then point actuals at Visa Digital
for r in range(6, 74):
    for col in [get_column_letter(i) for i in range(2, 19)]:
        if col == 'M':
            continue                                         # Black-specific notes
        v, st, isf, istxt = E.src(f'{col}{r}')
        dst = f'{col}{r + OFF}'
        if v is None and st is None:
            continue
        if isf:
            E.f(dst, shift_rows(v, OFF), st)
        elif v is None:
            E.blank(dst, st)
        elif istxt:
            E.t(dst, v, st)
        else:
            E.n(dst, v, st)
E.t(f'F{6 + OFF}', 'Fast Free (Visa Digital)')
fr = lambda r: r + OFF
FREE_ACTUALS = {
    12: f"{CC}!K34*3", 18: f"{CC}!K52/SUM({CC}!K47,{CC}!K52)", 20: f"{CC}!K47/{CC}!K8", 21: f"{CC}!K54/{CC}!K8",
    26: "0", 28: f"{CC}!K71/{CC}!K8", 33: f"{CC}!K79/{CC}!K8", 37: f"{CC}!K81",
    45: f"({CC}!K92+{CC}!K99)/{CC}!K8", 46: f"1-{CC}!K92/({CC}!K92+{CC}!K99)", 50: f"{CC}!$K$130*3",
}
for r, fml in FREE_ACTUALS.items():
    _, st, _, _ = E.src(f'D{fr(r)}')
    E.f(f'D{fr(r)}', fml, st)
for col in ('E', 'F'):
    E.f(f'{col}{fr(37)}', f'D{fr(37)}')                     # Black's 2 / 3 AMD placeholders don't apply to Free
E.f(f'I{fr(58)}', f"{CC}!K127")
# forward volumes follow Fast Black's growth path from Free's own starting point
for r in (20, 28, 33, 45):
    for col in ('H', 'J', 'K'):
        _, st, _, _ = E.src(f'{col}{fr(r)}')
        E.f(f'{col}{fr(r)}', f'$D{fr(r)}*{col}{r}/$D{r}', st)
# the cash-out volume rows were labelled "Non-cash payment" in the original blocks; relabel them
for r0 in (27, 96, 171, 27 + OFF):
    E.t(f'B{r0}', 'Cashout volume (total)'); E.t(f'B{r0 + 1}', 'Cashout volume (monthly)')

for tier in ('black', 'premium', 'elite', 'free'):
    write_terms(tier)
E.dimension('A1:Y293')

# ------------------------------------------------------------------ Control panel
for r in range(4, 70):
    if r in C.rows:
        for c in list(C.rows[r]):
            if c.get('r') not in ('C13',):                     # C13 carries a threaded comment - keep the cell
                C.rows[r].remove(c)
LABELS = ['Service fee, AMD per year', 'Cashout fee (FB ATM), %', 'Cashout fee (other ATM), %', 'Transfer to other bank fee, %',
          'Remaining balance rate (AMD), %', 'Remaining balance rate (non-AMD), %', 'Virtual, plastic or metal card',
          'USD FX rate (half of bid-ask spread), %', 'EUR FX rate (half of bid-ask spread), %', 'RUB FX rate (half of bid-ask spread), %',
          'Cashback target rate, %', 'Deposit uplift rate, p.p.']
PCT = {k for k in KEYS if k not in ('fee', 'type')}
REF = {  # Fast Bank today (card tariff TC 04 01#12, 26.06.2026; 'Current cards' tab)
    'free':    dict(fee=f"={CC}!K37", own=f"={CC}!K60", oth=f"={CC}!K66", amd=f"={CC}!K89", fxr=f"={CC}!K96", type='Virtual'),
    'black':   dict(fee=f"={CC}!G37", own=f"={CC}!G60", oth=f"={CC}!G66", amd=f"={CC}!G89", fxr=f"={CC}!G96", type='Plastic'),
    'premium': dict(fee=f"={CC}!E37", own=f"={CC}!E60", oth=f"={CC}!E66", amd=f"={CC}!E89", fxr=f"={CC}!E96", type='Plastic'),
    'elite':   dict(fee=f"={CC}!I37", own=f"={CC}!I60", oth=f"={CC}!I66", amd=f"={CC}!I89", fxr=f"={CC}!I96", type='Plastic'),
}
COMMON_REF = dict(c2c=0.005, usd=0.0041, eur=0.0096, rub=0.0197, cb=0.0, up=0.0)
INPUT = {   # pre-filled with the model's previous assumptions so outputs stay comparable; edit freely
    'free':    dict(fee=0, type='Virtual', cb=0.0),
    'black':   dict(fee=0, type='Plastic', cb=0.0055),
    'premium': dict(fee=18000, type='Plastic', cb=0.0065),
    'elite':   dict(fee=84000, type='Plastic', cb=0.01),
}
COMMON_IN = dict(own=0.005, oth=0.012, c2c=0.005, amd=0.05, fxr=0.001, usd=0.0041, eur=0.0096, rub=0.0197, up=0.0)
BTIER = {'free': 'free', 'black': 'plus', 'premium': 'premium', 'elite': 'elite'}
NOTES = {
    'fee': 'Annual fee, other banks\' cards in the tier',
    'own': 'Effective % on the tier\'s monthly cash (free allowances applied)',
    'oth': 'Effective % on the tier\'s monthly cash (free allowances applied)',
    'c2c': 'Card-to-card to other banks, published %',
    'amd': 'Rate earned on the tier\'s typical AMD balance (thresholds applied)',
    'fxr': 'Not collected in the market scan',
    'type': 'Virtual: no plastic, delivery or embossing. Metal: plastic cost x73 (Current cards J109/I109)',
    'usd': 'Half of each bank\'s USD buy/sell spread, rate.am 21.09.2026 (card rate where published)',
    'eur': 'Half of each bank\'s EUR buy/sell spread, rate.am 21.09.2026',
    'rub': 'Half of each bank\'s RUB buy/sell spread, rate.am 21.09.2026',
    'cb': 'Bank-funded cashback (cash + points), effective on the tier\'s spend basket',
    'up': 'Deposit-rate boost linked to the card (Ameriabank packages +0.25, IDBank VISAGOLD +0.5)',
}
BM_KEY = dict(fee='fee', own='atm_own', oth='atm_oth', c2c='c2c_out', amd='int_amd', cb='cb', up='uplift')

C.t('B1', 'DEBIT CARD ECONOMICS - CONTROL PANEL', S['cp_hdr'])
C.t('B2', 'Edit the orange cells in column D. C = Fast Bank today; E-G = market low / median / high (Armenian Card Tier Benchmark v8, 21.09.2026, '
          'other 6 banks\' cards in the same tier); I-L = per-card output from \'Economics Sept26 Upd\'. Inputs apply from the Q3 2026 launch.', S['cp_note'])
C.t('M3', 'BENCHMARK BASIS', S['cp_hdr_bm'])
for tier in TIERS:
    b = BASE[tier]
    C.t(f'B{b}', NAMES[tier], S['cp_hdr']); C.t(f'C{b}', 'Reference (Fast today)', S['cp_hdr']); C.t(f'D{b}', 'Parameters', S['cp_hdr_d'])
    for col, lab in zip('EFG', ('Low-end', 'Mid-point', 'High-end')):
        C.t(f'{col}{b}', lab, S['cp_hdr_bm'])
    C.t(f'H{b}', 'Per card, AMD', S['cp_hdr_out'])
    for col, lab in zip('IJKL', ('2026', '2027', '2028', '3Y LTV')):
        C.t(f'{col}{b}', lab, S['cp_hdr_out'])
    bt = bench[BTIER[tier]]
    for i, key in enumerate(KEYS):
        r = b + 1 + i
        C.t(f'B{r}', LABELS[i], S['cp_lbl'])
        # reference
        ref = REF[tier].get(key, COMMON_REF.get(key))
        if key == 'type':
            C.t(f'C{r}', ref, S['cp_ref_txt'])
        elif isinstance(ref, str) and ref.startswith('='):
            C.f(f'C{r}', ref, S['cp_ref_amd'] if key == 'fee' else S['cp_ref_pct'])
        else:
            if tier == 'free' and key == 'usd':
                C.n('C13', ref, S['cp_ref_pct'])
            else:
                C.n(f'C{r}', ref, S['cp_ref_pct'])
        # input
        v = INPUT[tier].get(key, COMMON_IN.get(key))
        if key == 'type':
            C.t(f'D{r}', v, S['asm_txt'])
        else:
            C.n(f'D{r}', v, S['asm_amd'] if key == 'fee' else S['asm_pct'])
        # benchmark
        if key in BM_KEY and bt[BM_KEY[key]]:
            lo, mid, hi, n = bt[BM_KEY[key]]
            for col, val in zip('EFG', (lo, mid, hi)):
                if key == 'fee':
                    C.n(f'{col}{r}', val, S['cp_bm_amd'])
                elif key == 'up':
                    C.n(f'{col}{r}', val / 100, S['cp_bm_pct'])
                else:
                    C.n(f'{col}{r}', val / 100, S['cp_bm_pct'])
            C.t(f'M{r}', f"{NOTES[key]} (n={n})", S['cp_note'])
        elif key in ('usd', 'eur', 'rub'):
            lo, mid, hi = bench['fx_' + key]
            for col, val in zip('EFG', (lo, mid, hi)):
                C.n(f'{col}{r}', val / 100, S['cp_bm_pct'])
            C.t(f'M{r}', NOTES[key] + ' (6 banks)', S['cp_note'])
        elif key == 'type':
            ty = bt['types']
            C.t(f'F{r}', f"{ty['Virtual']} virtual / {ty['Plastic']} plastic / {ty['Metal']} metal", S['cp_bm_txt'])
            C.t(f'M{r}', NOTES[key], S['cp_note'])
        else:
            C.t(f'F{r}', 'n/p', S['cp_bm_txt']); C.t(f'M{r}', NOTES[key], S['cp_note'])
    # outputs
    sm = BLK[tier]['sm']
    OUTROWS = [(1, 'Total revenue per card', 'tot', True), (2, 'fee', 'fee', False), (3, 'interest', 'int', False),
               (5, 'First year OPEX', 'fy', True), (6, 'Recurring OPEX', 'rec', True), (8, 'Net income per card', 'net', True),
               (10, 'Cashback + perks', 'cb', True), (11, 'Deposit uplift cost', 'up', True), (12, 'Net income after cashback & uplift', 'after', True)]
    for off, lab, key, bold in OUTROWS:
        r = b + off
        C.t(f'H{r}', lab, S['cp_out_lbl_b'] if bold else S['cp_out_lbl'])
        for col, src in zip('IJKL', 'OPQR'):
            C.f(f'{col}{r}', f"{EC}!{src}{sm[key]}", S['cp_out_b'] if bold else S['cp_out_b'])

# card-type dropdowns
dv = etree.Element(N + 'dataValidations'); dv.set('count', '1')
d = etree.SubElement(dv, N + 'dataValidation'); d.set('type', 'list'); d.set('allowBlank', '1'); d.set('showErrorMessage', '1')
d.set('sqref', ' '.join(f"D{BASE[t] + 1 + KEYS.index('type')}" for t in TIERS))
etree.SubElement(d, N + 'formula1').text = '"Virtual,Plastic,Metal"'
anchor = C.root.find(N + 'mergeCells')
anchor.addnext(dv)
cols = C.root.find(N + 'cols')
etree.SubElement(cols, N + 'col', min='13', max='13', width='70', customWidth='1')
C.dimension('B1:M62')

E.save(); C.save()
parts['xl/styles.xml'] = etree.tostring(styles, xml_declaration=True, encoding='UTF-8', standalone=True)

# ------------------------------------------------------------------ force a full recalculation in Excel; drop the stale calc chain
wbx = etree.fromstring(parts['xl/workbook.xml'])
cpr = wbx.find(N + 'calcPr'); cpr.set('fullCalcOnLoad', '1')
parts['xl/workbook.xml'] = etree.tostring(wbx, xml_declaration=True, encoding='UTF-8', standalone=True)
parts.pop('xl/calcChain.xml', None)
parts['[Content_Types].xml'] = re.sub(rb'<Override[^>]*calcChain[^>]*/>', b'', parts['[Content_Types].xml'])
parts['xl/_rels/workbook.xml.rels'] = re.sub(rb'<Relationship[^>]*calcChain[^>]*/>', b'', parts['xl/_rels/workbook.xml.rels'])

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in zin.namelist():
        if n in parts:
            z.writestr(zin.getinfo(n), parts[n])
print('written', OUT)
