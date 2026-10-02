"""Version 4 of the cashback playbook: template_v3 + data_v3 -> template_v4 + data_v4 -> cashback-playbook.html.
Adds the team's September 2026 app screenshots (T-Bank Premium, Yandex Pay, Ozon Bank, Sber) and
removes Revolut from block 1, pathway C."""
SP = '/private/tmp/claude-501/-Users-suprunov-Documents-claude-fb/444d06dd-82fb-4e1b-8c91-b1f7bce70025/scratchpad/cb'


def edit(text, pairs):
    for a, b in pairs:
        assert text.count(a) == 1, (a[:100], text.count(a))
        text = text.replace(a, b)
    return text


# ---------------- data ----------------
d = open('data_v3.js', encoding='utf-8').read()
d = edit(d, [
    # bank one-liners
    ('line:"Categories up to 25% outside Ozon, 1% elsewhere; instant card price on the marketplace."',
     'line:"Pick 4 a month, “1% on all purchases” and brand partners among the options; instant card price on Ozon."'),
    ('line:"Plus points: 3 categories a month, up to 50% in Yandex services; needs Yandex Plus."',
     'line:"Plus points: pick 5 of 10 a month, “1% on all purchases” is one option; up to 50% in Yandex services."'),
    # a source for the screenshots
    ('  fin_jun:  {t:"Finuslugi: which cashback categories to choose in June (bank comparison)", d:"1 Jun 2026", u:"https://finuslugi.ru/navigator/finansovaya-gramotnost/stat_keshbek-na-iyun-kakie-kategorii-vybrat"}',
     '  fin_jun:  {t:"Finuslugi: which cashback categories to choose in June (bank comparison)", d:"1 Jun 2026", u:"https://finuslugi.ru/navigator/finansovaya-gramotnost/stat_keshbek-na-iyun-kakie-kategorii-vybrat"},\n'
     '  app_sep:  {t:"App screenshots taken by the H21 team: T-Bank (Premium client), Yandex Pay, Ozon Bank and Sber", d:"late Sep 2026", u:""}'),

    # block 1: Revolut out of pathway C; Yandex's list has MCC categories, so it moves to A
    ('''    banks:["plata","tbank","alfa"]},
   {k:"B", name:"Short fixed list for everyone"''', '''    banks:["plata","tbank","alfa","yandex"]},
   {k:"B", name:"Short fixed list for everyone"'''),
    ('''   {k:"C", name:"No categories: ecosystem or all spend", short:"No categories",
    desc:"Rewards come from own services, promotions or all spend.",''', '''   {k:"C", name:"No categories: ecosystem promotions", short:"No categories",
    desc:"Rewards come from own services, sellers and promotions.",'''),
    ('    banks:["kaspi","yandex","revolut"]}\n  ],\n  det:{\n   tbank:{p:"A", head:"MCC categories and named partner merchants',
     '    banks:["kaspi"]}\n  ],\n  det:{\n   tbank:{p:"A", head:"MCC categories and named partner merchants'),
    ('''   yandex:{p:"C", head:"Yandex services are the core; monthly categories sit on top.",
     pts:["Up to 50% in points in Yandex services; the client adds 3 categories a month.",''', '''   yandex:{p:"A", head:"MCC categories, Yandex services and partner offers sit in one monthly list.",
     pts:["The October 2026 list mixes MCC categories (bars and restaurants, supermarkets, clothing and footwear, books) with Yandex services (Yandex Fuel, Kinopoisk) and partner offers payable with any bank card (S7, car insurance).",'''),
    ('''     app:"Benefit screen with Yandex services and categories", src:["ya_help","kb_ya"]},''',
     '''     app:"Benefit screen with Yandex services and categories", src:["app_sep","ya_help","kb_ya"]},'''),
    ('''     app:"Promotions section", src:["kaspi_b","db_kaspi"]},
   revolut:{p:"C", head:"No categories: every eligible card payment earns points.",
     pts:["The plan sets the earn rate. Merchant boosts come through Revolut Offers and Shops."],
     app:"RevPoints on a card transaction", src:["revopt","dscout"]}
  }},''', '''     app:"Promotions section", src:["kaspi_b","db_kaspi"]}
  }},'''),

    # block 2: Yandex shows the base as one of 5 picks; the "services, no base" pathway goes
    ('''    banks:["tbank","plata","ozon"]},
   {k:"B", name:"Pick N categories; base on top"''', '''    banks:["tbank","plata","ozon","yandex"]},
   {k:"B", name:"Pick N categories; base on top"'''),
    ('''   {k:"C", name:"Pick among own services; no base rate", short:"Services, no base",
    desc:"Picks among the group's services and partners; nothing outside them.",
    plus:"Drives traffic to the group's own services.", minus:"No reward on everyday spend outside the picks.",
    banks:["yandex"]},
   {k:"D", name:"No monthly picks", short:"No picks",''', '''   {k:"C", name:"No monthly picks", short:"No picks",'''),
    ('''          "2026 reviews give 7 and 8; the long read (January 2026) gave 8, 9 and 10. To confirm on T-Bank's own pages."],''',
     '''          "A Premium client's October 2026 screen reads “Select 4 categories” with “More categories for you”: 1% on all purchases, 15% fuel and up to 25% shopping in T-Bank's City service, 5% pharmacies, beauty, entertainment and sports goods, and at least one more.",
          "2026 reviews give 7 and 8; the long read (January 2026) gave 8, 9 and 10. The Premium screen shows at least 8. To confirm the Black count."],'''),
    ('''     app:"Category picker with the 1% option", src:["fin_tb","kb_tb","tb_help"]},''',
     '''     app:"Category picker with the 1% option", src:["app_sep","fin_tb","kb_tb","tb_help"]},'''),
    ('''   ozon:{p:"A", head:"Pick 4 categories a month; “1% on all purchases” is one of the options.", verify:true,
     pts:["The app's picker reads “Choose 4 cashback categories for the month”, with “1% on all purchases” first in the list (store screenshot).",
          "A 2026 review says purchases outside the chosen categories earn 1% automatically and that Ozon Premium adds a fifth pick. To confirm which rule applies now."],
     kv:[["Picked","4"],["Base","1%, shown as a pick in the app"]],
     app:"Category picker", src:["fin_ozon","kb_ozon"]},''', '''   ozon:{p:"A", head:"Pick 4 categories a month; “1% on all purchases” is one of the options.",
     pts:["A client's September 2026 cashback screen lists 4 chosen categories: 1% on all purchases, 5% cosmetics, 10% Globus and 50% Tasty Coffee. The 1% takes one of the 4 slots.",
          "Brand partners (Globus, Tasty Coffee) are picks in the same list as categories.",
          "A 2026 review says Ozon Premium adds a fifth pick."],
     kv:[["Picked","4"],["Base","1%, only if picked"]],
     app:"Category picker", src:["app_sep","fin_ozon","kb_ozon"]},'''),
    ('''   yandex:{p:"C", head:"Pick categories each month among Yandex services and partners; no base rate.", verify:true,
     pts:["The app asks clients to “choose 4 more categories” (Yandex Taxi, Yandex Market, Yandex Eda, Delivery and others) for points and discounts all month. A review says 3 picks.",
          "Points need an active Yandex Plus subscription."],
     kv:[["Picked","4 in the app (3 per a review)"],["Paid as","Plus points"]],
     app:"“Benefit in [month]” screen", src:["kb_ya","ya_help"]},
   revolut:{p:"D",''', '''   yandex:{p:"A", head:"Pick 5 of 10 each month; “1% on all purchases” is one of the options.",
     pts:["The October 2026 screen reads “Select 5 out of 10 categories”. With the Yandex Pay card: 1% on all purchases, 3% bars and restaurants, 3% supermarkets, 3% Yandex Fuel, 10% Kinopoisk, 5% clothing and footwear, 10% books. With any bank card: 100% in S7 and 100% on car insurance, in Plus points.",
          "Earlier sources gave 3 or 4 picks among Yandex services; the app now shows 5 of 10.",
          "Points need an active Yandex Plus subscription."],
     kv:[["Offered","10"],["Picked","5"],["Base","1%, only if picked"],["Paid as","Plus points"]],
     app:"“Select 5 out of 10” screen", src:["app_sep","kb_ya","ya_help"]},
   revolut:{p:"C",'''),
    ('''   kaspi:{p:"D", head:"No monthly picks."''', '''   kaspi:{p:"C", head:"No monthly picks."'''),

    # block 3: rates seen on the screens
    ('''     pts:["Partner offers go up to 30%, as do some promotions."],''',
     '''     pts:["Partner offers go up to 30%, as do some promotions.",
          "A Premium client's October 2026 menu: 5% on pharmacies, beauty, entertainment and sports goods; 15% on fuel and up to 25% on shopping through the City partner service; 1% on all purchases."],'''),
    ('''     kv:[["Categories","1–15%"],["Partners","up to 30%"]], app:"Menu showing different rates per category", src:["fin_tb"]},''',
     '''     kv:[["Categories","1–15%"],["Partners","up to 30%"]], app:"Menu showing different rates per category", src:["app_sep","fin_tb"]},'''),
    ('''     pts:["2% in points on SBP QR payments, if chosen as a category."],
     kv:[["Headline","up to 50% (points)"]], app:"Category rates", src:["kb_ya","ya_help"]},''',
     '''     pts:["2% in points on SBP QR payments, if chosen as a category.",
          "The October 2026 list pays 1% on all purchases, 3–5% on categories, 10% on Kinopoisk and books, and 100% on partner offers."],
     kv:[["Headline","up to 50% (points)"]], app:"Category rates", src:["app_sep","kb_ya","ya_help"]},'''),

    # block 5: brand partners inside the pick lists
    ('''    banks:["tbank","alfa","plata"]},
   {k:"B", name:"Separate offer wall, activated before buying"''', '''    banks:["tbank","alfa","plata","ozon"]},
   {k:"B", name:"Separate offer wall, activated before buying"'''),
    ('''          "A separate partner section (“City”) runs offers up to 30% for limited periods.",''',
     '''          "A separate partner section (“City”) runs offers up to 30% for limited periods.",
          "City offers also sit in the pick list: 15% fuel and up to 25% shopping in City for a Premium client in October 2026.",'''),
    ('''     app:"Partner offers section", src:["bi_tb","kb_tb","fin_tb"]},''',
     '''     app:"Partner offers section", src:["app_sep","bi_tb","kb_tb","fin_tb"]},'''),
    ('''   ozon:{p:"C", head:"On Ozon, the marketplace funds a lower card price.",
     pts:["Product pages show two prices, the regular one and the Ozon Card price, so the saving is instant rather than paid back later."],
     app:"Product page with two prices", src:["kb_ozon"]},''', '''   ozon:{p:"A", head:"Brand partners are picks in the monthly list; on Ozon itself, the marketplace funds a lower card price.",
     pts:["A client's September 2026 picks included Globus at 10% and Tasty Coffee at 50%, next to 1% on all purchases and 5% cosmetics.",
          "A separate “Partner benefits” section lists offers from more than 60 merchants, among them Pyaterochka, Magnit, CDEK and Perekrestok.",
          "Product pages on Ozon show two prices, the regular one and the Ozon Card price, so the saving is instant rather than paid back later."],
     app:"Pick list with brand partners", src:["app_sep","kb_ozon"]},'''),
    ('''     pts:["Up to 50% in points in Yandex services. Yandex Market gives a direct discount (up to 3,000 RUB) instead of cashback."],''',
     '''     pts:["Up to 50% in points in Yandex services. Yandex Market gives a direct discount (up to 3,000 RUB) instead of cashback.",
          "Partner offers also sit in the monthly pick list, payable with any bank card: 100% in S7 and on car insurance (October 2026)."],'''),

    # block 6
    ('''   yandex:{p:"B", head:"A monthly list; the client picks 3.", pts:["The list refreshes every month."], app:"“Benefit in [month]” screen", src:["kb_ya","ya_help"]},''',
     '''   yandex:{p:"B", head:"A monthly list of 10; the client picks 5.", pts:["The list refreshes every month."], app:"“Select 5 out of 10” screen", src:["app_sep","kb_ya","ya_help"]},'''),

    # block 7: Yandex's base is a pick, so the fallback is uncertain; home-screen reminder
    ('''   yandex:{p:"B", head:"Categories refresh monthly on the “Benefit in [month]” screen.", pts:[], app:"Benefit screen", src:["ya_help"]},''',
     '''   yandex:{p:"B", head:"Categories refresh monthly; a home-screen card reminds clients to choose.", verify:true,
     pts:["In late September 2026 the home screen showed “Select categories for October” with a Select button.",
          "“1% on all purchases” is one of the 5 picks, so the 1% may not apply to clients who don't choose. To confirm."], app:"Home-screen reminder", src:["app_sep","ya_help"]},'''),

    # block 8
    ('''     pts:["A second programme pays “Stars” points instead of rubles; clients can switch between them monthly."],''',
     '''     pts:["The cashback screen shows the running total, “accumulating until 17 October”, and a Limits button (September 2026).",
          "A second programme pays “Stars” points instead of rubles; clients can switch between them monthly."],'''),
    ('''app:"Cashback credit and the Stars switch", src:["fin_ozon","kb_ozon"]},''',
     '''app:"Cashback credit and the Stars switch", src:["app_sep","fin_ozon","kb_ozon"]},'''),

    # block 9
    ('''     pts:["Partner offers live in a separate section of the app."], app:"Category picker and cap progress", src:["tb_help"]},''',
     '''     pts:["Partner offers live in a separate section of the app.",
          "The picker tells Premium clients they get “More categories for you” (October 2026)."], app:"Category picker and cap progress", src:["app_sep","tb_help"]},'''),
    ('''     pts:["The weekly “Monday Plus” wheel gives extra cashback and prizes."], app:"Weekly wheel", src:["ya_help"]},''',
     '''     pts:["The weekly “Monday Plus” wheel gives extra cashback and prizes.",
          "A card on the home screen prompts “Select categories for October”, next to a banner to open a Super Split card."], app:"Weekly wheel", src:["app_sep","ya_help"]},'''),
])
open('data_v4.js', 'w', encoding='utf-8').write(d)

