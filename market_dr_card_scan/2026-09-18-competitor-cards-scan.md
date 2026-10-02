# Competitor debit card scan — six Armenian banks (2026-09-18)

Full sweep of every debit card published for individuals by IDBank, Ameriabank, Evocabank,
FastBank, Ardshinbank and Conversebank. Read off the live product pages and published tariffs in
Armenian, Russian and English on 2026-09-18. **Supersedes `competitor-tariffs-2026-02.md`**, which
was transcribed from S4 slide 18 and carried an unverified Ameria attribution.

- **Dataset:** `data/2026-09-18-competitor-cards.csv` (104 rows, 47 columns) and
  `data/2026-09-18-competitor-cards.json` (full records with verbatim quotes, gaps, per-card sources).
- **Dashboard:** `2026-09-18-competitor-cards-dashboard.html` (local copy; also published as a
  Claude artifact, "Armenian Debit Card Field Map").
- **Method:** one fixed field schema per card; figures quoted from the product page, falling back to
  the bank's published tariff where the product page was silent. Nothing inferred — an unpublished
  field is empty and listed under `gaps` on the record. Six contradictions were re-opened in a
  second pass and settled (section 6).

Coverage: **104 cards**, of which **100 are in the debit comparison** (4 held out: IDBank's Visa
Wizz Air, which is a credit card, and three gift/prepaid cards). Per bank — Ardshinbank 28,
Ameriabank 22, Conversebank 16, Evocabank 15, IDBank 15, FastBank 8.

---

## 1. The headline: selectable cashback categories do not exist in Armenia

**0 of 100 cards** let the holder choose their own cashback categories. This was the deck's proposed
differentiator (S4 slide 16, Feb 2026) and `claims.md` flagged it "re-verify before relying on it —
seven months old and the easiest claim for a competitor to invalidate."

It survives. The falsification attempt searched Armenian, Russian and English across all six banks
plus Acba, Inecobank, Unibank, AMIO, Araratbank, Armeconombank, ArmSwissBank, Idram and Telcell.
Every mechanic found is one of: flat rate, issuer-fixed categories, a fixed cash amount, a merchant
promo, or the national ArCa 2%. **The white space is real as of 2026-09-18** — and it is the one
claim in this project that a competitor could erase with a single product release, so it carries an
as-of date, not a permanent status.

## 2. Cashback in Armenia is mostly not the bank's money

| | Cards |
|---|---|
| Bank-funded cashback | **8** — at **2 of 6 banks** (IDBank 4, Evocabank 4) |
| National ArCa 2% (1% Armenian Card + 1% RA state budget) | 10 |
| Promo / campaign only | 11 |
| Partner-only (merchant discounts, no issuer cashback) | 6 |
| No cashback at all | 65 |

The "2% cashback" that every Armenian bank advertises is the **national ArCa scheme**, not a
competitive offer: 2% on domestic non-cash payments, minimum transaction 1,000 AMD, capped at
6,000 AMD per transaction and 60,000 AMD per month, and it attaches to any ArCa-branded card
regardless of issuer. It is ArCa-only — Visa and Mastercard products are structurally excluded.
Ardshinbank's own tariff table leaves its "Cash-back" row empty for exactly this reason: the money
is not the bank's (see V1).

Bank-funded cashback, where it exists, is thin:

- **IDBank** — 0.5% flat on Visa Signature / Infinite / Infinite Special Edition (the *most expensive*
  cards carry the *lowest* rate); Travel Card 1.5% on travel categories, 0.5% on other foreign spend.
- **Evocabank** — Visa Vision and Visa Digital 0.25% local / 0.5% abroad, 5,000 AMD monthly cap;
  Travel Card 1.5% on foreign hotels/air/travel agencies/car hire/rail, 0.5% other foreign,
  20,000 AMD cap; Visa Infinite on the same pattern.

**Implication.** A bank-funded, selectable-category cashback on a Visa or Mastercard product would
be a market first in two ways at once — selectable, and not ArCa-dependent. It would also be the
only mechanic in the market the bank pays for itself, which is where the economics get real.

## 3. The market competes on the balance, not the spend

**48 of 100 cards pay interest on the AMD balance.** Highest published rate per bank:

| Bank | Best AMD rate | Where | Cards paying interest |
|---|---|---|---|
| **FastBank** | **4.0%** | current-account tariff, all cards | 8 of 8 |
| Evocabank | 4.0% | Visa Vision, Visa Digital (no balance threshold) | 9 of 15 |
| Conversebank | 4.0% | Student Card; 4–4.25% inside a C360 package | 2 of 15 |
| Ameriabank | 3.0% | student cards only | 2 of 21 |
| Ardshinbank | 3.0% | Visa Gold and above, from a 5m AMD balance | 27 of 28 |
| IDBank | — | none | 0 of 13 |

