#/usr/bin/env python

"""
based on http://twistedmatrix.com/projects/web2/documentation/examples/intro/simple.py
"""

from angel_app.resource.remote import clone

def connectToTracker():
    
    try:
        tracker = clone.Clone("missioneternity.org", 6223)
        statistics = tracker._performRequestWithTimeOut("GET").read()
        return statistics
    except:
        return "Tracker unavailable. Try connecting later."