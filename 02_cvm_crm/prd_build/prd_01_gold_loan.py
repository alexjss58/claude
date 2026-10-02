"""PRD #1 - Gold-loan money to card. Builds the Word file; all economics computed here.
python3 prd_01_gold_loan.py [out.docx]
"""
import sys, os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    '~/Downloads/20261002_FastBank_CVM_PRD_01_GoldLoan_to_card_v1.docx')

NAVY = RGBColor(0x20, 0x2A, 0x7D); MAG = RGBColor(0xEC, 0x00, 0x8C); GREY = RGBColor(0x59, 0x59, 0x59)
PANEL = 'F1F1F7'; HEAD = '202A7D'

# ---------------------------------------------------------------- economics
A = dict(
    ticket=600_000,          # avg gold loan sold, AMD (profit pools v5.1: 0.58-0.61m in 2025-26)
    rate=0.195,              # gold-loan rate p.a. (profit pools 'Loans' r133, market 2024; FB tariff to confirm)
    refund_share=0.25,       # share of first-month interest returned
    refund_cap=3_000,        # AMD
    base_q=0.05,             # holdout: share reaching 5+ eligible purchases in 30 days anyway
    uplift=0.10,             # +10 p.p. qualifying vs holdout
    takeup=0.40,             # share of treated taking the loan on the card
    v_month=1_237,           # net card margin a month, gold-loan card with 5+ purchases (model v19.1 Cards dataset)
    v_months=6,              # months of that margin counted in year 1 (decay)
    float_share=0.10,        # avg share of the loan kept on the card in the first 30 days
    ftp=0.111, card_rate=0.04,
    msgs=3, msg_cost=20,     # SMS / Viber per targeted client, AMD per message
    base_year=100_000,       # unique gold-loan clients without an active card targeted a year
    nii_margin=0.106, loan_months=4,
)
m1_int = A['ticket'] * A['rate'] / 12
refund = min(A['refund_share'] * m1_int, A['refund_cap'])
v_card = A['v_month'] * A['v_months']
float_inc = A['ticket'] * A['float_share'] * (A['ftp'] - A['card_rate']) / 12
comms = A['msgs'] * A['msg_cost']


def net_per_k(u=A['uplift'], R=refund, vm=A['v_months'], take=A['takeup']):
    """Net P&L per 1,000 targeted clients, AMD."""
    ben = u * 1000 * A['v_month'] * vm + take * 1000 * float_inc
    cost = (A['base_q'] + u) * 1000 * R + 1000 * comms
    return ben - cost


ben_cards = A['uplift'] * 1000 * v_card
ben_float = A['takeup'] * 1000 * float_inc
cost_ref = (A['base_q'] + A['uplift']) * 1000 * refund
cost_dead = A['base_q'] * 1000 * refund
cost_msg = 1000 * comms
NET = ben_cards + ben_float - cost_ref - cost_msg
slope = v_card - refund
be_uplift = (A['base_q'] * refund + comms - A['takeup'] * float_inc) / slope
worst = net_per_k(u=0) / 1000
extra_loan_nii = A['ticket'] * A['nii_margin'] * A['loan_months'] / 12
year_net = NET / 1000 * A['base_year'] * 0.9
year_cards = A['uplift'] * A['base_year'] * 0.9


def amd(x, k=False):
    if k:
        return f"{x/1000:,.0f}k"
    return f"{x:,.0f}"


def mn(x):
    return f"{x/1e6:,.1f}m"


# ---------------------------------------------------------------- doc helpers
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2); sec.top_margin = sec.bottom_margin = Cm(1.8)
st = doc.styles['Normal']; st.font.name = 'Arial'; st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
st.paragraph_format.space_after = Pt(4)
for lvl, size in [(1, 14), (2, 11.5)]:
    h = doc.styles[f'Heading {lvl}']; h.font.name = 'Arial'; h.font.size = Pt(size); h.font.bold = True
    h.font.color.rgb = NAVY; h.element.rPr.rFonts.set(qn('w:asciiTheme'), 'Arial') if False else None
    rf = h.element.rPr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts'); h.element.rPr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
        rf.set(qn(a), 'Arial')
    for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(a)) is not None:
            del rf.attrib[qn(a)]
    h.paragraph_format.space_before = Pt(12 if lvl == 1 else 8); h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
