"""Чтение документов: docx, pdf, xlsx/xls, csv, txt -> список блоков (абзацы и таблицы) в порядке документа."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED = {".docx", ".pdf", ".xlsx", ".xlsm", ".xls", ".txt", ".csv", ".md"}


@dataclass
class Doc:
    path: str
    blocks: list = field(default_factory=list)   # ("p", str) | ("t", list[list[str]])

    def text(self) -> str:
        out = []
        for kind, b in self.blocks:
            if kind == "p":
                out.append(b)
            else:
                for row in b:
                    out.append(" | ".join(c for c in row if c))
        return "\n".join(out)


def _clean(s) -> str:
    if s is None:
        return ""
    s = str(s).replace(" ", " ").replace("\r", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    return s.strip()


def _dedupe_row(cells: list[str]) -> list[str]:
    """python-docx повторяет текст объединённой ячейки — убираем подряд идущие дубли."""
    out = []
    for c in cells:
        if out and c == out[-1] and c:
            continue
        out.append(c)
    return out


def read_docx(path: Path) -> Doc:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    d = docx.Document(str(path))
    doc = Doc(str(path))
    body = d.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            t = _clean(Paragraph(child, d).text)
            if t:
                doc.blocks.append(("p", t))
        elif tag == "tbl":
            tbl = Table(child, d)
            rows = []
            for r in tbl.rows:
                try:
                    cells = [_clean(c.text) for c in r.cells]
                except Exception:
                    continue
                rows.append(cells)
            if rows:
                doc.blocks.append(("t", rows))
    return doc


def read_pdf(path: Path) -> Doc:
    import pdfplumber

    doc = Doc(str(path))
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            tables = page.find_tables()
            bboxes = [t.bbox for t in tables]

            def outside(obj, bb=bboxes):
                x0, top, x1, bottom = obj.get("x0", 0), obj.get("top", 0), obj.get("x1", 0), obj.get("bottom", 0)
                for (a, b, c, d) in bb:
                    if x0 >= a - 1 and x1 <= c + 1 and top >= b - 1 and bottom <= d + 1:
                        return False
                return True

            txt = page.filter(outside).extract_text() or ""
            # текст до таблиц, затем таблицы (для ТЗ этого порядка достаточно)
            for line in txt.split("\n"):
                line = _clean(line)
                if line:
                    doc.blocks.append(("p", line))
            for t in tables:
                rows = [[_clean(c) for c in row] for row in t.extract()]
                rows = [r for r in rows if any(r)]
                if rows:
                    doc.blocks.append(("t", rows))
    # таблица, продолженная на следующей странице без шапки, — склеиваем
    merged: list = []
    for kind, b in doc.blocks:
        if kind == "t" and merged and merged[-1][0] == "t" and len(b[0]) == len(merged[-1][1][0]) \
                and not re.search(r"наименован|характерист|значени", " ".join(b[0]).lower()):
            merged[-1][1].extend(b)
        else:
            merged.append((kind, b))
    doc.blocks = merged
    return doc


def read_xlsx(path: Path) -> Doc:
    import pandas as pd

    doc = Doc(str(path))
    xl = pd.ExcelFile(path)
    for sh in xl.sheet_names:
        df = pd.read_excel(xl, sh, header=None, dtype=str)
        rows = []
        for _, r in df.iterrows():
            cells = [_clean(x) if str(x) != "nan" else "" for x in r.tolist()]
            if any(cells):
                rows.append(cells)
        if not rows:
            continue
        # строки с одной заполненной ячейкой до таблицы — это абзацы (заголовки)
        i = 0
        while i < len(rows) and sum(bool(c) for c in rows[i]) == 1:
            doc.blocks.append(("p", next(c for c in rows[i] if c)))
            i += 1
        if i < len(rows):
            doc.blocks.append(("t", rows[i:]))
    return doc


def read_txt(path: Path) -> Doc:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    doc = Doc(str(path))
    table: list = []
    for line in text.splitlines():
        sep = "\t" if "\t" in line else ("|" if line.count("|") >= 2 else None)
        if sep:
            cells = [_clean(c) for c in line.strip().strip("|").split(sep)]
            if re.fullmatch(r"[-:| ]+", line.strip()):
                continue
            table.append(cells)
            continue
        if table:
            doc.blocks.append(("t", table))
            table = []
        t = _clean(line)
        if t:
            doc.blocks.append(("p", t))
    if table:
        doc.blocks.append(("t", table))
    return doc


def read_document(path: str | Path) -> Doc:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".docx":
        return read_docx(p)
    if ext == ".pdf":
        return read_pdf(p)
    if ext in (".xlsx", ".xlsm", ".xls"):
        return read_xlsx(p)
    if ext in (".txt", ".md", ".csv"):
        return read_txt(p)
    if ext == ".doc":
        raise ValueError("формат .doc (старый Word) не поддерживается — пересохраните файл в .docx")
    raise ValueError(f"неподдерживаемый формат: {ext}")
