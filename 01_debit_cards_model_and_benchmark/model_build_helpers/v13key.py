import zipfile,re,pandas as pd
from lxml import etree
z=zipfile.ZipFile('/Users/suprunov/Downloads/20260924_Debit_cards_model_v13.xlsx')
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ss=[]
for ev,el in etree.iterparse(z.open('xl/sharedStrings.xml'),tag=X+'si'):
    ss.append(''.join(x.text or '' for x in el.iter(X+'t'))); el.clear()
hdr=None; out=[]
KEEP=None
for ev,el in etree.iterparse(z.open('xl/worksheets/sheet22.xml'),tag=X+'row',huge_tree=True):
    rn=int(el.get('r'))
    d={}
    for c in el:
        col=re.match('[A-Z]+',c.get('r')).group()
        v=c.find(X+'v'); val=v.text if v is not None else None
        if c.get('t')=='s' and val is not None: val=ss[int(val)]
        d[col]=val
    if rn==2:
        hdr=d
        open('v13_header.txt','w').write('\n'.join(f'{k}\t{v}' for k,v in d.items()))
        KEEP={k:v for k,v in d.items() if v in ('contract_id','card_issued','card_of_record','in_analysis','card_type_group','card_type_detail_en','card_currency','card_sub_segment','segment','gold_backed_loan_holder','card_activated','reissue_role')}
    elif rn>2:
        out.append({KEEP[k]:d.get(k) for k in KEEP})
    el.clear()
    while el.getprevious() is not None: del el.getparent()[0]
df=pd.DataFrame(out); df.to_pickle('v13key.pkl'); print(df.shape); print(df.head()); print(df.card_type_group.value_counts())