

def boot():
    # here we don't do anything (yet)
    pass

def dance(options):
    import angel_app.wx.main
    app = angel_app.wx.main.AngelApp(0)
    app.MainLoop()


if __name__ == '__main__':
    options = boot()
    dance(options)