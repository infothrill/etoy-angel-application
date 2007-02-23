#!/usr/bin/env python

"""
example3.py

Import a public key, and encrypt some data
"""

orig = "Here is something we don't want the govt to know about"

import ezPyCrypto

# Create a key object
k = ezPyCrypto.key()

# Read in a public key
fd = open("ex_mykey.pub", "rb")
pubkey = fd.read()
fd.close()

# import this public key
k.importKey(pubkey)

# Now encrypt some text against this public key
enc = k.encString(orig)

# Save the encrypted text to disk
fd = open("ex_mysecret.enc", "wb")
fd.write(enc)
fd.close()

print "Original text:"
print orig
print
print "Saved encrypted text in ex_mysecret.enc - example4.py will use this"

