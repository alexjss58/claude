from pptx import Presentation
p = Presentation('user_v3.pptx')
S = list(p.slides)


def title(s):
    t = [sh for sh in s.shapes if sh.name == 'Title 3']
    return t[0].text_frame.text if t else ''


def runs_set(sh, paras):
    """paras: list of lists of run texts; keeps the existing run formatting position by position."""
    tf = sh.text_frame
    ps = tf.paragraphs
    for i, texts in enumerate(paras):
        rs = ps[i].runs
        assert len(rs) >= len(texts), (sh.name, tf.text, texts)
        for r, tx in zip(rs, texts):
            r.text = tx
        for r in rs[len(texts):]:
            r._r.getparent().remove(r._r)


def find(s, name, top=None, contains=None):
    for sh in s.shapes:
        if sh.name == name and (top is None or sh.top == top) and (contains is None or contains in sh.text_frame.text):
            return sh
    raise KeyError((title(s)[:30], name, top, contains))


# remove review stickies
for s in S:
    for sh in list(s.shapes):
        if sh.name == 'Sticky':
            sh._element.getparent().remove(sh._element)

# slide 2: typo
sh = find(S[1], 'Topic', contains='Triggers and offers')
for r in sh.text_frame.paragraphs[0].runs:
    r.text = r.text.replace('offers:quick', 'offers: quick')

# slide 3: building blocks = key questions + bank contact
s = S[2]
assert title(s).startswith('Building blocks')
find(s, 'Title 3').text_frame.paragraphs[0].runs[0].text = 'Building blocks toward launching any campaign: what each block covers and who at the bank can help'
for r in find(s, 'Title 3').text_frame.paragraphs[0].runs[1:]:
    r._r.getparent().remove(r._r)
Q = ['Which products and levers first? Which P&L metric must move?',
     'Largest pool or a high-LTV sub-segment? Which exclusions (risk, opt-outs)?',
     'One primary metric per campaign? Per client, in AMD, against the holdout?',
     'What must the client do, which MCCs count, what reward and cap?',
     'Which BI tables and fields? How often refreshed? Consent flags?',
     'Live channels and cost per contact: SMS, e-mail, calls, WhatsApp, Viber, Telegram, push?',
     'Who writes and designs? Legal sign-off? Which variants to A/B test?',
     'Event trigger¹ or whole segment? Which day and time? Frequency cap?',
     'Holdout size, readout dates, who reports the results?']
todays = sorted([sh for sh in s.shapes if sh.name == 'Today'], key=lambda x: (x.top, x.left))
neededs = sorted([sh for sh in s.shapes if sh.name == 'Needed'], key=lambda x: (x.top, x.left))
assert len(todays) == 9 and len(neededs) == 9
for sh, q in zip(todays, Q):
    runs_set(sh, [['Key questions: ', q]])
    sh.name = 'Key questions'
for sh in neededs:
    runs_set(sh, [['Bank contact: ', '______________________ (to fill in at the meeting)']])
    sh.name = 'Bank contact'

# slide 6: wave 1 – #3 = free-service condition, all channels
s = S[5]
assert title(s).startswith('Short term')
row = {sh.top for sh in s.shapes if sh.name == 'Campaign'}
tops = sorted(row)
t3 = tops[2]
runs_set(find(s, 'Campaign', t3), [['Free service: from deposit to balance condition'],
                                   ['Free service now rests on holding a deposit; a card-balance condition keeps money on the card and fits the new cards']])
runs_set(find(s, 'Whom', t3), [['Cardholders with free service via a deposit today, and paid-card holders']])
runs_set(find(s, 'When', t3), [['New tariff; notice 30 days before the change'], ['SMS, e-mail, WhatsApp, Telegram, push']])
runs_set(find(s, 'Action', t3), [['Keep a minimum average card balance → free service (check which depositors keep free cards)']])
runs_set(find(s, 'KPI', t3), [['Card balances; paid cards retained']])
CH = {0: 'Branch next-best offer; SMS, WhatsApp', 1: 'Telemarketing for large tickets; SMS, WhatsApp, e-mail',
      3: 'SMS, WhatsApp, Telegram, e-mail; telemarketing for high value', 4: 'Push, WhatsApp, Telegram, SMS'}
for k, ch in CH.items():
    w = find(s, 'When', tops[k])
    runs_set(w, [[w.text_frame.paragraphs[0].runs[0].text], [ch]])
rule = find(s, 'Rule', contains='Consent')
runs_set(rule, [['Channels'], ['all live channels – SMS, e-mail, telemarketing, WhatsApp, Viber, Telegram; offers only with consent']])

# slide 8: waves 2-3 – #6 becomes the welcome quest; channels beyond Viber
s = S[7]
assert title(s).startswith('Beyond wave 1')
t6 = min(sh.top for sh in s.shapes if sh.name == 'Campaign')
runs_set(find(s, 'Campaign', t6), [['Welcome quest, first 30 days'], ['Benchmark: Bereke; Sber']])
runs_set(find(s, 'Whom', t6), [['New cardholders, days 0–30 (~10k cards a month); 3.7k issued cards not activated']])
runs_set(find(s, 'When (trigger)', t6), [['Card issued; no purchase by day 7']])
runs_set(find(s, 'Client action → reward', t6), [['Tasks: first purchase, Apple / Google Pay, transfer → prize-draw tickets; day-6 boost']])
runs_set(find(s, 'Channel', t6), [['Push, SMS, WhatsApp; call on day 7']])
runs_set(find(s, 'KPI vs holdout', t6), [['Activated in 14 days; 5+ purchases in 30 days']])
for sh in s.shapes:
    if sh.name == 'Channel':
        for r in sh.text_frame.paragraphs[0].runs:
            r.text = r.text.replace('Viber, e-mail, app', 'WhatsApp, e-mail, app').replace('Push, Viber, e-mail', 'Push, WhatsApp, e-mail').replace('App, Viber', 'App, WhatsApp, Telegram')

# summary: wave-1 list
for s in S:
    for sh in s.shapes:
        if sh.has_text_frame:
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    r.text = (r.text.replace('Gold-loan money to card, deposit maturity, welcome and activation push, dormant reactivation and a 7-day streak',
                                             'Gold-loan money to card, deposit maturity, free service on a balance instead of a deposit, dormant reactivation and a 7-day streak')
                              .replace('(page 8)', '(page 11)')
                              .replace('BI, channel owners (Viber, SMS, e-mail, call centre)', 'BI, channel owners (SMS, e-mail, telemarketing, WhatsApp, Viber, Telegram)')
                              .replace('Channel owners: Viber, SMS, e-mail, call centre, branches', 'Channel owners: SMS, e-mail, telemarketing, WhatsApp, Viber, Telegram, branches')
                              .replace('V. PATH FORWARD · CURRENT CAMPAIGNS', 'BACKUP · CURRENT CAMPAIGNS'))

# backup prioritisation: #3 and #6 swap names (wave 1 / wave 2)
s = next(x for x in S if title(x).startswith('Prioritisation'))
for sh in s.shapes:
    if sh.name == 'Legend':
        r = sh.text_frame.paragraphs[0].runs[0]
        if r.text == 'Welcome and activation push':
            r.text = 'Free service on balance, not deposit'
        elif r.text == 'Balance-based free service':
            r.text = 'Welcome quest, first 30 days'
p.save('cvm_v4.pptx')
print('saved')