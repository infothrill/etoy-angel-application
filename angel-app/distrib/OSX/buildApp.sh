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

echo "Giving angel.py a capital letter..."
SCRIPTDIR="./src/bin/"
mv "${SCRIPTDIR}/angel.py" "${SCRIPTDIR}/AAngel.py" # rename twice (Mac OS X is case preserving, not case sensitive)
mv "${SCRIPTDIR}/AAngel.py" "${SCRIPTDIR}/Angel.py"
APPNAME="Angel"

# include the source tree in the PYTHONPATH:
export PYTHONPATH=$PWD/src/:$PYTHONPATH
echo "Pythonpath: " $PYTHONPATH

echo "Running py2applet..."
rm -rf "${SCRIPTDIR}/${APPNAME}.app" # make sure it's not there yet
py2applet --iconfile=${repo}/distrib/OSX/icons/m221e.icns "${SCRIPTDIR}/Angel.py" "${SCRIPTDIR}/master.py" "${SCRIPTDIR}/presenter.py" "${SCRIPTDIR}/provider.py" "${SCRIPTDIR}/maintainer.py" > $THISTMPDIR/py2applet.log 2>&1
if [[ $? -ne 0 ]]
then
	mv $THISTMPDIR/py2applet.log ${TMPDIR}/py2applet.log
	error "py2applet exited with a non-zero exit code. Check ${TMPDIR}/py2applet.log for details"
fi

echo "Moving Application bundle..."
rm -rf "${repo}/${APPNAME}.app" # make sure it's not there yet
mv "${SCRIPTDIR}/${APPNAME}.app" "${repo}"
BUNDLE="${repo}/${APPNAME}.app"

echo "Adding resources to application Bundle..."
mkdir -p "${BUNDLE}/Resources/images/" || error "could not mkdir"
cp ${repo}/distrib/images/* "${BUNDLE}/Resources/images/" || error "could not cp"
mkdir -p "${BUNDLE}/Resources/files/" || error "could not mkdir"
cp ${repo}/distrib/files/* "${BUNDLE}/Resources/files/" || error "could not cp"

mkdir -p "${BUNDLE}/Resources/applescript/" || error "could not mkdir"
cp ${repo}/distrib/applescript/* "${BUNDLE}/Resources/applescript/" || error "could not cp"

echo "Patching Info.plist to match our info..."
"${repo}/distrib/OSX/patchPlist.py" --version "$VERSION" --buildnumber "$BUILD_ID" "${BUNDLE}"

# cleanup temp junk
rm -rf $THISTMPDIR > /dev/null 2>&1 # cleanup temp junk

echo "app-bundle created in ${BUNDLE}"
cd "${repo}"
tar cjf angel-$VERSION-macosx.tar.bz2 $APPNAME.app
echo "tar bzip2 created in ${repo}/angel-$VERSION-macosx.tar.bz2"

