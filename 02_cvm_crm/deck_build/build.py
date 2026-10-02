import sys
from pptx import Presentation
from pptx.util import Emu, Pt
from h import *

SRC, OUT = sys.argv[1], sys.argv[2]
prs = Presentation(SRC)

# keep only the title slide (slide 8 of the source) and rebuild the rest
lst = prs.slides._sldIdLst
for i, sid in enumerate(list(lst)):
    if i != 7:
        prs.part.drop_rel(sid.rId); lst.remove(sid)
cover = prs.slides[0]
for sh in cover.shapes:
    if sh.name == 'Title 3':
        set_text(sh, 'Fast Bank CVM: priorities, quick wins and first findings')
    elif sh.name == 'Subtitle 2':
        set_text(sh, 'Document for discussion')
    elif sh.name == 'Text Placeholder 1':
        set_text(sh, '30 Sep, 2026')

WAVE = {1: MAG, 2: BLUE, 3: GREY}

# ---------------------------------------------------------------- 2. Executive summary
s = new_slide(prs, 'Executive summary: CVM should grow usage and balances of today’s clients, starting with five measurable quick wins')
rows = [
    ('The base is gold-loan heavy: cross-sell and balances are the prize',
     '134k of 236k clients (57%) hold gold loans; only 46k use a debit card and 15k hold term deposits, yet deposits are the largest book (124bn AMD)'),
    ('The card funnel works up to activation; usage is the gap',
     '100% of card applications are issued and 85% activated, but only ~40% of cards are active in a month (target 75%+) at 2.4 transactions per card'),
    ('Current campaigns are batch mailings and rarely measured',
     'Only 2 of 6 completed sales campaigns had a holdout; both show ≤1 p.p. uplift. Viber delivered 36%, e-mail clicks 0.3%. Targeted calls work: 41 sales, 250m AMD'),
    ('Wave 1: five campaigns in Oct–Nov, scaled only if they beat the holdout',
     'Deposit maturity, gold-loan money to card, card activation, dormant reactivation and a 7-day streak – on today’s data and channels, with no IT build'),
    ('One flow from idea to readout, on shared value-based segments',
     'A 9-question canvas serves as the PRD; bank BI builds segments in-house; 10% holdout plus a global control; weekly CVM committee; Creatio automates later'),
    ('Decisions and inputs needed now',
     'Confirm products, wave 1 and owners; BI counts (maturities for the next 180 days, non-activated cards); consents and opt-outs; risk readiness for pre-approved limits'),
]
y, RH = 1400000, 790000
for i, (a, b) in enumerate(rows):
    num(s, L, y + 40000, i + 1)
    tb(s, L + 440000, y, 3900000, RH - 80000, [[r(a, 14, True, '000000')]], name='Lead')
    tb(s, L + 4600000, y + 20000, CW - 4600000, RH - 80000, [[r(b, 12, False, INK)]], name='Support')
    if i < len(rows) - 1:
        hline(s, L, y + RH - 50000, CW)
    y += RH
footnote(s, ['Sources: Fast Bank profit pools model (Sep 2025); card funnel extract, Mar–Aug 2026; campaign manager export (15 Sep 2026); transformation kick-off (3 Sep 2026)'])

# ---------------------------------------------------------------- 3. I. Long-term priorities
s = new_slide(prs, 'Long-term, CVM should push usage and balances on one campaign flow and shared value-based segments',
              'Five topics to agree today', 'I. LONG-TERM PRIORITIES')
X2, X3 = L + 3050000, L + 8500000
band(s, L, 1400000, 2800000, 'Topic'); band(s, X2, 1400000, 5000000, 'What we propose'); band(s, X3, 1400000, 2500000, 'Decision needed today')
hline(s, L, 1610000, CW, color=GREY)
items = [
    ('1.1', 'Products to push before the Dec–Jan card launch',
     [[r('Debit card activation and usage · gold-loan money onto the Fast Bank card · deposit retention and balances · pre-approved cash loan once risk signs off', 11)]],
     'Confirm the product list and a product owner for each', 820000),
    ('1.2', 'Triggers and offers',
     [[r('Move from batch mailings to event triggers: deposit maturity, loan disbursement, dormancy, inflows and outflows, salary day. Quick wins first (pages 10–12)', 11)]],
     'Agree wave 1 (five campaigns)', 820000),
    ('2', 'Infrastructure and operating model',
     [[r('One flow from idea to readout; bank BI builds segments in-house; weekly CVM committee; H21 runs the PMO; Creatio automates the same flow later (page 4)', 11)]],
     'Name an owner for each step and a weekly slot', 820000),
    ('3.1', 'Segmentation: as-is to to-be',
     [[r('From lists built per campaign to one Finalta-style tree: product holding × behaviour × lifecycle, with LTV per segment (page 5)', 11)]],
     'Agree the target segment tree', 820000),
    ('3.2', 'Active client definition',
     [[r('Keep as is: the definition is fixed in the contract', 11)]],
     'None – confirm', 520000),
]
y = 1680000
for code, topic, prop, dec, h in items:
    num(s, L, y + 30000, code, d=340000, size=9)
    tb(s, L + 440000, y + 40000, 2500000, h - 80000, [[r(topic, 13, True, '000000')]], name='Topic')
    tb(s, X2, y + 40000, 5250000, h - 80000, prop, name='Proposal')
    tb(s, X3, y + 40000, CW - (X3 - L), h - 80000, [[r(dec, 11, True, MAG)]], name='Decision')
    y += h
    hline(s, L, y - 20000, CW)
# side quests
py = y + 110000
rect(s, L, py, CW, 6250000 - py, shape='round', radius=0.06, name='Side quests panel')
band(s, L + 200000, py + 110000, 6000000, 'Open questions and side quests')
sq = [('Creatio', 'Which data sources feed it first: core banking, cards, app events, consents'),
      ('Measurement', 'Global control group vs campaign holdout; no t-test at this stage'),
      ('Best practices', 'Sessions with Anna and Nikita on how peers run CVM'),
      ('Current debit card offers', 'Review today’s terms: change, delete or update')]
cw4 = (CW - 400000) / 4
for i, (a, b) in enumerate(sq):
    tb(s, L + 200000 + i * cw4, py + 340000, cw4 - 150000, 6250000 - py - 380000,
       [[r(a, 11, True, INK)], [r(b, 10, False, INK)]], name='Side quest')

# ---------------------------------------------------------------- 4. I.2 Operating model
s = new_slide(prs, 'One flow from idea to readout lets the bank launch within 10 working days and learn from every campaign',
              'Campaign flow, owners and timing (proposed)', 'I. LONG-TERM PRIORITIES · 2. OPERATING MODEL')
