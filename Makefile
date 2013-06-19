###########################################################
#
# Makefile for LaTeX docs
#

DEPS=$(wildcard plots/*/*.pdf) $(wildcard figs/*.pdf) $(wildcard graphs/*.tex)
DOT=$(patsubst %.dot,%.tex,$(wildcard graphs/final_*.dot))

PAPER=paper
LATEXOPTS=-interaction=nonstopmode

all: pdf

pdf: $(PAPER).pdf

$(PAPER).pdf: $(wildcard *.tex) $(wildcard *.bib) $(DEPS) $(DOT)
	pdflatex $(LATEXOPTS) $(PAPER)
	if egrep '\\cite' $(PAPER).tex ; then bibtex $(PAPER) ; fi
	if [ -e $(PAPER).toc ] ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if [ -e $(PAPER).bbl ] ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if egrep Rerun $(PAPER).log ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if egrep Rerun $(PAPER).log ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	if egrep Rerun $(PAPER).log ; then pdflatex $(LATEXOPTS) $(PAPER) ; fi
	$(RM) *.aux *.bbl *.blg *.toc

visu.pdf: $(wildcard *.tex) $(wildcard *.bib) $(DEPS) $(DOT)
	pdflatex $(LATEXOPTS) visu
	if egrep '\\cite' visu.tex ; then bibtex visu ; fi
	if [ -e visu.toc ] ; then pdflatex $(LATEXOPTS) visu ; fi
	if [ -e visu.bbl ] ; then pdflatex $(LATEXOPTS) visu ; fi
	if egrep Rerun visu.log ; then pdflatex $(LATEXOPTS) visu ; fi
	if egrep Rerun visu.log ; then pdflatex $(LATEXOPTS) visu ; fi
	if egrep Rerun visu.log ; then pdflatex $(LATEXOPTS) visu ; fi
	$(RM) *.aux *.bbl *.blg *.toc

sync: $(PAPER).pdf
	rsync -av ~/Documents/library.bib mendeley.bib

%.ps: %.pdf
	pdf2ps $< $@

# Translate dot files to tex files
# Remove begin tikzpicture along with it
%.tex: %.dot
	dot2tex --prog=neato --figonly $< | head -n -3 | tail -n +5 > $@

dot: $(DOT)

clean:
	$(RM) *.aux *.log *.bbl *.blg *~ \#*\# *.toc *.idx
	$(RM) $(patsubst %.tex, %.ps, $(wildcard *.tex))
	$(RM) $(patsubst %.tex, %.dvi, $(wildcard *.tex))
	$(RM) $(patsubst %.tex, %.pdf, $(wildcard *.tex))
