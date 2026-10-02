"""Build the cashback engine prototype workbook (T-Bank model: personalised menu, 4 picks, partner offers).

    python3 build_workbook.py <data_dir> <out.xlsx>

data_dir holds prep.py outputs (mcc_stats.csv, profiles.pkl, sample.csv) and the v8 model reference values.
Everything the engine computes is an Excel formula; only data (sample spend, profiles) are values.
"""
import pickle
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation

from mcc_ref import CATEGORIES, ELIGIBLE, M, PICKABLE, lookup
from params import (CARD_TIER, FOREIGN, IF_DOM, IF_INTL, P, PARTNER, PARTNER_NAME, RATE, ROLE, TARGET, TARGET_SRC, TIERS,
                    UNKNOWN, UNKNOWN_TIER)

DATA, OUT = sys.argv[1:3]
IN_MODEL = '--in-model' in sys.argv          # link targets / caps to the tier model's 'Control panel' and prefix sheet names
CP_ROW = {'Free': 6, 'Black': 29, 'Premium': 52, 'Elite': 75}  # table headers on the v8 'Control panel'
PREFIX = 'CB ' if IN_MODEL else ''
stats = pd.read_csv(f'{DATA}/mcc_stats.csv', dtype={'mcc': str})
prof = pickle.load(open(f'{DATA}/profiles.pkl', 'rb'))
smp = pd.read_csv(f'{DATA}/sample.csv', dtype={'card_type': str, 'stratum': str})
clong = pd.read_csv(f'{DATA}/client_long.csv', dtype={'mcc': str})
ctypes = pd.read_csv(f'{DATA}/client_types.csv', dtype={'card_type': str})
MCCS = [c for c in smp.columns if c.isdigit()]

# ------------------------------------------------------------------ styles
FONT = 'Arial'
f_norm = Font(name=FONT, size=10)
f_bold = Font(name=FONT, size=10, bold=True)
f_title = Font(name=FONT, size=14, bold=True)
f_h = Font(name=FONT, size=10, bold=True, color='FFFFFF')
f_in = Font(name=FONT, size=10, color='0000FF')                 # inputs: blue
f_link = Font(name=FONT, size=10, color='008000')               # cross-sheet links: green
f_note = Font(name=FONT, size=9, italic=True, color='666666')
fill_h = PatternFill('solid', fgColor='1F3864')
fill_sub = PatternFill('solid', fgColor='D9E1F2')
fill_in = PatternFill('solid', fgColor='FFF2CC')                # key assumptions: light yellow
fill_out = PatternFill('solid', fgColor='E2EFDA')               # key outputs
fill_grey = PatternFill('solid', fgColor='F2F2F2')
thin = Side(style='thin', color='BFBFBF')
box = Border(top=thin, bottom=thin, left=thin, right=thin)
PCT, PCT2, AMD, AMD0, X = '0.0%', '0.00%', '#,##0;(#,##0);-', '#,##0', '0.00x'

wb = Workbook()
wb.remove(wb.active)


def ws_new(name, tab=None, widths=None):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    if tab:
        ws.sheet_properties.tabColor = tab
    for k, v in (widths or {}).items():
        ws.column_dimensions[k].width = v
    return ws


def put(ws, ref, v, font=f_norm, fmt=None, fill=None, bold=False, align=None, border=False):
    c = ws[ref]
    c.value = v
    c.font = f_bold if bold and font is f_norm else font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = box
    return c


def header(ws, row, cols, labels, fill=fill_h, font=f_h):
    for c, lab in zip(cols, labels):
        put(ws, f'{c}{row}', lab, font=font, fill=fill, align=Alignment(horizontal='center', vertical='center', wrap_text=True))


def inp(ws, ref, v, fmt=None):
    return put(ws, ref, v, font=f_in, fmt=fmt, fill=fill_in, border=True)


TC = ['D', 'E', 'F', 'G']                                           # tier columns on Inputs
NPK = len(PICKABLE)                                                 # 20
CAT_TXT = {c: CATEGORIES[c][0] for c in CATEGORIES}

# ================================================================== Inputs
wi = ws_new('Inputs', '0000FF', {'A': 2, 'B': 46, 'C': 14, 'D': 13, 'E': 13, 'F': 13, 'G': 13, 'H': 13, 'I': 13, 'J': 13, 'K': 13, 'L': 60})
put(wi, 'B1', 'CASHBACK ENGINE – INPUTS', f_title)
put(wi, 'B2', 'Blue on yellow = editable input. Black = formula. Green = link to another sheet. Rates are fractions (1% = 0.01).', f_note)

put(wi, 'B4', 'A. Global settings', f_bold, fill=fill_sub)
g = {}
rows = [('month', 'Data month in the engine sample', '2026-08', None, 'Latest full month in SPEND BY MCC.csv (Aug-25 – Aug-26)'),
        ('unk', 'Tier for clients whose card type is unknown', UNKNOWN_TIER, None, 'Alex 24.09: no card information → no cashback. Cards issued before Aug-25 are not in Extract_client_DB (23% of August clients)'),
        ('ifintl', 'Issuer interchange on foreign / cross-border spend', IF_INTL, PCT2, "Model 'Cards model as at late 25' row 50 (1.5%)"),
        ('months', 'Months per year (annualisation)', 12, AMD0, '')]
for i, (k, lab, v, fmt, note) in enumerate(rows):
    r = 5 + i
    g[k] = f'Inputs!$C${r}'
    put(wi, f'B{r}', lab)
    inp(wi, f'C{r}', v, fmt)
    put(wi, f'L{r}', note, f_note)

put(wi, 'B10', 'B. Card type → tier', f_bold, fill=fill_sub)
header(wi, 11, ['B', 'C', 'D'], ['Card type (as in Extract_client_DB)', 'Tier', 'Note'])
card_rows = list(CARD_TIER.items()) + [(UNKNOWN, None)]
for i, (ct, t) in enumerate(card_rows):
    r = 12 + i
    put(wi, f'B{r}', ct)
    if t is None:
        put(wi, f'C{r}', '=$C$6', font=f_norm, border=True)
        put(wi, f'D{r}', 'follows the global setting above', f_note)
    else:
        inp(wi, f'C{r}', t)
        if t == 'No cashback':
            put(wi, f'D{r}', 'business cards: not in the retail programme (excluded from the sample)', f_note)
MAP_RNG = f'Inputs!$B$12:$C${12 + len(card_rows) - 1}'

# ---- C. per-tier programme parameters
R0 = 25
put(wi, f'B{R0 - 1}', 'C. Programme parameters by tier (T-Bank model: personalised menu + picks + partner offers)', f_bold, fill=fill_sub)
header(wi, R0, ['B', 'C'] + TC + ['L'], ['Parameter', 'Unit', *TIERS, 'Notes'])
PR = {}
prm = [
    ('active', 'Programme active (kill switch)', '1 / 0', AMD0, 'Free runs with 0% rates: engine-ready, switch on by entering rates'),
    ('menu', 'Menu size: bank categories shown to the client', '#', AMD0, 'T-Bank: 8 / 9 / 10 by plan. Here 7 bank categories + up to 2 partner offers'),
    ('picks', 'Picks per month', '#', AMD0, 'Client picks the options with the highest expected reward (rational top-k)'),
    ('bmode', 'Base option ("all purchases")', 'Pickable / Automatic / Off', None, 'T-Bank since 2023: base 1% is one of the pickable options, not automatic'),
    ('brate', 'Base rate on all eligible purchases', '%', PCT2, 'Applies to eligible spend outside the picked categories'),
    ('auto', 'Scale menu rates to hit the Control panel target', 'Yes / No', None, 'Yes = category and base rates are multiplied so that bank cost = target × non-cash spend (the P&L follows the target). No = rates as typed below × manual multiplier'),
    ('mult', 'Manual rate multiplier (used when scaling is "No")', 'x', X, 'Scales all bank category and base rates of the tier at once'),
    ('cap', 'Monthly cap, bank-funded cashback', 'AMD / client', AMD0, "One cap on the sum of category + base cashback, per client (v8 'Control panel')"),
    ('pcomp', 'Partner offers take one of the picks', 'Yes / No', None, 'Yes = client chooses them among the 4 picks; No = applied automatically on top'),
    ('pcap', 'Monthly cap, partner offers', 'AMD / client', AMD0, 'Separate cap so a generous merchant does not use the bank budget (T-Bank: 6,000 RUB)'),
    ('q', 'Share of clients who do not choose', '%', PCT, 'Typically high in the first months; depends on reminders and app placement'),
    ('ncrule', 'What non-choosers get', 'Nothing / Flat rate / Auto-pick', None, 'Alex 24.09: clients who do not pick get a flat rate on all eligible purchases'),
    ('ncrate', 'Flat rate for non-choosers (all eligible purchases)', '%', PCT2, 'Used when the rule above is "Flat rate". Not scaled by the rate multiplier'),
    ('prepl', 'Partner offer replaces the same bank category', 'Yes / No', None, 'Yes = a category with an active partner offer is not shown again as a bank category (no double listing)'),
    ('minsp', 'Minimum monthly eligible spend to earn', 'AMD', AMD0, 'Gate: below this no cashback'),
    ('hair', 'Share of spend below the minimum transaction amount', '%', PCT, 'Haircut for a per-transaction minimum (e.g. 1,000 AMD); no transaction counts in the data yet'),
]
for i, (k, lab, unit, fmt, note) in enumerate(prm):
    r = R0 + 1 + i
    PR[k] = r
    put(wi, f'B{r}', lab)
    put(wi, f'C{r}', unit, f_note)
    src = {'active': P['active'], 'menu': P['menu_size'], 'picks': P['picks'], 'bmode': P['base_mode'], 'brate': P['base_rate'],
           'mult': {t: 1.0 for t in TIERS}, 'cap': P['cap'], 'pcomp': P['partner_compete'], 'pcap': P['partner_cap'],
           'q': P['nonchooser_share'], 'ncrule': P['nonchooser_rule'], 'minsp': P['min_spend'], 'hair': P['min_txn_haircut'],
           'ncrate': P['nc_rate'], 'prepl': P['partner_replace'], 'auto': {t: 'Yes' for t in TIERS}}[k]
    for c, t in zip(TC, TIERS):
        if IN_MODEL and k == 'cap':
            put(wi, f'{c}{r}', f"='Control panel'!$D${CP_ROW[t] + 14}", f_link, fmt, border=True)
        else:
            inp(wi, f'{c}{r}', src[t], fmt)
    put(wi, f'L{r}', "Linked to 'Control panel' cashback limit (row 20 / 43 / 66 / 89) – edit it there" if IN_MODEL and k == 'cap' else note, f_note)
r = R0 + 1 + len(prm)
PR['slots'] = r
put(wi, f'B{r}', 'Personalised slots (menu size − "Always" categories)')
put(wi, f'C{r}', '#', f_note)
r += 1
PR['meff'] = r
put(wi, f'B{r}', 'Rate multiplier in use (auto-scaled to the target, or manual)', bold=True)
put(wi, f'C{r}', 'x', f_note)
put(wi, f'L{r}', 'Auto value comes from Results ("Multiplier that makes bank cost = target × non-cash")', f_note)
r += 1
PR['tgt'] = r
put(wi, f'B{r}', 'Model target: cashback, % of non-cash spend', bold=True)
put(wi, f'C{r}', '%', f_note)
for c, t in zip(TC, TIERS):
    if IN_MODEL:
        put(wi, f'{c}{r}', f"='Control panel'!$D${CP_ROW[t] + 13}", f_link, PCT2, border=True)
    else:
        inp(wi, f'{c}{r}', TARGET[t], PCT2)
put(wi, f'L{r}', "Linked to 'Control panel' cashback target rate (row 19 / 42 / 65 / 88). The model applies it to ALL non-cash spend, incl. gambling" if IN_MODEL else "Typed from v8 'Control panel' (" + ', '.join(f'{t} {TARGET_SRC[t].split(" / ")[0]}' for t in TIERS) + '). The model applies it to ALL non-cash spend, incl. gambling', f_note)
PR_END = r

