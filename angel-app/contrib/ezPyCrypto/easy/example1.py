#!/usr/bin/env python

"""
example1.py

Simple demo of ezPyCrypto
"""

from pdb import set_trace as trace
import ezPyCrypto

secretString = "Hello, this string will be encrypted"

# Create a key object
print "Generating 2048-bit keypair - could take a while..."
k = ezPyCrypto.key(2048)
#k = ezPyCrypto.key(512)

# Encrypt a string
print "Unencrypted string: '%s'" % secretString
enc = k.encString(secretString)

# Now decrypt it
dec = k.decString(enc)
print "Decrypted string: '%s'" % dec

