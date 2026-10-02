# Thread 02: Fast Bank CVM / CRM initiative

**Read this file first in every session of this thread.**
- Last updated: 2 Oct 2026, the milestone before the fork.
- The sister thread is `../01_debit_cards_model_and_benchmark/CONTEXT.md` (debit cards model + market benchmark). Use it only when a campaign needs card economics (fees, cashback, FX, free-service conditions).


**Cross-thread sync:** after this file, read `../00_shared/SYNC.md` (dependencies with thread 01 and a dated log). Append there whenever a change here affects the other thread.

---

## 0. Who / what

- **Client:** Fast Bank CJSC, Armenia, in its "FB 2.0" 2026–28 transformation.
- **H21:**
  - Alex Suprunov owns CVM/CRM and this thread;
  - Andranik Konstantinidi works on cards and CVM;
  - Anton Savin is the project lead;
  - Ilya Kubar is the managing partner.
- **CRM stream:** sponsor Armine Ter-Hovsepyan, PO Tigran Hakobyan.
  - Scope: Creatio integrator selection plus the first 4–6 offer campaigns.
- **Start:** Alex started CVM on 30 Sep 2026, on team plan items:
  - 1.1: products to push before the Dec 2026 – Jan 2027 debit-card launch;
  - 1.2: triggers and offers, i.e. the quick-win campaigns.
- **Ambition:** top-5 bank in Armenia by retail clients by 2028 (236k in 2025 → 600k). Card MAU ~40% → 75%+.
- Programme background: memory `fast-bank-transformation.md`.

## 1. Files and where they live

| What | Location |
|---|---|
| **CVM deck, current = v4** (1 Oct 2026, cover dated 1 Oct) | `~/Downloads/20260930_FastBank_CVM_deck_v4.pptx` + `.pdf` |
| CVM deck v3: **Alex's edited version** with his order and stickies | `~/Downloads/20260930_FastBank_CVM_deck_v3.pptx` |
| Early draft | `~/Downloads/20260930_FastBank_CVM_deck_draft.pptx` |
| Talking notes (first take, 30 Sep) | `~/Downloads/20260930_FastBank_CVM_talking_notes.md` / `.docx` |
| Design base: the bank's debit slides design system (**never edit**) | `~/Downloads/debit_slides.pptx` |
| Fast Bank portfolio by product (Sep 2025) | `~/Downloads/Market profit pools Armenia v5.1.xlsx`, sheet "Bank model – main" |
| Current campaigns export (campaign manager) | `~/Downloads/campaigns-2026-09-15 (1).json`, `~/Downloads/Campaign Manager.html` |
| Card funnel data | `~/Downloads/card-funnel-database_v14.xlsx`, `~/Downloads/Funnel & transactions data_rev_AS.xlsx` |
| Card funnel artifact (Alex shared it as a source) | https://claude.ai/artifact/AjyWtZuryB3aiuqBD3fXnm |
| Bereke Bank premium CVM benchmark (H21 SteerCo) | `~/Downloads/20260819_SteerCo Premium_v7 sent slides 17-22.pdf` |
| Other H21 CVM references (Vbet / AI CVM, not Fast Bank) | `~/Downloads/SOW 2_AI CVM_Period 1 closure - v13 slides 6,24-29.pdf`, `Best-in-class campaign leaflets.pdf`, `Plans CVM B2C.pdf` |

### This folder (`02_cvm_crm/`)

- **`deck_build/`** (python-pptx):
  - `h.py`: helpers (`new_slide`, `tb`, `rect`, `chip`, `num`, `band`, `hline`, `vline`, `footnote`, `set_text`);
  - `build.py`: v1 (16 slides) on a copy of `debit_slides.pptx`;
  - `new_sections.py`: the v3 sections;
  - `build_v4.py`: edits Alex's v3 **in place on a copy**. It removes the stickies and applies his comments.
  - The scripts point at old scratchpad paths, so fix the paths before re-running.
- **`reference_slides/`:** 14 benchmark slides Alex shared:
  - 01–02: Kazakhstan bank segments and comms per client;
  - 03–04: MTS prioritisation matrices for cash loans and credit cards;
  - 05–08: Finalta CRM offer structure, Alfa channel loads, real-time vs batch, Monzo / Barclays triggers;
  - 09–14: McKinsey personal offers (selection logic, types, channels, in-app display), CVM tribe of 23 people, target IT architecture.

### Design system for decks

- Segoe UI. Colours:
  - magenta `EC008C`;
  - blue `2E41F3`;
  - navy `202A7D`;
  - panels `F1F1F7`.