W = 17.0  # text width, cm


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement('w:shd')
    s.set(qn('w:val'), 'clear'); s.set(qn('w:color'), 'auto'); s.set(qn('w:fill'), fill); tcPr.append(s)


def runs(p, text, size=None, color=None, bold=None, italic=None):
    """text with **bold** segments"""
    parts = text.split('**')
    for i, t in enumerate(parts):
        if not t:
            continue
        r = p.add_run(t)
        r.bold = (i % 2 == 1) if bold is None else bold
        if italic: r.italic = True
        if size: r.font.size = Pt(size)
        if color is not None: r.font.color.rgb = color
    return p


def P(text, size=None, color=None, italic=False, after=None, align=None):
    p = doc.add_paragraph(); runs(p, text, size, color, italic=italic)
    if after is not None: p.paragraph_format.space_after = Pt(after)
    if align: p.alignment = align
    return p


def B(text, level=0):
    p = doc.add_paragraph(style='List Bullet' if level == 0 else 'List Bullet 2'); runs(p, text)
    p.paragraph_format.space_after = Pt(2)
    return p


def N(text):
    p = doc.add_paragraph(style='List Number'); runs(p, text); p.paragraph_format.space_after = Pt(2)
    return p


def H(text, lvl=1):
    return doc.add_heading(text, lvl)


def T(rows, widths, header=True, size=8.5, bold_first_col=False, total_rows=()):
    t = doc.add_table(rows=len(rows), cols=len(widths)); t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j); c.width = Cm(widths[j])
            c.paragraphs[0].text = ''
            for k, line in enumerate(str(val).split('\n')):
                p = c.paragraphs[0] if k == 0 else c.add_paragraph()
                p.paragraph_format.space_after = Pt(1)
                hdr = header and i == 0
                runs(p, line, size, RGBColor(0xFF, 0xFF, 0xFF) if hdr else None,
                     bold=True if (hdr or (bold_first_col and j == 0) or i in total_rows) else None)
                if j > 0 and isinstance(val, str) and val[:1] in '+-−0123456789' and len(val) < 18:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if header and i == 0:
                shade(c, HEAD)
            elif i in total_rows:
                shade(c, PANEL)
    for j, w in enumerate(widths):
        for c in t.columns[j].cells:
            c.width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def box(title, lines, fill=PANEL):
    t = doc.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = t.cell(0, 0); c.width = Cm(W); shade(c, fill)
    p = c.paragraphs[0]; runs(p, title, 10.5, NAVY, bold=True); p.paragraph_format.space_after = Pt(3)
    for ln in lines:
        q = c.add_paragraph(style='List Bullet'); runs(q, ln, 9.5); q.paragraph_format.space_after = Pt(2)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# ---------------------------------------------------------------- content
p = P('FAST BANK · CVM WAVE 1 · CAMPAIGN #1', 8.5, MAG, after=0)
p = doc.add_paragraph(); runs(p, 'PRD: Gold-loan money to card', 20, NAVY, bold=True); p.paragraph_format.space_after = Pt(2)
P('Take the gold loan onto a Fast Bank card, use the card, get part of the interest back', 11, GREY, after=8)
T([['Version', 'Date', 'Status', 'Prepared by', 'Campaign owner'],
   ['v1, draft for discussion', '2 Oct 2026', 'For review; executive summary goes to SteerCo on 7 Oct', 'H21 (Alexey Suprunov)', 'CRM PO (Tigran Hakobyan)']],
  [3.0, 2.3, 4.7, 3.5, 3.5], size=8.5)

