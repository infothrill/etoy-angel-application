import wx

from angel_app.log import getLogger
log = getLogger(__name__)

_ = wx.GetTranslation

class PrefsWindow(wx.Dialog):
    """Preferences dialog class"""


    def __init__(self, parent, id, title, pos=wx.DefaultPosition, 
                size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        """Initialize preferences dialog window"""
      
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        self.app = wx.GetApp()
 
        vboxMain = wx.BoxSizer(wx.VERTICAL)

        hboxCfgFile = wx.BoxSizer(wx.HORIZONTAL)
        hboxCfgFile.Add(wx.StaticText(self, -1, _("Config file: ")), 0, wx.ALIGN_CENTER_VERTICAL)
        hboxCfgFile.Add(wx.StaticText(self, -1, self.app.config.getConfigFilename()), 1, wx.EXPAND, 0)
        vboxMain.Add(hboxCfgFile, 0, wx.ALL | wx.EXPAND, 4)

        ######################
        # Network
        ######################
        panelNetworkSettings = wx.Panel(self, -1)
        sbSizerNetwork = wx.StaticBoxSizer(wx.StaticBox(panelNetworkSettings, -1, _("Network")), wx.VERTICAL)
        panelNetworkSettings.SetSizer(sbSizerNetwork)
        panelNetworkSettings.SetAutoLayout(True)
        sbSizerNetwork.Fit(panelNetworkSettings)
        vboxMain.Add(panelNetworkSettings, 0, wx.ALL | wx.EXPAND, 5)

        gridnet = wx.FlexGridSizer(2, 3, 1, 1) # 3 cols
        gridnet.AddGrowableCol(1) # second column epands

        #### Provider port #####
        gridnet.Add(wx.StaticText(panelNetworkSettings, -1, _("Provider listen port: ")), 0, wx.ALIGN_CENTER_VERTICAL)

        self.providerPort = wx.TextCtrl(panelNetworkSettings, -1, unicode(self.app.config.get('provider', 'listenPort')))
        gridnet.Add(self.providerPort, 0, wx.ALIGN_CENTER_VERTICAL)
      
        ID_onDefaultProviderPort = wx.NewId()
        self.defaultProviderPortButton = wx.Button(panelNetworkSettings, ID_onDefaultProviderPort, _("Default"))
        gridnet.Add(self.defaultProviderPortButton, 0, wx.ALIGN_CENTER_VERTICAL)

        #### Presenter port #####
        gridnet.Add(wx.StaticText(panelNetworkSettings, -1, _("Presenter listen port: ")), 0, wx.ALIGN_CENTER_VERTICAL)

        self.presenterPort = wx.TextCtrl(panelNetworkSettings, -1, unicode(self.app.config.get('presenter', 'listenPort')))
        gridnet.Add(self.presenterPort, 0, wx.ALIGN_CENTER_VERTICAL)
      
        ID_onDefaultPresenterPort = wx.NewId()
        self.defaultPresenterPortButton = wx.Button(panelNetworkSettings, ID_onDefaultPresenterPort, _("Default"))
        gridnet.Add(self.defaultPresenterPortButton, 0, wx.ALIGN_CENTER_VERTICAL)
      
        ID_onUseIpv6Checkbox = wx.NewId()
        self.useIpv6Checkbox = wx.CheckBox(panelNetworkSettings, ID_onUseIpv6Checkbox, _('Use IPv6'))
        self.useIpv6Checkbox.SetValue(self.app.config.get('provider','useIPv6'))
        gridnet.Add(self.useIpv6Checkbox, 0, wx.ALIGN_CENTER_VERTICAL)
        
        sbSizerNetwork.Add(gridnet, 0, wx.ALL | wx.EXPAND, 4)

        ######################
        # Other
        ######################
        panelTest = wx.Panel(self, -1)
        sbSizerTest = wx.StaticBoxSizer(wx.StaticBox(panelTest, -1, _("Other")), wx.VERTICAL)
        panelTest.SetSizer(sbSizerTest)
        panelTest.SetAutoLayout(True)
        sbSizerTest.Fit(panelTest)
        vboxMain.Add(panelTest, 0, wx.ALL | wx.EXPAND, 5)

        gridtest = wx.FlexGridSizer(2, 2, 1, 1)
        gridtest.AddGrowableCol(1) # second column epands

        #### Log level ####
        gridtest.Add(wx.StaticText(panelTest, -1, _("Log level: ")), 0, wx.ALIGN_CENTER_VERTICAL)

        from angel_app.log import getAllowedLogLevels
        levelNames = map(unicode, getAllowedLogLevels())
        levelNames.sort()
        self.loglevelChooser = wx.ComboBox(panelTest, wx.NewId(), 
                                    self.app.config.get('common', 'loglevel'), 
                                    wx.Point(-1, -1), 
                                    wx.Size(-1, -1), levelNames, wx.TE_READONLY)
        
        gridtest.Add(self.loglevelChooser, 0, wx.EXPAND)
      
        #### Max clones ####
        gridtest.Add(wx.StaticText(panelTest, -1, _("Max clones: ")), 0, wx.ALIGN_CENTER_VERTICAL)
        self.maxClones = wx.TextCtrl(panelTest, -1, unicode(self.app.config.get('common', 'maxclones')))
        gridtest.Add(self.maxClones, 0, wx.EXPAND)

        sbSizerTest.Add(gridtest, 0, wx.ALL | wx.EXPAND, 4)
        
        # OK, add OK/Cancel buttons

        hboxButtons = wx.BoxSizer(wx.HORIZONTAL)


        ID_ON_OK = wx.NewId()
        self.buttonOK = wx.Button(self, ID_ON_OK, _("OK"))
        hboxButtons.Add(self.buttonOK, 0, wx.ALL | wx.EXPAND, 1)

        ID_ON_CANCEL = wx.NewId()
        self.buttonCancel = wx.Button(self, ID_ON_CANCEL, _("Cancel"))
        hboxButtons.Add(self.buttonCancel, 0, wx.ALL | wx.EXPAND, 1)

        vboxMain.Add(hboxButtons, 0, wx.ALL | wx.ALIGN_RIGHT, 4)

        self.SetSizer(vboxMain)
        self.Fit()

        # add the button event hooks:
        wx.EVT_CHECKBOX(self, ID_onUseIpv6Checkbox, self.onUseIpv6Checkbox)

        wx.EVT_BUTTON(self, ID_onDefaultProviderPort, self.onDefaultProviderPort)
        wx.EVT_BUTTON(self, ID_onDefaultPresenterPort, self.onDefaultPresenterPort)
        wx.EVT_BUTTON(self, ID_ON_OK, self.onOK)
        wx.EVT_BUTTON(self, ID_ON_CANCEL, self.onCancel)


    def onDefaultProviderPort(self, event):
        """Reset to default value"""
        self.providerPort.SetValue(u'6221')

    def onDefaultPresenterPort(self, event):
        """Reset to default value"""
        self.presenterPort.SetValue(u'6222')

    def onUseIpv6Checkbox(self, event):
        """use or don't use ipv6?"""
        #print self.useIpv6Checkbox.GetValue()
        pass

    def onOK(self, event):
        """
        Save the configuration
        """
        self.app.config.container['common']['loglevel']= self.loglevelChooser.GetValue()
        self.app.config.container['provider']['listenPort'] = self.providerPort.GetValue()
        self.app.config.container['presenter']['listenPort'] = self.presenterPort.GetValue()
        self.app.config.container['common']['maxclones'] = self.maxClones.GetValue()
        self.app.config.container['provider']['useIPv6'] = self.useIpv6Checkbox.GetValue()

        self.app.config.commit()
      
        self.Destroy()


    def onCancel(self, event):
        """
        Close dialog window discarding changes
        """
        self.Destroy()
        