# ---- D. partner offers
PO = R0 + len(prm) + 5
put(wi, f'B{PO - 1}', 'D. Partner-funded offers (2 slots per tier; coverage = share of the category\'s spend at participating merchants)', f_bold, fill=fill_sub)
header(wi, PO, ['B', 'C'] + TC, ['Offer', 'Unit', *TIERS])
PRow = {}
for j in range(2):
    for m, (k, lab, unit, fmt) in enumerate([('cat', 'category', 'code', None), ('name', 'name shown in the app', 'text', None),
                                             ('rate', 'cashback rate', '%', PCT), ('cov', 'coverage of category spend', '%', PCT),
                                             ('fund', 'partner-funded share', '%', PCT)]):
        r = PO + 1 + j * 5 + m
        PRow[(j, k)] = r
        put(wi, f'B{r}', f'Offer {j + 1}: {lab}')
        put(wi, f'C{r}', unit, f_note)
        for c, t in zip(TC, TIERS):
            cat0, rate0, cov0, fund0 = PARTNER[t][j]
            inp(wi, f'{c}{r}', {'cat': cat0, 'name': PARTNER_NAME.get(cat0, 'Partner offer'), 'rate': rate0, 'cov': cov0, 'fund': fund0}[k], fmt)
PO_END = PO + 10

# ---- E. category rates and roles
CR0 = PO_END + 3
put(wi, f'B{CR0 - 1}', 'E. Category menu: headline rate and menu role by tier', f_bold, fill=fill_sub)
header(wi, CR0, ['B', 'C'] + TC + ['H', 'I', 'J', 'K', 'L'],
       ['Category', 'Code', *[f'Rate – {t}' for t in TIERS], *[f'Role – {t}' for t in TIERS], 'Role: Always = bank puts it on every menu (discovery); If spent = shown if among the client\'s top spend categories; No = never shown'])
CROW = {}
for i, c in enumerate(PICKABLE):
    r = CR0 + 1 + i
    CROW[c] = r
    put(wi, f'B{r}', CAT_TXT[c])
    put(wi, f'C{r}', c)
    for col, t in zip(TC, TIERS):
        inp(wi, f'{col}{r}', RATE[t][c], PCT)
    for col, t in zip(['H', 'I', 'J', 'K'], TIERS):
        inp(wi, f'{col}{r}', ROLE[t][c])
CR_END = CR0 + NPK

# ---- F. helper block for the engine (horizontal, tier x category)
H0 = CR_END + 3
put(wi, f'B{H0 - 1}', 'F. Engine helper tables (formulas, do not edit) – tier rows × category columns', f_bold, fill=fill_grey)
HC = [L(4 + k) for k in range(len(ELIGIBLE))]                       # D.. for 21 eligible categories
for k, c in enumerate(ELIGIBLE):
    put(wi, f'{HC[k]}{H0}', c, f_bold, align=Alignment(horizontal='center'))
HELP = {}
BLOCKS = [('hidden', 'Replaced by a partner offer'), ('spent', 'If-spent mask'), ('always', 'Always mask'), ('rate', 'Menu rate at ×1 (rate × active)')]
for b, (key, lab) in enumerate(BLOCKS):
    for ti, t in enumerate(TIERS):
        r = H0 + 1 + b * 5 + ti
        put(wi, f'B{r}', f'{lab} – {t}')
        put(wi, f'C{r}', ti + 1)
        for k, c in enumerate(PICKABLE):
            rc, tc = CROW[c], TC[ti]
            rolec = 'HIJK'[ti]
            hid = f'{HC[k]}{H0 + 1 + ti}'                                  # hidden-mask cell of this tier / category
            if key == 'hidden':
                f = (f'=IF(AND({tc}${PR["prepl"]}="Yes",OR(AND({tc}${PRow[(0, "cat")]}="{c}",{tc}${PRow[(0, "rate")]}>0),'
                     f'AND({tc}${PRow[(1, "cat")]}="{c}",{tc}${PRow[(1, "rate")]}>0))),1,0)')
            elif key == 'spent':
                f = f'=IF(AND(${rolec}${rc}="If spent",{hid}=0),1,0)'
            elif key == 'always':
                f = f'=IF(AND(${rolec}${rc}="Always",{hid}=0),1,0)'
            else:
                f = f'=${tc}${rc}*{tc}${PR["active"]}'
            wi[f'{HC[k]}{r}'] = f
            wi[f'{HC[k]}{r}'].number_format = PCT if key == 'rate' else AMD0
    HELP[key] = f'Inputs!$D${H0 + 1 + b * 5}:${HC[NPK - 1]}${H0 + 4 + b * 5}'
for ti, c in enumerate(TC):
    ar = H0 + 1 + 2 * 5 + ti                                               # always-mask row of the tier
    wi[f'{c}{PR["slots"]}'] = f'=MAX(0,{c}{PR["menu"]}-SUM($D${ar}:${HC[NPK - 1]}${ar}))'
    wi[f'{c}{PR["slots"]}'].font = f_norm
r = H0 + 1 + len(BLOCKS) * 5
ICF_ROW = r
put(wi, f'B{r}', 'Blended issuer interchange by category (from Categories)')
for k, c in enumerate(ELIGIBLE):
    wi[f'{HC[k]}{r}'] = f'=INDEX(Categories!$I$5:$I${4 + len(ELIGIBLE)},{k + 1})'
    wi[f'{HC[k]}{r}'].number_format = PCT2
    wi[f'{HC[k]}{r}'].font = f_link
HELP['icf'] = f'Inputs!$D${r}:${HC[len(ELIGIBLE) - 1]}${r}'

# data validation
dv = DataValidation(type='list', formula1='"Free,Black,Premium,Elite,No cashback"', allow_blank=False)
wi.add_data_validation(dv); dv.add('C6'); dv.add(f'C12:C{12 + len(card_rows) - 2}')
for key, lst in [('bmode', '"Pickable,Automatic,Off"'), ('pcomp', '"Yes,No"'), ('ncrule', '"Nothing,Flat rate,Auto-pick"'), ('prepl', '"Yes,No"'), ('auto', '"Yes,No"')]:
    d = DataValidation(type='list', formula1=lst); wi.add_data_validation(d); d.add(f'D{PR[key]}:G{PR[key]}')
d = DataValidation(type='list', formula1='"Always,If spent,No"'); wi.add_data_validation(d); d.add(f'H{CR0 + 1}:K{CR_END}')
d = DataValidation(type='list', formula1=f'=$C${CR0 + 1}:$C${CR_END}'); wi.add_data_validation(d)
for j in range(2):
    d.add(f'D{PRow[(j, "cat")]}:G{PRow[(j, "cat")]}')
wi.freeze_panes = 'D5'


def T(key, col_expr='$D7'):
    """Per-tier parameter for the engine row: INDEX(Inputs!$D$r:$G$r, tier_idx)."""
    r = PR[key]
    return f'INDEX(Inputs!$D${r}:$G${r},{col_expr})'


def PO_(j, key, col_expr='$D7'):
    r = PRow[(j, key)]
    return f'INDEX(Inputs!$D${r}:$G${r},{col_expr})'


# ================================================================== Categories
wc = ws_new('Categories', '7030A0', {'A': 2, 'B': 10, 'C': 40, 'D': 22, 'E': 34, 'F': 28, 'G': 10, 'H': 12, 'I': 12, 'J': 12, 'K': 60})
put(wc, 'B1', 'CASHBACK CATEGORIES (client-facing)', f_title)
put(wc, 'B2', 'Level 1 = spend group (Revolut-style analytics). Level 2 = cashback category (T-Bank-style pickable). Excluded groups follow T-Bank / Kaspi / ArCa-programme practice.', f_note)
header(wc, 4, list('BCDEFGHIJK'), ['Code', 'Cashback category', 'Spend group (Revolut)', 'T-Bank analog', 'Kaspi partner-catalogue analog (indicative)',
                                  'Pickable', 'Domestic interchange', 'Foreign share of spend', 'Blended interchange', 'Why'])
WHY = {'SUP': 'Biggest, most stable category: high deadweight, capped POS interchange – keep at a low rate',
       'RES': 'Visible, talked-about; good headline category', 'FST': 'High reach (38% of clients), small tickets',
       'DEL': 'Natural partner-funded category (delivery apps)', 'TAX': 'Clients often use another card or cash: incremental potential; partner-funding candidate',
       'TRN': 'Very high reach (41%), tiny volume: cheap engagement', 'FUE': 'Regular, mid-volume; fuel networks can co-fund',
       'AUT': 'Occasional, higher ticket', 'PHA': 'Frequent, needs-based purchases: good everyday category with moderate deadweight',
       'MED': 'Occasional, higher tickets (clinics, dentists, labs)', 'BEA': 'Strong perceived value; salons and cosmetics',
       'CLO': 'Large, seasonal category; retailers can co-fund', 'ELE': 'Large tickets, low margin: keep low or off the menu',
       'HOM': 'Occasional large tickets', 'KID': 'Family segment', 'ENT': 'Cheap discovery category: cost only if spend moves in',
       'SPO': 'Gyms: recurring, loyal spend', 'TRV': 'Higher (cross-border) interchange: can afford higher rates; partner-funding candidate',
       'ONL': 'Marketplaces (MCC 5262, 5399) and digital stores; cross-border online earns higher interchange', 'JEW': 'Rare large tickets: keep low',
       'OTH': 'Eligible, earns only through the base option'}
for i, c in enumerate(ELIGIBLE):
    r = 5 + i
    name, grp, tb, kas, pk = CATEGORIES[c]
    for col, v in zip('BCDEF', [c, name, grp, tb, kas]):
        put(wc, f'{col}{r}', v)
    put(wc, f'G{r}', 'Yes' if pk else 'Base only')
    inp(wc, f'H{r}', IF_DOM[c], PCT2)
    inp(wc, f'I{r}', FOREIGN[c], PCT)
    put(wc, f'J{r}', f'=H{r}*(1-I{r})+{g["ifintl"]}*I{r}', fmt=PCT2)
    put(wc, f'K{r}', WHY.get(c, ''), f_note)
# the Inputs helper reads column I (blended) – keep it there: swap J/I semantics? helper uses I -> fix below
for i, c in enumerate(ELIGIBLE):
    r = 5 + i
    wc[f'I{r}'].value, wc[f'J{r}'].value = FOREIGN[c], f'=H{r}*(1-I{r})+{g["ifintl"]}*I{r}'
r = 6 + len(ELIGIBLE)
put(wc, f'B{r}', 'Excluded (no cashback)', f_bold, fill=fill_sub)
for i, c in enumerate([k for k in CATEGORIES if k.startswith('X_')]):
    rr = r + 1 + i
    name, grp, tb, kas, pk = CATEGORIES[c]
    for col, v in zip('BCDEF', [c, name, grp, tb, kas]):
        put(wc, f'{col}{rr}', v)
put(wc, f'B{r + 13}', "Domestic interchange default 0.6% = model's local interchange margin ('Cards model as at late 25' row 45). CBA caps the interbank fee for small merchants at physical POS at 0.2% (from 1 March 2026) – replace with actual issuer interchange by MCC / channel when Ani provides it.", f_note)
put(wc, f'B{r + 14}', "Foreign share of spend is an estimate (no channel field in the data yet). Check: implied international share vs the model's actual share by card type on the Profiles sheet.", f_note)
# fix the helper reference to column J (blended)
for k, c in enumerate(ELIGIBLE):
    wi[f'{HC[k]}{ICF_ROW}'] = f'=INDEX(Categories!$J$5:$J${4 + len(ELIGIBLE)},{k + 1})'

# ================================================================== MCC_map
wm = ws_new('MCC_map', '00B050', {'A': 8, 'B': 58, 'C': 44, 'D': 10, 'E': 38, 'F': 20, 'G': 9, 'H': 9, 'I': 16, 'J': 16, 'K': 12})
put(wm, 'A1', 'MCC MAP – merchant category codes → cashback categories', f_title)
put(wm, 'A2', 'Edit column D (category code) to regroup an MCC; the Data, Engine and Results sheets follow. Brand names on 3xxx codes: verify against the scheme table before client-facing use.', f_note)
header(wm, 4, list('ABCDEFGHIJK'), ['MCC', 'Official name (ISO 18245 / scheme)', 'Plain name', 'Category', 'Category name', 'Spend group',
                                    'Eligible', 'In data', 'Avg monthly volume Mar–Aug 26, AMD', 'Aug-26 volume, AMD', 'Reach (6m)'])
