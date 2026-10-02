# ---------------------------------------------------------------- PLAN (I)
s = new_slide(prs, 'Our view of the next months: set focus products, build the campaign machine, define target segments and launch first campaigns',
              'Proposed CVM plan by topic – for discussion', 'I. LONG-TERM PRIORITIES')
K['plan'] = s
X2 = L + 3350000
band(s, L, 1400000, 3000000, 'Topic'); band(s, X2, 1400000, R - X2, 'What needs to be done')
hline(s, L, 1610000, CW, color=GREY)
items = [
    ('1.1', 'Products to push before the Dec–Jan card launch',
     ['Pick 3–4 focus products: card usage, gold-loan money to card, deposits and balances, pre-approved loans',
      'Set one target metric per product']),
    ('1.2', 'Triggers and offers',
     ['Build a campaign backlog around client events: deposit maturity, loan disbursement, dormancy, inflows, salary day',
      'Launch the first campaigns now and scale those that beat the holdout']),
    ('2', 'Infrastructure and operating model',
     ['Put the building blocks for any campaign in place: data, segments, channels, measurement (next page)',
      'Name owners for project management, data sourcing, segment creation and the campaign flow']),
    ('3', 'Segmentation',
     ['Define target segments by product holding, behaviour, lifecycle and value (see backup)',
      'Reuse them in every campaign instead of building one-off lists']),
]
y = 1680000
RHp = 840000
for code, topic, bl in items:
    num(s, L, y + 30000, code, d=340000, size=9)
    tb(s, L + 440000, y + 50000, 2800000, RHp - 100000, [[r(topic, 14, True, '000000')]], name='Topic')
    tb(s, X2, y + 50000, R - X2, RHp - 100000, [{'runs': [r(t, 12)], 'bullet': True, 'after': 4} for t in bl], name='To do')
    y += RHp
    hline(s, L, y - 20000, CW)
py = y + 130000
rect(s, L, py, CW, 6250000 - py, shape='round', radius=0.06, name='Side quests panel')
band(s, L + 200000, py + 110000, 6000000, 'Open questions and side quests')
sq = [('Creatio', 'Which data sources feed it first: core banking, cards, app events, consents'),
      ('Measurement', 'Global control group vs campaign holdout; no t-test at this stage'),
      ('Best practices', 'Sessions with Anna and Nikita on how peers run CVM'),
      ('Current debit card offers', 'Review today’s terms: change, delete or update')]
cw4 = (CW - 400000) / 4
for i, (a, b) in enumerate(sq):
    tb(s, L + 200000 + i * cw4, py + 360000, cw4 - 150000, 6250000 - py - 420000,
       [[r(a, 12, True, INK)], [r(b, 11, False, INK)]], name='Side quest')

# ---------------------------------------------------------------- BUILDING BLOCKS (I.2 + III)
s = new_slide(prs, 'Building blocks toward launching any campaign: most exist in part; data, triggers and measurement are the gaps',
              'Status today and what is needed (H21 view, to verify with the bank)', 'I. LONG-TERM PRIORITIES · 2. INFRASTRUCTURE AND OPERATING MODEL')
K['blocks'] = s
ST = {'In place': (NAVY, WHITE, None), 'Partly': (WHITE, NAVY, NAVY), 'Missing': (MAG, WHITE, None)}
bb = [('Target area', 'Partly', 'Campaigns picked product by product', 'Focus products and a target metric for each'),
      ('Whom we target', 'Partly', 'Lists from product flags and balance bands', 'Shared target segments; high-LTV sub-segments'),
      ('Target metric', 'Partly', 'Loose rules: “+1% balance” counts a third of the holdout', 'One metric per campaign, in AMD per client'),
      ('Target action and reward', 'Partly', 'Blanket offers: 4% on balances, 2% cashback', 'Action tied to the metric; reward capped below margin uplift'),
      ('Data source', 'Missing', 'One-off lists pulled by BI for each campaign', 'Refreshable BI views with consent flags'),
      ('Channels and fallback', 'Partly', 'Viber, e-mail, SMS, calls; Viber reached 36%, e-mail clicks 0.3%', 'Push and in-app, a fallback chain, clean contact data'),
      ('Content and design', 'In place', 'Marketing produces texts and visuals', 'One call to action; two variants to A/B test'),
      ('When', 'Missing', 'Batch sends only', 'Event triggers: maturity, disbursement, dormancy – 3–8x conversion¹'),
      ('Impact tracking', 'Partly', 'Campaign manager tracker; holdout in 2 of 6 sales campaigns', 'Holdout in every campaign plus a global control')]
