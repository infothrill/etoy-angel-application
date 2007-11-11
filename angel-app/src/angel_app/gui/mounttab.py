import wx
import sys

from angel_app.admin.initializeRepository import getMountTab
from angel_app.config.config import getConfig
from angel_app.log import getLogger
from angel_app.log import initializeLogging
import  wx.lib.mixins.listctrl  as  listmix
#import images

_ = wx.GetTranslation
log = getLogger(__name__)

def mountDict():
    # convert the mounttab to a dictionary for the ListCtrl:
    mounttab = getMountTab()
    mountdict = {}
    c = 1
    for e in mounttab:
        tmp = ( e[0], e[1] )
        mountdict[c] = tmp
        c += 1
    return mountdict


#tableData = mountDict()

class OurListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class MountListCtrlPanel(wx.Panel): #, listmix.ColumnSorterMixin
    def __init__(self, parent, log):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        self.parent = parent # need to remember so we can call parent.OnEdit()

        self.currentItem = 0

        self.log = log
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
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnItemDelete, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
        self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self.list)
        self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self.list)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self.list)
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
            self.list.InsertColumn(0, _("Source"))
            self.list.InsertColumn(1, _("Mount point"), wx.LIST_FORMAT_RIGHT)
            #self.list.InsertColumn(2, "Status")
        else:
            # but since we want images on the column header we have to do it the hard way:
            info = wx.ListItem()
            info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
            info.m_image = -1
            info.m_format = 0
            info.m_text = _("Source")
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

        # select first row:
        #self.list.SetItemState(self.currentItem, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

        # show how to change the colour of a couple items
#        item = self.list.GetItem(1)
#        item.SetTextColour(wx.BLUE)
#        self.list.SetItem(item)
#        item = self.list.GetItem(2)
#        item.SetTextColour(wx.RED)
#        self.list.SetItem(item)


    def refreshContent(self):
        #cur = self.currentItem
        #self.list.ClearAll()
        #wx.CallAfter(self.PopulateList)
        #self.list.SetItemState(cur, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        #return
        self.itemDataMap = mountDict()
        items = mountDict().items()
        for key, data in items:
            #index = self.list.InsertImageStringItem(sys.maxint, data[0], self.idx1)
            index = self.list.InsertStringItem(sys.maxint, data[0])
            self.list.SetStringItem(index, 1, data[1])
            #self.list.SetStringItem(index, 2, data[2])
            self.list.SetItemData(index, key)
        
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
        self.log.WriteText("x, y = %s\n" % str((self.x, self.y)))
        item, flags = self.list.HitTest((self.x, self.y))

        if flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)

        event.Skip()


    def getColumnText(self, index, col):
        #print "index: %s, col: %s" % (str(index), str(col))
        item = self.list.GetItem(index, col)
        return item.GetText()


    def OnItemSelected(self, event):
        ##print event.GetItem().GetTextColour()
        self.currentItem = event.m_itemIndex
        self.log.WriteText("OnItemSelected: %s, %s, %s, %s\n" %
                           (self.currentItem,
                            self.list.GetItemText(self.currentItem),
                            self.getColumnText(self.currentItem, 0),
                            self.getColumnText(self.currentItem, 1)))

#        if self.currentItem == 10:
#            self.log.WriteText("OnItemSelected: Veto'd selection\n")
            #event.Veto()  # doesn't work
            # this does
#            self.list.SetItemState(10, 0, wx.LIST_STATE_SELECTED)

        event.Skip()


    def OnItemDeselected(self, evt):
        item = evt.GetItem()
        self.log.WriteText("OnItemDeselected: %d" % evt.m_itemIndex)

        # Show how to reselect something we don't want deselected
