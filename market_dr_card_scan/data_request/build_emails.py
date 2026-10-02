"""Build the Fast Bank data-request e-mails (one Outlook draft per recipient) plus the full master text.

    python3 build_emails.py <out_dir>

Drafts are .eml with X-Unsent: 1, so Outlook opens them as editable, unsent messages.
Recipients' addresses are left blank on purpose (fill in before sending).
"""
import html
import os
import sys
from email.message import EmailMessage
from email.utils import formataddr

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

SENDER = ('Aleksei Suprunov', 'Suprunov@h21.ai')
CC = [('Farid Minnikhanov', 'Minnikhanov@h21.ai'), ('Andranik Konstantinidi', 'Konstantinidi@h21.ai')]
SUBJECT = 'Data request – refresh of the debit card economics model (Q2–Q3 2026)'
DUE = '[due date]'

INTRO = ('We are rebuilding the debit card economics model that we built together with Farid in late 2025 and '
         'early 2026. The new version covers the four new card tiers (Fast Free, Fast Black, Fast Premium, '
         'Fast Elite) and their combined P&L. Most of the model still runs on Q4 2025 actuals, and we would '
         'like to refresh it to today\'s position (Q2–Q3 2026).')

GUIDE = [
    ('Period', ['Monthly data for March–August 2026 (the last 6 months).',
                'If monthly data is not possible, quarterly totals for Q2 2026 are fine.']),
    ('Breakdown by card type', ['Unless stated otherwise, please split every number by card type: ArCa Classic, '
                                'Visa Classic, Visa Gold, Mastercard World, Mastercard World Elite, Visa Infinite, '
                                'Visa Infinite Metal, Visa Digital.']),
    ('Units', ['Money in full AMD, not thousands or millions.',
               'Foreign-currency amounts either converted to AMD at the CBA rate for that month, or left in the '
               'original currency and labelled.',
               'Counts in pieces (cards, transactions, clients).']),
    ('Format', ['Excel preferred, one sheet per section. Rows are months and columns are card types, or a simple '
                'table like "month | card type | value". Any layout is fine as long as it is labelled.']),
    ('If something is not available', ['Write "n/a" and, if you know, the person who might have it.',
                                       'If you can give an estimate, please mark it "estimate" and say how it was made.']),
    ('Aggregated data only', ['Please send totals, averages and counts by card type and month only.',
                              'Please do NOT send: client names, tax IDs, card or account numbers, balances or '
                              'transactions of individual clients or accounts, income or salary information, or '
                              'lists of individual transfers (who sent to whom).',
                              'If a number can only be built from client-level data, please aggregate it on your '
                              'side before sending. This applies even where sharing the detail would be easier.']),
    ('Definitions', ['If your internal definition differs from ours (e.g. what an "active card" is), please use '
                     'yours and write the definition down.']),
]

