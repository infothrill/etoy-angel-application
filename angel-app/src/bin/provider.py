"""
DAV server that runs on the 'external' interface -- i.e. the 
communicates with other angel-app instances.
This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the angel-app (except e.g. new clone
metadata).
"""

def main():
    import angel_app.proc.provider

    options = angel_app.proc.provider.boot()
    angel_app.proc.provider.dance(options)


if __name__ == "__main__":
    main()