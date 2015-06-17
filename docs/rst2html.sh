#!/bin/bash

# Creates HTML that includes webgl visualization
#
# Input: file.rst
# Output: file.html
# Tools required:
#	- pandoc
#	- notedown
# 	- ipython

# example: rst2html.sh file.rst file.html

INPUTFILE=$(basename $1)
INPUTDIR=$(dirname $1)
FILE="${INPUTFILE%.*}"
OUTPUT=$2

# if output file not provided
if [ -z "$OUTPUT" ]; then
	OUTPUT=$INPUTDIR/$FILE.html
fi

OUTPUTDIR=$(dirname $OUTPUT)

# convert RST to temp MD
pandoc -i $1 -o $FILE.md

# convert temp MD to IPYNB
notedown $FILE.md > $FILE.ipynb

# delete temp MD
rm $FILE.md

# convert ipynb to html with custom template
ipython nbconvert --to html --template ./tpl/mbuild_ipynb_template.tpl $FILE.ipynb --output $OUTPUT
mv $FILE.ipynb $OUTPUTDIR/

# don't delete temp ipynb
#rm $FILE.ipynb