S = {}   # section id -> (title, intro line or None, [(num, text, [sub-bullets])])
S['1'] = ('Card base', None, [
    ('1.1', 'Cards issued as at end of month: cards that are valid and not closed, at the end of each month. Pieces, by card type.', []),
    ('1.2', 'Active cards: cards with at least one client transaction in the month. Pieces, by card type. Please state your definition of "active".', []),
    ('1.3', 'New cards issued in the month. Pieces, by card type. If possible, also split by channel: branch, mobile app, delivery.', []),
    ('1.4', 'Cards closed in the month. Pieces, by card type. If possible, split by reason: closed by the client, expired and not reissued, closed by the bank.', []),
    ('1.5', 'Paying cards: number of cards charged the annual/monthly service fee in the month, versus cards where the fee was waived. Pieces, by card type and by waiver reason (salary project, balance condition, promotion, etc.). Counts only – no salary or income amounts.', []),
])
S['2'] = ('Card transactions (volumes and counts)', 'For every item: monthly total amount in AMD and number of transactions, by card type. Totals only – no individual transactions.', [
    ('2.1', 'Purchases in Armenia: card payments at Armenian merchants, in shops and online.', []),
    ('2.2', 'Purchases abroad or at foreign merchants: card payments outside Armenia, including foreign online shops.', []),
    ('2.3', 'Purchases by currency of the card account: AMD, USD, EUR, RUB.', []),
    ('2.4', 'Purchases by merchant category, if available: groceries/supermarkets, restaurants, fuel, travel (airlines, hotels), utilities and telecom, e-wallets, other. This tells us how much spend qualifies for cashback.', []),
    ('2.5', 'Cash withdrawals: split into Fast Bank ATMs, other banks\' ATMs in Armenia, and ATMs abroad.', []),
    ('2.6', 'Card-to-card transfers, as monthly totals by direction: to other Fast Bank cards, to cards of other Armenian banks, and to cards abroad. Totals only – no individual transfers, senders or receivers.', []),
    ('2.7', 'Currency conversions made with the card (purchases or withdrawals in a currency different from the account currency): volume in AMD, split by currency.', []),
])
S['3'] = ('Card income', 'Monthly totals in AMD and the rates (%) charged, by card type:', [
    ('3.1', 'Service fee income: annual and monthly card fees actually collected.', []),
    ('3.2', 'Interchange income from card payments, split into payments in Armenia and abroad. Please also state the interchange rates you receive (% of payment amount) for ArCa, Visa and Mastercard, domestic and international.', []),
    ('3.3', 'Cash withdrawal fee income: split into Fast Bank ATMs, other banks\' ATMs and ATMs abroad.', []),
    ('3.4', 'Card-to-card transfer fee income: split into Fast Bank cards, other Armenian banks and abroad.', []),
    ('3.5', 'FX conversion income from card transactions (the spread earned). Please explain how it is calculated.', []),
    ('3.6', 'Other card income, if material (e.g. card reissue, SMS/notifications, express delivery). Please list the items.', []),
])
S['4.1'] = ('Funding cost', None, [
    ('4.1', 'Funding / internal transfer price used for card balances: % per year, AMD and foreign currency, monthly or the latest value.', []),
])
S['4.2'] = ('Deposits of debit cardholders', None, [
    ('4.2', 'Term deposits and savings of debit cardholders, aggregated by the card type the client holds: total and average monthly balance, number of depositors, and average interest rate (% per year). Please split by deposit currency and term if possible. Aggregates only – not individual accounts.', []),
])
S['4.3'] = ('Deposit rate uplift', None, [
    ('4.3', 'Do any cards currently give a higher deposit rate? If yes: which cards, how much (+ percentage points), and how many clients use it (count only).', []),
])
S['5'] = ('Direct costs of card transactions', None, [
    ('5.1', 'Processing fees paid to ArCa: monthly total in AMD, by card type, plus the tariff (% of volume and/or AMD per transaction).', []),
    ('5.2', 'Scheme and processing fees paid to Visa and Mastercard: monthly total in AMD, by card type, plus the main tariffs.', []),
    ('5.3', 'Cost when Fast Bank cardholders use other banks\' ATMs (the acquiring fee Fast Bank pays): monthly total in AMD and % of volume.', []),
    ('5.4', 'Cost of card-to-card transfers to other banks (interbank fee): monthly total in AMD and % of volume.', []),
])
S['6'] = ('Card issuing and acquisition costs (per card)', 'Please give the current cost per card in AMD and the date of the price:', [
    ('6.1', 'Plastic card blank, by card type.', []),
    ('6.2', 'Metal card (Visa Infinite Metal).', []),
    ('6.3', 'Embossing / personalisation.', []),
    ('6.4', 'PIN envelope or PIN setup, if separate.', []),
    ('6.5', 'Delivery to the client (courier), plus the share of cards delivered versus picked up at a branch.', []),
    ('6.6', 'First activation at an ATM, if there is a cost.', []),
    ('6.7', 'Marketing for debit cards: monthly spend in AMD (March–August 2026) and the number of debit cards sold in the same months.', []),
    ('6.8', 'Branch time on cards: estimated share of branch staff time spent on card sales and servicing (%), and total branch cost for the period. Optional.', []),
])
S['7'] = ('Loyalty and perks', 'If these are tracked – even roughly – please share:', [
    ('7.1', 'Premium perks used and their cost, monthly by card type:', [
        'Airport lounge visits (DragonPass / LoungeKey): number of visits, cost per visit.',
        'Fast Track: number used, cost per use.',
        'Travel insurance: number of policies and premium per card or per policy.',
        'Concierge: fee per card or per month.',
        'Airport parking, baggage wrapping, roaming data packages: number used and cost.',
        'Any partner discounts co-funded by Fast Bank: cost.']),
])
S['8'] = ('Tariffs and confirmations', None, [
    ('8.1', 'The current tariff document for all debit cards, and any changes effective after 26.06.2026.', []),
    ('8.2', 'Current card FX buy/sell rates (or spread) for USD, EUR, RUB, and how they differ from branch/cash rates.', []),
    ('8.3', 'Fee waiver rules currently in force, by card type (balance thresholds, salary projects, promotions).', []),
    ('8.4', 'Please confirm: transfers between Fast Bank cards are free (0%), and transfers to other banks cost 0.5%.', []),
])
S['9'] = ('Plans for 2027–2029 (optional)', 'Only if a budget or plan already exists – we do not need new projections to be made:', [
    ('9.1', 'Planned number of active debit cards and new cards sold per year, 2027–2029 (by tier or card type if available).', []),
    ('9.2', 'Planned card balances and deposit volumes; funding / transfer-price and deposit-rate assumptions.', []),
    ('9.3', 'Planned debit card marketing budget and card business OPEX.', []),
])

