"""Per-card normalisation for the tier dashboard.

One entry per card that sits in the four tier columns, keyed "Bank|card_name_en" exactly as in
data/2026-09-18-competitor-cards.json. Every number is read off that record's raw tariff text;
where the text was ambiguous the choice is written in `note`. To add a bank (e.g. ACBA), add its
records to the JSON and its entries here - cards without an entry fall into the niche strip.

Field shapes
  tier      free | plus | premium | elite
  atm_*     {'pct': %, 'fm': free AMD per month, 'fd': free AMD per day, 'min': min fee AMD}
            None = not published, 'na' = card cannot be used there
  c2c_in    card-to-card to a card of the same bank, %   (None = not published)
  c2c_out   card-to-card to another Armenian bank, %
  int       {'rate': %, 'thr': min AMD balance, 'bands': [[upto, %], [None, %]], 'via': 'card'|'package'}
  uplift    None or {'text':..., 'via': 'card'|'package'}
  waiver    {'type': balance|spend|deposit|package|payroll|promo|app|none|free, 'text': ...}
  fx        None or {'markup': %|None, 'pref': bool, 'text': ...}
  cb        {'rules': [{'src': bank|points|arca, 'rate': %, 'scope': all|dom|foreign|trav|foth}],
             'cap': {'bank': AMD/month, 'points': ..., 'arca': ...}, 'text': ..., 'promo': ...}
  perks     list of [tag, text]
  partners  list of [name, benefit]
"""

ARCA = {'src': 'arca', 'rate': 2.0, 'scope': 'dom'}
ARCA_CAP = 60000
ARCA_TXT = 'National ArCa scheme: 2% on domestic non-cash payments ≥1,000 AMD, capped 6,000 AMD per payment and 60,000 AMD a month. Funded by ArCa and the state budget, not the bank.'


def A(pct, fm=None, fd=None, mn=None):
    return {'pct': pct, 'fm': fm, 'fd': fd, 'min': mn}


def I(rate, thr=0, bands=None, via='card', text=None):
    return {'rate': rate, 'thr': thr, 'bands': bands, 'via': via, 'text': text}


def W(type_, text):
    return {'type': type_, 'text': text}


NONE_CB = {'rules': [], 'cap': {}, 'text': 'No cashback published.', 'promo': None}


def arca_cb(extra=None):
    return {'rules': [ARCA], 'cap': {'arca': ARCA_CAP}, 'text': ARCA_TXT, 'promo': extra}


# ---------------------------------------------------------------- Fast Bank
FB_ATM = dict(atm_own=A(0.5), atm_other=A(1.2), atm_abroad=A(2.0, mn=1500))
FB_C2C = dict(c2c_in=0.0, c2c_out=0.5, c2c_note='0% between Fast Bank cards (confirmed by the Fast Bank team, 21.09.2026); 0.5% "Transfer to Card" to other banks via the mobile app (card tariff, 26.06.2026).')
FB_INT = I(4.0, 0, text='4% (4.07% APY) on AMD balances, no threshold, paid monthly.')
FB_SRC = 'Fees: Fast Bank card tariff TC 04 01#12 (effective 26.06.2026); benefits: Fast Bank benefit brochures (downloaded manually 21.09.2026).'
FB_VISA_OFFERS = ['Merchant discounts', 'Visa Armenia offers (time-limited): Buy.am 30% back, Yerevan Mall app 15% on cinema tickets, 16% at Cole Haan / New Balance / Puma / Levi\'s, 10–15% at Square One, Segafredo, Cinnabon, Paul, AKG; e-learning 10–25% (British Council, Skillshare, edX).']
FB_INF_PERKS = [['Lounge', 'DragonPass (Visa Airport Companion): 20 visits if ≥$400 non-cash spend in the prior 35 days, otherwise 3 a year.'],
                ['Fast Track', '6 Fast Tracks a year at Zvartnots and 50+ international airports.'],
                ['Travel insurance', 'International travel insurance when tickets / hotel are paid with the card (accident, baggage and flight delay, missed flight, loss of money).'],
                ['Concierge', 'Visa Concierge chatbot (Viber, Telegram, WhatsApp).'],
                ['Airport services', 'Free Zvartnots parking up to 3 times a year; free baggage wrapping 10 times a year.'],
                ['Roaming data', '3GB roaming 3 times a year (193 countries); Ucom 500MB roaming 6 times a year.'],
                ['Travel & hotel partners', 'Agoda up to 12%, Booking.com up to 8%.'], ['Car rental', 'Avis up to 35%, SIXT up to 15%.'],
                ['Entertainment', 'BookingBash ULTIMATE annual subscription (up to 50% off attractions).']]
FB_INF_P = [['DragonPass', '20 / 3 lounge visits a year'], ['Visa Concierge', 'Chatbot concierge, Fast Track, parking'], ['Agoda', 'Up to 12% off'], ['Booking.com', 'Up to 8% off'],
            ['Avis', 'Up to 35% off'], ['SIXT', 'Up to 15% off'], ['BookingBash', 'ULTIMATE subscription'], ['Ucom', '500MB roaming ×6']]
FB_GIVE = ['Giveaways', 'Periodic Visa card giveaways (e.g. Spring Giveaway 2026, 500,000 AMD Fast × Visa draw).']

N = {
    'FastBank|Arca Classic': dict(tier='free', atm_own=A(0.2), atm_other=A(0.8), atm_abroad='na', **FB_C2C, int=FB_INT,
        waiver=W('promo', 'Free for the card\'s whole validity when ordered in the app (5 Dec 2025 – 30 Sep 2026, one card); otherwise free with 50k–5m AMD in deposits/bonds of 181+ days.'),
        cb=arca_cb(), perks=[], partners=[]),
    'FastBank|VISA Classic': dict(tier='plus', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('deposit', 'Free with 50k–5m AMD in deposits/bonds of 181+ days (one card per client).'),
        cb=NONE_CB, perks=[FB_GIVE], partners=[]),
    'FastBank|Visa Digital': dict(tier='free', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('free', 'No service fee.'), cb=NONE_CB, perks=[], partners=[],
        note='Cash via Apple Pay / Google Pay at the Visa-card ATM rates (card tariff, 26.06.2026).'),
    'FastBank|VISA Gold': dict(tier='plus', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('deposit', 'Free with 5–20m AMD in deposits/bonds of 181+ days.'),
        cb=NONE_CB, perks=[FB_VISA_OFFERS, ['Travel & hotel partners', 'Booking.com up to 8% off rooms.'], ['Entertainment', 'BookingBash ADVENTURER subscription (up to 50% off attractions).'], FB_GIVE],
        partners=[['Booking.com', 'Up to 8% off'], ['BookingBash', 'ADVENTURER subscription'], ['Buy.am', '30% back'], ['Yerevan Mall / KinoPark', '15% off tickets'], ['E-learning (British Council, FutureLearn, Skillshare, edX)', '10–25% off']],
        note='Benefits are Visa Armenia network offers, mostly time-limited.'),
    'FastBank|Mastercard World': dict(tier='premium', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('deposit', 'Free with 20–50m AMD in deposits/bonds of 181+ days.'),
        cb=dict(NONE_CB, promo='Campaigns only: up to 25% on spend abroad / foreign online, capped 25,000 AMD (24 Nov–31 Dec); 12,000 AMD for 100k AMD spend on a new card (1 May–31 Jul).'),
        perks=[['Lounge', 'LoungeKey: 6 visits a year, usable for guests.'], ['Fast Track', 'Mastercard Travel Pass: 6 Fast Tracks a year at 100+ European airports.'],
               ['Concierge', 'Mastercard Concierge.'], ['Roaming data', 'Flexiroam 1GB a year (5 days) + 15% off.']],
        partners=[['LoungeKey', '6 visits a year, guests allowed'], ['Mastercard Travel Pass', '6 Fast Tracks a year'], ['Flexiroam', '1GB roaming data']]),
    'FastBank|VISA INFINITE': dict(tier='elite', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('deposit', 'Free with 50–100m AMD in deposits/bonds of 181+ days.'),
        cb=NONE_CB, perks=FB_INF_PERKS + [FB_GIVE], partners=FB_INF_P),
    'FastBank|Mastercard World Elite': dict(tier='elite', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('deposit', 'Free with 50–100m AMD in deposits/bonds of 181+ days.'),
        cb=dict(NONE_CB, text='No bank cashback; Mastercard Travel Rewards up to 20% back at 500+ merchants abroad (network offer).'),
        perks=[['Lounge', 'Unlimited LoungeKey access (1,200+ lounges).'], ['Fast Track', 'Unlimited Fast Track at 100+ European airports incl. Zvartnots.'],
               ['Travel insurance', 'AIG travel insurance for holder and family: medical & evacuation to $500,000, accident to $500,000, baggage $3,000, trip cancellation $7,500, delay $500.'],
               ['Concierge', 'Mastercard Concierge.'], ['Roaming data', 'Flexiroam 3GB a year (15 days) + 15% off.'],
               ['Travel & hotel partners', 'Mastercard Travel Rewards up to 20% back; Priceless experiences.']],
        partners=[['LoungeKey', 'Unlimited'], ['Mastercard Travel Pass', 'Unlimited Fast Track'], ['AIG', 'Family travel insurance'], ['Flexiroam', '3GB roaming data'], ['Mastercard Travel Rewards / Priceless', 'Up to 20% back']]),
    'FastBank|Visa Infinite Metal': dict(tier='elite', **FB_ATM, **FB_C2C, int=FB_INT,
        waiver=W('deposit', 'Product page: one card free with 50m+ AMD in deposits/bonds (the card tariff\'s deposit ladder lists only Infinite / World Elite).'),
        cb=NONE_CB, perks=FB_INF_PERKS, partners=FB_INF_P),
}

