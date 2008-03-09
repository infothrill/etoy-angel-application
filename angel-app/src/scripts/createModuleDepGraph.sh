#!/bin/bash

if [ ! -f src/scripts/py2depgraph.py ]
then
	echo "You must execute this script from the base checkout directory!"
	exit -1
fi

format=${1:?Please specify format (png or svg)}
outdir=${2:?Please specify a directory for the output files!}

if [ ! -d $outdir ]
then
	echo "Output dir $outdir does not exist or is not a directory"
	exit -1
fi

for f in zeo master presenter provider maintainer angel
do
	`PYTHONPATH=src/:$PYTHONPATH python src/scripts/py2depgraph.py src/bin/$f.py | python src/scripts/depgraph2dot.py | dot -T $format -o $outdir/$f.$format`
done