box('Executive summary (reusable for SteerCo)', [
    '**Problem.** 57% of Fast Bank clients (134k) hold a gold loan, and the bank already issues them a card: 54k "gold-loan" cards in Jan–Aug 2026, 56% of all new cards. '
    'But the loan is paid out **in cash**, and only **13.5%** of these cards make 5+ purchases a month (other cards: 26%). The average balance is 2k AMD and the median is 0.',
    '**Offer.** Take the loan onto your Fast Bank card. Make **5+ card purchases within 30 days** (gambling, transfers and cash-like MCCs do not count) and get back '
    f'**25% of the first month\'s interest** (≈{amd(refund)} AMD on a {amd(A["ticket"]/1000)}k AMD loan, capped at {amd(A["refund_cap"])} AMD). Cash-outs at Fast Bank ATMs stay free, so the client is never worse off than with cash.',
    f'**Why the bank wins.** An active gold-loan card earns ≈{amd(A["v_month"])} AMD a month; an idle one ≈14 AMD. The refund is paid **only** to clients who reach the activity that earns this margin.',
    f'**Economics (base case).** With an uplift of +{A["uplift"]*100:.0f} p.p. vs the holdout, the campaign makes ≈**+{amd(NET/1000)} AMD per targeted client** (benefit {(ben_cards+ben_float)/(cost_ref+cost_msg):.1f}× cost). '
    f'At {amd(A["base_year"]/1000)}k targeted clients a year that is ≈**{mn(year_net)} AMD** in the first year and ≈**{amd(year_cards/1000)}k extra active cards**. '
    f'Upside from repledges, deposits and the new paid tiers is not counted.',
    f'**Downside is capped.** Break-even needs only **+{be_uplift*100:.1f} p.p.** uplift. With zero uplift the loss is ≈{amd(-worst)} AMD per targeted client (refunds to people who would have qualified anyway, plus SMS). '
    'A 4-week pilot with a 10% holdout proves the effect before scale-up.',
    '**Ask.** Approve the pilot; name the owners in branches, legal and operations; give BI a daily data view (§3.5).',
])

H('1. Why this campaign')
B('**Largest pool and visit flow.** Gold loans: 134k clients (57% of the base), 101bn AMD portfolio, ≈49k loans sold a month (588k in 2025; ≈4.4 loans per client a year). '
  'Each loan is a branch visit, the strongest moment to change behaviour.')
B('**The card is issued but not used.** Gold-loan cards issued Jan–Aug 2026: 54,286 (84% ArCa). 39% were active in Jun–Aug, against 58% for other cards. '
  'Per card a month: 1.7 debit transactions (others 3.3), 23k AMD of purchases (others 43k), 2k AMD balance (others 16k). 1.2% hold a deposit (others 22%).')
B('**The loan money leaves on day 0.** Cash is paid at the teller, so the bank earns nothing on the money and the card stays idle. On the card, the money passes through Fast Bank: float, purchases and interchange, and a habit that outlives the loan.')
B('**Supports the card targets.** 195k activated cards in 2026, 470k in 2028, MAU ≈40% → 75%+. This campaign moves existing cards from idle to active ahead of the Dec–Jan card launch.')
P('Card value by activity (gold-loan cards issued in 2026, AMD per card a month; source: debit-cards model v19.1, Cards dataset; fee and interchange rates as in the model):', 9, GREY)
T([['Activity level', 'Share of gold-loan cards', 'Purchases, AMD / month', 'Net card margin, AMD / month'],
   ['5+ purchases a month', '13.5%', '162k', amd(A['v_month'])],
   ['1–4 purchases a month', '9.5%', 'n/a', '188'],
   ['No purchases', '77.0%', '≈0', '14']],
  [5.0, 3.8, 3.8, 4.4])
P('Net margin = interchange 0.5% + ATM and C2C fees + balance float at FTP 11.1% minus 4% paid, minus ArCa processing 0.1% of volume.', 8, GREY, italic=True)

