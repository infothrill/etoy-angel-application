"""
DAV server that runs on the 'internal' interface -- i.e. the UI.
This guy is safe and has access to the secret key(s). I.e. it 
may commit data to the angel-app.
"""

def main():
    import angel_app.proc.presenter

    options = angel_app.proc.presenter.boot()
    angel_app.proc.presenter.dance(options)

if __name__ == "__main__":
    main()
