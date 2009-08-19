import wx
import sys
import os

from angel_app.maintainer.mount import getMountTab
from angel_app.config.config import getConfig
from angel_app.log import getLogger
import  wx.lib.mixins.listctrl  as  listmix
#import images

_ = wx.GetTranslation
log = getLogger(__name__)

def mountDict():
    # convert the mounttab to a dictionary for the ListCtrl:
    mounttab = getMountTab()
    mountdict = {}
    for c, e in enumerate(mounttab):
        tmp = ( e[0], e[1] )
        mountdict[c] = tmp
    return mountdict


class OurListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class MountListCtrlPanel(wx.Panel): #, listmix.ColumnSorterMixin
    def __init__(self, parent, statuslog):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        self.parent = parent # need to remember so we can call parent.OnEdit()

        self.currentItem = 0

        self.statuslog = statuslog
        tID = wx.NewId()
        #self.il = wx.ImageList(16, 16)

        #self.idx1 = self.il.Add(images.getSmilesBitmap())
        #self.sm_up = self.il.Add(images.getSmallUpArrowBitmap())
        #self.sm_dn = self.il.Add(images.getSmallDnArrowBitmap())

        self.list = OurListCtrl(self, tID,
                                 style=wx.LC_REPORT 
                                 | wx.BORDER_SUNKEN
                                 #| wx.BORDER_NONE
                                 #| wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 #| wx.LC_NO_HEADER
                                 | wx.LC_VRULES
                                 | wx.LC_HRULES
                                 | wx.LC_SINGLE_SEL
                                 )
        
        #self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wx/lib/mixins/listctrl.py
        self.itemDataMap = mountDict()
        #listmix.ColumnSorterMixin.__init__(self, 2)
        #self.SortListItems(0, True)

        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        #self.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnItemDelete, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.list)

        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        # for wxMSW
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)

        # for wxGTK
        self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)


    def PopulateList(self):
        if True:
            # for normal, simple columns, you can add them like this:
            self.list.InsertColumn(0, _("Source URL"))
            self.list.InsertColumn(1, _("Mount point"), wx.LIST_FORMAT_RIGHT)
            #self.list.InsertColumn(2, "Status")
        else:
            # but since we want images on the column header we have to do it the hard way:
            info = wx.ListItem()
            info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
            info.m_image = -1
            info.m_format = 0
            info.m_text = _("Source URL")
            self.list.InsertColumnInfo(0, info)

            info.m_format = wx.LIST_FORMAT_RIGHT
            info.m_text = _("Mountpoint")
            self.list.InsertColumnInfo(1, info)

        items = mountDict().items()
        for key, data in items:
            #index = self.list.InsertImageStringItem(sys.maxint, data[0], self.idx1)
            index = self.list.InsertStringItem(sys.maxint, data[0])
            self.list.SetStringItem(index, 1, data[1])
            #self.list.SetStringItem(index, 2, data[2])
            self.list.SetItemData(index, key)

        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)


    def refreshContent(self):
        self.itemDataMap = mountDict()
        items = mountDict().items()
        for key, data in items:
            index = self.list.InsertStringItem(sys.maxint, data[0])
            self.list.SetStringItem(index, 1, data[1])
            self.list.SetItemData(index, key)
        
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        # select  row:
        self.list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (0, 0)
        #return (self.sm_dn, self.sm_up) # arrow icons

    def OnRightDown(self, event):
        self.x = event.GetX()
        self.y = event.GetY()
        #self.statuslog.WriteText("x, y = %s\n" % str((self.x, self.y)))
        item, flags = self.list.HitTest((self.x, self.y))

        if flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)

        event.Skip()


    def getColumnText(self, index, col):
        #print "index: %s, col: %s" % (str(index), str(col))
        item = self.list.GetItem(index, col)
        return item.GetText()


    def OnItemSelected(self, event):
        #self.currentItem = event.m_itemIndex
        #self.statuslog.WriteText("OnItemSelected: %s, %s, %s, %s\n" %
        #                   (self.currentItem,
        #                    self.list.GetItemText(self.currentItem),
        #                    self.getColumnText(self.currentItem, 0),
        #                    self.getColumnText(self.currentItem, 1)))

        event.Skip()


    def OnItemDeselected(self, event):
        #dummyitem = evt.GetItem()
        #self.statuslog.WriteText("OnItemDeselected: %d" % evt.m_itemIndex)

        # Show how to reselect something we don't want deselected
        #if evt.m_itemIndex == 11:
        #    wx.CallAfter(self.list.SetItemState, 11, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        event.Skip()

    def showDialog(self, title, source, mountpoint):
        """
        @return: a (source, mountpoint) pair, unless the dialog was cancelled, in which case we return None
        """
                
        def validate(source, mountpoint):
            """
            @return: an error message, if validation failed, None otherwise
            """                    
            # validate the source url
            from angel_app.uri import parse
            try:
                parse(source)
                # valid uri
            except Exception, e:
                # couldn't parse, so fail    
                return "Not a valid angel-app URI: " + source  + """
Example valid URI: http://missioneternity.org:6221/"""   
            
            # validate the destination path
            try:
                from angel_app.resource.local.basic import Basic
                repositoryPath = wx.GetApp().config.container['common']['repository']
                destination = Basic(repositoryPath + os.sep + mountpoint)
                if not destination.fp.exists() or not destination.isCollection():
                    from angel_app.resource.local.internal.resource import Crypto
                    try:
                        newResource = Crypto(repositoryPath + os.sep + mountpoint)
                        os.mkdir(repositoryPath + os.sep + mountpoint)
                        newResource.seal()
                    except Exception, e:
                        log.warn("Error creating mount point '%s'" % mountpoint, exc_info = e)
                        return "Error creating the mount point '%s'!" % mountpoint
                    else:
                        return None
                else:
                    return "Cannot mount to existing resource '%s'!" % mountpoint

            except Exception, e:
                import traceback, cStringIO
                err = cStringIO.StringIO()
                traceback.print_exc(file=err)
                return "An error occured while validating the mount point: " + err.getvalue()
            
            return None
        
        dlg = MountEditDialog(self, title = _(title), source = source, mountpoint = mountpoint)
        dlg.CenterOnParent()
        
        res = dlg.ShowModal()
        # get user input and clean up:
        source = dlg.getSource()
        mountpoint = dlg.getMountPoint()    
        dlg.Destroy()
        
        # now decide what to do with the input
        
        if wx.ID_CANCEL == res:
            # user aborted
            return None
        else:
            # wx.ID_OK == res 
            
            # validate input
            errorMessage = validate(source, mountpoint)
            
            if None == errorMessage:
                # all is fine, return:
                return (source, mountpoint)
            
            else:
                # display error message and let the user correct it:
                from angel_app.gui.errorDialog import errorDialog
                errorDialog("Invalid mount.", errorMessage)
                return self.showDialog(title, source, mountpoint)
            
    def modifyMountPoints(self, title, oldsource = "", oldmountpoint = ""):
        """
        @param title: title for dialog
        @param oldsource: old value for source uri
        @param oldmountpoint: old value for mount point (file system path relative to repository)
           
        Ask the user to provide a new mount point / source URI.
        Write the results to the config file, if they pass validation.
        """        
        res = self.showDialog(title, oldsource, oldmountpoint)
        if None == res:
            # user cancelled:
            return
        else:
            # store user settings:
            (source, mountpoint) = res
            
            log.debug("source: '%s' mount: %s" % (source, mountpoint))
            config = wx.GetApp().config
            #del config.container['mounttab'][oldsource]
            config.container['mounttab'][source] = mountpoint
            config.commit() 
            
            # refresh the view of available mount points:
            self.list.DeleteAllItems()
            self.refreshContent()      

    def add(self):
        """
        We want to add a new mount point.
        """
        self.modifyMountPoints("Add new mount point")


    def edit(self, item):
        """
        We want to modify a mount point that already exists:
        """
        log.debug("Want to edit %d" % item)
        oldsource = self.getColumnText(item, 0)
        oldmountpoint = self.getColumnText(item, 1)
        self.modifyMountPoints("Edit mount point", oldsource, oldmountpoint)
        
    def delete(self, item):
        if item == -1:
            log.debug("no mount point deleted because item is -1")
            return None
        log.debug("user wants to delete mount point item %s" % `item`)
        dlg = wx.MessageDialog(self, _("Are you sure you want to delete the mount point?"), _('Warning'),
                               wx.ICON_QUESTION | wx.YES_NO | wx.NO_DEFAULT
                               )
        res = dlg.ShowModal()
        log.debug("result of dialogue: %s" % res)
        if res == wx.ID_YES:
            oldsource = self.list.GetItem(item, 0).GetText()
            self.list.DeleteItem(item)
            #del self.itemDataMap[i] // no need, refreshContent() does that for us
            config = wx.GetApp().config
            del config.container['mounttab'][oldsource]
            config.commit()
            #log.debug("mount points after deletion: %s" % self.itemDataMap)
            self.list.DeleteAllItems()
            self.refreshContent()
            self.statuslog.WriteText(_("Mount point deleted"))
            try:
                wx.GetApp().p2p.conditionalRestart()
            except Exception, e:
                log.warn("Caught an exception while trying to restart the p2p process", exc_info = e)
                self.statuslog.WriteText(_("Could not restart the p2p process"))

        dlg.Destroy()

    def OnItemActivated(self, event):
        # activation happens on double click
        #self.statuslog.WriteText("OnItemActivated: %s\nTopItem: %s" %
        #                   (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))
        self.edit(event.m_itemIndex)

    def OnBeginEdit(self, event):
        #self.statuslog.WriteText("OnBeginEdit")
        event.Veto() # don't make the cell editable
        #event.Allow()
        #self.parent.OnEdit(event)

    def OnItemDelete(self, event):
        log.debug("OnItemDelete")
        selectedItem = self.GetListCtrl().GetFocusedItem()
        self.delete(selectedItem)

    def OnColClick(self, event):
        #self.statuslog.WriteText("OnColClick: %d\n" % event.GetColumn())
        event.Skip()

    def OnColRightClick(self, event):
        #item = self.list.GetColumn(event.GetColumn())
        #self.statuslog.WriteText("OnColRightClick: %d %s\n" %
        #                   (event.GetColumn(), (item.GetText(), item.GetAlign(),
        #                                        item.GetWidth(), item.GetImage())))
        event.Skip()

    def OnDoubleClick(self, event):
        #self.statuslog.WriteText("OnDoubleClick item %s\n" % self.list.GetItemText(self.currentItem))
        event.Skip()

    def OnRightClick(self, event):
        #self.statuslog.WriteText("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnItemDelete, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnRightClickEdit, id=self.popupID2)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, _("Delete"))
        menu.Append(self.popupID2, _("Edit"))

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu, (self.x, self.y))
        menu.Destroy()

    def OnRightClickEdit(self, event):
        selectedItem = self.GetListCtrl().GetFocusedItem()
        self.edit(selectedItem)

    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        #self.list.SetDimensions(0, 0, w, h)
        self.GetListCtrl().SetDimensions(0, 0, w, h)

