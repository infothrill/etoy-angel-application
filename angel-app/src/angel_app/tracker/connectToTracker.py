#/usr/bin/env python

"""
based on http://twistedmatrix.com/projects/web2/documentation/examples/intro/simple.py
"""

from angel_app.resource.remote.httpRemote import HTTPRemote

from angel_app.tracker.tracker import TRACKER_PORT

def connectToTracker():
    try:
        tracker = HTTPRemote("missioneternity.org", TRACKER_PORT)
        statistics = tracker.performRequestWithTimeOut("GET").read()
        return statistics
    except:
        return "Tracker unavailable. Try connecting later."

def pingTracker():
    try:
        tracker = HTTPRemote("missioneternity.org", TRACKER_PORT)
        dummyresponse = tracker.performRequestWithTimeOut("HEAD")
        return True
    except:
        return False
