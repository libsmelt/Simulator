DEP_PYTHON=$(wildcard *.py)
DEP_LATEX=$(wildcard *.tex)

all: graph visu

graph: visu.tex $(DEP_PYTHON)

visu.tex: $(DEP_PYTHON)
	./graph_example.py

visu: template.pdf $(DEP_PYTHON) $(DEP_LATEX)

template.pdf: visu.tex $(DEP_PYTHON) $(DEP_LATEX)
	pdflatex -interaction=nonstopmode template.tex