class MountsPanel(wx.Panel):
    def __init__(self, parent, statuslog):
        wx.Panel.__init__(self, parent)

        vboxList = wx.BoxSizer(wx.VERTICAL)

        tableBox = wx.BoxSizer(wx.VERTICAL)
        boxButtons = wx.BoxSizer(wx.HORIZONTAL)
        buttonpanel = wx.Panel(self, -1)
        buttonpanel.SetSizer(boxButtons)

        txtTitle = wx.StaticText(self, -1, _("Currently configured mount points"), style=wx.ALIGN_CENTER)
        vboxList.Add(txtTitle, proportion = 0, flag = wx.TOP|wx.ALIGN_CENTER, border = 5)

        self.listPanel = MountListCtrlPanel(self, statuslog)
        self.listPanel.SetSizer(tableBox)
        vboxList.Add(self.listPanel, proportion = 2, flag = wx.EXPAND|wx.ALL, border = 12)

        _buttonsParent = buttonpanel
        button_Add = wx.Button(_buttonsParent, wx.ID_ADD)
        button_Edit = wx.Button(_buttonsParent, wx.ID_EDIT)
        button_Delete = wx.Button(_buttonsParent, wx.ID_DELETE)
        
        boxButtons.Add(button_Add, flag = wx.ALL, border = 5)
        boxButtons.Add(button_Edit, flag = wx.ALL, border = 5)
        boxButtons.Add(button_Delete, flag = wx.ALL, border = 5)
    
        vboxList.Add( buttonpanel, proportion = 0, flag=wx.ALL|wx.ALIGN_CENTER, border = 5)

        self.SetSizer(vboxList)

        wx.EVT_BUTTON(self, wx.ID_EDIT, self.OnEdit)
        wx.EVT_BUTTON(self, wx.ID_DELETE, self.OnDelete)
        wx.EVT_BUTTON(self, wx.ID_ADD, self.OnAdd)

    def OnEdit(self, event):
        selectedItem = self.listPanel.GetListCtrl().GetFocusedItem()
        self.listPanel.edit(selectedItem)

    def OnAdd(self, event):
        self.listPanel.add()

    def OnDelete(self, event):
        selectedItem = self.listPanel.GetListCtrl().GetFocusedItem()
        self.listPanel.delete(selectedItem)


