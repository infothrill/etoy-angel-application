import wx
import logging

from angel_app.log import getLogger
from angel_app.log import enableHandler as enableLogHandler
from angel_app.log import removeHandler as removeLogHandler
log = getLogger(__name__)

_ = wx.GetTranslation

class WxLog(logging.Handler):
    def __init__(self, ctrl):
        logging.Handler.__init__(self)
        self.ctrl = ctrl
    def emit(self, record):
        '''here we jut take the string formatted with the declared Formatter and add a new line
        alternatively you could take the record object and extract the information you need from it
        '''
        self.ctrl.AppendText(self.format(record)+"\n")

class RawWxLog(object):
    def fileno(self):
        1
    def __init__(self, ctrl = None):
        #self.fileno = 0
        if ctrl is None:
            self.doit = False
        else:
            self.ctrl = ctrl
            self.doit = True
    def startLogging(self):
        self.doit = True
    def stopLogging(self):
        self.doit = True
    def setCtrl(self, ctrl):
        self.ctrl = ctrl
    def write(self, buf):
        log.debug(buf)
        if self.doit:
            self.ctrl.AppendText(buf+"\n")

class AutoLoggingButton(wx.Button):
    def __init__(self, parent, label, level):
        wx.Button.__init__(self, parent, label = label)
        self.level = level
        self.Bind(wx.EVT_BUTTON, self.OnButton)

    def OnButton(self, event):
        log.log(self.level, self.GetLabel())

class LogFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title=_("log console"), size = (800, 200))
        sizer = wx.BoxSizer(wx.VERTICAL)
        closeButton = wx.Button(self, wx.ID_CLOSE, _("Close"))
        self.Bind(wx.EVT_BUTTON, self.OnClose, closeButton)
        #debug  = AutoLoggingButton(self, "Close", logging.DEBUG)
        error  = AutoLoggingButton(self, _("Press for ERROR logging event"), logging.ERROR)
        logCtrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.ALL | wx.EXPAND)

        sizer.Add(logCtrl, 1, wx.EXPAND|wx.ALL, 10)
        #sizer.Add(debug, 1, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(error, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        sizer.Add(closeButton, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # here is where the magic begins
        self.loghandler = WxLog(logCtrl)
        self.loghandler.setFormatter(logging.Formatter('%(levelname)-6s %(name)-20s - %(message)s'))

        enableLogHandler('wx', self.loghandler)
        # now for some message formating.
        log.debug("wxLogger initialized")

    def OnClose(self, event):
        removeLogHandler(self.loghandler)
        self.Destroy()
