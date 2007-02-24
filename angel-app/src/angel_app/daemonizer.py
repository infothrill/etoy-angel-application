'''
	This module is mostly taken verbatim from
	http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
	Assuming it is OK to use it here. Paul Kremer
	
    This module is used to fork the current process into a daemon.
    Almost none of this is necessary (or advisable) if the daemon 
    is being started by inetd. In that case, stdin, stdout and stderr are 
    all set up for you to refer to the network connection, and the fork()s 
    and session manipulation should not be done (to avoid confusing inetd). 
    Only the chdir() and umask() steps remain as useful.
    References:
        UNIX Programming FAQ
            1.7 How do I get my program to act like a daemon?
                http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        Advanced Programming in the Unix Environment
            W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.

    History:
      2001/07/10 by Juergen Hermann
      2002/08/28 by Noah Spurrier
      2003/02/24 by Clark Evans
      
      http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
'''
import sys, os, time
from twisted.python.filepath import FilePath
from signal import SIGTERM

def getAngelHomePath():
	from angel_app.config.defaults import getAngelHomePath
	return getAngelHomePath()

def getAngelVarPath():
	from os import path
	varPath = path.join(getAngelHomePath(), "var")
	return varPath

def setup():
	"""
	setup() creates the needed internal directory structure for var
	(.angel_app/var/). It must be called at least once during bootstrap.
	"""
	from os import path, mkdir
	angelhomePath = FilePath(getAngelHomePath())
	if not angelhomePath.exists():
		mkdir(angelhomePath.path, 0750)
	angelVarPath = FilePath(getAngelVarPath())
	if not angelVarPath.exists():
		mkdir(angelVarPath.path, 0750)

def daemonize(stdout=os.devnull, stderr=None, stdin=os.devnull,
              pidfile=None, startmsg = 'started with pid %s' ):
    '''
        This forks the current process into a daemon.
        The stdin, stdout, and stderr arguments are file names that
        will be opened and be used to replace the standard file descriptors
        in sys.stdin, sys.stdout, and sys.stderr.
        These arguments are optional and default to /dev/null.
        Note that stderr is opened unbuffered, so
        if it shares a file with stdout then interleaved output
        may not appear in the order that you expect.
    '''
    # Do first fork.
    try: 
        pid = os.fork() 
        if pid > 0: sys.exit(0) # Exit first parent.
    except OSError, e: 
        sys.stderr.write("fork #1 failed: (%d) %s%s" % (e.errno, e.strerror, os.linesep))
        sys.exit(1)
        
    # Decouple from parent environment.
    os.chdir("/")
    os.umask(0) 
    os.setsid()
    
	# interestingly enough, we MUST open STDOUT explicitly before we
	# fork the second time.
	# Otherwise, the duping of sys.stdout won't work,
	# and we will not be able to capture stdout
    print ""

    # Do second fork.
    try: 
        pid = os.fork() 
        if pid > 0: sys.exit(0) # Exit second parent.
    except OSError, e: 
        sys.stderr.write("fork #2 failed: (%d) %s%s" % (e.errno, e.strerror, os.linesep))
        sys.exit(1)
    
    # Open file descriptors and print start message
    if not stderr: stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'w+')
    se = file(stderr, 'w+', 0)
    pid = str(os.getpid())
    sys.stderr.write("%s%s" % (startmsg, os.linesep )% pid)
    sys.stderr.flush()
    if pidfile: file(pidfile,'w+').write("%s%s" % (pid, os.linesep))
    
    # Redirect standard file descriptors.
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

def startstop(action=None, stdout=os.devnull, stderr=None, stdin=os.devnull,
              pidfile='pid.txt', startmsg = 'started with pid %s' ):
	'''
		This is the "front-end"method for starting the daemon, stopping
		and restarting it.
	'''
	if len(action) > 1:
		setup()
		from os import path
		if not path.isabs(stdout):
			stdout = path.join(getAngelVarPath(), stdout)
		if not path.isabs(stderr):
			stderr = path.join(getAngelVarPath(), stderr)
		if not path.isabs(stdin):
			stdin = path.join(getAngelVarPath(), stdin)
		if not path.isabs(pidfile):
			pidfile = path.join(getAngelVarPath(), pidfile)
		try:
			pf  = file(pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None
		if 'stop' == action or 'restart' == action:
			if not pid:
				mess = "Could not stop, pid file '%s' missing.%s"
				sys.stderr.write(mess % (pidfile, os.linesep))
				sys.exit(1)
			try:
				while 1:
					os.kill(pid,SIGTERM)
					time.sleep(1)
			except OSError, err:
				err = str(err)
				if err.find("No such process") > 0:
					os.remove(pidfile)
					if 'stop' == action:
						sys.exit(0)
					action = 'start'
					pid = None
				else:
					print str(err)
					sys.exit(1)
		if 'start' == action:
			if pid:
				mess = "Start aborded since pid file '%s' exists.%s"
				sys.stderr.write(mess % (pidfile, os.linesep))
				sys.exit(1)
			daemonize(stdout,stderr,stdin,pidfile,startmsg)
			return
	print "action must be one of: start|stop|restart"
	sys.exit(2)