st = stats.set_index('mcc')
codes = sorted(set(M) | set(st.index))
# collapse the brand-specific 3xxx codes that are not in the data into range rows
keep = [m for m in codes if not ('3000' <= m <= '3999') or m in st.index]
ranges = [('3000-3350', 'Airlines (carrier-specific codes)', 'Airline tickets', 'TRV'),
          ('3351-3500', 'Car rental agencies (brand-specific codes)', 'Car rental', 'TRV'),
          ('3501-3999', 'Hotels, motels, resorts (brand-specific codes)', 'Hotels', 'TRV')]
rows_m = [(m,) + lookup(m) for m in keep] + [(a, b, c, d) for a, b, c, d in ranges]
rows_m.sort(key=lambda x: x[0])
for i, (m, off, plain, cat) in enumerate(rows_m):
    r = 5 + i
    put(wm, f'A{r}', m, align=Alignment(horizontal='center'))
    put(wm, f'B{r}', off)
    put(wm, f'C{r}', plain)
    inp(wm, f'D{r}', cat)
    put(wm, f'E{r}', f'=IFERROR(VLOOKUP(D{r},Categories!$B$5:$D$40,2,FALSE),"?")')
    put(wm, f'F{r}', f'=IFERROR(VLOOKUP(D{r},Categories!$B$5:$D$40,3,FALSE),"?")')
    put(wm, f'G{r}', f'=IF(LEFT(D{r},2)="X_","No","Yes")')
    ind = m in st.index
    put(wm, f'H{r}', 'Yes' if ind else '')
    if ind:
        put(wm, f'I{r}', float(st.loc[m, 'vol_month_avg']), fmt=AMD)
        put(wm, f'J{r}', float(st.loc[m, 'vol_aug']), fmt=AMD)
        put(wm, f'K{r}', float(st.loc[m, 'reach_6m']), fmt=PCT)
MM_END = 4 + len(rows_m)
wm.auto_filter.ref = f'A4:K{MM_END}'
wm.freeze_panes = 'B5'
d = DataValidation(type='list', formula1='=Categories!$B$5:$B$40'); wm.add_data_validation(d); d.add(f'D5:D{MM_END}')

# ================================================================== Data
wd = ws_new('Data', '808080', {'A': 9, 'B': 30, 'C': 14, 'D': 9})
N = len(smp)
D0 = 7                                                             # first data row
DC = [L(5 + k) for k in range(len(MCCS))]                          # MCC columns E..
DL = DC[-1]
put(wd, 'A1', f'DATA – client × MCC card spend, {N:,} sampled clients, August 2026 (AMD)', f_title)
put(wd, 'A2', 'Stratified random sample by tier (all Elite clients); weight scales each client to the August population. Column A is the bank client_id (as requested); no names, card or account numbers. Source: SPEND BY MCC.csv + card type from Extract_client_DB.', f_note)
put(wd, 'D3', 'MCC →', f_bold)
put(wd, 'D4', 'Category →', f_bold)
put(wd, 'D5', 'Name →', f_bold)
header(wd, 6, ['A', 'B', 'C', 'D'], ['Client ID', 'Card type', 'Sample stratum', 'Weight'])
for k, m in enumerate(MCCS):
    c = DC[k]
    put(wd, f'{c}3', m, f_bold, align=Alignment(horizontal='center'))
    put(wd, f'{c}4', f'=IFERROR(VLOOKUP({c}$3,MCC_map!$A$5:$D${MM_END},4,FALSE),"OTH")', f_link, align=Alignment(horizontal='center'))
    put(wd, f'{c}5', lookup(m)[1], f_note, align=Alignment(wrap_text=True))
    put(wd, f'{c}6', m, f_h, fill=fill_h, align=Alignment(horizontal='center'))
    wd.column_dimensions[c].width = 11
wd.row_dimensions[5].height = 45
vals = smp[['client_key', 'card_type', 'stratum', 'weight'] + MCCS].values.tolist()
for i, row in enumerate(vals):
    r = D0 + i
    wd.cell(r, 1, int(row[0])); wd.cell(r, 2, row[1]); wd.cell(r, 3, row[2])
    wd.cell(r, 4, round(float(row[3]), 6))
    for k in range(len(MCCS)):
        v = row[4 + k]
        if v:
            wd.cell(r, 5 + k, round(float(v), 2))
DEND = D0 + N - 1
wd.freeze_panes = 'E7'

# ================================================================== Engine
we = ws_new('Engine', 'C00000')
E0 = D0
S0 = 12                                                           # column L: first category spend column
SC = [L(S0 + k) for k in range(len(ELIGIBLE))]                   # L..AF (21)
KS = L(S0 + len(ELIGIBLE))                                       # AG  kth spent
EV = [L(S0 + len(ELIGIBLE) + 1 + k) for k in range(NPK)]         # AH..BA
EVB, EVP1, EVP2 = [L(S0 + len(ELIGIBLE) + 1 + NPK + k) for k in range(3)]   # BB BC BD
P1R, P2R, KTH = [L(S0 + len(ELIGIBLE) + 4 + NPK + k) for k in range(3)]    # BE BF BG
PK = [L(S0 + len(ELIGIBLE) + 7 + NPK + k) for k in range(NPK)]  # BH..CA
PKB, PKP1, PKP2 = [L(S0 + len(ELIGIBLE) + 7 + 2 * NPK + k) for k in range(3)]  # CB CC CD
rest = ['SPK', 'CBC', 'CBB', 'CBCH', 'CBNC', 'CAP', 'NCCAP', 'BANK', 'CAPHIT', 'PRAW', 'PPAID', 'PBANK', 'COST', 'ICF']
RC = {k: L(S0 + len(ELIGIBLE) + 10 + 2 * NPK + i) for i, k in enumerate(rest)}  # CE..
put(we, 'A1', 'ENGINE – one row per client (monthly): menu → expected reward → top-k picks → caps → cashback', f_title)
put(we, 'A2', 'All formulas. Row 4 holds the category codes used by the SUMIFs and INDEX lookups. Expected values blend choosers and non-choosers (share from Inputs).', f_note)
groups = [('A', 'K', 'Client & spend'), (SC[0], SC[-1], 'Eligible spend by category (from Data via MCC_map)'), (KS, KS, 'Menu'),
          (EV[0], EVP2, 'Expected reward of each option (0 = not on the menu)'), (P1R, KTH, 'Partner / pick threshold'),
          (PK[0], PKP2, 'Picked (1/0)'), (RC['SPK'], RC['ICF'], 'Cashback and economics')]
for a, b, lab in groups:
    put(we, f'{a}3', lab, f_h, fill=fill_h)
    if a != b:
        we.merge_cells(f'{a}3:{b}3')
labels = {'A': 'Client ID', 'B': 'Card type', 'C': 'Tier', 'D': 'Tier #', 'E': 'Weight', 'F': 'Total card spend',
          'G': 'Cash withdrawals', 'H': 'Gambling', 'I': 'All excluded spend', 'J': 'Non-cash spend (model basis)', 'K': 'Eligible spend',
          KS: 'Menu threshold (k-th largest spend among "If spent" categories)', EVB: 'Base option', EVP1: 'Partner offer 1 (if it takes a pick)',
          EVP2: 'Partner offer 2 (if it takes a pick)', P1R: 'Partner offer 1 reward', P2R: 'Partner offer 2 reward', KTH: 'Pick threshold (k-th largest option)',
          PKB: 'Base picked', PKP1: 'Offer 1 applied', PKP2: 'Offer 2 applied',
          RC['SPK']: 'Spend in picked categories', RC['CBC']: 'Cashback on picked categories', RC['CBB']: 'Cashback from base option',
          RC['CBCH']: 'Cashback if the client chooses, menu rates ×1 (before cap)', RC['NCCAP']: 'Non-chooser cashback, capped (not scaled; 0 if non-choosers auto-pick)', RC['CBNC']: 'Cashback if the client does not choose (before cap)', RC['CAP']: 'Monthly cap',
          RC['BANK']: 'BANK CASHBACK (expected, rates × multiplier in use, capped)', RC['CAPHIT']: 'Cap hit (expected share)', RC['PRAW']: 'Partner cashback before cap',
          RC['PPAID']: 'Partner cashback paid (expected, capped)', RC['PBANK']: 'of which bank-funded', RC['COST']: 'TOTAL BANK COST',
          RC['ICF']: 'Issuer interchange on eligible spend'}
for k, c in enumerate(ELIGIBLE):
    labels[SC[k]] = c
for k, c in enumerate(PICKABLE):
    labels[EV[k]] = c
    labels[PK[k]] = c
for col, lab in labels.items():
    put(we, f'{col}5', lab, f_h, fill=fill_h, align=Alignment(horizontal='center', vertical='center', wrap_text=True))
for k, c in enumerate(ELIGIBLE):
    put(we, f'{SC[k]}4', c, f_bold, align=Alignment(horizontal='center'))
for k, c in enumerate(PICKABLE):
    put(we, f'{EV[k]}4', c, f_note, align=Alignment(horizontal='center'))
    put(we, f'{PK[k]}4', c, f_note, align=Alignment(horizontal='center'))
we.row_dimensions[5].height = 60
for col in ['A', 'B', 'C']:
    we.column_dimensions[col].width = 12
we.column_dimensions['B'].width = 20
for k in range(6, 12):
    we.column_dimensions[L(k)].width = 13
for c in SC + EV + [KS, EVB, EVP1, EVP2, P1R, P2R, KTH] + list(RC.values()):
    we.column_dimensions[c].width = 11
for c in PK + [PKB, PKP1, PKP2]:
    we.column_dimensions[c].width = 5

