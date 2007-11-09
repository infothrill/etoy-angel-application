#!/bin/bash
#
# Shell script to prepare the creation of release packages/bundles:
#
# Can be used to prepare a release from a local copy, from the latest trunk
# and from any tag.
#
# Takes care of cleaning the source tree from unwanted junk, setting version
# and build number (svn revision).
#
# This script is to be used before running one of the platform specific
# build/packaging scripts.
#
# Author: Paul Kremer <pol@etoy.com>
#

function error()
{
	echo "$0: $1" 1>&2
	rm -rf $THISTMPDIR > /dev/null 2>&1 # cleanup temp junk
	exit -1
}

function usage()
{
	echo "Usage: `basename $0` [local|trunk|release] directory|tag VERSION"
	echo ""
	echo "  Example usage:"
	echo "     `basename $0` local ~/src/angel-app/  creates a prepared tree of a local working copy"
	echo "     `basename $0` trunk                   creates a prepared tree of the current trunk"
	echo "     `basename $0` release testtag  0.1.2  creates a prepared tree of tag 'testtag' and sets version to 0.1.2"
	echo ""
	exit
}

# setup a temp dir for temp junk:
THISTMPDIR=${TMPDIR:?env variable TMPDIR must be set}/`basename $0`_$$
mkdir $THISTMPDIR
chmod 700 $THISTMPDIR # just be sure it's only readable by the current user!

#clean env:
env -i

if [ -z "$1" ]
then
	usage
fi

MODE=$1

SHORTNAME="angel_app"
SVNURL="http://svn.gna.org/svn/angel-app"

if [ "${MODE}" = "release" ]
then
	shift
	TAG=$1
	shift
	RELEASE=$1
	if [ -z $TAG ];
	then
		echo "Please specify a tag!" 1>&2
		exit 1
	fi
	if [ -z $RELEASE ];
	then
		echo "Please specify a release number!" 1>&2
		exit 1
	fi
	echo "release: tag (ABC_x_xx) '$TAG' and release (x.xx) '$RELEASE'"
fi

if [ "${MODE}" = "local" ]
then
	shift
	LOCALDIR=$1
	echo "release: local from dir '$LOCALDIR'"
	if [ -z $LOCALDIR ];
	then
		echo "Please specify a local source directory!" 1>&2
		exit 1
	fi
	if [ ! -d $LOCALDIR ];
	then
		echo "Directory '$LOCALDIR' does not exist!" 1>&2
		exit 1
	fi
fi

cd ${THISTMPDIR} || error "Could not switch to directory $THISTMPDIR"
# rm -rf ${MODULE} # TODO: remove eventual previous checkout

if [ "${MODE}" = "release" ]
then
	echo "Checking out fresh copy from SVN with tag ${TAG}...";
	nice svn co ${SVNURL}/tags/${TAG} > /dev/null
	if [ $? != 0 ];
	then
		echo "An error occured while checking out from repository!" 1>&2
		exit 1
	fi
	mv ${TAG} ${SHORTNAME}
fi
if [ "${MODE}" = "trunk" ]
then
	RELEASE="SVN"
	echo "Checking out fresh copy from SVN...";
	svn co ${SVNURL}/trunk/angel-app > /dev/null
	if [ $? != 0 ];
	then
		echo "An error occured while checking out from repository!" 1>&2
		exit 1
	fi
	mv angel-app ${SHORTNAME}
fi
if [ "${MODE}" = "local" ]
then
	RELEASE="LOCALDEV"
	echo "Clean local copy..."
	rm -rf ${THISTMPDIR}/${SHORTNAME}
	cp -ax $LOCALDIR ${SHORTNAME}  > /dev/null
fi

# get the revision number from svn:
BUILD_ID=`svn info ${SHORTNAME} | grep '^Revision' | sed -e 's/Revision: *//'`
if [ -z ${BUILD_ID} ]
then
	BUILD_ID="unknown" # should not happen, but set a string!
fi
echo "BUILD_ID is: ${BUILD_ID}"

# remove spurious development files/repository files
echo "Removing files not used for production/release..."
cd ${THISTMPDIR}
echo -n " SVN directories"
find ${SHORTNAME}/ -type d -name '.svn' -print0 | xargs -0 rm -rf
echo ""
echo -n " Python pre-compiled files"
find ${SHORTNAME}/ -type f -name '.pyc' -print0 | xargs -0 rm -f
echo ""

echo "Setting correct version to '$RELEASE'..."
if [ "x${RELEASE}" == "xSVN" ]
then
	STRING="SVN_"`date +"%m%d_%H:%M:%S"`
	#echo $STRING
	sed -i.bak s/#\!#VERSION#\!#/$STRING/ ${SHORTNAME}/src/angel_app/version.py
	sed -i.bak s/#\!#BUILD_ID#\!#/$BUILD_ID/ ${SHORTNAME}/src/angel_app/version.py
	rm -f ${SHORTNAME}/src/angel_app/version.py.bak 
else
	sed -i.bak s/#\!#VERSION#\!#/$RELEASE/ ${SHORTNAME}/src/angel_app/version.py
	sed -i.bak s/#\!#BUILD_ID#\!#/$BUILD_ID/ ${SHORTNAME}/src/angel_app/version.py
	rm -f ${SHORTNAME}/src/angel_app/version.py.bak
fi

rm -rf "${SHORTNAME}-${RELEASE}"
#rm -rf "${SHORTNAME}-${RELEASE}.tgz"

mv ${SHORTNAME} "${SHORTNAME}-${RELEASE}"
rm -rf "$TMPDIR/${SHORTNAME}-${RELEASE}" > /dev/null 2>&1
mv "${SHORTNAME}-${RELEASE}" $TMPDIR
# clean temp junk:
rm -rf $THISTMPDIR > /dev/null 2>&1 # cleanup temp junk
echo "You can now create a platform build from the directory:"
echo "${TMPDIR}${SHORTNAME}-${RELEASE}"
