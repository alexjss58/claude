"""Prepare engine data from the client-level MCC extract (kept outside the project folder).

    python3 prep.py <spend_by_mcc.csv> <client_cards.csv> <out_dir>

client_cards.csv holds only contract / client / card type columns taken from the model's Extract_client_DB
sheet (no balances). Outputs (in out_dir): mcc_stats.csv, profiles.pkl, sample.csv (Aug-26, stratified,
re-keyed - no bank IDs), population.pkl (full Aug-26 category matrix for the Python cross-check).
"""
import pickle
import sys

import numpy as np
import pandas as pd

from mcc_ref import CATEGORIES, ELIGIBLE, lookup
from params import CARD_TIER, UNKNOWN, UNKNOWN_TIER

SRC, CARDS, OUT = sys.argv[1:4]
MONTH, LAST6 = '2026-08', ['2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08']
SAMPLE_N = {'Free': 800, 'Black': 3000, 'Premium': 2200, 'Elite': 99999, UNKNOWN: 400}
CENSUS = 0.02          # top 2% of each tier by non-cash spend and by eligible spend are always in the sample (weight 1)

mc = pd.read_csv(SRC, encoding='utf-8-sig', dtype={'client_id': str, 'card_id': str, 'mcc': str, 'month': str})
cc = pd.read_csv(CARDS, dtype=str)[['client_id', 'card_type']].drop_duplicates('client_id')
mc['mcc'] = mc.mcc.str.strip().str.zfill(4)                  # some codes come without the leading zero (742 -> 0742)
mc = mc.merge(cc, on='client_id', how='left')
mc['card_type'] = mc.card_type.fillna(UNKNOWN)
mc['tier'] = mc.card_type.map(CARD_TIER).fillna('Unknown card type → ' + UNKNOWN_TIER)
mc['cat'] = mc.mcc.map(lambda m: lookup(m)[2])

# ---- MCC stats (6 months and August)
l6 = mc[mc.month.isin(LAST6)]
nc6 = l6.client_id.nunique()
st = l6.groupby('mcc').agg(vol_6m=('txn_volume_amd', 'sum'), clients_6m=('client_id', 'nunique'))
st['vol_aug'] = mc[mc.month == MONTH].groupby('mcc').txn_volume_amd.sum()
st['reach_6m'] = st.clients_6m / nc6
st['vol_month_avg'] = st.vol_6m / 6
st = st.fillna(0).reset_index()
st.to_csv(f'{OUT}/mcc_stats.csv', index=False)

# ---- profiles (August 2026 and 6-month average), by card type and by tier
def profile(df, key):
    g = df.groupby(key)
    out = pd.DataFrame({'clients': g.client_id.nunique(), 'total': g.txn_volume_amd.sum()})
    for c in ['X_CASH', 'X_GAMB']:
        out[c] = df[df.cat == c].groupby(key).txn_volume_amd.sum()
    out['X_other'] = df[df.cat.str.startswith('X_') & ~df.cat.isin(['X_CASH', 'X_GAMB'])].groupby(key).txn_volume_amd.sum()
    out['eligible'] = df[~df.cat.str.startswith('X_')].groupby(key).txn_volume_amd.sum()
    return out.fillna(0)