MR = f'Data!$E$4:${DL}$4'
h = f"(1-{T('hair')})"
for i in range(N):
    r = E0 + i
    dr = f'Data!$E{r}:${DL}{r}'
    row = {
        'A': f'=Data!A{r}', 'B': f'=Data!B{r}',
        'C': f'=IFERROR(VLOOKUP(B{r},{MAP_RNG},2,FALSE),{g["unk"]})',
        'D': f'=IFERROR(MATCH(C{r},Inputs!$D${R0}:$G${R0},0),0)',
        'E': f'=Data!D{r}', 'F': f'=SUM({dr})',
        'G': f'=SUMIF({MR},"X_CASH",{dr})', 'H': f'=SUMIF({MR},"X_GAMB",{dr})', 'I': f'=SUMIF({MR},"X_*",{dr})',
        'J': f'=F{r}-G{r}', 'K': f'=F{r}-I{r}',
    }
    for k in range(len(ELIGIBLE)):
        row[SC[k]] = f'=SUMIF({MR},{SC[k]}$4,{dr})'
    srow = f'${SC[0]}{r}:${SC[NPK - 1]}{r}'
    row[KS] = (f'=IF($D{r}=0,0,IF({T("slots", f"$D{r}")}<1,9E+99,'
               f'_xlfn.AGGREGATE(14,6,{srow}*INDEX({HELP["spent"]},$D{r},0),{T("slots", f"$D{r}")})))')
    for k, c in enumerate(PICKABLE):
        s = f'{SC[k]}{r}'
        row[EV[k]] = (f'=IF($D{r}=0,0,IF(OR(INDEX({HELP["always"]},$D{r},{k + 1})=1,AND(INDEX({HELP["spent"]},$D{r},{k + 1})=1,{s}>0,{s}>=${KS}{r})),'
                      f'INDEX({HELP["rate"]},$D{r},{k + 1})*{s}*{h.replace("$D7", f"$D{r}")}+{NPK - k}*1E-6,0))')
    tp = lambda key: T(key, f'$D{r}')                                        # noqa: E731
    hh = f"(1-{tp('hair')})"
    act = tp('active')
    evc_rng, evp_rng, s_rng = f'${EV[0]}{r}:${EV[-1]}{r}', f'${EVP1}{r}:${EVP2}{r}', f'${SC[0]}{r}:${SC[NPK - 1]}{r}'
    # base option is worth the base rate on eligible spend OUTSIDE the other (picks - 1) best options
    s_top = f'IF({tp("picks")}<2,0,SUMPRODUCT(({evc_rng}>=LARGE(({evc_rng},{evp_rng}),{tp("picks")}-1))*({evc_rng}>0.001)*{s_rng}))'
    row[EVB] = f'=IF($D{r}=0,0,IF({tp("bmode")}="Pickable",{tp("brate")}*{act}*($K{r}-{s_top})*{hh},0))'
    for j, (evc, rawc) in enumerate([(EVP1, P1R), (EVP2, P2R)]):
        catv = PO_(j, 'cat', f'$D{r}')
        row[rawc] = (f'=IF($D{r}=0,0,{PO_(j, "rate", f"$D{r}")}*{act}*IFERROR(INDEX(${SC[0]}{r}:${SC[-1]}{r},MATCH({catv},${SC[0]}$4:${SC[-1]}$4,0)),0)'
                     f'*{PO_(j, "cov", f"$D{r}")}*{hh})')
        row[evc] = f'=IF($D{r}=0,0,IF({tp("pcomp")}="Yes",{rawc}{r},0))'
    row[KTH] = f'=IF($D{r}=0,0,LARGE(${EV[0]}{r}:${EVP2}{r},{tp("picks")}))'
    for k in range(NPK):
        row[PK[k]] = f'=IF(AND({EV[k]}{r}>=${KTH}{r},{EV[k]}{r}>0.001),1,0)'
    row[PKB] = f'=IF(AND({EVB}{r}>=${KTH}{r},{EVB}{r}>0.001),1,0)'
    for pkc, evc, rawc in [(PKP1, EVP1, P1R), (PKP2, EVP2, P2R)]:
        row[pkc] = f'=IF($D{r}=0,0,IF({tp("pcomp")}="Yes",IF(AND({evc}{r}>=${KTH}{r},{evc}{r}>0.001),1,0),IF({rawc}{r}>0,1,0)))'
    pkr, sr = f'${PK[0]}{r}:${PK[-1]}{r}', f'${SC[0]}{r}:${SC[NPK - 1]}{r}'
    row[RC['SPK']] = f'=SUMPRODUCT({pkr},{sr})'
    row[RC['CBC']] = f'=IF($D{r}=0,0,SUMPRODUCT({pkr},{sr},INDEX({HELP["rate"]},$D{r},0))*{hh})'
    base = f'{tp("brate")}*{act}'
    row[RC['CBB']] = (f'=IF($D{r}=0,0,IF({tp("bmode")}="Pickable",{PKB}{r}*{base}*($K{r}-{RC["SPK"]}{r}),'
                      f'IF({tp("bmode")}="Automatic",{base}*($K{r}-{RC["SPK"]}{r}),0))*{hh})')
    row[RC['CBCH']] = f'=IF($D{r}=0,0,IF($K{r}>={tp("minsp")},{RC["CBC"]}{r}+{RC["CBB"]}{r},0))'
    row[RC['CBNC']] = (f'=IF($D{r}=0,0,IF($K{r}<{tp("minsp")},0,IF({tp("ncrule")}="Nothing",0,IF({tp("ncrule")}="Flat rate",'
                       f'{tp("ncrate")}*{act}*$K{r}*{hh},{RC["CBCH"]}{r}))))')
    row[RC['CAP']] = f'=IF($D{r}=0,0,{tp("cap")})'
    q = tp('q')
    meff = tp('meff')
    row[RC['NCCAP']] = f'=IF($D{r}=0,0,IF({tp("ncrule")}="Auto-pick",0,MIN({RC["CBNC"]}{r},{RC["CAP"]}{r})))'
    row[RC['BANK']] = (f'=IF($D{r}=0,0,(1-{q})*MIN({meff}*{RC["CBCH"]}{r},{RC["CAP"]}{r})+{q}*IF({tp("ncrule")}="Auto-pick",'
                       f'MIN({meff}*{RC["CBCH"]}{r},{RC["CAP"]}{r}),{RC["NCCAP"]}{r}))')
    row[RC['CAPHIT']] = f'=IF($D{r}=0,0,(1-{q})*IF({meff}*{RC["CBCH"]}{r}>{RC["CAP"]}{r},1,0))'
    row[RC['PRAW']] = f'={PKP1}{r}*{P1R}{r}+{PKP2}{r}*{P2R}{r}'
    row[RC['PPAID']] = f'=IF($D{r}=0,0,(1-{q})*MIN({RC["PRAW"]}{r},{tp("pcap")}))'
    row[RC['PBANK']] = (f'=IF($D{r}=0,0,IF({RC["PRAW"]}{r}>0,{RC["PPAID"]}{r}*({PKP1}{r}*{P1R}{r}*(1-{PO_(0, "fund", f"$D{r}")})'
                        f'+{PKP2}{r}*{P2R}{r}*(1-{PO_(1, "fund", f"$D{r}")}))/{RC["PRAW"]}{r},0))')
    row[RC['COST']] = f'={RC["BANK"]}{r}+{RC["PBANK"]}{r}'
    row[RC['ICF']] = f'=SUMPRODUCT(${SC[0]}{r}:${SC[-1]}{r},{HELP["icf"]})'
    for col, f in row.items():
        we[f'{col}{r}'] = f
EEND = E0 + N - 1
for col in ['F', 'G', 'H', 'I', 'J', 'K'] + SC + [KS, RC['SPK'], RC['CBC'], RC['CBB'], RC['CBCH'], RC['CBNC'], RC['CAP'], RC['BANK'], RC['PRAW'], RC['PPAID'], RC['PBANK'], RC['COST'], RC['ICF'], P1R, P2R]:
    for r in range(E0, EEND + 1):
        we[f'{col}{r}'].number_format = AMD
for col in EV + [EVB, EVP1, EVP2, KTH]:
    for r in range(E0, EEND + 1):
        we[f'{col}{r}'].number_format = '#,##0.00'
for r in range(E0, EEND + 1):
    we[f'E{r}'].number_format = '0.00'
    we[f'{RC["CAPHIT"]}{r}'].number_format = '0.00'
we.freeze_panes = f'D{E0}'


def ER(col):
    return f'Engine!${col}${E0}:${col}${EEND}'


# ================================================================== Results
wr = ws_new('Results', 'FFC000', {'A': 2, 'B': 56, 'C': 14, 'D': 15, 'E': 15, 'F': 15, 'G': 15, 'H': 15, 'I': 50})
put(wr, 'B1', 'RESULTS – monthly, scaled to the August 2026 active client base', f_title)
put(wr, 'B2', 'Weighted sums over the Engine rows (weight = population / sample in each tier). Green rows are the numbers that feed the tier model.', f_note)
RT = ['D', 'E', 'F', 'G']
header(wr, 4, ['B', 'C'] + RT + ['H', 'I'], ['Metric', 'Unit', *TIERS, 'Total', 'Note'])
mask = lambda t: f'({ER("C")}="{t}")'                                  # noqa: E731
res_rows = {}
MAXM = 10           # ceiling on the multiplier: beyond ×10 the typed rates make no sense (target unreachable under the cap)
NEWTON = 6          # Newton steps for the capped multiplier (cost is concave in m, so steps approach the target from below)


def newton(t, k):
    x = f'{{{{m{k - 1}}}}}*{ER(RC["CBCH"])}'
    cap = ER(RC['CAP'])
    val = f'SUMPRODUCT({mask(t)}*{ER("E")}*({x}-({x}>{cap})*({x}-{cap})))'
    der = f'SUMPRODUCT({mask(t)}*{ER("E")}*({x}<={cap})*{ER(RC["CBCH"])})'
    return f'=IFERROR({{{{m{k - 1}}}}}+({{{{tgt}}}}*{{{{nc}}}}-{{{{fixed}}}}-{{{{sshare}}}}*{val})/({{{{sshare}}}}*{der}),{{{{m{k - 1}}}}})'
spec = [
    ('clients', 'Active clients (card spend in the month)', '#', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")})', AMD0, 'sum'),
    ('total', 'Total card spend', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER("F")})', AMD, 'sum'),
    ('cash', '  cash withdrawals', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER("G")})', AMD, 'sum'),
    ('gamb', '  gambling', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER("H")})', AMD, 'sum'),
    ('excl', '  other excluded (transfers, e-wallets, quasi-cash, government, utilities, telecom…)', 'AMD',
     lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*({ER("I")}-{ER("G")}-{ER("H")}))', AMD, 'sum'),
    ('elig', 'Eligible spend', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER("K")})', AMD, 'sum'),
    ('nc', 'Non-cash spend (model basis: everything except ATM / counter cash)', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER("J")})', AMD, 'sum'),
    ('eshare', 'Eligible share of non-cash spend', '%', lambda t: f'=IFERROR({{elig}}/{{nc}},0)', PCT, 'ratio:elig/nc'),
    ('bank', 'Bank cashback (categories + base, after cap)', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["BANK"])})', AMD, 'sum'),
    ('pbank', 'Partner offers: bank-funded part', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["PBANK"])})', AMD, 'sum'),
    ('cost', 'TOTAL BANK COST', 'AMD', lambda t: '={bank}+{pbank}', AMD, 'sum'),
    ('pfund', 'Partner offers: partner-funded part (not a bank cost)', 'AMD',
     lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["PPAID"])})-{{pbank}}', AMD, 'sum'),
    ('eff_el', 'Effective rate on eligible spend (bank cost)', '%', lambda t: '=IFERROR({cost}/{elig},0)', PCT2, 'ratio:cost/elig'),
    ('eff_nc', 'Effective rate on non-cash spend (bank cost) → model', '%', lambda t: '=IFERROR({cost}/{nc},0)', PCT2, 'ratio:cost/nc'),
    ('eff_cl', 'Client-perceived rate on eligible spend (bank + partner)', '%', lambda t: '=IFERROR(({cost}+{pfund})/{elig},0)', PCT2, 'ratio:(cost+pfund)/elig'),
    ('tgt', 'Model target (Inputs, % of non-cash)', '%', lambda t: f'=Inputs!{RT[TIERS.index(t)]}${PR["tgt"]}', PCT2, 'none'),
    ('gap', 'Engine minus target', 'p.p.', lambda t: '={eff_nc}-{tgt}', PCT2, 'none'),
    ('meff', 'Menu rate multiplier in use (Inputs: auto-scaled to the target, or manual)', 'x',
     lambda t: f'=Inputs!{RT[TIERS.index(t)]}${PR["meff"]}', X, 'none'),
    ('caphit', 'Clients hitting the bank cap', '%', lambda t: f'=IFERROR(SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["CAPHIT"])})/{{clients}},0)', PCT, 'none'),
    ('avg', 'Average bank cost per active client', 'AMD', lambda t: '=IFERROR({cost}/{clients},0)', AMD, 'ratio:cost/clients'),
    ('icf', 'Issuer interchange on eligible spend', 'AMD', lambda t: f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["ICF"])})', AMD, 'sum'),
    ('cover', 'Bank cost ÷ interchange on eligible spend', 'x', lambda t: '=IFERROR({cost}/{icf},0)', X, 'ratio:cost/icf'),
    ('annual', 'Annual bank cost (month × 12)', 'AMD', lambda t: f'={{cost}}*{g["months"]}', AMD, 'sum'),
    ('sshare', 'Scaling: share of clients on menu rates (choosers; all clients if non-choosers auto-pick)', '%',
     lambda t: f'=IF(Inputs!{RT[TIERS.index(t)]}${PR["ncrule"]}="Auto-pick",1,1-Inputs!{RT[TIERS.index(t)]}${PR["q"]})', PCT, 'none'),
    ('scal', 'Scaling: menu cashback at ×1 rates, before cap', 'AMD',
     lambda t: f'={{sshare}}*SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["CBCH"])})', AMD, 'sum'),
    ('fixed', 'Scaling: cost that is not scaled (non-chooser flat rate + bank share of partner offers)', 'AMD',
     lambda t: f'=Inputs!{RT[TIERS.index(t)]}${PR["q"]}*SUMPRODUCT({mask(t)}*{ER("E")}*{ER(RC["NCCAP"])})+{{pbank}}', AMD, 'sum'),
    ('m0', 'Scaling: multiplier ignoring caps (first guess)', 'x',
     lambda t: '=IF({scal}>0,({tgt}*{nc}-{fixed})/{scal},0)', X, 'none'),
] + [
    (f'm{k}', f'Scaling: step {k} (Newton, with caps)', 'x', (lambda k: lambda t: newton(t, k))(k), X, 'none') for k in range(1, NEWTON + 1)
] + [
    ('automult', 'Scaling: multiplier that makes bank cost = target × non-cash', 'x', lambda t: f'=MIN({MAXM},MAX(0,{{m{NEWTON}}}))', X, 'none'),
    ('reach', 'Scaling check: target reached?', '', lambda t: (f'=IF(Inputs!{RT[TIERS.index(t)]}${PR["auto"]}<>"Yes","manual multiplier",'
        'IF({scal}=0,IF({tgt}=0,"target 0%: no cashback","no menu rates to scale"),IF(ABS({eff_nc}-{tgt})<0.00005,"Yes",IF({eff_nc}<{tgt},"No: caps bind – raise the cap or lower the target",'
        '"No: flat rate + partner offers alone exceed the target"))))'), None, 'none'),
]
for i, (k, *_ ) in enumerate(spec):
    res_rows[k] = 5 + i
