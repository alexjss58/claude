# Thread 01: Debit cards model + Armenia debit card benchmark

**Read this file first in every session of this thread.**
- Last updated: 2 Oct 2026, the milestone before the fork.
- The sister thread is `../02_cvm_crm/CONTEXT.md` (CVM / CRM). Don't mix the two.


**Cross-thread sync:** after this file, read `../00_shared/SYNC.md` (dependencies with thread 02 and a dated log). Append there whenever a change here affects the other thread.

---

## 0. Who / what

- **Client:** Fast Bank CJSC, Armenia.
  - It is a retail bank (formerly Fast Credit) and has had a licence since Nov 2022.
  - Same founders as SoftConstruct.
- **Programme:** "FB 2.0", the 2026–28 transformation.
- **H21:**
  - Alex Suprunov ("Aleksei | H21") owns the cards model, the CVM work and this thread.
  - Andranik Konstantinidi works on cards and CVM.
  - Anton Savin is the project lead.
- **Debit card stream:**
  - Bank sponsor Tigran Sargsyan; PO Ani Arshakyan; PM Avetik Shahbazyan.
  - Targets: 195k activated cards in 2026 and 470k in 2028; MAU ~40% → 75%+.
  - Launch of the new card lineup: Dec 2026 – Jan 2027.
- **Product idea:** 4 tiers (Free / Black / Premium / Elite).
  - T-Bank-style chosen-category cashback, paid monthly in AMD with caps.
  - Paid tiers carry a service fee and perks.
  - Card profitability rests on balances (NII / FTP), FX and fees, because cashback runs above interchange.
- The full background is in the memory file `fast-bank-transformation.md`.

## 1. Deliverables in this thread and where they live

| Deliverable | Current version | Location |
|---|---|---|
| **Debit cards financial model (Excel)** | **v19.1** (1 Oct 2026) | OneDrive: `~/Library/CloudStorage/OneDrive-HorizonTwentyOneFZCO/Shortcuts/Softconstruct - Documents/13. Bank 2.0/02. Working folder/05. Alexey Suprunov/01. Debit cards model and Data/20261001_Debit_cards_model_v19.1.xlsx` (copy in `~/Downloads`) |
| Past model versions | v7 … v19 | same folder → `past versions/` (v18 is still in the main folder because Alex had it open; **move it to `past versions/` when it is closed**) |
| Data request sent to the bank | – | same folder → `20260925_Debit_Model_Data_Request.xlsx` |
| **Armenia debit-card tier dashboard (HTML artifact)** | **v13** | https://claude.ai/artifact/ADerBkkaPqLrELjDHSWZ2m (private). Source: `~/Documents/claude_fb/market_dr_card_scan/` |
| **Cashback playbook (HTML artifact)** | v5 (balances blurred) | https://claude.ai/artifact/EVzYQKKr22ZDmJmCaEJfHk (shared by link). Source: `market_dr_card_scan/cashback_design/` |
| Debit value-prop slides (pptx, the bank's design system) | edits of 29–30 Sep | `~/Downloads/debit_slides.pptx` (Alex's master; **never edit it**); my outputs `debit_slides_fees_cashback.pptx`, `debit_slides_s6-7_fixed.pptx`, `debit_slides_slide4.pptx` |
| Market profit pools (bank model and plan KPIs) | v5.1 | `~/Downloads/Market profit pools Armenia v5.1.xlsx` |
| Per-contract card report | Aug-25 – Aug-26 | `~/Downloads/final_report.xlsx` (it has no card type; join via v13) |
| v13 model (holds contract_id / client_id keys) | – | `~/Downloads/20260924_Debit_cards_model_v13.xlsx` (174 MB) |
| MCC spend data (cashback engine) | – | `~/Downloads/ТРАТЫ ПО MCC.csv` (391 MCCs, 2.18M rows); older `SPEND BY MCC.csv` |

### This folder (`01_debit_cards_model_and_benchmark/`)

- **`model_build_helpers/`:**
  - `xmlbook.py` is the XML workbook helper: `Book`, `Sheet`, `f()`, `t()`, `_reset()`, `cell()`.
  - `dump.py` reads cached values via iterparse: `open_book`, `cells`, CLI.
  - `recalc.applescript` runs an Excel full calculation on `~/Downloads/_recalc_*.xlsx`. Edit the file name before each use.
  - `parse_fr.py` parses final_report.
  - `v13key.py`, `v13key2.py` and `v13client.py` handle the contract → card-type / client join through v13.
  - `make_assets_v4.py` builds the playbook assets.
