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

function end()
{
	exitcode=$1
	rm -rf $THISTMPDIR > /dev/null 2>&1 # cleanup temp junk
	exit $exitcode
}

function error()
{
	echo "$0: $1" 1>&2
	end -1
}

function usage()
{
	echo "Usage: `basename $0` DESTDIR [local|trunk|release] directory|tag VERSION"
	echo ""
	echo "  Example usage:"
	echo "     `basename $0` ~/build/ local ~/src/angel-app/  creates a prepared tree of a local working copy"
	echo "     `basename $0` ~/build/ trunk                   creates a prepared tree of the current trunk"
	echo "     `basename $0` ~/build/ release testtag  0.1.2  creates a prepared tree of tag 'testtag' and sets version to 0.1.2"
	echo ""
	end 0
}

# setup a temp dir for temp junk:
THISTMPDIR=$(mktemp -d -t `basename $0`XXXXXX)

#clean env:
env -i

if [ -z "$1" ]
then
	usage
fi
DESTDIR=$1
if [ ! -d $DESTDIR ]
then
	error "Destination dir $DESTDIR does not exist"
fi
shift
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
		error "Please specify a tag!"
	fi
	if [ -z $RELEASE ];
	then
		error "Please specify a release number!"
	fi
	echo "release: tag (ABC_x_xx) '$TAG' and release (x.xx) '$RELEASE'"
elif [ "${MODE}" = "local" ]
then
	shift
	LOCALDIR=$1
	echo "release: local from dir '$LOCALDIR'"
	if [ -z $LOCALDIR ];
	then
		error "Please specify a local source directory!"
	fi
	if [ ! -d $LOCALDIR ];
	then
		error "Directory '$LOCALDIR' does not exist!"
	fi
elif [ "${MODE}" = "trunk" ]
then
	# NOP
	echo "Trunk"
else
	error "unknown mode $MODE"
fi

cd ${THISTMPDIR} || error "Could not switch to directory $THISTMPDIR"
# rm -rf ${MODULE} # TODO: remove eventual previous checkout

if [ "${MODE}" = "release" ]
then
	echo "Checking out fresh copy from SVN with tag ${TAG}...";
	svn co ${SVNURL}/tags/${TAG} > /dev/null || error "An error occured while checking out from repository!"
	mv ${TAG} ${SHORTNAME}
fi
if [ "${MODE}" = "trunk" ]
then
	RELEASE="SVN"
	echo "Checking out fresh copy from SVN...";
	svn co ${SVNURL}/trunk/angel-app > /dev/null || error "An error occured while checking out from repository!"
	mv angel-app ${SHORTNAME}
fi
if [ "${MODE}" = "local" ]
then
	RELEASE="LOCALDEV"
	echo "Clean local copy..."
	rm -rf ${THISTMPDIR}/${SHORTNAME}
	cp -R $LOCALDIR ${SHORTNAME}  > /dev/null || error "Error while copying local data"
fi

# get the revision number from svn:
BUILD_ID=`svn info ${SHORTNAME} | grep '^Revision' | sed -e 's/Revision: *//'`
if [ -z ${BUILD_ID} ]
then
	BUILD_ID="unknown" # should not happen, but set a string!
fi

# remove spurious development files/repository files
echo "Removing files not used for production/release..."
cd ${THISTMPDIR}
echo -n " SVN directories"
find ${SHORTNAME}/ -type d -name '.svn' -print0 | xargs -0 rm -rf
echo ""
echo -n " Python pre-compiled files"
find ${SHORTNAME}/ -type f -name '.pyc' -print0 | xargs -0 rm -f
echo ""

# twisted: unpack the tarball we ship, so we are sure we use it during the build process
twistedtar=`ls ${SHORTNAME}/twisted_trunk_*.tar.bz2`
twistedsrc=`basename $twistedtar .tar.bz2`
echo "Unpacking twisted from ${twistedtar} to ${SHORTNAME}/src/"
tar xjf ${twistedtar} || error "Could not untar ${twistedtar}"
rm -rf ${SHORTNAME}/src/twisted/
mv ${twistedsrc}/twisted/ ${SHORTNAME}
rm -rf ${twistedsrc}
rm ${twistedtar} # we don't want to distribute the tar file

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

mv ${SHORTNAME} "${SHORTNAME}-${RELEASE}" || error "Could not rename to shortname-release"
rm -rf "$DESTDIR/${SHORTNAME}-${RELEASE}" || error "Could not remove data from DESTDIR"
mv "${SHORTNAME}-${RELEASE}" $DESTDIR || error "Could not move to DESTDIR"
# clean temp junk:
echo "BUILD_ID: ${BUILD_ID}"
echo "You can now create a platform build from the directory:"
echo "${DESTDIR}${SHORTNAME}-${RELEASE}"
end 0