for i, (k, lab, unit, fn, fmt, tot) in enumerate(spec):
    r = res_rows[k]
    bold = k in ('cost', 'eff_nc', 'eff_el')
    put(wr, f'B{r}', lab, bold=bold)
    put(wr, f'C{r}', unit, f_note)
    for c, t in zip(RT, TIERS):
        f = fn(t)
        f = f.replace('{{', '{').replace('}}', '}')
        f = f.format(**{kk: f'{c}{rr}' for kk, rr in res_rows.items()})
        put(wr, f'{c}{r}', f, fmt=fmt, fill=fill_out if k == 'eff_nc' else None, bold=bold)
    if tot == 'sum':
        put(wr, f'H{r}', f'=SUM(D{r}:G{r})', fmt=fmt, bold=bold)
    elif tot.startswith('ratio:'):
        expr = tot.split(':')[1]
        for kk, rr in sorted(res_rows.items(), key=lambda x: -len(x[0])):
            expr = expr.replace(kk, f'H{rr}')
        put(wr, f'H{r}', f'=IFERROR({expr},0)', fmt=fmt, bold=bold)
notes = {'eff_nc': 'Same basis as the model\'s cashback line (target rate × non-cash payments). Link this row to the Control panel.',
         'tgt': 'The model applies its target to non-cash spend including gambling, which is 50–60% of non-cash in every tier',
         'cover': '>1 means cashback costs more than the interchange it earns on eligible spend (the "interchange trap")',
         'meff': 'Auto: every category and base rate of the tier is multiplied by this so bank cost = target × non-cash (caps can keep it slightly below)',
         'm0': '(target × non-cash − cost not scaled) ÷ menu cashback at ×1',
         'automult': 'Solves: cost not scaled + Σ min(m × menu cashback, cap) = target × non-cash. 0 if the flat rate + partner offers alone cost more than the target; at most ×10 (then the cap makes the target unreachable)'}
for k, n in notes.items():
    put(wr, f'I{res_rows[k]}', n, f_note)
RE = 5 + len(spec)

# bridge: model target logic -> engine cost
B0 = RE + 2
put(wr, f'B{B0}', 'Bridge: why the engine costs less than the model target (monthly, AMD)', f_bold, fill=fill_sub)
header(wr, B0 + 1, ['B', 'C'] + RT + ['H', 'I'], ['Step', 'Unit', *TIERS, 'Total', 'Note'])
R = res_rows
bridge = [
    ('Model logic: target rate × all non-cash spend', 'AMD', '={c}{tgt}*{c}{nc}', 'What the tier model books today (rate × non-cash payments)'),
    ('  less: target rate × gambling spend', 'AMD', '=-{c}{tgt}*{c}{gamb}', 'Gambling earns no cashback (industry standard; ArCa state programme excludes it too)'),
    ('  less: target rate × other excluded non-cash spend', 'AMD', '=-{c}{tgt}*{c}{excl}', 'Transfers, e-wallet top-ups, quasi-cash / crypto, government, utilities, telecom, insurance, charity'),
    ('Subtotal: target rate × eligible spend', 'AMD', '={c}{tgt}*{c}{elig}', ''),
    ('  plus / less: menu design (rates, 4 picks, base option, non-choosers, caps)', 'AMD', '={c}{cost}-{c}{tgt}*{c}{elig}', 'Positive = the menu pays more than the target rate on eligible spend'),
    ('Result: engine bank cost', 'AMD', '={c}{cost}', ''),
    ('Rate on eligible spend that the model target implies', '%', '=IFERROR({c}{tgt}*{c}{nc}/{c}{elig},0)', 'Target × non-cash ÷ eligible spend: what the menu would have to pay to match the model'),
    ('Engine rate on eligible spend', '%', '={c}{eff_el}', ''),
]
for i, (lab, unit, f, note) in enumerate(bridge):
    r = B0 + 2 + i
    bold = lab.startswith(('Subtotal', 'Result', 'Model'))
    put(wr, f'B{r}', lab, bold=bold)
    put(wr, f'C{r}', unit, f_note)
    for c in RT:
        put(wr, f'{c}{r}', f.format(c=c, **{k: v for k, v in R.items()}), fmt=AMD if unit == 'AMD' else PCT2, bold=bold)
    if unit == 'AMD':
        put(wr, f'H{r}', f'=SUM(D{r}:G{r})', fmt=AMD, bold=bold)
    put(wr, f'I{r}', note, f_note)
BRIDGE_END = B0 + 2 + len(bridge)
r = BRIDGE_END + 1
put(wr, f'B{r}', 'Clients outside the programme (unknown card type or business card → no cashback)', f_bold, fill=fill_sub)
nc_mask = f'({ER("C")}<>"Free")*({ER("C")}<>"Black")*({ER("C")}<>"Premium")*({ER("C")}<>"Elite")'
for i, (lab, f, fmt) in enumerate([('Clients (card spend in August)', f'=SUMPRODUCT({nc_mask}*{ER("E")})', AMD0),
                                    ('Their total card spend, AMD per month', f'=SUMPRODUCT({nc_mask}*{ER("E")}*{ER("F")})', AMD),
                                    ('of which eligible for cashback if they were in a tier, AMD', f'=SUMPRODUCT({nc_mask}*{ER("E")}*{ER("K")})', AMD)]):
    put(wr, f'B{r + 1 + i}', lab)
    put(wr, f'D{r + 1 + i}', f, fmt=fmt)
put(wr, f'I{r + 1}', 'Cards issued before Aug-25 have no card type in Extract_client_DB; the data request asks for it', f_note)
BRIDGE_END = r + 4

# picks and cashback by category
r0 = BRIDGE_END + 2
put(wr, f'B{r0}', 'Share of choosing clients who pick each category', f_bold, fill=fill_sub)
header(wr, r0 + 1, ['B', 'C'] + RT, ['Category', 'Code', *TIERS])
for k, c in enumerate(PICKABLE + ['BASE', 'P1', 'P2']):
    r = r0 + 2 + k
    col = (PK + [PKB, PKP1, PKP2])[k]
    put(wr, f'B{r}', {**CAT_TXT, 'BASE': 'Base option (all purchases)', 'P1': 'Partner offer 1', 'P2': 'Partner offer 2'}[c])
    put(wr, f'C{r}', c)
    for cc_, t in zip(RT, TIERS):
        put(wr, f'{cc_}{r}', f'=IFERROR(SUMPRODUCT({mask(t)}*{ER("E")}*{ER(col)})/{cc_}${res_rows["clients"]},0)', fmt=PCT)
r1 = r0 + 2 + NPK + 3 + 2
put(wr, f'B{r1}', 'Eligible spend by category (AMD per month) and share of clients spending', f_bold, fill=fill_sub)
header(wr, r1 + 1, ['B', 'C'] + RT + ['H'], ['Category', 'Code', *TIERS, 'Total'])
for k, c in enumerate(ELIGIBLE):
    r = r1 + 2 + k
    put(wr, f'B{r}', CAT_TXT[c]); put(wr, f'C{r}', c)
    for cc_, t in zip(RT, TIERS):
        put(wr, f'{cc_}{r}', f'=SUMPRODUCT({mask(t)}*{ER("E")}*{ER(SC[k])})', fmt=AMD)
    put(wr, f'H{r}', f'=SUM(D{r}:G{r})', fmt=AMD)
wr.freeze_panes = 'D5'

# ================================================================== Profiles (values)
wp = ws_new('Profiles', '5B9BD5', {'A': 2, 'B': 40, 'C': 14, 'D': 16, 'E': 16, 'F': 16, 'G': 16, 'H': 16, 'I': 16, 'J': 14, 'K': 40})
put(wp, 'B1', 'SPEND PROFILES (values from the full extract, not the sample)', f_title)
put(wp, 'B2', 'Source: SPEND BY MCC.csv (Aug-25 – Aug-26, client × card × MCC × month) joined to card type from Extract_client_DB on client_id (match validated: Spearman 0.73 with debit turnover).', f_note)
r = 4
put(wp, f'B{r}', '1. Monthly trend (all clients)', f_bold, fill=fill_sub)
header(wp, r + 1, list('BCDEFGH'), ['Month', 'Clients', 'Total card spend', 'Cash', 'Gambling', 'Eligible', 'Eligible share of total'])
mt = prof['months']
for i, (m, rw) in enumerate(mt.iterrows()):
    rr = r + 2 + i
    put(wp, f'B{rr}', m)
    for col, v, fmt in [('C', rw.clients, AMD0), ('D', rw.total, AMD), ('E', rw.cash, AMD), ('F', rw.gamb, AMD), ('G', rw.eligible, AMD)]:
        put(wp, f'{col}{rr}', float(v), fmt=fmt)
    put(wp, f'H{rr}', f'=IFERROR(G{rr}/D{rr},0)', fmt=PCT)
r = r + 3 + len(mt)
put(wp, f'B{r}', '2. By card type, August 2026', f_bold, fill=fill_sub)
header(wp, r + 1, list('BCDEFGHIJ'), ['Card type', 'Clients', 'Total card spend', 'Cash', 'Gambling', 'Other excluded', 'Eligible', 'Eligible per client', 'Gambling share of non-cash'])
ca = prof['card_aug'].sort_values('clients', ascending=False)
for i, (ct, rw) in enumerate(ca.iterrows()):
    rr = r + 2 + i
    put(wp, f'B{rr}', ct)
    for col, v in zip('CDEFGH', [rw.clients, rw.total, rw.X_CASH, rw.X_GAMB, rw.X_other, rw.eligible]):
        put(wp, f'{col}{rr}', float(v), fmt=AMD)
    put(wp, f'I{rr}', f'=IFERROR(H{rr}/C{rr},0)', fmt=AMD)
    put(wp, f'J{rr}', f'=IFERROR(F{rr}/(D{rr}-E{rr}),0)', fmt=PCT)