# ---------------------------------------------------------------- Ameriabank
AM_C2C = dict(c2c_in=0.3, c2c_out=0.5, c2c_note='0.3% to Ameriabank cards, 0.5% to other Armenian banks\' cards (tariff ed. 46, rows 25–26).')
AM_INT = I(0.0, 0, text='0% on card balances (only student cards pay 3%).')
AM_PKG_UP = {'text': 'Premium / Partner package: +0.25% / +0.35% on term deposits and +1% on AMD savings accounts. The packages need 40m / 120m AMD in average balances (ed. 22, 22 Aug 2026), so they are not tied to the card.',
             'via': 'package', 'dep_pp': 0.25, 'min_bal': 40000000}
AM_PKG_W = W('package', 'Free inside the Premium (40m AMD avg balance) or Partner (120m) package. MyAmeria app price: Gold 10,000, Platinum / World 20,000, Signature 50,000 AMD.')
AM_FX_V = {'markup': 2.0, 'pref': False, 'text': 'Tariff: Visa exchange rates include a 2% bank fee.'}
AM_FX_PKG = {'markup': 2.0, 'pref': True, 'text': 'Visa rates include a 2% bank fee; Premium/Partner package holders get discretionary preferential FX (no rate published).'}
AM_INS = ['Card insurance', 'Optional card-transaction insurance, 3,000–5,000 AMD a year (bundled travel insurance withdrawn 2023).']
AM_REF = ['Referral', 'MyAmeria "Invite a friend" (Jul–Aug 2026, ended): 5,000 AMD per referral from the 5th, plus a trip draw.']
AM_PLAT_PERKS = [['Lounge', 'LoungeKey: 2 visits a year (standing); campaign to 30 Sep 2026 lifts it to 6 + 2 guests if ≥$400 non-cash spend in the prior 35 days.'],
                 ['Fast Track', 'Fast Track 2× Zvartnots, 6× international.'],
                 ['Concierge', 'Visa Concierge (chatbot, phone, e-mail).']]
AM_SIG_PERKS = [['Lounge', 'LoungeKey: 4 visits a year (standing); campaign to 30 Sep 2026 lifts it to 10 + 3 guests if ≥$400 non-cash spend in the prior 35 days.'],
                ['Fast Track', 'Fast Track 4× Zvartnots, 10× international.'],
                ['Concierge', 'Visa Concierge.'],
                ['Taxi & transfers', 'Partner package adds 3 luxury car transfers a year.']]
AM_VISA_P = [['Visa', 'Airport Companion / LoungeKey lounges, Fast Track and Visa Concierge']]
AM_DISPUTE_PLAT = 'Fee disputed: two reads of the same tariff PDF give 30,000 or 60,000 AMD. Confirm with the bank.'
AM_DISPUTE_SIG = 'Fee disputed: two reads of the same tariff PDF give 60,000 or 40,000 AMD. Confirm with the bank.'

