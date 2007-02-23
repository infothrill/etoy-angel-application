#@+leo
#@+node:0::@file easy/autoexec.py
#@+body
#import mytest as m
#k = m.mykey

from pdb import set_trace as trace

from Crypto.Cipher import Blowfish as bf

import ezPyCrypto as ez
from ezPyCrypto import key

k = key()

#e = k._encRawPub("Hello")
#d = k._decRawPub(e)

#raw = "Now is the time for all good men to come to the aid of their party"
raw = "abcdefghijk"

#trace()

#e = k.encString(raw)
#d = k.decString(e)
#print repr(d)

#e = k.encString("Another test")
#d = k.decString(e)
#print repr(d)

#trace()

bookfile = "/bulk/books/asapersonthinketh/aapt.txt"
#bookfile = "/bulk/books/RebirthingInTheNewAge/rebirthinginthenewage.txt"

fd = open(bookfile)
txt = fd.read()
fd.close()
print "Length of book text: %d" % len(txt)

print "encrypting..."
enc = k.encStringToAscii(txt)

fd = open(bookfile+".enc", "w")
fd.write(enc)
fd.close()

#print "decrypting..."
#dec = k.decStringFromAscii(enc)

keypair = k.exportKeyPrivate()

# now create a new key, import the private key, and decrypt

k1 = key()
k1.importKey(keypair)

#trace()

dec = k1.decStringFromAscii(enc)

if txt == dec:
	print "Success"
else:
	print "fail"

#@-body
#@-node:0::@file easy/autoexec.py
#@-leo
