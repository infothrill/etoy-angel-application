#!/usr/bin/env python

"""
example8.py

Like example 7, but demonstrates exporting private key with custom passphrase
"""

import ezPyCrypto

mysecret = "Don't look at this!!!"
raw = "Here is a string to encrypt"

# Create a key object
k = ezPyCrypto.key(passphrase=mysecret)

# Export public/private key
anotherSecret = "This is another passphrase"
publicAndPrivateKey = k.exportKeyPrivate(passphrase=anotherSecret)

# Encrypt against this keypair
enc = k.encString(raw)

# Create a new key object, and import keys (with new passphrase)
k1 = ezPyCrypto.key(publicAndPrivateKey, passphrase=anotherSecret)

# Decrypt text
dec = k.decString(enc)

# test
if dec == raw:
	print "Successful decryption using correct NEW passphrase"
else:
	print "Failed somewhere"

print "Trying now with the old passphrase"
try:
	k2 = ezPyCrypto.key(publicAndPrivateKey, passphrase=mysecret)
except ezPyCrypto.CryptoKeyError:
	print "Oops - our old passphrase failed (which is a good thing)."
else:
	print "Old passphrase worked - something not right here! :("
	# We're in - let's plunder
	dec2 = k2.decString(enc)

