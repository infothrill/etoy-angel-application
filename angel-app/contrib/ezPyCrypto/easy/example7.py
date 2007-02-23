#!/usr/bin/env python

"""
example7.py

Demonstrate the use of passphrases with private keys
"""

import ezPyCrypto


mysecret = "Don't look at this!!!"

raw = "Here is a string to encrypt"

# Create a key object
k = ezPyCrypto.key(passphrase=mysecret)

# Export public/private key
publicAndPrivateKey = k.exportKeyPrivate()

# Encrypt against this keypair
enc = k.encString(raw)

# Create a new key object, and import keys (with passphrase)
k1 = ezPyCrypto.key(publicAndPrivateKey, passphrase=mysecret)

# Decrypt text
dec = k.decString(enc)

# test
if dec == raw:
	print "Successful decryption using correct passphrase"
else:
	print "Failed somewhere"

print "Trying now with a bad passphrase"
try:
	k2 = ezPyCrypto.key(publicAndPrivateKey, passphrase="cracking attempt")
except ezPyCrypto.CryptoKeyError:
	print "Oops - our feeble cracking attempt failed (which is a good thing)."
else:
	print "Cracking attempt succeeded - we're not safe"
	# We're in - let's plunder
	dec2 = k2.decString(enc)

