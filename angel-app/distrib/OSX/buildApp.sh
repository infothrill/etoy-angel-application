#!/bin/bash
#
# Automatic building of the Mac OS X application bundle using py2app
#
# requires all libraries to be correctly installed! See distrib/OSX/README for details
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

# setup a temp dir for temp junk:
THISTMPDIR=${TMPDIR:?env variable TMPDIR must be set}/`basename $0`_$$
mkdir $THISTMPDIR
chmod 700 $THISTMPDIR # just be sure it's only readable by the current user!

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
else
	VERSION=$1
	shift
fi

if [ -z "$1" ]
then
	echo "WARNING: no build number supplied, using $BUILD_ID"
else
	BUILD_ID=$1
	shift
fi


RENAMETO="angel.py" # is not allowed to contain empty spaces for now. This will set the application name that appears in the dock and other places
BASENAME=`basename $RENAMETO .py`

export PYTHONPATH=$PWD/contrib/:$PWD/src/:$PYTHONPATH
cp ./src/bin/wxmaster.py ./src/bin/$RENAMETO

echo "Running py2applet..."
py2applet --iconfile=${repo}/distrib/OSX/icons/m221e.icns ./src/bin/$RENAMETO ./src/bin/master.py ./src/bin/presenter.py ./src/bin/provider.py ./src/bin/maintainer.py > $THISTMPDIR/py2applet.log 2>&1
if [ $? -ne 0 ]
then
	rm ./src/bin/$RENAMETO
	mv $THISTMPDIR/py2applet.log ${TMPDIR}/py2applet.log
	error "py2applet exited with a non-zero exit code. Check ${TMPDIR}/py2applet.log for details"
fi
rm ./src/bin/$RENAMETO

echo "Adding resources to application Bundle..."
mkdir -p ${repo}/src/bin/$BASENAME.app/Resources/images/ || error "could not mkdir"
cp ${repo}/distrib/images/* ${repo}/src/bin/$BASENAME.app/Resources/images/ || error "could not cp"

mkdir -p ${repo}/src/bin/$BASENAME.app/Resources/applescript/ || error "could not mkdir"
cp ${repo}/distrib/applescript/* ${repo}/src/bin/$BASENAME.app/Resources/applescript/ || error "could not cp"

echo "Patching Info.plist to match our info..."
${repo}/distrib/OSX/patchPlist.py --version "$VERSION" --buildnumber "$BUILD_ID" ${repo}/src/bin/$BASENAME.app

# cleanup temp junk
rm -rf $THISTMPDIR > /dev/null 2>&1 # cleanup temp junk

echo "You app should now be in ${repo}/src/bin/$BASENAME.app"