- Section tags like "I. LONG-TERM PRIORITIES · 2. …" sit above the title.
- Build on a **copy** of `debit_slides.pptx`.
  - Preview with a PIL renderer: `../01_debit_cards_model_and_benchmark/debit_slides_build/render.py`.
  - Validate with the pptx skill's `validate.py`.
- Never automate PowerPoint or Keynote.
- Watch out for duplicate slide part names when copying slides (rename to `slideN.xml`).

---

## 2. Alex's deck rules (feedback, keep applying)

- **Length and order:**
  - 7–9 high-quality main slides; everything else goes to backup.
  - **Executive summary at the END**, not the start.
  - Keep Alex's step structure and slide order (he reorders in his own copy, so diff it).
- **Framing:**
  - "Our view", not "decisions to agree".
  - No days or timelines on plan slides (the path-forward "due" dates are marked "proposed").
  - Don't raise the active-client definition: keep today's contract definition.
- **Content:**
  - Every campaign needs its logic spelled out ("why").
  - Building blocks show **key questions + bank contact** (blank to fill in at the meeting), not "today / needed".
  - Channels: list **all** of them (SMS, e-mail, calls / telemarketing, WhatsApp, Viber, Telegram, push, branches), not only Viber.
- **Process:**
  - Alex leaves review notes as **"Sticky" shapes** on slides. Find them by diffing shapes against the previous build, apply them, then remove them.
  - Never edit Alex's file. Write a new version (`…_vN.pptx`) in `~/Downloads`.
- **Data rule** (management): no client names, tax IDs, account numbers, per-account balances or income data leave the bank. H21 sees counts and aggregates only; the bank BI builds lists.

---

## 3. Deck v4: slide by slide

### Main slides

1. **Cover:** "Fast Bank CVM: plan, first findings and path toward quick wins" (document for discussion, 1 Oct 2026).
2. **I. Long-term priorities (our view).** Four topics:
   1. product selection before the card launch: 3–4 focus products, one target metric each;
   2. triggers and offers: event-based backlog, launch now, scale what beats the holdout;
   3. infrastructure and operating model: building blocks, owners, team / hiring;
   4. segmentation (Finalta-style, reusable).

   Open questions: which data feeds Creatio first; global control vs campaign holdout; review today's debit card offers.
3. **I.2 Building blocks:** 9 blocks, each with key questions and a bank contact.
   - The blocks: target product, whom, target metric, action and reward, data, channels and fallback, content and design, when, impact tracking.
   - Enablers and owners:
     - project management: H21 with the CRM PO;
     - data sourcing: bank BI and compliance;
     - segment creation: CRM team with BI;
     - campaign flow: CRM PO and channel owners.
4. **IV.1 Funnel:** the funnel is healthy up to activation; the gap is usage.
   - Cohort Mar–Aug 2026: applied 24.0k → issued 24.0k (next day) → delivered 21.3k (89%) → activated 20.4k (85%; 96% within 90 days).
   - MAU ~40% vs a 75%+ target.
   - Transactions per card a month: 2.4 for all cards, 5.7 for active, 11.3 for high-activity.
   - So CVM should drive activity, ARPU and reactivation, not acquisition.
5. **IV.2 Base by product** (Sep 2025, flagged "needs update"):

   | Product | Clients | Portfolio | Note |
   |---|---|---|---|
   | Gold loans | 134k (57%) | 101bn | ~46k disbursements a month |
   | Debit cards | 46k (19%) | ~1bn balances | 84% of paid cards given free |
   | Term deposits | 15k | 124bn | 8.4m average; FB rate 10.0% vs 8.05% median |
   | Cash loans | 11k | 16.5bn | |
   | Mortgage | 5k | 73bn | |
   | Current accounts | – | 10.7bn | plan 33bn in 2026 |
   | Credit cards | <0.1k | | launching |

