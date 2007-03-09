
import angel_app.wx.main
import wx

class AngelSplashScreen(wx.SplashScreen):
    """
    Create a splash screen widget.
    """
    def __init__(self, parent=None):
        # This is a recipe to a the screen.
        # Modify the following variables as necessary.
        aBitmap = wx.Image(name = "images/angelsplash.jpg").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 4000 # milliseconds
        # Call the constructor with the above arguments in exactly the
        # following order.
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        wx.Yield()

    def OnExit(self, evt):
        self.Hide()
        # MyFrame is the main frame.
        #frame = angel_app.wx.main.AngelMainFrame(None, -1, "Angel-App: CROSSING THE DEAD-LINE")
        #self.app.SetTopWindow(frame)
        #frame.Show(True)

        # The program will freeze without this line.
        evt.Skip()  # Make sure the default handler runs too...