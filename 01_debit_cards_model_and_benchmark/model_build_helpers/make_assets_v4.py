"""assets.json (v3) + the team's September 2026 app screenshots -> assets_v4.json."""
import json, base64, io
from PIL import Image, ImageDraw
S = '/private/tmp/claude-501/-Users-suprunov-Documents-claude-fb/444d06dd-82fb-4e1b-8c91-b1f7bce70025'
IMG, CB = f'{S}/images/', f'{S}/scratchpad/cb/'
a = json.load(open(CB + 'assets.json'))

def b64(im, q):
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=q, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

def excerpt(name, bands, x0=0, x1=590, gap=8):
    """Stack horizontal bands of one screenshot; a dashed rule marks each cut."""
    im = Image.open(IMG + name).convert('RGB')
    parts = [im.crop((x0, y0, x1, y1)) for y0, y1 in bands]
    w = x1 - x0; h = sum(p.size[1] for p in parts) + gap * (len(parts) - 1)
    out = Image.new('RGB', (w, h), (22, 23, 26)); d = ImageDraw.Draw(out); y = 0
    for i, p in enumerate(parts):
        out.paste(p, (0, y)); y += p.size[1]
        if i < len(parts) - 1:
            for x in range(8, w - 8, 14): d.line([(x, y + gap // 2), (x + 7, y + gap // 2)], fill=(110, 115, 122), width=1)
            y += gap
    out = out.resize((480, round(h * 480 / w)), Image.LANCZOS)
    out.save(f'crop_{name.split(".")[0]}.png')
    print(name, 'crop', out.size, round(out.size[0] / out.size[1], 2))
    return b64(out, 84)

def full(name):
    im = Image.open(IMG + name).convert('RGB')
    im = im.resize((320, round(im.size[1] * 320 / im.size[0])), Image.LANCZOS)
    return b64(im, 80)

# option pictures (key = block + pathway)
a['crop']['b2A'] = excerpt('8.jpg', [(200, 305), (428, 500)])            # Yandex: Select 5 of 10 · 1% All purchases
a['crop']['b5A'] = excerpt('11.jpg', [(312, 360), (645, 815)], x1=575)   # Ozon: September categories · Globus 10% · Tasty Coffee 50%
a['crop']['b7A'] = excerpt('10.jpg', [(165, 252), (292, 440)])           # Sber: Your 5 categories · change from 1 Oct · 1% all purchases
a['crop']['b9A'] = excerpt('9.jpg', [(198, 366), (408, 468)])            # T-Bank: Select 4 for October · Premium · 1% all purchases
a['crop'].pop('b2C', None)                                               # the old Yandex pathway is gone

# sidebar screenshots
a['shot'].update(tb_prem=full('9.jpg'), ya_pick5=full('8.jpg'), ya_home=full('7.jpg'), ozon_hub=full('11.jpg'))
for k in ['tbank_pick', 'tbank_city', 'yandex_pick', 'ozon_disc', 'ozon_switch']:
    a['shot'].pop(k)

json.dump(a, open(CB + 'assets_v4.json', 'w'))
print({k: len(v) for k, v in a.items()}, 'bytes', len(json.dumps(a)))