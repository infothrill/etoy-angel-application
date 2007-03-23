#!/bin/bash
#
# Automatic building of a source tarball for installation
#
# Usage: buildApp.sh path_to_source [version] [buildnumber]
#
#

function usage()
{
	echo "Usage: `basename $0` PATHTOSOURCE [version] [buildnumber]"
	echo ""
	echo "  Example usage:"
	echo "     `basename $0` ~/src/angel-app/ 1.0.2  34536"
	echo ""
	exit
}

function error()
{
	echo "$0: $1" 1>&2
	rm -rf $THISTMPDIR > /dev/null 2>&1 # cleanup temp junk
	exit -1
}

if [ -z $1 ]
then
	usage
fi

repo=${1}
cd $repo || error "Specified dir '$repo' does no exist"
name=`basename ${repo}`
cd ..
if [ ! -d $name ]
then
	echo "Something's wrong"
	exit -1
fi

tar cjf ${name}.tar.bz2 ${name}


echo "The source tarball is now in `dirname ${repo}`/$name.tar.bz2"