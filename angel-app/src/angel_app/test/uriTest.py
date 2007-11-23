"""
Tests for uri parsing.
"""

author = """Vincent Kraeutler 2007"""

from angel_app import uri
import unittest

class URITest(unittest.TestCase):

    def testBasicURI(self):
        _uri = "http://missioneternity.org:6221/"
        pp = uri.parse(_uri)
        #print "PARSE: ", pp.dump()
        #print "parse host: ", pp.host
    
    def testBasicURI(self):
        _uri = "http://missioneternity.org:6221/"
        pp = uri.parse(_uri)
        #print "PARSE: ", pp.dump()
        #print "parse host: ", pp.host
             
    