Two things follow. **First, FastBank's 4% is already the joint-best rate in the market** and it is
paid on every card without a balance threshold — which Evocabank matches on two cards and
Ardshinbank gates behind 5,000,000 AMD. The deck proposes replacing this perk with cashback
(S4 slides 25–27); that trade is giving up the bank's only market-leading position, and the
economics should price what it buys. **Second, Ardshinbank has made balance interest its whole
proposition** — 27 of 28 cards, stepping 2.0% → 3.0% at the Gold tier, with fees waived on average
daily balance. It is the clearest rival architecture to anything spend-based.

## 4. Pricing: FastBank's premium tiers are far below market

Annual service fees across the field run from free to 150,000 AMD. Comparable tiers:

| Tier | FastBank | IDBank | Ameriabank | Ardshinbank | Evocabank | Conversebank |
|---|---|---|---|---|---|---|
| Classic / Standard | 2,000 | 3,000 | 5,000 | 4,800 | 5,000 | 3,000 |
| Gold | 4,000 | 8,000–12,000 | 20,000 | 24,000 | 15,000 | 15,000 |
| World / Platinum | 12,000 | 20,000 | 30,000 * | 36,000 | 30,000 | — |
| Signature / Black | — | 69,900 | 60,000 * | 96,000 | — | — |
| Infinite / World Elite | 50,000 | 99,900 | — | 120,000 | 100,000 | — |
| Metal / top | 150,000 | 150,000 | — | — | 300,000 (one-off) | — |

(Monthly fees normalised ×12: Ardshinbank publishes per month; Evocabank's Visa Vision is 600 AMD/month.
\* **Ameriabank's Platinum and Signature fees are disputed.** Two reads of the same tariff PDF — the only
source, since the product pages are JS-rendered — disagree: 30,000 / 60,000 on one reading, 60,000 / 40,000
on the other. Both are recorded on the card records; confirm with the bank before using either.)

**FastBank's Visa Infinite at 50,000 AMD/year sits at roughly 40% of Ardshinbank's and half of
IDBank's.** Either the new tiers have room to price up, or the cheapness is itself the positioning
and should be stated as such. Note also that FastBank's tariffs barely differentiate by tier —
ATM (0.50% own / 1.20% other RA / 2% abroad), card-to-card 0.5% and cash-in 0.80% are identical from
Visa Classic to Infinite Metal. The only things that move across the whole range are the annual fee,
the reissue fee and free SMS.

## 5. Fee waivers are the market standard; the S2 draft has none

**68 of 100 cards publish a fee-waiver condition** and 17 carry no fee at all. The dominant
mechanic is an **average daily balance** threshold, sometimes paired with spend:

- **Ardshinbank** — 60,000 AMD (ArCa) / 100,000 (classic) / 200,000 (Gold, Platinum, World) /
  500,000 (Signature, Black Edition); a 1,000,000 AMD term deposit or a bond purchase waives year one.
- **IDBank** — package-based: IDROCKET at 50,000 avg balance or 100,000 spend; VISAGOLD at
  150,000 / 300,000.
- **Conversebank** — 2,000,000 AMD average daily balance waives any C360 package.
- **Ameriabank** — waivers come from the Premium / Partner packages (40m / 120m average balances);
  ordering in MyAmeria halves the fee, and digital variants cost roughly half the plastic.
- **FastBank** — waives on a deposit ladder only (500k–5m → Classic; 5–20m → Gold; 20–50m → World;
  50m+ → Infinite / World Elite).

The bank's own S2 draft for the three new tiers has **no waiver at all** ("–" on every tier). Every
premium tier in the international benchmark set waives its fee on a balance or spend condition, and
now the domestic set does too. This is the sharpest remaining divergence between the draft and the
market, and it is an open question, not a settled design.

## 6. Perks: scheme-funded, spend-gated, and cheap to match

- **Lounge access** — 21 of 100 cards, all of it Visa Airport Companion / DragonPass or LoungeKey,
  not bank-funded. Ardshinbank: Platinum 1 visit/yr, Signature 4, Infinite 6, unlimited above
  $400 of non-cash spend over 12 months. Ameriabank gates the first visit behind $400 of spend in
  the preceding 35 days. **FastBank's premium benefits documents are robots-blocked**, so its own
  lounge, insurance and concierge terms are unread — a gap, not a finding (section 7).
- **Insurance** — widespread but shallow: Ameriabank attaches free card-transaction insurance to
  20 of 21 cards; Ardshinbank to 15 of 28. Bank-funded travel insurance and Priority Pass were
  withdrawn at Ameriabank in 2023.
- **Preferential FX** — **only 5 of 100 cards publish one.** Evocabank's Travel Card is the clearest
  (0.5 dram margin on USD/EUR up to ~5m AMD equivalent). Nobody advertises FX as a headline perk,
  which means it is neither a threat nor, on current evidence, a proven draw.
