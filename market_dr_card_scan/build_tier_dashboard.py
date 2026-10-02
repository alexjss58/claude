"""Build the tier dashboard: python3 build_tier_dashboard.py --note "what changed"

Every build that changes the page is archived as versions/debit-card-tiers_<date>_v<N>.html and logged in
versions/CHANGELOG.md, so earlier states of the dashboard stay openable.

Inputs  data/2026-09-18-competitor-cards.json   card records (scan)
        data/2026-09-21-fx-snapshot-rate-am.json bank FX rates
        data/2026-09-29-deposit-rates.json       1-year AMD term deposit on 1m AMD per bank (fininfo.am + bank pages)
        norms.py                                 per-card tier + normalised tariffs
Outputs debit-card-tiers.html                    self-contained dashboard
        data/card-tiers-normalised.csv           the numbers the dashboard uses, for audit

Adding a bank: append its records to the cards JSON (same schema), add its entries to norms.py,
add its rate.am code to FX_CODES if the snapshot has it, and re-run.
"""
import argparse
import base64
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from norms import N, STRIP_REASON, STRIP_WHY, LEGACY

HERE = Path(__file__).parent
CARDS = HERE / 'market/data/2026-09-18-competitor-cards.json'  # 7-bank file incl. Acba (2026-09-21)
FX = HERE / 'data/2026-09-21-fx-snapshot-rate-am.json'
DEPOSITS = HERE / 'data/2026-09-29-deposit-rates.json'
TEMPLATE = HERE / 'tier_dashboard_template.html'
OUT = HERE / 'debit-card-tiers.html'
CSV_OUT = HERE / 'data/card-tiers-normalised.csv'
VERSIONS = HERE / 'versions'
IMAGES = HERE / 'assets/cards/index.json'   # card photos from the banks' sites (21.09.2026); missing -> styled render

BANK_ORDER = ['FastBank', 'Acba', 'Ameriabank', 'Ardshinbank', 'Conversebank', 'Evocabank', 'IDBank']
BANK_NAME = {'FastBank': 'Fast Bank', 'IDBank': 'IDBank', 'Ameriabank': 'Ameriabank', 'Ardshinbank': 'Ardshinbank',
             'Evocabank': 'Evocabank', 'Conversebank': 'Converse Bank', 'Acba': 'Acba Bank'}
PENDING = []


def scheme_of(c):
    n, s = c['card_name_en'].lower(), (c.get('scheme') or '')
    if 'unionpay' in n and 'arca' not in n:
        return 'UnionPay'
    if 'mir' in n.split() or s == 'Mir':
        return 'Mir'
    if s.startswith('ArCa') or 'arca' in n:
        return 'ArCa'
    if s in ('Visa', 'Mastercard'):
        return s
    if 'visa' in n:
        return 'Visa'
    if 'master' in n or 'maestro' in n or 'cirrus' in n:
        return 'Mastercard'
    return 'Other'


def short_name(name):
    s = name
    s = s.replace('(non-personalised / instant)', 'Instant').replace('Mastercard', 'MC').replace('VISA', 'Visa')
    s = s.replace(' debit', '').replace(' Debit', '').replace(' (debit)', '').replace(' Card', '').replace('Evoca ', '')
    s = s.replace('Arca Classic / ArCa-UnionPay', 'ArCa Classic').replace('INFINITE', 'Infinite').replace(' for RA non-residents', ' (non-resident)')
    return re.sub(r'\s+', ' ', s).strip()


def fee_display(c, norm):
    if norm and norm.get('fee_display'):
        return norm['fee_display']
    raw = (c.get('service_fee') or {}).get('raw') or ''
    fee = c.get('fee_amd_year')
    if fee is None:
        return 'Not published'
    if fee == 0:
        return 'Free'
    per = c.get('fee_period') or (c.get('service_fee') or {}).get('period')
    txt = f'{int(fee):,} AMD / yr'
    if per == 'month':
        txt += f' ({int(round(fee / 12)):,} a month)'
    return txt


def strip_reason(c):
    key = f"{c['bank']}|{c['card_name_en']}"
    if key in STRIP_WHY:
        return STRIP_WHY[key]
    av = c.get('availability')
    if av == 'non-resident variant':
        return 'Non-resident variant'
    if av == 'legacy':
        return 'Legacy · no longer issued'
    if av in STRIP_REASON:
        return STRIP_REASON[av]
    return STRIP_REASON.get(c.get('sub_segment'), 'Niche')


