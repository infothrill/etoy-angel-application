from pdb import set_trace as trace
from binascii import hexlify as hexdump
import ezPyCrypto, tempfile, sys

filename = 'pycrypto-1.9a5.win32-py2.2.exe'
#filename = 'ezPyCrypto.py'
#filename = 'example9.py'

def streamTest( blksz ):
    #trace()
    k = ezPyCrypto.key()
    infile  = file( filename, 'rb' )
    outfile = tempfile.TemporaryFile()

    k.encStart()

    while 1:
        plain = infile.read( blksz )
        if not plain: break
        enc =  k.encNext( plain )
        outfile.write(enc)

    outfile.write(k.encEnd())

    infile.seek(0)
    outfile.seek(0)

    k.decStart()

    #trace()

    position = 0
    while 1:
        enc = outfile.read( blksz )
        if not enc: break
        plain = k.decNext( enc )
        if plain != '':
            #trace()
            plainOld = infile.read( len( plain ))
            if plain != plainOld:
                print "fail: size=%d, pos=%d wanted %s, got %s" \
                      % (len(plain),
                         position,
                         repr(plainOld),
                         repr(plain))
                print "Old key=%s IV=%s init=%s" % (
                    hexdump(k._tstSessKey0),
                    hexdump(k._tstIV0),
                    hexdump(k._tstBlk0))
                print "New key=%s IV=%s init=%s" % (
                    hexdump(k._tstSessKey1),
                    hexdump(k._tstIV1),
                    hexdump(k._tstBlk1))
                assert plain == plainOld
        position += len(plain)

    #print
    #print "Old key=%s IV=%s init=%s" % (
    #    hexdump(k._tstSessKey0),
    #    hexdump(k._tstIV0),
    #    hexdump(k._tstBlk0))
    #print "New key=%s IV=%s init=%s" % (
    #    hexdump(k._tstSessKey1),
    #    hexdump(k._tstIV1),
    #    hexdump(k._tstBlk1))

    assert not infile.read()

    k.decEnd()
    infile.close()
    outfile.close()

#sys.stdout = file( 'example9.log', 'w' )

for bs in range(1, 10):
    try:
        print bs, 
        streamTest( bs )
        print 'PASS'
    except AssertionError:
        print 'Assertion Fail'
        #raise
    except KeyboardInterrupt:
        break
    except:
        print 'Other Fail'
        raise

    sys.stdout.flush()
