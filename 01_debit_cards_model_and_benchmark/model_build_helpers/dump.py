"""Print cells (value + formula) of one sheet of a large .xlsx without openpyxl.
    python3 dump.py <book.xlsx>                      -> list sheet names
    python3 dump.py <book.xlsx> "<sheet>" <r0> <r1>   -> cells of rows r0..r1
Also importable: open_book(path) -> (zip, {sheet: part}, shared strings); cells(zip, part, ss, rows=None)
"""
import zipfile, sys, re
from lxml import etree
ns = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main', 'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
M = '{%s}' % ns['m']


def open_book(p):
    z = zipfile.ZipFile(p)
    wb = etree.fromstring(z.read('xl/workbook.xml')); rels = etree.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    tgt = {r.get('Id'): r.get('Target') for r in rels}
    sheets = {s.get('name'): 'xl/' + tgt[s.get('{%s}id' % ns['r'])].replace('/xl/', '').lstrip('/') for s in wb.find('m:sheets', ns)}
    ss = [''.join(si.itertext()) for si in etree.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', ns)]
    return z, sheets, ss


def cells(z, part, ss, rows=None):
    out = {}
    for ev, c in etree.iterparse(z.open(part), tag=M + 'c', huge_tree=True):
        ref = c.get('r'); rn = int(re.search(r'\d+', ref).group())
        if rows is None or rn in rows:
            v = c.find(M + 'v'); f = c.find(M + 'f'); isv = c.find(M + 'is')
            val = v.text if v is not None else (''.join(isv.itertext()) if isv is not None else None)
            if c.get('t') == 's' and val is not None:
                val = ss[int(val)]
            out[ref] = (val, f.text if f is not None else None, f.get('ref') if f is not None else None, f.get('si') if f is not None else None)
        c.clear()
    return out


if __name__ == '__main__':
    z, sheets, ss = open_book(sys.argv[1])
    if len(sys.argv) < 3:
        print(list(sheets)); sys.exit()
    sh = sys.argv[2]; r0, r1 = int(sys.argv[3]), int(sys.argv[4])
    cs = cells(z, sheets[sh], ss, set(range(r0, r1 + 1)))
    def key(r):
        m = re.match(r'([A-Z]+)(\d+)', r); c = m.group(1); return (int(m.group(2)), len(c), c)
    for ref in sorted(cs, key=key):
        v, f, rf, si = cs[ref]
        if v is None and f is None:
            continue
        print(ref, repr(v)[:60], ('=' + f[:140]) if f else '')