#        if evt.m_itemIndex == 11:
#            wx.CallAfter(self.list.SetItemState, 11, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


    def OnItemActivated(self, event):
        # double click
        self.currentItem = event.m_itemIndex
        self.log.WriteText("OnItemActivated: %s\nTopItem: %s" %
                           (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))
        self.parent.OnEdit(event)

    def OnBeginEdit(self, event):
        log.debug("OnBeginEdit")
        event.Veto() # don't make the cell editable
        #event.Allow()
        self.parent.OnEdit(event)

    def OnItemDelete(self, event):
        #self.parent.OnDelete(event)
        self.log.WriteText("Mount point removed")

    def OnColClick(self, event):
        self.log.WriteText("OnColClick: %d\n" % event.GetColumn())
        event.Skip()

    def OnColRightClick(self, event):
        item = self.list.GetColumn(event.GetColumn())
        self.log.WriteText("OnColRightClick: %d %s\n" %
                           (event.GetColumn(), (item.GetText(), item.GetAlign(),
                                                item.GetWidth(), item.GetImage())))

    def OnColBeginDrag(self, event):
        self.log.WriteText("OnColBeginDrag\n")
        ## Show how to not allow a column to be resized
        #if event.GetColumn() == 0:
        #    event.Veto()


    def OnColDragging(self, event):
        self.log.WriteText("OnColDragging\n")

    def OnColEndDrag(self, event):
        self.log.WriteText("OnColEndDrag\n")

    def OnDoubleClick(self, event):
        self.log.WriteText("OnDoubleClick item %s\n" % self.list.GetItemText(self.currentItem))
        event.Skip()

    def OnRightClick(self, event):
        self.log.WriteText("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnItemDelete, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnPopupFour, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnPopupFive, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.OnPopupSix, id=self.popupID6)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, "Delete")
        menu.Append(self.popupID2, "Iterate Selected")
        menu.Append(self.popupID3, "ClearAll and repopulate")
        menu.Append(self.popupID4, "DeleteAllItems")
        menu.Append(self.popupID5, "GetItem")
        menu.Append(self.popupID6, "Edit")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu, (self.x, self.y))
        menu.Destroy()


#    def OnPopupOne(self, event):
#        self.log.WriteText("Popup one\n")
#        print "FindItem:", self.list.FindItem(-1, "Roxette")
#        print "FindItemData:", self.list.FindItemData(-1, 11)

    def OnPopupTwo(self, event):
        self.log.WriteText("Selected items:\n")
        index = self.list.GetFirstSelected()

        while index != -1:
            self.log.WriteText("      %s: %s\n" % (self.list.GetItemText(index), self.getColumnText(index, 1)))
            index = self.list.GetNextSelected(index)

    def OnPopupThree(self, event):
        self.log.WriteText("Popup three\n")
        self.list.ClearAll()
        wx.CallAfter(self.PopulateList)

    def OnPopupFour(self, event):
        self.list.DeleteAllItems()

    def OnPopupFive(self, event):
        item = self.list.GetItem(self.currentItem)
        print item.m_text, item.m_itemId, self.list.GetItemData(self.currentItem)

    def OnPopupSix(self, event):
        self.list.EditLabel(self.currentItem)


    def OnSize(self, event):
        w,h = self.GetClientSizeTuple()
        self.list.SetDimensions(0, 0, w, h)