# ---------------- template ----------------
t = open('template_v3.html', encoding='utf-8').read()
t = edit(t, [
    ('<span>Version 3 · 27 Sep 2026</span>', '<span>Version 4 · 28 Sep 2026</span>'),
    # the no-picks schematic is pathway C again; pathway C of block 1 no longer covers all-spend points
    ('  b2D: () => `<div class="vh">Earn rate set by plan</div>`', '  b2C: () => `<div class="vh">Earn rate set by plan</div>`'),
    ('''  b1C: () => `<div class="vh">No category list</div>` + row("Any card purchase", "+pts") + row("Promotion at a partner", "+15%") + row("Own marketplace", "card price"),''',
     '''  b1C: () => `<div class="vh">No category list</div>` + row("Promotion at a partner", "+15%") + row("Seller bonus on the marketplace", "+60%") + row("Paying outside a promotion", "0%"),'''),
    # option pictures: label, and a translation on hover for Russian screens
    ('''const CROPBANK = {b2A:"T-Bank", b2C:"Yandex Pay", b3B:"Ozon Bank", b5B:"T-Bank", b5C:"Ozon Bank", b8A:"Plata", b8B:"Yandex Pay", b9A:"Plata", b9B:"Alfa-Bank", b9C:"Kaspi"};
const vis = key => ASSETS.crop[key] ? `<figure class="vis real" style="margin:0"><img src="${ASSETS.crop[key]}" alt="${esc(CROPBANK[key])} app screenshot" loading="lazy"><span class="sch">App · ${esc(CROPBANK[key])}</span></figure>`''',
     '''const CROPBANK = {b2A:"Yandex Pay", b3B:"Ozon Bank", b5A:"Ozon Bank", b5B:"T-Bank", b5C:"Ozon Bank", b7A:"Sber, for reference", b8A:"Plata", b8B:"Yandex Pay", b9A:"T-Bank", b9B:"Alfa-Bank", b9C:"Kaspi"};
const CROPTXT = {
  b2A:"Yandex Pay: “Select 5 out of 10 categories for October”; “1% All purchases” is one of the options.",
  b5A:"Ozon Bank: “Categories in September”, with brand partners among the 4 picks: 10% Globus, 50% Tasty Coffee.",
  b7A:"Sber (not one of the seven benchmark banks): “Your 5 categories in September. Can be changed from 1 October. Valid with SberPremier. 1% on all purchases, when paying by debit card.”",
  b9A:"T-Bank, Premium client: “Select 4 categories for October. More categories for you.” First option: 1% on all purchases."
};
const vis = key => ASSETS.crop[key] ? `<figure class="vis real" style="margin:0"${CROPTXT[key] ? ` title="${esc(CROPTXT[key])}"` : ""}><img src="${ASSETS.crop[key]}" alt="${esc(CROPTXT[key] || CROPBANK[key] + " app screenshot")}" loading="lazy"><span class="sch">App · ${esc(CROPBANK[key])}</span></figure>`'''),
    # sources without a link (the team's screenshots)
    ('''$("#srclist").innerHTML = Object.values(SRC).map(s => `<li><a href="${s.u}" target="_blank" rel="noopener">${esc(s.t)}</a>''',
     '''const srcLink = s => s.u ? `<a href="${s.u}" target="_blank" rel="noopener">${esc(s.t)}</a>` : esc(s.t);
$("#srclist").innerHTML = Object.values(SRC).map(s => `<li>${srcLink(s)}'''),
    ('''const srcList = keys => `<h4>Sources</h4><ol class="src">${keys.map(k => SRC[k]).map(s => `<li><a href="${s.u}" target="_blank" rel="noopener">${esc(s.t)}</a>''',
     '''const srcList = keys => `<h4>Sources</h4><ol class="src">${keys.map(k => SRC[k]).map(s => `<li>${srcLink(s)}'''),
    # sidebar screenshots: the team's app screenshots replace store images where they show the same thing
    ('''const SHOTDEF = {tbank:"tbank_pick", alfa:"alfa_wheel", ozon:"ozon_pick", yandex:"yandex_pick", kaspi:"kaspi_promo", plata:"plata_cats"};
const SHOTBLOCK = {tbank:{b5:"tbank_city"}, ozon:{b5:"ozon_disc", b8:"ozon_switch"}, yandex:{b3:"yandex_qr", b4:"yandex_qr", b5:"yandex_shops", b8:"yandex_qr", b10:"yandex_qr"}, kaspi:{b5:"kaspi_store"}, plata:{b8:"plata_home"}};
const SHOTCAP = {
  tbank_pick:"T-Bank: “Which 4 categories do you choose for November?”, with “1% on all purchases” among the options.",
  tbank_city:"T-Bank: everyday services with partner cashback (the 10% badges).",
  alfa_wheel:"Alfa-Bank: “Up to 100% cashback in the Supercashback wheel”.",
  ozon_pick:"Ozon Bank: “Cashback up to 25% in rubles, new categories every month”, with the pick-4 list.",
  ozon_disc:"Ozon Bank: “Discounts up to 30% on Ozon” for card holders.",
  ozon_switch:"Ozon Bank: switch between ruble cashback and “items for 1 ₽” at any time.",
  yandex_pick:"Yandex Pay: “Choose your benefit”, new cashback and discount categories every month.",''',
     '''const SHOTDEF = {tbank:"tb_prem", alfa:"alfa_wheel", ozon:"ozon_hub", yandex:"ya_pick5", kaspi:"kaspi_promo", plata:"plata_cats"};
const SHOTBLOCK = {ozon:{b3:"ozon_pick"}, yandex:{b4:"yandex_qr", b5:"yandex_shops", b7:"ya_home", b8:"yandex_qr", b9:"ya_home", b10:"yandex_qr"}, kaspi:{b5:"kaspi_store"}, plata:{b8:"plata_home"}};
const APPSHOT = new Set(["tb_prem", "ozon_hub", "ya_pick5", "ya_home"]);
const SHOTCAP = {
  tb_prem:"T-Bank, Premium client: “Select 4 categories for October”, “More categories for you”. Options: 1% on all purchases, 15% fuel and up to 25% shopping in T-Bank's City service, 5% on pharmacies, beauty, entertainment and sports goods.",
  ozon_hub:"Ozon Bank cashback screen: 0 ₽ “accumulating until 17 October” and a Limits button; September's 4 categories (1% on all purchases, 5% cosmetics, 10% Globus, 50% Tasty Coffee) with “You can choose again”; partner offers from more than 60 merchants.",
  ya_pick5:"Yandex Pay: “Select 5 out of 10 categories for October”. With the Pay card: 1% on all purchases and 3–10% categories and Yandex services. With any bank card: 100% in S7 and on car insurance.",
  ya_home:"Yandex Pay home screen: a card prompts “Select categories for October”, next to a banner to open a Super Split card.",
  alfa_wheel:"Alfa-Bank: “Up to 100% cashback in the Supercashback wheel”.",
  ozon_pick:"Ozon Bank: “Cashback up to 25% in rubles, new categories every month”, with the pick-4 list.",'''),
    ('''function appShot(bk, blockId) {
  const key = (SHOTBLOCK[bk] && blockId && SHOTBLOCK[bk][blockId]) || SHOTDEF[bk];
  if (!key) return `<div class="shot"><b>No public screenshot</b>Revolut's store listings don't show a RevPoints screen, and revolut.com blocks automated access.</div>`;
  return `<figure class="appshot"><img src="${ASSETS.shot[key]}" alt="${esc(SHOTCAP[key])}"><figcaption>${esc(SHOTCAP[key])} Store listing screenshot.</figcaption></figure>`;
}''', '''const shotKey = (bk, blockId) => (SHOTBLOCK[bk] && blockId && SHOTBLOCK[bk][blockId]) || SHOTDEF[bk];
const storeSrc = (bk, blockId) => STORE[bk] && !APPSHOT.has(shotKey(bk, blockId)) ? [STORE[bk]] : [];
function appShot(bk, blockId) {
  const key = shotKey(bk, blockId);
  if (!key) return `<div class="shot"><b>No public screenshot</b>Revolut's store listings don't show a RevPoints screen, and revolut.com blocks automated access.</div>`;
  return `<figure class="appshot"><img src="${ASSETS.shot[key]}" alt="${esc(SHOTCAP[key])}"><figcaption>${esc(SHOTCAP[key])} ${APPSHOT.has(key) ? "App screenshot, late September 2026." : "Store listing screenshot."}</figcaption></figure>`;
}'''),
    ('''    ${srcList(d.src.concat(STORE[bk] ? [STORE[bk]] : []))}`);''',
     '''    ${srcList([...new Set(d.src.concat(storeSrc(bk, blockId)))])}`);'''),
    ('''    ${srcList(keys.concat(STORE[bk] ? [STORE[bk]] : []))}`);''',
     '''    ${srcList(keys.concat(storeSrc(bk, null)))}`);'''),
    # reading note
    ("Pictures on the options are either app screenshots (labelled “App · bank”, from the banks’ public store listings) or schematic illustrations of the mechanic (labelled “Schematic”) where no bank screen shows it. The bank sidebars carry the store screenshots.",
     "Pictures on the options are either app screenshots (labelled “App · bank”: taken in the banks’ apps in late September 2026, or from their public store listings) or schematic illustrations of the mechanic (labelled “Schematic”) where no bank screen shows it. Hover over a screenshot for an English translation. Sber appears once, for reference; it is not one of the seven benchmark banks. The bank sidebars carry more screenshots."),
])
open('template_v4.html', 'w', encoding='utf-8').write(t)

page = (t.replace('/*DATA*/', d)
         .replace('/*ENGINE*/', open(f'{SP}/engine_page_data.json').read())
         .replace('/*ASSETS*/', open(f'{SP}/assets_v4.json').read()))
open('cashback-playbook.html', 'w', encoding='utf-8').write(page)
print('page bytes', len(page.encode('utf-8')))
