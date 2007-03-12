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

export PYTHONPATH=$PWD/contrib/:$PWD/src/:$PYTHONPATH

py2applet --iconfile=${repo}/distrib/OSX/icons/m221e.icns ./src/bin/wxmaster.py ./src/bin/master.py ./src/bin/presenter.py ./src/bin/provider.py ./src/bin/maintainer.py

mkdir -p ${repo}/src/bin/wxmaster.app/distrib/images/ || error "could not mkdir"
cp ${repo}/distrib/images/* ${repo}/src/bin/wxmaster.app/distrib/images/ || error "could not cp"

mkdir -p ${repo}/src/bin/wxmaster.app/distrib/applescript/ || error "could not mkdir"
cp ${repo}/src/angel_app/wx/platform/mac/applescript/* ${repo}/src/bin/wxmaster.app/distrib/applescript/ || error "could not cp"

echo "You app should now be in ${repo}/src/bin/"