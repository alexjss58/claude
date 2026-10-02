"""MCC reference: official name, plain-English name, spend group and cashback category.

Official names follow the ISO 18245 / Visa-Mastercard MCC lists. Brand names for the carrier / hotel /
car-rental specific codes (3000-3999) are given only where the code-to-brand link is well known; the rest
are labelled generically and should be checked against the scheme table before any client-facing use.

Grouping (see CATEGORIES / GROUPS):
  * Spend group (level 1) follows the Revolut analytics groups (Groceries, Restaurants, Transport, ...).
  * Cashback category (level 2) follows the T-Bank pickable-category model: narrow, recognisable
    categories that a client can pick 4 of each month; 'OTH' earns only through the base option.
  * Excluded categories (X_*) follow the common exclusion list (T-Bank, Kaspi, the ArCa state programme):
    cash and quasi-cash, gambling, transfers / e-wallets, government, utilities, telecom, insurance, charity.
"""

# code -> (name, group, T-Bank analog, Kaspi partner-catalogue analog (indicative), in pickable pool)
CATEGORIES = {
    'SUP': ('Supermarkets & groceries', 'Groceries', 'Супермаркеты', 'Супермаркеты', True),
    'RES': ('Restaurants & bars', 'Restaurants', 'Рестораны', 'Кафе и рестораны', True),
    'FST': ('Fast food & coffee', 'Restaurants', 'Фастфуд', 'Кафе и рестораны', True),
    'DEL': ('Delivery & courier', 'Restaurants', 'Доставка (partner offers)', 'Доставка', True),
    'TAX': ('Taxi & ride-hailing', 'Transport', 'Такси', 'Такси', True),
    'TRN': ('Public transport & tolls', 'Transport', 'Местный транспорт', 'Транспорт', True),
    'FUE': ('Fuel, gas stations & EV charging', 'Transport', 'Топливо (АЗС)', 'АЗС', True),
    'AUT': ('Auto services & parking', 'Transport', 'Автоуслуги', 'Автотовары и СТО', True),
    'PHA': ('Pharmacies', 'Health & beauty', 'Аптеки', 'Аптеки', True),
    'MED': ('Medical & dental', 'Health & beauty', 'Медицина', 'Медицина', True),
    'BEA': ('Beauty & cosmetics', 'Health & beauty', 'Красота', 'Салоны красоты', True),
    'CLO': ('Clothing & shoes', 'Shopping', 'Одежда и обувь', 'Одежда и обувь', True),
    'ELE': ('Electronics & appliances', 'Shopping', 'Электроника / Бытовая техника', 'Электроника (Kaspi Магазин)', True),
    'HOM': ('Home & DIY', 'Home', 'Дом и ремонт', 'Товары для дома', True),
    'KID': ('Kids & toys', 'Shopping', 'Детские товары', 'Детские товары', True),
    'ENT': ('Entertainment & cinema', 'Entertainment', 'Развлечения / Кино', 'Развлечения', True),
    'SPO': ('Sport & fitness', 'Entertainment', 'Спорттовары / Спорт', 'Спорт', True),
    'TRV': ('Travel: airlines, hotels, rail, car rental', 'Travel', 'Авиабилеты / Отели / Ж/д / Аренда авто', 'Kaspi Travel', True),
    'ONL': ('Marketplaces, online shopping & digital', 'Shopping', 'Маркетплейсы / Цифровые товары', 'Kaspi Магазин', True),
    'JEW': ('Jewelry & watches', 'Shopping', 'Ювелирные изделия', 'Ювелирные изделия', True),
    'OTH': ('Other eligible purchases (base only)', 'Other', 'Все покупки (базовый кэшбэк)', 'Прочее', False),
    'X_CASH': ('EXCLUDED: cash withdrawals', 'Cash', 'не начисляется', 'не начисляется', False),
    'X_QCASH': ('EXCLUDED: quasi-cash, FX, crypto, pawn', 'Cash', 'не начисляется', 'не начисляется', False),
    'X_GAMB': ('EXCLUDED: gambling & lotteries', 'Gambling', 'не начисляется', 'не начисляется', False),
    'X_FIN': ('EXCLUDED: transfers, e-wallets, financial services', 'Financial & transfers', 'не начисляется', 'не начисляется', False),
    'X_GOV': ('EXCLUDED: government, taxes & fines', 'Government & taxes', 'не начисляется', 'не начисляется', False),
    'X_UTIL': ('EXCLUDED: utilities', 'Bills & utilities', 'не начисляется (ЖКХ)', 'не начисляется', False),
    'X_TEL': ('EXCLUDED: telecom & internet', 'Bills & utilities', 'не начисляется (связь)', 'не начисляется', False),
    'X_INS': ('EXCLUDED: insurance', 'Financial & transfers', 'не начисляется', 'не начисляется', False),
    'X_CHAR': ('EXCLUDED: charity, religious & political', 'Other', 'не начисляется', 'не начисляется', False),
    'X_OTH': ('EXCLUDED: rent, intra-company, adult', 'Other', 'не начисляется', 'не начисляется', False),
}
PICKABLE = [c for c, v in CATEGORIES.items() if v[4]]          # 20 pickable categories
ELIGIBLE = PICKABLE + ['OTH']

