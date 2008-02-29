#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
=======================================================================
Copyright (c) 2007 Paul Kremer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

def daemonize() is from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
which was written by by Juergen Hermann, Noah Spurrier, Clark Evans.
That code had no license with it, so I assume it is OK to re-use it here.

=======================================================================

dyndnsc.py - a dynamic dns update client that tries to be consistent, stable and efficient on network resources

Design:
    - updating a dyndns entry is done by a "DynDNS Update Protocol handler"
    - detecting IPs, both in DNS or elsewhere is done using IPDetector's
      which all have a detect() method and bookkeeping about changes
    - the DynDnsClient uses the Protocol Handler to do the updates and
      the IPDetectors to decide when an update needs to occur
    - a dummy endless loop ( used for time.sleep() ) repeatedly asks the
      DynDnsClient to make sure everything is fine

Ideas:
- add other protocol handlers, for example for dyndns.org
- use timer events?
- detection of internet connectivity, other than querying an IP from a webpage?

Other:
 requires python 2.3, Growl notification works with python 2.4 (subprocess module)
"""

__author__ = "Paul Kremer < pkremer TA spurious TOD biz >"
__license__ = "MIT License"
__revision__ = "$Id: dyndnsc.py 490 2008-02-29 11:32:40Z pkremer $"

import sys
import os
import urllib
import urllib2
from urllib2 import URLError
import re
import socket
import time
import logging


def daemonize(stdout='/dev/null', stderr=None, stdin='/dev/null', # os.devnull only python 2.4
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

class DyndnsLogger(logging.getLoggerClass()):
    "We use our own Logger class so we can introduce additional logger methods"
    def growl(self, type, title, msg):
        """
        Method to explicitly send a notification to the desktop of the user
        
        Essentially, this method is an alternative to using loglevels for the decision wether the
        message should be a desktop notification or not. 
         
        @param type: a notification type
        @param title: the title of the notification
        @param msg: the actual message
        """
        # TODO: this is ugly and probably slow
        if not vars(self).has_key('__growlnotifier'):
            try:
                import Growl
            except ImportError:
                logger.debug("No native growl support")
                self.__growlnotifier = False
            else:
                self.__growlnotifier = Growl.GrowlNotifier(applicationName = 'dyndns', notifications = ['User'], defaultNotifications = ['User'])
                self.__growlnotifier.register()
        
        if not self.growl == False:
            logger.debug('trying growl native')
            self.__growlnotifier.notify(noteType = 'User', title = title, description = msg)
        else:
            logger.debug('trying growlnotify cmd line')
            cmd = ["/usr/local/bin/growlnotify", '-i', '.term', '-t', title, '-m', msg]
            try:
                import subprocess
                proc = subprocess.Popen(cmd)
                proc.wait()
            except:
                logger.debug("growlnotify cmd line failed")

class BaseClass(object):
    """
    A common base class providing logging and desktop-notification.
    """
    # TODO: clean this up!

    def emit(self, message):
        """
        logs and notifies the message
        """
        logger.info(message)
        logger.growl('User', 'Dynamic DNS', "%s" % message)



class HTTPGetHelper(BaseClass):
    """
    This class really just wraps the python urllib/urllib2 for fetching URLs
    with GET parameters and handle exceptions/problems gracefully by logging and
    returning an empty string.

    Also sets the User-Agent header.
    """
    def __init__(self):
        """
        By default sets the user agent string to
        dyndnsc.py/%s (http://dyndns.majimoto.net/)
        where %s is the subversion revision currently
        """
        regex = re.compile('^\$Id: (.*?) (\d+) (.*)\$$')
        v = 'unknown'
        matchObj = regex.search(__revision__)
        if not matchObj is None:
            v = matchObj.group(2)
        self.useragent = 'dyndnsc.py/%s (http://dyndns.majimoto.net/)' % v

    def setUserAgent(self, useragent):
        """
        Explicitly set the user agent to the given string
        """
        self.useragent = useragent

    def get(self, url, params = {}, size = -1):
        """
        This fetches the data returned from the given url and the given params.
        If size is specified, only size amount of bytes are read and returned.
        I anything goes wrong, this returns an empty string.
        """
        # TODO: refuse to follow redirects
        params = urllib.urlencode(params) # needs urllib
        headers = { 'User-Agent' : self.useragent }
        req = urllib2.Request(url + '?' + params, headers = headers)
        data = ''
        try:
            response = urllib2.urlopen(req)
        except URLError, e:
            logger.warning("Got an exception while opening and reading from url '%s'" % (url) )
            if hasattr(e, 'reason'):
                logger.warning('Failed to reach the server with reason: %s' % e.reason)
            elif hasattr(e, 'code'):
                from BaseHTTPServer import BaseHTTPRequestHandler
                logger.warning("HTTP error code: %s, %s" % ( e.code, BaseHTTPRequestHandler.responses[e.code] ) )
        except IOError, e:
            logger.warning("IO error: %s" % ( e ) )
        else:
            # everything seems fine:
            data = response.read(size)
        return data


class IPDetector(BaseClass):
    """
    Base class for IP detectors. Really is just a state machine for old/current value.
    """

    def canDetectOffline(self):
        """
        Must be overwritten. Return True when the IP detection can work offline without causing network traffic.
        """
        raise Exception, "Abstract method, must be overridden"

    def getOldValue(self):
        if not vars(self).has_key('_oldvalue'):
            self._oldvalue = self.getCurrentValue()
        return self._oldvalue

    def setOldValue(self, value):
        self._oldvalue = value

    def getCurrentValue(self, default = None):
        if not vars(self).has_key('_currentvalue'):
            self._currentvalue = default
        return self._currentvalue

    def setCurrentValue(self, value):
        self._oldvalue = self.getCurrentValue(value)
        self._currentvalue = value
        return self._currentvalue

    def hasChanged(self):
        """
        Detect a state change with old and current value
        """
        if self.getOldValue() == self.getCurrentValue():
            return False
        else:
            return True


class IPDetector_DNS(IPDetector):
    """
    Class to resolve a hostname using socket.getaddrinfo()
    """
    def canDetectOffline(self):
        "Returns false, as this detector generates dns traffic"
        return False

    def setHostname(self, hostname):
        self.hostname = hostname

    def detect(self):
        try:
            ip = socket.getaddrinfo(self.hostname, None)[0][4][0]
        except:
            #print "WARN: dns is None"
            ip = None
        #print "dnsdetect for %s: %s" % (self.hostname, ip)
        self.setCurrentValue(ip)
        return ip


class IPDetector_TeredoOSX(IPDetector):
    """
    Class to detect the local Teredo ipv6 address by checking the local 'ifconfig' information
    """
    interfacename = "tun0" 
    def canDetectOffline(self):
        "Returns true, as this detector only queries local data"
        return True

    def _netifaces(self):
        "uses the netifaces module to detect ifconfig information"
        try:
            import netifaces
        except ImportError:
            logger.critical("The 'netifaces' module is not installed!")
            raise
            #return None
        addrlist = netifaces.ifaddresses(self.interfacename)[netifaces.AF_INET6]
        for pair in addrlist:
            matchObj = re.match("2001:.*", pair['addr'])
            if not matchObj is None:
                #print "Found ipv6 addr with netifaces on interface '%s': %s" % (self.interfacename, pair['addr'])
                return pair['addr']
        return None

#    def _popenGrep(self):
#        "uses the command line tools to detect ifconfig information"
#        # this method must be avoided when running in a twisted thread, because twisted breaks SIGCHLD
#        cmd = "/sbin/ifconfig %s" % self.interfacename
#        try:
#            stdout = os.popen(cmd).readlines()
#            for line in stdout:
#                matchObj = re.match("\tinet6 (2001.*?) .*", line)
#                if not matchObj is None:
#                    ip = matchObj.group(1)
#                    return ip
#        except:
#            raise
#            return None

    def detect(self):
        ip = self._netifaces()
        if ip is None:
            logger.debug("The teredo ipv6 address could not be detected with 'netifaces'")
#            ip = self._popenGrep() 
        # at this point, ip can be None
        self.setCurrentValue(ip)
        return ip


class IPDetector_WebCheck(IPDetector):
    """
    Class to detect an IP address as seen by an online website that returns parsable output
    """

    def canDetectOffline(self):
        "Returns false, as this detector generates http traffic"
        return False

    def _getClientIPFromUrl(self, url):
        data = HTTPGetHelper().get(url, size = 1024)
        lines = data.splitlines()
        self.regex = re.compile("Current IP Address: (.*?)(<.*){0,1}$")
        for line in lines:
            matchObj = self.regex.search(line)
            if not matchObj is None:
                return matchObj.group(1)
        return None

    def detect(self):
        #self.log("detect WebCheck")
        ip = None
        urls = (
                "http://dyndns.majimoto.net/nic/checkip",
                "http://checkip.dyndns.org/",
                "http://checkip.eurodyndns.org/",
                "http://dynamic.zoneedit.com/checkip.html", # renders bad stuff if queried too quickly, but that's fine ;-)
                "http://dns.iltuonome.net/checkip.html",
                "http://ipcheck.rehbein.net/"
                "http://www.antifart.com/stuff/checkip/",
                )
        for url in urls:
            ip = self._getClientIPFromUrl(url)
            if not ip is None: break
        if ip is None:
            logger.info("Could not detect IP using webchecking! Offline?")
        self.setCurrentValue(ip)
        return ip


class DyndnsUpdateProtocol(BaseClass):
    """
    This class contains the logic for talking to the update service of dyndns.majimoto.net
    
    For other protocols, you can just implement a different class. This one might be compatible
    with dyndns.org, but that's untested.
    """
    def __init__(self, hostname, key, usessl = False):
        self.key = key
        self.hostname = hostname
        if usessl:
            self.updateurl = "https://dyndns.majimoto.net/nic/update"
        else:
            self.updateurl = "http://dyndns.majimoto.net/nic/update"

        self.failcount = 0
        self.nochgcount = 0
        self.httpgetter = HTTPGetHelper()

    def sendUpdateRequest(self, ip):
        # TODO: before sending an update request, make sure we are not abusing the service
        # e.g. is it in 911 state or avoid too many 'nochg' reponses
        self.ip = ip
        params = {'myip': self.ip, 'key': self.key , 'hostname': self.hostname }
        self.updateResult = self.httpgetter.get(self.updateurl, params, size = 1024)
        self.lastUpdate = time.time()
        logger.debug("Update result: '%s'" % self.updateResult )
        if self.updateResult == 'good':
            self.success()
        elif self.updateResult == 'nochg':
            self.nochg()
        elif self.updateResult == 'abuse':
            self.abuse()
        elif self.updateResult == '911':
            self.failure()
        else:
            self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.ip, self.updateResult))

    def success(self):
        self.failcount = 0
        self.nochgcount = 0
        self.emit("Updated IP address of '%s' to %s" % (self.hostname, self.ip))

    def abuse(self):
        self.failcount = 0
        self.nochgcount = 0
        self.emit("This client is considered to be abusive for hostname '%s'" % (self.hostname))

    def nochg(self):
        self.failcount = 0
        self.nochgcount += 1
        logger.debug("IP address of '%s' is unchanged [%s]" % (self.hostname, self.ip))

    def failure(self):
        self.failcount +=1
        logger.warning("DynDns service is failing with result '%s'!" % (self.updateResult))
        self.emit("DynDns service is failing with result '%s'!" % (self.updateResult))


class DynDnsClient(BaseClass):
    """
    This class represents a client to the dynamic dns service.
    """
    def __init__(self, sleeptime = 300):
        self.ipchangedetection_sleep = sleeptime # check every n seconds if our IP changed
        self.forceipchangedetection_sleep = sleeptime * 5 # force check every n seconds if our IP changed
        logger.debug("DynDnsClient instantiated")
        logger.growl("User", "Network", "Dynamic DNS client activated")

    def setProtocolHandler(self, proto):
        self.proto = proto
    
    def setDNSDetector(self, detector):
        self.dns = detector

    def setChangeDetector(self, detector):
        self.detector = detector

    def sync(self):
        """
        Forces a syncronisation if there is a difference between the IP from DNS and the detector.
        This can be expensive, mostly depending on the detector, but also because updating the
        dynamic ip in itself is costly.
        Therefore, this method should usually only be called on startup or when the state changes.
        
        Return values:
            0 : nothing happend, no sync needed
            1 : sync done, successfull
            2 : sync done, error received from protocolHandler
        """
        if self.dns.detect() != self.detector.detect():
            if not self.detector.getCurrentValue() is None:
                logger.info("Current dns IP '%s' does not match current detected IP '%s', updating" % (self.dns.getCurrentValue(), self.detector.getCurrentValue()))
                self.proto.sendUpdateRequest(self.detector.getCurrentValue())
                # TODO: handle response
            else:
                # we don't have a value to set it to, so don't update! Still shouldn't happen though
                pass

    def stateHasChanged(self):
        """
        Detects a change either in the offline detector or a
        difference between the real DNS value and what the online
        detector last got.
        This is efficient, as it only generates minimal dns traffic
        for online detectors and no traffic at all for offline detectors.
        
        @return: boolean
        """
        self.lastcheck = time.time()
        # prefer offline state change detection:
        if self.detector.canDetectOffline():
            self.detector.detect()
        elif not self.dns.detect() == self.detector.getCurrentValue(): # query current dns, and only detect if there's no match
            # this produces traffic, but probably less traffic overall than the detector
            self.detector.detect()
        if self.detector.hasChanged() == True:
            logger.debug("detector changed")
            return True
        elif self.dns.hasChanged() == True:
            logger.debug("dns changed")
            return True
        else:
            return False

    def needsCheck(self):
        """
        This checks if the planned time between checks has elapsed.
        When this time has elapsed, a state change check through stateHasChanged() should be performed and eventually a sync().
        """
        if not vars(self).has_key('lastcheck'):
            self.lastcheck = time.time()
        elapsed = time.time() - self.lastcheck
        if ( elapsed < self.ipchangedetection_sleep):
            return False
        return True
        
    def needsForcedCheck(self):
        """
        This checks if self.forceipchangedetection_sleep between checks has elapsed.
        When this time has elapsed, a sync() should be performed, no matter what stateHasChanged() says.
        This is really just a safety thing to enforce consistency in case the state gets messed up.
        """
        if not vars(self).has_key('lastforce'):
            self.lastforce = time.time()
        elapsed = time.time() - self.lastforce
        if (elapsed < self.forceipchangedetection_sleep):
            return False
        return True
        
    def check(self):
        if self.needsCheck():
            logger.debug("needs a check according to ipchangedetection_sleep (%s sec)" % self.ipchangedetection_sleep)
            if self.stateHasChanged():
                logger.debug("state changed, syncing...")
                self.sync()
            elif self.needsForcedCheck():
                logger.debug("forcing sync after %s seconds" % self.forceipchangedetection_sleep)
                self.lastforce = time.time()
                self.sync()
            else:
                # nothing to be done
                pass

    def loop(self):
        """
        Blocking endless loop with built-in sleeping between checks and updates.
        """
        while True:
            self.check()
            time.sleep(self.ipchangedetection_sleep)


def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="go into daemon mode (implies --loop)", action="store_true", default=False)
    parser.add_option("--hostname", dest="hostname", help="hostname to update", default=None)
    parser.add_option("--key", dest="key", help="your authentication key", default=None)
    parser.add_option("--method", dest="method", help="method for detecting your IP (default webcheck)", default='webcheck')
    parser.add_option("--loop", dest="loop", help="loop forever (default is to update once)", action="store_true", default=False)
    parser.add_option("--sleeptime", dest="sleeptime", help="how long to sleep between checks in seconds", default=300)
    (options, dummyargs) = parser.parse_args()

    if options.hostname is None: raise Exception, "Please specify a hostname using --hostname"
    hostname = options.hostname
    if options.key is None: raise Exception, "Please specify a key using --key"
    key = options.key
    if not options.sleeptime is None: sleeptime = int(options.sleeptime)
    if sleeptime < 60:
        print "WARNING: sleeptime should be > 60 sec, but it might be fine if you use an offline method for IP detection"

    if options.method == 'webcheck':
        changeDetector = IPDetector_WebCheck()
    elif options.method == 'teredoosx':
        changeDetector = IPDetector_TeredoOSX()
    else: raise Exception, "unknown method given! Allowed: webcheck, teredoosx"

    # done with option parsing, bring on the dancing girls
    
    dnsChecker = IPDetector_DNS()
    dnsChecker.setHostname(hostname)

    protoHandler = DyndnsUpdateProtocol(hostname = hostname, key = key)

    dyndnsclient = DynDnsClient( sleeptime = sleeptime)
    dyndnsclient.setProtocolHandler(protoHandler)
    dyndnsclient.setDNSDetector(dnsChecker)
    dyndnsclient.setChangeDetector(changeDetector)
    # do an initial syncronisation, before going into endless loop:
    dyndnsclient.sync()
    
    if options.daemon:
        daemonize() # fork into background
        options.loop = True

    if options.loop:
        dyndnsclient.loop()
    else:
        dyndnsclient.check()

    return 0

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    logging.setLoggerClass(DyndnsLogger)
    logger = logging.getLogger('a')
    sys.exit(main())
