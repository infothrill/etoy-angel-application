"""
The main GUI module.
"""

import os
import wx

import angel_app.proc.subprocessthread as masterthread
import angel_app.gui.compat.wrap as platformwrap
from angel_app.config import config


from angel_app.log import getLogger
log = getLogger(__name__)

_ = wx.GetTranslation

class AngelMainFrame(wx.Frame):

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
            ("I&mport crypto key...", "Import crypto key...", self.on_file_import_key),
            ("E&xport personal ANGEL KEY...", "Export personal ANGEL KEY...", self.on_file_export_key),  
            ("Purge repository", "Purge repository", self.on_file_purge_repository),
            ("L&og console", "Log console", self.on_log_console)  
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
                        ("S&tart p2p service", "Start p2p service", self.on_net_start),
                        ("S&top p2p service", "Stop p2p service", self.on_net_stop)
                        ]
        return self.__buildMenuWith(netMenuItems)
    
    def __buildHelpMenu(self):
        helpMenuItems = [
                         ("A&bout", "About ANGEL APPLICATION", self.on_about_request),
                         ("ANGEL APPLICATION W&iki (Website)", "http://angelapp.missioneternity.org", self.on_help_wiki),
                         ("M&ISSION ETERNITY (Website)", "http://www.missioneternity.org", self.on_help_m221e),
                         ("Technical Report on ANGEL APPLICATION (Online PDF)", self.TECHNICALREPORT_URL, self.on_help_technicalreport),
                         ("Send a b&ug report (Website)", self.BUGREPORT_URL, self.on_help_bugreport),
                         ("S&oftware License", "Software License", self.on_help_license)
                         ]
        return self.__buildMenuWith(helpMenuItems)

    def __init__(self, parent, ID, title):
        """
        The constructor, initializes the menus, the mainframe with the logo and the statusbar.
        By default, also starts the p2p process automatically on start-up
        """
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(823, 548))
        self.app = wx.GetApp()
        self.frames = []
        # define the menus
        self.menu_bar  = wx.MenuBar()
  
        # file menu
        self.menu_bar.Append(self.__buildFileMenu(), 
                             "&File")

        # network menu
        self.menu_bar.Append(self.__buildNetworkMenu(), 
                             "&Network")

        # Help menu
        self.menu_bar.Append(self.__buildHelpMenu(), 
                             "&Help")

        self.SetMenuBar(self.menu_bar)
        # end define the menus

        self.SetBackgroundColour(wx.WHITE)
        M221E_WELCOME_SCREEN = os.path.join(platformwrap.getResourcePath(), "images", "angel_app_welcomescreen.jpg")
        self.bitmap = wx.Bitmap(M221E_WELCOME_SCREEN)
        wx.EVT_PAINT(self, self.OnPaint)

        self.Centre()

        self.daemon = masterthread.MasterThread()
        self.daemon.setDaemon(True)
        self.daemon.start()

        self.sb = AngelStatusBar(self, self.daemon)
        self.SetStatusBar(self.sb)

        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        
    def on_log_console(self, eventt):
        from angel_app.gui.log import LogFrame
        self.logwin = LogFrame()
        self.logwin.Show(True)
        self.frames.append(self.logwin)

    def OnPaint(self, event):
        """
        Handler for wx.EVT_PAINT event.
        Also draws the m221e logo.
        """
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 0, 0)
    
    def OnQuit(self, event):
        """
        Handler for wx.EVT_CLOSE event
        """
        self.daemon.stop()
        self.Destroy()

    def doExit(self, event):
        """
        Exits the application explicitly
        """
        log.info("Exiting on user request")
        # TODO: how to clean up old frames that are possibly still open?
        try: # the frames might be gone already.... 
            for frame in self.frames:
                frame.Destroy()
        except:
            pass
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
        was_alive = self.daemon.isAlive()
        max = 3
        dlg = wx.ProgressDialog(_("Purging"),
                               _("Please wait while the repository is purged"),
                               maximum = max,
                               parent=self,
                               style = wx.PD_APP_MODAL)
        if self.daemon.isAlive():
            self.daemon.stop()
        dlg.Update(1)
        
        success = False
        if not self.daemon.isAlive():
            from angel_app.admin.directories import removeDirectory 
            removeDirectory('repository')
            dlg.Update(2)
            if was_alive:
                self.daemon.run()
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
                if self.daemon.isAlive():
                    self.daemon.stop()
                    self.daemon.run()
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

    def on_net_start(self, event):
        """
        Starts the p2p process if not running
        """
        if not self.daemon.isAlive():
            log.info("Starting the p2p process")
            self.daemon.run()

    def on_net_stop(self, event):
        """
        Stops the p2p process if running
        """
        if self.daemon.isAlive():
            log.info("Stopping the p2p process")
            self.daemon.stop()
    
    def on_repo_in_filemanager(self, event):
        """
        Opens the local private repository from presenter in the
        file manager
        """
        interface = self.app.config.get("presenter", "listenInterface")
        port = self.app.config.get("presenter", "listenPort")
        platformwrap.showRepositoryInFilemanager(interface, port)
        
    def on_about_request(self, event):
        """
        Shows the about window
        """
        from angel_app.gui.about import AboutWindow 
        aboutWindow = AboutWindow(self, -1, _("About"), style=wx.DEFAULT_DIALOG_STYLE)
        aboutWindow.CentreOnScreen()
        aboutWindow.Show(True)
        
    def on_file_prefs(self, event):
        """
        Shows the about window
        """
        from angel_app.gui.prefs import PrefsWindow 
        self.prefsWindow = PrefsWindow(self, -1, _("Preferences"),
                                        size=(-1, -1),
                                        style=wx.DEFAULT_FRAME_STYLE)
        self.prefsWindow.CentreOnScreen()
        self.prefsWindow.Show(True)
        
    def on_help_license(self, event):
        """
        Shows the license in a scroll box
        """
        from angel_app.gui.about import LicenseWindow 
        licenseWindow = LicenseWindow(self, -1, _("Licence"), size=(500, 400), style=wx.DEFAULT_FRAME_STYLE)
        licenseWindow.CenterOnScreen()
        licenseWindow.Show(True)

    def on_help_presenter(self, event):
        """
        Opens the local presenter website in a web browser
        """
        interface = self.app.config.get("presenter", "listenInterface")
        port = self.app.config.get("presenter", "listenPort")
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
    