H('2. Campaign card (building blocks)')
T([['Block', 'Decision'],
   ['1. Target product and P&L lever', 'Debit card (whichever card the branch issues today: ArCa or Visa Digital; Free tier from Dec–Jan). Levers: purchases and interchange, card balance, transaction fees; the gold loan is only the trigger.'],
   ['2. Whom', 'Clients receiving a gold loan (new or repeat) who have **no active card** (no card purchase in the last 30 days). Exclusions: no marketing consent, staff, loans in arrears, clients already in the campaign (one offer per client per 6 months). Size: ≈80% of disbursements; ≈100k unique clients a year.'],
   ['3. Target metric', '**Primary:** share of targeted clients with 5+ eligible purchases in 30 days, treated vs holdout, converted to **net P&L per targeted client** (§4). **Secondary:** share of loans taken on the card, card balance at D+30, purchases at D+60 / D+90, app activation, repledge within 90 days. **Guardrails:** refund cost per targeted client, gambling share of card spend, complaints.'],
   ['4. Client action → reward', f'Take the loan onto the card (D0) → 5+ card purchases of any amount, total ≥ 20,000 AMD, at eligible merchants within 30 days → **bonus = 25% of the interest accrued in the first 30 days, capped at {amd(A["refund_cap"])} AMD**, credited to the card on D+31. Fast Bank ATM and teller cash-outs of the loan stay free.'],
   ['5. Data', 'Daily BI view (§3.5). H21 receives aggregates only.'],
   ['6. Channels and fallback', 'Branch at D0 (loan officer script and leaflet), the main channel. SMS / Viber for confirmation, progress and result; push for app users. WhatsApp / Telegram once integrated. No telemarketing (value per client too low).'],
   ['7. Content and design', 'Marketing (Zhanna) owns the final texts and visuals; drafts in §3.7. Legal review of the bonus terms.'],
   ['8. When', 'Trigger = gold-loan disbursement. Daily batch (no real-time before Creatio): the D+1 message goes to yesterday\'s disbursements. Journey in §3.8.'],
   ['9. Impact tracking', '10% random holdout of eligible disbursements (no offer, loan in cash as today) plus the 5% bank-wide global control. Readouts at D+30 (qualification, refunds) and D+90 (persistence). Decision rules in §5.'],
   ], [4.0, 13.0], bold_first_col=True)

H('3. Detailed design')
H('3.1 Offer terms (draft)', 2)
B('**Who can join:** a client who receives a gold loan in a pilot branch during the pilot window and agrees to take the loan onto a Fast Bank card. If the client has no card, the branch issues one on the spot, as today.')
B('**What counts:** card purchases (POS, e-commerce, Apple / Google Pay) settled within 30 days of disbursement. **Not counted:** gambling and betting (MCC 7995 and related), quasi-cash, money transfers and e-wallet top-ups, ATM and teller cash-outs, utilities and government payments. This is the same exclusion list as the cashback engine (45 MCCs).')
B(f'**Bonus:** 25% of the interest accrued on the loan in the first 30 days, capped at {amd(A["refund_cap"])} AMD. If the loan is repaid earlier, the bonus is based on the interest actually accrued. One bonus per client per campaign.')
B('**Form:** a promotional bonus credited to the card. The loan contract and its rate do **not** change. Legal to confirm the wording and any tax treatment (open question).')
B('**Cash access:** the loan amount can be withdrawn free at Fast Bank ATMs and cash desks. Standard fees apply at other banks\' ATMs; the client is told this at D0.')
H('3.2 Segment and size', 2)
B('Gold-loan sales: ≈49k loans a month across ≈134k clients. After excluding clients with an active card and repeat offers, ≈100k unique clients a year (≈8k a month) enter the campaign. BI to confirm.')
B('The pilot needs ≈4,400 eligible disbursements (≈4k treated + ≈440 holdout) to read a +5 p.p. difference: about 4 weeks in a quarter of the branch network, or 1–2 weeks network-wide.')
H('3.3 Holdout and measurement', 2)
B('Random 10% of eligible disbursements, assigned by BI by client ID (e.g. last digit), are not offered the campaign. Branch staff see a flag "no offer" in the list, or the offer is only shown to flagged clients.')
B('The bank-wide 5% global control (agreed with Tigran) is excluded from all campaigns, this one included.')
B('Comparison: treated vs holdout on the primary metric and on net card margin per targeted client at D+30 and D+90. No significance test at this stage; sample sized for a readable +5 p.p. gap.')
H('3.4 Owners', 2)
T([['Role', 'Who', 'Does what'],
   ['Campaign owner', 'CRM PO (Tigran Hakobyan)', 'Approves the PRD, runs the weekly CVM committee, decides scale or stop'],
   ['Product', 'Gold-loan product owner (TBD); cards PO (Ani Arshakyan)', 'Terms, free cash-out at FB ATMs, loan-to-card disbursement in the core system'],
   ['Branches', 'Head of branch network (TBD)', 'Script, leaflet, staff briefing; daily list of offered / not offered'],
   ['Marketing', 'Zhanna (head of marketing)', 'Texts, visuals, SMS / Viber / push sends'],
   ['BI', 'Grigoriy Arutyunyan', 'Daily view, holdout flags, qualification and bonus lists, readouts'],
   ['Legal / compliance', 'TBD', 'Bonus terms, consents, tax'],
   ['Operations', 'TBD', 'Credit the bonuses at D+31 from the BI list'],
   ['H21', 'Alexey Suprunov', 'PRD, economics, readout template, iteration']],
  [3.2, 5.3, 8.5])
