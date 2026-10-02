"""Default engine parameters (first draft, to be tuned in the workbook's Inputs sheet)."""
from mcc_ref import PICKABLE, ELIGIBLE

TIERS = ['Free', 'Black', 'Premium', 'Elite']
CARD_TIER = {'Arca': 'Black', 'Visa Classic': 'Black', 'Visa Gold': 'Premium', 'MasterCard World': 'Premium',
             'MasterCard World Elite': 'Elite', 'Visa Infinite': 'Elite', 'Visa Infinite Metal': 'Elite',
             'Visa Digital': 'Free', 'Visa Business Platinum': 'No cashback',
             'MasterCard Business Digital': 'No cashback'}
UNKNOWN = 'Unknown (card issued before Aug-25)'
UNKNOWN_TIER = 'No cashback'          # Alex 24.09: no card info -> no cashback

# model targets (v8 'Control panel', cashback target % of non-cash and monthly cap)
TARGET = {'Free': 0.0, 'Black': 0.005, 'Premium': 0.01, 'Elite': 0.01}
TARGET_SRC = {'Free': "D19 / D20", 'Black': "D42 / D43", 'Premium': "D65 / D66", 'Elite': "D88 / D89"}
CAP = {'Free': 5000, 'Black': 5000, 'Premium': 20000, 'Elite': 30000}

P = {  # per-tier programme parameters
    'active':       {t: 1 for t in TIERS},                   # kill switch; Free runs at 0% rates
    'menu_size':    {t: 7 for t in TIERS},
    'picks':        {t: 4 for t in TIERS},
    'base_mode':    {t: 'Pickable' for t in TIERS},          # Pickable / Automatic / Off
    'base_rate':    {'Free': 0.0, 'Black': 0.005, 'Premium': 0.01, 'Elite': 0.01},
    'cap':          CAP,
    'partner_cap':  {'Free': 0, 'Black': 5000, 'Premium': 10000, 'Elite': 20000},
    'partner_compete': {t: 'Yes' for t in TIERS},            # partner offers take one of the picks
    'nonchooser_share': {'Free': 0.3, 'Black': 0.3, 'Premium': 0.25, 'Elite': 0.2},
    'nonchooser_rule':  {t: 'Flat rate' for t in TIERS},     # Nothing / Flat rate / Auto-pick
    'nc_rate':      {'Free': 0.0, 'Black': 0.01, 'Premium': 0.01, 'Elite': 0.01},   # flat rate for non-choosers (Alex: 1%)
    'partner_replace': {t: 'Yes' for t in TIERS},            # partner offer replaces the same bank category on the menu
    'min_spend':    {t: 0 for t in TIERS},                   # min monthly eligible spend to earn
    'min_txn_haircut': {t: 0.0 for t in TIERS},              # share of spend below min transaction amount
}
# partner-funded offers: 2 slots per tier (category, rate, coverage of category spend, partner-funded share)
PARTNER = {
    'Free':    [('TAX', 0.0, 0.6, 1.0), ('RES', 0.0, 0.15, 1.0)],
    'Black':   [('TAX', 0.10, 0.6, 1.0), ('RES', 0.10, 0.15, 1.0)],
    'Premium': [('TAX', 0.10, 0.6, 1.0), ('TRV', 0.10, 0.2, 1.0)],
    'Elite':   [('RES', 0.15, 0.15, 1.0), ('TRV', 0.10, 0.2, 1.0)],
}
PARTNER_NAME = {'TAX': 'Partner taxi app', 'RES': 'Partner restaurants', 'TRV': 'Partner travel agency'}
# headline rates by category and tier (Free kept at 0: engine-ready)
RATES = {  # Black, Premium, Elite
    'SUP': (0.01, 0.01, 0.015), 'RES': (0.03, 0.03, 0.05), 'FST': (0.03, 0.05, 0.05), 'DEL': (0.03, 0.05, 0.05),
    'TAX': (0.05, 0.05, 0.07), 'TRN': (0.05, 0.05, 0.05), 'FUE': (0.02, 0.03, 0.03), 'AUT': (0.03, 0.03, 0.05),
    'PHA': (0.05, 0.05, 0.05), 'MED': (0.03, 0.03, 0.05), 'BEA': (0.05, 0.05, 0.07), 'CLO': (0.03, 0.05, 0.05),
    'ELE': (0.01, 0.01, 0.02), 'HOM': (0.02, 0.03, 0.03), 'KID': (0.03, 0.05, 0.05), 'ENT': (0.05, 0.07, 0.07),
    'SPO': (0.05, 0.05, 0.07), 'TRV': (0.02, 0.03, 0.05), 'ONL': (0.02, 0.03, 0.03), 'JEW': (0.01, 0.01, 0.02),
}
RATE = {t: {c: (0.0 if t == 'Free' else RATES[c][TIERS.index(t) - 1]) for c in PICKABLE} for t in TIERS}
# menu role per category: Always (bank-pushed discovery), If spent (personalised: client's top spend), No
ROLE = {t: {c: 'If spent' for c in PICKABLE} for t in TIERS}
for t in TIERS:
    ROLE[t]['ENT'] = 'Always'
ROLE['Black']['ELE'] = 'No'
ROLE['Black']['JEW'] = 'No'

# interchange (issuer), by category: domestic rate and share of spend that is foreign / cross-border
IF_DOM_DEFAULT, IF_INTL = 0.006, 0.015
FOREIGN = {c: 0.03 for c in ELIGIBLE}
FOREIGN.update({'TRV': 0.7, 'ONL': 0.5, 'ELE': 0.1, 'CLO': 0.1, 'ENT': 0.2, 'JEW': 0.1, 'OTH': 0.1})
IF_DOM = {c: IF_DOM_DEFAULT for c in ELIGIBLE}