class MountsPanel(wx.Panel):
    def __init__(self, parent, log):
        wx.Panel.__init__(self, parent)

        vboxList = wx.BoxSizer(wx.VERTICAL)

        tableBox = wx.BoxSizer(wx.VERTICAL)
        boxButtons = wx.BoxSizer(wx.HORIZONTAL)
        buttonpanel = wx.Panel(self, -1)
        buttonpanel.SetSizer(boxButtons)

        txtTitle = wx.StaticText(self, -1, _("Configured mounts:"), style=wx.ALIGN_LEFT)
        vboxList.Add(txtTitle, proportion = 0, flag = wx.ALL, border = 5)

        self.listCtrl = MountListCtrlPanel(self, log)
        self.listCtrl.SetSizer(tableBox)
        vboxList.Add(self.listCtrl, proportion = 2, flag = wx.EXPAND|wx.ALL, border = 12)

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
        list = self.listCtrl.GetListCtrl()
        item = list.GetFocusedItem()
        i =  list.GetItemData(item)
        log.debug("Want to edit %d" % item)
        oldsource = self.listCtrl.getColumnText(item, 0)
        oldmountpoint = self.listCtrl.getColumnText(item, 1)

        dlg = MountEditDialog(self, source = oldsource , mountpoint = oldmountpoint)
        dlg.CenterOnParent()
        res = dlg.ShowModal()
        log.debug("result of dialogue: %s" % res)
        if res == wx.ID_OK:
            source = dlg.getSource()
            mountpoint = dlg.getMountPoint()
            log.debug("source: '%s' mount: %s" % (source, mountpoint))
            #self.listCtrl.itemDataMap[i][0] = str(source)
            #self.listCtrl.itemDataMap[i][1] = str(mountpoint)
            config = wx.GetApp().config
            del config.container['mounttab'][oldsource]
            config.container['mounttab'][source] = mountpoint
            config.commit()
            list.DeleteAllItems()
            #self.listCtrl.PopulateList()
            self.listCtrl.refreshContent()

        dlg.Destroy()

    def OnAdd(self, event):
        list = self.listCtrl.GetListCtrl()
        dlg = MountEditDialog(self, title = _("Add mount"))
        dlg.CenterOnParent()
        res = dlg.ShowModal()
        log.debug("result of dialogue: %s" % res)
        if res == wx.ID_OK:
            source = dlg.getSource()
            mountpoint = dlg.getMountPoint()
            log.debug("source: '%s' mount: %s" % (source, mountpoint))
            #self.listCtrl.itemDataMap[i][0] = str(source)
            #self.listCtrl.itemDataMap[i][1] = str(mountpoint)
            config = wx.GetApp().config
            #del config.container['mounttab'][oldsource]
            config.container['mounttab'][source] = mountpoint
            config.commit()
            list.DeleteAllItems()
            #self.listCtrl.PopulateList()
            self.listCtrl.refreshContent()

        dlg.Destroy()
        print self.listCtrl.itemDataMap

    def OnDelete(self, event):
        #self.listCtrl.OnItemDelete(event)
        list = self.listCtrl.GetListCtrl()
        item = list.GetFocusedItem()
        i =  list.GetItemData(item)
        oldsource = self.listCtrl.getColumnText(item, 0)
        list.DeleteItem(item)
        del self.listCtrl.itemDataMap[i]
        config = wx.GetApp().config
        del config.container['mounttab'][oldsource]
        config.commit()
        log.debug("After deletion: %s" % self.listCtrl.itemDataMap)


class MountEditDialog(wx.Dialog):
    def __init__(self, parent, title = _("Edit mount"), source = '', mountpoint = ''):
        wx.Dialog.__init__(self, parent, -1, title)

        self.SetAutoLayout(True)
    
        textBox = wx.BoxSizer(wx.HORIZONTAL)
        textBox.Add(wx.StaticText(self, -1, "What data shall be backed up to which folder?"), proportion = 1)

        fgs = wx.FlexGridSizer(2, 2)

        labelSource = wx.StaticText(self, -1, _("Source: "))
        fgs.Add(labelSource, proportion = 0, flag = wx.ALIGN_RIGHT)

        self.sourceCtrl = wx.TextCtrl(self, -1, source) 
        fgs.Add(self.sourceCtrl, proportion = 2, flag = wx.EXPAND|wx.ALL, border = 2)

        labelMountpoint = wx.StaticText(self, -1, _("Mount point: "))
        fgs.Add(labelMountpoint, proportion = 0, flag = wx.ALIGN_RIGHT)
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
        border.Add(buttons, proportion = 1)
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
    initializeLogging()
    app = wx.App(0)
    app.config = getConfig()
    MountsWindow(None, -1, _('mounts'))
    app.MainLoop()