H('3.5 Data (BI view, refreshed daily)', 2)
B('**Disbursements:** date, branch, client ID, loan ID, amount, rate, disbursement channel (cash / card), card ID, holdout flag, consent flags.')
B('**Card activity per client and day:** purchases (count, amount, MCC), ATM / teller cash-outs (Fast Bank / other), C2C, end-of-day card balance.')
B('**Outputs:** progress per participant (purchases so far); qualification list at D+30; bonus amount (interest accrued × 25%, capped); readout aggregates for H21.')
H('3.6 Channels', 2)
B('**Branch (D0):** a 3-line loan-officer script plus a leaflet. Card issued or activated on the spot, with the app installed where possible ("make a card → connect the app").')
B('**SMS / Viber (D+1, D+10, D+22, D+31):** confirmation, progress, reminder, result. Viber delivered only 36% in past campaigns, so SMS is the fallback for non-delivered Viber.')
B('**Push:** same touchpoints for app users, with UTM-tagged deep links to the card screen (Firebase).')
H('3.7 Messages (draft; marketing to finalise in Armenian / Russian)', 2)
T([['When', 'Channel', 'Draft text'],
   ['D0', 'Branch', '"Take your loan on your Fast Bank card. Pay by card 5 times in 30 days and we\'ll give you back part of the interest – up to 3,000 AMD. Withdrawals at our ATMs are free."'],
   ['D+1', 'SMS / Viber / push', '"Your loan is on your card. Make 5 card purchases by {date} and get back 25% of the first month\'s interest (up to 3,000 AMD)."'],
   ['D+10', 'SMS / Viber / push', '"You have made {n} of 5 purchases. {5-n} more by {date} to get your interest back."'],
   ['D+22', 'SMS / Viber / push', '"8 days left: {5-n} card purchases to go for your bonus of up to 3,000 AMD."'],
   ['D+31', 'SMS / Viber / push', 'Qualified: "{bonus} AMD of your interest is back on your card." Not qualified: "Keep paying by card – your next loan can earn the bonus."']],
  [1.6, 3.0, 12.4])
H('3.8 Journey', 2)
T([['Day', 'Step', 'Owner'],
   ['D0', 'Loan disbursed; offer at the desk; loan to the card; app set-up', 'Branch'],
   ['D+1', 'Daily BI list → confirmation message (holdout excluded)', 'BI → marketing'],
   ['D+10 / D+22', 'Progress and reminder messages to non-qualified participants', 'BI → marketing'],
   ['D+30', 'Qualification list and bonus amounts', 'BI'],
   ['D+31', 'Bonuses credited; result messages', 'Operations, marketing'],
   ['D+30 / D+90', 'Readouts vs holdout; weekly CVM committee decides', 'BI, H21, CRM PO']],
  [2.4, 10.6, 4.0])

