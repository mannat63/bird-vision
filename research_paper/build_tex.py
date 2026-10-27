"""Generate an editable IEEEtran LaTeX source + references.bib from paper_content.

The .tex uses an embedded thebibliography so it compiles without running BibTeX;
references.bib is also emitted for users who prefer \\bibliography. This source is
NOT compiled here (no TeX toolchain in the build environment); it is provided as
the editable deliverable. Build with: pdflatex x2 (e.g. on Overleaf).
Run:  python research_paper/build_tex.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import paper_content as C  # noqa: E402


def esc(t: str) -> str:
    """Escape LaTeX specials, then convert *italic* markup and [n] citations."""
    t = (t.replace("\\", r"\textbackslash{}").replace("&", r"\&")
          .replace("%", r"\%").replace("#", r"\#").replace("_", r"\_")
          .replace("$", r"\$"))
    # italic markup *...*
    def ital(m):
        return r"\textit{" + m.group(1) + "}"
    t = re.sub(r"\*(.+?)\*", ital, t)
    # citations [n] or [n], [m] -> \cite
    t = re.sub(r"\[(\d+)\]", lambda m: r"\cite{ref" + m.group(1) + "}", t)
    t = t.replace("->", r"$\rightarrow$").replace("+/-", r"$\pm$")
    t = t.replace("~", r"$\sim$")
    return t


def table_tex(label, caption, header, rows):
    ncol = len(header)
    colspec = "l" + "c" * (ncol - 1)
    lines = [r"\begin{table}[t]", r"\centering",
             r"\caption{" + caption + "}",
             r"\label{tab:" + label + "}",
             r"\footnotesize",
             r"\begin{tabular}{" + colspec + "}", r"\toprule",
             " & ".join(r"\textbf{" + esc(h) + "}" for h in header) + r" \\",
             r"\midrule"]
    for r in rows:
        lines.append(" & ".join(esc(str(c)) for c in r) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def main():
    out = []
    w = out.append
    w(r"\documentclass[conference]{IEEEtran}")
    w(r"\usepackage{graphicx,amsmath,amssymb,booktabs,url}")
    w(r"\usepackage[hidelinks]{hyperref}")
    w(r"\begin{document}")
    w(r"\title{" + C.TITLE + "}")
    a = C.AUTHORS[0]
    w(r"\author{\IEEEauthorblockN{" + a["name"] + r"}\IEEEauthorblockA{"
      + a["dept"] + r"\\" + a["org"] + r"\\" + a["extra"] + r"}}")
    w(r"\maketitle")
    w(r"\begin{abstract}")
    w(esc(C.ABSTRACT))
    w(r"\end{abstract}")
    w(r"\begin{IEEEkeywords}")
    w(esc(C.INDEX))
    w(r"\end{IEEEkeywords}")

    for b in C.BLOCKS:
        k = b[0]
        if k == "h1":
            w(r"\section{" + b[2].title() + "}")
        elif k == "h2":
            w(r"\subsection{" + b[2] + "}")
        elif k == "p":
            w(esc(b[1]))
        elif k == "runin":
            w(r"\textit{" + esc(b[1]) + "} " + esc(b[2]))
        elif k == "olist":
            w(r"\begin{enumerate}")
            for it in b[1]:
                w(r"\item " + esc(it))
            w(r"\end{enumerate}")
        elif k == "ulist":
            w(r"\begin{itemize}")
            for it in b[1]:
                w(r"\item " + esc(it))
            w(r"\end{itemize}")
        elif k == "eq":
            w(r"\begin{equation}")
            w(C.EQUATIONS[b[1]])
            w(r"\end{equation}")
        elif k == "fig":
            _, label, cap, img, wide = b
            env = "figure*" if wide else "figure"
            w(r"\begin{" + env + "}[t]")
            w(r"\centering")
            w(r"\includegraphics[width=" + ("\\textwidth" if wide else "\\columnwidth")
              + "]{figures/" + img + "}")
            w(r"\caption{" + esc(cap) + "}")
            w(r"\label{fig:" + label + "}")
            w(r"\end{" + env + "}")
        elif k == "table":
            _, label, cap, header, rows, wide = b
            w(table_tex(label, cap, header, rows))
        elif k == "codeavail":
            w(r"\section*{Code Availability}")
            w(esc(b[1]))

    # embedded bibliography
    w(r"\begin{thebibliography}{99}")
    for i, r in enumerate(C.REFERENCES, 1):
        w(r"\bibitem{ref" + str(i) + "} " + esc(r))
    w(r"\end{thebibliography}")
    w(r"\end{document}")

    (HERE / "birdvision_research_paper.tex").write_text("\n".join(out), encoding="utf-8")
    print("Wrote birdvision_research_paper.tex")

    # references.bib (misc entries; details identical to the thebibliography)
    bib = []
    for i, r in enumerate(C.REFERENCES, 1):
        bib.append("@misc{ref%d,\n  note = {%s}\n}" % (i, r.replace("{", "(").replace("}", ")")))
    (HERE / "references.bib").write_text("\n\n".join(bib), encoding="utf-8")
    print("Wrote references.bib")


if __name__ == "__main__":
    main()