# mcc -> (official name, plain name, category)
M = {}


def add(codes, official, plain, cat):
    for c in (codes if isinstance(codes, (list, tuple, range)) else [codes]):
        M['%04d' % c] = (official, plain, cat)


# ---- carrier / hotel / car-rental specific ranges (generic first, brands override below)
add(range(3000, 3351), 'Airlines (carrier-specific code)', 'Airline tickets', 'TRV')
add(range(3351, 3501), 'Car rental agencies (brand-specific code)', 'Car rental', 'TRV')
add(range(3501, 4000), 'Hotels, motels, resorts (brand-specific code)', 'Hotels', 'TRV')
for code, brand in {3357: 'Hertz', 3381: 'Europcar', 3389: 'Avis', 3390: 'Dollar Rent A Car', 3405: 'Enterprise Rent-A-Car'}.items():
    add(code, f'Car rental – {brand}', f'Car rental ({brand})', 'TRV')
for code, brand in {3501: 'Holiday Inn', 3502: 'Best Western', 3503: 'Sheraton', 3504: 'Hilton', 3509: 'Marriott',
                    3510: 'Days Inn', 3512: 'InterContinental', 3513: 'Westin', 3520: 'Le Méridien', 3530: 'Renaissance',
                    3533: 'Ibis', 3535: 'Hilton International', 3543: 'Four Seasons', 3545: 'Shangri-La', 3553: 'Park Inn',
                    3579: 'Mercure', 3590: 'Fairmont', 3612: 'Mövenpick', 3640: 'Hyatt', 3641: 'Sofitel', 3642: 'Novotel',
                    3649: 'Radisson', 3665: 'Hampton Inn', 3692: 'DoubleTree', 3710: 'Ritz-Carlton'}.items():
    add(code, f'Hotels – {brand}', f'Hotel ({brand})', 'TRV')

# ---- agriculture, contractors, publishing
add(742, 'Veterinary Services', 'Vet clinics', 'OTH')
add(763, 'Agricultural Cooperatives', 'Agricultural cooperatives', 'OTH')
add(780, 'Landscaping and Horticultural Services', 'Landscaping & gardening services', 'HOM')
add([1520, 1711, 1731, 1740, 1750, 1761, 1771, 1799], 'Contractors (construction, plumbing, electrical, etc.)', 'Building & repair contractors', 'HOM')
add([2741, 2791], 'Publishing, Printing and Typesetting', 'Printing & publishing', 'OTH')
add(2842, 'Specialty Cleaning, Polishing and Sanitation Preparations', 'Cleaning supplies', 'HOM')

# ---- transport
add(4011, 'Railroads (freight)', 'Freight rail', 'OTH')
add(4111, 'Local and Suburban Commuter Passenger Transportation, incl. Ferries', 'Metro, buses, commuter transport', 'TRN')
add(4112, 'Passenger Railways', 'Train tickets', 'TRV')
add(4119, 'Ambulance Services', 'Ambulance', 'MED')
add(4121, 'Taxicabs and Limousines', 'Taxi & ride-hailing (Yandex Go, GG)', 'TAX')
add(4131, 'Bus Lines', 'Intercity buses', 'TRN')
add(4214, 'Motor Freight Carriers and Trucking', 'Trucking & moving', 'OTH')
add(4215, 'Courier Services – Air and Ground, Freight Forwarders', 'Courier & delivery services', 'DEL')
add(4225, 'Public Warehousing and Storage', 'Storage', 'OTH')
add(4411, 'Steamship and Cruise Lines', 'Cruises', 'TRV')
add(4457, 'Boat Rentals and Leasing', 'Boat rental', 'TRV')
add(4468, 'Marinas, Marine Service and Supplies', 'Marinas', 'TRV')
add(4511, 'Airlines and Air Carriers', 'Airline tickets', 'TRV')
add(4582, 'Airports, Flying Fields and Airport Terminals', 'Airport services', 'TRV')
add(4722, 'Travel Agencies and Tour Operators', 'Travel agencies & tours', 'TRV')
add(4784, 'Tolls and Bridge Fees', 'Road tolls', 'TRN')
add(4789, 'Transportation Services (not elsewhere classified)', 'Transport services (public transport, parking apps)', 'TRN')

