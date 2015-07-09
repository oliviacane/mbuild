#!/bin/bash

# Creates HTML that includes webgl visualization
#
# Input: file.rst
# Output: file.ipynb and file.html
# Tools required:
#	- pandoc
#	- notedown
# 	- ipython

# example: rst2html.sh file.rst file.ipynb file.html

INPUTFILE=$(basename $1)
INPUTDIR=$(dirname $1)
FILENAME="${INPUTFILE%.*}"

OUTPUT_IPYNB=$2
OUTPUT_HTML=$3

# if html output file not provided
if [ -z "$OUTPUT_HTML" ]; then
	OUTPUT_HTML=$INPUTDIR/$FILENAME.html
fi

# if ipynb output not provided
if [ -z "$OUTPUT_IPYNB" ]; then
	OUTPUT_IPYNB=$INPUTDIR/$FILENAME.ipynb
fi

# check output dirs
OUTPUTDIR_IPYNB=$(dirname $OUTPUT_IPYNB)
OUTPUTDIR_HTML=$(dirname $OUTPUT_HTML)
if [ ! -d "$OUTPUTDIR_IPYNB" ]; then
	mkdir -p $OUTPUTDIR_IPYNB
fi
if [ ! -d "$OUTPUTDIR_HTML" ]; then
	mkdir -p $OUTPUTDIR_HTML
fi

# convert RST to temp MD
pandoc -i $1 -o $FILENAME.md

echo "Converting $INPUTFILE to $OUTPUT_IPYNB"
# convert temp MD to IPYNB
notedown $FILENAME.md > $OUTPUT_IPYNB

# delete temp MD
rm $FILENAME.md

# convert ipynb to html with custom template
ipython nbconvert --to html --template ./tpl/mbuild_ipynb_template.tpl $OUTPUT_IPYNB --output $OUTPUT_HTML