r = r + 3 + len(ca)
put(wp, f'B{r}', '3. By tier, August 2026 (unknown card types shown separately)', f_bold, fill=fill_sub)
header(wp, r + 1, list('BCDEFGHIJK'), ['Tier', 'Clients', 'Eligible per client P25', 'P50', 'P75', 'P90', 'P99', 'Avg categories per client', 'Top category share (median)', 'Eligible share of non-cash'])
ta = prof['tier_aug']
for i, t in enumerate([x for x in ta.index]):
    rr = r + 2 + i
    put(wp, f'B{rr}', t)
    put(wp, f'C{rr}', float(ta.loc[t, 'clients']), fmt=AMD0)
    dist = prof['dist'].loc[t] if t in prof['dist'].index else None
    for col, qv in zip('DEFGH', [.25, .5, .75, .9, .99]):
        put(wp, f'{col}{rr}', float(dist[qv]) if dist is not None else 0, fmt=AMD)
    put(wp, f'I{rr}', float(prof['ncat'].get(t, 0)), fmt='0.0')
    put(wp, f'J{rr}', float(prof['topshare'].get(t, 0)), fmt=PCT)
    put(wp, f'K{rr}', float(ta.loc[t, 'eligible'] / max(1, ta.loc[t, 'total'] - ta.loc[t, 'X_CASH'])), fmt=PCT)
r = r + 3 + len(ta)
put(wp, f'B{r}', "4. Model reference, Q4 2025 ('Cards model as at late 25') – used for channel and transaction estimates", f_bold, fill=fill_sub)
header(wp, r + 1, list('BCDEF'), ['Card type', 'International share of non-cash', 'Transactions per card per month', 'Non-cash per card per month', 'Average ticket'])
ref = [('ArCa Classic', 0.0, 5.12, 33783), ('Mastercard World', 41608534 / (190405113 + 41608534), 16.03, 102258 + 22346),
       ('Mastercard World Elite', 12440099 / (10295538 + 12440099), 9.80, 56056 + 67732), ('Visa Classic', 88772339 / (854255545 + 88772339), 13.20, 74156 + 7706),
       ('Visa Gold', 111730476 / (1232274726 + 111730476), 12.07, 71465 + 6480), ('Visa Infinite', 111073837 / (262820138 + 111073837), 28.15, 263964 + 111557),
       ('Visa Infinite Metal', 30472393 / (55055890 + 30472393), 46.43, 500508 + 277022), ('Visa Digital', 23379361 / (202941019 + 23379361), 3.37, 22974 + 2647)]
for i, (ct, ish, trx, ncpc) in enumerate(ref):
    rr = r + 2 + i
    put(wp, f'B{rr}', ct); put(wp, f'C{rr}', ish, fmt=PCT); put(wp, f'D{rr}', trx, fmt='0.0'); put(wp, f'E{rr}', ncpc, fmt=AMD)
    put(wp, f'F{rr}', f'=IFERROR(E{rr}/D{rr},0)', fmt=AMD)
put(wp, f'B{r + 11}', 'No transaction counts or channel flag in the MCC extract: the engine uses the foreign-share estimates on the Categories sheet and an optional minimum-transaction haircut (Inputs).', f_note)

# ================================================================== Client data (all August clients, long format)
wcd = ws_new('Client data', '808080', {'A': 12, 'B': 8, 'C': 16, 'D': 3, 'E': 12, 'F': 34})
header(wcd, 1, ['A', 'B', 'C', 'E', 'F'], ['Client ID', 'MCC', 'Card spend Aug-26, AMD', 'Client ID', 'Card type'])
for i, (cid, mcc, amt) in enumerate(clong[['client_id', 'mcc', 'txn_volume_amd']].itertuples(index=False)):
    wcd.cell(2 + i, 1, int(cid)); wcd.cell(2 + i, 2, mcc); wcd.cell(2 + i, 3, round(float(amt), 2))
for i, (cid, ct) in enumerate(ctypes[['client_id', 'card_type']].itertuples(index=False)):
    wcd.cell(2 + i, 5, int(cid)); wcd.cell(2 + i, 6, ct)
CL_END, CT_END = 1 + len(clong), 1 + len(ctypes)
CD_ID, CD_MCC, CD_AMT = f"'Client data'!$A$2:$A${CL_END}", f"'Client data'!$B$2:$B${CL_END}", f"'Client data'!$C$2:$C${CL_END}"
CT_IDS, CT_RNG = f"'Client data'!$E$2:$E${CT_END}", f"'Client data'!$E$2:$F${CT_END}"
wcd.freeze_panes = 'A2'
# default client for the Client view: a Visa Gold client with a varied basket
elig_codes = {m for m in clong.mcc.unique() if not lookup(m)[2].startswith('X_')}
cand = clong[clong.mcc.isin(elig_codes)].groupby('client_id').agg(n=('mcc', 'nunique'), s=('txn_volume_amd', 'sum'))
cand = cand.join(ctypes.set_index('client_id'))
pick = cand[(cand.card_type == 'Visa Gold') & (cand.n >= 5) & cand.s.between(150000, 400000)].sort_values('n', ascending=False)
DEFAULT_CID = int(pick.index[0]) if len(pick) else int(ctypes.client_id.iloc[0])

# ================================================================== Client view
PERSONAS = [
    ('Anna – everyday shopper', 'Black', 'ArCa Classic, 34, Yerevan. Groceries near home, coffee on the go, metro and some taxi; takes cash for the market.',
     {'5411': 60000, '5814': 8000, '4789': 1500, '4121': 6000, '5172': 15000, '6011': 60000, '4814': 3000}),
    ('Davit – young & digital', 'Free', 'Visa Digital, 24. Lives in apps: fast food, delivery, taxi, mobile games; bets on football and tops up e-wallets.',
     {'5814': 15000, '4121': 12000, '5812': 12000, '5411': 12000, '4215': 4000, '5816': 3000, '7995': 40000, '6540': 20000}),
    ('Petrosyan family – car & household', 'Premium', 'Visa Gold, family of four with a car. Big supermarket shop, fuel, pharmacy, kids\' clothes, one appliance; pays utilities by card.',
     {'5411': 150000, '5172': 40000, '5812': 25000, '5814': 10000, '5722': 30000, '5912': 15000, '5641': 12000, '4900': 20000, '6011': 80000}),
    ('Mariam – affluent traveller', 'Elite', 'Visa Infinite, business owner. Restaurants and bars, flies monthly (flights, hotels), taxi, jewelry and cosmetics.',
     {'5812': 120000, '5813': 30000, '7011': 250000, '4511': 180000, '4121': 25000, '5411': 90000, '5944': 60000, '5977': 20000, '6011': 100000}),
    ('Aram – bettor, mostly cash', 'Black', 'Visa Classic. Most card turnover is betting, cash and e-wallet top-ups; little everyday spend.',
     {'7995': 300000, '6011': 200000, '6051': 50000, '6540': 40000, '5411': 15000, '5814': 5000}),
]
EXTRA = {'5912', '5641', '5977', '5813', '5816', '5651', '5661', '5399', '7230', '7832', '8099', '8021', '5945', '5200', '5311', '5999'}
CV_MCCS = sorted(set(MCCS) | set(clong.mcc) | EXTRA | {m for p in PERSONAS for m in p[3]})
N_FREE = 12                                                             # blank rows for any other MCC
wv = ws_new('Client view', '00B0F0', {'A': 2, 'B': 50, 'C': 16, 'D': 14, 'E': 16, 'F': 13, 'G': 11, 'H': 14, 'I': 9, 'J': 14, 'K': 13, 'L': 14,
                                       'M': 8, 'N': 36, 'O': 9, 'P': 14, 'Q': 13, 'R': 14, 'S': 3, 'T': 16, 'U': 16, 'V': 16, 'W': 16, 'X': 16, 'Y': 3, 'Z': 30})
put(wv, 'B1', 'CLIENT VIEW – what one client is shown, what they pick and what they earn this month', f_title)
put(wv, 'B2', 'Choose a persona, a real client by bank client ID, or "Custom". To change spend, type amounts in column R of the MCC table on the right '
              '(any MCC; empty rows at the bottom take new MCC codes). Tables 2–5 recalculate – do not type into them. Same rules as the Engine sheet.', f_note)
wv.merge_cells('B2:K3')
wv['B2'].alignment = Alignment(wrap_text=True, vertical='top')
PN, PT, PD = '$T$4:$X$4', '$T$3:$X$3', '$T$2:$X$2'
put(wv, 'T1', 'Persona definitions (editable: tier, name, monthly spend by MCC)', f_bold)
for i, (name, tier, desc, spend) in enumerate(PERSONAS):
    col = 'TUVWX'[i]
    put(wv, f'{col}2', desc, f_note, align=Alignment(wrap_text=True, vertical='top'))
    inp(wv, f'{col}3', tier)
    inp(wv, f'{col}4', name)
    wv[f'{col}4'].alignment = Alignment(wrap_text=True)
wv.row_dimensions[2].height = 64
wv.row_dimensions[4].height = 30
put(wv, 'Z3', 'Selector list', f_note)
for i in range(5):
    put(wv, f'Z{4 + i}', f'={"TUVWX"[i]}4', f_note)
put(wv, 'Z9', 'Client ID', f_note)
put(wv, 'Z10', 'Custom', f_note)
# MCC table (M..R)
MV0 = 6
header(wv, MV0 - 1, list('MNOPQR'), ['MCC', 'Plain name', 'Category', 'Spend from selection', 'Spend used', 'Your amount (edit)'])
rows_mcc = CV_MCCS + [None] * N_FREE
for i, m in enumerate(rows_mcc):
    r = MV0 + i
    if m is None:
        inp(wv, f'M{r}', None)
        put(wv, f'N{r}', f'=IF(M{r}="","← type any MCC",IFERROR(VLOOKUP(TEXT(M{r},"0000"),MCC_map!$A$5:$C${MM_END},3,FALSE),"MCC not in MCC_map – counts as Other"))', f_note)
    else:
        put(wv, f'M{r}', m, align=Alignment(horizontal='center'))
        put(wv, f'N{r}', lookup(m)[1])
    put(wv, f'O{r}', f'=IF(M{r}="","",IFERROR(VLOOKUP(TEXT(M{r},"0000"),MCC_map!$A$5:$D${MM_END},4,FALSE),"OTH"))', f_link, align=Alignment(horizontal='center'))
    put(wv, f'P{r}', f'=IF(OR(M{r}="",$C$5="Custom"),0,IF($C$5="Client ID",SUMIFS({CD_AMT},{CD_ID},$C$6,{CD_MCC},TEXT(M{r},"0000")),'
                      f'IFERROR(INDEX($T{r}:$X{r},MATCH($C$5,{PN},0)),0)))', fmt=AMD)
    put(wv, f'Q{r}', f'=IF(R{r}<>"",R{r},P{r})', fmt=AMD, bold=True)
    inp(wv, f'R{r}', None, AMD)
    for j, (name, tier, desc, spend) in enumerate(PERSONAS):
        inp(wv, f'{"TUVWX"[j]}{r}', spend.get(m) if m else None, AMD)
MV1 = MV0 + len(rows_mcc) - 1
MCAT, MSP = f'$O${MV0}:$O${MV1}', f'$Q${MV0}:$Q${MV1}'
put(wv, f'M{MV1 + 2}', 'Column Q is what the engine uses: your amount in column R if you typed one, otherwise the selected client / persona. Clear R to go back. '
                       'Do not list the same MCC twice.', f_note)

# 1. selector
put(wv, 'B4', '1. Choose a client', f_bold, fill=fill_sub)
sel = [('Who', PERSONAS[0][0]), ('Client ID (bank client_id, any client with card spend in August 2026)', DEFAULT_CID),
       ('Tier override (optional)', None), ('Tier used', None), ('Does the client pick categories this month?', 'Chooses'), ('About this client', None)]
for i, (lab, v) in enumerate(sel):
    r = 5 + i
    put(wv, f'B{r}', lab)
    if lab in ('Tier used', 'About this client'):
        continue
    inp(wv, f'C{r}', v)
ctype = f'IFERROR(VLOOKUP($C$6,{CT_RNG},2,FALSE),"")'
wv['C8'] = (f'=IF(C7<>"",C7,IF(C5="Client ID",IFERROR(VLOOKUP({ctype},{MAP_RNG},2,FALSE),{g["unk"]}),'
            f'IF(C5="Custom","Black",IFERROR(INDEX({PT},MATCH(C5,{PN},0)),"Black"))))')
