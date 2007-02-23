#!/usr/bin/env python

"""
example4.py

Import a private key, and decrypt some data
"""

import ezPyCrypto

# Read in a private key
fd = open("ex_mykey.priv", "rb")
pubprivkey = fd.read()
fd.close()

# Create a key object, and auto-import private key
k = ezPyCrypto.key(pubprivkey)

# Read in an encrypted file
fd = open("ex_mysecret.enc", "rb")
enc = fd.read()
fd.close()

# Decrypt this file
dec = k.decString(enc)

# Spill the beans
print "Decrypted: %s" % dec