# recipient -> (file tag, greeting name, role line, [(section id, note or None)], extra paragraph or None)
RECIPIENTS = [
    ('01_Narek_Jilavyan_card_base', 'Narek', 'Narek Jilavyan',
     [('1', None)],
     'You probably already have most of this in the regular card report – if so, the report in Excel is perfect as is. '
     'It would also help to know whether it covers transaction volumes (Section 2 of our list, which we have asked '
     'Vahan about); if it does, we will not ask him to duplicate it.'),
    ('02_Vahan_Ochinyan_transactions_deposits', 'Vahan', 'Vahan Ochinyan',
     [('2', None), ('4.2', None)],
     'Some of Section 2 may already be in Narek\'s card report – we will check with him first so you do not have '
     'to duplicate work. We would also be glad to sit with you for 30 minutes to go through what is needed and what '
     'is easiest to extract. Please note that we need aggregates only: last time we worked with a client-level '
     'extract, and this time everything should be aggregated on the bank\'s side (totals, averages and counts by '
     'card type and month).'),
    ('03_Gohar_Harutyunyan_CFO', 'Gohar', 'Gohar Harutyunyan',
     [('4.1', None), ('3', 'We understand card income is not reported separately by card type. If it is available in management accounts, the totals would be ideal; if not, please point us to the right person – last time we built it from commission rates × volumes.'), ('9', None)],
     None),
    ('04_Ani_Arshakyan_costs_tariffs', 'Ani', 'Ani Arshakyan',
     [('3', 'Mainly the rates (%) and fees that apply to each income type – last time we used your commission rates and multiplied them by volumes. Actual totals are welcome if you have them.'),
      ('5', None), ('6', None), ('7', 'We have also asked Tigran Sargsyan – one reply from either of you is enough.'), ('8', None)],
     None),
    ('05_Tigran_Sargsyan_retail', 'Tigran', 'Tigran Sargsyan',
     [('4.3', None), ('7', 'We have also asked Ani Arshakyan – one reply from either of you is enough.')],
     None),
]


def sec_text(sid, note):
    title, lead, items = S[sid]
    num = sid.split('.')[0]
    head = f'SECTION {num}. {title.upper()}' if '.' not in sid else f'{title.upper()} (item {sid})'
    lines = [head]
    if note:
        lines.append(note)
    if lead:
        lines.append(lead)
    for n, t, subs in items:
        lines.append(f'{n}. {t}')
        lines += [f'   • {s}' for s in subs]
    return '\n'.join(lines)


def sec_html(sid, note):
    title, lead, items = S[sid]
    num = sid.split('.')[0]
    head = f'Section {num}. {title}' if '.' not in sid else f'{title} (item {sid})'
    h = [f'<p style="margin:14px 0 4px"><b>{html.escape(head)}</b></p>']
    if note:
        h.append(f'<p style="margin:2px 0;color:#555"><i>{html.escape(note)}</i></p>')
    if lead:
        h.append(f'<p style="margin:2px 0">{html.escape(lead)}</p>')
    for n, t, subs in items:
        h.append(f'<p style="margin:3px 0 3px 12px">{n}. {html.escape(t)}</p>')
        if subs:
            h.append('<ul style="margin:0 0 4px 30px">' + ''.join(f'<li>{html.escape(s)}</li>' for s in subs) + '</ul>')
    return '\n'.join(h)