# ---- telecom, utilities, financial
add(4812, 'Telecommunication Equipment and Telephone Sales', 'Phones & telecom equipment', 'ELE')
add(4814, 'Telecommunication Services', 'Mobile & phone bills', 'X_TEL')
add(4816, 'Computer Network / Information Services', 'Internet providers & online services', 'X_TEL')
add(4821, 'Telegraph Services', 'Telegraph services', 'X_TEL')
add(4899, 'Cable, Satellite and Other Pay Television and Radio Services', 'Cable / satellite TV', 'X_TEL')
add(4829, 'Wire Transfers and Money Orders', 'Money transfers', 'X_FIN')
add(4900, 'Utilities – Electric, Gas, Water and Sanitary', 'Utility bills', 'X_UTIL')
add(6010, 'Financial Institutions – Manual Cash Disbursements', 'Cash at bank counter', 'X_CASH')
add(6011, 'Financial Institutions – Automated Cash Disbursements', 'ATM cash withdrawal', 'X_CASH')
add(6012, 'Financial Institutions – Merchandise, Services and Debt Repayment', 'Bank payments, loan repayments, transfers', 'X_FIN')
add(6050, 'Quasi Cash – Member Financial Institution', 'Quasi-cash at banks', 'X_QCASH')
add(6051, 'Non-Financial Institutions – Foreign Currency, Money Orders, Travelers\' Cheques, Quasi-Cash', 'FX exchange, money orders, crypto', 'X_QCASH')
add(6211, 'Security Brokers / Dealers', 'Brokers & investments', 'X_FIN')
add(6300, 'Insurance Sales, Underwriting and Premiums', 'Insurance premiums', 'X_INS')
add(6381, 'Insurance Premiums', 'Insurance premiums', 'X_INS')
add(6513, 'Real Estate Agents and Managers – Rentals', 'Rent & real estate', 'X_OTH')
add([6529, 6530], 'Remote Stored Value Load', 'Stored-value loads', 'X_FIN')
add([6531, 6532, 6533, 6535, 6536, 6537, 6538], 'Payment / Money Transfer Transactions', 'Payment & money-send transactions', 'X_FIN')
add(6540, 'Non-Financial Institutions – Stored Value Card Purchase / Load', 'E-wallet top-ups (Idram, Telcell, etc.)', 'X_FIN')