H('4. Economics: does the campaign make money?')
P('Logic: the bank gives up part of the loan interest (the bonus) and gains debit-card P&L. Only the **difference vs the holdout** counts as gain, '
  'while the bonus is paid to **every** qualifier, including those who would have been active anyway (deadweight).')
H('4.1 Base case per 1,000 targeted clients', 2)
T([['Line', 'Calculation', 'AMD'],
   ['Extra active cards', f'({(A["base_q"]+A["uplift"])*100:.0f}% treated − {A["base_q"]*100:.0f}% holdout) × 1,000', f'{A["uplift"]*1000:.0f} cards'],
   ['+ Card margin from extra active cards', f'{A["uplift"]*1000:.0f} × {amd(A["v_month"])} AMD × {A["v_months"]} months', '+' + amd(ben_cards)],
   ['+ Float on loan money kept on the card', f'{A["takeup"]*100:.0f}% take-up × {amd(A["ticket"])} × {A["float_share"]*100:.0f}% avg kept × (11.1% − 4%) / 12', '+' + amd(ben_float)],
   ['= Benefit', '', '+' + amd(ben_cards + ben_float)],
   ['− Interest bonus', f'{(A["base_q"]+A["uplift"])*1000:.0f} qualifiers × {amd(refund)} (of which deadweight {amd(cost_dead)})', '−' + amd(cost_ref)],
   ['− Messages', f'{A["msgs"]} × {A["msg_cost"]} AMD × 1,000', '−' + amd(cost_msg)],
   ['= Net P&L', f'benefit / cost = {(ben_cards+ben_float)/(cost_ref+cost_msg):.1f}×', '+' + amd(NET)],
   ['Per targeted client', '', '+' + amd(NET/1000)]],
  [5.4, 8.6, 3.0], total_rows=(4, 7, 8))
P(f'Break-even uplift: **+{be_uplift*100:.1f} p.p.** Worst case, no uplift at all: **{worst:,.0f} AMD per targeted client** '
  f'(≈{mn(abs(worst)*A["base_year"])} AMD a year at full scale). Each extra point of uplift adds ≈{amd(slope*10)} AMD per 1,000 targeted clients.')
H('4.2 Sensitivity: net P&L per 1,000 targeted clients, AMD thousands', 2)
refunds = [1_500, refund, min(0.5 * m1_int, 5_000)]
rows = [['Uplift vs holdout', f'Bonus {amd(refunds[0])} AMD', f'Bonus {amd(refunds[1])} AMD (base: 25%)', f'Bonus {amd(refunds[2])} AMD (50%)']]
for u in [0, 0.025, 0.05, 0.10, 0.15]:
    rows.append([f'+{u*100:.1f} p.p.' if u else '0 (no effect)'] + [f'{net_per_k(u=u, R=R)/1000:+,.0f}' for R in refunds])
