#/usr/bin/env python

"""
based on http://twistedmatrix.com/projects/web2/documentation/examples/intro/simple.py
"""

tracked = []
import time, calendar
oneDay = 24 * 60 * 60

def removeOldItems():
    
    now = time.gmtime()

    for ti in tracked:
        diff = calendar.timegm(now) - calendar.timegm(ti.timeStamp)
        if diff > oneDay:
            print "old item: " + `ti`
            tracked.remove(ti)
            
            
import commands
from angel_app.config import config
AngelConfig = config.getConfig()
repository =  AngelConfig.get("common", "repository")

def repositorySize():
    """
    Currently, all angel-app instances completely mirror the repository on missioneternity.org
    (and nothing else). It's therefore sufficient to know the repository size on m221e.org.
    """
    return int(commands.getoutput("du -sk " + repository).split()[0].strip())

class TrackedItem(object):
    """
    A combination of hostname and timestamp, to keep track of which hosts run the angel-app.
    """
    def __init__(self, host):
        self.timeStamp = time.gmtime()
        self.host = host
        
    def __eq__(self, other):
        return self.host == other.host
    
    def __repr__(self):
        return `self.host` + ": " + `self.timeStamp`


def humanReadableKilobytes(kb = 0):
    units = ["KiB", "MiB", "GiB"]
    size = kb
    ii = 0
    while size > 0:
        size = size / 1024
        ii += 1
    ii = ii - 1
    assert ii < 3, "Off the scale: " + `ii`
    return (kb / (1024 ** ii), units[ii])

def makeStatistics(numberOfHosts = 0, amountOfData = 0):

    # format the repository size
    (normalizedData, unit) = humanReadableKilobytes(amountOfData)
    
    # estimate for the amount of data in the overall network
    networkData = numberOfHosts * amountOfData
    # estimate the amount of data validated
    (normalizedTransferred, transferUnit) = humanReadableKilobytes(networkData * 24 / oneDay)
    
    # estimate data lifetime (we assume one day traversal, and three years lifetime
    # for individual hard disks, see Eq. (6) in the report):
    oneYear = oneDay * 365
    threeYears = float(oneDay * 365 * 3) 
    tau_1 = float(1. / oneDay) * ((oneDay / threeYears) ** numberOfHosts)
    tau = (1 / tau_1) / oneYear
    
    return """
estimated number of nodes online: %i
repository size: %i %s
total amount of data validated: %i %s / h
estimated data lifetime: %8.3f years
""" % (numberOfHosts, normalizedData, unit, normalizedTransferred, transferUnit, tau)

    
        
from twisted.web2 import http, resource

class Toplevel(resource.Resource):
  addSlash = True
  def render(self, request):
      removeOldItems()
      ti = TrackedItem(request.remoteAddr.host)
      if not ti in tracked:
          print "not tracked yet: " + `ti`
          tracked.append(ti)
      else:
          print "already tracked: " + `tracked[tracked.index(ti)]`
          
      stats = makeStatistics(len(tracked), repositorySize())    
      return http.Response(stream=stats)

def main():

    from twisted.web2 import server
    from twisted.web2 import channel
    from twisted.internet import reactor
    
    site = server.Site(Toplevel())
    
    reactor.listenTCP(6223, channel.HTTPFactory(site), 50)
    reactor.run()


if __name__ == "__main__":
    main()