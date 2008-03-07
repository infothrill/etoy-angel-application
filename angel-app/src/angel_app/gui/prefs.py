import wx

from angel_app.log import getLogger
from angel_app.gui.statusbar import StatusLog

log = getLogger(__name__)

_ = wx.GetTranslation

class PrefsPanel(wx.Panel):
    def __init__(self, parent, statuslog):
        wx.Panel.__init__(self, parent)

        self.parent = parent
        self.statuslog = statuslog

        self.app = wx.GetApp()
 
        vboxMain = wx.BoxSizer(wx.VERTICAL)

        hboxCfgFile = wx.BoxSizer(wx.HORIZONTAL)
        hboxCfgFile.Add(wx.StaticText(self, -1, _("Using configuration file: ")), proportion = 0, flag = wx.ALIGN_CENTER, border = 0)
        hboxCfgFile.Add(wx.StaticText(self, -1, self.app.config.getConfigFilename()), proportion = 0, flag = wx.ALIGN_CENTER, border = 0)
        vboxMain.Add(hboxCfgFile, proportion = 0, flag = wx.ALL | wx.ALIGN_CENTER, border = 4)

        ######################
        # Network
        ######################
        panelNetworkSettings = wx.Panel(self, -1)
        sbSizerNetwork = wx.StaticBoxSizer(wx.StaticBox(panelNetworkSettings, -1, _("Network")), wx.VERTICAL)
        panelNetworkSettings.SetSizer(sbSizerNetwork)
        panelNetworkSettings.SetAutoLayout(True)
        sbSizerNetwork.Fit(panelNetworkSettings)
        vboxMain.Add(panelNetworkSettings, 0, wx.ALL | wx.EXPAND, 5)

        vboxNetwork = wx.BoxSizer(wx.VERTICAL) # inside the panelNetworksettings
        sbSizerNetwork.Add(vboxNetwork, 0, wx.ALL | wx.EXPAND, 3)

        ## new grid with 2 cols
        gridnode = wx.FlexGridSizer(2, 2, 1, 1) # 2 cols
        gridnode.AddGrowableCol(1) # second column epands
        gridnode.Add(wx.StaticText(panelNetworkSettings, -1, _("Node name: ")), 0, wx.ALIGN_CENTER_VERTICAL)

        #### Node name ####
        self.nodeName = wx.TextCtrl(panelNetworkSettings, -1, unicode(self.app.config.get('maintainer', 'nodename')))
        gridnode.Add(self.nodeName, 1, wx.EXPAND| wx.ALIGN_CENTER_VERTICAL)
        gridnode.Add(wx.StaticText(self, -1, ''), 0, wx.ALIGN_CENTER_VERTICAL) # nop filler
        vboxNetwork.Add(gridnode, 0, wx.ALL | wx.EXPAND, 0)

        ## new grid with 4 cols
        gridnet = wx.FlexGridSizer(2, 4, 1, 1) # 3 cols
        gridnet.AddGrowableCol(1) # second column epands

        #### Provider #####

        ID_onProviderCheckbox = wx.NewId()
        self.providerCheckbox = wx.CheckBox(panelNetworkSettings, ID_onProviderCheckbox, _('Provide data'))
        self.providerCheckbox.SetValue(self.app.config.get('provider','enable'))
        gridnet.Add(self.providerCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)

        gridnet.Add(wx.StaticText(panelNetworkSettings, -1, _("Port: ")), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)

        self.providerPort = wx.TextCtrl(panelNetworkSettings, -1, unicode(self.app.config.get('provider', 'listenPort')))
        gridnet.Add(self.providerPort, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
      
        ID_onDefaultProviderPort = wx.NewId()
        self.defaultProviderPortButton = wx.Button(panelNetworkSettings, ID_onDefaultProviderPort, _("Default"))
        gridnet.Add(self.defaultProviderPortButton, 0, wx.ALIGN_CENTER_VERTICAL)

        #### Presenter port #####
        ID_onPresenterCheckbox = wx.NewId()
        self.presenterCheckbox = wx.CheckBox(panelNetworkSettings, ID_onPresenterCheckbox, _('Enable file management'))
        self.presenterCheckbox.SetValue(self.app.config.get('presenter','enable'))
        gridnet.Add(self.presenterCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)

        gridnet.Add(wx.StaticText(panelNetworkSettings, -1, _("Port: ")), 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)

        self.presenterPort = wx.TextCtrl(panelNetworkSettings, -1, unicode(self.app.config.get('presenter', 'listenPort')))
        gridnet.Add(self.presenterPort, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)
      
        ID_onDefaultPresenterPort = wx.NewId()
        self.defaultPresenterPortButton = wx.Button(panelNetworkSettings, ID_onDefaultPresenterPort, _("Default"))
        gridnet.Add(self.defaultPresenterPortButton, 0, wx.ALIGN_CENTER_VERTICAL)
      
        # maintainer enable/disable?
        ID_onMaintainerCheckbox = wx.NewId()
        self.maintainerCheckbox = wx.CheckBox(panelNetworkSettings, ID_onMaintainerCheckbox, _('Maintain repository'))
        self.maintainerCheckbox.SetValue(self.app.config.get('maintainer','enable'))
        gridnet.Add(self.maintainerCheckbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)


        gridnet.Add(wx.StaticText(self, -1, ''), 0, wx.ALIGN_CENTER_VERTICAL) # nop filler
        gridnet.Add(wx.StaticText(self, -1, ''), 0, wx.ALIGN_CENTER_VERTICAL) # nop filler
        gridnet.Add(wx.StaticText(self, -1, ''), 0, wx.ALIGN_CENTER_VERTICAL) # nop filler

        ID_onUseIpv6Checkbox = wx.NewId()
        self.useIpv6Checkbox = wx.CheckBox(panelNetworkSettings, ID_onUseIpv6Checkbox, _('enable IPv6'))
        self.useIpv6Checkbox.SetValue(self.app.config.get('provider','useIPv6'))
        gridnet.Add(self.useIpv6Checkbox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 20)
        
        vboxNetwork.Add(gridnet, 0, wx.ALL | wx.EXPAND, 0)

        ######################
        # Other
        ######################
        panelOther = wx.Panel(self, -1)
        sbSizerOther = wx.StaticBoxSizer(wx.StaticBox(panelOther, -1, _("Other")), flag = wx.VERTICAL)
        panelOther.SetSizer(sbSizerOther)
        panelOther.SetAutoLayout(True)
        sbSizerOther.Fit(panelOther)
        vboxMain.Add(panelOther, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 5)

        gridOther = wx.FlexGridSizer(2, 2, 1, 1)
        #gridOther.AddGrowableCol(1) # second column epands

        #### Log level ####
        gridOther.Add(wx.StaticText(panelOther, -1, _("Log level: ")), proportion = 0, flag = wx.ALIGN_CENTER_VERTICAL)

        from angel_app.log import getAllowedLogLevels
        levelNames = map(unicode, getAllowedLogLevels())
        self.loglevelChooser = wx.ComboBox(panelOther, wx.NewId(), 
                                    self.app.config.get('common', 'loglevel'), 
                                    wx.Point(-1, -1), 
                                    wx.Size(-1, -1), levelNames, wx.TE_READONLY)
        
        gridOther.Add(self.loglevelChooser, 0, wx.EXPAND)
      
        #### Max clones ####
        gridOther.Add(wx.StaticText(panelOther, -1, _("Max clones: ")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.maxClones = wx.TextCtrl(panelOther, -1, unicode(self.app.config.get('common', 'maxclones')))
        gridOther.Add(self.maxClones, 0, wx.EXPAND)

        ### Desktop notification ###
        ID_onDesktopNotificationCheckbox = wx.NewId()
        self.desktopnotificationCheckbox = wx.CheckBox(panelOther, ID_onDesktopNotificationCheckbox, _('Enable desktop notifications'))
        self.desktopnotificationCheckbox.SetValue(self.app.config.get('common','desktopnotification'))
        gridOther.Add(self.desktopnotificationCheckbox, proportion = 0, flag = wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border = 20)

        sbSizerOther.Add(gridOther, proportion = 0, flag = wx.ALL | wx.EXPAND, border = 4)
        ### Apply/OK/Cancel buttons ###
        hboxButtons = self.buttons()

        vboxMain.Add(hboxButtons, proportion = 0, flag = wx.ALL | wx.ALIGN_CENTER, border = 4)

        ### do layout ###
        self.SetSizer(vboxMain)
        self.Fit()

        # add the button event hooks:
        wx.EVT_BUTTON(self, ID_onDefaultProviderPort, self.onDefaultProviderPort)
        wx.EVT_BUTTON(self, ID_onDefaultPresenterPort, self.onDefaultPresenterPort)
        wx.EVT_BUTTON(self, wx.ID_OK, self.onOK)
        wx.EVT_BUTTON(self, wx.ID_CANCEL, self.onCancel)

    def buttons(self):
        hboxButtons = wx.BoxSizer(wx.HORIZONTAL)

        self.buttonOK = wx.Button(self, wx.ID_OK, _("Apply"))
        hboxButtons.Add(self.buttonOK, 0, wx.ALL | wx.EXPAND, 1)

        #self.buttonCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        #hboxButtons.Add(self.buttonCancel, 0, wx.ALL | wx.EXPAND, 1)
        return hboxButtons

    def onDefaultProviderPort(self, event):
        """Reset to default value"""
        self.providerPort.SetValue(u'6221')

    def onDefaultPresenterPort(self, event):
        """Reset to default value"""
        self.presenterPort.SetValue(u'6222')

    def savePrefs(self):
        self.app.config.container['common']['loglevel']= self.loglevelChooser.GetValue()
        self.app.config.container['provider']['listenPort'] = self.providerPort.GetValue()
        self.app.config.container['provider']['enable'] = self.providerCheckbox.GetValue()
        self.app.config.container['presenter']['listenPort'] = self.presenterPort.GetValue()
        self.app.config.container['presenter']['enable'] = self.presenterCheckbox.GetValue()
        self.app.config.container['common']['maxclones'] = self.maxClones.GetValue()
        self.app.config.container['provider']['useIPv6'] = self.useIpv6Checkbox.GetValue()
        self.app.config.container['maintainer']['enable'] = self.maintainerCheckbox.GetValue()
        self.app.config.container['maintainer']['nodename'] = self.nodeName.GetValue()
        self.app.config.container['common']['desktopnotification'] = self.desktopnotificationCheckbox.GetValue()

        self.app.config.commit()
        
    def onOK(self, event):
        self.savePrefs()
        wx.GetApp().p2p.conditionalRestart()
        self.statuslog.WriteText("Preferences saved")

    def onCancel(self, event):
        pass

class PrefsPanelForWindow(PrefsPanel):
    """
    A special class inherited from PrefsPanel where buttons are different
    and behave "window-style"
    """
    def buttons(self):
        hboxButtons = wx.BoxSizer(wx.HORIZONTAL)

        self.buttonOK = wx.Button(self, wx.ID_OK, _("OK"))
        hboxButtons.Add(self.buttonOK, 0, wx.ALL | wx.EXPAND, 1)

        self.buttonCancel = wx.Button(self, wx.ID_CANCEL, _("Cancel"))
        hboxButtons.Add(self.buttonCancel, 0, wx.ALL | wx.EXPAND, 1)
        return hboxButtons

    def onOK(self, event):
        self.savePrefs()
        wx.GetApp().p2p.conditionalRestart()
        self.statuslog.WriteText(_("Preferences saved"))
        self.closeMe()

    def onCancel(self, event):
        self.closeMe()

    def closeMe(self):
        self.parent.Close()


class PrefsWindow(wx.Dialog):
    """Preferences dialog class"""
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, 
                size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        """Initialize preferences dialog window"""
      
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        Sizer  = wx.BoxSizer(wx.VERTICAL)
        p = PrefsPanelForWindow(self, statuslog = StatusLog())
        Sizer.Add(p, proportion = 1, flag = wx.ALL | wx.EXPAND, border = 0)
        self.SetSizer(Sizer)
        self.Fit()