# ---- wholesale / B2B-type codes
add(5013, 'Motor Vehicle Supplies and New Parts', 'Car parts', 'AUT')
add(5021, 'Office and Commercial Furniture', 'Office furniture', 'HOM')
add(5039, 'Construction Materials (not elsewhere classified)', 'Building materials', 'HOM')
add(5044, 'Office, Photographic, Photocopy and Microfilm Equipment', 'Office equipment', 'ELE')
add(5045, 'Computers, Computer Peripheral Equipment, Software', 'Computers & software', 'ELE')
add(5046, 'Commercial Equipment (not elsewhere classified)', 'Commercial equipment', 'OTH')
add(5047, 'Medical, Dental, Ophthalmic and Hospital Equipment and Supplies', 'Medical supplies', 'MED')
add(5051, 'Metal Service Centers and Offices', 'Metal products', 'OTH')
add(5065, 'Electrical Parts and Equipment', 'Electrical parts', 'ELE')
add(5072, 'Hardware Equipment and Supplies', 'Hardware supplies', 'HOM')
add(5074, 'Plumbing and Heating Equipment and Supplies', 'Plumbing & heating supplies', 'HOM')
add(5085, 'Industrial Supplies (not elsewhere classified)', 'Industrial supplies', 'OTH')
add(5094, 'Precious Stones and Metals, Watches and Jewelry', 'Jewelry & watches (wholesale)', 'JEW')
add(5099, 'Durable Goods (not elsewhere classified)', 'Durable goods', 'OTH')
add(5111, 'Stationery, Office Supplies, Printing and Writing Paper', 'Stationery', 'OTH')
add(5122, 'Drugs, Drug Proprietaries and Druggists\' Sundries', 'Pharmaceuticals', 'PHA')
add(5131, 'Piece Goods, Notions and Other Dry Goods', 'Fabrics & haberdashery', 'CLO')
add(5137, 'Men\'s, Women\'s and Children\'s Uniforms and Commercial Clothing', 'Uniforms & workwear', 'CLO')
add(5139, 'Commercial Footwear', 'Footwear (wholesale)', 'CLO')
add(5169, 'Chemicals and Allied Products (not elsewhere classified)', 'Chemicals', 'OTH')
add(5172, 'Petroleum and Petroleum Products', 'Fuel & gas stations (petroleum products)', 'FUE')
add(5192, 'Books, Periodicals and Newspapers', 'Books & press (wholesale)', 'OTH')
add(5193, 'Florists\' Supplies, Nursery Stock and Flowers', 'Plants & flowers (wholesale)', 'OTH')
add(5198, 'Paints, Varnishes and Supplies', 'Paints', 'HOM')
add(5199, 'Nondurable Goods (not elsewhere classified)', 'Non-durable goods', 'OTH')

