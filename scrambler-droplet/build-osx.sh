#!/bin/bash

# quickly hacked script to ease building an OSX application bundle
#
# Usage: ./build-osx.sh VERSION
#

VERSION=${1:?Please specify the version}

rm -rf build dist
./setup.py py2app
rm -rf scrambler-droplet-${VERSION}.app
mv dist/scrambler-droplet.app scrambler-droplet-${VERSION}.app
rm -rf build dist
