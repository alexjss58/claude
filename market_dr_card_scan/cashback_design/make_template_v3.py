"""Build template_v3.html from template_v2.html (version 3 of the cashback playbook)."""
t = open('template_v2.html', encoding='utf-8').read()


def rep(a, b):
    global t
    assert t.count(a) == 1, (a[:90], t.count(a))
    t = t.replace(a, b)


# header
rep('<div class="eyebrow">Fast Bank · cashback debit card · <span class="draft">Content draft 2</span></div>',
    '<div class="eyebrow">Fast Bank · cashback debit card</div>')
rep("<p class=\"lede\">Ten open decisions on the way to launching choose-your-cashback on Fast Bank's paid debit cards, the pathways the market uses, and the recommended option in blue. The Engine logic tab shows how our engine builds each client's menu and rates. Click a bank to read how it does it.</p>",
    "<p class=\"lede\">Ten open decisions on the way to launching choose-your-cashback on Fast Bank's paid debit cards, the pathways the market uses, and the recommended option in blue. One decision is still open for Fast Bank; it is at the end of Design decisions. The Engine logic tab shows how our engine builds each client's menu and rates. Click a bank to see how it does it, with app screenshots.</p>")
rep('''      <span>Draft 2 · 27 Sep 2026</span>
      <span>Logos and app screenshots come in the final version</span>''', '''      <span>Version 3 · 27 Sep 2026</span>''')

# CSS additions
rep('/* engine logic */', '''.logo{flex:none;width:30px;height:30px;border-radius:7px;object-fit:contain;background:#fff;border:1px solid var(--line)}
.logo.sm{width:20px;height:20px;border-radius:5px}
.vis.real{padding:0;background:#fff}
.vis.real img{width:100%;height:100%;object-fit:cover;object-position:top center;display:block}
.vis.real .sch{top:auto;bottom:6px;right:6px;background:rgba(20,22,26,.72);color:#fff;padding:2px 6px;border-radius:4px;letter-spacing:.04em}
.appshot{margin:0;display:grid;gap:6px;justify-items:start}
.appshot img{width:min(280px,100%);border-radius:12px;border:1px solid var(--line);display:block}
.appshot figcaption{font-size:12px;color:var(--ink-2);max-width:48ch}
.decision{margin-top:36px;scroll-margin-top:76px;background:var(--gap-soft);border:1.5px solid var(--gap-ink);border-radius:14px;padding:18px 18px 20px}
.decision .dtag{display:inline-block;font-size:10.5px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;padding:3px 8px;border-radius:4px;background:var(--gap-ink);color:var(--surface)}
.decision h2{margin-top:8px}
.decision p{margin:6px 0 0;max-width:96ch;color:var(--ink)}
.dopts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}
@media (max-width:980px){.dopts{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:560px){.dopts{grid-template-columns:1fr}}
.dopt{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 13px;display:grid;gap:6px;align-content:start}
.dopt .dk{display:flex;gap:8px;align-items:center;font-weight:750;font-size:14px}
.dopt .dk span{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:6px;background:var(--gap-ink);color:var(--surface);font-size:12px;font-weight:800;flex:none}
.dopt dl{display:grid;grid-template-columns:auto 1fr;gap:4px 8px;margin:0;font-size:12.5px}
.dopt dt{color:var(--muted);font-weight:650}
.dopt dd{margin:0;color:var(--ink-2)}
.dopt .cost{font-weight:750;color:var(--ink)}
.dnote{font-size:12px;color:var(--ink-2);margin-top:10px}

/* engine logic */''')

# logos instead of monograms
rep('const mono = (b, cls = "") => `<span class="mono ${cls}" aria-hidden="true">${esc(BANKS[b].mono)}</span>`;',
    'const mono = (b, cls = "") => ASSETS.logo[b] ? `<img class="logo ${cls}" src="${ASSETS.logo[b]}" alt="" aria-hidden="true">` : `<span class="mono ${cls}" aria-hidden="true">${esc(BANKS[b].mono)}</span>`;')

