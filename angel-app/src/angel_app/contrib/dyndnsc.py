#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
a dynamic dns update client that tries to be consistent, stable and efficient on network resources

Design:
    - updating a dyndns entry is done by a "DynDNS Update Protocol handler"
    - detecting IPs, both in DNS or elsewhere is done using IPDetector's
      which all have a detect() method and bookkeeping about changes
    - the DynDnsClient uses the Protocol Handler to do the updates and
      the IPDetectors to decide when an update needs to occur
    - a dummy endless loop ( used for time.sleep() ) repeatedly asks the
      DynDnsClient to make sure everything is fine

Other:
 should work with python 2.3, tested with python 2.4 and python 2.5
"""

__copyright__ = """Copyright (c) 2007-2008 Paul Kremer

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
"""

__author__ = "Paul Kremer <pkremer TA spurious TOD biz>"
__license__ = "MIT License"
__version__ = "$Revision: 511 $"

import sys
import os
import urllib
import urllib2
from urllib2 import URLError
import re
import socket
import time
import logging
import random
import base64
import string
import netifaces
import IPy
import unittest

def daemonize(stdout='/dev/null', stderr=None, stdin='/dev/null', # os.devnull only python 2.4
              pidfile=None, startmsg = 'started with pid %s' ):
    """
        This forks the current process into a daemon.
        The stdin, stdout, and stderr arguments are file names that
        will be opened and be used to replace the standard file descriptors
        in sys.stdin, sys.stdout, and sys.stderr.
        These arguments are optional and default to /dev/null.
        Note that stderr is opened unbuffered, so
        if it shares a file with stdout then interleaved output
        may not appear in the order that you expect.
    """
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
    """We use our own Logger class so we can introduce additional logger methods"""
    def growl(self, type, title, msg):
        """Method to explicitly send a notification to the desktop of the user
        
        Essentially, this method is an alternative to using loglevels for the decision wether the
        message should be a desktop notification or not. 
         
        @param type: a notification type
        @param title: the title of the notification
        @param msg: the actual message
        """
        # Try native growl first
        if not vars(self).has_key('__growlnotifier'):
            try:
                import Growl
            except ImportError:
                logger.debug("No native growl support")
                self.growl = False
            else:
                self.__growlnotifier = Growl.GrowlNotifier(applicationName = 'dyndns', notifications = ['User'], defaultNotifications = ['User'])
                self.__growlnotifier.register()
        
        if not self.growl == False:
            logger.debug('trying growl native')
            self.__growlnotifier.notify(noteType = 'User', title = title, description = msg)
        else:
            logger.debug('trying growlnotify cmd line')
            tool = "/usr/local/bin/growlnotify"
            cmd = [tool, '-i', '.term', '-t', title, '-m', msg]
            try:
                import subprocess
                proc = subprocess.Popen(cmd)
                proc.wait()
            except Exception, e:
                logger.debug("executing '%s' failed" % tool, exc_info = e)

class BaseClass(object):
    """A common base class providing logging and desktop-notification.
    """
    def emit(self, message):
        """
        logs and notifies the message
        """
        logger.info(message)
        logger.growl('User', 'Dynamic DNS', "%s" % message)


class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    """Class to hook into urllib2 to handle http redirects"""
    def redirect_request(self, req, fp, code, msg, hdrs, *args, **kwargs):
        """
        Refuse to handle redirects. We are working with known services, so we know what to expect.
        """
        raise urllib2.HTTPError(req.get_full_url(), code, msg, hdrs, fp)

class HTTPGetHelper(BaseClass):
    """This class really just wraps the python urllib/urllib2 for fetching URLs
    with GET parameters and handle exceptions/problems gracefully by logging and
    returning an empty string.

    Also sets the User-Agent header.
    """
    def __init__(self):
        """By default sets the user agent string to
        dyndnsc.py/%s (http://dyndns.majimoto.net/)
        where %s is the subversion revision currently
        """
        regex = re.compile('^\$Revision: (\d+) \$$')
        v = 'unknown'
        matchObj = regex.search(__version__)
        if not matchObj is None:
            v = matchObj.group(1)
        self.useragent = 'dyndnsc.py/%s (http://dyndns.majimoto.net/)' % v

    def setUserAgent(self, useragent):
        """Explicitly set the user agent to the given string"""
        self.useragent = str(useragent)

    def get(self, url, params = {}, size = -1, authheader = None):
        """This fetches the data returned from the given url and the given params.
        If size is specified, only size amount of bytes are read and returned.
        If anything goes wrong, this returns an empty string.
        
        @param url: string url
        @param params: dictionary with GET/POST parameters
        @param size: read this many bytes, default all
        @param authheader: string http authentication header
        
        @return tuple (bool success, mixed value)
        """
        params = urllib.urlencode(params) # needs urllib
        headers = { 'User-Agent' : self.useragent }
        opener = urllib2.build_opener(NoRedirectHandler()) # refuse redirects
        req = urllib2.Request(url + '?' + params, headers = headers)
        if authheader:
            req.add_header("Authorization", authheader)
        data = ''
        try:
            response = opener.open(req)
        except URLError, e:
            logger.warning("Got an exception while opening and reading from url '%s'" % (url) )
            if hasattr(e, 'reason'):
                logger.warning('Failed to reach the server with reason: %s' % e.reason)
                return (False, e)
            elif hasattr(e, 'code'):
                from BaseHTTPServer import BaseHTTPRequestHandler
                logger.warning("HTTP error code: %s, %s" % ( e.code, BaseHTTPRequestHandler.responses[e.code] ) )
                return (False, e)
        except IOError, e:
            msg = "IO error: %s" % ( e ) 
            logger.warning(msg)
            return (False, e)
        else:
            # everything seems fine:
            data = response.read(size)
        return (True, data)

class IPDetector(BaseClass):
    """Base class for IP detectors. Really is just a state machine for old/current value."""
    def __init__(self, *args, **kwargs):
        pass

    def canDetectOffline(self):
        """Must be overwritten. Return True when the IP detection can work offline without causing network traffic."""
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
        """Detect a state change with old and current value"""
        if self.getOldValue() == self.getCurrentValue():
            return False
        else:
            return True


class IPDetector_DNS(IPDetector):
    """Class to resolve a hostname using socket.getaddrinfo()"""
    def canDetectOffline(self):
        """Returns false, as this detector generates dns traffic"""
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

class RandomIPGenerator:
    def __init__(self, maxRandomTries = None):
        self.maxRandomTries = maxRandomTries

        # Reserved list from http://www.iana.org/assignments/ipv4-address-space
        # (dated 2001 September 12)
        self._reserved_netmasks = frozenset([
                "0.0.0.0/8",
                "1.0.0.0/8",
                "2.0.0.0/8",
                "5.0.0.0/8",
                "7.0.0.0/8",
                "10.0.0.0/8",
                "23.0.0.0/8",
                "27.0.0.0/8",
                "31.0.0.0/8",
                "36.0.0.0/8",
                "39.0.0.0/8",
                "41.0.0.0/8",
                "42.0.0.0/8",
                "58.0.0.0/8",
                "59.0.0.0/8",
                "60.0.0.0/8",
                "127.0.0.0/8",
                "169.254.0.0/16",
                "172.16.0.0/12",
                "192.168.0.0/16",
                "197.0.0.0/8",
                "224.0.0.0/3",
                "240.0.0.0/8"
                ])

    def isReservedIP(self, ip):
        """Check if the given ip address is in a reserved ipv4 address space
        
        @param ip: IPy ip address
        @return: boolean
        """
        for res in self._reserved_netmasks:
            if ip in IPy.IP(res):
                return True
        return False

    def randomIP(self):
        """Return a randomly generated IPv4 address that is not in a reserved ipv4 address space

        @return: IPy ip address
        """
        randomip = IPy.IP("%i.%i.%i.%i" % (random.randint(1, 254),random.randint(1, 254),random.randint(1, 254),random.randint(1, 254)))
        while self.isReservedIP(randomip):
            randomip = IPy.IP("%i.%i.%i.%i" % (random.randint(1, 254),random.randint(1, 254),random.randint(1, 254),random.randint(1, 254)))
        return randomip

    def next(self):
        """Generator that returns randomly generated IPv4 addresses that are not in a reserved ipv4 address space
        until we hit self.maxRandomTries

        @return: IPy ip address
        """
        if self.maxRandomTries is None or self.maxRandomTries > 0:
            generate = True
        c = 0
        while generate:
            if not self.maxRandomTries is None:
                c += 1
            yield self.randomIP()
            if not self.maxRandomTries is None and c < self.maxRandomTries:
                generate = False        

        raise StopIteration

    def __iter__(self):
        """Iterator for this class. See method next()"""
        return self.next()

class IPDetector_Random(IPDetector):
    """For testing: detect randomly generated IP addresses"""
    def __init__(self):
        self.rips = RandomIPGenerator()

    def canDetectOffline(self):
        """Returns True"""
        return True

    def detect(self):
        for ip in self.rips:
            logger.debug('detected %s' % str(ip))
            self.setCurrentValue(str(ip))
            return str(ip)

class IPDetector_Iface(IPDetector):
    """IPDetector to detect any ip address of a local interface.
    """
    def __init__(self, options):
        """
        Constructor
        @param options: dictionary
        """
        self.opts = {'iface': 'en0', 'family': "INET6"} # TODO: clarify address family option!
        for k in options.keys():
            logger.debug("%s explicitly got option: %s -> %s" % (self.__class__.__name__, k, options[k]))
            self.opts[k] = options[k]

    def canDetectOffline(self):
        """Returns true, as this detector only queries local data"""
        return True

    def detect(self):
        """uses the netifaces module to detect ifconfig information"""
        ip = None
        try:
            addrlist = netifaces.ifaddresses(self.opts['iface'])[netifaces.AF_INET6]
        except Exception, e:
            logger.error("netifaces choked while trying to get inet6 interface information for interface '%s'" % self.opts['iface'], exc_info = e)
        else:
            netmask = IPy.IP("2001:0000::/32")
            for pair in addrlist:
                try:
                    detip = IPy.IP(pair['addr'])
                except Exception, e:
                    logger.debug("Found invalid IP '%s' on interface %s!?" % (pair['addr'], self.opts['iface']))
                    continue
                if detip in netmask:
                    ip = pair['addr']
                    break
        # ip can still be None at this point!
        self.setCurrentValue(ip)
        return ip

class IPDetector_Teredo(IPDetector):
    """IPDetector to detect a Teredo ipv6 address of a local interface.
    Bits 0 to 31 of the ipv6 address are set to the Teredo prefix (normally 2001:0000::/32).
    This detector only checks the first 16 bits!
    See http://en.wikipedia.org/wiki/Teredo_tunneling for more information on Teredo.
    """
    def __init__(self, options):
        """
        Constructor
        @param options: dictionary
        """
        self.opts = {'iface': 'tun0'}
        for k in options.keys():
            logger.debug("%s explicitly got option: %s -> %s" % (self.__class__.__name__, k, options[k]))
            self.opts[k] = options[k]

    def canDetectOffline(self):
        """Returns true, as this detector only queries local data"""
        return True

    def detect(self):
        """uses the netifaces module to detect ifconfig information"""
        ip = None
        try:
            addrlist = netifaces.ifaddresses(self.opts['iface'])[netifaces.AF_INET6]
        except Exception, e:
            logger.error("netifaces choked while trying to get inet6 interface information for interface '%s'" % self.opts['iface'], exc_info = e)
        else:
            netmask = IPy.IP("2001:0000::/32")
            for pair in addrlist:
                try:
                    detip = IPy.IP(pair['addr'])
                except Exception, e:
                    logger.debug("Found invalid IP '%s' on interface %s!?" % (pair['addr'], self.opts['iface']))
                    continue
                if detip in netmask:
                    ip = pair['addr']
                    break
        # ip can still be None at this point!
        self.setCurrentValue(ip)
        return ip


class IPDetector_WebCheck(IPDetector):
    """Class to detect an IP address as seen by an online web site that returns parsable output"""

    def canDetectOffline(self):
        """Returns false, as this detector generates http traffic"""
        return False

    def _getClientIPFromUrl(self, url):
        (success, data) = HTTPGetHelper().get(url, size = 1024)
        if success:
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

class UpdateProtocol(BaseClass):
    """the base class for all update protocols"""
    def update(self, ip):
        self.ip = ip
        return self.protocol()

    def httpauthentication(self):
        raise Exception, "abstract method, please implement in subclass"

    def updateUrl(self):
        raise Exception, "abstract method, please implement in subclass"

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

    def nohost(self):
        self.failcount += 1
        self.emit("Invalid/non-existant hostname: [%s]" % (self.hostname))

    def failure(self):
        self.failcount +=1
        self.emit("Service '%s' is failing with result '%s'!" % (self.name, self.updateResult))

    def notfqdn(self):
        self.failcount +=1
        self.emit("The provided hostname '%s' is not a valid hostname!" % (self.hostname))

class UpdateProtocolMajimoto(UpdateProtocol):
    """This class contains the logic for talking to the update service of dyndns.majimoto.net"""
    def __init__(self, protocol_options):
        for k in ['key', 'hostname']:
            assert protocol_options.has_key(k), "Protocol option '%s' is missing" % k
            assert protocol_options[k] is not None, "Protocol option '%s' is not set" % k
            assert type(protocol_options[k]) == type(""), "Protocol option '%s' is not a string" % k

        self.key = protocol_options['key']
        self.hostname = protocol_options['hostname']

        self.failcount = 0
        self.nochgcount = 0

    def protocol(self):
        # TODO: before sending an update request, make sure we are not abusing the service
        # e.g. is it in 911 state or avoid too many 'nochg' reponses
        # have a helper for doing the http work:
        if not vars(self).has_key('httpgetter'):
            self.httpgetter = HTTPGetHelper()

        params = {'myip': self.ip, 'key': self.key , 'hostname': self.hostname }
        (httpsuccess, self.updateResult) = self.httpgetter.get(self.updateUrl(), params, size = 1024, authheader = self.httpauthentication())
        #logger.debug("Update result: '%s'" % self.updateResult )
        if httpsuccess == False:
            pass # TODO: how to behave here??? we might just be offline
        elif self.updateResult == 'good':
            self.success()
        elif self.updateResult == 'nochg':
            self.nochg()
        elif self.updateResult == 'nohost':
            self.nohost()
        elif self.updateResult == 'abuse':
            self.abuse()
        elif self.updateResult == '911':
            self.failure()
        elif self.updateResult == 'notfqdn':
            self.notfqdn()
        else:
            self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.ip, self.updateResult))

    def updateUrl(self):
        return "https://dyndns.majimoto.net/nic/update"

    def httpauthentication(self):
        return ''


class UpdateProtocolDyndns(UpdateProtocol):
    """Protocol handler for dyndns.com"""

    def __init__(self, protocol_options):
        for k in ['hostname', 'userid', 'password']:
            assert protocol_options.has_key(k), "Protocol option '%s' is missing" % k
            assert protocol_options[k] is not None, "Protocol option '%s' is not set" % k
            assert type(protocol_options[k]) == type(""), "Protocol option '%s' is not a string" % k

        self.hostname = protocol_options['hostname']
        self.userid = protocol_options['userid']
        self.password = protocol_options['password']

        self.failcount = 0
        self.nochgcount = 0

    def httpauthentication(self):
        a = base64.encodestring(self.userid + ':' + self.password)
        return 'Basic ' + a.strip()

    def updateUrl(self):
        return "https://members.dyndns.org/nic/update"

    def protocol(self):
        # TODO: before sending an update request, make sure we are not abusing the service
        # e.g. is it in 911 state or avoid too many 'nochg' reponses
        # have a helper for doing the http work:
        if not vars(self).has_key('httpgetter'):
            self.httpgetter = HTTPGetHelper()

        params = {'myip': self.ip, 'hostname': self.hostname }
        (httpsuccess, self.updateResult) = self.httpgetter.get(self.updateUrl(), params, size = 1024, authheader = self.httpauthentication())
        #logger.debug("Update result: '%s'" % self.updateResult )
        if httpsuccess == False:
            pass # TODO: how to behave here??? we might just be offline
        elif self.updateResult == 'good':
            self.success()
        elif self.updateResult == 'nochg':
            self.nochg()
        elif self.updateResult == 'nohost':
            self.nohost()
        elif self.updateResult == 'abuse':
            self.abuse()
        elif self.updateResult == '911':
            self.failure()
        elif self.updateResult == 'notfqdn':
            self.notfqdn()
        else:
            self.emit("Problem updating IP address of '%s' to %s: %s" % (self.hostname, self.ip, self.updateResult))



def getProtocolHandlerClass( protoname = 'dyndns'):
    """factory method to get the correct protocol Handler given its name"""
    avail = {
             'dyndns': UpdateProtocolDyndns,
             'majimoto': UpdateProtocolMajimoto,
             }
    return avail[protoname]


class DynDnsClient(BaseClass):
    """This class represents a client to the dynamic dns service."""
    def __init__(self, sleeptime = 300):
        self.ipchangedetection_sleep = sleeptime # check every n seconds if our IP changed
        self.forceipchangedetection_sleep = sleeptime * 5 # force check every n seconds if our IP changed
        logger.debug("DynDnsClient instantiated")
        #logger.growl("User", "Network", "Dynamic DNS client activated")

    def setProtocolHandler(self, proto):
        self.proto = proto
    
    def setDNSDetector(self, detector):
        self.dns = detector

    def setChangeDetector(self, detector):
        self.detector = detector

    def sync(self):
        """Forces a syncronisation if there is a difference between the IP from DNS and the detector.
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
                self.proto.update(self.detector.getCurrentValue())
                # TODO: handle response
            else:
                #print self.detector.detect()
                logger.debug("DNS is out of sync, but we don't know what to update it to (detector returns None)")
                # we don't have a value to set it to, so don't update! Still shouldn't happen though
                pass
        else:
            logger.debug("Nothing to do, dns '%s' equals detection '%s'" % (self.detector.getCurrentValue(), self.detector.getCurrentValue()))

    def stateHasChanged(self):
        """Detects a change either in the offline detector or a
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
        """This checks if the planned time between checks has elapsed.
        When this time has elapsed, a state change check through stateHasChanged() should be performed and eventually a sync().
        """
        if not vars(self).has_key('lastcheck'):
            self.lastcheck = time.time()
        elapsed = time.time() - self.lastcheck
        if ( elapsed < self.ipchangedetection_sleep):
            return False
        return True
        
    def needsForcedCheck(self):
        """This checks if self.forceipchangedetection_sleep between checks has elapsed.
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
        """Blocking endless loop with built-in sleeping between checks and updates."""
        while True:
            self.check()
            time.sleep(self.ipchangedetection_sleep)

def getChangeDetectorClass(name):
    avail = {
             'webcheck': IPDetector_WebCheck,
             'teredoosx': IPDetector_Teredo,
             'teredo': IPDetector_Teredo,
             'random': IPDetector_Random
             }
    return avail[name]

def getDynDnsClientForConfig(config):
    """Factory method to instantiate and initialize a complete and working dyndns client
    
    @param config: a dictionary with configuration pairs
    """
    if config is None: return None
    if not config.has_key('hostname'):
        logger.warn("No hostname configured")
        return None
    dnsChecker = IPDetector_DNS()
    dnsChecker.setHostname(config['hostname'])
    try:
        klass = getProtocolHandlerClass(config['protocol'])
    except:
        logger.warn("Invalid protocol: '%s'" % config['protocol'])
        return None
    try:
        protoHandler = klass(config)
    except Exception, e:
        logger.warn("Invalid protocol configuration: '%s'" % (str(e)),  exc_info = e)
        return None

    dyndnsclient = DynDnsClient( sleeptime = config['sleeptime'])
    dyndnsclient.setProtocolHandler(protoHandler)
    dyndnsclient.setDNSDetector(dnsChecker)

    # allow config['method'] to be a list or a comma-separated string:
    if type([]) != type(config['method']):
        dummy = config['method'].split(',')
    else:
        dummy = config['method']
    method = dummy[0]
    if len(dummy) > 1:
        method_optlist = dummy[1:]
    else:
        method_optlist = []
    try:
        klass = getChangeDetectorClass(method)
    except Exception, e:
        logger.warn("Invalid change detector configuration: '%s'" % method, exc_info = e)
        return None

    # make a dictionary from method_optlist:
    opts = {}
    for o in method_optlist:
        # options are key value pairs, separated by a colon ":"
        # allow whitespaces in input, but strip them here:
        res = map(string.strip, o.split(":", 2))
        if len(res) == 2:
            opts[res[0]] = res[1]
    try:
        dyndnsclient.setChangeDetector(klass(opts))
    except Exception, e:
        logger.warn("Invalid change detector parameters: '%s'" % opts, exc_info = e)
        return None

    return dyndnsclient


class TestCases(unittest.TestCase):
    def setUp(self):
        logger.info("TestCases are being initialized")
        unittest.TestCase.setUp(self)
    
    def tearDown(self):
        unittest.TestCase.tearDown(self)
    
    def testAdetectorTypes(self):
        # make sure all advertised "types" are actually available and instantiatable
        avail = ['teredo', 'teredoosx', 'webcheck']
        for a in avail:
            try:
                DetectorClass = getChangeDetectorClass(a)
            except Exception, e:
                self.fail("Invalid options test failed %s" % e)
            d = DetectorClass(options = {'': '', 'foo': 'bar', 'iface': 'sdfsd'})
            self.assertTrue(isinstance(d, DetectorClass))
    
    def testGrowl(self):
        logger.growl('User', 'Dynamic DNS', "%s" % "Test")

    def testKTeredo(self):
        # constructor: test invalid options
        DetectorClass = getChangeDetectorClass('teredo')
        d = DetectorClass(options = {'iface': 'tun0'})
        self.assertTrue(isinstance(d, DetectorClass))
        print d.detect()
        #self.assertEquals(type(d.detect()), type(''))
        
def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-t", "--test", dest="test", help="run test-suite", action="store_true", default=False)
    parser.add_option("-d", "--daemon", dest="daemon", help="go into daemon mode (implies --loop)", action="store_true", default=False)
    parser.add_option("--hostname", dest="hostname", help="hostname to update", default=None)
    parser.add_option("--key", dest="key", help="your authentication key", default=None)
    parser.add_option("--userid", dest="userid", help="your userid", default=None)
    parser.add_option("--password", dest="password", help="your password", default=None)    
    parser.add_option("--protocol", dest="protocol", help="protocol/service to use for updating your IP (default dyndns)", default='dyndns')
    parser.add_option("--method", dest="method", help="method for detecting your IP (default webcheck)", default='webcheck')
    parser.add_option("--loop", dest="loop", help="loop forever (default is to update once)", action="store_true", default=False)
    parser.add_option("--sleeptime", dest="sleeptime", help="how long to sleep between checks in seconds", default=300)
    (options, dummyargs) = parser.parse_args()

    if options.test:
        sys.argv = sys.argv[:1] # unittest module chokes with arguments ;-(
        logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(levelname)s %(message)s')
        unittest.main()
        sys.exit()
    else:
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')

    if options.hostname is None: raise Exception, "Please specify a hostname using --hostname"

    config = {}
    config['hostname'] = options.hostname
    config['key'] = options.key
    config['userid'] = options.userid
    config['password'] = options.password
    config['protocol'] = options.protocol
    config['method'] = options.method
    config['sleeptime'] = int(options.sleeptime)

    # done with command line options, bring on the dancing girls
    dyndnsclient = getDynDnsClientForConfig(config)
    if dyndnsclient is None:
        return 1
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
    logging.setLoggerClass(DyndnsLogger)
    logger = logging.getLogger('dyndns') # we have to set this here in order to make it a module scope variable
    sys.exit(main())