- **`debit_slides_build/`:**
  - `render.py` is the PIL preview renderer.
  - `build4.py`, `build67.py`, `build23.py` and `build6b.py` are slide builders.
  - The Segoe UI ttf fonts were lost. Regenerate them from the Office woff files with fontTools.
- **`reference_images/`:**
  - cashback app screenshots 1–5 (Alex's phone);
  - the deposit strip style reference;
  - the slide 23 redo request;
  - rate.am FX screenshots from 30 Sep 2026, sorted by buy and by sell.

### Model build scripts (the main script folder)

They live in `~/Documents/claude_fb/market_dr_card_scan/cashback_engine/`.

| Script | What it did |
|---|---|
| `build_v16.py` | Tier re-cut, Cards dataset cols O–AB from final_report, Client profiles sections 6–8, interchange 0.5/1.2 & 0.6/1.5, perks |
| `build_v16b.py` | FX vs the CBA rate plus capture (superseded) |
| `build_v16c.py` | **One FX line per tier** (margin vs CBA); 'FX ranking' sheet rebuilt |
| `build_v16d.py` | Removed the Visa 2% fee line |
| `build_v17.py <in> <out> A\|B` | Option A (Visa Gold in Black) / B (Visa Gold in Premium) |
| `bench_v17.py` | Control panel benchmark cols F–H from dashboard stats |
| `elig_v17.py` + `elig_excl_gold.json` | Eligible-spend shares excluding gold-loan clients |
| `build_v18.py` | AMD-only switch, output re-layout, 'Eligible spend' tab |
| `build_v19.py` | 'Bank PnL' bridge (cols AX:BF, helper rows 96–114) |
| `build_v19b.py` | → v19.1: processing → row 60; Bank-PnL-only paid shares |

- **Older scripts** in the same folder:
  - cashback engine: `prep.py`, `build_workbook.py`, `engine.py` (Python reference that must equal Excel), `params.py`, `mcc_ref.py`, `merge_into_model.py`;
  - profiles: `profiles_prep.py`, `build_profiles.py`, `wire_profiles.py`;
  - forecasts and clean-up: `update_forecasts.py`, `cleanup_model.py`;
  - variants: `build_alt_arca_free.py`, `build_breakeven_sheet.py`.
- **Even older:** `market_dr_card_scan/excel/` (`build_model_v7.py`, `build_cp_v8.py`).

---

## 2. Workflow rules (non-negotiable)

1. **Never touch Alex's master or open files.**
   - Every change makes a new version file, `YYYYMMDD_Debit_cards_model_vNN.xlsx`.
   - Save it in the OneDrive folder and move the previous version to `past versions/`. Alex's rule: new version in the main folder, old ones in `past versions`.
2. **Always diff Alex's latest saved file before building.**
   - He edits inputs in place: fees, targets, the FTP rate, inserted rows, renamed sheets.
   - Carry his edits forward and never rebuild from an older raw output.
3. **Edit xlsx as XML** (`xmlbook.py`). Never round-trip through openpyxl, because it breaks pivots, comments, spill metadata and styles.
   - Shared formulas: overwrite only whole groups.
   - Adding a sheet means entries in workbook.xml, workbook.xml.rels, [Content_Types].xml and docProps/app.xml.
   - Set `fullCalcOnLoad="1"` and delete calcChain.xml.
   - Separator sheet names contain a raw `>`, so parse workbook.xml with lxml, not regex.
   - Overlapping `<cols>` ranges must be split before adding widths.
4. **Recalculate in real Excel via AppleScript**, on a copy at `~/Downloads/_recalc_<name>.xlsx`. Excel's sandbox won't open /private/tmp.
   - `open workbook` returns before loading, so poll the workbook names.
   - Close **only** that workbook and never other windows Alex has open.
   - Automation blocks while Alex is editing a cell.
5. **Verify** with `dump.py`: compare error cells against the previous version, check that the check rows equal 0, and spot-check key outputs.
6. **Report figures with labels** (memory `label-model-figures.md`).
   - Say whether each number is per card in AMD (Control panel J–N) or portfolio in AMD mn ('Cards PnL all tiers'), and give the cell.
   - Alex reads the Control panel first.
7. **Management data rule** (from Alex): never take client names, tax IDs, account numbers, per-account balances or income data from the bank. Specific transfers only as aggregates.
8. Never automate PowerPoint or Keynote. Work on pptx copies with python-pptx, render previews with PIL, and validate with the pptx skill's validate.py.
9. Blur personal info (balances, photos) in any screenshot before publishing.
10. Ask Alex before large modelling decisions (AskUserQuestion); small ones take a sensible default and get flagged.

---

## 3. Model v19.1: structure and key cells

### Sheets (main ones, in order)

- **Control panel:** the inputs and outputs Alex reads first.
- **Break-even curves:** break-even cashback % vs deposit uplift, live.
- **'8 cards model (as is lineup)':** today's 8 card types in columns D–K (ArCa, MCW, MCWE, Visa Classic, Visa Gold, Infinite, Metal, Digital).
  - Row 148 maps each card to a tier.
  - Tier aggregates sit in columns N–Q (Free / Black / Premium / Elite), rows 152–196 (SUMIF plus weights).
  - D90 = FTP credit rate, **11.1%** (Alex's input); D97 = FX reference rate, 7.1%.
  - Rows 45/50: interchange. Row 195: tier interchange.
  - Rows 81–83: FX revenue, which already includes Visa's 2% cross-currency fee.
- **'4 tiers model (to be lineup)':** one block per tier at row offsets 0 / 77 / 154 / 231 (Free / Black / Premium / Elite).
  - Columns: D = Q4-26 base, E–H = Q1–Q4 2027, I–K = 2027 / 2028 / 2029.
  - The per-card summary sits in N–R, rows 9–22 (Free; shifted +77 per tier).
  - Cashback rate rows are 59 / 136 / 213 / 290. They divide the Control panel target (% of eligible spend) by the eligible share.
- **'Cards PnL all tiers'** (Alex renamed it from 'PnL all tiers'): the portfolio P&L, average active cards × per-card economics, with first-year OPEX on new cards only.
- **'Bank PnL':** whole-bank P&L added by Alex, in AMD '000.
  - 2024–25 actuals, 2026 monthly budget, Budget 2027/2028 = columns AE/AF, Ambitious 2027/2028 = AR/AS.
  - Card lines 25–32: POS, Service, Interchange, Cashout, C2C, FX, Cashback.
  - My bridge sits in AX:BF (see §5).
- **Client profiles:** profile modes 1–3, multipliers (rows 74–80), sections 6–8 from final_report (rows 84–118), eligible shares excluding gold loans (rows 119–122).
- **Cards dataset:** 96,906 retail cards issued in 2026, with no IDs, plus final_report fields in columns O–AB.
- **CB engine sheets:** CB README / Inputs / Client view / Results / Categories / MCC_map / Profiles / Engine / Data.
- **'FX ranking':** rate.am bank quotes from 30.09.2026 vs CBA official rates, plus FB's margin today. F23 = CBA EUR rate.
- **'Eligible spend':** the eligible vs non-eligible split by tier from CB Results, 10 excluded categories, 45 excluded MCCs.
- Market benchmarking, Planned KPIs, 'PP v5.1 extract' and the other data sheets.

### Control panel layout

- **D3** = profile mode: 1 = all 2026 cards (as v13), 2 = **active users** (current), 3 = top 25% of active users.
- **Tier blocks** start at rows **6 / 30 / 54 / 78** (Free / Black / Premium / Elite). Alex inserted one row per block in v18, which pushed the v17 rows 6/29/52/75 down.
- **Columns:**
  - C = as is today;
  - D = to-be parameter (the input);
  - F / G / H = market benchmark min / median / max from the dashboard (FB excluded);
  - J–N = outputs per card (AMD);
  - O = notes.
- **Inputs inside each block** (b = block header row; Free shown, checked in v19.1):

  | Row | Input |
  |---|---|
  | b+1 | balance rate AMD |
  | b+2 | balance rate non-AMD |
  | b+3 / b+4 | cashout FB ATM / FB ATM ArCa |
  | b+5 / b+6 | cashout other ATM / other ATM ArCa |
  | b+7 | transfer to another bank |
  | b+8 | service fee, AMD / yr (D38 / D62 / D86) |
  | **b+9** | **FX margin vs CBA** (rows 15 / 39 / 63 / 87) |
  | b+10…b+12 | empty / hidden |
  | **b+13** | **cashback target, % of eligible spend** (D19 / D43 / D67 / D91) |
  | b+14 | cashback limit, AMD / month |
  | b+15 | deposit uplift, p.p. |
  | b+16 | Engine / Target switch (column C = engine rate as % of non-cash). All paid tiers are on "Target"; Free is on "Engine" |
  | b+18 | virtual share |
  | b+19 | metal share |
  | b+20 | paid-card share (Black D50 = 90%) |
  | b+21 | multipliers in use (text) |
  | **b+22** | **AMD-only switch** (rows 28 / 52 / 76 / 100; C = 1 as is, D = 0) |
- **Outputs (rows b+1 … b+20, columns J–N):** revenue, interest, interchange, cashout FB ATMs, cashout other ATMs, transfers, fee, FX; then costs: cashback (b+14), deposit uplift (b+15), recurring OPEX, one-off marketing, one-off other, perks; operating profit (b+20).

---

## 4. Parameters and decisions (current state)

### Tiers (v16+ cut, option "A")

| Tier | Cards today | Fee (AMD/yr, Alex) | Cashback target (% eligible spend) | Cap |
|---|---|---|---|---|
| Free | Visa Digital + ArCa Classic | 0 | 0 | – |
| Black | Visa Classic + Visa Gold | 5,000 | 1.9% | – |
| Premium | MC World | 20,000 | 2.6% | 14k AMD |
| Elite | MC World Elite + Infinite + Infinite Metal | 100,000 | 2.1% | – |

- Option B (Visa Gold in Premium) exists only as v17B / v17.1B in `past versions`. **A is the line taken forward.**
- Alex keeps changing fees and targets. Treat the table as "last seen" and read the file.

### Interchange and fees (finance team, 30 Sep 2026)

- Interchange, domestic / international:
  - standard cards: 0.5% / 1.2%;
  - Visa Gold and above: 0.6% / 1.5%.
- C2C 0.5%.
- Visa settles in EUR with a 2% cross-currency fee. **That fee is already in FX revenue: never add it again.** Mastercard settles in USD, no fee.
- Perks:
  - Premium = 10 EUR / yr × CBA EUR rate × MC World share of the tier;
  - Elite = 20k AMD / yr plus taxi rides.
- ArCa Pay / SBP free until 31 Dec (open: what happens after).

### FX

- **One line per tier: "FX margin vs CBA official rate"** (Alex rejected rating places, bid/ask half-spread and multi-row controls).
- FB today: **0.79%** (USD 0.48%, EUR 1.03%, RUB 1.85%). Currency weights follow the card FX balance mix: USD 44%, EUR 56%, RUB 0.3%. Buy/sell mix is 50/50.
- That makes FB 3rd thinnest of 16 banks. Market range 0.56–1.26%, median 1.04%.
- Tier FX revenue = today's 8-cards FX revenue × (parameter ÷ 0.79%).
- CBA official rates, 30.09.2026: USD 363.18, EUR 412.14, RUB 4.3187. Source: the api.cba.am SOAP call `ExchangeRatesByDate`.
- No liquid AMD perps exist, so CBA is the reference.

### AMD-only new cards (v18)

- Switch D = 0 removes international card payments (non-cash × (1 − today's international share D19)), the international share and FX card balances from 2027.
- The FX line then means the margin on cardholders' conversions on accounts / in the app (preferential-rate lever).

### Cashback eligible share (non-cash → eligible)

- Gold-loan clients are excluded (holders of a gold-backed loan or a gold-loan card), and so are dormant clients.
- Shares (option A): **Free 52.4%, Black 49.7%, Premium 65.9%, Elite 87.2%** (option B: Black 43.0%, Premium 55.5%).
- Client profiles rows 119–122: mode 1 = 'CB Results' row 12 (the engine sample); modes 2–3 = these static shares.
- Why Elite is so high: 109 gold-loan-holder Elite clients do 187m of 524m non-cash spend, mostly gambling.
- **'Eligible spend' tab:**
  - card spend splits into cash 32%, gambling 31% and eligible 27%;
  - excluded: gambling, cash, transfers, e-wallets, quasi-cash, government, utilities, telecom, insurance and charity;
  - 45 excluded MCCs.

### Cashback engine (inside the model)

- **Mechanic** (T-Bank style):
  - a menu of 7 bank categories + 2 partner offers, of which the client picks 4;
  - the base rate is pickable;
  - caps per client;
  - non-choosers get a flat 1% (Free 0%).
- **Auto-scaling:** the Control panel target auto-scales the menu rates through a Newton solver in CB Results rows 28–39.
- **Choice rule:** the client picks the 4 options with the highest expected reward.
- **Personas:** Anna (Black), Davit (Free), Petrosyan (Premium), Mariam (Elite), Aram (bettor).
- **Gambling (MCC 7995)** is about 37% of card volume, hence the eligible-share logic.
- More detail: memory `cashback-engine.md`.

### Profile modes (v14+)

- **Mode 1** = all 2026 cards; it reproduces v13.
- **Mode 2** = active users: excludes gold-loan cards and cards with no transaction in Jun–Aug 2026.
- **Mode 3** = top 25% of active users by volume.
- Multiplier = profile average ÷ average of all 2026 cards, per tier.
- The median of all cards is 0, so medians don't work.

### Other model logic

- **Balances:**
  - FTP income is gross, i.e. card balances × FTP 11.1%.
  - Deposit uplift = a pure cost (p.p. × deposited amount).
  - Deposit margin 1.25 p.p. (Alex).
- **Cashback cap saving** = share of capped clients × max(0, rate × capped spend − cap).
- **P&L volumes** come from Planned KPIs (profit pools v5.1); 2029 is extrapolated.
- **First-year OPEX** is scaled by the virtual and metal shares.

---

## 5. Bank PnL reconciliation (v19 / v19.1)

**Question Alex asked:** does the planned cards product P&L fit the whole-bank budget?

### Layout

| Columns | Content |
|---|---|
| AX / AY | Cards model 2027 / 2028, in AMD '000 |
| AZ–BB | Δ vs Budget 2027, Budget 2028 and Ambitious 2028, on card-only rows 25–32 |
| BC… | Card share of each budget line |
| BF | Notes |

- Helper bridge: rows **96–114**; the check rows must equal 0. Row 114 also covers the service-fee difference.
- Paid-card shares used only in Bank PnL: **AX117:AY120**, default = the model's '4 tiers' row 15.
  - They drive service fees in row 27 via rows 121–123.
  - Alex will set more conservative rates there.

### Mapping (agreed with Alex)

| Model line | Bank PnL row |
|---|---|
| FTP income on card balances | 8 |
| Deposit uplift | 11 |
| Client interest | 13 |
| Card fee lines (Service / Interchange / Cashout / C2C / FX / Cashback) | 27–32 (POS not modelled) |
| Processing + production + card DB | 60 (card technology); row 37 left empty |
| Perks | 67 |
| Marketing | 69 |
| Allocated fixed card OPEX | memo only, not mapped (0.64bn in 2027) |

- The profile mode follows Control panel D3, so Alex chooses it there.
- Mode 1 is the most comparable (Alex agrees). In mode 1, interchange is half the budget.

### Results (mode 2, 2027, AMD bn)

- Card fee income 2.06 vs budget 1.29. The biggest gap is service fees: 1.02 vs 0.20.
- Card contribution 0.87bn before overhead and 0.23bn after allocated fixed OPEX.

---

## 6. Version history (short)

| Version | Date | What changed |
|---|---|---|
| v7 | 22 Sep | 4 tier blocks cloned from Fast Free; tier mapping |
| v8 | 23 Sep | Control panel rebuilt in Alex's order |
| v9–v12 | 24 Sep | Cashback engine merged in; v12: target drives the P&L |
| v13 | 24 Sep | Alex's manual version (174 MB; holds contract_id / client_id) |
| v14 | 24 Sep | Client-profile modes; clean-up to 29 MB |
| v14 alt | 25 Sep | ArCa in Free; break-even curves sheet (28 Sep) |
| v15 | 29 Sep | Alex's version |
| v16 | 30 Sep | New tiers, final_report data, finance rates |
| v16.1 / v16.2 / v16.3 | 30 Sep | FX iterations; v16.3 = one FX line, no Visa fee |
| v17A/B, v17.1A/B | 30 Sep | Visa Gold split options; benchmarks; eligible shares excluding gold loans |
| v18 | 30 Sep | AMD-only switch; output split (cashout FB / other, marketing / other one-off); Eligible spend tab |
| v19 | 1 Oct | Bank PnL bridge on Alex's edited v18 |
| **v19.1** | **1 Oct** | **Current.** Processing → row 60; Bank-PnL-only paid shares |

Detailed notes per version are in memory `card-economics-model.md`.

---

## 7. Market benchmark dashboard (HTML artifact)

- **URL:** https://claude.ai/artifact/ADerBkkaPqLrELjDHSWZ2m, v13. The watch on it was lost, so re-subscribe with ArtifactComments if needed.
- **Rebuild:** `cd ~/Documents/claude_fb/market_dr_card_scan && python3 build_tier_dashboard.py --note "what changed"`, then republish `debit-card-tiers.html` to the same URL.
  - Versions are archived in `versions/` and logged in `versions/CHANGELOG.md`.
- **Inputs:**
  - `market/data/2026-09-18-competitor-cards.json`: 7 banks (Fast, Acba, Ameria, Ardshin, Converse, Evoca, IDBank);
  - `data/2026-09-21-fx-snapshot-rate-am.json`;
  - `data/2026-09-29-deposit-rates.json`;
  - `norms.py` (per-card normalisation, `STRIP_WHY`, `LEGACY`);
  - `tier_dashboard_template.html`.
- **v13 tiers** (aligned to the model):
  - all ArCa cards → Free;
  - Gold cards → Black;
  - Platinum / World → Premium;
  - Signature / Infinite / World Elite / Metal / Amex Gold Debit → Elite.
  - Counts: Free 25, Black 39, Premium 13, Elite 19.
  - Pre-change norms are in `versions/norms_pre_v13.py`.
- **Local preview:** `.claude/launch.json` config "tier-dashboard" on port 8765 (the page is ~1.7 MB with base64 card images).
- **Key findings:**
  - FB leads on balance interest (4%) and FX cost.
  - FB has the top deposit rate (10.0% vs median 8.05%).
  - FB funds no cashback today.
  - Acba Amex Cashback is the market's best bank-funded cashback.
  - FB's ATM fees are below median.
- The model's Control panel benchmarks (columns F–H) come from these dashboard stats (`bench_v17.py`).

## 8. Cashback playbook (HTML artifact)

- **URL:** https://claude.ai/artifact/EVzYQKKr22ZDmJmCaEJfHk, v5 (balances blurred).
- **Source:** `market_dr_card_scan/cashback_design/` (`make_v4.py`, `template_v4.html`, `data_v4.js`, the assets JSON).
- **Content:**
  - 10 open launch decisions × pathways × 7 benchmark banks (T-Bank, Alfa, Ozon, Yandex, Kaspi, Revolut, Plata);
  - an "Already decided" section;
  - an Engine logic tab.
- **Open:** the Premium vs Black rate inversion (options A–D). Some "to verify" items remain.
- More detail: memory `cashback-playbook.md`.

---

## 9. Open items / next steps

**Carry forward into the next build (v19.2 / v20):** Alex edited **v18** after v19.1 was built (saved 1 Oct 15:52; diffed 2 Oct). None of these are in v19.1 yet:

| Sheet | Cells | v19.1 | Alex's v18 |
|---|---|---|---|
| Control panel | Black cashback target D43 | 1.9% | **2.2%** |
| Control panel | Premium cashback target D67 | 2.6% | **3.0%** |
| Control panel | Black deposit uplift D45 | 0 | **−0.25 p.p.** |
| Control panel | Premium deposit uplift D69 | 0 | **−0.10 p.p.** |
| 4 tiers model | Baseline deposit rate D54:K54 | Deposit_rates_projection path, 9.5–9.6% (E54 = TRANSPOSE formula) | **hard-coded 10.25%** in every period |
| Bank PnL | Budget columns E–AS | pasted values | his budget formulas, same numbers |

- Ask Alex whether v18 or v19.1 is now his working file before building.
- A negative uplift means Black / Premium depositors get a lower rate than the baseline.

- Alex picks the Bank PnL comparison mode (D3; mode 1 is the most comparable) and sets conservative paid shares in AX117:AY120.
- Explain or close the service-fee gap vs budget (1.02 vs 0.20bn in 2027): fee levels, waiver rules and the paid share.
- Waiver rules for paid tiers: what counts as "active", free conditions. The CVM thread proposes moving free service from a deposit condition to a card-balance condition.
- ArCa Pay / SBP pricing after 31 Dec.
- Marketing / CAC data from Zhanna, the bank's marketing lead (pending).
- Finance confirmation of card FX income: what is booked vs quoted.
- Move v18 to `past versions/`.
- Dashboard: the open items are Ardshinbank's fee for card-to-card transfers to other banks and the Acba Visa Signature Limited Edition fees.
- Playbook: final verification items; Premium/Black inversion decision.

## 10. Links to other memory

- `fast-bank-transformation.md`: programme, people, targets.
- `card-economics-model.md`: per-version build notes, v7 → v19.1.
- `cashback-engine.md`: engine mechanics, data, solver.
- `card-tier-dashboard.md`: dashboard decisions, sources, findings.
- `cashback-playbook.md`: playbook scope and versions.
- `label-model-figures.md`: how to quote model numbers.