# visuals: the no-picks schematic moves to D; real crops take precedence
rep('  b2C: () => `<div class="vh">Earn rate set by plan</div>`', '  b2D: () => `<div class="vh">Earn rate set by plan</div>`')
rep('const vis = key => VIS[key] ? `<div class="vis"><span class="sch">Schematic</span>${VIS[key]()}</div>` : "";',
    '''const CROPBANK = {b2A:"T-Bank", b2C:"Yandex Pay", b3B:"Ozon Bank", b5B:"T-Bank", b5C:"Ozon Bank", b8A:"Plata", b8B:"Yandex Pay", b9A:"Plata", b9B:"Alfa-Bank", b9C:"Kaspi"};
const vis = key => ASSETS.crop[key] ? `<figure class="vis real" style="margin:0"><img src="${ASSETS.crop[key]}" alt="${esc(CROPBANK[key])} app screenshot" loading="lazy"><span class="sch">App · ${esc(CROPBANK[key])}</span></figure>`
  : VIS[key] ? `<div class="vis"><span class="sch">Schematic</span>${VIS[key]()}</div>` : "";''')

# the open decision, appended to the decisions view
rep('''/* ---------- engine logic ---------- */''', '''/* ---------- the open decision ---------- */
(function () {
  const taxB = ENG.rows.find(r => r.code === "TAX").show.Black, taxP = ENG.rows.find(r => r.code === "TAX").show.Premium;
  const inv = ENG.rows.filter(r => r.role.Black !== "No" && r.show.Premium < r.show.Black).length;
  const opts = [
    ["A", "Raise Premium's target", "About 1.2% of non-cash spend (≈2.4% of eligible), so Premium rates are at least Black's.", "+≈1.4bn AMD (Premium 2.5 → 3.9bn)", "Premium's portfolio profit turns slightly negative (1.3bn → −0.1bn AMD)."],
    ["B", "Lower Black's target", "About 0.4% of non-cash, so Black rates are no higher than Premium's (taxi " + pct(taxB) + " → " + pct(taxP) + ").", "−≈0.4bn AMD", "A weaker headline for the mass tier that drives new-to-bank acquisition."],
    ["C", "Keep both targets", "Accept lower Premium rates; Premium's edge is the cap (20,000 vs 5,000 AMD), one extra menu slot and the travel partner offer.", "none", "Premium looks worse than Black on the menu itself."],
    ["D", "Set targets on eligible spend", "One basis for all tiers, so gambling-heavy non-cash stops inflating Black's budget. Levels are then chosen per tier.", "depends on the levels", "The model's cashback line has to be reworked to use eligible spend."]
  ];
  $("#view-dec").insertAdjacentHTML("beforeend", `
  <section class="decision" id="decision" aria-labelledby="decision-t">
    <span class="dtag">Decision needed</span>
    <h2 id="decision-t">Should Premium show higher rates than Black?</h2>
    <p>With today's targets, Premium clients would see lower rates than Black in ${inv} of 18 categories: taxi is ${pct(taxP)} on Premium against ${pct(taxB)} on Black. Black's 0.5% target is measured on non-cash spend of which only 33% is eligible for cashback (most of the rest is gambling), against 48% for Premium, so it buys much richer menus. Details in the Engine logic tab.</p>
    <div class="dopts">${opts.map(([k, n, what, cost, watch]) => `
      <div class="dopt"><div class="dk"><span>${k}</span>${esc(n)}</div>
        <dl><dt>What</dt><dd>${esc(what)}</dd><dt>3Y cost</dt><dd class="cost">${esc(cost)}</dd><dt>Watch</dt><dd>${esc(watch)}</dd></dl></div>`).join("")}
    </div>
    <p class="dnote">Cost is bank cashback over 2027–2029 from the v14 P&amp;L (mode 1), approximate. Options can be combined, for example B now and D when the model is next rebuilt.</p>
  </section>`);
})();

/* ---------- engine logic ---------- */''')

# jump list: add the decision
rep('''$("#jumps").innerHTML = BLOCKS.map((b, i) => `<button class="jump" data-jump="${b.id}" title="${esc(b.title)}">${i + 1}</button>`).join("");''',
    '''$("#jumps").innerHTML = BLOCKS.map((b, i) => `<button class="jump" data-jump="${b.id}" title="${esc(b.title)}">${i + 1}</button>`).join("") + `<button class="jump" data-jump="decision" title="Decision needed" style="background:var(--gap-soft);border-color:var(--gap-ink);color:var(--gap-ink);font-weight:700">Decision</button>`;''')

# engine flag points to the decision
rep('<div class="flag"><span class="ft">Flag: Premium clients would see lower rates than Black in ${inv.length} of 18 categories</span>',
    '<div class="flag"><span class="ft">Decision needed: Premium clients would see lower rates than Black in ${inv.length} of 18 categories</span>')