steps = [
    ('Idea', 'CRM PO, product owners, H21', 'Backlog ranked by value × time to launch', 'Weekly'),
    ('PRD', 'CRM team with H21 (Alexey)', '9-question canvas (page 7) and one data request', '2 days'),
    ('Segment', 'Bank BI', 'Refreshable list with a random holdout; H21 sees counts only', '3 days'),
    ('Offer and content', 'Product owner, marketing, compliance', 'Terms, texts, visuals and legal check', '3 days, in parallel'),
    ('Launch', 'Channel owners: Viber, SMS, e-mail, call centre, branches', 'Sends, call lists, branch next-best-offer lists', 'Day 0'),
    ('Measure', 'Bank BI with H21', 'Uplift vs holdout at D+14 and D+30', 'D+30'),
    ('Decide', 'Weekly CVM committee', 'Scale, iterate once or stop; learnings logged in the campaign manager', 'Weekly'),
]
W7 = 1640000; STEP = (CW - W7) / 6
# brackets
x5 = L + 4 * STEP + W7
band(s, L, 1330000, x5 - L, 'Idea to launch: ≤10 working days¹', color=MAG, align='c')
hline(s, L + 100000, 1520000, x5 - L - 200000, color=MAG, lw=12700)
band(s, L + 5 * STEP, 1330000, R - (L + 5 * STEP), 'Learn: D+30', color=NAVY, align='c')
hline(s, L + 5 * STEP + 150000, 1520000, R - (L + 5 * STEP) - 250000, color=NAVY, lw=12700)
for i, (name, who, out, t) in enumerate(steps):
    x = L + i * STEP
    sh = rect(s, x, 1600000, W7, 460000, fill=PANEL if i < 5 else PINK, shape='pentagon' if i == 0 else 'chevron', name='Step')
    shape_text(sh, [[r(f'{i + 1}  {name}', 12, True, NAVY if i < 5 else MAG)]], margins=(120000 if i == 0 else 200000, 0, 60000, 0))
    cx, cw_ = x + (60000 if i == 0 else 180000), W7 - 260000
    band(s, cx, 2230000, cw_, 'Who')
    tb(s, cx, 2420000, cw_, 700000, [[r(who, 10.5)]], name='Who')
    band(s, cx, 3170000, cw_, 'Output')
    tb(s, cx, 3360000, cw_, 850000, [[r(out, 10.5)]], name='Output')
    band(s, cx, 4260000, cw_, 'Time')
    tb(s, cx, 4450000, cw_, 260000, [[r(t, 13, True, MAG if i < 5 else NAVY)]], name='Time')
hline(s, L, 4830000, CW, color=GREY)
band(s, L, 4900000, 3000000, 'Enablers')
en = [('Data', 'BI views with product, balance, transaction and consent flags; weekly refresh, daily for triggers'),
      ('Measurement', 'Global control: 5% of clients get no CVM messages; 10% random holdout per campaign; one readout template'),
      ('Tools', 'Campaign manager tracker today; Creatio adds triggers and journeys after the integrator is selected'),
      ('Governance', 'Weekly CVM committee (H21 runs the PMO); results to the bi-weekly ops committee and monthly SteerCo')]
pw = (CW - 3 * 120000) / 4
for i, (a, b) in enumerate(en):
    x = L + i * (pw + 120000)
    rect(s, x, 5110000, pw, 1140000, shape='round', radius=0.06, name='Enabler panel')
    tb(s, x + 150000, 5200000, pw - 300000, 1000000, [[r(a, 12, True, '000000')], [r(b, 10, False, INK)]], name='Enabler')
footnote(s, ['1. Today 2–16 days pass from a ready target list to launch (campaign manager, Jun–Aug 2026); PRD time is not tracked'])

# ---------------------------------------------------------------- 5. I.3.1 Segmentation
s = new_slide(prs, 'Segmentation should move from lists built per campaign to one value-based segment tree reused by every campaign',
              'Segmentation as-is and to-be (Finalta-style)', 'I. LONG-TERM PRIORITIES · 3. SEGMENTATION')
PW = 3250000
rect(s, L, 1400000, PW, 4850000, shape='round', radius=0.04, name='As-is panel')
band(s, L + 180000, 1520000, PW - 360000, 'As-is')
tb(s, L + 180000, 1740000, PW - 360000, 600000, [[r('A new list for every campaign', 14, True, '000000')]], name='Lead')
asis = ['Lists are built from product flags and balance bands, e.g. “no loan now, had loans before”, “balance 1–50k AMD”',
        'No shared segment ID and no LTV per segment, so campaigns cannot be compared',
        'No cap on contact pressure across campaigns',
        'Gold-loan-only clients (57% of the base) are not a managed segment']
tb(s, L + 180000, 2250000, PW - 360000, 2900000, [{'runs': [r(t, 11)], 'bullet': True, 'after': 6} for t in asis], name='As-is')
chip(s, L + 180000, 5650000, PW - 360000, 420000, '3.2 Active client: keep the contract definition', fill=WHITE, color=INK, size=10, bold=True)
arr = rect(s, L + PW + 80000, 3550000, 230000, 420000, fill=MAG, shape='chevron', name='Arrow')
TX = L + PW + 420000; TW = R - TX
band(s, TX, 1400000, TW, 'To-be', color=MAG)
tb(s, TX, 1620000, TW, 350000, [[r('Segments defined once in BI; LTV decides who gets rich offers and costly channels', 14, True, '000000')]], name='Lead')
layers = [
    ('1', 'Product holding', ['Gold loan only', 'Card only', 'Deposit only', 'Multi-product', 'Registered, no product']),
    ('2', 'Behaviour', ['Salary', 'Groceries', 'Taxi and restaurants', 'Shopping', 'Travel and FX', 'Auto', 'Marketplaces', 'Cash-out', 'Remittance receiver']),
    ('3', 'Lifecycle', ['New, 0–90 days', 'Active', 'Declining', 'Dormant 60 / 90 days', 'Churned']),
    ('4', 'Value', ['LTV decile: offer richness and channel cost (calls and branch for top deciles only)']),
]
y = 2300000
LBW = 1750000
for code, name, chips_ in layers:
    num(s, TX, y + 10000, code, d=280000, fill=NAVY)
    tb(s, TX + 360000, y + 40000, LBW - 360000, 300000, [[r(name, 12, True, NAVY)]], name='Layer')
    cx = TX + LBW; cy = y
    for c in chips_:
        w = int(len(c) * 62000 + 260000)
        if cx + w > R:
            cx = TX + LBW; cy += 360000
        chip(s, cx, cy, w, 290000, c, fill=PANEL, size=10)
        cx += w + 90000
    y = cy + 560000
    if code != '4':
        hline(s, TX, y - 150000, TW)
