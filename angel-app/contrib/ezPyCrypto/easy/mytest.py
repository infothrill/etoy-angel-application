#@+leo
#@+node:0::@file easy/mytest.py
#@+body
import ezPyCrypto

raw = """This is raw and rearing to go right now. And this string just keeps going
on and on because we have to test things out with a very large amount of test,
to see what the overhead of encryption actally is. With small amounts of data, there
seems to be a really severe overhead going on which might be a problem. And we
have to see what happens with longer amounts of data.
"""

fd = open("/bulk/books/asapersonthinketh/aapt.txt")
raw = fd.read()
fd.close()

mykey = ezPyCrypto.key(512, 'RSA')
#mykey = ezPyCrypto.key(512, 'ElGamal')

print "encrypting..."
enc = mykey.encrypt(raw)
print "decrypting..."
dec = mykey.decrypt(enc)
print "done"

#print "Raw key:     ", raw
#print "Decrypts as: ", dec
print "Orig length = %d, enc len = %d" % (len(raw), len(enc))

exppub = mykey.exportKey()
exppriv = mykey.exportKeyPrivate()

#print "Exported lengths - public %d, private %d" % (len(exppub), len(exppriv))

kpub = ezPyCrypto.key(exppub)
kpriv = ezPyCrypto.key(exppriv)

print "Decrypting with exported privkey"
#print repr(kpriv.decrypt(enc))

print "Encrypting/decrypting in ascii form"
ea = kpub.encryptAscii(raw)
#print "Encrypted Message:"
#print ea
ead = kpriv.decryptAscii(ea)
#print "Decrypted:"
#print ead

if ead != raw:
	print "not the same"
else:
	print "same"

#print "Decrypting with exported pubkey"
#print repr(kpub.decrypt(enc))


#@-body
#@-node:0::@file easy/mytest.py
#@-leo
