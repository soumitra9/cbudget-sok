MAIN = main
LATEX = pdflatex
BIBTEX = bibtex
export TEXINPUTS := .:./texmf/tex/latex/sttools//:./texmf/tex/latex/threeparttable//:./texmf/tex/latex/appendix//:./texmf/tex/latex/wrapfig//:
export BIBINPUTS := .:./bst//:

.PHONY: all clean figures

all: $(MAIN).pdf

figures:
	cd figures/scripts && bash generate_all.sh

$(MAIN).pdf: $(MAIN).tex references.bib sn-jnl.cls sn-basic.bst Fig1.pdf Fig2.pdf Fig3.pdf Fig4.pdf Fig5.pdf Fig6.pdf
	$(LATEX) $(MAIN)
	$(BIBTEX) $(MAIN)
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out $(MAIN).pdf $(MAIN).synctex.gz