aug = mc[mc.month == MONTH]
prof = {'card_aug': profile(aug, 'card_type'), 'tier_aug': profile(aug, 'tier'), 'tier_6m': profile(l6, 'tier')}
prof['tier_6m'][['total', 'X_CASH', 'X_GAMB', 'X_other', 'eligible']] /= 6
prof['tier_6m']['clients'] = l6.groupby(['tier', 'month']).client_id.nunique().groupby('tier').mean()
# category mix (Aug) by tier: share of eligible spend and reach
el = aug[~aug.cat.str.startswith('X_')]
mix = el.groupby(['tier', 'cat']).agg(vol=('txn_volume_amd', 'sum'), clients=('client_id', 'nunique')).reset_index()
prof['mix'] = mix
# eligible spend per client distribution (Aug)
pc = el.groupby(['tier', 'client_id']).txn_volume_amd.sum().reset_index()
allc = aug.groupby(['tier', 'client_id']).size().reset_index()[['tier', 'client_id']]
pc = allc.merge(pc, how='left').fillna(0)
prof['dist'] = pc.groupby('tier').txn_volume_amd.quantile([.25, .5, .75, .9, .99]).unstack()
ncat = el.groupby(['tier', 'client_id']).cat.nunique()
prof['ncat'] = ncat.groupby('tier').mean()
top = el.groupby(['tier', 'client_id', 'cat']).txn_volume_amd.sum()
prof['topshare'] = (top.groupby(level=[0, 1]).max() / top.groupby(level=[0, 1]).sum()).groupby('tier').median()
prof['months'] = mc.groupby('month').agg(clients=('client_id', 'nunique'), total=('txn_volume_amd', 'sum'))
prof['months']['eligible'] = mc[~mc.cat.str.startswith('X_')].groupby('month').txn_volume_amd.sum()
prof['months']['gamb'] = mc[mc.cat == 'X_GAMB'].groupby('month').txn_volume_amd.sum()
prof['months']['cash'] = mc[mc.cat == 'X_CASH'].groupby('month').txn_volume_amd.sum()
pickle.dump(prof, open(f'{OUT}/profiles.pkl', 'wb'))

# ---- August client-level long table for the Client view (all clients, bank client_id kept as asked by Alex)
lng = aug.groupby(['client_id', 'mcc']).txn_volume_amd.sum().reset_index()
lng['client_id'] = lng.client_id.astype(int)
lng = lng.sort_values(['client_id', 'mcc'])
lng.to_csv(f'{OUT}/client_long.csv', index=False)
aug[['client_id', 'card_type']].drop_duplicates('client_id').assign(client_id=lambda d: d.client_id.astype(int)) \
    .sort_values('client_id').to_csv(f'{OUT}/client_types.csv', index=False)

# ---- August client x MCC matrix, stratified sample (Business cards out of scope)
aug = aug[~aug.card_type.str.startswith(('Visa Business', 'MasterCard Business'))]
wide = aug.pivot_table(index=['client_id', 'card_type'], columns='mcc', values='txn_volume_amd', aggfunc='sum').fillna(0)
wide = wide.reset_index()
wide['stratum'] = wide.card_type.map(CARD_TIER).fillna(UNKNOWN)
pickle.dump(wide, open(f'{OUT}/population.pkl', 'wb'))
rng = np.random.default_rng(20260924)
mcc_all = [c for c in wide.columns if str(c).isdigit()]
cat_of = {m: lookup(m)[2] for m in mcc_all}
wide['_nc'] = wide[[m for m in mcc_all if cat_of[m] != 'X_CASH']].sum(axis=1)
wide['_el'] = wide[[m for m in mcc_all if not cat_of[m].startswith('X_')]].sum(axis=1)
parts = []
for s, g in wide.groupby('stratum'):
    n = min(SAMPLE_N[s], len(g))
    if n >= len(g):
        pick = g.copy(); pick['weight'] = 1.0; parts.append(pick); continue
    top = g.index[:0]
    if s != UNKNOWN:                                                   # census of the heaviest spenders (heavy tails)
        k = int(round(len(g) * CENSUS))
        top = g.nlargest(k, '_nc').index.union(g.nlargest(k, '_el').index)
        top = top[:max(0, n - 100)]
    cen = g.loc[top].copy(); cen['weight'] = 1.0
    rest = g.drop(index=top); m = n - len(cen)
    rnd = rest.iloc[np.sort(rng.choice(len(rest), m, replace=False))].copy(); rnd['weight'] = len(rest) / m
    parts += [cen, rnd]
smp = pd.concat(parts).sample(frac=1, random_state=7).reset_index(drop=True)
smp.insert(0, 'client_key', smp.client_id.astype(int))      # bank client_id (Alex 24.09: select exact client IDs)
smp = smp.drop(columns=['client_id'])
mcc_cols = sorted([c for c in smp.columns if c.isdigit()])
smp = smp[['client_key', 'card_type', 'stratum', 'weight'] + mcc_cols]
wide = wide.drop(columns=['_nc', '_el'])
smp.to_csv(f'{OUT}/sample.csv', index=False)
print('population', wide.groupby('stratum').size().to_dict())
print('sample', smp.groupby('stratum').size().to_dict(), 'mcc cols', len(mcc_cols))
