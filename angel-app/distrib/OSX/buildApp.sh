#!/bin/bash
#
# Automatic building of the Mac OS X application bundle using py2app
#
# requires all libraries to be correctly installed! See distrib/OSX/README for details
#


function error()
{
	echo "$0: $1" 1>&2
	exit -1
}


repo=${1:?Please specify the full path to the base directory of the repository tree}
cd $repo || error "Specified dir does no exist"

RENAMETO="Angel-App.py" # is not allowed to contain empty spaces for now. This will set the application name that appears in the dock and other places
BASENAME=`basename $RENAMETO .py`

export PYTHONPATH=$PWD/contrib/:$PWD/src/:$PYTHONPATH
cp ./src/bin/wxmaster.py ./src/bin/$RENAMETO

py2applet --iconfile=${repo}/distrib/OSX/icons/m221e.icns ./src/bin/$RENAMETO ./src/bin/master.py ./src/bin/presenter.py ./src/bin/provider.py ./src/bin/maintainer.py

mkdir -p ${repo}/src/bin/$BASENAME.app/distrib/images/ || error "could not mkdir"
cp ${repo}/distrib/images/* ${repo}/src/bin/$BASENAME.app/distrib/images/ || error "could not cp"

mkdir -p ${repo}/src/bin/$BASENAME.app/distrib/applescript/ || error "could not mkdir"
cp ${repo}/src/angel_app/wx/platform/mac/applescript/* ${repo}/src/bin/$BASENAME.app/distrib/applescript/ || error "could not cp"

rm ./src/bin/$RENAMETO

echo "You app should now be in ${repo}/src/bin/$BASENAME.app"