GW = (CW - 2 * 110000) / 3; GH = 1150000; GY0 = 1380000
for i, (a, st, today, need) in enumerate(bb):
    x = L + (i % 3) * (GW + 110000); y = GY0 + (i // 3) * (GH + 90000)
    rect(s, x, y, GW, GH, shape='round', radius=0.05, name='Block card')
    num(s, x + 120000, y + 100000, i + 1, d=270000)
    tb(s, x + 470000, y + 120000, GW - 1500000, 280000, [[r(a, 12, True, '000000')]], name='Block')
    f, c, ln = ST[st]
    chip(s, x + GW - 950000, y + 125000, 830000, 230000, st, fill=f, color=c, line=ln, size=9, bold=True)
    tb(s, x + 120000, y + 450000, GW - 240000, 330000, [[r('Today: ', 10, True, GREY), r(today, 10)]], name='Today')
    tb(s, x + 120000, y + 790000, GW - 240000, 330000, [[r('Needed: ', 10, True, MAG), r(need, 10)]], name='Needed')
ey = GY0 + 3 * GH + 2 * 90000 + 110000
band(s, L, ey, 4000000, 'Enablers and owners')
en = [('Project management', 'H21 PMO with CRM PO', 'Backlog, a PRD per campaign, weekly CVM committee'),
      ('Data sourcing', 'Bank BI; compliance', 'Refreshable BI views and consents; no personal data leaves the bank'),
      ('Segment creation', 'CRM team with BI', 'Target segments defined once, refreshed for every campaign'),
      ('Campaign flow', 'CRM PO; channel owners', 'Idea → PRD → segment → offer → launch → measure → decide; Creatio later')]
pw = (CW - 3 * 110000) / 4
for i, (a, o, b) in enumerate(en):
    x = L + i * (pw + 110000)
    rect(s, x, ey + 210000, pw, 6250000 - ey - 210000, shape='round', radius=0.06, fill=WHITE, line=LINE, name='Enabler panel')
    tb(s, x + 130000, ey + 280000, pw - 260000, 6250000 - ey - 330000,
       [[r(a, 11, True, '000000')], [r(o, 10, True, MAG)], [r(b, 10)]], name='Enabler')
footnote(s, ['1. Finalta by McKinsey, Russian banks 2019: event-triggered cash-loan offers convert at 3.7–4.8% vs 0.6–1.1% for batch offers'])

# ---------------------------------------------------------------- WAVE 1 (II)
s = new_slide(prs, 'Short term: five wave-1 campaigns can launch on today’s data and channels and must beat the holdout',
              'Wave 1: campaign logic', 'II. SHORT TERM')
K['wave1'] = s
WC = [('#', 0, 330000), ('Campaign and why', 380000, 3050000), ('Whom', 3480000, 1700000), ('When and channel', 5230000, 1700000),
      ('Client action → reward', 6980000, 2300000), ('KPI vs holdout', 9330000, 1752528)]
for h_, x, w in WC:
    band(s, L + x, 1400000, w, h_, align='c' if h_ == '#' else 'l')
hline(s, L, 1610000, CW, color=GREY)
w1 = [('Gold-loan money to card', '57% of clients hold a gold loan but few use a card; the disbursement visit is the moment to issue one',
       'Gold-loan clients without an active card (134k)', 'Loan disbursement in a branch (~46k a month)', 'Branch next-best offer; SMS',
       'Take the loan onto a Fast Bank card → preferential gold-loan rate', 'Share of loans paid to a card; card balance at D+30'),
      ('Deposit maturity: prolong or upgrade', 'Deposits are the largest book (124bn AMD); every maturity is a moment the money can leave',
       'Clients with a maturing term deposit (15k)', '14, 7 and 1 days before maturity', 'Call for large tickets; SMS, Viber',
       'Prolong or auto-prolong, or move to savings or bonds → rate bonus', 'Retained share of maturing volume'),
      ('Welcome and activation push', '3.7k issued cards are not activated; the first 30 days set the habit (full quest with prize draws later)',
       'New cardholders (~10k cards a month)', 'Card issued; no purchase by day 7', 'Push, SMS; call on day 7',
       'First purchase and Apple / Google Pay → small bonus', 'Activated in 14 days; 5+ purchases in 30 days'),
      ('Dormant card reactivation', '~60% of cards are idle in a month; waking one up costs less than issuing a new one',
       'Cards idle for 60 or 90 days', 'Day 60 or 90 without a purchase', 'Viber, SMS fallback',
       'Make a purchase → one month of free ATM, transfers and preferential rates', 'Reactivated share at D+30'),
      ('7-day streak', 'An average card makes 2.4 transactions a month; a daily streak builds the habit',
       'Cardholders with 1–4 purchases a month', 'Start of the week', 'Push, Viber',
       '1+ card purchase every day for 7 days → fixed bonus, e.g. 1,000 AMD', 'Transactions per card; active days a month')]
y = 1650000
RHw = 790000
for i, (name, why, whom, when, ch, act, kpi) in enumerate(w1):
    num(s, L + 20000, y + 70000, i + 1, d=280000)
    tb(s, L + WC[1][1], y + 70000, WC[1][2] - 80000, RHw - 90000,
       [[r(name, 12, True, '000000')], [r(why, 9.5, False, GREY)]], name='Campaign')
    tb(s, L + WC[2][1], y + 70000, WC[2][2] - 80000, RHw - 90000, [[r(whom, 10.5)]], name='Whom')
    tb(s, L + WC[3][1], y + 70000, WC[3][2] - 80000, RHw - 90000, [[r(when, 10.5)], [r(ch, 9.5, False, GREY)]], name='When')
    tb(s, L + WC[4][1], y + 70000, WC[4][2] - 80000, RHw - 90000, [[r(act, 10.5)]], name='Action')
    tb(s, L + WC[5][1], y + 70000, WC[5][2], RHw - 90000, [[r(kpi, 10.5)]], name='KPI')
    y += RHw
    hline(s, L, y - 20000, CW)
py = y + 60000
rect(s, L, py, CW, 6250000 - py, shape='round', radius=0.1, name='Rules panel')
rules = [('Holdout', '10% random per campaign, plus a 5% global control'), ('Success', 'beats the holdout (>0) at D+30; no t-test yet'),
         ('Consent', 'service messages first; offers only with marketing consent'), ('Then', 'scale winners, iterate once, stop the rest')]
rw = (CW - 300000) / 4
for i, (a, b) in enumerate(rules):
    tb(s, L + 150000 + i * rw, py + 90000, rw - 120000, 6250000 - py - 120000, [[r(a, 11, True, MAG)], [r(b, 10)]], name='Rule')
footnote(s, ['Bases: Fast Bank data Sep 2025; card funnel Mar–Aug 2026; MAU ~40% from the transformation kick-off. Rewards and sizes to be set in each PRD'])

# ---------------------------------------------------------------- WAVES 2–3 (IV.3)
COLS = [('#', 0, 330000), ('Campaign', 380000, 2000000), ('Whom', 2480000, 1700000), ('When (trigger)', 4280000, 1550000),
        ('Client action → reward', 5930000, 2250000), ('Channel', 8280000, 1150000), ('KPI vs holdout', 9530000, 1150000), ('Wave', 10720000, 362528)]


def camp_table(s, rows, RHc=760000):
    for h_, x, w in COLS:
        band(s, L + x, 1400000, w, h_, align='c' if h_ in ('#', 'Wave') else 'l')
    hline(s, L, 1610000, CW, color=GREY)
    y = 1650000
    for n, name, src, whom, when, act, ch, kpi, wave in rows:
        num(s, L + 20000, y + 60000, n, d=280000, fill=NAVY)
        paras = [[r(name, 11, True, '000000')]]
        if src:
            paras.append([r(src, 8.5, False, TAN if src.startswith('Benchmark') else GREY)])
        tb(s, L + COLS[1][1], y + 60000, COLS[1][2], RHc - 80000, paras, name='Campaign')
        for (h_, x, w), t in zip(COLS[2:7], (whom, when, act, ch, kpi)):
            tb(s, L + x, y + 60000, w - 60000, RHc - 80000, [[r(t, 10)]], name=h_)
        num(s, L + COLS[7][1] + 60000, y + 60000, wave, d=260000, fill=WAVE[wave], size=10)
        y += RHc
        hline(s, L, y - 20000, CW)


s = new_slide(prs, 'Beyond wave 1, seven campaigns follow with the new cards (wave 2) and with Creatio or the new app (wave 3)',
              'Top campaigns after wave 1', 'IV. FIRST FINDINGS · 3. TOP CAMPAIGNS')
K['waves23'] = s
camp_table(s, [
    (6, 'Balance-based free service', 'Team idea', 'Cardholders whose free service rests on a deposit (check who keeps it)', 'Tariff change with the new cards',
     'Keep a minimum average balance instead of a deposit → free service', 'E-mail, Viber, app', 'Card balances; paid cards retained', 2),
    (7, 'Bring your money: 1% bonus', 'Team idea', 'Clients with inflows or salary at other banks', 'After a first inflow from another bank',
     'Move money in and hold it a month, or make X purchases → 1% bonus, capped', 'Viber, e-mail, app', 'Net new balances held 30 days', 2),
    (8, 'Pre-approved cash loan for gold-loan clients', 'Benchmark: Finalta; Monzo', 'Gold-loan clients with a clean repayment record', 'Loan nearing its end; abandoned application',
     'Accept a pre-approved limit → loan without paperwork', 'SMS, call, branch', 'Conversion vs holdout', 2),
    (9, 'FX offers for traveller look-alikes', 'Team idea', 'Clients with travel spend, FX purchases or transfers abroad', 'Air ticket, hotel or FX purchase',
     'Buy FX or pay abroad with the card → preferential FX rate', 'Push, Viber, e-mail', 'FX volume; card spend abroad', 2),
    (10, 'Salary-day and outflow moment', 'Benchmark: McKinsey case; Kazakhstan bank', 'Salary clients (80% of salary leaves via ATMs¹)', 'Salary credit; cash-out or transfer out',
     'Keep the money in → savings rate or cashback boost, in real time', 'Push, SMS', 'Share of salary kept after 7 days', 3),
    (11, 'Autopay switch', 'Benchmark: Sber; VTB', 'App users paying mobile or utilities elsewhere', 'After a bill payment',
     'Set up autopay for mobile or utilities → bonus or prize draw', 'App, push', 'Autopays set up; MAU', 3),
    (12, 'Referral (to test)', 'Team idea', 'Active cardholders', 'After the 5th purchase',
     'Invite a friend who activates and transacts → bonus to both, e.g. 2,000 AMD', 'App, Viber', 'New active cards; cost vs 10–20k AMD CAC', 3),
], RHc=640000)
footnote(s, ['1. Kazakhstan bank, salary clients (H21 reference case). Team ideas are from the CVM working session; benchmark ideas are from reference cases. Rewards and sizes to be set in each PRD'])

# ---------------------------------------------------------------- SUMMARY (end)
s = new_slide(prs, 'Summary: CVM should grow usage and balances of today’s clients, starting with five measurable quick wins', None, 'SUMMARY')
K['summary'] = s
rows = [
    ('The base is gold-loan heavy: cross-sell and balances are the prize',
     '134k of 236k clients (57%) hold gold loans; only 46k use a debit card and 15k hold term deposits, yet deposits are the largest book (124bn AMD)'),
    ('The card funnel works up to activation; usage is the gap',
     '100% of card applications are issued and 85% activated, but only ~40% of cards are active in a month (target 75%+) at 2.4 transactions per card'),
    ('Current campaigns are batch mailings and rarely measured',
     'Only 2 of 6 completed sales campaigns had a holdout; both show ≤1 p.p. uplift. Viber reached 36%, e-mail clicks 0.3%. Targeted calls work: 41 sales, 250m AMD'),
    ('Most building blocks exist in part; data, triggers and measurement are the gaps',
     'Lists are one-off, sends are batch only and holdouts are rare; refreshable BI views, event triggers and a holdout in every campaign close the gap'),
    ('Wave 1: five campaigns on today’s data and channels',
     'Gold-loan money to card, deposit maturity, welcome and activation push, dormant reactivation and a 7-day streak; scale only what beats the holdout'),
    ('Next two weeks',
     'PRDs for wave 1; BI counts (maturities for the next 180 days, non-activated cards); consents and opt-outs; risk readiness for pre-approved limits'),
]
y, RH = 1250000, 810000
for i, (a, b) in enumerate(rows):
    num(s, L, y + 40000, i + 1)
    tb(s, L + 440000, y, 3900000, RH - 80000, [[r(a, 14, True, '000000')]], name='Lead')
    tb(s, L + 4600000, y + 20000, CW - 4600000, RH - 80000, [[r(b, 12, False, INK)]], name='Support')
    if i < len(rows) - 1:
        hline(s, L, y + RH - 50000, CW)
    y += RH
footnote(s, ['Sources: Fast Bank profit pools model (Sep 2025); card funnel extract, Mar–Aug 2026; campaign manager export (15 Sep 2026); transformation kick-off (3 Sep 2026)'])

# ---------------------------------------------------------------- BACKUP divider
s = new_slide(prs, 'Backup')
K['backup'] = s