6. **II. Short term: wave 1 quick wins.** Five campaigns: why, whom, when / channel, action → reward, KPI vs holdout.
   1. **Gold-loan money to card.**
      - Whom: gold-loan clients without an active card (134k).
      - When / channel: at disbursement in the branch (~46k a month); branch next-best offer, SMS, WhatsApp.
      - Action → reward: take the loan onto an FB card → preferential gold-loan rate.
      - KPI: share of loans paid to a card; card balance at D+30.
   2. **Deposit maturity: prolong or upgrade.**
      - Whom: clients with a maturing term deposit (15k).
      - When / channel: 14 / 7 / 1 days before maturity; telemarketing for large tickets, SMS, WhatsApp, e-mail.
      - Action → reward: prolong, or move to savings / bonds → rate bonus.
      - KPI: retained share of maturing volume.
   3. **Free service on balance, not deposit.**
      - Today free service rests on a deposit; the new tariff conditions it on a minimum average card balance, with 30 days' notice.
      - Check which depositors keep free cards.
      - KPI: card balances; paid cards retained.
   4. **Dormant card reactivation.**
      - Whom: cards idle 60 / 90 days (~60% idle in a month).
      - Action → reward: make a purchase → one month of free ATM, transfers and preferential rates.
      - KPI: reactivated share at D+30.
   5. **7-day streak.**
      - Whom: cardholders with 1–4 purchases a month.
      - Action → reward: a purchase every day for 7 days → a fixed bonus (e.g. 1,000 AMD).
      - KPI: transactions per card; active days.

   Rules for all five:
   - holdout: 10% random per campaign plus a 5% global control;
   - success: beats the holdout at D+30, no t-test yet;
   - offers only with consent;
   - scale the winners, iterate once, stop the rest.
7. **V. Path forward** (due dates are proposed):

   | # | Step | Owner | Due |
   |---|---|---|---|
   | 0 | PRD per wave-1 campaign (building blocks → stages → one data request) | Alexey (H21) and the CRM PO | 9 Oct |
   | 1 | BI counts, no personal data: deposit maturities for the next 180 days (count and AMD by week and ticket band); issued-not-activated cards by age | Bank BI | 7 Oct |
   | 2 | Marketing consents and opt-outs | Compliance and the CRM team | 7 Oct |
   | 3 | Risk-model readiness for pre-approved limits on gold-loan clients | H21 risk stream | 14 Oct |
   | 4 | Current campaigns baseline: answer the questions, agree metrics, one calendar | CRM team | 7 Oct |
   | 5 | Contact list for the whole chain | CRM PO | 2 Oct |

