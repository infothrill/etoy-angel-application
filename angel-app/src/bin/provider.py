#!/usr/bin/env python

"""
Essentially the DAV server that runs on the 'external' interface -- i.e. the 
server that provides local data to other ANGEL APPLICATION instances.

This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the local repository (except e.g. new clone
metadata).
"""

def main():
    import angel_app.proc.provider as provider

    options = provider.boot()
    provider.dance(options)


if __name__ == "__main__":
    main()