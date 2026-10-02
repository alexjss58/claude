import zipfile, re, numpy as np, time
from lxml import etree
z=zipfile.ZipFile('fr.xlsx')
M='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ss=[''.join(si.itertext()) for si in etree.fromstring(z.read('xl/sharedStrings.xml')).iter(M+'si')]
def colnum(s):
    n=0
    for ch in s: n=n*26+ord(ch)-64
    return n-1
hdr=None; rows=[]; t=time.time()
for ev,row in etree.iterparse(z.open('xl/worksheets/sheet1.xml'),tag=M+'row',huge_tree=True):
    if hdr is None:
        hdr={}
        for c in row:
            v=c.find(M+'v'); val=v.text
            if c.get('t')=='s': val=ss[int(val)]
            hdr[colnum(re.match('[A-Z]+',c.get('r')).group())]=val
        ncol=max(hdr)+1
    else:
        arr=np.full(ncol,np.nan)
        for c in row:
            v=c.find(M+'v')
            if v is not None:
                try: arr[colnum(re.match('[A-Z]+',c.get('r')).group())]=float(v.text)
                except: pass
        rows.append(arr)
    row.clear()
    while row.getprevious() is not None: del row.getparent()[0]
    if len(rows)%100000==0 and rows: print(len(rows), time.time()-t, flush=True)
A=np.vstack(rows)
names=[hdr[i] for i in range(ncol)]
np.savez_compressed('fr.npz',A=A,names=np.array(names))
print('done',A.shape,time.time()-t)