8. **IV.3 Waves 2–3 (#6–12).**
   - **Wave 2** (Dec–Jan, with the new cards):
     - **#6 Welcome quest, first 30 days** (Bereke, Sber): tasks → prize-draw tickets, day-6 boost. Targets ~10k new cards a month plus the 3.7k issued but not activated.
     - **#7 Bring your money: 1% bonus** on inflows from other banks.
     - **#8 Pre-approved cash loan** for gold-loan clients (Finalta, Monzo).
     - **#9 FX offers for traveller look-alikes.**
   - **Wave 3** (2027, needs Creatio or the new app):
     - **#10 Salary-day / outflow moment** (80% of salary leaves via ATMs in the Kazakhstan case);
     - **#11 Autopay switch;**
     - **#12 Referral** (to test; 2,000 AMD to both vs 10–20k CAC).
9. **Backup divider.**
10. **Summary** (at the end). Six points:
    1. The base is gold-loan heavy.
    2. The funnel works; usage is the gap.
    3. Current campaigns are batch mailings and rarely measured.
    4. Data, triggers and measurement are the gaps.
    5. Wave 1 is five campaigns.
    6. The next two weeks.

### Backup

11. **Current campaigns baseline** (campaign manager, May–Aug 2026):
    - 4% on balances: Viber 24.6k targeted, 33.3% vs 33.1% holdout (+0.2 p.p.); e-mail 50.1k, +0.9 p.p. "Converted" = balance +1%, a loose metric.
    - Consumer loans: ≈0 uplift vs holdout (23 loans, 52m AMD). Bank-wide loan agreements rose 740 → 839 a month, but targeted clients did no better than the holdout.
    - Secured loans: 3 loans; calls 0 of 826.
    - Deposit and bond calls: 1.5k called, 2.7% conversion, 250m AMD sold (41 sales).
    - 2% cashback for new cards: 140k targeted, 0.14%, 202 cards.
    - Four promos with no results reported.
    - Only 2 of 6 completed sales campaigns had a holdout; Viber delivered 36%; e-mail clicks 0.3%.
    - Questions to the bank: why is Viber reach only 36%; is there one calendar and a contact cap; what drove the loan +13%.
12. **Segmentation as-is vs to-be** (Finalta-style).
    - As-is: one-off lists per campaign.
    - To-be: one value-based tree defined in BI, with axes product holding / behaviour / lifecycle / value. LTV decides who gets rich offers and costly channels.
13. **Prioritisation matrix:** value × time to launch (< 1 month / 1–3 months / 3+ months).
    - Wave 1 Oct–Nov: #1–5.
    - Wave 2 Dec–Jan: #6–9.
    - Wave 3 in 2027: #10–12.
14. **Campaign flow and owners:**
    - Steps and owners:
      1. idea: CRM PO, product owners, H21;
      2. PRD: CRM team with H21 (Alexey);
      3. segment: bank BI (H21 sees counts only);
      4. offer and content: product, marketing, compliance;
      5. launch: channel owners;
      6. measure: uplift at D+14 and D+30;
      7. decide: weekly CVM committee.
    - Enablers:
      - BI views refreshed weekly (daily for triggers);
      - 5% global control and a 10% holdout;
      - campaign-manager tracker now, Creatio later;
      - governance: weekly CVM committee → bi-weekly ops committee → monthly SteerCo.
15. **Longlist 1/2 (L1–L16):**
    - cards and payments: boosted first-month cashback, in-branch welcome, personal offers, monthly cashback choice, partner offers, bonus reminder, privileges page;
    - savings: welcome-rate savings and round-ups, salary → deposit rate, cross-sell to 66k past depositors, bond offers, RM hand-off, lottery deposit, flexible savings;
    - insurance: gadget, home, car.
16. **Longlist 2/2 (L17–L29):**
    - lending: top-up, overdraft, instalments, counter-offer, ghost product, car loan, credit-line stimulation;
    - FX and transfers: remittance receivers, special FX rate;
    - app: daily prize draw, monthly tasks, app tips, in-app offer showcase.

---

## 4. Key facts and benchmarks (don't re-derive)

- **Finalta:** event-triggered cash-loan offers convert at 3.7–4.8% vs 0.6–1.1% for batch, i.e. ×3–8.
- **Kazakhstan bank:** mono-product clients dominate the active base (336k of ~410k) and got only 3–4 communications per client in 4 months.
- **McKinsey personal offers:** ~400 variants tested; the best lifted fee income by 20%+.
- **Card funnel extract (15 Sep 2026):** 67.5k registrations. A card counts at a stage if it reached that stage or a later one.
- **Card side** (from thread 01):
  - FB has no cashback today;
  - 84% of paid cards were given free;
  - FB has the top deposit rate in the market;
  - the new tiers Free / Black / Premium / Elite launch Dec–Jan;
  - cashback = a monthly choice of categories.

## 4b. Agreements with the bank (meeting with Tigran Hakobyan, CRM PO, 1–2 Oct 2026)

Alex sent deck v4 (PDF) after the meeting along with these agreements:

1. Tigran sets up a meeting with Zhanna (marketing).
2. H21 designs the target marketing process from idea to launch, including SLAs and resources. Goal: when CRM is integrated, marketing launches 10–20 campaigns a month, up from 2–3.
3. Map today's approval chain and design the target one.
4. A permanent (global) control group to measure effect.
5. Tigran adds H21 to the Creatio demo and working group.
6. Tigran sends the WhatsApp integration request (and any answer).
7. Data from Tigran: (a) updateable sources; (b) his static datasets.
8. H21 proposes how to track conversions from push (UTM tags in Firebase).
9. **PRDs with effect rationale for campaigns 1, 3, 4, 5.** Wave-1 #2 (deposit maturity) is not in this list.
10. Tigran reviews slide 8 (waves 2–3) for anything else to prioritise.

**Tigran's main concern:** prove that each campaign does not lose the bank money.
**Plan:** PRDs first, starting with #1 gold-loan money to card. Then short executive summaries of the PRDs for **SteerCo approval on Wed 7 Oct 2026**.

### Gold-loan facts gathered for PRD #1 (2 Oct 2026)

**Gold-loan book** (profit pools v5.1, 'Bank model - main' rows 161–169, 57):
- Portfolio: 100.8bn AMD in Sep-25, 115bn in 2025.
- Sales in 2025: 347bn AMD across 588k loans. Average ticket about 0.58–0.61m AMD.
- Repayment is about 3× the average portfolio, so a loan lives about 4 months. That is about 4.4 loans per client a year.
- 134k clients.
- Gold-loan net interest income: 8.4bn in 2024 and 10.1bn in 2025, a net margin of about 13% / 11% on the average portfolio.

**Gold-loan cards** (model v19.1 'Cards dataset', 'Card sub-segment' = Gold loan):
- 54,286 of the 96,906 cards issued Jan–Aug 2026 (56%), about 6.8k a month; 84% are ArCa.
- Only 39% were active in Jun–Aug, against 58% of other cards.

| Per card a month | Gold-loan cards | Other cards |
|---|---|---|
| Card balance | 2.0k AMD (median 0) | 15.8k |
| Inflow | 55k | 99k |
| Non-cash | 23k | 43k |
| Cashout | 12k | 20k |
| Debit transactions | 1.7 | 3.3 |
| Share holding a deposit | 1.2% | 22% |

- Active gold-loan cards only: inflow 139k, non-cash 58k, cashout 30k, C2C 25k, balance 5.1k, 4.2 transactions a month.
- From the cards thread: gold-loan holders' card spend is mostly gambling (one example is in the cards CONTEXT eligible-share section).

### Meeting notes (Alex, 1 Oct 2026)

- **Marketing.** Throughput is 2–3 campaigns a month. Start pushing now and prepare the process with Zhanna, head of marketing. Content and design stay with marketing for now.
- **Process.** Review the approval chain. Make one universal control group; the old per-campaign controls were odd. There is effectively no effect measurement today.
- **Data.** BI contact is Grigoriy Arutyunyan. Tigran sends the subset he has collected.
- **Channels.** Today: SMS, Viber, push, e-mail, telemarketing. WhatsApp / Telegram are to be added; Nikita (mobile) has been asked.
- **No real-time triggers before Creatio** (Tigran). Creatio will aggregate by day and by MCC category.
- **Push tracking.** Firebase gives no push conversions, so use UTM tags.
- **App.** Lead clients from "make a card" into "connect the app".
- **Deposits.** Prolongation already exists, but only via telemarketing; add channels. The base goes stale, so this is more of a CRM topic (regulation).
- **Campaigns.** Ideas 1, 3, 4 and 5 are fine; #3 is top. Cashback is one of the promo mechanisms.

## 4c. PRDs

| # | Campaign | Status | Files |
|---|---|---|---|
| 1 | Gold-loan money to card | v1 draft, 2 Oct 2026 | `~/Downloads/20261002_FastBank_CVM_PRD_01_GoldLoan_to_card_v1.docx`; generator `prd_build/prd_01_gold_loan.py` (economics computed in the script; edit the dict `A` and rebuild) |

**Alex's PRD decisions (2 Oct 2026):**
- Format: Word (.docx), English, built with python-docx because node is not installed.
- Render check: Word AppleScript "save as PDF" on a `_render` copy, then PyMuPDF to PNG.
- Structure:
  - exec summary box (reusable for SteerCo);
  - why;
  - the 9 building blocks table;
  - detailed design (terms, segment, holdout, owners, data, channels, messages, journey);
  - economics (base case per 1,000 targeted clients, sensitivity, upside, assumptions);
  - pilot and decision rules;
  - risks;
  - open questions.
- PRD #1 offer mechanics:
  - today the bank issues a card but pays the loan in cash;
  - the offer: loan onto the card, then a conditional interest refund (25% of first-month interest, cap 3,000 AMD) for 5+ eligible purchases (≥20k AMD total) in 30 days;
  - free cash-out at FB ATMs.
- Proof = the offer's overall P&L: card P&L gained minus the interest given up, which must be well above 0.

**PRD #1 base case:**
- Net is +459 AMD per targeted client (2.1× benefit / cost); break-even uplift is +0.8 p.p.; with zero uplift the result is −40 AMD per client.
- At 100k targeted clients a year: about 41m AMD and about 9k extra active cards.
- Key inputs:
  - active gold-loan card margin 1,237 AMD a month (model v19.1 Cards dataset; 13.5% of gold-loan cards make 5+ purchases);
  - gold-loan rate 19.5% (market);
  - ticket 600k AMD.

## 5. Next steps / open items

- **PRDs for #1, #3, #4, #5** (agreed with Tigran; #1 v1 done 2 Oct), then 1-page exec summaries for SteerCo **Wed 7 Oct**. Each PRD covers: trigger, segment logic (BI-side SQL), offer, channel, holdout, KPI, data request. Alex owns these with the CRM PO.
- **Size each campaign** (pool × conversion × value per conversion) once the BI counts arrive.
- **Fill in the bank contacts** on the building-blocks slide after the meeting.
- **Get the answers:** consents and opt-outs, channel costs and limits, the Viber delivery issue, risk-model readiness.
- **Map the campaigns to the Creatio roadmap**, once the integrator is chosen.
- **Align with the card thread:**
  - campaign #3 (free service on balance) depends on the new tariff's waiver rules;
  - campaign #9 (FX) depends on FX pricing (thread 01 FX margin lever).
- **Update** the base-by-product slide with fresh data (it is Sep 2025).

## 6. Memory links

- `cvm-stream.md`: short memory pointer for this stream.
- `fast-bank-transformation.md`: programme, people, targets.
