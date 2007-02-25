# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""Directory listing."""

# system imports
import os
import urllib
import stat
import time

# twisted imports
from twisted.web2 import iweb, resource, http, http_headers

def formatFileSize(size):
    if size < 1024:
        return '%i' % size
    elif size < (1024**2):
        return '%iK' % (size / 1024)
    elif size < (1024**3):
        return '%iM' % (size / (1024**2))
    else:
        return '%iG' % (size / (1024**3))

def formatClones(path):
    from angel_app.resource.local import basic
    from angel_app.resource.remote.clone import cloneFromElement
    
    def links(clone):
        
        return `clone`
        aa =  '<a href="http://' + `clone`+ '%(clone)s">' + clone.host + '</a>'# % clone
        log.info(aa)
        return aa
    
    try:
        return "Clones: " + " ".join([              
                   '<a href="http://' + `clone`+ '">' + clone.host + '</a>'
                   #`cloneFromElement(clone)`
                   #`clone`
                   for clone in [
                                 cloneFromElement(cc) for cc in basic.Basic(path).clones().children]])
    except:
        return ""
    

class DirectoryLister(resource.Resource):
    def __init__(self, pathname, dirs=None,
                 contentTypes={},
                 contentEncodings={},
                 defaultType='text/html'):
        self.contentTypes = contentTypes
        self.contentEncodings = contentEncodings
        self.defaultType = defaultType
        # dirs allows usage of the File to specify what gets listed
        self.dirs = dirs
        self.path = pathname
        resource.Resource.__init__(self)

    def data_listing(self, request, data):
        if self.dirs is None:
            directory = os.listdir(self.path)
            directory.sort()
        else:
            directory = self.dirs

        files = []

        for path in directory:
            url = urllib.quote(path, '/')
            fullpath = os.path.join(self.path, path)
            try:
                st = os.stat(fullpath)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                url = url + '/'
                files.append({
                    'link': url,
                    'linktext': path + "/",
                    'size': '',
                    'type': '-',
                    'lastmod': time.strftime("%Y-%b-%d %H:%M", time.localtime(st.st_mtime)),
                    'clones': formatClones(path)
                    })
            else:
                from twisted.web2.static import getTypeAndEncoding
                mimetype, encoding = getTypeAndEncoding(
                    path,
                    self.contentTypes, self.contentEncodings, self.defaultType)
                
                filesize = st.st_size
                files.append({
                    'link': url,
                    'linktext': path,
                    'size': formatFileSize(filesize),
                    'type': mimetype,
                    'lastmod': time.strftime("%Y-%b-%d %H:%M", time.localtime(st.st_mtime)),
                    'clones': formatClones(path)
                    })

        return files

    def __repr__(self):  
        return '<DirectoryLister of %r>' % self.path
        
    __str__ = __repr__


    def render(self, request):
        title = "Directory listing for %s" % urllib.unquote(request.path)
    
        s= """<html><head><title>%s</title>
        <link href="http://missioneternity.org/files/m221e.css" rel="stylesheet" type="text/css" media="all" />
        <style>
          th, .even td, .odd td { padding-right: 0.5em;}
          .even-dir { background-color: #efe0ef }
          .even { background-color: #eee }
          .odd-dir {background-color: #f0d0ef }
          .odd { background-color: #dedede }
          .icon { text-align: center }
          .listing {
              margin-left: auto;
              margin-right: auto;
              width: 50%%;
              padding: 0.1em;
              }
            
          body { border: 0; padding: 0; margin:}
          h1 {padding: 0.1em; background-color: #777; color: white; border-bottom: thin white dashed;}
</style></head><body><div id="container"><div class="directory-listing"><h1>%s</h1>""" % (title,title)
        s += "<div>" + formatClones(self.path) + "</div>"
        s+="<table>"
        s+="<tr><th>Filename</th><th>Size</th><th>Last Modified</th><th>File Type</th><th>Clones</th></tr>"
        even = False
        for row in self.data_listing(request, None):
            s+='<tr class="%s">' % (even and 'even' or 'odd',)
            s+='<td><a href="%(link)s">%(linktext)s</a></td><td align="right">%(size)s</td><td>%(lastmod)s</td><td>%(type)s</td><td>%(clones)s</td></tr>' % row
            even = not even
                
        s+="</table></div></div></body></html>"
        response = http.Response(200, {}, s)
        response.headers.setHeader("content-type", http_headers.MimeType('text', 'html'))
        return response

__all__ = ['DirectoryLister']
