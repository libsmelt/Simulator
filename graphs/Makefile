DEP_PYTHON=$(wildcard *.py)
DEP_LATEX=$(patsubst %.tex,%.pdf,$(wildcard visu*.tex))

all: graph visu

graph: visu.tex $(DEP_PYTHON)

.PHONY: visu visu_all.pdf
visu: $(DEP_PYTHON) $(DEP_LATEX) visu_all.pdf

visu_all.pdf: $(DEP_LATEX)
	pdftk $(DEP_LATEX) cat output $@

%.pdf: %.tex
	cp $< input.tex
	pdflatex -interaction nonstopmode "template.tex"
	cp template.pdf $@
	rm input.tex

debug: 
	echo $(DEP_LATEX)
	echo $(DEP_PYTHON)
