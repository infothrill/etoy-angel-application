"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""
def py2appletWorkaroundIgnoreMe():
    """
    Import the other binaries, so py2applet takes them along in the packaging process.
    """
    import maintainer, presenter, provider


def main():
    import angel_app.proc.wxmaster

    options = angel_app.proc.wxmaster.boot()
    angel_app.proc.wxmaster.dance(options)

if __name__ == "__main__":
    main()
