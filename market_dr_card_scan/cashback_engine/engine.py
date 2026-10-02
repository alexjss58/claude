"""Python reference implementation of the Excel engine (same rules, same order), used to
(1) sanity-check default parameters on the full August population and (2) verify the workbook.

    run(wide_df, weights, target=None) -> per-client DataFrame with the engine outputs

Menu rates are ranked and costed at x1, then scaled per tier by a multiplier m so that bank cost
= target x non-cash spend (auto-scaling, same as Inputs "Scale menu rates to hit the target" = Yes).
"""
import numpy as np
import pandas as pd

from mcc_ref import ELIGIBLE, PICKABLE, lookup
from params import (CARD_TIER, FOREIGN, IF_DOM, IF_INTL, P, PARTNER, RATE, ROLE, TIERS, UNKNOWN,
                    UNKNOWN_TIER)

EPS = 1e-6


def category_matrix(wide):
    mcc_cols = [c for c in wide.columns if str(c).isdigit()]
    cats = {m: lookup(m)[2] for m in mcc_cols}
    out = pd.DataFrame(index=wide.index)
    for c in ELIGIBLE:
        cols = [m for m in mcc_cols if cats[m] == c]
        out[c] = wide[cols].sum(axis=1) if cols else 0.0
    tot = wide[mcc_cols].sum(axis=1)
    cash = wide[[m for m in mcc_cols if cats[m] == 'X_CASH']].sum(axis=1)
    gamb = wide[[m for m in mcc_cols if cats[m] == 'X_GAMB']].sum(axis=1)
    excl = wide[[m for m in mcc_cols if cats[m].startswith('X_')]].sum(axis=1)
    return out, tot, cash, gamb, excl


def run(wide, w=None, target=None, auto=True, mult=None):
    S, tot, cash, gamb, excl = category_matrix(wide)
    tier = wide.card_type.map(CARD_TIER).fillna(UNKNOWN_TIER)
    rows = []
    for i in wide.index:
        t = tier[i]
        s = S.loc[i]
        J = tot[i] - excl[i]
        r = dict(tier=t, total=tot[i], cash=cash[i], gamb=gamb[i], excl=excl[i], elig=J, noncash=tot[i] - cash[i])
        if t not in TIERS or not P['active'][t]:
            r.update(bank=0, partner_total=0, partner_bank=0, cap_hit=0, picks={})
        else:
            h = P['min_txn_haircut'][t]
            # a partner offer replaces the bank category of the same kind on the menu (no double listing)
            hidden = {pc for (pc, rate, cov, fund) in PARTNER[t] if rate > 0} if P['partner_replace'][t] == 'Yes' else set()
            role = {c: ('No' if c in hidden else ROLE[t][c]) for c in PICKABLE}
            always = [c for c in PICKABLE if role[c] == 'Always']
            slots = P['menu_size'][t] - len(always)
            spent = sorted([s[c] for c in PICKABLE if role[c] == 'If spent'], reverse=True)
            kth_s = 9e99 if slots < 1 else (spent[slots - 1] if len(spent) >= slots else 0)
            ev = {}
            for k, c in enumerate(PICKABLE):
                menu = role[c] == 'Always' or (role[c] == 'If spent' and s[c] > 0 and s[c] >= kth_s)
                ev[c] = (RATE[t][c] * s[c] * (1 - h) + (len(PICKABLE) - k) * EPS) if menu else 0.0
            base = P['base_rate'][t]
            mode = P['base_mode'][t]
            pr = []
            for (pc, rate, cov, fund) in PARTNER[t]:
                pr.append(rate * s[pc] * cov * (1 - h))
            comp = P['partner_compete'][t] == 'Yes'
            evp = [x if comp else 0.0 for x in pr]
            k = P['picks'][t]
            # base is worth the base rate on eligible spend outside the (k-1) best other options
            if k < 2:
                s_top = 0.0
            else:
                thr = sorted(list(ev.values()) + evp, reverse=True)[k - 2]
                s_top = sum(s[c] for c in PICKABLE if ev[c] >= thr and ev[c] > 1e-3)
            ev_base = base * (J - s_top) * (1 - h) if mode == 'Pickable' else 0.0
            allev = list(ev.values()) + [ev_base] + evp
            kth = sorted(allev, reverse=True)[k - 1]
            pick = {c: (ev[c] >= kth and ev[c] > 1e-3) for c in PICKABLE}
            pick_base = ev_base >= kth and ev_base > 1e-3
            sp = sum(s[c] for c in PICKABLE if pick[c])
            cb_cat = sum(RATE[t][c] * s[c] * (1 - h) for c in PICKABLE if pick[c])
            if mode == 'Pickable':
                cb_base = base * (J - sp) * (1 - h) if pick_base else 0.0
            elif mode == 'Automatic':
                cb_base = base * (J - sp) * (1 - h)
            else:
                cb_base = 0.0
            ok = J >= P['min_spend'][t]
            cb_ch = (cb_cat + cb_base) if ok else 0.0
            rule = P['nonchooser_rule'][t]
            cb_nc = P['nc_rate'][t] * J * (1 - h) if rule == 'Flat rate' else (cb_ch if rule == 'Auto-pick' else 0.0)
            cb_nc = cb_nc if ok else 0.0
            cap = P['cap'][t]
            q = P['nonchooser_share'][t]
            bank = (1 - q) * min(cb_ch, cap) + q * min(cb_nc, cap)
            pp = [pr[j] if (not comp or (evp[j] >= kth and evp[j] > 1e-3)) else 0.0 for j in range(len(pr))]
            ptot = sum(pp)
            pcap = P['partner_cap'][t]
            pcapped = min(ptot, pcap)
            pbank_share = (sum((1 - PARTNER[t][j][3]) * pp[j] for j in range(len(pp))) / ptot) if ptot > 0 else 0.0
            r['cb_ch'] = cb_ch
            r.update(cap=cap, q=q, nc_cap=min(cb_nc, cap), bank=bank, partner_total=(1 - q) * pcapped,
                     partner_bank=(1 - q) * pcapped * pbank_share,
                     cap_hit=(1 - q) * (cb_ch > cap), picks={c: (1 - q) * pick[c] for c in PICKABLE})
        r['icf'] = sum(s[c] * (IF_DOM[c] * (1 - FOREIGN[c]) + IF_INTL * FOREIGN[c]) for c in ELIGIBLE)
        rows.append(r)
    res = pd.DataFrame(rows, index=wide.index)
    return scale(res, w, target, auto, mult)