# benchmark strip
by = 5000000
band(s, TX, by, TW, 'Benchmark: value hides in sub-segments¹')
bm = [('Mono-product', 1.6, 336), ('Salary', 1.0, 29), ('Shopping', 18.0, 4), ('Travel', 17.7, 2)]
bw = (TW - 100000) / 4
for i, (n, v, k) in enumerate(bm):
    x = TX + i * bw
    tb(s, x, by + 230000, bw - 100000, 200000, [[r(n, 10, True, INK), r(f'  {k}k clients', 9, False, GREY)]], name='Bm label')
    rect(s, x, by + 500000, max(30000, (bw - 700000) * v / 18.0), 150000, fill=MAG if v > 10 else LIGHT, name='Bar')
    tb(s, x + max(30000, (bw - 700000) * v / 18.0) + 60000, by + 450000, 600000, 250000, [[r(f'{v:.1f}', 12, True, INK)]], name='Value')
tb(s, TX, by + 800000, TW, 300000, [[r('Net operating income ex-lending per client, KZT k a month: shopping and travel transactors are worth ~11x a mono-product client', 10, False, GREY)]], name='Bm note')
footnote(s, ['1. Kazakhstan bank, active mass clients, Apr 2026 (H21 reference case)'])

# ---------------------------------------------------------------- 6. II. Short term
s = new_slide(prs, 'Short term: launch five campaigns in Oct–Nov and scale only those that beat the holdout',
              'Wave 1: obvious campaigns on today’s data and channels', 'II. SHORT TERM')
TW6 = 6750000
band(s, L, 1400000, 400000, '#'); band(s, L + 400000, 1400000, 2300000, 'Wave-1 campaign'); band(s, L + 2800000, 1400000, 2500000, 'Target metric vs holdout'); band(s, L + 5350000, 1400000, 1400000, 'Base')
hline(s, L, 1610000, TW6, color=GREY)
w1 = [(1, 'Gold-loan money to card', 'Share of disbursements paid to a card; card balance at D+30', '~46k disbursements a month'),
      (2, 'Deposit maturity retention', 'Retained share of maturing volume', '15k depositors, 124bn AMD'),
      (7, 'Card activation push', 'Activated within 14 days; first purchase', '3.7k idle cards + ~10k new a month'),
      (9, 'Dormant card reactivation', 'Share with 1+ purchase within 30 days', '~60% of cards idle in a month'),
      (8, '7-day streak', 'Transactions per card; active days a month', 'Cards with 1–4 purchases a month')]
y = 1660000
for n, a, b, c in w1:
    num(s, L, y + 60000, n, d=280000)
    tb(s, L + 400000, y + 70000, 2350000, 420000, [[r(a, 12, True, '000000')]], name='Campaign')
    tb(s, L + 2800000, y + 70000, 2450000, 440000, [[r(b, 10.5)]], name='Metric')
    tb(s, L + 5350000, y + 70000, 1400000, 440000, [[r(c, 10.5, False, GREY)]], name='Base')
    y += 530000
    hline(s, L, y - 20000, TW6)
PX = L + TW6 + 250000
rect(s, PX, 1400000, R - PX, 2900000, shape='round', radius=0.05, name='Rules panel')
tb(s, PX + 180000, 1500000, R - PX - 360000, 300000, [[r('Rules of the game', 14, True, '000000')]], name='Lead')
rules = [('Today’s data and channels: ', 'BI lists; Viber, SMS, e-mail, call centre, branch – no IT build'),
         ('Holdout: ', '10% random per campaign, plus a 5% global control with no CVM messages'),
         ('Success: ', 'target group beats holdout (>0) on the target metric at D+30; no t-test at this stage'),
         ('Then: ', 'scale winners, iterate once, stop the rest')]
tb(s, PX + 180000, 1900000, R - PX - 360000, 2300000,
   [{'runs': [r(a, 11, True, INK), r(b, 11)], 'bullet': True, 'after': 6} for a, b in rules], name='Rules')
# timeline
band(s, L, 4480000, 3000000, 'Timeline (proposed)')
TL0 = L + 2750000; MW = (R - TL0) / 4
months = [('Oct', 31), ('Nov', 30), ('Dec', 31), ('Jan', 31)]
for i, (m, d) in enumerate(months):
    tb(s, TL0 + i * MW, 4480000, MW, 180000, [[r(m, 10, True, GREY)]], align='c', name='Month')
    vline(s, TL0 + i * MW, 4700000, 1550000, color=LINE)
vline(s, R, 4700000, 1550000, color=LINE)
def dx(mi, day):
    return TL0 + (mi + (day - 1) / months[mi][1]) * MW
tasks = [('PRDs, BI counts, consents', (0, 1), (0, 10), NAVY, ''),
         ('Segments, content, compliance', (0, 12), (0, 17), NAVY, ''),
         ('Wave 1 live, staggered', (0, 19), (1, 19), MAG, 'from 19 Oct'),
         ('Readout D+30; scale or stop', (1, 19), (2, 5), NAVY, ''),
         ('Wave 2 with the new cards', (2, 7), (3, 31), BLUE, 'card launch Dec–Jan')]
y = 4760000
for name, a, b, col, lab in tasks:
    tb(s, L, y, 2650000, 250000, [[r(name, 10.5, col in (MAG,), INK)]], name='Task')
    x1, x2 = dx(*a), dx(*b)
    rect(s, x1, y + 30000, x2 - x1, 180000, fill=col, name='Bar')
    if lab:
        tb(s, x2 + 60000 if x2 < R - 1200000 else x1 - 1300000, y, 1250000, 250000, [[r(lab, 9, False, GREY)]], align='l' if x2 < R - 1200000 else 'r', name='Bar label')
    y += 300000
footnote(s, ['Numbers refer to the campaign list on pages 10–11; bases: Fast Bank data Sep 2025, card funnel Mar–Aug 2026, transformation kick-off (MAU ~40%)'])

# ---------------------------------------------------------------- 7. III. Quick-win canvas
s = new_slide(prs, 'Every quick win is specified on one 9-question canvas, which doubles as the PRD',
              'Quick-win plan: questions to answer before launch, with our default answer', 'III. QUICK-WIN PLAN')
qs = [('Target area', 'Which product and lever: card usage, balances, deposits, gold-loan cross-sell, lending?', 'The priority products agreed in 1.1'),
      ('Whom we target', 'The largest segment by AMD value, or a sub-segment with 3–5x LTV inside it?', 'Start with the largest pool; richer offers only for high-LTV sub-segments'),
      ('Target metric', 'Balances, average or number of transactions, active cards, products per client?', 'One primary metric per campaign, per client, vs holdout'),
      ('Target action', '(a) What the client does, (b) the reward, (c) the MCCs that count', 'Reward below the expected margin uplift; capped per client'),
      ('Data source', 'A dynamic segment that refreshes, not a one-off list', 'BI view with clear SQL logic; H21 works with counts only'),
      ('Channels and fallback', 'Push / e-mail → Viber → SMS; call or branch for high value', 'Cheapest channel first, fallback for undelivered (Viber reached 36% in May)'),
      ('Content and design', 'Message, visual, call to action, legal text', 'One call to action; benefit in AMD; two variants to A/B test'),
      ('When', '(a) Real-time trigger or whole segment, (b) day and time', 'Triggers where possible: they convert 3–8x better than batch¹'),
      ('Impact tracking', 'Holdout, metric, readout dates, owner', '10% holdout plus global control; readouts at D+14 and D+30')]
