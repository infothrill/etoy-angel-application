#!/usr/bin/env python

"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""
def py2appletWorkaroundIgnoreMe():
    """
    Import the other binaries, so py2applet takes them along in the packaging process.
    """
    # explicitly import sax parser for py2app:
    import xml.sax.drivers2.drv_pyexpat
    # fix to make py2applet happy:
    import twisted.web2.dav.method.copymove
    import twisted.web2.dav.method.delete
    import twisted.web2.dav.method.lock
    import twisted.web2.dav.method.mkcol
    import twisted.web2.dav.method.propfind
    import twisted.web2.dav.method.proppatch
    import twisted.web2.dav.method.put
    import twisted.web2.dav.method.report_expand
    import twisted.web2.dav.method.report
    # end fix to make py2applet happy
    import maintainer, presenter, provider

def main():
    import angel_app.proc.master

    options = angel_app.proc.master.boot()
    angel_app.proc.master.dance(options)

if __name__ == "__main__":
    main()
