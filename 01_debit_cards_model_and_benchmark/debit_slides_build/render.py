import sys
from pptx import Presentation
from pptx.util import Emu
from PIL import Image, ImageDraw, ImageFont
prs=Presentation(sys.argv[1]); idx=int(sys.argv[2]); out=sys.argv[3]
s=prs.slides[idx]; W,H=prs.slide_width,prs.slide_height; SC=1600/W
im=Image.new('RGB',(1600,int(H*SC)),'white'); d=ImageDraw.Draw(im)
px=lambda v:int(v*SC)
def col(sh):
    try:
        if sh.fill.type==1: return '#'+str(sh.fill.fore_color.rgb)
    except Exception: pass
    return None
def lcol(sh):
    try: return '#'+str(sh.line.color.rgb)
    except Exception: return None
for sh in s.shapes:
    if sh.shape_type==7: continue
    x,y,w,h=px(sh.left or 0),px(sh.top or 0),px(sh.width or 0),px(sh.height or 0)
    tag=sh._element.tag.split('}')[1]
    if tag=='cxnSp':
        c=lcol(sh) or '#999'; d.line([x,y,x+w,y+h],fill=c,width=max(1,int((sh.line.width or 9525)*SC/9000)))
        continue
    geom=sh._element.xpath('.//a:prstGeom/@prst')
    f=col(sh); lc=lcol(sh) if geom else None
    if geom and (f or lc):
        g=geom[0]
        if g=='ellipse': d.ellipse([x,y,x+w,y+h],fill=f,outline=lc)
        elif g=='diamond': d.polygon([(x+w/2,y),(x+w,y+h/2),(x+w/2,y+h),(x,y+h/2)],fill=f)
        elif g=='roundRect': d.rounded_rectangle([x,y,x+w,y+h],radius=12,fill=f)
        else: d.rectangle([x,y,x+w,y+h],fill=f,outline=lc)
    if sh.has_text_frame and sh.text_frame.text.strip():
        ty=y
        for p in sh.text_frame.paragraphs:
            txt=''.join(r.text for r in p.runs)
            if not txt: continue
            r0=p.runs[0]; sz=(r0.font.size.pt if r0.font.size else 14 if 'Subtitle' not in sh.name else 16)
            if 'Title' in sh.name and sh.is_placeholder: sz=24
            fn='segoesb.ttf' if (r0.font.name or '').endswith('Semibold') or 'Title' in sh.name else 'segoe.ttf'
            font=ImageFont.truetype(fn, max(8,int(sz*12700*SC)))
            try: c='#'+str(r0.font.color.rgb)
            except Exception: c='#000000'
            # wrap
            words=txt.split(' '); lines=[]; cur=''
            for wd in words:
                t=(cur+' '+wd).strip()
                if d.textlength(t,font=font)<=w+2 or not cur: cur=t
                else: lines.append(cur); cur=wd
            lines.append(cur)
            for ln in lines:
                al=p.alignment
                tw=d.textlength(ln,font=font)
                xx=x+w-tw if al is not None and int(al)==3 else (x+(w-tw)/2 if al is not None and int(al)==2 else x)
                d.text((xx,ty),ln,font=font,fill=c); ty+=int(sz*12700*SC*1.3)
            if ty>y+h+4 and 'Footnote' not in sh.name: d.rectangle([x,y,x+w,ty],outline='red')
im.save(out); print(out, im.size)