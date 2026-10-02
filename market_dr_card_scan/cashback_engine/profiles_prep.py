"""Client profiles (model v14): compact the model's 'Cards dataset' tab and compute reference statistics.

    python3 profiles_prep.py <model.xlsx> <out_dir>

Reads the full 'Cards dataset' tab (one row per contract, 173 columns, header on row 2) and writes:
  cards_compact.pkl  - retail cards issued Jan-Aug 2026, 14 columns, no IDs (goes into the new 'Cards dataset' tab)
  profiles_ref.json  - Python reference for every figure the 'Client profiles' formulas calculate

Profiles (agreed with Alex 24.09.2026)
  1 All client base    every retail card issued Jan-Aug 2026 (cards of record; business cards and superseded reissues out)
  2 Active users       without card_sub_segment 'Gold loan' and without cards with no transaction in Jun-Aug 2026
                       (never-used + dormant). Transactions = debit + credit counts.
  3 High engagement    active users with total transaction volume >= the tier's 75th percentile of active users
Metrics = monthly averages over Jun-Aug 2026, months after issue only. Coefficient = profile average / all-2026 average
per tier; if it can't be calculated, the average of the tier's other (mapped) coefficients.
"""
import json
import re
import sys
import zipfile

import numpy as np
import pandas as pd
from lxml import etree
from openpyxl.utils import column_index_from_string as ci

SRC, OUT = sys.argv[1:3]
X = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
MONTHS = ['2025-08', '2025-09', '2025-10', '2025-11', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04', '2026-05',
          '2026-06', '2026-07', '2026-08']
L3 = ['2026-06', '2026-07', '2026-08']
TIER = {'Visa Digital': 'Free', 'Arca': 'Black', 'Visa Classic': 'Black', 'MasterCard World': 'Premium', 'Visa Gold': 'Premium',
        'MasterCard World Elite': 'Elite', 'Visa Infinite': 'Elite', 'Visa Infinite Metal': 'Elite'}
TIERS = ['Free', 'Black', 'Premium', 'Elite']
# column name in the compact tab, source field family, rounding
METRICS = [('Outflow (debit) volume, AMD / month', 'debit_volume_amd', 0),
           ('Inflow (credit) volume, AMD / month', 'credit_volume_amd', 0),
           ('Total transaction volume, AMD / month', 'txn_volume_amd', 0),
           ('Debit transactions, # / month', 'debit_txn_count', 2),
           ('Card balance, AMD (month end)', 'card_balance_eom_amd', 0),
           ('Current-account balance, AMD (month end)', 'current_account_balance_eom_amd', 0),
           ('Deposit balance, AMD (month end)', 'deposit_balance_eom_amd', 0),
           ('FX volume, AMD / month', 'fx_volume_amd', 0)]
MAPPED = ['debit_volume_amd', 'debit_txn_count', 'card_balance_eom_amd', 'deposit_balance_eom_amd', 'fx_volume_amd']


def read_cards(path):
    z = zipfile.ZipFile(path)
    wbx = z.read('xl/workbook.xml').decode()
    rels = z.read('xl/_rels/workbook.xml.rels').decode()
    rid = re.search(r'<sheet [^>]*name="Cards dataset"[^>]*r:id="([^"]+)"', wbx).group(1)
    target = re.search(r'Id="%s"[^>]*Target="([^"]+)"|Target="([^"]+)"[^>]*Id="%s"' % (rid, rid), rels)
    part = 'xl/' + (target.group(1) or target.group(2)).lstrip('/').replace('xl/', '')
    ss = []
    for ev, el in etree.iterparse(z.open('xl/sharedStrings.xml'), tag=X + 'si'):
        ss.append(''.join(t.text or '' for t in el.iter(X + 't')))
        el.clear()
    hdr, data = None, []
    rx = re.compile(r'([A-Z]+)')
    for ev, el in etree.iterparse(z.open(part), tag=X + 'row', huge_tree=True):
        r = int(el.get('r'))
        if r >= 2:
            row = [None] * 173
            for c in el.iter(X + 'c'):
                k = ci(rx.match(c.get('r')).group(1)) - 1
                v = c.find(X + 'v')
                if v is None or k >= 173:
                    continue
                t = c.get('t')
                row[k] = ss[int(v.text)] if t == 's' else (v.text if t in ('str', 'e', 'b') else float(v.text))
            (data.append(row) if r > 2 else None)
            hdr = row if r == 2 else hdr
        el.clear()
        while el.getprevious() is not None:
            del el.getparent()[0]
    return pd.DataFrame(data, columns=hdr)


