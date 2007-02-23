#!/usr/bin/env python

"""
example6.py

Verify a signature against a document
"""

import ezPyCrypto

# Read in a public key
fd = open("ex_mykey.pub")
pubkey = fd.read()
fd.close()

# Create a key object, and auto-import just a public key
k = ezPyCrypto.key(pubkey)

# Read in a document we need to verify
fd = open("ex_signeddoc.txt")
doc = fd.read()
fd.close()

# Read in the signature
fd = open("ex_signeddoc.txt.sig")
sig = fd.read()
fd.close()

# Now try to verify
if k.verifyString(doc, sig):
	print "Verification successful - signature is authentic"
else:
	print "Verification failed - bad signature"