# drawer: real screenshots
rep('''    <h4>In the app</h4>
    <div class="shot"><b>Screenshot slot: ${esc(d.app)}</b>Added in the final version</div>
    ${srcList(d.src)}`);''', '''    <h4>In the app</h4>
    ${appShot(bk, blockId)}
    ${srcList(d.src.concat(STORE[bk] ? [STORE[bk]] : []))}`);''')
rep('''    <h4>App</h4>
    <div class="shot"><b>Screenshot slot: ${esc(bank.name)} cashback home screen</b>Added in the final version</div>
    ${srcList(keys)}`);''', '''    <h4>In the app</h4>
    ${appShot(bk, null)}
    ${srcList(keys.concat(STORE[bk] ? [STORE[bk]] : []))}`);''')
rep('''function showDetail(bk, blockId) {''', '''const STORE = {tbank:"st_tb", alfa:"st_alfa", ozon:"st_ozon", yandex:"st_ya", kaspi:"st_kaspi", plata:"st_plata"};
const SHOTDEF = {tbank:"tbank_pick", alfa:"alfa_wheel", ozon:"ozon_pick", yandex:"yandex_pick", kaspi:"kaspi_promo", plata:"plata_cats"};
const SHOTBLOCK = {tbank:{b5:"tbank_city"}, ozon:{b5:"ozon_disc", b8:"ozon_switch"}, yandex:{b3:"yandex_qr", b4:"yandex_qr", b5:"yandex_shops", b8:"yandex_qr", b10:"yandex_qr"}, kaspi:{b5:"kaspi_store"}, plata:{b8:"plata_home"}};
const SHOTCAP = {
  tbank_pick:"T-Bank: “Which 4 categories do you choose for November?”, with “1% on all purchases” among the options.",
  tbank_city:"T-Bank: everyday services with partner cashback (the 10% badges).",
  alfa_wheel:"Alfa-Bank: “Up to 100% cashback in the Supercashback wheel”.",
  ozon_pick:"Ozon Bank: “Cashback up to 25% in rubles, new categories every month”, with the pick-4 list.",
  ozon_disc:"Ozon Bank: “Discounts up to 30% on Ozon” for card holders.",
  ozon_switch:"Ozon Bank: switch between ruble cashback and “items for 1 ₽” at any time.",
  yandex_pick:"Yandex Pay: “Choose your benefit”, new cashback and discount categories every month.",
  yandex_qr:"Yandex Pay: “Pay by QR with cashback”, up to 50% in Plus points.",
  yandex_shops:"Yandex Pay: discounts and cashback in 3,500 shops.",
  kaspi_promo:"Kaspi: Promotions, with bonus and discount offers (Kazakh-language listing).",
  kaspi_store:"Kaspi: the Kaspi Store marketplace.",
  plata_cats:"Plata: “Up to 15% cashback”, April categories and cashback earned.",
  plata_home:"Plata: home screen with cashback earned this month."
};
function appShot(bk, blockId) {
  const key = (SHOTBLOCK[bk] && blockId && SHOTBLOCK[bk][blockId]) || SHOTDEF[bk];
  if (!key) return `<div class="shot"><b>No public screenshot</b>Revolut's store listings don't show a RevPoints screen, and revolut.com blocks automated access.</div>`;
  return `<figure class="appshot"><img src="${ASSETS.shot[key]}" alt="${esc(SHOTCAP[key])}"><figcaption>${esc(SHOTCAP[key])} Store listing screenshot.</figcaption></figure>`;
}
function showDetail(bk, blockId) {''')

# footer
rep('The small pictures on each option are schematic illustrations of the mechanic, not bank screenshots; real app screenshots go into the bank sidebars in the final version.',
    "Pictures on the options are either app screenshots (labelled “App · bank”, from the banks’ public store listings) or schematic illustrations of the mechanic (labelled “Schematic”) where no bank screen shows it. The bank sidebars carry the store screenshots.")
rep('const ENG = /*ENGINE*/;', 'const ENG = /*ENGINE*/;\nconst ASSETS = /*ASSETS*/;')
open('template_v3.html', 'w', encoding='utf-8').write(t)

# assemble the page
SP = '/private/tmp/claude-501/-Users-suprunov-Documents-claude-fb/444d06dd-82fb-4e1b-8c91-b1f7bce70025/scratchpad/cb'
page = (t.replace('/*DATA*/', open('data_v3.js', encoding='utf-8').read())
         .replace('/*ENGINE*/', open(f'{SP}/engine_page_data.json').read())
         .replace('/*ASSETS*/', open(f'{SP}/assets.json').read()))
open('cashback-playbook.html', 'w', encoding='utf-8').write(page)
print('page bytes', len(page.encode('utf-8')))
