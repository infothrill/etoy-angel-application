import wx

def errorDialog(anErrorType = "ERROR",  message = "default error message"):
    """
    Inform the user of an error (via a dialog).
    """
    dlg = wx.MessageDialog(None, message, anErrorType, wx.OK | wx.ICON_ERROR)
    
    if dlg.ShowModal() == wx.ID_OK:
        # block until we receive confirmation
        pass
    
    dlg.Destroy()