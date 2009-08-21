#!/bin/bash

# quickly hacked script to ease building an OSX application bundle
#
# Usage: ./build-osx.sh VERSION
#

VERSION=${1:?Please specify the version}
NAME="Scrambler Droplet"

rm -rf build dist
./setup.py py2app
rm -rf "${NAME}-${VERSION}.app"
mv "dist/${NAME}.app" "${NAME}-${VERSION}.app"
rm -rf build dist
