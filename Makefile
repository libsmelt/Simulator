###########################################################
#
# Makefile for LaTeX docs
#

PAPER=paper

DEPS=$(wildcard plots/*/*.pdf) $(wildcard figs/*.pdf) $(wildcard graphs/*.tex)
DOT=$(patsubst %.dot,%.tex,$(wildcard graphs/final_*.dot))

DEP_PNG=$(patsubst %.pdf,%.png,$(wildcard $(PAPER)-figure*.pdf))
FIG_CACHE_PDF=$(wildcard $(PAPER)-figure*.pdf)
FIG_CACHE_PNG=$(wildcard $(PAPER)-figure*.png)
FIG_CACHE=$(FIG_CACHE_PNG) $(FIG_CACHE_PDF)

LATEXOPTS=-interaction=nonstopmode -shell-escape

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

pitch.pdf: $(wildcard *.tex) $(wildcard *.bib) $(DEPS) $(DOT)
	pdflatex $(LATEXOPTS) pitch
	if egrep Rerun pitch.log ; then pdflatex $(LATEXOPTS) pitch ; fi
	if egrep Rerun pitch.log ; then pdflatex $(LATEXOPTS) pitch ; fi
	if egrep Rerun pitch.log ; then pdflatex $(LATEXOPTS) pitch ; fi
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
	$(RM) *.aux *.log *.bbl *.blg *~ \#*\# *.toc *.idx $(FIG_CACHE)
	$(RM) $(patsubst %.tex, %.ps, $(wildcard *.tex))
	$(RM) $(patsubst %.tex, %.dvi, $(wildcard *.tex))
	$(RM) $(patsubst %.tex, %.pdf, $(wildcard *.tex))

%.png: %.pdf
	convert -compose copy -density 200 $< $@

png: $(DEP_PNG)
.PHONY: png