df = read_cards(SRC)
print('Cards dataset rows', len(df))
num = lambda f, months: df[[f'{f}_{m}' for m in months]].apply(pd.to_numeric, errors='coerce')   # noqa: E731
iss = pd.to_datetime(pd.to_numeric(df.card_issued, errors='coerce'), unit='D', origin='1899-12-30')
keep = (iss.dt.year == 2026) & df.card_of_record.eq('YES') & df.card_type_group.isin(list(TIER))
cnt_all = num('debit_txn_count', MONTHS).fillna(0).values + num('credit_txn_count', MONTHS).fillna(0).values
cnt_l3 = num('debit_txn_count', L3).fillna(0).values + num('credit_txn_count', L3).fillna(0).values
out = pd.DataFrame({
    'Card type': df.card_type_group,
    'Tier': df.card_type_group.map(TIER),
    'Card sub-segment': df.card_sub_segment,
    'Issue month': df.issue_month,
    'Transactions since issue, #': cnt_all.sum(axis=1),
    'Transactions Jun-Aug 2026, #': cnt_l3.sum(axis=1),
})
for name, fam, nd in METRICS:
    out[name] = num(fam, L3).mean(axis=1, skipna=True).fillna(0).round(nd)
out = out[keep.values].reset_index(drop=True)
out = out.sort_values(['Tier', 'Card type', 'Issue month'], key=lambda s: s.map({t: i for i, t in enumerate(TIERS)}) if s.name == 'Tier' else s,
                      kind='stable').reset_index(drop=True)
out.to_pickle(f'{OUT}/cards_compact.pkl')
print('compact rows', len(out), out.Tier.value_counts().to_dict())

# ---------------------------------------------------------------- reference statistics (same logic as the formulas)
ref = {'n': len(out), 'tiers': {}}
col = {fam: name for name, fam, nd in METRICS}
tot_col = col['txn_volume_amd']
for t in TIERS + ['All']:
    d = out if t == 'All' else out[out.Tier == t]
    act = (d['Card sub-segment'] != 'Gold loan') & (d['Transactions Jun-Aug 2026, #'] > 0)
    a = d[act]
    cut = float(np.percentile(a[tot_col], 75)) if len(a) else 0.0            # = PERCENTILE.INC
    hi = a[a[tot_col] >= cut]
    g = d['Card sub-segment'] == 'Gold loan'
    r = {'cards': int(len(d)), 'gold': int(g.sum()),
         'never': int((~g & (d['Transactions since issue, #'] == 0)).sum()),
         'dormant': int((~g & (d['Transactions since issue, #'] > 0) & (d['Transactions Jun-Aug 2026, #'] == 0)).sum()),
         'active': int(len(a)), 'cutoff': cut, 'high': int(len(hi)), 'avg': {}, 'coef2': {}, 'coef3': {}}
    for name, fam, nd in METRICS:
        m1, m2, m3 = d[name].mean(), a[name].mean(), hi[name].mean()
        r['avg'][fam] = [m1, m2, m3]
        r['coef2'][fam] = (m2 / m1) if m1 else None
        r['coef3'][fam] = (m3 / m1) if m1 else None
    for k in ('coef2', 'coef3'):                                            # fallback: average of the other mapped coefficients
        ok = [r[k][f] for f in MAPPED if r[k][f] is not None]
        r[k + '_used'] = {f: (r[k][f] if r[k][f] is not None else (sum(ok) / len(ok) if ok else 1.0)) for f in MAPPED}
    ref['tiers'][t] = r
json.dump(ref, open(f'{OUT}/profiles_ref.json', 'w'), indent=1)
for t in TIERS:
    r = ref['tiers'][t]
    print(t, r['cards'], 'active', r['active'], 'high', r['high'], 'cut-off', round(r['cutoff']),
          'mode2', {k[:6]: round(v, 2) for k, v in r['coef2_used'].items()}, 'mode3', {k[:6]: round(v, 2) for k, v in r['coef3_used'].items()})
