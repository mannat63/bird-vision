"""Render the BirdVision AI paper to a two-column IEEE-style PDF with reportlab.

Content comes from paper_content.py; figures and equation images from figures/.
Run:  python research_paper/build_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, FrameBreak, Image, NextPageTemplate, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
sys.path.insert(0, str(HERE))
import paper_content as C  # noqa: E402

# ---- page geometry -------------------------------------------------------- #
PW, PH = letter
ML = MR = 44
MT = 48
MB = 46
GUT = 16
COLW = (PW - ML - MR - GUT) / 2        # 254
BAND_H = 150
band_y = PH - MT - BAND_H
col_top = band_y - 8
col_h_first = col_top - MB
col_h = (PH - MT) - MB
RX = ML + COLW + GUT

# ---- styles --------------------------------------------------------------- #
SER = "Times-Roman"
def style(name, **kw):
    base = dict(fontName=SER, fontSize=9, leading=10.6, alignment=TA_JUSTIFY,
                spaceAfter=4)
    base.update(kw)
    return ParagraphStyle(name, **base)

S = {
    "title": style("title", fontName="Times-Roman", fontSize=17.5, leading=20,
                   alignment=TA_CENTER, spaceAfter=10),
    "author": style("author", fontSize=10, leading=12.5, alignment=TA_CENTER,
                    spaceAfter=2),
    "abstract": style("abstract", fontName="Times-Bold", fontSize=9, leading=10.8),
    "index": style("index", fontName="Times-Bold", fontSize=9, leading=10.8,
                   spaceAfter=6),
    "h1": style("h1", fontName="Times-Roman", fontSize=9.5, leading=12,
                alignment=TA_CENTER, spaceBefore=8, spaceAfter=4),
    "h2": style("h2", fontName="Times-Italic", fontSize=9.5, leading=12,
                alignment=TA_LEFT, spaceBefore=5, spaceAfter=3),
    "body": style("body", firstLineIndent=10),
    "body0": style("body0"),
    "cap": style("cap", fontSize=8, leading=9.4, alignment=TA_JUSTIFY,
                 spaceBefore=3, spaceAfter=6),
    "tabcap": style("tabcap", fontSize=8, leading=9.4, alignment=TA_CENTER,
                    spaceBefore=4, spaceAfter=2),
    "tabnum": style("tabnum", fontSize=8, leading=9.4, alignment=TA_CENTER),
    "cell": style("cell", fontSize=7.3, leading=8.4, alignment=TA_LEFT,
                  spaceAfter=0),
    "cellc": style("cellc", fontSize=7.3, leading=8.4, alignment=TA_CENTER,
                   spaceAfter=0),
    "cellh": style("cellh", fontName="Times-Bold", fontSize=7.3, leading=8.4,
                   alignment=TA_LEFT, spaceAfter=0),
    "cellhc": style("cellhc", fontName="Times-Bold", fontSize=7.3, leading=8.4,
                    alignment=TA_CENTER, spaceAfter=0),
    "ref": style("ref", fontSize=8, leading=9.3, firstLineIndent=-10,
                 leftIndent=10, spaceAfter=2),
    "li": style("li", firstLineIndent=0, leftIndent=12, spaceAfter=3),
}


def inline(text: str) -> str:
    """Convert *italic* markup to reportlab <i> tags; leave [n] citations."""
    out, i, ital = [], 0, False
    for ch in text:
        if ch == "*":
            out.append("</i>" if ital else "<i>")
            ital = not ital
        else:
            out.append(ch)
    return "".join(out)


def img_flowable(path: Path, max_w: float):
    iw, ih = PILImage.open(path).size
    w = min(max_w, iw * 72 / 300.0)   # assume 300 dpi source, cap at max_w
    scale = w / iw
    return Image(str(path), width=w, height=ih * scale)


def eq_flowable(n: int):
    """Centered equation image with a right-aligned number, within the column."""
    img = img_flowable(FIG / f"eq{n}.png", COLW - 34)
    t = Table([[img, Paragraph(f"({n})", S["tabnum"])]],
              colWidths=[COLW - 30, 30])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def make_table(label, caption, header, rows):
    ncol = len(header)
    cw = COLW / ncol
    # header centered-bold, first column left, numeric columns centered
    data = [[Paragraph(h, S["cellhc"]) for h in header]]
    for r in rows:
        cells = []
        for j, c in enumerate(r):
            st = S["cell"] if j == 0 else S["cellc"]
            cells.append(Paragraph(str(c), st))
        data.append(cells)
    t = Table(data, colWidths=[cw] * ncol, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.0, black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, black),
        ("LINEBELOW", (0, -1), (-1, -1), 1.0, black),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return [
        Paragraph(f"TABLE {label}", S["tabcap"]),
        Paragraph(caption.upper(), S["tabcap"]),
        t,
        Spacer(1, 6),
    ]


def build():
    story = [NextPageTemplate("later")]

    # --- title band ---
    story.append(Paragraph(C.TITLE, S["title"]))
    for a in C.AUTHORS:
        story.append(Paragraph(f"<b>{a['name']}</b>", S["author"]))
        story.append(Paragraph(a["dept"], S["author"]))
        story.append(Paragraph(a["org"], S["author"]))
        story.append(Paragraph(a["extra"], S["author"]))
    story.append(FrameBreak())   # jump to first text column

    # --- abstract + index terms ---
    story.append(Paragraph("<b><i>Abstract</i></b>&mdash;" + C.ABSTRACT,
                           S["abstract"]))
    story.append(Spacer(1, 3))
    story.append(Paragraph("<b><i>Index Terms</i></b>&mdash;" + C.INDEX,
                           S["index"]))

    # --- body ---
    for b in C.BLOCKS:
        kind = b[0]
        if kind == "h1":
            story.append(Paragraph(f"{b[1]}.&nbsp;&nbsp;{b[2]}", S["h1"]))
        elif kind == "h2":
            story.append(Paragraph(f"<i>{b[1]}. {b[2]}</i>", S["h2"]))
        elif kind == "p":
            story.append(Paragraph(inline(b[1]), S["body"]))
        elif kind == "runin":
            story.append(Paragraph(f"<i>{b[1]}</i> " + inline(b[2]), S["body"]))
        elif kind == "olist":
            for i, it in enumerate(b[1], 1):
                story.append(Paragraph(f"{i})&nbsp; " + inline(it), S["li"]))
        elif kind == "ulist":
            for it in b[1]:
                story.append(Paragraph("&bull;&nbsp; " + inline(it), S["li"]))
        elif kind == "eq":
            story.append(eq_flowable(b[1]))
        elif kind == "fig":
            _, label, cap, img, wide = b
            story.append(Spacer(1, 2))
            story.append(img_flowable(FIG / img, COLW))
            story.append(Paragraph(f"<b>Fig. {label}.</b> " + cap, S["cap"]))
        elif kind == "table":
            _, label, cap, header, rows, wide = b
            for fl in make_table(label, cap, header, rows):
                story.append(fl)
        elif kind == "codeavail":
            story.append(Paragraph("<i>Code Availability.</i> " + inline(b[1]),
                                   S["body"]))

    # --- references ---
    story.append(Paragraph("REFERENCES", S["h1"]))
    for i, r in enumerate(C.REFERENCES, 1):
        story.append(Paragraph(f"[{i}]&nbsp; {r}", S["ref"]))

    # --- document with frames ---
    doc = BaseDocTemplate(
        str(HERE / "birdvision_research_paper.pdf"), pagesize=letter,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title="BirdVision AI", author="BirdVision AI")

    band = Frame(ML, band_y, PW - ML - MR, BAND_H, id="band",
                 leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    l1 = Frame(ML, MB, COLW, col_h_first, id="l1", leftPadding=0, rightPadding=0)
    r1 = Frame(RX, MB, COLW, col_h_first, id="r1", leftPadding=0, rightPadding=0)
    l2 = Frame(ML, MB, COLW, col_h, id="l2", leftPadding=0, rightPadding=0)
    r2 = Frame(RX, MB, COLW, col_h, id="r2", leftPadding=0, rightPadding=0)

    doc.addPageTemplates([
        PageTemplate(id="first", frames=[band, l1, r1]),
        PageTemplate(id="later", frames=[l2, r2]),
    ])
    doc.build(story)
    print("PDF written:", HERE / "birdvision_research_paper.pdf")


if __name__ == "__main__":
    build()