- **Loyalty points** — near-universal and near-worthless as money. IDBank's idcoin is the strongest
  (1 idcoin = 1 AMD, redeemable via Idram QR) but the whole balance is cancelled if no idcoin payment
  is made within 365 days. Converse Points "have no monetary expression and can never be exchanged
  for money" — redeemable only for physical gifts via a branch coupon valid 3 days.
- **Airline co-brand** — exactly one in the market: **IDBank's Visa Wizz Air**, launched 15 Sep 2026,
  and it is a **credit** card. 3% on Wizz Air, 1.5% on selected categories, 1% elsewhere, capped
  20,000 AMD/month, paid into the holder's Wizz Account wallet as airline scrip rather than cash,
  plus a EUR 20 welcome credit and free Wizz Discount Club membership. No other Armenian bank runs
  an airline or travel carrier partnership.
- **Referral and gamification** — almost absent. 2 cards publish a referral bonus.

## 7. Contested points, resolved

| | Question | Verdict | Confidence |
|---|---|---|---|
| V1 | Does Ardshinbank's ArCa card carry the national 2%? | **Yes** — its own Armenian page carries the scheme section with the national caps; the empty "Cash-back" tariff row is about bank-funded cashback. Initial scan was a false negative. | high |
| V2 | IDBank Visa Signature annual fee: 69,900 or 69,000? | **69,900 AMD** — Armenian page and the official Debit Cards Information Bulletin agree; the English tariff tab contradicts its own page. | high |
| V3 | Ameriabank "ArCa Pension" cashback | **Name unsettled.** The in-force tariff lists the row as ArCa Pension; a follow-up finds the marketed product named "Ameria Pension Card" and could not confirm an ArCa-branded pension card. Record kept at low confidence. | medium |
| V4 | FastBank balance interest: 4% or 5%? | **4% nominal / 4.07% APY**, per the bank-account tariff updated 09.07.2026. The "5%" survives only in a stale article title whose own body says 4%. The 10.25% is a 367–550 day term deposit. | high |
| V5 | Does anyone offer selectable cashback categories? | **No.** Three languages, sixteen institutions, two independent market surveys. | medium |
| V6 | Is IDBank's Visa Wizz Air in scope? | **No — it is a credit card.** Kept in the register as the market's only airline co-brand, excluded from every debit aggregate. | medium |

## 8. Known gaps

- **FastBank's own premium benefits documents are unread** — `/api/assets/` PDFs are robots-blocked.
  Lounge, insurance, concierge, supplementary-card fees, minimum balances, transfer tariffs and any
  FX markup are null for Visa Gold, Mastercard World, Visa Infinite, World Elite and Infinite Metal.
  These exist internally; pull them from the bank rather than the website.
- **Ameriabank's product pages are JS-rendered** and return only meta descriptions, so nearly every
  Ameriabank figure comes from the tariff PDFs, whose 20-header/14-column table was reconstructed.
  Most Ameriabank records are medium confidence; Signature is low (LoungeKey sheet says 4 visits/year,
  the current announcement says 10).
- **Conversebank** `/cards/`, blog and news pages are JS-rendered; `benefits.conversebank.am` partly
  blocked. Payroll Group 1 fees and Visa Virtual terms are published differently on two URLs — both
  recorded verbatim, confidence low.
- **Ardshinbank's Status | Plus loyalty programme** (`statusplus.ardshinbank.am`) is JS-only and
  unverified on every card.
- **Ameriabank's Platinum and Signature annual fees are disputed between two reads of the same tariff PDF**
  (30,000 / 60,000 vs 60,000 / 40,000). Neither reading is preferred; the records carry both at low
  confidence. This is a symptom of the JS-rendering problem above, not a separate issue.
- Card validity periods, reissue and closing fees are simply not published by most banks.

## 9. What this changes for the three new tiers

1. **The selectable-category differentiator holds** — re-verified, with an as-of date. It is the one
   mechanic in the design that nobody in the market has, and the only one that is both bank-funded
   and defensible for as long as it takes a competitor to copy it.
2. **Cashback and balance interest are alternatives, not a sequence.** The deck's plan to replace
   the 5% (in fact 4%) balance rate with cashback trades away FastBank's only market-leading
   position. The economics should price that trade explicitly, not assume it.
3. **Add a fee waiver to the tier design.** Every domestic competitor and every international
   benchmark has one; the S2 draft has none. Average daily balance is the domestic convention,
   sometimes paired with monthly spend.
4. **Premium pricing has headroom** — FastBank's Infinite is ~40% of Ardshinbank's equivalent.
5. **Do not spend design budget on lounges, insurance or concierge.** They are scheme-funded,
   spend-gated and identical across the field; matching them is cheap and differentiates nothing.
6. **Preferential FX is unproven either way.** Five cards in the whole market publish one, so there
   is no competitor to beat and no evidence of demand — it belongs in customer discovery, not in the
   tier spec, until someone tests it.

---

*Scan run 2026-09-18. Figures move; every record carries its own confidence level and source URLs.
Re-verify anything marked low confidence before it enters a pricing decision.*
