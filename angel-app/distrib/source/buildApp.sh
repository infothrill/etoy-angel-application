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
shift
cd $repo || error "Specified dir '$repo' does no exist"

VERSION="NO_VERSION"
BUILD_ID="NO_BUILD"

if [ -z "$1" ]
then
	echo "WARNING: no version supplied, using $VERSION"
	echo "Press [RETURN] to continue... (interrupt with Ctrl-C)"
	read
else
	VERSION=$1
	shift
fi

if [ -z "$1" ]
then
	echo "WARNING: no build number supplied, using $BUILD_ID"
	echo "Press [RETURN] to continue... (interrupt with Ctrl-C)"
	read
else
	BUILD_ID=$1
	shift
fi


currentname=`basename ${repo}`
cd ..
if [ ! -d $currentname ]
then
	echo "Something's wrong"
	exit -1
fi

rm -rf angel-$VERSION-src
mv $currentname angel-$VERSION-src
tar cjf angel-$VERSION-src.tar.bz2 angel-$VERSION-src

echo "The source tarball is now in `dirname ${repo}`/angel-$VERSION-src.tar.bz2"