def raw_of(c):
    p = c.get('perks') or {}
    cb = c.get('cashback') or {}
    i = c.get('interest_on_balance') or {}
    du = c.get('deposit_uplift') or {}
    return {
        'Service fee': (c.get('service_fee') or {}).get('raw'),
        'Fee waiver': c.get('service_fee_waiver'),
        'Issuance fee': (c.get('issuance_fee') or {}).get('raw'),
        'Interest on balance': i.get('conditions') or i.get('raw'),
        'Deposit uplift': (du.get('raw') or '') + ((' — ' + du['notes']) if du.get('notes') else '') if du else None,
        'ATM – own bank': c.get('atm_own'),
        'ATM – other Armenian banks': c.get('atm_other_ra'),
        'ATM – abroad': c.get('atm_abroad'),
        'Free ATM allowance': c.get('free_atm'),
        'Card-to-card': c.get('card_to_card'),
        'Transfer – same bank': c.get('transfer_own_bank'),
        'Transfer – other banks': c.get('transfer_other_ra'),
        'FX – preferential': c.get('fx_preferential'),
        'FX – markup abroad': c.get('fx_markup_abroad'),
        'Cashback': cb.get('raw'),
        'Loyalty programme': c.get('loyalty_programme'),
        'Lounge': p.get('lounge_access'),
        'Insurance': p.get('insurance'),
        'Concierge': p.get('concierge'),
        'Subscriptions': p.get('subscriptions'),
        'Taxi / transport': p.get('taxi_transport'),
        'Referral': p.get('referral'),
        'Gamification': p.get('gamification'),
        'Other perks': p.get('other'),
    }


def next_version():
    nums = [int(m.group(1)) for f in VERSIONS.glob('debit-card-tiers_*_v*.html') if (m := re.search(r'_v(\d+)\.html$', f.name))]
    return max(nums, default=0) + 1


def archive(html, note):
    VERSIONS.mkdir(exist_ok=True)
    digest = lambda t: hashlib.md5(re.sub(r'"version":"[^"]*"', '', t).encode()).hexdigest()
    last = sorted(VERSIONS.glob('debit-card-tiers_*_v*.html'), key=lambda f: int(re.search(r'_v(\d+)', f.name).group(1)))
    if last and digest(last[-1].read_text()) == digest(html):
        return None
    n = next_version()
    path = VERSIONS / f'debit-card-tiers_{dt.date.today().isoformat()}_v{n}.html'
    path.write_text(html)
    log = VERSIONS / 'CHANGELOG.md'
    head = '' if log.exists() else '# Dashboard versions\n\nEach entry is a full, self-contained copy of the page in this folder.\n\n'
    with log.open('a') as fh:
        fh.write(f"{head}- **v{n}** · {dt.datetime.now():%Y-%m-%d %H:%M} · `{path.name}` — {note or 'rebuild'}\n")
    return n