T(rows, [4.0, 4.0, 4.6, 4.4])
rows = [['Months of active margin counted', '3', '6 (base)', '12']]
rows.append(['Net per 1,000 targeted, AMD thousands'] + [f'{net_per_k(vm=v)/1000:+,.0f}' for v in (3, 6, 12)])
T(rows, [6.2, 3.6, 3.6, 3.6])
H('4.3 Upside not counted', 2)
B(f'**Gold-loan retention:** an extra repledge earns ≈{amd(extra_loan_nii)} AMD of interest margin ({amd(A["ticket"]/1000)}k × ≈10.6% net margin × 4 months). +1 p.p. repledge = +{amd(10*extra_loan_nii/1000)}k AMD per 1,000 targeted clients.')
B('**Deposits and balances:** only 1.2% of gold-loan cardholders hold a deposit, against 22% for other cardholders.')
B('**New paid tiers from 2027** (service fee, cashback economics): active clients are the ones who migrate.')
B('**Cash handling:** less cash paid out at the teller.')
H('4.4 Assumptions and sources', 2)
T([['Assumption', 'Value', 'Source / status'],
   ['Average gold loan', f'{amd(A["ticket"])} AMD', 'Profit pools v5.1: 0.58m (2025) – 0.61m (2026F). Confirm with BI'],
   ['Gold-loan rate', f'{A["rate"]*100:.1f}% p.a.', 'Market average (CBA data in profit pools). Confirm the Fast Bank tariff'],
   ['First-month interest → bonus', f'{amd(m1_int)} → {amd(refund)} AMD', '25% of 1 month, cap 3,000'],
   ['Qualifying anyway (holdout)', f'{A["base_q"]*100:.0f}%', '13.5% of all gold-loan cards make 5+ purchases; the target has no active card. Pilot measures it'],
   ['Uplift', f'+{A["uplift"]*100:.0f} p.p.', 'Assumption; activation campaigns typically +10–15 p.p. Pilot measures it'],
   ['Take-up of loan on the card', f'{A["takeup"]*100:.0f}%', 'Assumption; pilot measures it'],
   ['Margin of an active card', f'{amd(A["v_month"])} AMD / month', 'Model v19.1, gold-loan cards with 5+ purchases a month'],
   ['Months of margin in year 1', f'{A["v_months"]}', 'Conservative: about half the active cards stay active'],
   ['Average share of the loan kept on the card, first 30 days', f'{A["float_share"]*100:.0f}%', 'Assumption; FTP 11.1%, 4% paid on card balances'],
   ['Message cost', f'{A["msg_cost"]} AMD', 'Assumption; marketing to confirm SMS / Viber prices']],
  [5.2, 3.3, 8.5])

H('5. Pilot and decision rules')
B('**Pilot:** 4 weeks of disbursements in about a quarter of the branches (selected with the branch network), with the 10% holdout inside the same branches.')
B('**Readout at D+30 of the last cohort:** take-up, qualification treated vs holdout, bonus cost, net P&L per targeted client using the measured uplift.')
B('**Scale** to all branches if net P&L per targeted client > 0 and the guardrails hold. **Iterate once** (bonus size, threshold, script) if the uplift is between 0 and break-even. **Stop** if it is negative after one iteration.')
B('**D+90 check:** does activity persist (purchases at D+60–90 vs holdout)? This updates the "months of margin" assumption.')

H('6. Risks and mitigations')
T([['Risk', 'Mitigation'],
   ['Gambling: gold-loan clients\' card spend is skewed to betting; loan money on a card makes betting easier', 'Gambling never counts toward the bonus; track the gambling share of spend as a guardrail; compliance to review responsible-lending wording'],
   ['Deadweight: clients who would be active anyway get the bonus', 'Target only clients with no active card; a low cap; the holdout measures it'],
   ['Client is worse off than with cash (ATM fees, queue)', 'Free cash-outs at FB ATMs and cash desks; staff can still pay cash on request'],
   ['Gaming the threshold with tiny purchases', 'Minimum total of 20,000 AMD across the 5 purchases; one bonus per client'],
   ['Branch execution varies', 'Short script, daily list with offer / no-offer flags, branch-level take-up in the weekly readout'],
   ['Bonus treated as a change of loan rate (disclosure)', 'Promotional bonus outside the loan contract; legal sign-off before launch'],
   ['Messages not delivered (Viber 36%)', 'SMS fallback; branch D0 contact is the main channel']],
  [6.5, 10.5])

H('7. Open questions for the bank')
N('Can the core system pay a gold loan onto a card account at the desk today, and is it instant?')
N('Actual gold-loan rates and average ticket in 2026; share of disbursements to clients with an active card.')
N('Fast Bank ATM coverage near gold-loan branches; can cash-out fees on the card be waived for 30 days?')
N('Legal form of the bonus (promotional bonus vs interest refund), terms and tax treatment.')
N('Who credits the bonuses (operations) and from which budget line (marketing vs loan product)?')
N('SMS and Viber price per message; consent coverage of gold-loan clients.')

doc.save(OUT)
print(OUT)
print(f'refund {refund:.0f}  NET/1000 {NET:,.0f}  per client {NET/1000:.0f}  BE {be_uplift*100:.2f}pp  worst {worst:.0f}  year {year_net/1e6:.1f}m  cards {year_cards:.0f}')