N.update({
    'Ameriabank|ArCa Classic': dict(tier='free', atm_own=A(0.5, fm=300000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT,
        waiver=W('app', 'No standing waiver (free-for-life campaign closed 30 Jun 2026); 2,500 AMD/yr if ordered in MyAmeria.'),
        cb=arca_cb(), perks=[], partners=[]),
    'Ameriabank|VISA Classic': dict(tier='plus', atm_own=A(0.5, fm=300000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, fx=AM_FX_V,
        waiver=W('app', '2,500 AMD/yr if ordered in MyAmeria; free when issued to carry a scoring overdraft.'),
        cb=NONE_CB, perks=[AM_INS, AM_REF], partners=[]),
    'Ameriabank|Mastercard Standard': dict(tier='plus', atm_own=A(0.5, fm=300000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT,
        waiver=W('app', '2,500 AMD/yr if ordered in MyAmeria; free when issued to carry a scoring overdraft.'),
        cb=dict(NONE_CB, promo='Campaign "1% cashback for new Mastercard holders" (dates and terms unreadable).'),
        perks=[AM_INS, AM_REF], partners=[]),
    'Ameriabank|VISA Classic Digital': dict(tier='free', atm_own=A(0.5, fm=300000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, fx=AM_FX_V,
        waiver=W('promo', 'Free for new clients to 31 Dec 2026, plus up to 2,000 AMD (1,000 on issue + 1,000 after first payment).'),
        cb=dict(NONE_CB, promo='Welcome: up to 2,000 AMD for new clients (to 31 Dec 2026).'), perks=[AM_INS], partners=[]),
    'Ameriabank|Mastercard Standard Digital': dict(tier='free', atm_own=A(0.5, fm=300000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT,
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[AM_INS], partners=[]),
    'Ameriabank|VISA Gold': dict(tier='plus', atm_own=A(0.5, fm=500000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, uplift=AM_PKG_UP, fx=AM_FX_PKG,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[AM_INS], partners=[]),
    'Ameriabank|Mastercard Gold': dict(tier='plus', atm_own=A(0.5, fm=500000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, uplift=AM_PKG_UP,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[AM_INS], partners=[]),
    'Ameriabank|VISA Gold Digital': dict(tier='plus', atm_own=A(0.5, fm=500000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, fx=AM_FX_V,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[AM_INS], partners=[]),
    'Ameriabank|Mastercard Gold Digital': dict(tier='plus', atm_own=A(0.5, fm=500000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[AM_INS], partners=[]),
    'Ameriabank|VISA Platinum': dict(tier='premium', atm_own=A(0.5, fm=700000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, uplift=AM_PKG_UP, fx=AM_FX_PKG,
        waiver=AM_PKG_W, cb=NONE_CB, perks=AM_PLAT_PERKS + [AM_INS], partners=AM_VISA_P),
    'Ameriabank|Mastercard World': dict(tier='premium', atm_own=A(0.5, fm=700000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, uplift=AM_PKG_UP,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[['Concierge', 'Concierge ("international virtual assistant") mentioned in the card terms; no Mastercard benefit sheet published.'], AM_INS], partners=[]),
    'Ameriabank|VISA Platinum Digital': dict(tier='premium', atm_own=A(0.5, fm=700000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, fx=AM_FX_V,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[['Lounge', 'Visa Platinum lounge set published by tier; not stated whether the digital card is included.'], ['Concierge', 'Visa Concierge.'], AM_INS], partners=AM_VISA_P),
    'Ameriabank|Mastercard World Digital': dict(tier='premium', atm_own=A(0.5, fm=700000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[AM_INS], partners=[]),
    'Ameriabank|VISA Signature': dict(tier='elite', atm_own=A(0.5, fm=1000000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, uplift=AM_PKG_UP, fx=AM_FX_PKG,
        waiver=AM_PKG_W, cb=NONE_CB, perks=AM_SIG_PERKS + [AM_INS], partners=AM_VISA_P),
    'Ameriabank|VISA Signature Digital': dict(tier='elite', atm_own=A(0.5, fm=1000000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, fx=AM_FX_V,
        waiver=AM_PKG_W, cb=NONE_CB, perks=[['Lounge', 'Visa Signature lounge set published by tier; not stated whether the digital card is included.'], ['Concierge', 'Visa Concierge.'], AM_INS], partners=AM_VISA_P),
})

# ---------------------------------------------------------------- Ardshinbank
AR_C2C = dict(c2c_in=0.0, c2c_out=None, c2c_note='Free between Ardshinbank cards. To other banks: "item 4.3 of each card\'s tariff package", not printed on the C2C page (other banks\' cardholders pay 0.4% to use the service).')
AR_INT2 = I(2.0, 5000000, text='2% on AMD balances of 5m AMD and above; 0% below.')
AR_INT3 = I(3.0, 5000000, text='3% on AMD balances of 5m AMD and above; 0% below.')
AR_INT3_10 = I(3.0, 10000000, text='3% on AMD balances of 10m AMD and above; 0% below.')
AR_ABR = A(2.0, mn=1500)
AR_STD = dict(atm_own=A(0.5, fd=100000), atm_other=A(1.5, fd=100000), atm_abroad=AR_ABR)
AR_LOY = ['Loyalty points', 'Status | Plus bank-wide programme (page JS-only, card participation unverified).']
AR_CINS = ['Card insurance', 'Optional services package: 200,000 AMD card insurance for 1 year.']
AR_GOLD_P = [['Agoda', 'Up to 12% off (Visa Gold and above)'], ['Local merchants', '10–15% off at pharmacies, cafés, wellness, retail (Gold and above)']]
AR_PREM_P = [['Booking.com', 'Up to 7% back (Visa Platinum, Signature, Infinite)'], ['Agoda', 'Up to 12% off'], ['Avis', '20% off (Platinum), 35% (Signature/Infinite)'], ['GG (ride-hailing)', 'Discount for Visa premium cards (terms unreadable)']]

N.update({
    'Ardshinbank|Mastercard Debit': dict(tier='plus', **AR_STD, **AR_C2C, int=AR_INT2,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 100,000 AMD; year 1 free with a 1m AMD term deposit.'),
        cb=NONE_CB, perks=[AR_CINS, AR_LOY], partners=[]),
    'Ardshinbank|Visa Classic': dict(tier='plus', **AR_STD, **AR_C2C, int=AR_INT2,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 100,000 AMD.'),
        cb=NONE_CB, perks=[AR_CINS, AR_LOY], partners=[]),
    'Ardshinbank|Arca': dict(tier='free', **AR_STD, **AR_C2C, int=AR_INT2,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 60,000 AMD.'),
        cb=arca_cb(), perks=[AR_CINS, AR_LOY], partners=[]),
    'Ardshinbank|Mastercard Debit (non-personalised / instant)': dict(tier='free', atm_own=A(0.3), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AR_C2C, int=AR_INT2,
        waiver=W('free', 'No service fee.'), cb=NONE_CB, perks=[AR_LOY], partners=[]),
    'Ardshinbank|Visa Classic (non-personalised / instant)': dict(tier='free', atm_own=A(0.3), atm_other=A(1.5), atm_abroad=A(2.0, mn=1500), **AR_C2C, int=AR_INT2,
        waiver=W('free', 'No service fee.'), cb=NONE_CB, perks=[AR_LOY], partners=[]),
    'Ardshinbank|Arca (non-personalised / instant)': dict(tier='free', atm_own=A(0.3), atm_other=A(1.5), atm_abroad=A(2.0, mn=1500), **AR_C2C, int=AR_INT2,
        waiver=W('free', 'No service fee.'), cb=arca_cb(), perks=[AR_LOY], partners=[]),
    'Ardshinbank|Visa Gold Debit': dict(tier='plus', **AR_STD, **AR_C2C, int=AR_INT3,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 200,000 AMD.'),
        cb=NONE_CB, perks=[['Merchant discounts', 'Visa Gold benefits: Agoda up to 12%, 10–15% at local merchants.'], AR_CINS, AR_LOY], partners=AR_GOLD_P),
    'Ardshinbank|Visa Platinum Debit': dict(tier='premium', **AR_STD, **AR_C2C, int=AR_INT3,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 200,000 AMD.'),
        cb=dict(NONE_CB, text='No card cashback; Booking.com "up to 7% back" is a Visa partner benefit.'),
        perks=[['Lounge', 'Visa Airport Companion (DragonPass): 1 visit a year, unlimited after $400 non-cash spend in 12 months.'], ['Fast Track', 'Fast Track included.'],
               ['Travel insurance', 'Travel and medical insurance.'], ['Concierge', 'Visa Concierge (Telegram, WhatsApp, Viber).'],
               ['Travel & hotel partners', 'Booking.com up to 7% back, Agoda up to 12%.'], ['Car rental', 'Avis 20% off.'], ['Taxi & transfers', 'GG ride-hailing discount.'], AR_LOY],
        partners=AR_PREM_P),
    'Ardshinbank|Mastercard World': dict(tier='premium', **AR_STD, **AR_C2C, int=AR_INT3,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 200,000 AMD.'),
        cb=NONE_CB, perks=[AR_CINS, AR_LOY], partners=[]),
    'Ardshinbank|Visa Gold Debit Digital Card': dict(tier='plus', atm_own=A(0.5), atm_other=A(1.5), atm_abroad=AR_ABR, **AR_C2C, int=AR_INT3,
        waiver=W('free', 'No service fee.'), cb=NONE_CB,
        perks=[['Merchant discounts', 'Visa Gold benefits: Agoda up to 12%, 10–15% at local merchants.'], AR_LOY], partners=AR_GOLD_P,
        note='No free daily ATM allowance on the digital card.'),
    'Ardshinbank|Visa Signature Debit': dict(tier='elite', atm_own=A(0.5, fd=200000), atm_other=A(1.5, fd=200000), atm_abroad=AR_ABR, **AR_C2C, int=AR_INT3,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 500,000 AMD.'),
        cb=dict(NONE_CB, text='No card cashback; Booking.com "up to 7% back" is a Visa partner benefit.'),
        perks=[['Lounge', 'DragonPass: 4 visits a year, unlimited after $400 non-cash spend in 12 months; $32 per extra visit.'], ['Fast Track', 'Fast Track included.'],
               ['Travel insurance', 'Travel insurance, baggage cover, card protection.'], ['Concierge', 'Visa Concierge.'],
               ['Entertainment', 'BookingBash annual subscription (up to 50% off entertainment).'], ['Travel & hotel partners', 'Booking.com up to 7% back, Agoda up to 12%.'],
               ['Car rental', 'Avis 35% off.'], ['Taxi & transfers', 'GG ride-hailing discount.'], AR_LOY],
        partners=AR_PREM_P + [['DragonPass', '4 lounge visits a year'], ['BookingBash', 'Free annual subscription']]),
    'Ardshinbank|Mastercard World Black Edition': dict(tier='elite', atm_own=A(0.5, fd=100000), atm_other=A(1.5, fd=100000), atm_abroad=AR_ABR, **AR_C2C, int=AR_INT3,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 500,000 AMD.'), cb=NONE_CB,
        perks=[['Lounge', 'LoungeKey: 600 lounges, visit allowance not published.'], ['Travel insurance', 'Travel, medical and baggage insurance.'], ['Concierge', 'Support-desk service.'], AR_LOY],
        partners=[['LoungeKey', 'Lounge access (allowance not published)']], note='Abroad ATM fee taken from the non-resident twin (2%, min 1,500 AMD).'),
    'Ardshinbank|Visa Infinite Debit': dict(tier='elite', atm_own=A(0.5, fd=200000), atm_other=A(1.5, fd=200000), atm_abroad=AR_ABR, **AR_C2C, int=AR_INT3_10,
        waiver=W('none', 'No waiver published.'),
        cb=dict(NONE_CB, text='No card cashback; Booking.com "up to 7% back" is a Visa partner benefit.'),
        perks=[['Lounge', 'DragonPass: 6 visits a year, unlimited after $400 non-cash spend in 12 months.'], ['Fast Track', 'Fast Track included.'],
               ['Travel insurance', 'Travel and medical insurance.'], ['Concierge', 'Visa Concierge.'], ['Entertainment', 'BookingBash annual subscription.'],
               ['Travel & hotel partners', 'Booking.com up to 7% back, Agoda up to 12%.'], ['Car rental', 'Avis 35% off.'], ['Taxi & transfers', 'GG ride-hailing discount.'], AR_LOY],
        partners=AR_PREM_P + [['DragonPass', '6 lounge visits a year'], ['BookingBash', 'Free annual subscription']]),
    'Ardshinbank|Mastercard World Elite': dict(tier='elite', atm_own=A(0.5, fd=200000), atm_other=A(1.5), atm_abroad=AR_ABR, **AR_C2C, int=AR_INT3_10,
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[AR_LOY], partners=[],
        note='Other-bank ATM fee published only as "tiered up to 1.5%"; 1.5% used.'),
})

# ---------------------------------------------------------------- Conversebank
CV_C2C = dict(c2c_in=0.5, c2c_out=0.5, c2c_note='0.5% card-to-card in remote banking (debit), to Converse or other ArCa banks.')
CV_PKG_INT = I(4.0, 50000, via='package', text='Not published for the card; inside a C360 package the account pays 4–4.25% on AMD balances above 50,000 AMD (4% used).')
CV_PTS = ['Loyalty points', 'Converse Points: 1 point per 1,000 AMD spent; gifts only, no cash value.']

N.update({
    'Conversebank|Arca Classic / ArCa-UnionPay': dict(tier='free', atm_own=A(0.2), atm_other=A(1.0), atm_abroad=A(3.2), **CV_C2C, int=CV_PKG_INT,
        waiver=W('package', '0 AMD as the primary card of the C360 "Neo Light" package (50 AMD/month, waivable on balance).'),
        cb=arca_cb(), perks=[CV_PTS], partners=[], note='Abroad only through the UnionPay co-badge (3.2% AMD / 3.3% FX).'),
    'Conversebank|Visa Electron': dict(tier='plus', atm_own=A(0.2), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **CV_C2C, int=I(0.0, text='No interest on the card balance.'),
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[CV_PTS], partners=[]),
    'Conversebank|Cirrus/Maestro': dict(tier='plus', atm_own=A(0.2), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **CV_C2C, int=I(0.0, text='No interest on the card balance.'),
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[CV_PTS], partners=[]),
    'Conversebank|Visa Classic': dict(tier='plus', atm_own=A(0.2), atm_other=A(1.0), atm_abroad=A(2.0, mn=2500), **CV_C2C, int=CV_PKG_INT,
        waiver=W('package', '0 AMD as the primary card of the C360 "Neo" package (500 AMD/month, waived at 2m AMD average daily balance).'),
        cb=NONE_CB, perks=[CV_PTS], partners=[['Visa', 'Generic Visa offers widget (no specific offers published)']]),
    'Conversebank|Mastercard Standard': dict(tier='plus', atm_own=A(0.2), atm_other=A(1.0), atm_abroad=A(2.0, mn=2500), **CV_C2C, int=CV_PKG_INT,
        waiver=W('package', '0 AMD as the primary card of the C360 "Neo" package (500 AMD/month, waived at 2m AMD average daily balance).'),
        cb=NONE_CB, perks=[CV_PTS], partners=[]),
    'Conversebank|Visa Gold (debit)': dict(tier='plus', atm_own=A(0.5), atm_other=A(1.0), atm_abroad=A(2.0, mn=2500), **CV_C2C, int=CV_PKG_INT,
        waiver=W('package', '0 AMD as the primary card of the C360 "Ultra" package (2,000 AMD/month, waived at 2m AMD average daily balance).'),
        cb=NONE_CB, perks=[['Lounge', 'Zvartnots business lounge at 100 AMD a visit; the C360 Ultra package adds 2 free entries a year.'], CV_PTS], partners=[]),
    'Conversebank|Mastercard Gold (debit)': dict(tier='plus', atm_own=A(0.5), atm_other=A(1.0), atm_abroad=A(2.0, mn=2500), **CV_C2C, int=CV_PKG_INT,
        waiver=W('package', '0 AMD as the primary card of the C360 "Ultra" package (2,000 AMD/month, waived at 2m AMD average daily balance).'),
        cb=NONE_CB, perks=[['Lounge', 'C360 Ultra package: 2 free lounge entries a year.'], CV_PTS], partners=[]),
    'Conversebank|Visa Virtual Account': dict(tier='free', fee=0, fee_display='0 in any C360 package', atm_own=A(0.0), atm_other=None, atm_abroad=None, **CV_C2C, int=None,
        waiver=W('package', 'Four virtual cards (AMD/USD/EUR/RUB) included at 0 AMD in every C360 package.'), cb=NONE_CB, perks=[CV_PTS], partners=[],
        note='Online-payment card; one branch visit still required to issue.'),
    'Conversebank|Arca Mir': dict(tier='free', atm_own=A(0.2), atm_other=A(1.0), atm_abroad=A(1.5), **CV_C2C, int=None,
        waiver=W('none', 'No waiver published.'), cb=arca_cb(), perks=[CV_PTS], partners=[], note='Abroad on the international Mir network only.'),
})

# ---------------------------------------------------------------- Evocabank
EV_BEN = ['Merchant discounts', 'Evoca Benefits: discounts, cashback or gift cards at 100+ Armenian partners (up to 25%).']
EV_BEN_P = [['Evoca Benefits', '100+ Armenian merchants, discounts / cashback up to 25%']]
EV_DIGI_CB = {'rules': [{'src': 'bank', 'rate': 0.25, 'scope': 'dom'}, {'src': 'bank', 'rate': 0.5, 'scope': 'foreign'}], 'cap': {'bank': 5000},
              'text': '0.25% on domestic (ArCa-terminal) payments, 0.5% abroad; capped 5,000 AMD a month; paid in AMD.', 'promo': None}

N.update({
    'Evocabank|Visa Digital': dict(tier='free', atm_own=A(2.0), atm_other=A(2.5), atm_abroad=A(2.5, mn=1500), c2c_in=0.0, c2c_out=0.5,
        c2c_note='0% same-currency inside Evoca (app), 0.3% cross-currency, 0.5% to other ArCa banks.', int=I(4.0, 0, text='4% on AMD balances, no threshold.'),
        waiver=W('none', 'No waiver published.'), cb=EV_DIGI_CB, perks=[EV_BEN], partners=EV_BEN_P),
    'Evocabank|Mastercard World Digital': dict(tier='premium', atm_own=A(2.0), atm_other=A(2.5), atm_abroad=A(2.5, mn=1500), c2c_in=0.0, c2c_out=0.5,
        c2c_note='0% same-currency inside Evoca (app), 0.5% to other ArCa banks.', int=I(0.0, text='No interest on this card.'),
        waiver=W('promo', 'Annual fee not charged under a promotion running to 01.02.2027.'), cb=NONE_CB, perks=[EV_BEN], partners=EV_BEN_P),
    'Evocabank|Visa Vision': dict(tier='plus', atm_own=A(0.2, fm=2000000), atm_other=A(1.0), atm_abroad=A(1.5, mn=1500), c2c_in=0.3, c2c_out=0.5,
        c2c_note='0.3% to Evoca cards via ATM, 0.5% to other banks.', int=I(4.0, 0, text='4% on AMD balances regardless of size.'),
        waiver=W('none', 'No waiver published (600 AMD a month).'), cb=dict(EV_DIGI_CB, text='0.25% domestic, 0.5% abroad; capped 5,000 AMD a month; paid monthly.'),
        perks=[EV_BEN], partners=EV_BEN_P, note='Free own-ATM allowance of 2m AMD; period not stated in the tariff row (monthly assumed).'),
    'Evocabank|Visa Classic': dict(tier='plus', atm_own=A(0.2, fm=1000000), atm_other=A(0.8), atm_abroad=A(1.0, mn=1500), c2c_in=0.3, c2c_out=0.5,
        c2c_note='0.3% in-bank, 0.5% to other ArCa banks.', int=I(1.0, 5000000, text='1% on AMD balances above 5m AMD; 0% below.'),
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[EV_BEN], partners=EV_BEN_P,
        note='Own-ATM: shared tariff table says free to 1m AMD a month; the product tile says 0.2%. Table used.'),
    'Evocabank|Mastercard Standard': dict(tier='plus', atm_own=A(0.2, fm=1000000), atm_other=A(0.8), atm_abroad=A(1.0, mn=1500), c2c_in=0.3, c2c_out=0.5,
        c2c_note='0.3% in-bank, 0.5% to other ArCa banks.', int=I(1.0, 5000000, text='1% on AMD balances above 5m AMD; 0% below.'),
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[EV_BEN], partners=EV_BEN_P, note='Rate above the 1m AMD free allowance not published; 0.2% assumed as for Visa Classic.'),
    'Evocabank|Mastercard Gold': dict(tier='plus', atm_own=A(0.2, fm=2000000), atm_other=A(0.8), atm_abroad=A(1.0, mn=1500), c2c_in=0.3, c2c_out=0.5,
        c2c_note='0.3% in-bank, 0.5% to other ArCa banks.', int=I(1.0, 5000000, text='1% above 5m AMD (2% advertised for EvocaSALARY clients).'),
        waiver=W('payroll', 'Free for EvocaSALARY payroll clients.'), cb=NONE_CB, perks=[EV_BEN], partners=EV_BEN_P,
        note='Rate above the 2m AMD free allowance not published; 0.2% assumed.'),
    'Evocabank|Evoca Visa Platinum': dict(tier='premium', atm_own=A(0.5), atm_other=A(1.0), atm_abroad=A(1.5, mn=1500), c2c_in=0.0, c2c_out=0.5,
        c2c_note='0% same-currency in the app, 0.3% at ATM, 0.5% to other ArCa banks.', int=I(0.0, text='No interest.'),
        waiver=W('none', 'No waiver published.'), cb=dict(NONE_CB, text='No card cashback; Evoca Benefits partner offers only.'),
        perks=[['Lounge', '6 free lounge visits a year (1,200+ lounges) after ≥$400 spend in the prior 35 days.'],
               ['Travel insurance', 'Flight delay, baggage and missed-connection cover; purchase protection for 90 days.'],
               ['Concierge', '24/7 concierge via Telegram and Viber.'], EV_BEN],
        partners=EV_BEN_P + [['Visa', 'International merchant discounts']]),
    'Evocabank|Visa Infinite': dict(tier='elite', atm_own=A(1.0), atm_other=A(1.2), atm_abroad=A(1.5, mn=2500), c2c_in=1.0, c2c_out=1.2,
        c2c_note='1% in-bank, 1.2% to other ArCa banks (dearer than the mass cards).', int=I(2.0, 0, bands=[[5000000, 1.5], [None, 2.0]], text='1.5% on AMD balances up to 5m AMD, 2% above.'),
        waiver=W('none', 'No waiver published.'),
        cb={'rules': [{'src': 'bank', 'rate': 0.5, 'scope': 'foreign'}], 'cap': {}, 'text': '0.5% on international payments (tariff page only; not on the product page); no cap published.', 'promo': None},
        perks=[['Lounge', 'DragonPass: 20 visits if ≥$400 spend in the prior 35 days, else 3 a year; plus LoungeKey 6 a year.'],
               ['Travel insurance', 'CHUBB annual family travel insurance (90 days, worldwide); $2.5m medical cover.'],
               ['Concierge', 'Visa Concierge, 24/7.'], ['Taxi & transfers', 'gg Airport Rides: 1,000 AMD off from Zvartnots.'], EV_BEN],
        partners=[['DragonPass', '20 / 3 lounge visits'], ['LoungeKey', '6 visits a year'], ['CHUBB', 'Family travel insurance'], ['gg', 'Airport ride discount']] + EV_BEN_P),
    'Evocabank|UnionPay Gold': dict(tier='plus', atm_own=A(0.2, fm=2000000), atm_other=A(1.0), atm_abroad=A(1.5, mn=2000), c2c_in=0.3, c2c_out=0.5,
        c2c_note='0.3%–0.5% depending on route and recipient bank.', int=I(0.0, text='No interest.'),
        waiver=W('none', 'No waiver published.'), cb=dict(NONE_CB, text='No cashback ("0.5%" tile is the cash-withdrawal rate).'),
        perks=[['Merchant discounts', 'UnionPay International discounts; Evoca Benefits.']], partners=[['UnionPay International', 'International discounts and offers']] + EV_BEN_P),
    'Evocabank|Arca Classic': dict(tier='free', atm_own=A(0.2, fm=300000), atm_other=A(1.0), atm_abroad='na', c2c_in=0.3, c2c_out=None,
        c2c_note='0.3% within Evoca; other-bank rate not published for this card.', int=I(0.0, text='No interest.'),
        fx={'markup': 0.5, 'pref': False, 'text': '0.5% on foreign-currency transactions (product page).'},
        waiver=W('none', 'No waiver published.'),
        cb=dict(arca_cb(), text=ARCA_TXT + ' Evoca\'s page does not state it; applied because the scheme covers all ArCa cards.'),
        perks=[EV_BEN], partners=EV_BEN_P),
    'Evocabank|Evoca Travel Card': dict(tier='premium', atm_own=A(0.5), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), c2c_in=0.0, c2c_out=0.5,
        c2c_note='0% same-currency in-bank, 0.3% cross-currency, 0.5% to other ArCa banks.', int=I(0.0, text='No interest.'),
        fx={'markup': None, 'pref': True, 'text': 'Preferential USD/EUR rate: 0.5 AMD margin on conversions up to ~5m AMD equivalent.'},
        waiver=W('payroll', '50% off for EvocaSALARY payroll clients.'),
        cb={'rules': [{'src': 'bank', 'rate': 1.5, 'scope': 'trav'}, {'src': 'bank', 'rate': 0.5, 'scope': 'foth'}], 'cap': {'bank': 20000},
            'text': '1.5% on hotels, flights, travel agencies, car hire and rail abroad; 0.5% on other spend abroad; capped 20,000 AMD a month.', 'promo': None},
        perks=[['Lounge', 'LoungeKey: 6 free visits a year for the holder and guests.'], ['Fast Track', 'Mastercard Travel Pass Fast Track, 6 a year.'],
               ['Travel insurance', 'Nairi Insurance multi-trip cover, 30 days a year.'], ['Concierge', '24/7 concierge.'], EV_BEN],
        partners=[['LoungeKey', '6 visits a year'], ['Mastercard Travel Pass', '6 Fast Track passes'], ['Nairi Insurance', 'Travel cover']] + EV_BEN_P,
        placement='Mastercard travel card (level not published); placed in Premium on price and benefits.'),
})

# ---------------------------------------------------------------- IDBank
ID_C2C = dict(c2c_in=0.0, c2c_out=0.75, c2c_note='Free between IDBank cards; 0.75% to other Armenian banks via IDBanking / Idram (0.5% at ATMs).')
ID_INT = I(0.0, text='No interest on card balances.')
ID_ABR = A(1.5, mn=1500)
ID_PREM_CB = {'rules': [{'src': 'bank', 'rate': 0.5, 'scope': 'all'}, {'src': 'points', 'rate': 0.5, 'scope': 'all'}], 'cap': {}, 'paid': 'Cash + idcoin',
              'text': '0.5% cash on all purchases plus 0.5% in idcoin (1 idcoin = 1 AMD, spend via Idram; balance lapses after 365 days without use). 10% idcoin on gettransfer.com.', 'promo': None}
ID_IDC = ['Loyalty points', 'idcoin (1 idcoin = 1 AMD via Idram QR; lapses after 365 days without an idcoin payment).']
ID_GT = ['gettransfer.com', '10% back in idcoin']

N.update({
    'IDBank|Arca Classic': dict(tier='free', atm_own=A(1.0), atm_other=A(1.0, mn=200), atm_abroad='na', **ID_C2C, int=ID_INT,
        waiver=W('payroll', 'Free under the IDsalary payroll package.'), cb=arca_cb(), perks=[], partners=[]),
    'IDBank|Visa Gold debit': dict(tier='plus', atm_own=A(1.0, fm=500000), atm_other=A(1.0, fm=500000), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        uplift={'text': '+0.5% on the savings-account rate (VISAGOLD package); term deposits are not lifted.', 'via': 'package', 'dep_pp': 0, 'sav_pp': 0.5},
        waiver=W('balance', 'VISAGOLD package: 1,000 AMD/month waived if last month\'s average daily balance ≥ 150,000 AMD or payments ≥ 300,000 AMD.'),
        cb=dict(NONE_CB, text='0% cashback on purchases.', promo='VISAGOLD package: up to 5,000 idcoin a month from international transactions (rate not published).'),
        perks=[ID_IDC, ['Merchant discounts', 'Visa and partner discounts.']], partners=[['Visa', 'Ongoing discounts and privileges']],
        note='The 500k AMD free monthly allowance covers IDBank and other banks\' ATMs together.'),
    'IDBank|Visa Signature debit': dict(tier='elite', atm_own=A(1.0, fm=2500000), atm_other=A(1.0, fm=2500000), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('payroll', '20% off the first year when ordered in the app; fee waived under IDsalary.'), cb=ID_PREM_CB,
        perks=[['Lounge', '10 lounge visits a year (1,300+ lounges).'], ['Fast Track', 'Fast Track 10 times.'], ['Travel insurance', 'Travel and medical insurance up to $500,000.'],
               ['Concierge', 'International 24/7 concierge plus IDBank Concierge on Telegram.'], ['Taxi & transfers', 'gettransfer.com: 10% idcoin.'], ID_IDC],
        partners=[ID_GT, ['Visa', 'Signature global discounts']]),
    'IDBank|Visa Infinite debit': dict(tier='elite', atm_own=A(1.0, fm=5000000), atm_other=A(1.0, fm=5000000), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('payroll', '20% off the first year when ordered in the app; fee waived under IDsalary.'), cb=ID_PREM_CB,
        perks=[['Lounge', '20 lounge visits a year (1,300+ lounges).'], ['Fast Track', 'Fast Track 20× international and 20× Zvartnots.'], ['Travel insurance', 'Travel and medical insurance.'],
               ['Concierge', 'International 24/7 concierge plus IDBank Concierge.'], ['Travel & hotel partners', 'Agoda up to 12% off.'], ['Car rental', 'Avis up to 35% off.'],
               ['Taxi & transfers', 'gettransfer.com: 10% idcoin.'], ID_IDC],
        partners=[['Agoda', 'Up to 12% off'], ['Avis', 'Up to 35% off'], ID_GT]),
    'IDBank|Visa Infinite Special Edition': dict(tier='elite', atm_own=A(1.0, fm=5000000), atm_other=A(1.0), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('none', 'No waiver published.'), cb=ID_PREM_CB,
        perks=[['Lounge', 'Unlimited lounge access.'], ['Fast Track', 'Unlimited Fast Track for the holder + up to 6 guests a year.'], ['Travel insurance', 'Travel insurance up to $2.5m.'],
               ['Concierge', 'IDBank and international concierge.'], ['Private banking', 'Private Banking service included.'],
               ['Taxi & transfers', 'Bolt 50% off (max €50) at select European airports; 4 free airport-hotel transfers in the UAE.'], ID_IDC],
        partners=[['Bolt', '50% off airport rides in Europe'], ID_GT]),
    'IDBank|Mastercard World': dict(tier='premium', atm_own=A(1.0), atm_other=A(1.0), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('app', '20% off the first year when ordered in the app.'),
        cb=dict(NONE_CB, text='No standing cashback (tariff shows "–").', promo='Banner: 10,000 idcoin welcome on activation by 15.11; up to 25% idcoin on hotel bookings, capped 25,000 a month.'),
        perks=[['Lounge', 'LoungeKey: 6 visits a year.'], ['Fast Track', 'Fast Track 6 times a year.'], ['Travel insurance', '50% off travel insurance.'],
               ['Concierge', 'Mastercard Concierge 24/7.'], ['Taxi & transfers', 'gettransfer.com: 10% idcoin.'], ID_IDC],
        partners=[['LoungeKey', '6 visits a year'], ID_GT]),
    'IDBank|Mastercard Gold': dict(tier='plus', atm_own=A(0.5), atm_other=A(1.0), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('payroll', '20% off the first year in the app; fee waived under IDsalary.'),
        cb=dict(NONE_CB, promo='Campaign (1 Feb–30 Apr, ended): 5% idcoin on international payments, cap 10,000 a month.'),
        perks=[ID_IDC, ['Merchant discounts', 'Mastercard and partner discounts.']], partners=[['Mastercard', 'Partner discounts'], ID_GT]),
    'IDBank|Mastercard Standard': dict(tier='plus', atm_own=A(0.5), atm_other=A(1.0), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('payroll', '20% off the first year in the app; free under IDsalary.'),
        cb=dict(NONE_CB, promo='Campaign (1 Feb–30 Apr, ended): 5% idcoin on international payments, cap 10,000 a month.'),
        perks=[ID_IDC], partners=[['Mastercard', 'Partner discounts'], ID_GT]),
    'IDBank|Mastercard Standard Instant': dict(tier='free', atm_own=A(1.0), atm_other=A(1.0), atm_abroad=ID_ABR, c2c_in=None, c2c_out=0.75,
        c2c_note='0.75% to other banks via IDBanking / Idram; in-bank rate not published for this card.', int=ID_INT,
        waiver=W('free', 'No service fee; issued in 10 minutes at selected branches.'), cb=dict(NONE_CB, text='No cashback; 10% idcoin on gettransfer.com.'),
        perks=[ID_IDC], partners=[ID_GT]),
})

# Cards that sit in the niche strip, with the reason shown on the page.
STRIP_REASON = {
    'pension': 'Pension / social', 'youth-student': 'Student / youth', 'co-brand': 'Co-brand', 'payroll': 'Payroll',
    'gift-prepaid': 'Gift / prepaid', 'other': 'Niche', 'non-resident variant': 'Non-resident', 'legacy': 'Legacy',
}

# ---------------------------------------------------------------- Acba (scan 2026-09-21)
AC_INT = I(0.0, text='0% on every card and current account (tariff, Jul 2026); only a separate savings account pays 3%.')
AC_C2C = dict(c2c_in=0.5, c2c_out=0.5, c2c_note='0.5% card-to-card within Armenia online / acba digital (0.2% at ATMs); no same-bank vs other-bank split.')
AC_NP_C2C = dict(c2c_in=None, c2c_out=None, c2c_note='Transfer fees not published for this card (standalone tariff PDF unreadable).')
AC_V3 = dict(atm_own=A(0.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500))
AC_VISA_OFFERS = ['Merchant discounts', 'About 20 Visa-network offers: hotels (Amberd, Best Western Dilijan, Courtyard), cafés, pharmacy, retail, 5–15%.']
AC_GOLD_P = [['Agoda', 'Up to 12% off (to 30.10.2026)'], ['SIXT', 'Up to 10% off car rental'], ['Amberd, Best Western Dilijan, Apricot, Courtyard by Marriott', 'Hotel and spa offers 10–15%'],
             ['BookingBash', 'Free ADVENTURER subscription'], ['Square One, Cinnabon, Segafredo, Paul, AKG pharmacy', '10–15% off']]

N.update({
    'Acba|ArCa Classic': dict(tier='free', atm_own=A(0.0), atm_other=A(1.0), atm_abroad='na', **AC_C2C, int=AC_INT,
        waiver=W('app', '2,500 AMD/yr when ordered in acba digital (3,500 standard).'), cb=arca_cb(), perks=[], partners=[]),
    'Acba|Visa Classic': dict(tier='plus', **AC_V3, **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Free for payroll clients; 3,500 AMD/yr in acba digital.'), cb=NONE_CB, perks=[], partners=[]),
    'Acba|Mastercard Standard': dict(tier='plus', fee=4500, fee_display='4,500 AMD / yr (or 400 a month)', **AC_V3, **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Free for payroll clients; 3,500 AMD/yr in acba digital.'), cb=NONE_CB, perks=[], partners=[]),
    'Acba|Visa Digital': dict(tier='free', atm_own=A(1.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AC_C2C, int=AC_INT,
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[], partners=[], note='ATM fees from the card\'s standalone tariff sheet (decoded from ArmSCII).'),
    'Acba|Mastercard Digital First': dict(tier='free', atm_own=A(1.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AC_C2C, int=AC_INT,
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[], partners=[], note='ATM fees from the card\'s standalone tariff sheet (decoded from ArmSCII).'),
    'Acba|American Express Cashback': dict(tier='free', atm_own=A(0.8), atm_other=A(1.5, mn=1500), atm_abroad=A(1.5, mn=1500), c2c_in=1.5, c2c_out=1.5,
        c2c_note='1.5% card-to-card within Armenia (Amex tariff section).', int=AC_INT,
        waiver=W('free', 'No service fee.'),
        cb={'rules': [{'src': 'bank', 'rate': 2.0, 'scope': 'groc'}, {'src': 'bank', 'rate': 1.0, 'scope': 'domx'}], 'cap': {}, 'cap_note': 'no cap (stated)', 'paid': 'Cash · yearly',
            'text': '2% at Armenian supermarkets, 1% at other Armenian merchants, no cap. Paid once a year; unpaid cashback lost if the card is closed early. Excludes payments abroad, cash, utilities, card-to-card, e-wallets and mobile-operator payments.', 'promo': None},
        perks=[], partners=[['American Express', 'Network (Amex acceptance in Armenia not assessed)']],
        placement='American Express debit card with no published level; free, so placed in Free.',
        note='The most generous bank-funded cashback in the market; Amex merchant acceptance in Armenia is narrower than Visa/Mastercard and is not modelled.'),
    'Acba|Visa Gold': dict(tier='plus', **AC_V3, **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Payroll clients 5,000 AMD/yr, free with a salary of 300,000 AMD+; 10,000 in acba digital.'),
        cb=dict(NONE_CB, text='No Acba cashback; Visa-network merchant discounts only.'),
        perks=[AC_VISA_OFFERS, ['Travel & hotel partners', 'Agoda up to 12%, hotel offers in Armenia.'], ['Car rental', 'SIXT up to 10%.'], ['Entertainment', 'BookingBash ADVENTURER subscription (to 30.11.2026).']],
        partners=AC_GOLD_P),
    'Acba|Mastercard Gold': dict(tier='plus', **AC_V3, **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Payroll clients 5,000 AMD/yr, free with a salary of 300,000 AMD+; 10,000 in acba digital.'), cb=NONE_CB, perks=[], partners=[]),
    'Acba|UnionPay Gold': dict(tier='plus', atm_own=A(1.0), atm_other=A(1.0), atm_abroad=A(2.0, mn=2000), **AC_C2C, int=AC_INT,
        waiver=W('app', '12,000 AMD/yr in acba digital (15,000 standard).'), cb=NONE_CB, perks=[], partners=[['UnionPay', 'QuickPass contactless; China/Asia acceptance']]),
    'Acba|Mastercard World': dict(tier='premium', atm_own=A(0.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Free with a salary of 1m AMD+ paid through Acba.'), cb=NONE_CB,
        perks=[['Lounge', 'LoungeKey: 6 visits a year, usable for guests.'], ['Fast Track', 'Mastercard Travel Pass: 6 Fast Tracks a year at 100+ European airports.'],
               ['Concierge', 'Mastercard Concierge 24/7.'], ['Roaming data', 'Flexiroam 1GB a year + 20% off.']],
        partners=[['LoungeKey', '6 visits a year, guests allowed'], ['Mastercard Travel Pass', '6 Fast Tracks a year'], ['Flexiroam', '1GB roaming data a year']]),
    'Acba|Visa Signature': dict(tier='elite', atm_own=A(0.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Free with a salary of 1m AMD+ paid through Acba; 4,000 AMD a month option.'),
        cb=dict(NONE_CB, text='No Acba cashback; Visa partner discounts only.'),
        perks=[['Lounge', 'DragonPass: 2 visits a year, 10 if ≥$400 non-cash spend in the prior 35 days (to 31.12.2026).'], ['Fast Track', '4× Zvartnots; 10× Europe/UAE (to 30.09.2026).'],
               ['Travel insurance', 'Travel insurance and 365-day purchase protection.'], ['Concierge', 'Visa Concierge 24/7.'],
               ['Travel & hotel partners', 'Agoda up to 12%, Visa Luxury Hotel Collection.'], ['Car rental', 'SIXT up to 15%, Avis.'], AC_VISA_OFFERS],
        partners=[['DragonPass', '2 / 10 lounge visits'], ['Agoda', 'Up to 12% off'], ['SIXT', 'Up to 15% off'], ['Visa Luxury Hotel Collection, Avis', 'Hotel privileges, car rental']],
        note='Own-ATM fee: Armenian page 0% for AMD cards, English page 1%; Armenian page used.'),
    'Acba|Visa Signature Limited Edition': dict(tier='elite', atm_own=A(1.0), atm_other=None, atm_abroad=None, **AC_NP_C2C, int=AC_INT,
        waiver=W('none', 'No waiver published.'),
        cb=dict(NONE_CB, text='No spend cashback; museum-entry refunds abroad up to 20,000 AMD a year (to 01.03.2027).'),
        perks=[['Lounge', 'DragonPass: 2 visits a year for holder + 1 guest.'], ['Fast Track', '4× Zvartnots, 10× international (to 30.09.2026).'], ['Travel insurance', 'Travel insurance and purchase protection.'],
               ['Concierge', 'Bookings, car rental, travel planning.'], ['Entertainment', 'Free Saryan House-Museum entry; museum refunds abroad; Epos private club; BookingBash ULTIMATE.'],
               ['Car rental', 'Avis up to 35%, SIXT 15%, Rentalcars.com 10%.'], ['Taxi & transfers', 'gg 10% off, 1,000 AMD off airport rides.'], ['Roaming data', 'Roamingo 3GB twice.']],
        partners=[['Martiros Saryan House-Museum', 'Unlimited free entry + guest'], ['Museums abroad', 'Entry refunds up to 20,000 AMD/yr'], ['Epos private club', 'Membership'],
                  ['DragonPass', '2 visits + guest'], ['Avis, SIXT, Rentalcars.com, Agoda', 'Up to 35% / 15% / 10% / 12% off'], ['gg', 'Ride discounts'], ['Roamingo', '3GB data'], ['BookingBash', 'ULTIMATE subscription']]),
    'Acba|Mastercard World Elite': dict(tier='elite', atm_own=A(0.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AC_C2C, int=AC_INT,
        waiver=W('none', 'No waiver published.'),
        cb=dict(NONE_CB, text='No Acba cashback; Mastercard Travel Rewards up to 20% at 500+ merchants abroad (network offer).'),
        perks=[['Lounge', 'Unlimited LoungeKey access (no guests).'], ['Fast Track', 'Unlimited Fast Track at 100+ European airports incl. Zvartnots.'],
               ['Travel insurance', 'Travel medical and inconvenience insurance.'], ['Concierge', '24/7 concierge via messengers.'], ['Roaming data', 'Flexiroam 3GB a year + 20% off.'],
               ['Travel & hotel partners', 'Mastercard Travel Rewards up to 20%; Priceless experiences.']],
        partners=[['LoungeKey', 'Unlimited, no guests'], ['Mastercard Fast Track', 'Unlimited in Europe'], ['Flexiroam', '3GB a year'], ['Mastercard Travel Rewards / Priceless', 'Up to 20% back at 500+ merchants']]),
    'Acba|American Express Gold Debit': dict(tier='elite', atm_own=A(4.0), atm_other=None, atm_abroad=A(4.0, mn=2500), c2c_in=4.0, c2c_out=4.0,
        c2c_note='4% card-to-card (Amex tariff section).', int=AC_INT,
        waiver=W('none', 'No waiver (50,000 AMD for merchant owners); 6,000 AMD a month option.'),
        cb=dict(NONE_CB, paid='Points · no AMD value', text='No cashback. Earns American Express Membership Rewards points (1 point per 500 AMD spent, 1 per 1,000 AMD withdrawn) for rewards from the MR catalogue; Acba publishes no AMD value per point, so they are not counted. Programme fee 10,000 AMD/yr after year 1.'),
        perks=[['Lounge', 'Priority Pass: 2 visits a year for the holder and each supplementary holder.'], ['Fast Track', '2 Zvartnots Fast Tracks a year.'],
               ['Travel insurance', 'Travel insurance, 120-day purchase protection, doubled warranty.'], ['Taxi & transfers', 'Roadside towing twice a year in Armenia.'],
               ['Loyalty points', 'American Express Membership Rewards (no published AMD value).']],
        partners=[['Priority Pass', '2 lounge visits a year'], ['American Express Membership Rewards', '1 point per 500 AMD']],
        placement='American Express Gold sits above Visa/Mastercard Gold in Amex\'s own ladder; USD/EUR card at 70,000 AMD/yr, placed in Elite on price and benefits.'),
})

# ---------------------------------------------------------------- reclassified into tiers (2026-09-21)
# Rule agreed with Alex: every card sits in a tier except demographic cards (pension, student/youth, women) and
# genuine co-brands with an outside partner (airline, wallet, telecom, charity, club, wealth manager, association).
N.update({
    'IDBank|Travel Card (Visa Platinum)': dict(tier='premium', atm_own=A(1.0), atm_other=A(1.0), atm_abroad=ID_ABR, **ID_C2C, int=ID_INT,
        waiver=W('app', '20% off the first year when ordered in the app.'),
        cb={'rules': [{'src': 'bank', 'rate': 1.5, 'scope': 'foreign'}, {'src': 'bank', 'rate': 0.5, 'scope': 'dom'}, {'src': 'points', 'rate': 0.5, 'scope': 'all'}],
            'cap': {'points': 8000}, 'paid': 'Cash + idcoin',
            'text': '1.5% cash on international payments, 0.5% on local ones (no cap published on the cash stream), plus 0.5% in idcoin on payments of 5,000 AMD+ (1 idcoin = 1 AMD), capped 8,000 idcoin a month after tax (IDBank idcoin tariffs, checked 22.09.2026). 10% idcoin on gettransfer.com.', 'promo': None},
        perks=[['Lounge', '6 lounge visits a year.'], ['Fast Track', '6 international + 6 Zvartnots Fast Tracks a year.'], ['Travel insurance', '50% off travel insurance.'],
               ['Concierge', 'Concierge, free.'], ['Airport services', '6 free baggage wraps a year.'], ['Roaming data', '3GB roaming.'], ['Car rental', 'Avis up to 20% off.'], ID_IDC],
        partners=[['Avis', 'Up to 20% off'], ID_GT],
        note='Travel-positioned Visa Platinum with no outside partner, so it sits in Premium, not with the co-brands. The 1.5% / 0.5% split is read as international / local from the Russian marketing copy.'),
    'Ardshinbank|Visa Individual': dict(tier='plus', **AR_STD, **AR_C2C, int=AR_INT2,
        waiver=W('balance', 'Free if last month\'s average daily balance ≥ 100,000 AMD.'), cb=NONE_CB, perks=[AR_LOY], partners=[],
        note='Personal-design Visa Classic at 700 AMD a month; otherwise classic-tier terms.'),
    'Ardshinbank|Mastercard Meghu Card': dict(tier='free', atm_own='na', atm_other='na', atm_abroad='na', c2c_in=None, c2c_out=None,
        c2c_note='Transfer fees not published for this card.', int=I(0.1, 250000, text='0.1% on AMD balances from 250,000 AMD, paid quarterly.'),
        waiver=W('free', 'No service fee.'), cb=dict(NONE_CB, text='No cashback; 2% fee on e-wallet top-ups.'), perks=[AR_LOY], partners=[],
        note='Cashless-only card: cash withdrawal is switched off at every ATM (shown as n/a).'),
    'Conversebank|Transfer Card': dict(tier='plus', atm_own=A(0.0), atm_other=A(1.0), atm_abroad=A(2.0, mn=2500), **CV_C2C,
        int=I(3.0, 0, text='3% on AMD balances (3.03% APY), paid quarterly.'),
        waiver=W('none', '0 AMD on the Visa Electron variant (Armenian page); otherwise no waiver.'), cb=NONE_CB, perks=[CV_PTS], partners=[],
        note='Remittance-receiving card: can only be funded by incoming transfers.'),
    'Conversebank|Visa PaySticker / MiniFob': dict(tier='plus', atm_own=None, atm_other=None, atm_abroad=None, c2c_in=None, c2c_out=None,
        c2c_note='Follows the tariffs of the card it is attached to.', int=None,
        fx={'markup': 2.0, 'pref': False, 'text': '2% commission on foreign-currency transactions (except USD/EUR conversions within ArCa).'},
        waiver=W('none', 'No waiver published.'), cb=NONE_CB, perks=[CV_PTS], partners=[],
        note='Contactless sticker / key-fob attached to an existing Converse card; cash and transfer fees follow the base card.'),
    'Evocabank|Arca UnionPay Co-badge': dict(tier='free', atm_own=A(0.2, fm=1000000), atm_other=A(0.8), atm_abroad=A(1.0, mn=1500), c2c_in=0.0, c2c_out=0.5,
        c2c_note='0% same-currency in the app, 0.3% at ATMs, 0.5% to other ArCa banks.', int=I(0.0, text='No interest.'),
        waiver=W('none', 'No waiver published.'),
        cb=dict(arca_cb(), text=ARCA_TXT + ' Evoca markets it as "2% cashback on local transactions"; the card\'s own tariff has no cashback row.'),
        perks=[EV_BEN, ['Merchant discounts', 'UnionPay International discounts abroad.']], partners=[['UnionPay International', 'Acceptance in 189 countries, UnionPay offers']] + EV_BEN_P,
        note='ArCa + UnionPay co-badged card (two payment networks, no outside partner), so it sits in Plus.'),
    'Acba|ArCa Transfer': dict(tier='free', atm_own=A(0.0), atm_other=A(1.0), atm_abroad='na', **AC_C2C, int=AC_INT,
        waiver=W('app', 'Free when ordered in acba digital (1,000 AMD/yr otherwise).'), cb=arca_cb(), perks=[], partners=[],
        note='Remittance-receiver card with a credit line of up to 500,000 AMD based on incoming transfers.'),
})

# Why each remaining card sits outside the tiers (shown on the page).
STRIP_WHY = {
    'Acba|ArCa Pension': 'Demographic · pension', 'Acba|Visa Student': 'Demographic · youth (to 30)',
    'Acba|Visa Benefactor': 'Co-brand · Hayastan Fund', 'Acba|Mastercard UEFA Champions League': 'Co-brand · UEFA',
    'Acba|Arca Acba Federation payment card': 'Co-brand · farmers\' federation',
    'Ameriabank|ArCa Pension': 'Demographic · pension', 'Ameriabank|VISA Classic Student': 'Demographic · student',
    'Ameriabank|VISA Classic Student Digital': 'Demographic · student', 'Ameriabank|Visa Star': 'Demographic · kids 6–18',
    'Ameriabank|Team Pay Visa Classic Digital': 'Co-brand · Team Pay', 'Ameriabank|VISA Classic Moons': 'Legacy · no longer issued',
    'Conversebank|Woman\'s Card': 'Demographic · women', 'Conversebank|Pension Card': 'Demographic · pension',
    'Conversebank|Student Card': 'Demographic · student', 'Conversebank|Payroll payment cards': 'Payroll · terms set per employer',
    'Evocabank|Visa Gold': 'Legacy · no longer issued', 'Evocabank|Wilco Visa Infinite': 'Co-brand · Wilco',
    'Evocabank|ArCa pension / social account payment card': 'Demographic · pension',
    'IDBank|Visa Wizz Air': 'Co-brand · Wizz Air (credit card)', 'IDBank|Visa Digital': 'Legacy · no longer issued',
    'IDBank|Idram Rocket Visa': 'Co-brand · Idram', 'IDBank|Caring card': 'Demographic · pension',
    'Ardshinbank|Salary (payroll) tariff package': 'Payroll · package, not a card',
}

# ---------------------------------------------------------------- Alex, 2026-09-21: co-brands Benefactor / Team Pay and
# Ardshinbank's non-resident variants go into the tiers; legacy (no longer issued) cards are dropped from the page.
AR_NR = dict(atm_own=A(0.5), atm_other=A(1.5), atm_abroad=AR_ABR, **AR_C2C)
AR_NR_NOTE = 'Non-resident version: one-off issuance fee (10,000–50,000 AMD), no balance-based fee waiver and no free daily ATM allowance.'
N.update({
    'Acba|Visa Benefactor': dict(tier='plus', fee=4800, fee_display='4,800 AMD / yr (400 a month; 300 in acba digital)', atm_own=A(0.0), atm_other=A(1.0), atm_abroad=A(1.0, mn=1500), **AC_C2C, int=AC_INT,
        waiver=W('payroll', 'Free for payroll clients; 300 AMD a month in acba digital.'), cb=NONE_CB,
        perks=[['Charity', '0.025% of every payment and 50% of the service fee go to the Hayastan All-Armenian Fund, at no cost to the holder.']],
        partners=[['Hayastan All-Armenian Fund', 'Charity share of payments and fees']], note='Charity affinity Visa Classic; placed in Plus at Alex\'s request.'),
    'Ameriabank|Team Pay Visa Classic Digital': dict(tier='free', atm_own=A(0.5, fm=300000), atm_other=A(1.0), atm_abroad=A(1.0), **AM_C2C, int=AM_INT, fx=AM_FX_V,
        waiver=W('free', 'No service fee.'), cb=dict(NONE_CB, text='No Ameriabank cashback; any rewards sit on the Team Pay side (not reachable).'),
        perks=[['Card insurance', 'Card-transaction insurance free (3,000–5,000 AMD a year on other Ameriabank cards).']],
        partners=[['Team Pay (Team Telecom)', 'Card ordered only through the Team Pay platform']], note='Digital Visa Classic sold only through Team Pay; placed in Free at Alex\'s request.'),
    'Ardshinbank|Visa Classic for RA non-residents': dict(tier='plus', **AR_NR, int=AR_INT2, waiver=W('none', 'No waiver for non-residents; 15,000 AMD to issue.'), cb=NONE_CB, perks=[AR_CINS, AR_LOY], partners=[], note=AR_NR_NOTE),
    'Ardshinbank|Mastercard Debit for RA non-residents': dict(tier='plus', **AR_NR, int=AR_INT2, waiver=W('none', 'No waiver for non-residents; 15,000 AMD to issue.'), cb=NONE_CB, perks=[AR_CINS, AR_LOY], partners=[], note=AR_NR_NOTE),
    'Ardshinbank|ArCa card for RA non-residents': dict(tier='free', **AR_NR, int=AR_INT2, waiver=W('none', 'No waiver for non-residents; 10,000 AMD to issue.'), cb=arca_cb(), perks=[AR_CINS, AR_LOY], partners=[], note=AR_NR_NOTE),
    'Ardshinbank|Visa Gold Debit for RA non-residents': dict(tier='plus', **AR_NR, int=AR_INT3, waiver=W('none', 'No waiver for non-residents; 25,000 AMD to issue.'), cb=NONE_CB,
        perks=[['Merchant discounts', 'Visa Gold benefits: Agoda up to 12%, 10–15% at local merchants.'], AR_CINS, AR_LOY], partners=AR_GOLD_P, note=AR_NR_NOTE),
    'Ardshinbank|Visa Gold Debit Digital Card for RA non-residents': dict(tier='plus', **AR_NR, int=AR_INT3, waiver=W('free', 'No annual fee (one-off 25,000 AMD to issue).'), cb=NONE_CB,
        perks=[AR_LOY], partners=AR_GOLD_P, note=AR_NR_NOTE),
    'Ardshinbank|Mastercard World Black Edition for RA non-residents': dict(tier='elite', **AR_NR, int=AR_INT3, waiver=W('none', 'No waiver for non-residents; 35,000 AMD to issue.'), cb=NONE_CB,
        perks=[AR_CINS, AR_LOY], partners=[], note=AR_NR_NOTE + ' The non-resident page publishes none of the resident twin\'s LoungeKey benefits.'),
    'Ardshinbank|Visa Infinite Debit for RA non-residents': dict(tier='elite', **AR_NR, int=I(0.0, text='Page shows 0% on the balance (the resident card pays 3% from 10m AMD) — unverified.'),
        waiver=W('none', 'No waiver for non-residents; 50,000 AMD to issue.'), cb=NONE_CB, perks=[AR_LOY], partners=[],
        note=AR_NR_NOTE + ' Premium benefits are referred to but not reproduced on the non-resident page.'),
})
LEGACY = {'Ameriabank|VISA Classic Moons'}   # issuance terminated per the 06.06.2025 tariff although the scan marks it current
