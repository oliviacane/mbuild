#!/bin/bash

# set target output directory
HTMLDIR=_build/html
IPYNBDIR=_build/ipynb

# if does not exist, create it
if [ ! -d "$HTMLDIR" ]; then
	mkdir -p $HTMLDIR
fi
if [ ! -d "$IPYNBDIR" ]; then
	mkdir -p $IPYNBDIR
fi

# files' path
FILES=tutorials/*.rst

# convert the files
for f in $FILES
do
	base=$(basename $f)
	fname="${base%.*}"
	
	echo "Converting $f and moving results..."
	sh rst2html.sh $f $IPYNBDIR/$fname.ipynb $HTMLDIR/$fname.html
	#echo "sh rst2html.sh $f $IPYNBDIR/$fname.ipynb $HTMLDIR/$fname.html"
done

# copy assets next to htmls
echo "Copying assets/ to html directory"

# copy assets/ dir to HTMLDIR/ -- but don't delete if they're the same
if [ ! -d "$HTMLDIR/assets" ]; then
	ASSETS_ABSPATH_REAL=`cd "./assets/"; pwd`
	ASSETS_ABSPATH_TARGET=`cd "$HTMLDIR/assets"; pwd`

	if [ $ASSETS_ABSPATH_REAL -ne $ASSETS_ABSPATH_TARGET ]; then
		if [ -d "$HTMLDIR/assets" ]; then
			rm -rf $HTMLDIR/assets
		fi

		cp -r assets/ $HTMLDIR/assets/
	fi
fi

cp tutorials/*.pdb $IPYNBDIR