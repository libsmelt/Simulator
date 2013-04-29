###########################################################
#
# Makefile for LaTeX docs
#

DEPS=$(wildcard plots/*/*.pdf) $(wildcard figures/*.pdf)

PAPER=paper
LATEXOPTS=-interaction=nonstopmode

all: pdf

pdf: $(PAPER).pdf

$(PAPER).pdf: $(wildcard *.tex) $(wildcard *.bib) $(DEPS)
	pdflatex $(LATEXOPTS) $(PAPER)
	if egrep '\\cite' $(PAPER).tex ; then bibtex $(PAPER) ; fi
	if [ -e $(PAPER).toc ] ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if [ -e $(PAPER).bbl ] ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if egrep Rerun $(PAPER).log ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if egrep Rerun $(PAPER).log ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if egrep Rerun $(PAPER).log ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	$(RM) *.aux *.bbl *.blg *.toc

sync: $(PAPER).pdf
	rsync -av ~/Documents/library.bib mendeley.bib

%.ps: %.pdf
	pdf2ps $< $@

clean:
	$(RM) *.aux *.log *.bbl *.blg *~ \#*\# *.toc *.idx
	$(RM) $(patsubst %.tex, %.ps, $(wildcard *.tex))
	$(RM) $(patsubst %.tex, %.dvi, $(wildcard *.tex))
	$(RM) $(patsubst %.tex, %.pdf, $(wildcard *.tex))
