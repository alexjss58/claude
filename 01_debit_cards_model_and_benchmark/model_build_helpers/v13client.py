import zipfile,re,pandas as pd
from lxml import etree
z=zipfile.ZipFile('/Users/suprunov/Downloads/20260924_Debit_cards_model_v13.xlsx')
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
hdr=dict(l.rstrip('\n').split('\t') for l in open('v13_header.txt'))
want={k:v for k,v in hdr.items() if v in ('client_id','card_sub_segment','gold_backed_loan_holder','card_type_group') or re.match(r'(debit|credit)_txn_count_2026-0[678]$',v)}
print(want)
ss=[]
for ev,el in etree.iterparse(z.open('xl/sharedStrings.xml'),tag=X+'si'):
    ss.append(''.join(x.text or '' for x in el.iter(X+'t'))); el.clear()
out=[]
for ev,el in etree.iterparse(z.open('xl/worksheets/sheet22.xml'),tag=X+'row',huge_tree=True):
    if int(el.get('r'))>2:
        d={}
        for c in el:
            col=re.match('[A-Z]+',c.get('r')).group()
            if col in want:
                v=c.find(X+'v'); val=v.text if v is not None else None
                if c.get('t')=='s' and val is not None: val=ss[int(val)]
                d[want[col]]=val
        out.append(d)
    el.clear()
    while el.getprevious() is not None: del el.getparent()[0]
df=pd.DataFrame(out); df.to_pickle('v13client.pkl'); print(df.shape); print(df.head())