# ---- retail
add(5200, 'Home Supply Warehouse Stores', 'Home improvement hypermarkets', 'HOM')
add(5211, 'Lumber and Building Materials Stores', 'Building materials stores', 'HOM')
add(5231, 'Glass, Paint and Wallpaper Stores', 'Paint & wallpaper stores', 'HOM')
add(5251, 'Hardware Stores', 'Hardware stores', 'HOM')
add(5261, 'Lawn and Garden Supply Stores', 'Garden centres', 'HOM')
add(5271, 'Mobile Home Dealers', 'Mobile home dealers', 'OTH')
add(5300, 'Wholesale Clubs', 'Wholesale clubs / cash & carry', 'SUP')
add(5309, 'Duty Free Stores', 'Duty free', 'TRV')
add(5310, 'Discount Stores', 'Discount stores', 'OTH')
add(5311, 'Department Stores', 'Department stores & malls', 'OTH')
add(5331, 'Variety Stores', 'Variety stores', 'OTH')
add(5399, 'Miscellaneous General Merchandise', 'General merchandise & marketplaces', 'ONL')
add(5411, 'Grocery Stores and Supermarkets', 'Supermarkets & grocery stores', 'SUP')
add(5422, 'Freezer and Locker Meat Provisioners', 'Butchers', 'SUP')
add(5441, 'Candy, Nut and Confectionery Stores', 'Confectionery', 'SUP')
add(5451, 'Dairy Products Stores', 'Dairy shops', 'SUP')
add(5462, 'Bakeries', 'Bakeries', 'SUP')
add(5499, 'Miscellaneous Food Stores – Convenience Stores and Specialty Markets', 'Convenience & specialty food stores', 'SUP')
add([5511, 5521], 'Car and Truck Dealers', 'Car dealers', 'OTH')
add(5531, 'Auto and Home Supply Stores', 'Auto supply stores', 'AUT')
add(5532, 'Automotive Tire Stores', 'Tyre shops', 'AUT')
add(5533, 'Automotive Parts and Accessories Stores', 'Auto parts & accessories', 'AUT')
add(5541, 'Service Stations (with or without Ancillary Services)', 'Petrol stations', 'FUE')
add(5542, 'Automated Fuel Dispensers', 'Self-service fuel pumps', 'FUE')
add([5551, 5561, 5571, 5592, 5598, 5599], 'Boat, Motorcycle, RV and Other Vehicle Dealers', 'Vehicle dealers (boats, motorcycles, RVs)', 'OTH')
add(5611, 'Men\'s and Boys\' Clothing and Accessories Stores', 'Men\'s clothing', 'CLO')
add(5621, 'Women\'s Ready-to-Wear Stores', 'Women\'s clothing', 'CLO')
add(5631, 'Women\'s Accessory and Specialty Shops', 'Women\'s accessories', 'CLO')
add(5641, 'Children\'s and Infants\' Wear Stores', 'Children\'s clothing', 'KID')
add(5651, 'Family Clothing Stores', 'Family clothing stores', 'CLO')
add(5655, 'Sports and Riding Apparel Stores', 'Sportswear', 'SPO')
add(5661, 'Shoe Stores', 'Shoe stores', 'CLO')
add(5681, 'Furriers and Fur Shops', 'Fur shops', 'CLO')
add(5691, 'Men\'s and Women\'s Clothing Stores', 'Clothing stores', 'CLO')
add(5697, 'Tailors, Alterations', 'Tailors', 'CLO')
add(5698, 'Wig and Toupee Stores', 'Wig shops', 'BEA')
add(5699, 'Miscellaneous Apparel and Accessory Shops', 'Apparel & accessories', 'CLO')
add(5712, 'Furniture, Home Furnishings and Equipment Stores', 'Furniture stores', 'HOM')
add(5713, 'Floor Covering Stores', 'Flooring', 'HOM')
add(5714, 'Drapery, Window Covering and Upholstery Stores', 'Curtains & upholstery', 'HOM')
add(5718, 'Fireplace, Fireplace Screens and Accessories Stores', 'Fireplaces', 'HOM')
add(5719, 'Miscellaneous Home Furnishing Specialty Stores', 'Home décor', 'HOM')
add(5722, 'Household Appliance Stores', 'Household appliances', 'ELE')
add(5732, 'Electronics Stores', 'Electronics stores', 'ELE')
add(5733, 'Music Stores – Musical Instruments, Pianos and Sheet Music', 'Musical instruments', 'ELE')
add(5734, 'Computer Software Stores', 'Software stores', 'ELE')
add(5735, 'Record Stores', 'Music record stores', 'ENT')
add(5811, 'Caterers', 'Caterers & banquets', 'RES')
add(5812, 'Eating Places and Restaurants', 'Restaurants', 'RES')
add(5813, 'Drinking Places (Bars, Taverns, Nightclubs)', 'Bars & nightclubs', 'RES')
add(5814, 'Fast Food Restaurants', 'Fast food & coffee shops', 'FST')
add(5815, 'Digital Goods – Media: Books, Movies, Music', 'Digital media (books, films, music)', 'ONL')
add(5816, 'Digital Goods – Games', 'Digital games & in-game purchases', 'ONL')
add(5817, 'Digital Goods – Applications (excl. Games)', 'Apps & app stores', 'ONL')
add(5818, 'Digital Goods – Large Digital Goods Merchant', 'Large digital stores (Apple, Google)', 'ONL')
add(5912, 'Drug Stores and Pharmacies', 'Pharmacies', 'PHA')
add(5921, 'Package Stores – Beer, Wine and Liquor', 'Liquor stores', 'OTH')
add(5931, 'Used Merchandise and Secondhand Stores', 'Second-hand stores', 'OTH')
add(5932, 'Antique Shops', 'Antiques', 'OTH')
add(5933, 'Pawn Shops', 'Pawn shops', 'X_QCASH')
add(5935, 'Wrecking and Salvage Yards', 'Salvage yards', 'OTH')
add(5937, 'Antique Reproductions', 'Antique reproductions', 'OTH')
add(5940, 'Bicycle Shops', 'Bicycle shops', 'SPO')
add(5941, 'Sporting Goods Stores', 'Sporting goods', 'SPO')
add(5942, 'Book Stores', 'Bookstores', 'OTH')
add(5943, 'Stationery, Office and School Supply Stores', 'Stationery & school supplies', 'OTH')
add(5944, 'Jewelry, Watch, Clock and Silverware Stores', 'Jewelry & watch stores', 'JEW')
add(5945, 'Hobby, Toy and Game Shops', 'Toy & hobby shops', 'KID')
add(5946, 'Camera and Photographic Supply Stores', 'Cameras & photo', 'ELE')
add(5947, 'Gift, Card, Novelty and Souvenir Shops', 'Gift & souvenir shops', 'OTH')
add(5948, 'Luggage and Leather Goods Stores', 'Luggage & leather goods', 'CLO')
add(5949, 'Sewing, Needlework, Fabric and Piece Goods Stores', 'Fabric & sewing', 'CLO')
add(5950, 'Glassware and Crystal Stores', 'Glassware & crystal', 'HOM')
add(5960, 'Direct Marketing – Insurance Services', 'Insurance (direct marketing)', 'X_INS')
add(5962, 'Direct Marketing – Travel-Related Arrangement Services', 'Travel (direct marketing)', 'TRV')
add(5963, 'Door-to-Door Sales', 'Door-to-door sales', 'OTH')
add([5964, 5965, 5966, 5967, 5968, 5969], 'Direct Marketing – Catalog, Telemarketing, Subscription and Other', 'Online / catalogue shopping & subscriptions', 'ONL')
add([5970, 5971, 5972, 5973], 'Art, Craft, Stamp, Coin and Religious Goods Stores', 'Art, crafts & collectibles', 'OTH')
add([5975, 5976], 'Hearing Aids and Orthopedic Goods', 'Hearing aids & orthopaedic goods', 'MED')
add(5977, 'Cosmetic Stores', 'Cosmetics & perfume stores', 'BEA')
add(5978, 'Typewriter Stores', 'Typewriter stores', 'OTH')
add(5983, 'Fuel Dealers (Fuel Oil, Wood, Coal, Liquefied Petroleum)', 'Fuel dealers (LPG, heating fuel)', 'FUE')
add(5992, 'Florists', 'Florists', 'OTH')
add(5993, 'Cigar Stores and Stands', 'Tobacco shops', 'OTH')
add(5994, 'News Dealers and Newsstands', 'Newsstands', 'OTH')
add(5995, 'Pet Shops, Pet Food and Supplies', 'Pet shops', 'OTH')
add([5996, 5997, 5998], 'Swimming Pool, Electric Razor, Tent and Awning Shops', 'Specialty home & outdoor shops', 'HOM')
add(5999, 'Miscellaneous and Specialty Retail Stores', 'Other specialty retail', 'OTH')

