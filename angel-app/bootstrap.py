#!/usr/bin/env python

import os
import sys
import shutil
import subprocess

def check_python():
    if sys.version_info < (2,4):
        print "Python 2.4 or higher is required to run Angel."
        sys.exit(256)

check_python()

if len(sys.argv) < 2:
    print "Please provide an install target directory as parameter (must not exist, will be created)"
    sys.exit(1)
else:
    INSTALL_LOCATION = sys.argv[1]
    assert not os.path.exists(INSTALL_LOCATION), "Install dir '%s' already exists. Aborting." % INSTALL_LOCATION 
    os.mkdir(INSTALL_LOCATION)

def run(command, description):
    print description
    proc = subprocess.Popen(command, stdout=sys.stdout, stderr=sys.stderr, env=os.environ, stdin=None)
    alive = True
    while alive:
        exitcode = proc.poll()
        if exitcode is not None: alive = False
    if not exitcode == 0:
        raise Exception, "Error running command '%s' (exit code: %s)" %( " ".join(cmd), exitcode)

cmd = [sys.executable, "./virtual-python.py", "--prefix", INSTALL_LOCATION]
run(cmd, "create virtual python installation")
executable = os.path.join(INSTALL_LOCATION, 'bin', 'python')
assert os.path.isfile(executable)
print "using virtual python installation from now on"

# According to http://peak.telecommunity.com/DevCenter/EasyInstall#creating-a-virtual-python, we must clear any previously set PYTHONPATH
# but then it doesn't work. Also, to have it install the stuff into our virtual python's site-packages dir, we MUST set the PYTHONPATH:  
py_version = 'python%s.%s' % (sys.version_info[0], sys.version_info[1])
ourlibdir = INSTALL_LOCATION + '/lib/' +py_version+'/site-packages/'
os.environ['PYTHONPATH'] = ourlibdir
cmd = [executable, "./ez_setup.py"]
run(cmd, "running ez_setup.py")

cmd = [executable, "./setup.py",  "install", "--prefix", INSTALL_LOCATION]
run(cmd, "install Angel libraries")

print "install Angel binaries"
for fname in os.listdir(os.path.join(os.getcwd() ,'src/bin/')):
    src = os.path.join(os.getcwd() ,'src/bin/', fname)
    dest = os.path.join(INSTALL_LOCATION, "bin", os.path.basename(fname))
    if os.path.isfile(src):
        shutil.copyfile(src, dest)