wv['C8'].font = f_bold
wv['D8'] = f'=IFERROR(MATCH(C8,Inputs!$D${R0}:$G${R0},0),0)'
wv['D8'].font = f_note
wv['E8'] = '=IF(D8=0,"→ no cashback for this client (unknown card type or business card)","")'
put(wv, 'B11', 'Menu rates of this tier are scaled by (auto = hits the Control panel target)')
wv['C11'] = f'=IF($D$8=0,"",INDEX(Inputs!$D${PR["meff"]}:$G${PR["meff"]},$D$8))'
wv['C11'].number_format = X
wv['C11'].font = f_bold
wv['E8'].font = f_note
wv['C10'] = (f'=IF(C5="Client ID",IF(ISNA(MATCH($C$6,{CT_IDS},0)),"Client ID not found in August 2026 card spend",'
             f'"Client "&$C$6&" – card type: "&{ctype}&" – August 2026 card spend"),'
             f'IF(C5="Custom","Your own spend profile – type monthly amounts by MCC in column R",IFERROR(INDEX({PD},MATCH(C5,{PN},0)),"")))')
wv['C10'].font = f_note
wv['C10'].alignment = Alignment(wrap_text=True, vertical='top')
wv.merge_cells('C10:J10')
wv.row_dimensions[10].height = 30
for ref, lst in [('C5', '=$Z$4:$Z$10'), ('C7', '"Free,Black,Premium,Elite"'), ('C9', '"Chooses,Does not choose"')]:
    d = DataValidation(type='list', formula1=lst, allow_blank=True); wv.add_data_validation(d); d.add(ref)

# 2. spend summary
put(wv, 'B12', '2. Card spend this month', f_bold, fill=fill_sub)
spend_rows = [('Total card spend', f'=SUM({MSP})'), ('  cash withdrawals (no cashback)', f'=SUMIF({MCAT},"X_CASH",{MSP})'),
              ('  gambling (no cashback)', f'=SUMIF({MCAT},"X_GAMB",{MSP})'),
              ('  other excluded: transfers, e-wallets, quasi-cash, bills, government…', f'=SUMIF({MCAT},"X_*",{MSP})-C14-C15'),
              ('Eligible for cashback', f'=C13-SUMIF({MCAT},"X_*",{MSP})')]
for i, (lab, f) in enumerate(spend_rows):
    put(wv, f'B{13 + i}', lab, bold=(i in (0, 4)))
    put(wv, f'C{13 + i}', f, fmt=AMD, bold=(i in (0, 4)))

# 4. detail table (rows 36..)
DT0 = 36
tp = lambda key: f'INDEX(Inputs!$D${PR[key]}:$G${PR[key]},$D$8)'            # noqa: E731
hh = f"(1-{tp('hair')})"
put(wv, f'B{DT0 - 2}', '4. How the engine gets there (calculated – same rules as the Engine sheet)', f_bold, fill=fill_sub)
header(wv, DT0 - 1, list('BCDEFGHIJKL'), ['Option', 'Code', 'Client\'s spend', 'Menu role (tier)', 'Rate shown (× multiplier)', 'On the menu?', 'Ranking key (menu rates ×1)', 'Picked', 'Cashback', 'Issuer interchange', 'Expected cashback (rates shown)'])
for k, c in enumerate(PICKABLE):
    r = DT0 + k
    put(wv, f'B{r}', CAT_TXT[c]); put(wv, f'C{r}', c, align=Alignment(horizontal='center'))
    put(wv, f'D{r}', f'=SUMIF({MCAT},C{r},{MSP})', fmt=AMD)
    put(wv, f'E{r}', f'=IF($D$8=0,"",IF(INDEX({HELP["hidden"]},$D$8,{k + 1})=1,"Partner offer instead",INDEX(Inputs!$H${CR0 + 1}:$K${CR_END},{k + 1},$D$8)))',
        align=Alignment(horizontal='center'))
    put(wv, f'F{r}', f'=IF($D$8=0,0,INDEX({HELP["rate"]},$D$8,{k + 1})*{tp("meff")})', fmt=PCT2)
    put(wv, f'G{r}', f'=IF(OR(E{r}="Always",AND(E{r}="If spent",D{r}>0,D{r}>=$D${DT0 + 25})),"Yes","")', align=Alignment(horizontal='center'))
    put(wv, f'H{r}', f'=IF(G{r}="Yes",INDEX({HELP["rate"]},$D$8,{k + 1})*D{r}*{hh}+{NPK - k}*1E-6,0)', fmt='#,##0.00')
    put(wv, f'L{r}', f'=IF(G{r}="Yes",F{r}*D{r}*{hh},0)', fmt=AMD)
    put(wv, f'I{r}', f'=IF(AND(H{r}>=$D${DT0 + 26},H{r}>0.001),"✓","")', f_bold, align=Alignment(horizontal='center'))
    put(wv, f'J{r}', f'=IF(I{r}="✓",F{r}*D{r}*{hh},0)', fmt=AMD)
    put(wv, f'K{r}', f'=D{r}*INDEX(Categories!$J$5:$J${4 + len(ELIGIBLE)},{ELIGIBLE.index(c) + 1})', fmt=AMD)
rb = DT0 + NPK            # base
put(wv, f'B{rb}', 'Base option: all other eligible purchases'); put(wv, f'C{rb}', 'BASE', align=Alignment(horizontal='center'))
put(wv, f'D{rb}', '=C17', fmt=AMD)
put(wv, f'E{rb}', f'=IF($D$8=0,"",{tp("bmode")})', align=Alignment(horizontal='center'))
put(wv, f'F{rb}', f'=IF($D$8=0,0,{tp("brate")}*{tp("meff")}*{tp("active")})', fmt=PCT2)
put(wv, f'G{rb}', f'=IF(AND($D$8>0,E{rb}<>"Off",F{rb}>0),"Yes","")', align=Alignment(horizontal='center'))
_top = (f'IF({tp("picks")}<2,0,SUMPRODUCT(($H${DT0}:$H${DT0 + NPK - 1}>=LARGE(($H${DT0}:$H${DT0 + NPK - 1},$H${rb + 1}:$H${rb + 2}),{tp("picks")}-1))'
        f'*($H${DT0}:$H${DT0 + NPK - 1}>0.001)*$D${DT0}:$D${DT0 + NPK - 1}))')
put(wv, f'H{rb}', f'=IF(E{rb}="Pickable",{tp("brate")}*{tp("active")}*(D{rb}-{_top})*{hh},0)', fmt='#,##0.00')
put(wv, f'L{rb}', f'=IF(G{rb}="Yes",F{rb}*(D{rb}-{_top})*{hh},0)', fmt=AMD)
put(wv, f'I{rb}', f'=IF(E{rb}="Pickable",IF(AND(H{rb}>=$D${DT0 + 26},H{rb}>0.001),"✓",""),IF(AND(E{rb}="Automatic",F{rb}>0),"auto",""))', f_bold, align=Alignment(horizontal='center'))
put(wv, f'J{rb}', f'=IF(OR(I{rb}="✓",I{rb}="auto"),F{rb}*(D{rb}-SUMIF(I{DT0}:I{DT0 + NPK - 1},"✓",D{DT0}:D{DT0 + NPK - 1}))*{hh},0)', fmt=AMD)
for j in range(2):
    r = rb + 1 + j
    cat = f'INDEX(Inputs!$D${PRow[(j, "cat")]}:$G${PRow[(j, "cat")]},$D$8)'
    cov = f'INDEX(Inputs!$D${PRow[(j, "cov")]}:$G${PRow[(j, "cov")]},$D$8)'
    nm = f'INDEX(Inputs!$D${PRow[(j, "name")]}:$G${PRow[(j, "name")]},$D$8)'
    put(wv, f'B{r}', f'=IF($D$8=0,"Partner offer {j + 1}","Partner offer: "&{nm}&" ("&IFERROR(VLOOKUP({cat},Categories!$B$5:$C$40,2,FALSE),"")&", "&TEXT({cov},"0%")&" of that spend)")')
    put(wv, f'C{r}', f'=IF($D$8=0,"",{cat})', align=Alignment(horizontal='center'))
    put(wv, f'D{r}', f'=IF($D$8=0,0,IFERROR(INDEX($D${DT0}:$D${DT0 + NPK - 1},MATCH(C{r},$C${DT0}:$C${DT0 + NPK - 1},0)),0)*{cov})', fmt=AMD)
    put(wv, f'E{r}', 'Partner-funded', align=Alignment(horizontal='center'))
    put(wv, f'F{r}', f'=IF($D$8=0,0,INDEX(Inputs!$D${PRow[(j, "rate")]}:$G${PRow[(j, "rate")]},$D$8)*{tp("active")})', fmt=PCT)
    put(wv, f'G{r}', f'=IF(F{r}>0,"Yes","")', align=Alignment(horizontal='center'))
    put(wv, f'H{r}', f'=IF($D$8=0,0,IF({tp("pcomp")}="Yes",F{r}*D{r}*{hh}+IF(F{r}>0,{2 - j}*1E-7,0),0))', fmt='#,##0.00')
    put(wv, f'I{r}', f'=IF($D$8=0,"",IF({tp("pcomp")}="Yes",IF(AND(H{r}>=$D${DT0 + 26},H{r}>0.001),"✓",""),IF(F{r}*D{r}>0,"auto","")))', f_bold, align=Alignment(horizontal='center'))
    put(wv, f'J{r}', f'=IF(I{r}<>"",F{r}*D{r}*{hh},0)', fmt=AMD)
    put(wv, f'L{r}', f'=IF(G{r}="Yes",F{r}*D{r}*{hh},0)', fmt=AMD)
ro = rb + 3
put(wv, f'B{ro}', 'Other eligible purchases (earn only through the base option)'); put(wv, f'C{ro}', 'OTH', align=Alignment(horizontal='center'))
put(wv, f'D{ro}', f'=SUMIF({MCAT},"OTH",{MSP})', fmt=AMD)
put(wv, f'K{ro}', f'=D{ro}*INDEX(Categories!$J$5:$J${4 + len(ELIGIBLE)},{len(ELIGIBLE)})', fmt=AMD)
rk = DT0 + 25
put(wv, f'B{rk}', 'Menu threshold: smallest spend that still gets an "If spent" slot')
put(wv, f'D{rk}', f'=IF($D$8=0,0,IF({tp("slots")}<1,9E+99,_xlfn.AGGREGATE(14,6,$D${DT0}:$D${DT0 + NPK - 1}*($E${DT0}:$E${DT0 + NPK - 1}="If spent"),{tp("slots")})))', fmt=AMD)
put(wv, f'E{rk}', f'=IF($D$8=0,"","("&{tp("slots")}&" personalised slots + "&COUNTIF($E${DT0}:$E${DT0 + NPK - 1},"Always")&" bank-chosen)")', f_note)
put(wv, f'B{rk + 1}', 'Pick threshold: expected cashback of the last option the client picks')
put(wv, f'D{rk + 1}', f'=IF($D$8=0,0,LARGE($H${DT0}:$H${rb + 2},{tp("picks")}))', fmt='#,##0.00')
put(wv, f'E{rk + 1}', f'=IF($D$8=0,"","(client picks "&{tp("picks")}&" options)")', f_note)
assert rk == ro + 2

# 3. app view (rows 20..31)
AV0 = 21
put(wv, 'B19', '3. What the app shows – menu options, best first for this client', f_bold, fill=fill_sub)
header(wv, 20, list('BCDEF'), ['Option on the menu', 'Headline rate', 'Client\'s spend here', 'Expected cashback', 'Picked?'])
HR = f'$H${DT0}:$H${rb + 2}'
for n in range(1, 11):
    r = AV0 + n - 1
    key = f'LARGE({HR},{n})'
    pos = f'MATCH({key},{HR},0)'
    put(wv, f'B{r}', f'=IFERROR(IF(INDEX($G${DT0}:$G${rb + 2},{pos})="Yes",{n}&". "&INDEX($B${DT0}:$B${rb + 2},{pos}),""),"")')
    put(wv, f'C{r}', f'=IF(B{r}="","",INDEX($F${DT0}:$F${rb + 2},{pos}))', fmt=PCT, align=Alignment(horizontal='center'))
    put(wv, f'D{r}', f'=IF(B{r}="","",INDEX($D${DT0}:$D${rb + 2},{pos}))', fmt=AMD)
    put(wv, f'E{r}', f'=IF(B{r}="","",ROUND(INDEX($L${DT0}:$L${rb + 2},{pos}),0))', fmt=AMD)
    put(wv, f'F{r}', f'=IF(B{r}="","",INDEX($I${DT0}:$I${rb + 2},{pos}))', f_bold, align=Alignment(horizontal='center'))
