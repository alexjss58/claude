"""Build the 'Client profiles' and compact 'Cards dataset' tabs (model v14) as a small workbook for merge_into_model.py.

    python3 build_profiles.py <prep_dir> <out.xlsx>

prep_dir holds cards_compact.pkl from profiles_prep.py. Writes <out.xlsx> plus layout.json (cells the model links to).
Every figure on 'Client profiles' is a live formula over 'Cards dataset'; the mode comes from 'Control panel'!D3.
"""
import json
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

PREP, OUT = sys.argv[1:3]
df = pd.read_pickle(f'{PREP}/cards_compact.pkl')
N = len(df)
TIERS = ['Free', 'Black', 'Premium', 'Elite']
TC = ['C', 'D', 'E', 'F']                     # tier columns on 'Client profiles'
FONT = 'Aptos Narrow'
f_norm = Font(name=FONT, size=12)
f_bold = Font(name=FONT, size=12, bold=True)
f_title = Font(name=FONT, size=14, bold=True)
f_note = Font(name=FONT, size=12, italic=True, color='808080')
f_sub = Font(name=FONT, size=12, bold=True, italic=True)
f_link = Font(name=FONT, size=12, color='008000')
fill_hdr = PatternFill('solid', fgColor='D9E1F2')
fill_use = PatternFill('solid', fgColor='E2EFDA')
thin = Side(style='thin', color='A6A6A6')
b_bot = Border(bottom=thin)
AMD, CNT, MULT, PCT, DEC = '#,##0', '#,##0', '0.00"×"', '0%', '0.0'

wb = Workbook()
wp = wb.active
wp.title = 'Client profiles'
wd = wb.create_sheet('Cards dataset')

# ------------------------------------------------------------------ Cards dataset (compact, values only)
cols = list(df.columns)
for j, name in enumerate(cols, 1):
    c = wd.cell(row=1, column=j, value=name)
    c.font = f_bold
    c.fill = fill_hdr
    c.alignment = Alignment(wrap_text=True, vertical='top')
fmt = {name: (DEC if 'transactions, #' in name.lower() and '/ month' in name else (CNT if '#' in name else AMD)) for name in cols}
for i, row in enumerate(df.itertuples(index=False), 2):
    for j, v in enumerate(row, 1):
        c = wd.cell(row=i, column=j, value=(None if (isinstance(v, float) and pd.isna(v)) else v))
        if j > 4:
            c.number_format = fmt[cols[j - 1]]
wd.row_dimensions[1].height = 48
for j, w in enumerate([22, 10, 22, 11, 13, 13, 16, 16, 16, 13, 15, 16, 16, 14], 1):
    wd.column_dimensions[wd.cell(row=1, column=j).column_letter].width = w
wd.freeze_panes = 'A2'
last = N + 1
wd.auto_filter.ref = f'A1:N{last}'
R = lambda col: f"'Cards dataset'!${col}$2:${col}${last}"               # noqa: E731
TIER, SEG, EVER, L3, TOT = R('B'), R('C'), R('E'), R('F'), R('I')
METRICS = [('Outflow (debit) volume, AMD / month', 'G', AMD), ('Inflow (credit) volume, AMD / month', 'H', AMD),
           ('Total transaction volume, AMD / month', 'I', AMD), ('Debit transactions, # / month', 'J', DEC),
           ('Card balance, AMD (month end)', 'K', AMD), ('Current-account balance, AMD (month end)', 'L', AMD),
           ('Deposit balance, AMD (month end)', 'M', AMD), ('FX volume, AMD / month', 'N', AMD)]
ACT = f'{SEG},"<>Gold loan",{L3},">0"'                                  # active-user criteria (AVERAGEIFS / COUNTIFS)


# ------------------------------------------------------------------ Client profiles
def put(ref, v, font=f_norm, fmt=None, fill=None, align=None, border=None):
    c = wp[ref]
    c.value = v
    c.font = font
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if align:
        c.alignment = align
    if border:
        c.border = border
    return c


def header(r, title):
    put(f'B{r}', title, f_bold, fill=fill_hdr, border=b_bot)
    for c, t in zip(TC + ['G', 'H'], TIERS + ['All tiers', 'Notes']):
        put(f'{c}{r}', t, f_bold, fill=fill_hdr, border=b_bot, align=Alignment(horizontal='center' if c != 'H' else 'left'))


for col, w in {'A': 2, 'B': 62, 'C': 14, 'D': 14, 'E': 14, 'F': 14, 'G': 14, 'H': 70}.items():
    wp.column_dimensions[col].width = w
put('B1', 'CLIENT PROFILES', f_title)
put('B2', "Per-card activity of cards issued in 2026 by client profile, and the multipliers the tier model applies. "
          "Pick the mode on 'Control panel' D3.", f_note)
put('B4', 'Mode selected on the Control panel', f_bold)
put('C4', "='Control panel'!$D$3", f_link)
put('B5', 'Mode number used below (1 = today\'s figures)')
put('C5', '=IFERROR(VALUE(LEFT(C4,1)),1)', f_bold, fmt='0', align=Alignment(horizontal='center'))
MODE = '$C$5'