class MountEditDialog(wx.Dialog):
    def __init__(self, parent, title = _("Edit mount point"), source = '', mountpoint = ''):
        wx.Dialog.__init__(self, parent, -1, title)

        self.SetAutoLayout(True)
    
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        textBox.Add(wx.StaticText(self, -1, _("Please specify the source URL you want to backup and the place\n(mount point) where the source shall be backed up to:")), proportion = 1, flag = wx.ALIGN_LEFT)

        fgs = wx.FlexGridSizer(2, 2)

        labelSource = wx.StaticText(self, -1, _("Source URL: "))
        fgs.Add(labelSource, proportion = 0, flag = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)

        self.sourceCtrl = wx.TextCtrl(self, -1, source, size = (400,-1)) 
        fgs.Add(self.sourceCtrl, proportion = 2, flag = wx.EXPAND|wx.ALL, border = 2)

        labelMountpoint = wx.StaticText(self, -1, _("Mount point: "))
        fgs.Add(labelMountpoint, proportion = 0, flag = wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
        self.mountpointCtrl = wx.TextCtrl(self, -1, mountpoint) 
        fgs.Add(self.mountpointCtrl, proportion = 2, flag = wx.EXPAND|wx.ALL, border = 2)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        b = wx.Button(self, wx.ID_OK)
        b.SetDefault()
        buttons.Add(b, proportion = 0, flag = wx.ALL, border = 10)
        buttons.Add(wx.Button(self, wx.ID_CANCEL), proportion = 0, flag = wx.ALL, border = 10)

        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(textBox, proportion = 0, flag = wx.ALL, border = 15)
        border.Add(fgs, proportion = 2, flag = wx.EXPAND|wx.ALL, border = 15)

        border.Add(buttons, proportion = 1, flag=wx.ALL|wx.ALIGN_CENTER)
        self.SetSizer(border)
        border.Fit(self)
        self.Layout()

    def getMountPoint(self):
        return self.mountpointCtrl.GetValue()

    def getSource(self):
        return self.sourceCtrl.GetValue()


class MountsWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(500, 300))

        self.mountStatusbar = self.CreateStatusBar(1, 0)

        Sizer = wx.BoxSizer(wx.VERTICAL)
        self.mountsPanel = MountsPanel(self, Log())
        Sizer.Add(self.mountsPanel, proportion = 2, flag=wx.ALL|wx.EXPAND, border = 1)
        self.SetSizer(Sizer)

        self.Centre()

        self.Show(True)

class Log(object):
    """
    The log output is redirected to the status bar of the containing frame.
    """

    def WriteText(self,text_string):
        self.write(text_string)

    def write(self,text_string):
        wx.GetApp().GetTopWindow().SetStatusText(text_string)

if __name__ == '__main__':
    """
    This allows us to run it separately from the rest of the GUI
    """
    from angel_app.log import initializeLogging
    initializeLogging()
    app = wx.App(0)
    app.config = getConfig()
    MountsWindow(None, -1, _('Mounts'))
    app.MainLoop()