class AngelStatusBar(wx.StatusBar):
    """
    Status bar for the main frame. Shows 2 things:
    - currently selected menu
    - p2p status (running/stopped)
    """
    def __init__(self, parent, p2pProc):
        """
        Constructor, takes an additional parameter pointing to the
        thread object runing the p2p process. Initializes a timer to
        see if the p2p process is running.
        """
        self.masterproc = p2pProc
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has one field
        self.SetFieldsCount(2)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-2,-1])

        # We're going to use a timer to drive a status of the p2p-process
        # in the last field.
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(1001)
        self.Notify()

    def Notify(self):
        """
        Timer callback to check if the p2p process is running and
        set the status bar text accordingly.
        """
        if self.masterproc.isAlive():
            status = _("p2p running")
        else:
            status = _("p2p stopped")
        self.SetStatusText(status, 1)


class AngelApp(wx.App):
    """
    The main wx.App
    """
    def OnInit(self):
        """
        Instantiates the main frame and shows it
        """
        self.config = config.getConfig()
        mainframe = AngelMainFrame(None, -1, "ANGEL APPLICATION: THE CODE THAT CROSSES THE DEAD-LINE")
        mainframe.Show(True)
        self.SetTopWindow(mainframe)
        self.test = "testing"
        return True

if __name__ == '__main__':
    pass