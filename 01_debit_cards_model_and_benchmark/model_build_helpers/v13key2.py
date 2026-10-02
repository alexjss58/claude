import zipfile,re,pandas as pd
from lxml import etree
z=zipfile.ZipFile('/Users/suprunov/Downloads/20260924_Debit_cards_model_v13.xlsx')
X='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ss=[]
for ev,el in etree.iterparse(z.open('xl/sharedStrings.xml'),tag=X+'si'):
    ss.append(''.join(x.text or '' for x in el.iter(X+'t'))); el.clear()
COLS={'A':'contract_id','D':'card_issued','E':'issue_month','I':'card_of_record','M':'card_type_group','P':'card_currency','AK':'card_sub_segment','BB':'b6','BC':'b7','BD':'b8'}
out=[]
for ev,el in etree.iterparse(z.open('xl/worksheets/sheet22.xml'),tag=X+'row',huge_tree=True):
    rn=int(el.get('r'))
    if rn>2:
        d={}
        for c in el:
            col=re.match('[A-Z]+',c.get('r')).group()
            if col in COLS:
                v=c.find(X+'v'); val=v.text if v is not None else None
                if c.get('t')=='s' and val is not None: val=ss[int(val)]
                d[COLS[col]]=val
        out.append(d)
    el.clear()
    while el.getprevious() is not None: del el.getparent()[0]
pd.DataFrame(out).to_pickle('v13key2.pkl')