# ---- services
add(7011, 'Lodging – Hotels, Motels, Resorts', 'Hotels & resorts', 'TRV')
add(7012, 'Timeshares', 'Timeshares', 'TRV')
add([7032, 7033], 'Sporting / Recreational Camps, Trailer Parks and Campgrounds', 'Camps & campsites', 'TRV')
add([7210, 7211, 7216, 7217], 'Laundry, Dry Cleaning and Carpet Cleaning', 'Laundry & dry cleaning', 'OTH')
add(7221, 'Photographic Studios', 'Photo studios', 'OTH')
add(7230, 'Beauty and Barber Shops', 'Beauty salons & barbers', 'BEA')
add(7251, 'Shoe Repair, Shoe Shine and Hat Cleaning', 'Shoe repair', 'OTH')
add(7261, 'Funeral Services and Crematories', 'Funeral services', 'OTH')
add(7273, 'Dating and Escort Services', 'Dating & escort services', 'X_OTH')
add([7276, 7277, 7278], 'Tax Preparation, Counseling and Shopping Services', 'Personal services (tax prep, counselling)', 'OTH')
add(7296, 'Clothing Rental – Costumes, Uniforms, Formal Wear', 'Clothing rental', 'CLO')
add([7297, 7298], 'Massage Parlors, Health and Beauty Spas', 'Spas & massage', 'BEA')
add(7299, 'Miscellaneous Personal Services (not elsewhere classified)', 'Other personal services', 'OTH')
add([7311, 7321, 7333, 7338, 7339, 7342, 7349, 7361, 7392, 7393, 7394, 7395, 7399],
    'Business Services (advertising, cleaning, security, rental, consulting, etc.)', 'Business services', 'OTH')
