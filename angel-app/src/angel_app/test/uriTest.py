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
        
    def testIPv6URI(self):
        ipLiteral = "[2001::4136:e390:0:c952:c1f3:6f11]"
        _uri = "http://" + ipLiteral + ":6221/foo" 
        pp = uri.parse(_uri)
        print "Parse dump: ", pp.dump()
        print pp.host
             
    
