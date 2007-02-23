"""
dh.py

Implementation of Diffie-Hellman key exchange that uses the Python
ryptography Toolkit (http://www.amk.ca/python/code/crypto.html)

Requires that the two parties (Alice and Bob) each agree to use
the same two numbers, 'base' and 'modulus'.

Alice and Bob can reach such agreement in one of two ways:
  1. Prior agreement - choosing and agreeing on the two numbers
     'out of band'.
  2. Alice and Bob use the following protocol:
      - Alice randomly chooses the base and modulus, where the base
        is a small number, and modulus is a prime number of a required
        size (recommend minimum of 2048 bit).
      - Alice sends these two numbers, along with her public key, to Bob.
      - Bob uses these two numbers to generate his public key, which he
        sends to Alice.
After following either of these methods, Alice and Bob can independently
generate their session key.
"""

import pickle
import time
from pdb import set_trace as trace

import gmpy

import Crypto
import Crypto.Util
from Crypto.Util import number, randpool

randomFunc = randpool.RandomPool().get_bytes

def bigPrime(size):
    #t0 = time.time()
    randomPool.stir()
    while 1:
        p = number.getPrime(size, randomFunc)
        #break
        if number.isPrime((p - 1)/2):
            break
    #t1 = time.time()
    #print "took %f seconds" % (t1 - t0)
    return p

def numBits(num):
    """
    Determines number of bits in a number
    """
    bits = 0
    while num != 0:
        num /= 2
        bits += 1
    return bits

lastTime = time.time()
def timeTaken():
    global lastTime
    newTime = time.time()
    timeElapsed = newTime - lastTime
    lastTime = newTime
    return timeElapsed

class DHKeyNotGenerated(Exception):
    """Must generate public key first"""

class DHBadKey(Exception):
    """Tried to import a public key with mismatched parameters"""

class DH:
    """
    Diffie-Hellman Key Exchange class.
    """
    def __init__(self, base=None, modulus=None):
        self.base = base
        self.modulus = modulus
        self.privKey = None
        self.pubKey = None
        self._sessKey = None

    def _makeRandomParms(self, keySize):
        """
        _makeRandomParms - generate random base and exponent.

        Arguments:
         - keySize - number of bits for the modulus
        Returns:
         - None
        """
        baseSize = bigPrime(3)+1
        self.base = bigPrime(baseSize) # random 2-16 bit prime
        self.modulus = bigPrime(keySize)
        self.keySize = keySize

    def generateKey(self, keySize=1024):
        """
        Generate a public key.

        Arguments:
         - keySize - size of public key to generate. Ignored if object
           was created with a base and modulus. Otherwise, default 1024 bits
        """
        if self.base == None or self.modulus == None:
            self._makeRandomParms(keySize)
        self.keySize = keySize
        self.privKey = bigPrime(self.keySize)
        self.pubKey = pow(self.base, self.privKey, self.modulus)

    def exportKey(self):
        """
        Exports a generated public key, as a pickled tuple
        (base, mod, exponent) which can be imported by other party
        with importKey() method.

        Calling this function without first calling generateKey()
        will cause an exception.
        """
        if self.pubKey == None:
            raise DHKeyNotGenerated(
                "You haven't yet generated your DH public key")
        return pickle.dumps((self.base, self.modulus, self.pubKey), True)

    def importKey(self, otherKey):
        """
        Take someone else's public key (exported via publicKey()),
        and determine the session key. An exception is raised if
        the peer's public key contains different base and/or modulus
        to those contained (if any) within this key.

        Arguments:
         - otherKey - pickled tuple - (base, mod, exponent) - for
           other user
        Returns:
         - None
        Exceptions:
         - DHBadKey - conflicting key generation parameters
        """
        peerBase,peerModulus,peerPubKey = pickle.loads(otherKey)
        if self.base == None:
            self.base = peerBase
        if self.base != peerBase:
            raise DHBadKey(
                "Key base mismatch: self=%ld, peer=%ld" % (
                  self.base, peerBase))
        if self.modulus == None:
            self.modulus = peerModulus
        if self.modulus != peerModulus:
            raise DHBadKey(
                "Key modulus mismatch: self=%ld, peer=%ld" % (
                  self.modulus, peerModulus))

        # store peer's public key
        self.peerKey = peerPubKey

        # generate our private key if needed
        if self.privKey == None:
            self.generateKey(numBits(self.modulus))

        self._sessKey = pow(self.peerKey, self.privKey, self.modulus)

    def sessionKey(self):
        """
        Returns the generated session key.

        Arguments:
         - None
        Returns:
         - Session key, as string
        Exceptions:
         - DHKeyNotGenerated - call importKey() first
        """
        if self._sessKey == None:
            raise DHKeyNotGenerated("No session key available")
        return self._sessKey

def test(keySize = 128):
    #trace()
    #print "Creating key objects without predefined parameters"
    bob = DH()
    alice = DH()

    #print "Bob generating %d-bit public key using random parameters" % keySize
    bob.generateKey(keySize)
    bobPubKey = bob.exportKey()

    #print "Alice importing Bob's key and using Bob's parameters"
    alice.importKey(bobPubKey)
    alicePubKey = alice.exportKey()

    #print "Bob importing Alice's key"
    bob.importKey(alicePubKey)

    #print "Uplifting the generated session keys"
    bobSessKey = bob.sessionKey()
    aliceSessKey = alice.sessionKey()

    if bobSessKey == aliceSessKey:
        #print "SUCCESS - matching keys:"
        #print bobSessKey
        pass
    else:
        print "FAIL - different keys"
        print "alice:", aliceSessKey
        print "  bob:", bobSessKey
        raise Exception

thrashTimes = {}
def thrash():
    bits = 64
    while bits <= 256:
        timeTaken()
        test(bits)
        duration = timeTaken()
        thrashTimes[bits] = duration
        print "%5d bits: took %f seconds" % (bits, duration)
        bits *= 2

if __name__ == '__main__':
    test()