add([7372, 7375, 7379], 'Computer Programming, Information Retrieval and Computer Services', 'IT services', 'OTH')
add(7512, 'Automobile Rental Agency', 'Car rental', 'TRV')
add([7513, 7519], 'Truck, Trailer and RV Rentals', 'Truck / RV rental', 'TRV')
add(7523, 'Parking Lots, Parking Meters and Garages', 'Parking', 'AUT')
add([7531, 7534, 7535, 7538], 'Automotive Body, Paint, Tire and Service Shops', 'Car repair & service', 'AUT')
add(7542, 'Car Washes', 'Car washes', 'AUT')
add(7549, 'Towing Services', 'Towing', 'AUT')
add([7622, 7623, 7629], 'Electronics, A/C and Small Appliance Repair Shops', 'Electronics & appliance repair', 'HOM')
add(7631, 'Watch, Clock and Jewelry Repair', 'Watch & jewelry repair', 'JEW')
add([7641, 7692, 7699], 'Furniture Repair, Welding and Miscellaneous Repair Shops', 'Repair services', 'HOM')
add(7829, 'Motion Picture and Video Tape Production and Distribution', 'Film production & distribution', 'ENT')
add(7832, 'Motion Picture Theaters', 'Cinemas', 'ENT')
add(7841, 'Video Tape Rental Stores', 'Video rental', 'ENT')
add(7911, 'Dance Halls, Studios and Schools', 'Dance studios', 'ENT')
add(7922, 'Theatrical Producers and Ticket Agencies', 'Theatre & event tickets', 'ENT')
add(7929, 'Bands, Orchestras and Miscellaneous Entertainers', 'Live entertainment', 'ENT')
add([7932, 7933], 'Billiard, Pool and Bowling Establishments', 'Billiards & bowling', 'ENT')
add(7941, 'Commercial Sports, Professional Sports Clubs, Athletic Fields', 'Sports events & clubs', 'SPO')
add(7991, 'Tourist Attractions and Exhibits', 'Museums & attractions', 'ENT')
add(7992, 'Public Golf Courses', 'Golf courses', 'SPO')
add([7993, 7994], 'Video Amusement Game Supplies and Arcades', 'Video arcades', 'ENT')
add(7995, 'Betting, incl. Lottery Tickets, Casino Gaming Chips, Off-Track Betting', 'Betting & online casinos', 'X_GAMB')
add(7996, 'Amusement Parks, Circuses, Carnivals and Fortune Tellers', 'Amusement parks', 'ENT')
add(7997, 'Membership Clubs (Sports, Recreation, Athletic), Country Clubs', 'Gyms & fitness clubs', 'SPO')
add(7998, 'Aquariums, Seaquariums and Dolphinariums', 'Aquariums', 'ENT')
add(7999, 'Recreation Services (not elsewhere classified)', 'Recreation & leisure', 'ENT')
add([7800, 7801, 7802, 9406], 'Government-Owned / Licensed Lotteries, Online Casinos and Racing', 'Lotteries & licensed gambling', 'X_GAMB')
add([8011, 8031, 8041, 8049, 8050, 8062, 8071, 8099], 'Doctors, Hospitals, Laboratories and Health Practitioners', 'Clinics, hospitals & labs', 'MED')
add(8021, 'Dentists and Orthodontists', 'Dentists', 'MED')
add([8042, 8043], 'Optometrists, Opticians and Optical Goods', 'Opticians & eyewear', 'MED')
add(8111, 'Legal Services and Attorneys', 'Lawyers', 'OTH')
add([8211, 8220, 8241, 8244, 8249, 8299], 'Schools, Universities and Educational Services', 'Education & courses', 'OTH')
add(8351, 'Child Care Services', 'Childcare & kindergartens', 'KID')
add([8398, 8641, 8651, 8661], 'Charitable, Civic, Political and Religious Organizations', 'Charity, religious & political', 'X_CHAR')
add([8675, 8699], 'Automobile Associations and Membership Organizations', 'Membership organisations', 'OTH')
add([8734, 8911, 8931, 8999], 'Testing, Engineering, Accounting and Professional Services', 'Professional services', 'OTH')
add([9211, 9222, 9223], 'Court Costs, Fines, Bail and Bond Payments', 'Fines & court payments', 'X_GOV')
add(9311, 'Tax Payments', 'Tax payments', 'X_GOV')
add(9399, 'Government Services (not elsewhere classified)', 'Government services & fees', 'X_GOV')
add([9402, 9405], 'Postal Services and Government Agencies', 'Postal & government agencies', 'X_GOV')
add(9950, 'Intra-Company Purchases', 'Intra-company purchases', 'X_OTH')
# newer scheme codes seen in the bank's data
add(5262, 'Marketplaces', 'Online marketplaces (Wildberries, Ozon, AliExpress-type)', 'ONL')
add(5552, 'Electric Vehicle Charging', 'EV charging stations', 'FUE')
add([69, 1503], 'Non-standard code in the bank\'s data', 'Non-standard code (negligible volume)', 'OTH')


def lookup(mcc):
    mcc = '%04d' % int(mcc)
    return M.get(mcc, ('Unknown MCC – add to map', 'Unknown', 'OTH'))
