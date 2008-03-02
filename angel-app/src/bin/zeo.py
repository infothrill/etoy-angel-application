"""
Wrapper to run ZEO ZODB.
"""

def main():
    from angel_app.proc import zeo
    zeo.main()

if __name__ == "__main__":
    main()