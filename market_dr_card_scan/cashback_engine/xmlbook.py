"""Minimal XML-level access to a large .xlsx (no openpyxl round trip: keeps pivots, comments, metadata intact).

    wb = Book('model.xlsx')
    sh = wb.sheet('Control panel'); sh.f('D3', '1+1', s=978); sh.save()
    wb.write('out.xlsx')
"""
import re
import zipfile

from lxml import etree

M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
N = '{%s}' % M
RNS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG = '{http://schemas.openxmlformats.org/package/2006/relationships}'
CTN = '{http://schemas.openxmlformats.org/package/2006/content-types}'
X = lambda b: etree.fromstring(b, parser=etree.XMLParser(huge_tree=True))                          # noqa: E731
S = lambda e: etree.tostring(e, xml_declaration=True, encoding='UTF-8', standalone=True)           # noqa: E731


def col_key(ref):
    c = re.match(r'[A-Z]+', ref).group(0)
    return len(c), c


class Book:
    def __init__(self, path):
        z = zipfile.ZipFile(path)
        self.order = z.namelist()
        self.parts = {n: z.read(n) for n in self.order}

    # ---- sheets
    def sheet_map(self):
        rels = {r.get('Id'): r.get('Target') for r in X(self.parts['xl/_rels/workbook.xml.rels'])}
        out = []
        for s in X(self.parts['xl/workbook.xml']).find(N + 'sheets'):
            t = rels[s.get('{%s}id' % RNS)]
            out.append((s.get('name'), 'xl/' + t.lstrip('/').replace('xl/', '')))
        return out

    def sheet(self, name):
        return Sheet(self, dict(self.sheet_map())[name])

    def write(self, path):
        names = [n for n in self.order if n in self.parts] + [n for n in self.parts if n not in self.order]
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            for n in names:
                z.writestr(n, self.parts[n])


class Sheet:
    def __init__(self, book, part):
        self.book, self.part = book, part
        self.root = X(book.parts[part])
        self.data = self.root.find(N + 'sheetData')
        self.rows = {int(r.get('r')): r for r in self.data}

    def get(self, ref):
        r = self.rows.get(int(re.search(r'\d+', ref).group(0)))
        return None if r is None else next((c for c in r if c.get('r') == ref), None)

    def cell(self, ref):
        c = self.get(ref)
        if c is not None:
            return c
        rn = int(re.search(r'\d+', ref).group(0))
        row = self.rows.get(rn)
        if row is None:
            row = etree.Element(N + 'row', r=str(rn))
            prev = [x for x in self.rows if x < rn]
            (self.rows[max(prev)].addnext(row) if prev else self.data.insert(0, row))
            self.rows[rn] = row
        row.attrib.pop('spans', None)
        c = etree.Element(N + 'c', r=ref)
        for i, o in enumerate(row):
            if col_key(o.get('r')) > col_key(ref):
                row.insert(i, c)
                break
        else:
            row.append(c)
        return c

    def _reset(self, c, s):
        for ch in list(c):
            c.remove(ch)
        for a in ('t', 'cm', 'vm'):
            c.attrib.pop(a, None)
        if s is not None:
            c.set('s', str(s))

    def f(self, ref, formula, s=None):
        c = self.cell(ref)
        self._reset(c, s)
        etree.SubElement(c, N + 'f').text = formula

    def t(self, ref, text, s=None):
        c = self.cell(ref)
        self._reset(c, s)
        c.set('t', 'inlineStr')
        etree.SubElement(etree.SubElement(c, N + 'is'), N + 't').text = text

    def formula(self, ref):
        c = self.get(ref)
        f = None if c is None else c.find(N + 'f')
        return None if f is None else f.text

    def style(self, ref):
        c = self.get(ref)
        return None if c is None else c.get('s')

    def save(self):
        self.book.parts[self.part] = S(self.root)