put('B7', '1. How the profiles are defined', f_bold, fill=fill_hdr, border=b_bot)
for c in TC + ['G', 'H']:
    put(f'{c}7', None, fill=fill_hdr, border=b_bot)
defs = ["1. All client base: every retail card issued Jan–Aug 2026 (cards of record; business cards and superseded reissues out). "
        "Multiplier 1× = the model's current per-card figures.",
        "2. Active users: all 2026 cards without gold-loan cards (card sub-segment 'Gold loan'), never-used cards (no transaction "
        "since issue) and dormant cards (no transaction in Jun–Aug 2026).",
        "3. High engagement users: active users whose total transaction volume is at or above their tier's 75th percentile "
        "of active users (the top quartile).",
        "Per-card values are monthly averages over Jun–Aug 2026, counting only months after the card was issued. "
        "A transaction is any debit or credit transaction.",
        "Multiplier = profile average ÷ average of all 2026 cards in the tier. If it can't be calculated, the average of the "
        "tier's other multipliers (the five used by the model) is taken."]
for i, t in enumerate(defs):
    put(f'B{8 + i}', t)

# 2. counts
r0 = 14
header(r0, '2. Cards by profile')
TH = {t: f'{c}${r0}' for t, c in zip(TIERS, TC)}                        # tier name cells used as criteria
rows = {}
spec = [('cards', 'All 2026 cards', lambda h: f'=COUNTIFS({TIER},{h})', CNT, ''),
        ('gold', '  of which gold-loan cards', lambda h: f'=COUNTIFS({TIER},{h},{SEG},"Gold loan")', CNT, "Card sub-segment 'Gold loan'"),
        ('never', '  of which never used (no transaction since issue)', lambda h: f'=COUNTIFS({TIER},{h},{SEG},"<>Gold loan",{EVER},0)', CNT, 'Non-gold cards only'),
        ('dormant', '  of which dormant (no transaction in Jun–Aug 2026)', lambda h: f'=COUNTIFS({TIER},{h},{SEG},"<>Gold loan",{EVER},">0",{L3},0)', CNT, 'Non-gold cards with earlier transactions'),
        ('active', 'Active users', lambda h: f'=COUNTIFS({TIER},{h},{ACT})', CNT, 'All 2026 cards less the three groups above'),
        ('share', '  share of all 2026 cards', None, PCT, ''),
        ('cut', 'High-engagement cut-off: total transaction volume at least, AMD / month', None, AMD,
         "75th percentile of the tier's active users (PERCENTILE.INC)"),
        ('high', 'High engagement users', None, CNT, 'Active users at or above the cut-off')]
for i, (k, lab, fn, fm, note) in enumerate(spec):
    r = r0 + 1 + i
    rows[k] = r
    put(f'B{r}', lab, f_bold if k in ('active', 'high') else f_norm)
    put(f'H{r}', note, f_note)
    for c, t in zip(TC, TIERS):
        h = TH[t]
        if k == 'share':
            v = f'=IFERROR({c}{rows["active"]}/{c}{rows["cards"]},0)'
        elif k == 'cut':
            v = f'=_xlfn.AGGREGATE(16,6,{TOT}/(({TIER}={h})*({SEG}<>"Gold loan")*({L3}>0)),0.75)'
        elif k == 'high':
            v = f'=COUNTIFS({TIER},{h},{ACT},{TOT},">="&{c}${rows["cut"]})'
        else:
            v = fn(h)
        put(f'{c}{r}', v, f_bold if k in ('active', 'high') else f_norm, fmt=fm)
    if k == 'share':
        put(f'G{r}', f'=IFERROR(G{rows["active"]}/G{rows["cards"]},0)', fmt=fm)
    elif k != 'cut':
        put(f'G{r}', f'=SUM(C{r}:F{r})', f_bold if k in ('active', 'high') else f_norm, fmt=fm)
put(f'G{rows["cut"]}', 'per tier', f_note, align=Alignment(horizontal='center'))

# 3. averages
r0 = rows['high'] + 2
header(r0, '3. Average per card, by profile')
avg = {}
blocks = [('p1', 'All 2026 cards (mode 1)', lambda m, h: f'=IFERROR(AVERAGEIFS({R(m)},{TIER},{h}),0)', lambda m: f'=IFERROR(AVERAGE({R(m)}),0)'),
          ('p2', 'Active users (mode 2)', lambda m, h: f'=IFERROR(AVERAGEIFS({R(m)},{TIER},{h},{ACT}),0)', lambda m: f'=IFERROR(AVERAGEIFS({R(m)},{ACT}),0)'),
          ('p3', 'High engagement users (mode 3)', None, None)]
