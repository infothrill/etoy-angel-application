"""
The main GUI module.
"""

import os
import wx

import angel_app.proc.subprocessthread as masterthread
import angel_app.gui.compat.wrap as platformwrap
from angel_app.config import config
from angel_app.gui import statusbar


from angel_app.log import getLogger
log = getLogger(__name__)

_ = wx.GetTranslation


class AngelMainFrameBase(wx.Frame):
    BUGREPORT_URL = "https://gna.org/support/?func=additem&group=angel-app" # use "support", because "bugs" requires a gna account
    TECHNICALREPORT_URL = "http://svn.gna.org/viewcvs/*checkout*/angel-app/trunk/angel-app/doc/report/m221e-angel-app-0.2.pdf" # TODO: this URL needs to have NO version in it!!!


    def __withMenu(self, menu):
        """
        Return a function that will bind an item to this menu
        """         
        def append(text, help, action):            
            itemID = wx.NewId()
            menu.Append(itemID, text, help)
            self.Bind(wx.EVT_MENU, action, id=itemID)               
        return append

    def __appendItemsToMenu(self, menu, items):
        """
        Append the list of items to the menu.
        """
        appendToMenu = self.__withMenu(menu)
        for (text, help, action) in items:
            appendToMenu(text, help, action)
            
    def __buildMenuWith(self, items):
        menu = wx.Menu()
        self.__appendItemsToMenu(menu, items)
        return menu
        
    def __buildFileMenu(self):
        """
        Build/populate the File menu.
        """              

        filemanager = (platformwrap.isMacOSX() and "Finder") or "file manager"            
        fileMenuItems = [
            ("O&pen repository in web-browser", "Open repository in web-browser", self.on_help_presenter),
            ("O&pen repository in %s" % filemanager, "Open repository in %s" % filemanager, self.on_repo_in_filemanager),
            ("Purge repository", "Purge repository", self.on_file_purge_repository),
            #("L&og console", "Log console", self.on_log_console)  
                         ]

        file_menu = self.__buildMenuWith(fileMenuItems)

        # finally, attach "special" (i.e. with custom-id's) functionality:
        file_menu.Append(wx.ID_PREFERENCES, _("P&references"), _("Preferences"))
        self.Bind(wx.EVT_MENU, self.on_file_prefs, id=wx.ID_PREFERENCES)

        file_menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.doExit, id=wx.ID_EXIT)

        file_menu.Append(wx.ID_CLOSE, "Q&uit", "Quit")
        self.Bind(wx.EVT_MENU, self.doExit, id=wx.ID_CLOSE)

        return file_menu

        
    def __buildNetworkMenu(self):
        netMenuItems = [
                        ("Sta&rt p2p service", "Start p2p service", self.on_net_start),
                        ("Sto&p p2p service", "Stop p2p service", self.on_net_stop),
                        ("Re&start p2p service", "Restart p2p service", self.on_net_restart),
                        ]
        return self.__buildMenuWith(netMenuItems)
    
    def __buildUserMenu(self):
        keysMenuItems = [
                        ("I&mport crypto key...", "Import crypto key...", self.on_file_import_key),
                        ("E&xport personal ANGEL KEY...", "Export personal ANGEL KEY...", self.on_file_export_key),
                        ]
        keysMenu = self.__buildMenuWith(keysMenuItems)

        menuItems = [
                        ("Configure backups...", "Configure backups...", self.on_mounts),
                        ("Interactive A&ngelshell...", "Interactive Angelshell...", self.on_angelshell),
                    ]
        m = self.__buildMenuWith(menuItems)
        m.AppendMenu(wx.NewId(),'Keys', keysMenu)
        return m
    
    def __buildHelpMenu(self):
        helpMenuItems = [
                         ("ANGEL APPLICATION W&iki (Website)", "http://angelapp.missioneternity.org", self.on_help_wiki),
                         ("M&ISSION ETERNITY (Website)", "http://www.missioneternity.org", self.on_help_m221e),
                         ("Technical Report on ANGEL APPLICATION (Online PDF)", self.TECHNICALREPORT_URL, self.on_help_technicalreport),
                         ("Send a b&ug report (Website)", self.BUGREPORT_URL, self.on_help_bugreport),
                         ("S&oftware License", "Software License", self.on_help_license)
                         ]
        about_menu = self.__buildMenuWith(helpMenuItems)
        
        about_menu.Append(wx.ID_ABOUT, _("A&bout"), _("About ANGEL APPLICATION"))
        self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)
        
        return about_menu

    def _buildMenus(self):
        # define the menus
        self.menu_bar  = wx.MenuBar()
  
        # file menu
        self.menu_bar.Append(self.__buildFileMenu(), 
                             "&File")

        # network menu
        self.menu_bar.Append(self.__buildNetworkMenu(), 
                             "&Network")

        # Settings menu
        self.menu_bar.Append(self.__buildUserMenu(), 
                             "&User")

        # Help menu
        self.menu_bar.Append(self.__buildHelpMenu(), 
                             "&Help")

        self.SetMenuBar(self.menu_bar)
        # end define the menus

    def OnQuit(self, event):
        """
        Handler for wx.EVT_CLOSE event
        """
        wx.GetApp().p2p.stop()
        self.Destroy()

    def doExit(self, event):
        """
        Exits the application explicitly
        """
        log.info("Exiting on user request")
        self.Close(True)


    def askIFPurgeRepository(self):
        questiontext = _('By purging your repository, you delete all locally stored data. Are you sure you want to purge the repository?') 
        dlg = wx.MessageDialog(self, questiontext, _('Warning'),
                               wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT
                               )
        res = dlg.ShowModal()
        dlg.Destroy()
        if res == wx.ID_YES:
            return True
        else:
            return False
        
    def on_file_purge_repository(self, evt):
        if not self.askIFPurgeRepository():
            return

        # remember the current state of the p2p proc:
        was_alive = wx.GetApp().p2p.isAlive()
        max = 3
        dlg = wx.ProgressDialog(_("Purging"),
                               _("Please wait while the repository is purged"),
                               maximum = max,
                               parent=self,
                               style = wx.PD_APP_MODAL)
        if wx.GetApp().p2p.isAlive():
            wx.GetApp().p2p.stop()
        dlg.Update(1)
        
        success = False
        if not wx.GetApp().p2p.isAlive():
            from angel_app.admin.directories import removeDirectory 
            removeDirectory('repository')
            dlg.Update(2)
            if was_alive:
                wx.GetApp().p2p.run()
            dlg.Update(3)
            dlg.Destroy()
            success = True
        else:
            dlg.Destroy()
            
        if not success:
            dlg = wx.MessageDialog(self, _('Error'),
                                   _('The repository could not be purged!'),
                                   wx.OK | wx.ICON_ERROR
                                   #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                                   )
            dlg.ShowModal()
            dlg.Destroy()
        return 1
 
    def on_angelshell(self, event):
        from angel_app.gui.angelshell import AngelShellWindow
        window = AngelShellWindow(parent = self, id = -1, title = _("Angelshell"), size=None)
        window.CenterOnParent()
        window.Show()

    def on_file_export_key(self, evt):
        saveasfilename = "ANGEL.key"
        wildcard = "Key files (*.key)|*.key|"     \
                   "All files (*.*)|*.*"
        # Create the dialog. In this case the current directory is forced as the starting
        # directory for the dialog, and a default file name is forced.
        dlg = wx.FileDialog(
            self, message="Save ANGEL KEY as ...", defaultDir=os.getcwd(), 
            defaultFile=saveasfilename, wildcard=wildcard, style=wx.SAVE
            )
        
        # This sets the default filter that the user will initially see. Otherwise,
        # the first filter in the list will be used by default.
        dlg.SetFilterIndex(0)
        
        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        keyselectionresult = dlg.ShowModal()
        if keyselectionresult == wx.ID_OK:
            exportfilename = dlg.GetPath()
            #print "You selected filename %s\n" % exportfilename
        
            from angel_app.contrib.ezPyCrypto import key as ezKey
            key = ezKey()
            exportfile = open(exportfilename, 'wb')
            exportfile.write( key.exportKey() )
            exportfile.close()
            #
            # TODO: error checking on export!
            #
        elif keyselectionresult == wx.ID_CANCEL:
            self.sb.SetStatusText(_("personal ANGEL KEY export canceled"), 0)
   
        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()

    def on_file_import_key(self, evt):
        # This is how you pre-establish a file filter so that the dialog
        # only shows the extension(s) you want it to.
        wildcard = "Key files (*.key)|*.key|"     \
                   "All files (*.*)|*.*"
        #self.log.WriteText("CWD: %s\n" % os.getcwd())

        # Create the dialog. In this case the current directory is forced as the starting
        # directory for the dialog, and no default file name is forced.
        dlg = wx.FileDialog(
            self, message= _("Import crypto key ..."), defaultDir=os.getcwd(), 
            defaultFile="", wildcard=wildcard, style=wx.OPEN
            )

        # This sets the default filter that the user will initially see. Otherwise,
        # the first filter in the list will be used by default.
        #dlg.SetFilterIndex(0)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        keyselectionresult = dlg.ShowModal()
        if keyselectionresult == wx.ID_OK:
            path = dlg.GetPath()
            #self.log.WriteText('You selected "%s"' % path)
            log.debug('User selected "%s" for key import' % path)
            keynamedlg = wx.TextEntryDialog(
                    self, _('Please enter a name for the key (preferably something that associates the key with its usage):'),
                    _('Enter key name'), '')
            keynamedlg.CenterOnParent()
            #default keyname:
            keyname = os.path.basename(path)
            keynamedlg.SetValue(keyname)
    
            res = keynamedlg.ShowModal()
            if  res == wx.ID_OK:
                keyname = keynamedlg.GetValue()
                keynamedlg.Destroy()
            elif res == wx.ID_CANCEL:
                #print "HIT CANCEL"
                keynamedlg.Destroy()
                dlg.Destroy()
                self.sb.SetStatusText(_("Crypto key import canceled"), 0)
                return False
                #self.log.WriteText('You entered: %s\n' % keynamedlg.GetValue())    

            f = open(path, 'rb')
            from angel_app.admin.secretKey import importKey
            result = False
            try:
                result = importKey(f, keyname)
                f.close()
            except NameError, err:
                self.showErrorDialog(self, str(err))
                self.sb.SetStatusText(_("Crypto key import failed"), 0)
            if result == True:
                self.sb.SetStatusText(_("Crypto key successfully imported"), 0)
                # restart the p2p process (makes sure the key is now known)
                wx.GetApp().p2p.conditionalRestart()
        elif keyselectionresult == wx.ID_CANCEL:
                self.sb.SetStatusText(_("Crypto key import canceled"), 0)

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()


    def showErrorDialog(self, parent, message):
        dlg = wx.MessageDialog(parent, message,
                               _('Error:'),
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def on_mounts(self, event):
        from angel_app.gui.mounttab import MountsWindow 
        window = MountsWindow(self, -1, _("Mounts"))
        window.CenterOnParent()
        window.ShowModal()

    def on_net_restart(self, event):
        """
        Restart the p2p process
        """
        wx.GetApp().p2p.conditionalRestart()
        #self.on_net_stop(event)
        #self.on_net_start(event)
        
    def on_net_start(self, event):
        """
        Starts the p2p process if not running
        """
        if not wx.GetApp().p2p.isAlive():
            log.info("Starting the p2p process")
            wx.GetApp().p2p.run()

    def on_net_stop(self, event):
        """
        Stops the p2p process if running
        """
        if wx.GetApp().p2p.isAlive():
            log.info("Stopping the p2p process")
            wx.GetApp().p2p.stop()
    
    def on_repo_in_filemanager(self, event):
        """
        Opens the local private repository from presenter in the
        file manager
        """
        interface = wx.GetApp().config.get("presenter", "listenInterface")
        port = wx.GetApp().config.get("presenter", "listenPort")
        platformwrap.showRepositoryInFilemanager(interface, port)
        

    def on_about_request(self, event):
        """
        Shows the about window
        """
        from angel_app.gui.about import AboutWindow 
        aboutWindow = AboutWindow(self, -1, _("About"), style=wx.DEFAULT_DIALOG_STYLE)
        aboutWindow.CenterOnParent()
        aboutWindow.Show(True)
        
    def on_file_prefs(self, event):
        """
        Shows the preferences window
        """
        from angel_app.gui.prefs import PrefsWindow 
        self.prefsWindow = PrefsWindow(self, -1, _("Preferences"),
                                        size=(-1, -1),
                                        style=wx.DEFAULT_FRAME_STYLE)
        self.prefsWindow.CenterOnParent()
        self.prefsWindow.ShowModal()
        
    def on_help_license(self, event):
        """
        Shows the license in a scroll box
        """
        from angel_app.gui.about import LicenseWindow 
        licenseWindow = LicenseWindow(self, -1, _("Licence"), size=(500, 400), style=wx.DEFAULT_FRAME_STYLE)
        licenseWindow.CenterOnParent()
        licenseWindow.Show(True)

    def on_help_presenter(self, event):
        """
        Opens the local presenter website in a web browser
        """
        interface = wx.GetApp().config.get("presenter", "listenInterface")
        port = wx.GetApp().config.get("presenter", "listenPort")
        platformwrap.showURLInBrowser("http://%s:%s"% (interface, port))

    def on_help_wiki(self, event):
        """
        Opens http://angel-app.missioneternity.org in a web browser
        """
        platformwrap.showURLInBrowser("http://angelapp.missioneternity.org")
    
    def on_help_m221e(self, event):
        """
        Opens http://www.missioneternity.org in a web browser
        """
        platformwrap.showURLInBrowser("http://www.missioneternity.org")

    def on_help_bugreport(self, event):
        """
        Opens BUGREPORT_URL in web-browser
        """
        platformwrap.showURLInBrowser(self.BUGREPORT_URL)

    def on_help_technicalreport(self, event):
        """
        Opens TECHINCALREPORT_URL in a web browser
        """
        platformwrap.showURLInBrowser(self.TECHNICALREPORT_URL)


class AngelMainNoteBook(wx.Notebook): # deprecated
    def __init__(self, parent, id, statuslog):
        wx.Notebook.__init__(self, parent, id, size=(-1,-1))
        self.parent = parent
        self.statuslog = statuslog

        from angel_app.gui import mounttab
        win = mounttab.MountsPanel(self, statuslog = self.statuslog)
        self.AddPage(win, _('Mounts'))
        
        from angel_app.gui import prefs
        win = prefs.PrefsPanel(self, statuslog = self.statuslog)
        self.AddPage(win, _('Preferences'))
        
        from angel_app.gui.angelshell import angelshell 
        self.AddPage(angelshell(parent = self), _('Angelshell'))
    
        from angel_app.gui import welcome
        win = welcome.WelcomePanel(self, statuslog = self.statuslog)
        self.InsertPage(0, win, _('Welcome'), select = True)


class AngelMainWindow(AngelMainFrameBase):
    def __init__(self, parent, id, title):
        """
        The constructor, initializes the menus, the mainframe with the logo and the statusbar.
        By default, also starts the p2p process automatically on start-up
        """
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(820, 535))

        self._buildMenus()

        self.SetStatusBar(statusbar.AngelStatusBar(self))

        #self.doNoteBookLayout() # deprecated
        self.doControllerLayout()

        # start the p2p process:
        if wx.GetApp().config.getboolean('gui', 'autostartp2p'):
            wx.GetApp().p2p.start()

        # make sure to have a handler when quitting (shutdown p2p) 
        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        self.CenterOnScreen()
        self.Show(True)

    def doNoteBookLayout(self):
        """
        main window organized with tabs
        """
        log.debug("deprecated layout ;-) ")
        Sizer = wx.BoxSizer(wx.VERTICAL)
        self.nb = AngelMainNoteBook(self, -1, statuslog = statusbar.StatusLog())
        Sizer.Add(self.nb, proportion = 2, flag=wx.RIGHT|wx.LEFT|wx.EXPAND, border = 20)
        self.SetSizer(Sizer)
        
    def doControllerLayout(self):
        """
        media player style main window organized. For now, we just show the intro screen.
        """
        Sizer = wx.BoxSizer(wx.VERTICAL)
        from angel_app.gui import welcome
        win = welcome.WelcomePanel(self, None)
        Sizer.Add(win)


class AngelApp(wx.App):
    """
    The main wx.App
    """
    def OnInit(self):
        """
        Instantiates the main frame and shows it
        """
        bitmapfilename = os.path.join(platformwrap.getResourcePath(), "images", "skull.png")
        assert os.path.isfile(bitmapfilename), "Splash screen picture '%s' could not be found" % bitmapfilename
        aBitmap = wx.Image(name = bitmapfilename).ConvertToBitmap()
        splashDuration = 3000 # milliseconds
        splash = wx.SplashScreen(aBitmap, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT, splashDuration, None)

        self.config = config.getConfig()
        self.p2p = masterthread.MasterThread()
        self.p2p.setDaemon(True)
        mainframe = AngelMainWindow(None, -1, _("ANGEL APPLICATION"))
        mainframe.Show(True)
        self.SetTopWindow(mainframe)
        return True

if __name__ == '__main__':
    pass