MAXM = 10       # same ceiling as the workbook
NEWTON = 6      # same number of Newton steps as the workbook (Results "Scaling: step k")


def scale(res, w=None, target=None, auto=True, mult=None):
    """Multiply the menu cashback of choosers by m per tier so that bank cost = target x non-cash
    (cost not scaled = non-chooser flat rate + bank share of partner offers; caps applied per client)."""
    from params import TARGET
    target = target or TARGET
    w = pd.Series(1.0, index=res.index) if w is None else pd.Series(np.asarray(w, float), index=res.index)
    res = res.copy()
    res['m'] = 0.0
    for t in TIERS:
        d = res.tier == t
        if not d.any() or 'cb_ch' not in res or res.loc[d, 'cb_ch'].isna().all():
            continue
        x = res.loc[d]
        ww = w[d].values
        q = x.q.iloc[0]
        autopick = P['nonchooser_rule'][t] == 'Auto-pick'
        sh = 1.0 if autopick else 1 - q
        cb, cap = x.cb_ch.values, x.cap.values
        ncc = 0 * x.nc_cap.values if autopick else x.nc_cap.values
        scal = sh * (ww * cb).sum()
        fixed = q * (ww * ncc).sum() + (ww * x.partner_bank.values).sum()
        T = target[t] * (ww * x.noncash.values).sum()
        m = (T - fixed) / scal if scal > 0 else 0.0
        for _ in range(NEWTON):
            val = (ww * np.minimum(m * cb, cap)).sum()
            der = (ww * (m * cb <= cap) * cb).sum()
            if sh * der != 0:
                m = m + (T - fixed - sh * val) / (sh * der)
        m = min(MAXM, max(0.0, m))
        if not auto:
            m = (mult or {}).get(t, 1.0)
        res.loc[d, 'm'] = m
        res.loc[d, 'bank'] = sh * np.minimum(m * cb, cap) + q * ncc
        res.loc[d, 'cap_hit'] = (1 - q) * (m * cb > cap)
    return res


def summary(res, w):
    res = res.assign(w=w.values)
    out = {}
    for t in TIERS:
        d = res[res.tier == t]
        ww = d.w
        f = lambda col: float((d[col] * ww).sum())          # noqa: E731
        cost = f('bank') + f('partner_bank')
        out[t] = dict(clients=float(ww.sum()), eligible=f('elig'), noncash=f('noncash'), bank_cost=cost,
                      partner_funded=f('partner_total') - f('partner_bank'), icf=f('icf'),
                      eff_elig=cost / f('elig') if f('elig') else 0, eff_noncash=cost / f('noncash') if f('noncash') else 0,
                      cap_hit=f('cap_hit') / ww.sum() if ww.sum() else 0)
    return pd.DataFrame(out).T