def build(note=None):
    src = json.loads(CARDS.read_text())
    fx = json.loads(FX.read_text())
    imgs = json.loads(IMAGES.read_text()) if IMAGES.exists() else {}
    cards = []
    for c in src['cards']:
        key = f"{c['bank']}|{c['card_name_en']}"
        norm = N.get(key)
        if norm is None and not c['in_debit_scope'] and c['card_name_en'] != 'Visa Wizz Air':
            continue  # gift / prepaid cards stay out
        if c.get('availability') == 'legacy' or key in LEGACY:
            continue  # no longer issued: not part of the market (Alex, 2026-09-21)
        fee = norm['fee'] if norm and 'fee' in norm else c.get('fee_amd_year')
        rec = {
            'id': re.sub(r'[^a-z0-9]+', '-', key.lower()).strip('-'),
            'bank': c['bank'], 'name': c['card_name_en'], 'short': short_name(c['card_name_en']),
            'local': c['card_name'] if c['card_name'] != c['card_name_en'] else None,
            'scheme': scheme_of(c), 'level': c.get('tier'), 'segment': c.get('sub_segment'), 'availability': c.get('availability'),
            'fee': fee, 'fee_display': fee_display(c, norm),
            'confidence': c.get('confidence'), 'url': c.get('url'), 'sources': c.get('sources') or [], 'gaps': c.get('gaps') or [],
            'notable': c.get('notable'), 'raw': {k: v for k, v in raw_of(c).items() if v},
        }
        im = imgs.get(key)
        if im and (HERE / im['file']).exists():
            rec['img'] = 'data:image/webp;base64,' + base64.b64encode((HERE / im['file']).read_bytes()).decode()
            rec['img_src'] = im['source']
        if norm:
            rec.update({k: v for k, v in norm.items() if k not in ('fee', 'fee_display')})
            rec['place'] = 'column'
            rec.setdefault('uplift', None)
            rec.setdefault('fx', None)
        else:
            rec['place'] = 'strip'
            rec['strip_reason'] = strip_reason(c)
            rec['interest_pct'] = c.get('interest_amd_pct')
            rec['cb_kind'] = c.get('cashback_kind')
            rec['cb_headline'] = c.get('cashback_headline_pct')
        cards.append(rec)

    banks = []
    fx_codes = {k: v for k, v in fx['banks'].items()}
    for b in BANK_ORDER + PENDING:
        f = fx_codes.get(b)
        fxo = None
        if f:
            def hs(r):
                return round((r['sell'] - r['buy']) / (r['sell'] + r['buy']) * 100, 3)
            usd, eur = f['USD'], f['EUR']
            usd_k = 'CARD' if 'CARD' in usd else 'CLEARING'
            eur_k = 'CARD' if 'CARD' in eur else 'CLEARING'
            fxo = {'usd': hs(usd[usd_k]), 'usd_kind': 'card rate' if usd_k == 'CARD' else 'non-cash rate', 'usd_rate': usd[usd_k],
                   'usd_noncash': hs(usd['CLEARING']) if 'CLEARING' in usd else None,
                   'eur': hs(eur[eur_k]), 'eur_kind': 'card rate' if eur_k == 'CARD' else 'non-cash rate', 'eur_rate': eur[eur_k]}
        banks.append({'id': b, 'name': BANK_NAME.get(b, b), 'pending': b in PENDING, 'fx': fxo,
                      'n_cards': sum(1 for x in cards if x['bank'] == b)})

    data = {'as_of': src['as_of'], 'fx_as_of': fx['fetched'], 'fx_source': fx['source'], 'banks': banks, 'cards': cards,
            'deposits': json.loads(DEPOSITS.read_text()),
            'version': f'v{next_version()} · {dt.date.today():%d %b %Y}'}

    html = TEMPLATE.read_text().replace('/*__DATA__*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    n = archive(html, note)
    if n is None:  # unchanged since the last archived version: keep its label
        last = sorted(VERSIONS.glob('debit-card-tiers_*_v*.html'), key=lambda f: int(re.search(r'_v(\d+)', f.name).group(1)))[-1]
        html = last.read_text()
    OUT.write_text(html)
    print('version:', f'v{n} archived' if n else 'unchanged, not archived')

    with CSV_OUT.open('w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['bank', 'card', 'tier', 'fee_amd_year', 'waiver_type', 'interest_rate', 'interest_threshold_amd', 'interest_via',
                    'deposit_uplift', 'atm_own_pct', 'atm_own_free', 'atm_other_pct', 'atm_other_free', 'atm_abroad_pct', 'atm_abroad_min',
                    'c2c_same_bank_pct', 'c2c_other_bank_pct', 'fx_markup_pct', 'fx_preferential', 'cashback_rules', 'cashback_promo', 'perk_tags', 'note'])
        for r in cards:
            if r['place'] != 'column':
                continue

            def atm(a, k):
                if a is None:
                    return 'n/p'
                if a == 'na':
                    return 'n/a'
                if k == 'free':
                    return f"{a['fm']:,}/month" if a.get('fm') else (f"{a['fd']:,}/day" if a.get('fd') else '')
                if k == 'min':
                    return a.get('min') or ''
                return a['pct']
            i = r.get('int') or {}
            w.writerow([r['bank'], r['name'], r['tier'], r['fee'], r['waiver']['type'], i.get('rate', 'n/p'), i.get('thr', ''), i.get('via', ''),
                        (r.get('uplift') or {}).get('text', ''), atm(r['atm_own'], 'pct'), atm(r['atm_own'], 'free'), atm(r['atm_other'], 'pct'),
                        atm(r['atm_other'], 'free'), atm(r['atm_abroad'], 'pct'), atm(r['atm_abroad'], 'min'),
                        r.get('c2c_in') if r.get('c2c_in') is not None else 'n/p', r.get('c2c_out') if r.get('c2c_out') is not None else 'n/p',
                        (r.get('fx') or {}).get('markup') or '', (r.get('fx') or {}).get('pref') or '',
                        '; '.join(f"{x['src']} {x['rate']}% {x['scope']}" for x in r['cb']['rules']), r['cb'].get('promo') or '',
                        '; '.join(sorted({p[0] for p in r['perks']})), r.get('note', '')])
    n_col = sum(1 for x in cards if x['place'] == 'column')
    print(f'{OUT.name}: {len(html) / 1024:.0f} KB, {n_col} tier cards, {len(cards) - n_col} niche cards')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--note', help='one line for versions/CHANGELOG.md')
    build(ap.parse_args().note)