GW = (CW - 2 * 120000) / 3; GH = (6250000 - 1400000 - 2 * 110000) / 3
for i, (a, b, c) in enumerate(qs):
    x = L + (i % 3) * (GW + 120000); y = 1400000 + (i // 3) * (GH + 110000)
    rect(s, x, y, GW, GH, shape='round', radius=0.05, name='Canvas card')
    num(s, x + 140000, y + 130000, i + 1, d=300000)
    tb(s, x + 540000, y + 160000, GW - 680000, 300000, [[r(a, 13, True, '000000')]], name='Question')
    tb(s, x + 140000, y + 540000, GW - 280000, 480000, [[r(b, 10.5)]], name='Detail')
    tb(s, x + 140000, y + 1030000, GW - 280000, GH - 1080000, [[r('Default: ', 10.5, True, MAG), r(c, 10.5)]], name='Default')
footnote(s, ['1. Finalta by McKinsey, Russian banks 2019: event-triggered cash-loan offers convert at 3.7–4.8% vs 0.6–1.1% for batch offers'])

# ---------------------------------------------------------------- 8. IV.1 Funnel
s = new_slide(prs, 'The card funnel is healthy up to activation; the gap is usage, so CVM should drive activity, ARPU and reactivation',
              'Card funnel and card usage', 'IV. FIRST FINDINGS · 1. FUNNEL')
FW = 6500000
band(s, L, 1400000, FW, 'Issuance funnel, cohort Mar–Aug 2026, per card¹')
BX = L + 2250000; BMAX = 2900000
stages = [('Applied', '', 24.0, 100, ''), ('Issued', 'median: next day', 24.0, 100, '100% of applied'),
          ('Delivered', 'excl. virtual cards', 21.3, 88.6, '89% of issued'), ('Activated', '96% within 90 days', 20.4, 84.8, '85% of issued')]
y = 1680000
for n, note, k, pct, step in stages:
    tb(s, L, y, 2150000, 250000, [[r(n, 12, True, '000000')]], name='Stage')
    if note:
        tb(s, L, y + 230000, 2150000, 200000, [[r(note, 9, False, GREY)]], name='Stage note')
    rect(s, BX, y + 40000, BMAX * pct / 100, 200000, fill=NAVY, name='Bar')
    tb(s, BX + BMAX * pct / 100 + 80000, y + 10000, 1300000, 260000, [[r(f'{k:.1f}k', 12, True, INK), r(f'  {step}', 9, False, GREY)]], name='Value')
    y += 470000
hline(s, L, y + 20000, FW, color=GREY)
band(s, L, y + 110000, FW, 'Usage, all cards²')
y += 400000
tb(s, L, y, 2150000, 250000, [[r('Active in a month', 12, True, '000000')]], name='Stage')
tb(s, L, y + 230000, 2150000, 200000, [[r('share of cards (MAU)', 9, False, GREY)]], name='Stage note')
rect(s, BX, y + 40000, BMAX, 200000, fill=PANEL, name='Bar bg')
rect(s, BX, y + 40000, BMAX * 0.40, 200000, fill=MAG, name='Bar')
tb(s, BX + BMAX * 0.40 + 80000, y + 10000, 700000, 260000, [[r('~40%', 12, True, MAG)]], name='Value')
vline(s, BX + BMAX * 0.75, y - 20000, 320000, color=INK, lw=12700, name='Target')
tb(s, BX + BMAX * 0.75 + 50000, y + 250000, 1300000, 200000, [[r('target 75%+', 9, True, INK)]], name='Target label')
y += 560000
tb(s, L, y, 2150000, 250000, [[r('Transactions', 12, True, '000000')]], name='Stage')
tb(s, L, y + 230000, 2150000, 200000, [[r('per card a month', 9, False, GREY)]], name='Stage note')
for j, (n, v) in enumerate((('All cards', 2.4), ('Active', 5.7), ('High-activity', 11.3))):
    yy = y + j * 300000
    rect(s, BX, yy + 50000, BMAX * v / 11.3 * 0.75, 170000, fill=MAG if j == 0 else LIGHT, name='Bar')
    tb(s, BX + BMAX * v / 11.3 * 0.75 + 80000, yy + 10000, 1500000, 260000, [[r(f'{v}', 12, True, INK), r(f'  {n}', 9, False, GREY)]], name='Value')
# so-what panel
PX = L + FW + 300000
rect(s, PX, 1400000, R - PX, 4850000, shape='round', radius=0.04, name='So what panel')
band(s, PX + 180000, 1520000, R - PX - 360000, 'So what')
sw = [('Issuance is not the problem: ', 'each step after the application loses 0–11 p.p.; CVM needs no acquisition fix'),
      ('Usage is the gap: ', '~40% of cards are active in a month vs a 75%+ target; an average card makes 2.4 transactions a month'),
      ('Activity pays: ', 'active cards make 2.4x the transactions and hold 3.4x the card balance of an average card, so the levers are activity, ARPU and reactivation'),
      ('Quick win: ', '3.7k issued cards are not activated, 1.7k of them for over 90 days – an activation push in wave 1'),
      ('For the card stream: ', 'only 36% of new registrations apply for a card, down from 42% in March to 27% in August; branches convert at half the mobile rate (32% vs 60%)')]
tb(s, PX + 180000, 1800000, R - PX - 360000, 4350000,
   [{'runs': [r(a, 11, True, INK), r(b, 11)], 'bullet': True, 'after': 7} for a, b in sw], name='So what')
footnote(s, ['1. Fast Bank card funnel extract (15 Sep 2026): 67.5k registrations; a card counts at a stage if it reached that stage or a later one',
             '2. MAU and target from the transformation kick-off (3 Sep 2026); transactions per card from the debit cards model v14 client profile'])

# ---------------------------------------------------------------- 9. IV.2 Product base
s = new_slide(prs, 'Gold loans hold 57% of clients and deposits hold the most money: gold-loan cross-sell and deposit retention are the largest CRM pools',
              'Fast Bank retail base by product, Sep 2025', 'IV. FIRST FINDINGS · 2. BASE BY PRODUCT')
C1, C2, C3 = L + 2150000, L + 4800000, L + 7450000
BW9 = 2000000
band(s, L, 1450000, 2000000, 'Product'); band(s, C1, 1450000, 2500000, 'Clients, k (share of base)'); band(s, C2, 1450000, 2500000, 'Portfolio, AMD bn'); band(s, C3, 1450000, 3600000, 'CRM lever')
hline(s, L, 1660000, CW, color=GREY)
prod = [('Gold loans', 134, '134 (57%)', 101, '101', True, '~46k disbursements a month: card, deposit and pre-approved loan offers at every visit'),
        ('Debit cards', 46, '46 (19%)', 1, '~1 balances', True, 'Usage: MAU ~40% vs 75%+ target; 84% of paid cards were given free'),
        ('Term deposits', 15, '15 (6%)', 124, '124', True, 'Retention at maturity: 8.4m AMD average; top-of-market rate (10.0% vs 8.05% median)'),
        ('Unsecured cash loans', 11, '11 (5%)', 16.5, '16.5', False, 'Pre-approved top-ups; plan triples to 69bn by 2028'),
        ('Mortgage', 5, '5 (2%)', 73, '73', False, 'Low CRM leverage; insurance and deposits for owners'),
        ('Current accounts', 0, 'n/a', 10.7, '10.7', False, 'Balances: plan 33bn in 2026, so card balances matter'),
        ('Credit cards', 0.1, '<0.1', 0.1, '0.1', False, 'Launching; plan 13.5k clients by 2028')]
y = 1720000
RH9 = 610000
for n, c, cl, p, pl, hi, lev in prod:
    tb(s, L, y + 90000, 2050000, 300000, [[r(n, 12, True, '000000' if hi else GREY)]], name='Product')
    col = MAG if hi else LIGHT
    wc = BW9 * c / 134
    if c > 0:
        rect(s, C1, y + 150000, max(20000, wc), 190000, fill=col, name='Bar')
    tb(s, C1 + max(20000, wc) + 70000, y + 110000, 1200000, 260000, [[r(cl, 11, True, INK if hi else GREY)]], name='Value')
    wp = BW9 * p / 124
    rect(s, C2, y + 150000, max(20000, wp), 190000, fill=col, name='Bar')
    tb(s, C2 + max(20000, wp) + 70000, y + 110000, 1200000, 260000, [[r(pl, 11, True, INK if hi else GREY)]], name='Value')
    tb(s, C3, y + 60000, R - C3, RH9 - 80000, [[r(lev, 10.5, False, INK if hi else GREY)]], name='Lever')
    y += RH9
    hline(s, L, y - 10000, CW)
footnote(s, ['Source: Fast Bank data, Sep 2025 (profit pools model, sheet “Bank model – main”); 236k retail clients, a client can hold several products; 68k activated debit cards in Q4 2025'])

# ---------------------------------------------------------------- 10–11. IV.3 Top campaigns
COLS = [('#', 0, 330000), ('Campaign', 380000, 2000000), ('Whom', 2480000, 1700000), ('When (trigger)', 4280000, 1550000),
        ('Client action → reward', 5930000, 2250000), ('Channel', 8280000, 1150000), ('KPI vs holdout', 9530000, 1150000), ('Wave', 10720000, 362528)]


def camp_table(s, rows):
    for h_, x, w in COLS:
        band(s, L + x, 1400000, w, h_, align='c' if h_ in ('#', 'Wave') else 'l')
    hline(s, L, 1610000, CW, color=GREY)
    y = 1650000
    RHc = 760000
    for n, name, src, whom, when, act, ch, kpi, wave in rows:
        num(s, L + 20000, y + 70000, n, d=280000, fill=NAVY)
        paras = [[r(name, 11, True, '000000')]]
        if src:
            paras.append([r(src, 8.5, False, TAN if src.startswith('Benchmark') else GREY)])
        tb(s, L + COLS[1][1], y + 70000, COLS[1][2], RHc - 100000, paras, name='Campaign')
        for (h_, x, w), t in zip(COLS[2:7], (whom, when, act, ch, kpi)):
            tb(s, L + x, y + 70000, w - 60000, RHc - 100000, [[r(t, 10)]], name=h_)
        num(s, L + COLS[7][1] + 60000, y + 70000, wave, d=260000, fill=WAVE[wave], size=10)
        y += RHc
        hline(s, L, y - 20000, CW)


s = new_slide(prs, 'Top campaigns (1/2): bring money into Fast Bank and keep it there',
              'Balances, deposits and lending', 'IV. FIRST FINDINGS · 3. TOP CAMPAIGNS')
camp_table(s, [
    (1, 'Gold-loan money to card', 'Team idea', 'Gold-loan clients without an active card (134k base)', 'Disbursement in a branch (~46k a month)',
     'Take the loan onto a Fast Bank card → preferential gold-loan rate', 'Branch next-best offer; SMS follow-up', 'Share of loans paid to card; balance at D+30', 1),
    (2, 'Deposit maturity: prolong or upgrade', 'Team idea', 'Maturing term deposits (15k clients, 124bn AMD)', '14, 7 and 1 days before maturity',
     'Prolong or auto-prolong, or move to savings, bonds or a card → rate or bonus', 'Call for large tickets; SMS, Viber', 'Retained share of maturing volume', 1),
    (3, 'Balance-based free service', 'Team idea', 'Cardholders whose free service rests on a deposit today', 'Tariff change with the new cards',
     'Keep a minimum average balance instead of a deposit → free service; check whether today’s depositors keep free cards', 'E-mail, Viber, app', 'Card balances; paid cards retained', 2),
    (4, 'Bring your money: 1% bonus', 'Team idea', 'Clients with inflows or salary at other banks', 'After a first inflow from another bank',
     'Move money from another bank and hold it a month, or make X purchases → 1% bonus, capped', 'Viber, e-mail, app', 'Net new balances held 30 days', 2),
    (5, 'Salary-day and outflow moment', 'Benchmark: McKinsey case; Kazakhstan bank', 'Salary and large-inflow clients (80% of salary leaves via ATMs¹)', 'Salary credit; cash-out or transfer to another bank',
     'Keep the money in → savings rate or cashback boost, in real time', 'Push, SMS', 'Share of salary kept after 7 days', 3),
    (6, 'Pre-approved cash loan for gold-loan clients', 'Benchmark: Finalta; Monzo', 'Gold-loan clients with a clean repayment record', 'Loan nearing its end; abandoned application',
     'Accept a pre-approved limit → loan without paperwork; call-back to finish the application', 'SMS, call, branch', 'Conversion vs holdout', 2),
])
footnote(s, ['1. Kazakhstan bank, salary clients (H21 reference case). Team ideas are from the CVM working session; benchmark ideas are from reference cases. Rewards and sizes to be set in each PRD'])

s = new_slide(prs, 'Top campaigns (2/2): build the card habit before the Dec–Jan card launch',
              'Card usage and engagement', 'IV. FIRST FINDINGS · 3. TOP CAMPAIGNS')
camp_table(s, [
    (7, 'Welcome quest, first 30 days', 'Benchmark: Bereke; Sber', 'New cardholders, days 0–30 (~10k cards a month)', 'Card issued; no purchase by day 6',
     'Tasks: first purchase, Apple / Google Pay, transfer, autopay → prize-draw tickets; day-6 boost', 'Push, SMS; call on day 7', 'Share with 5+ purchases in 30 days', 1),
    (8, '7-day streak', 'Team idea', 'Cardholders with 1–4 purchases a month', 'Weekly start',
     '1+ card purchase every day for 7 days → fixed bonus, e.g. 1,000 AMD', 'Push, Viber', 'Transactions per card; active days a month', 1),
    (9, 'Dormant reactivation', 'Team idea', 'Cards idle for 60 / 90 days, incl. 3.7k never activated', 'Day 60 or 90 without a purchase',
     'Make a purchase → one month of free ATM, free transfers and preferential rates', 'Viber, SMS fallback; call for high value', 'Reactivated share at D+30', 1),
    (10, 'Autopay switch', 'Benchmark: Sber; VTB', 'App users paying mobile or utilities elsewhere or in cash', 'After a bill payment',
     'Set up autopay for mobile or utilities → bonus or prize draw', 'App, push', 'Autopays set up; MAU', 3),
    (11, 'FX offers for traveller look-alikes', 'Team idea', 'Clients with travel spend, FX purchases or transfers abroad', 'Air ticket, hotel or FX purchase; before holidays',
     'Buy FX or pay abroad with the card → preferential FX rate', 'Push, Viber, e-mail', 'FX volume; card spend abroad', 2),
    (12, 'Referral (to test)', 'Team idea', 'Active cardholders', 'After the 5th purchase',
     'Invite a friend who activates and transacts → bonus to both, e.g. 2,000 AMD', 'App, Viber', 'New active cards; cost vs 10–20k AMD CAC', 3),
])
footnote(s, ['Team ideas are from the CVM working session; benchmark ideas are from reference cases (Bereke Bank premium CVM, Sber, VTB). Rewards and sizes to be set in each PRD'])

# ---------------------------------------------------------------- 12. IV.4 Prioritisation
s = new_slide(prs, 'Five campaigns combine high value with launch in under a month: they form wave 1',
              'Campaign prioritisation, preliminary', 'IV. FIRST FINDINGS · 4. PRIORITISATION')
GX, GY, GWm, GHm = L + 900000, 1650000, 6300000, 4000000
cw3, ch3 = GWm / 3, GHm / 3
rect(s, GX, GY, cw3, 2 * ch3, fill=PINK, name='Quick-win zone')
tb(s, GX + 80000, GY + 60000, cw3 - 160000, 200000, [[r('QUICK WINS → WAVE 1', 9, True, MAG)]], name='Zone label')
for i in range(4):
    hline(s, GX, GY + i * ch3, GWm, color=LINE)
    vline(s, GX + i * cw3, GY, GHm, color=LINE)
tb(s, L, GY - 280000, 2000000, 200000, [[r('Expected value¹', 10, True, GREY)]], name='Axis title')
for i, lab in enumerate(('High', 'Medium', 'Low')):
    tb(s, L, GY + i * ch3 + ch3 / 2 - 120000, 820000, 250000, [[r(lab, 11, True, INK)]], align='r', name='Y label')
for i, (lab, sub) in enumerate((('< 1 month', 'today’s data and channels'), ('1–3 months', 'product, pricing or risk decision'), ('3+ months', 'Creatio or the new app'))):
    tb(s, GX + i * cw3, GY + GHm + 60000, cw3, 400000, [[r(lab, 11, True, INK)], [r(sub, 9, False, GREY)]], align='c', name='X label')
tb(s, GX, GY + GHm + 480000, GWm, 200000, [[r('Time to launch', 10, True, GREY)]], align='c', name='Axis title')
pos = {1: (0, 0, 0.25, 0.45), 2: (0, 0, 0.55, 0.45), 7: (0, 1, 0.2, 0.5), 9: (0, 1, 0.5, 0.5), 8: (0, 1, 0.8, 0.5),
       3: (1, 0, 0.25, 0.4), 4: (1, 0, 0.55, 0.4), 6: (1, 0, 0.85, 0.4), 11: (1, 1, 0.5, 0.5),
       5: (2, 0, 0.5, 0.45), 10: (2, 1, 0.5, 0.5), 12: (2, 2, 0.5, 0.5)}
wave_of = {1: 1, 2: 1, 7: 1, 8: 1, 9: 1, 3: 2, 4: 2, 6: 2, 11: 2, 5: 3, 10: 3, 12: 3}
D = 400000
for n, (cx, cy, fx, fy) in pos.items():
    num(s, GX + cx * cw3 + fx * cw3 - D / 2, GY + cy * ch3 + fy * ch3 - D / 2 + 60000, n, d=D, fill=WAVE[wave_of[n]], size=12)
LX = L + 7550000
names = {1: 'Gold-loan money to card', 2: 'Deposit maturity: prolong or upgrade', 7: 'Welcome quest / activation push', 8: '7-day streak',
         9: 'Dormant reactivation', 3: 'Balance-based free service', 4: 'Bring your money: 1% bonus', 6: 'Pre-approved loan, gold-loan clients',
         11: 'FX offers for travellers', 5: 'Salary-day and outflow moment', 10: 'Autopay switch', 12: 'Referral'}
groups = [(1, 'Wave 1 · Oct–Nov', [1, 2, 7, 9, 8]), (2, 'Wave 2 · Dec–Jan, with the new cards', [3, 4, 6, 11]), (3, 'Wave 3 · 2027, needs Creatio or the new app', [5, 10, 12])]
y = 1450000
for w, title, ns in groups:
    band(s, LX, y, R - LX, title, color=WAVE[w])
    y += 230000
    for n in ns:
        num(s, LX, y, n, d=230000, fill=WAVE[w], size=9)
        tb(s, LX + 320000, y + 10000, R - LX - 320000, 230000, [[r(names[n], 10.5)]], name='Legend')
        y += 290000
    y += 150000
tb(s, LX, y, R - LX, 700000, [[r('Wave 1 needs only BI lists and today’s channels; the rest wait for pricing decisions, the risk model, Creatio or the new app', 10.5, True, INK)]], name='Note')
footnote(s, ['1. Qualitative: pool size × expected conversion × value per conversion; to be sized once BI counts arrive'])

# ---------------------------------------------------------------- 13. V. Current campaigns baseline
s = new_slide(prs, 'Current campaigns are mostly batch mailings without a holdout; where one was measured, uplift is at most 1 p.p.',
              'Campaigns May–Aug 2026, from the campaign manager', 'V. PATH FORWARD · CURRENT CAMPAIGNS')
TWb = 7450000
cols = [('Campaign', 0, 1900000), ('Channel', 1950000, 900000), ('Targeted', 2900000, 750000), ('Converted', 3700000, 850000),
        ('Holdout', 4600000, 800000), ('Uplift', 5450000, 700000), ('Result', 6200000, 1250000)]
for h_, x, w in cols:
    band(s, L + x, 1400000, w, h_, align='l' if h_ in ('Campaign', 'Channel', 'Result') else 'r')
hline(s, L, 1610000, TWb, color=GREY)
base = [('4% on balances', 'Jul–Aug', 'Viber', '24.6k', '33.3%', '33.1%', '+0.2 p.p.', 'Converted = balance +1%¹', True),
        ('', '', 'E-mail', '50.1k', '19.8%', '18.8%', '+0.9 p.p.', '', True),
        ('Consumer loans', 'Jul–Aug', 'Viber', '22.2k', '0.09%', '0.11%', '≈0', '23 loans, 52m AMD²', True),
        ('', '', 'E-mail', '31.3k', '0.04%', '0.05%', '≈0', '', True),
        ('Secured loans', 'Jun–Aug', 'Viber, call', '22.1k', '3 loans', '–', 'n/a', '56m AMD; 826 calls, 0 sales', False),
        ('Deposit and bond calls', 'May–Aug', 'Call', '1.5k', '2.7%', '–', 'n/a', '250m AMD sold', False),
        ('2% cashback, new cards', 'May–Jul', 'E-mail, Viber, SMS', '140k', '0.14%', '–', 'n/a', '202 cards', False),
        ('Promos (Back to School and 3 more)', '', 'E-mail, Viber, SMS', '222k+', '–', '–', 'n/a', 'No results reported', False)]
y = 1650000
for n, when, ch, t, c, hld, up, res, meas in base:
    RHb = 420000 if n != 'Promos (Back to School and 3 more)' else 480000
    if n:
        tb(s, L, y + 50000, 1900000, RHb, [[r(n, 11, True, '000000')], [r(when, 8.5, False, GREY)]] if when else [[r(n, 11, True, '000000')]], name='Campaign')
    vals = (ch, t, c, hld, up, res)
    for (h_, x, w), v in zip(cols[1:], vals):
        bold = h_ == 'Uplift' and meas
        tb(s, L + x, y + 60000, w, RHb - 60000, [[r(v, 10.5, bold, MAG if bold else INK)]], align='l' if h_ in ('Channel', 'Result') else 'r', name=h_)
    y += RHb if (n or True) else 0
    nxt_new = True
    hline(s, L + (0 if (base.index((n, when, ch, t, c, hld, up, res, meas)) + 1 < len(base) and base[base.index((n, when, ch, t, c, hld, up, res, meas)) + 1][0]) else 1950000), y - 10000, TWb - (0 if True else 0))
tb(s, L, y + 60000, TWb, 400000, [[r('Planned: bonds and credit-line campaigns already include a holdout; deposit cross-sell and card activation do not yet', 10, False, GREY)]], name='Planned')
PX = L + TWb + 250000
rect(s, PX, 1400000, R - PX, 4850000, shape='round', radius=0.04, name='So what panel')
band(s, PX + 170000, 1510000, R - PX - 340000, 'What it tells us')
sw = [('Holdout is rare: ', 'only 2 of 6 completed sales campaigns had one, and both show ≤1 p.p.'),
      ('Metrics are loose: ', 'a +1% balance rule counts a third of the holdout as converted'),
      ('Reach is weak: ', 'Viber delivered 36%, e-mail opened 7%, clicked 0.3%'),
      ('Targeted calls work: ', '2.7% conversion, ~6m AMD per sale')]
tb(s, PX + 170000, 1740000, R - PX - 340000, 2300000, [{'runs': [r(a, 10.5, True, INK), r(b, 10.5)], 'bullet': True, 'after': 5} for a, b in sw], name='So what')
band(s, PX + 170000, 4150000, R - PX - 340000, 'Questions to the bank', color=MAG)
qq = ['Why did Viber reach only 36%: invalid numbers or opt-outs?',
      'Is there one campaign calendar and a cap on messages per client?',
      'What drove the +13% in loan agreements, if targeted clients converted like the holdout?']
tb(s, PX + 170000, 4380000, R - PX - 340000, 1800000, [{'runs': [r(t, 10.5)], 'bullet': True, 'after': 5} for t in qq], name='Questions')
footnote(s, ['1. Client counts as converted if the average daily balance grew 1%+ vs the previous 30 days. 2. Bank-wide loan agreements rose from 740 to 839 a month during the campaign, but targeted clients converted no better than the holdout',
             'Source: Fast Bank campaign manager export, 15 Sep 2026'])

# ---------------------------------------------------------------- 14. V. Path forward
s = new_slide(prs, 'Path forward: PRDs, BI counts and consents in the next two weeks unlock the wave-1 launch on 19 Oct',
              'Open questions and next steps', 'V. PATH FORWARD')
cols = [('#', 0, 400000), ('Next step', 450000, 3200000), ('What exactly', 3750000, 4600000), ('Owner', 8450000, 1650000), ('Due¹', 10150000, 932528)]
for h_, x, w in cols:
    band(s, L + x, 1400000, w, h_, align='c' if h_ == '#' else 'l')
hline(s, L, 1610000, CW, color=GREY)
nx = [('0', 'PRD for each wave-1 campaign', 'Canvas → stages → one data request per campaign', 'Alexey (H21), CRM PO', '9 Oct'),
      ('1', 'BI counts, no personal data', 'Deposit maturities for the next 180 days (count and AMD by week and ticket band); cards issued but not activated, by age', 'Bank BI', '7 Oct'),
      ('2', 'Marketing consents and opt-outs', 'What is stored, where and by channel; how opt-outs work; service vs marketing messages', 'Compliance, CRM team', '7 Oct'),
      ('3', 'Pre-approved limits for gold-loan clients', 'Is the risk model ready to score cash-loan limits, and when', 'Risk-model stream', '14 Oct'),
      ('4', 'Current campaigns baseline', 'Answer the open questions (page 13); agree metric definitions and one campaign calendar', 'CRM team', '7 Oct'),
      ('5', 'Contact list for the whole chain', 'BI, channel owners (Viber, SMS, e-mail, call centre), branches, compliance, product owners', 'CRM PO', '2 Oct')]
y = 1660000
for n, a, b, o, d in nx:
    num(s, L + 50000, y + 90000, n, d=300000)
    tb(s, L + 450000, y + 110000, 3200000, 600000, [[r(a, 13, True, '000000')]], name='Step')
    tb(s, L + 3750000, y + 110000, 4600000, 600000, [[r(b, 11)]], name='Detail')
    tb(s, L + 8450000, y + 110000, 1650000, 600000, [[r(o, 11)]], name='Owner')
    tb(s, L + 10150000, y + 110000, 932528, 300000, [[r(d, 13, True, MAG)]], name='Due')
    y += 720000
    hline(s, L, y - 20000, CW)
footnote(s, ['1. Proposed dates'])

# ---------------------------------------------------------------- 15–16. VI. Longlist
SEG = ['New, 0–90 days', 'Gold-loan clients', 'Mass and salary', 'Affluent, depositors', 'Dormant, lapsing']
LC = [('Idea', 0, 4150000), ('seg', 4200000, 4150000), ('Benchmark', 8450000, 1350000), ('Needs', 9850000, 1232528)]
SW = 4150000 / 5


def longlist(s, groups):
    band(s, L, 1330000, 4000000, 'Idea')
    for i, sg in enumerate(SEG):
        tb(s, L + LC[1][1] + i * SW, 1250000, SW, 350000, [[r(sg.upper(), 8.5, True, GREY)]], align='c', anchor='b', name='Segment')
    band(s, L + LC[2][1], 1430000, LC[2][2], 'Benchmark'); band(s, L + LC[3][1], 1430000, LC[3][2], 'Needs')
    hline(s, L, 1640000, CW, color=GREY)
    y = 1690000
    k = 1
    for g, rows in groups:
        band(s, L, y + 20000, 4000000, g, color=NAVY)
        y += 230000
        for idea, segs, bm, need in rows:
            rh = 300000 if len(idea) <= 78 else 450000
            tb(s, L, y + 45000, LC[0][2], rh - 60000, [[r(f'{k}. ', 10, True, GREY), r(idea, 10)]], name='Idea')
            for i in range(5):
                cx = L + LC[1][1] + i * SW + SW / 2
                if i in segs:
                    rect(s, cx - 60000, y + rh / 2 - 60000, 120000, 120000, fill=MAG, shape='ellipse', name='Dot')
            tb(s, L + LC[2][1], y + 45000, LC[2][2] - 50000, rh - 60000, [[r(bm, 9, False, GREY)]], name='Benchmark')
            tb(s, L + LC[3][1], y + 45000, LC[3][2], rh - 60000, [[r(need, 9, False, INK)]], name='Needs')
            y += rh
            hline(s, L, y, CW)
            k += 1
        y += 40000
    return k


s = new_slide(prs, 'Longlist (1/2): cards and savings ideas map onto every segment and feed the backlog after wave 1',
              'Further ideas by product and segment', 'VI. LONGLIST OF CAMPAIGNS')
longlist(s, [
    ('Cards and payments', [
        ('First-month boosted cashback on top categories, e.g. 15% taxi, 10% restaurants', [0], 'Bereke', 'Cashback engine'),
        ('In-branch welcome: install the app, add Apple / Google Pay, first purchase with staff', [0, 1], 'Bereke', 'Branch script'),
        ('Personal offers: “X% on your first N purchases in your top category”; 400 variants tested, 20%+ fee income growth', [2, 3], 'McKinsey case', 'Offer engine'),
        ('Monthly choice of cashback categories from a bank-picked set of 4–5', [2], 'T-Bank', 'Cashback engine'),
        ('Merchant-funded partner offers, the richest ones for top tiers', [2, 3], 'Amex; Bereke', 'Partner platform'),
        ('Bonus-balance reminder: “you have XX bonuses – time to spend them”', [2, 4], 'McKinsey case', 'Cashback engine'),
        ('Privileges page and education for Premium and Elite holders', [3], 'Bereke', 'App content'),
    ]),
    ('Savings and investments', [
        ('Welcome-rate savings account; round-ups from card purchases to savings', [0, 2], 'Savings stream', 'Savings product'),
        ('Keep your salary at Fast Bank → higher deposit rate', [2], 'Bereke', 'Pricing decision'),
        ('Deposit cross-sell to past depositors with loans (planned: 66k targeted)', [1, 3], 'Fast Bank, planned', 'None'),
        ('Bond offers linked to coupon dates and market news', [3], 'Bereke; Alfa', 'Content'),
        ('Relationship-manager hand-off before a promo deposit rate ends', [3], 'Bereke', 'RM capacity'),
        ('Lottery deposit', [2], 'Savings stream', 'Savings product'),
        ('Flexible savings message: “withdraw any time without losing interest”', [2, 4], 'Yandex Pay', 'Savings product'),
    ]),
])
footnote(s, ['Sources: Bereke Bank premium CVM (SteerCo, Aug 2026); Finalta by McKinsey; McKinsey personal-offers case; MTS Bank; Kazakhstan bank segmentation; Fast Bank savings stream'])

s = new_slide(prs, 'Longlist (2/2): lending, FX, app and insurance ideas need the risk model, Creatio or the new app',
              'Further ideas by product and segment', 'VI. LONGLIST OF CAMPAIGNS')
longlist(s, [
    ('Lending', [
        ('Top-up offer as a loan nears its end', [1, 2], 'Finalta', 'Risk model'),
        ('Overdraft or credit line when the balance nears zero', [2], 'Monzo', 'Product, risk model'),
        ('Instalments after a large purchase', [2, 3], 'Revolut', 'BNPL decision'),
        ('“Want more or a better rate” option and an LTV-based counter-offer after a decline', [1, 2, 3], 'MTS Bank', 'Risk model'),
        ('“Ghost product”: a declined offer stays on the app home screen, one tap to activate', [1, 2, 4], 'MTS Bank', 'New app'),
        ('Car loan for auto-category spenders (only 5% of them hold one)', [3], 'Kazakhstan bank', 'Product'),
        ('Credit-line stimulation (planned, with holdout)', [2], 'Fast Bank, planned', 'None'),
    ]),
    ('FX and transfers', [
        ('Remittance receivers: receive to the card and keep part as a balance', [1, 2], 'Armenia specific', 'Transfer data'),
        ('FX at a special rate in the app; large international transfers', [3], 'Bereke', 'FX pricing'),
    ]),
    ('App and engagement', [
        ('Daily prize draw for 1–10 in-app payments (transport, mobile, utilities)', [2], 'Halyk', 'New app'),
        ('Monthly personal tasks: “pay 5 times”, “set up autopay”', [2, 4], 'Sber', 'Offer engine'),
        ('App tips (“pay for parking in the app”); mobile-banking adoption (in progress)', [1, 4], 'McKinsey case; Fast Bank', 'None'),
        ('In-app offer showcase: inbox, carousel, stories, activate button', [0, 2, 3], 'McKinsey case', 'New app'),
    ]),
    ('Insurance', [
        ('Gadget insurance when the app is installed on a new phone; home insurance on address change', [2, 3], 'Revolut; Barclays', 'Partner insurer'),
    ]),
])
footnote(s, ['Sources: Finalta by McKinsey; Monzo; Revolut; Barclays; MTS Bank; Halyk; Sber; McKinsey personal-offers case; Kazakhstan bank segmentation'])

prs.save(OUT)
print('saved', OUT, len(prs.slides))
