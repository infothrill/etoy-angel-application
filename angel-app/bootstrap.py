#!/usr/bin/env python

INSTALL_LOCATION = "angel-app"

import os

os.mkdir(INSTALL_LOCATION)

import commands
run = commands.getstatusoutput

# create virtual python installation
run("python ./virtual-python.py " + INSTALL_LOCATION)

# use virtual python installation from now on
os.environ["PATH"] = os.environ["PATH"] + ":" + INSTALL_LOCATION + "/bin"

# install ez_setup
run("python ./ez_setup.py")

# install angel-app libraries
run("which python")