put(wv, f'B{AV0 + 10}', 'Options with zero value (e.g. a bank-chosen category the client never uses) still sit on the menu; the client picks the ones that pay most. '
                        'A category with a partner offer appears once – as the partner offer (switch on Inputs).', f_note)
wv.merge_cells(f'B{AV0 + 10}:J{AV0 + 11}')
wv[f'B{AV0 + 10}'].alignment = Alignment(wrap_text=True, vertical='top')

# 5. result
R5 = rk + 3
put(wv, f'B{R5}', '5. Cashback this month', f_bold, fill=fill_sub)
res5 = [
    ('Cashback on picked categories', f'=SUM(J{DT0}:J{DT0 + NPK - 1})', AMD),
    ('Cashback from the base option', f'=J{rb}', AMD),
    ('If the client picks: total before cap', f'=IF($D$8=0,0,IF(C17>={tp("minsp")},C{R5 + 1}+C{R5 + 2},0))', AMD),
    ('If the client does not pick: flat rate on all eligible purchases (rule on Inputs)',
     f'=IF($D$8=0,0,IF(C17<{tp("minsp")},0,IF({tp("ncrule")}="Nothing",0,IF({tp("ncrule")}="Flat rate",{tp("ncrate")}*{tp("active")}*C17*{hh},C{R5 + 3}))))', AMD),
    ('Monthly cap (bank-funded)', f'=IF($D$8=0,0,{tp("cap")})', AMD),
    ('BANK CASHBACK PAID', f'=MIN(IF(C9="Chooses",C{R5 + 3},C{R5 + 4}),C{R5 + 5})', AMD),
    ('Cap reached?', f'=IF(IF(C9="Chooses",C{R5 + 3},C{R5 + 4})>C{R5 + 5},"Yes – "&TEXT(IF(C9="Chooses",C{R5 + 3},C{R5 + 4})-C{R5 + 5},"#,##0")&" AMD above the cap is not paid","No")', None),
    ('Partner-funded cashback paid (own cap)', f'=IF(C9="Chooses",MIN(J{rb + 1}+J{rb + 2},IF($D$8=0,0,{tp("pcap")})),0)', AMD),
    ('  of which funded by the bank', f'=IF($D$8=0,0,IF(J{rb + 1}+J{rb + 2}>0,C{R5 + 8}*(J{rb + 1}*(1-INDEX(Inputs!$D${PRow[(0, "fund")]}:$G${PRow[(0, "fund")]},$D$8))+J{rb + 2}*(1-INDEX(Inputs!$D${PRow[(1, "fund")]}:$G${PRow[(1, "fund")]},$D$8)))/(J{rb + 1}+J{rb + 2}),0))', AMD),
    ('TOTAL CASHBACK THE CLIENT RECEIVES', f'=C{R5 + 6}+C{R5 + 8}', AMD),
    ('TOTAL COST TO THE BANK', f'=C{R5 + 6}+C{R5 + 9}', AMD),
    ('Client-perceived rate on eligible spend', f'=IFERROR(C{R5 + 10}/C17,0)', PCT2),
    ('Bank cost as % of eligible spend', f'=IFERROR(C{R5 + 11}/C17,0)', PCT2),
    ('Bank cost as % of all non-cash spend (model basis)', f'=IFERROR(C{R5 + 11}/(C13-C14),0)', PCT2),
    ('Issuer interchange earned on eligible spend', f'=SUM(K{DT0}:K{DT0 + NPK - 1})+K{ro}', AMD),
    ('Bank cost ÷ interchange', f'=IFERROR(C{R5 + 11}/C{R5 + 15},0)', X),
]
for i, (lab, f, fmt) in enumerate(res5):
    r = R5 + 1 + i
    big = lab.isupper() or lab.startswith('TOTAL') or lab.startswith('BANK')
    put(wv, f'B{r}', lab, bold=big)
    put(wv, f'C{r}', f, fmt=fmt, bold=big, fill=fill_out if big else None)
from openpyxl.worksheet.formula import ArrayFormula
wv['B33'] = ArrayFormula('B33', f'="Picks this month: "&_xlfn.TEXTJOIN(", ",TRUE,IF($I${DT0}:$I${rb + 2}="✓",$B${DT0}:$B${rb + 2},""))')
wv['B33'].font = f_bold
wv.merge_cells('B33:J33')
R6 = R5 + len(res5) + 3
put(wv, f'B{R6}', '6. How this runs in production, every month', f_bold, fill=fill_sub)
steps = ['1. Month start – the engine builds each client\'s menu: bank-chosen categories + the client\'s own top categories (from last month\'s spend) + partner offers, with rates for the client\'s tier.',
         '2. The app shows the menu; the client picks 4 options. A client who does nothing gets the flat non-chooser rate (default 1%) on all eligible purchases.',
         '3. During the month – every cleared card transaction is mapped MCC → category; if the category is picked, cashback accrues at its rate until the monthly cap is reached.',
         '4. Month end – bank cashback is paid to the account; the partner-funded part is invoiced to partners. Next month starts again at step 1.',
         'Note: this prototype builds the menu from the SAME month\'s spend (perfect foresight), so it slightly overstates cost vs production, where clients pick before they spend.']
for i, t in enumerate(steps):
    put(wv, f'B{R6 + 1 + i}', t, f_note if t.startswith('Note') else f_norm)
wv.freeze_panes = 'C5'

# ================================================================== README
wrd = ws_new('README', '000000', {'A': 2, 'B': 120})
wb.move_sheet('README', offset=-len(wb.sheetnames) + 1)
lines = [
    ('CASHBACK ENGINE – EXCEL PROTOTYPE (v3, 24.09.2026)', f_title),
    ('Purpose: design and cost a T-Bank-style category cashback for Fast Bank debit cards, then hand the logic to IT for production (back end + front end).', f_norm),
    ('', f_norm),
    ('HOW THE ENGINE WORKS (one month, one client)', f_bold),
    ('1. Every card transaction is mapped MCC → cashback category (MCC_map). Cash, gambling, transfers / e-wallets, quasi-cash, government, utilities, telecom, insurance and charity earn nothing.', f_norm),
    ('2. Menu: each client sees up to 7 bank categories – "Always" categories chosen by the bank plus the client\'s own top-spend categories ("If spent") – and up to 2 partner-funded offers.', f_norm),
    ('3. Choice: the client picks 4 options with the highest expected reward (rate × own spend). The base "all purchases" rate is one of the options (T-Bank design since 2023).', f_norm),
    ('4. Cashback = rate × spend on picked categories + base rate on the rest (if base picked), capped per client per month. Partner offers have their own cap and are funded by the partner.', f_norm),
    ('5. A share of clients never chooses; they get the base rate only (or nothing / auto-pick, per Inputs). All results are expected values across choosers and non-choosers.', f_norm),
    ('6. Results aggregate the sample to the August 2026 client base by tier and compare the effective rate with the model target.', f_norm),
    ('', f_norm),
    ('SHEETS', f_bold),
    ('Inputs – every parameter (blue on yellow). Categories – the client-facing category list with interchange assumptions. MCC_map – MCC names and grouping (edit the Category column to regroup).', f_norm),
    ('Profiles – spend facts from the full extract. Data – sampled client × MCC spend (values). Engine – the calculation, one row per client. Results – totals, effective rates, picks, and the bridge from the model target to the engine cost.', f_norm),
    ('Client view – pick a persona, any real client by bank client ID (August 2026), or type your own MCC spend: shows the menu the client sees, the 4 picks, the cap and the cashback. Start here.', f_norm),
    ('Client data – August 2026 card spend by client and MCC for all clients (feeds the Client view "Client ID" option).', f_norm),
    ('', f_norm),
    ('LINK TO THE TIER MODEL', f_bold),
    ("The Control panel cashback target drives everything: with 'Scale menu rates to hit the Control panel target' = Yes (default), all category and base rates of a tier are multiplied so that bank cost = target × non-cash spend. Change the target and the menu rates, the Client view and the P&L move together.", f_norm),
    ("Results row 'Effective rate on non-cash spend (bank cost) → model' is on the same basis as the model's cashback line ('Control panel' cashback target × non-cash payments).", f_norm),
    ("Model targets are typed into Inputs (section C, from v8 'Control panel'). Results shows the gap and the rate multiplier that would hit the target.", f_norm),
    ('', f_norm),
    ('DATA AND PRIVACY', f_bold),
    ('SPEND BY MCC.csv (client × card × MCC × month, Aug-25 – Aug-26) + card type from Extract_client_DB (joined on client_id; balances NOT used).', f_norm),
    ('Data (engine sample) and Client data carry the bank client_id with monthly spend by MCC – no names, tax IDs, card or account numbers, balances or income. Keep the file internal.', f_norm),
    ('', f_norm),
    ('KNOWN LIMITATIONS OF v1', f_bold),
    ('• Source: full MCC extract received 24.09.2026 (391 MCCs, incl. pharmacies, clothing, cosmetics, medical, marketplaces).', f_norm),
    ('• 23% of August clients hold cards issued before Aug-25 and have no card type in Extract_client_DB; by default they get no cashback (Inputs, global setting).', f_norm),
    ('• Partner offers replace the bank category of the same kind on the menu (Inputs switch). Non-choosers get a flat rate on all eligible purchases (default 1%).', f_norm),
    ('• No channel, transaction count or merchant ID: foreign share and interchange are estimates (Categories); partner offers are modelled at category level with a coverage share.', f_norm),
    ('• Static month: no behaviour change yet (spend lift, deadweight, retention). The rational top-4 choice replaces a fitted choice model until pilot data exist.', f_norm),
    ('• Sample-based: ~6,900 clients; tier totals are within a few % of the full-population run (Python cross-check).', f_norm),
    ('', f_norm),
    ('COLOUR LEGEND', f_bold),
    ('Blue text on yellow = input. Black = formula. Green = link to another sheet. Green fill on Results = figure that feeds the tier model.', f_norm),
]
for i, (txt, ft) in enumerate(lines):
    put(wrd, f'B{2 + i}', txt, ft)
    wrd[f'B{2 + i}'].alignment = Alignment(wrap_text=True, vertical='top')

for c in TC:
    wi[f'{c}{PR["meff"]}'] = f'=IF({c}{PR["auto"]}="Yes",Results!{c}{res_rows["automult"]},{c}{PR["mult"]})'
    wi[f'{c}{PR["meff"]}'].number_format = X
    wi[f'{c}{PR["meff"]}'].font = f_bold
order = ['README', 'Inputs', 'Client view', 'Results', 'Categories', 'MCC_map', 'Profiles', 'Engine', 'Data', 'Client data']
if PREFIX:
    import re as _re
    names = order
    pat = _re.compile(r"(?<![\w'])(" + '|'.join(n for n in names if ' ' not in n) + r")!|'(" + '|'.join(n for n in names if ' ' in n) + r")'!")
    fix = lambda f: pat.sub(lambda m: "'" + PREFIX + (m.group(1) or m.group(2)) + "'!", f)   # noqa: E731
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if isinstance(v, str) and v.startswith('='):
                    c.value = fix(v)
                elif isinstance(v, ArrayFormula):
                    v.text = fix(v.text)
        for dvx in ws.data_validations.dataValidation:
            if dvx.formula1 and dvx.formula1.startswith('='):
                dvx.formula1 = fix(dvx.formula1)
    for n in names:
        wb[n].title = PREFIX + n
    order = [PREFIX + n for n in names]
wb._sheets = [wb[n] for n in order]
wb.active = 1
wb.save(OUT)
print('saved', OUT, 'rows', N, 'engine cols', RC['ICF'], 'result rows', res_rows)