r = r0
for bk, title, fn, fall in blocks:
    r += 1
    put(f'B{r}', title, f_sub)
    for i, (lab, m, fm) in enumerate(METRICS):
        r += 1
        avg[(bk, i)] = r
        put(f'B{r}', '  ' + lab)
        for c, t in zip(TC, TIERS):
            h = TH[t]
            v = fn(m, h) if fn else f'=IFERROR(AVERAGEIFS({R(m)},{TIER},{h},{ACT},{TOT},">="&{c}${rows["cut"]}),0)'
            put(f'{c}{r}', v, fmt=fm)
        put(f'G{r}', fall(m) if fall else f'=IFERROR(SUMPRODUCT(C{r}:F{r},$C${rows["high"]}:$F${rows["high"]})/$G${rows["high"]},0)', fmt=fm)

# 4. multipliers
r0 = r + 2
header(r0, '4. Multiplier vs all 2026 cards (profile average ÷ all-card average)')
mult = {}
r = r0
for bk, title in [('p2', 'Active users (mode 2)'), ('p3', 'High engagement users (mode 3)')]:
    r += 1
    put(f'B{r}', title, f_sub)
    for i, (lab, m, fm) in enumerate(METRICS):
        r += 1
        mult[(bk, i)] = r
        put(f'B{r}', '  ' + lab)
        for c in TC + ['G']:
            put(f'{c}{r}', f'=IFERROR({c}{avg[(bk, i)]}/{c}{avg[("p1", i)]},"")', fmt=MULT)
put(f'H{mult[("p2", 1)]}', 'Inflow volume, total volume and current-account balance: for information, not used by the model', f_note)

# 5. multipliers in use
r0 = r + 2
put(f'B{r0}', '5. Multipliers used by the tier model (mode in use)', f_bold, fill=fill_hdr, border=b_bot)
for c, t in zip(TC + ['G', 'H'], TIERS + ['Based on', 'Where the model uses it']):
    put(f'{c}{r0}', t, f_bold, fill=fill_hdr, border=b_bot, align=Alignment(horizontal='center' if c in TC else 'left'))
USED = [0, 3, 4, 6, 7]                                                      # metrics that drive the model (fallback pool)
drivers = [('noncash', 'Non-cash payments per card', 0, "'4 tiers model' row 21 (Black 98, Premium 175, Elite 252)"),
           ('txn', 'Transactions per card', 3, 'row 22 / 99 / 176 / 253'),
           ('cashout', 'Cashout per card', 0, 'row 30 / 107 / 184 / 261 (no cash-only metric in the dataset: outflow is closest)'),
           ('c2c', 'C2C transfers per card', 0, 'row 35 / 112 / 189 / 266 (no transfer-only metric: outflow is closest)'),
           ('balance', 'Card balance per card (interest income)', 4, 'row 48 / 125 / 202 / 279'),
           ('fx', 'FX revenue per card', 7, 'row 39 / 116 / 193 / 270 (all periods, incl. the market-based years)'),
           ('deposit', 'Deposited amount per card (deposit uplift cost)', 6, 'row 53 / 130 / 207 / 284')]
layout = {'mode_cell': MODE, 'drivers': {}, 'tier_cols': dict(zip(TIERS, TC))}
for j, (k, lab, mi, where) in enumerate(drivers):
    rr = r0 + 1 + j
    layout['drivers'][k] = rr
    put(f'B{rr}', lab, f_bold)
    put(f'G{rr}', METRICS[mi][0].split(',')[0], f_note)
    put(f'H{rr}', where, f_note)
    for c in TC:
        def fb(bk):
            x = f'{c}{mult[(bk, mi)]}'
            pool = ','.join(f'{c}{mult[(bk, u)]}' for u in USED)
            return f'IF(ISNUMBER({x}),{x},IFERROR(AVERAGE({pool}),1))'
        put(f'{c}{rr}', f'=CHOOSE({MODE},1,{fb("p2")},{fb("p3")})', f_bold, fmt=MULT, fill=fill_use)
layout['rows'] = {'counts': rows, 'avg': {f'{k[0]}_{k[1]}': v for k, v in avg.items()}, 'mult': {f'{k[0]}_{k[1]}': v for k, v in mult.items()}}
put(f'B{r0 + len(drivers) + 2}', "Coefficients multiply the tier model's Q4-26 starting values; every later period grows from them, so the whole "
    "projection scales. Prices, fees, shares (international, FX, ArCa) and card counts are not changed by the mode.", f_note)
wp.freeze_panes = 'C4'
wp.sheet_view.showGridLines = False
wp.sheet_view.zoomScale = 130
wb.save(OUT)
json.dump(layout, open(OUT.replace('.xlsx', '_layout.json'), 'w'), indent=1)
# one workbook per tab, so each can be placed separately by merge_into_model.py
from openpyxl import load_workbook                                          # noqa: E402
for keep, suffix in [('Client profiles', '_cp'), ('Cards dataset', '_cd')]:
    w2 = load_workbook(OUT)
    for ws in list(w2.worksheets):
        if ws.title != keep:
            w2.remove(ws)
    w2.save(OUT.replace('.xlsx', f'{suffix}.xlsx'))
print('saved', OUT, 'rows', N, 'drivers at', layout['drivers'])
