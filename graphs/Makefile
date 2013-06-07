DEP_PYTHON=$(wildcard *.py)
DEP_PDF=$(patsubst %.tex,%.pdf,$(wildcard visu*.tex))

all: graph visu

graph: visu.tex $(DEP_PYTHON)

.PHONY: visu visu_all.pdf
visu: $(DEP_PYTHON) $(DEP_PDF) visu_all.pdf

visu_all.pdf: $(DEP_PDF)
	pdftk $(DEP_PDF) cat output $@

%.pdf: %.tex
	cp $< input.tex
	pdflatex -interaction nonstopmode "template.tex"
	cp template.pdf $@
	rm input.tex

debug: 
	echo $(DEP_PDF)
	echo $(DEP_PYTHON)
