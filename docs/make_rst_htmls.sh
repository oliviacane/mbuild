#!/bin/bash

# set target output directory
TARGETDIR=_build/html

# if does not exist, create it
if [ ! -d "$TARGETDIR" ]; then
	mkdir -p $TARGETDIR
fi

# files to load from
FILES=tutorials/*.rst

# convert the files
for f in $FILES
do
	base=$(basename $f)
	fname="${base%.*}"
	echo "Converting $f..."
	sh rst2html.sh $f $TARGETDIR/$fname.html
done

# copy assets next to htmls
echo "Copying assets/ to target directory"
cp -r assets/ $TARGETDIR/assets/