def guide_text():
    out = ['GENERAL GUIDELINES']
    for i, (t, bs) in enumerate(GUIDE, 1):
        out.append(f'{i}. {t}')
        out += [f'   • {b}' for b in bs]
    return '\n'.join(out)


def guide_html():
    h = ['<p style="margin:14px 0 4px"><b>General guidelines</b></p><ol style="margin:0 0 0 18px">']
    for t, bs in GUIDE:
        h.append(f'<li><b>{html.escape(t)}</b><ul>' + ''.join(f'<li>{html.escape(b)}</li>' for b in bs) + '</ul></li>')
    return '\n'.join(h) + '</ol>'


CLOSE = ('If any item is unclear or too heavy to collect, please tell us early and we will agree a simpler '
         'alternative or set up a short call. Partial data sent early is more useful to us than complete data sent late.')
SIGN = 'Best regards,\nAleksei | H21'

for tag, first, full, secs, extra in RECIPIENTS:
    ask = 'the items below'
    txt = [f'Dear {first},', '', INTRO, '',
           f'Farid suggested that you are the right person for {ask}. Could you please share them by {DUE}?']
    if extra:
        txt += ['', extra]
    txt += ['']
    txt += [sec_text(s, n) + '\n' for s, n in secs]
    txt += [guide_text(), '', 'Thank you in advance. ' + CLOSE, '', SIGN]
    body_txt = '\n'.join(txt)

    hb = [f'<p>Dear {html.escape(first)},</p>', f'<p>{html.escape(INTRO)}</p>',
          f'<p>Farid suggested that you are the right person for {ask}. Could you please share them by <b>{html.escape(DUE)}</b>?</p>']
    if extra:
        hb.append(f'<p>{html.escape(extra)}</p>')
    hb += [sec_html(s, n) for s, n in secs]
    hb += [guide_html(), f'<p>Thank you in advance. {html.escape(CLOSE)}</p>', '<p>Best regards,<br>Aleksei | H21</p>']
    body_html = ('<html><body style="font-family:Calibri,Arial,sans-serif;font-size:11pt;color:#222">'
                 + '\n'.join(hb) + '</body></html>')

    m = EmailMessage()
    m['From'] = formataddr(SENDER)
    m['To'] = ''
    m['Cc'] = ', '.join(formataddr(c) for c in CC)
    m['Subject'] = SUBJECT
    m['X-Unsent'] = '1'
    m.set_content(body_txt)
    m.add_alternative(body_html, subtype='html')
    with open(os.path.join(OUT, f'{tag}.eml'), 'wb') as f:
        f.write(bytes(m))

# master text with every section and its owner
OWNERS = {'1': 'Narek Jilavyan', '2': 'Vahan Ochinyan (after checking Narek\'s card report)',
          '3': 'Ani Arshakyan (rates) / Gohar Harutyunyan, CFO (actuals or pointer)', '4.1': 'Gohar Harutyunyan (CFO)',
          '4.2': 'Vahan Ochinyan', '4.3': 'Tigran Sargsyan', '5': 'Ani Arshakyan', '6': 'Ani Arshakyan',
          '7': 'Ani Arshakyan / Tigran Sargsyan', '8': 'Ani Arshakyan', '9': 'Gohar Harutyunyan (CFO), optional'}
master = [f'Subject: {SUBJECT}', '', 'Dear colleagues,', '', INTRO, '', guide_text(), '']
for sid in ['1', '2', '3', '4.1', '4.2', '4.3', '5', '6', '7', '8', '9']:
    master += [sec_text(sid, None), f'Responsible: {OWNERS[sid]}', '']
master += ['Thank you in advance. ' + CLOSE, '', SIGN]
with open(os.path.join(OUT, '00_master_request_all_sections.txt'), 'w') as f:
    f.write('\n'.join(master))
print('\n'.join(sorted(os.listdir(OUT))))
