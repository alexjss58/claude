# Cross-thread sync: 01 cards model ↔ 02 CVM/CRM

Both threads read this file at the start of each session, after their own CONTEXT.md.

**Sync rule**
- When a change in one thread affects the other, append a dated entry to the log at the bottom. Examples: a new model version, a tariff or fee decision, cashback parameters, a new deck version, a new campaign or data finding.
- Also update the dependency table if a link changes.
- Keep entries short and point to the file or cell. Don't copy content that lives in a CONTEXT.md.
- Each thread edits only its own CONTEXT.md and picks up the other thread's news from here.

---

## Dependencies between the threads

| CVM item (02) | Card model / benchmark item (01) | What must stay consistent |
|---|---|---|
| Wave 1 #3 "Free service on balance, not deposit" | Service fee and paid-card share per tier (Control panel b+8 / b+20); Bank PnL paid shares AX117:AY120; service fee gap 1.02 vs 0.20bn (2027) | The waiver condition (minimum card balance) and the share of clients paying the fee. The campaign is the lever behind the model's paid share. |
| Wave 1 #1 "Gold-loan money to card" | Eligible-spend shares exclude gold-loan clients; their card spend is mostly gambling | Pulling gold-loan clients onto cards raises card balances and MAU, but cashback must stay eligible-only (gambling excluded). Otherwise the cashback cost jumps. |
| Wave 1 #2 "Deposit maturity: prolong or upgrade" | Deposit uplift lever (b+15) and deposit margin 1.25 p.p. | Any rate bonus offered must be priced the same way as the model's deposit uplift. |
| Wave 1 #4 dormant reactivation; #5 7-day streak; MAU 40% → 75% | Profile mode 2 "active users" = a transaction in Jun–Aug 2026; transactions per card | Use one definition of "active card" in both threads. The model's mode 2 assumes activity levels that the CVM campaigns have to deliver. |
| Wave 2 #6 welcome quest; longlist L1 / L4 / L5 / L6 (cashback ideas) | Cashback engine (menu 7 + 2, pick 4, caps); playbook artifact; targets Black 1.9% / Premium 2.6% / Elite 2.1% of eligible spend | Welcome boosts and cashback offers sit inside the cashback budget, or get budgeted separately in the model (one-off marketing line). |
| Wave 2 #9 FX offers for travellers; L25 | FX margin vs CBA lever (Control panel b+9; FB today 0.79%, market median 1.04%); AMD-only new cards | A preferential FX rate = a lower FX margin parameter. If cards are AMD-only, FX offers run on accounts / in the app. |
| Wave 2 #7 "Bring your money: 1% bonus" | Card balances × FTP 11.1% (8 cards model D90) | The bonus cost has to stay below the FTP income on the extra balances. |
| Wave 3 #12 referral (2,000 AMD to both) | CAC / one-off marketing per card | Compare with the model's marketing CAC. |
| Timing: waves 2–3 | New card lineup launch Dec 2026 – Jan 2027 | Wave 2 starts with the new cards. |
| Data rule | Same management rule | No names, tax IDs, account numbers, per-account balances or income. Aggregates only. |

---

## Log (newest at the bottom)

- **2 Oct 2026, fork.**
  - Cards model at v19.1. Current tiers:
    - Free = Visa Digital + ArCa;
    - Black = Visa Classic + Gold, 5k AMD / yr;
    - Premium = MC World, 20k;
    - Elite = MCWE / Infinite / Metal, 100k.
  - Dashboard at v13.
  - CVM deck at v4, with wave 1 = #1–5.
  - Open on the card side that matters for CVM: the waiver rules for paid tiers, and ArCa Pay / SBP pricing after 31 Dec.
- **2 Oct 2026, cards thread: Alex's edits found in v18, not yet in v19.1.**
  - Black cashback target 1.9% → 2.2%; Premium 2.6% → 3.0% (% of eligible spend).
  - Deposit uplift: Black −0.25 p.p., Premium −0.10 p.p. A negative uplift means a lower rate for those cardholders' deposits.
  - Baseline deposit rate fixed at 10.25%.
  - These go into the next model version.
  - Relevance to CVM: wave 1 #2 (deposit maturity rate bonus) should be priced against a 10.25% baseline. Cashback budgets for wave 2 #6 and the longlist go up.
- **2 Oct 2026, CVM thread: PRD #1 gold-loan money to card uses card-model data.**
  - Margin of an active gold-loan card: 1,237 AMD a month (5+ purchases a month). Idle card: about 14 AMD.
  - Source: v19.1 'Cards dataset' 'Card sub-segment' = Gold loan, with the model's fee, interchange, FTP 11.1% and 4% card-rate assumptions.
  - 54k gold-loan cards were issued Jan–Aug 2026 (56% of new cards, 84% ArCa); only 13.5% make 5+ purchases a month.
  - If the cards thread changes fees, FTP or the card balance rate, tell the CVM thread so the PRD economics can be rebuilt (`02_cvm_crm/prd_build/prd_01_gold_loan.py`).
  - The campaign also assumes free cash-out at FB ATMs for 30 days for participants.
