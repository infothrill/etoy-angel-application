# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

"""Directory listing."""

# system imports
import os
import urllib
import stat
import time

DEBUG = True

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
    
    try:
        return ", ".join([              
                   '<a href="http://' + `clone`+ '">' + clone.host + '</a>'
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
                    'clones': formatClones(fullpath)
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
                    'clones': formatClones(fullpath)
                    })

        return files

    def __repr__(self):  
        return '<DirectoryLister of %r>' % self.path
        
    __str__ = __repr__


    def render(self, request):
        title = "Directory listing for %s" % urllib.unquote(request.path)
        # TODO we need a better way to transform between url paths and file paths...
        pathSegments = ["/"] + urllib.unquote(request.path.strip("/")).split(os.sep)
        linkTargets = ["/"]
        accumulated = "/"
        for segment in pathSegments[1:]:
            accumulated += urllib.quote(segment) + "/"
            linkTargets.append(accumulated)
        linkList = "Directory listing for " +'<a href="%s">%s</a>' % ("/", "/")  + \
            "/".join(['<a href="%s">%s</a>' % (linkTarget, pathSegment) 
                    for (linkTarget, pathSegment) in 
                    zip(linkTargets[1:], pathSegments[1:])
                    ])
    
        s= """<html><head><title>angel-app: %s</title>
        <link href="http://missioneternity.org/files/m221e.css" rel="stylesheet" type="text/css" media="all" />
        <style>
          .even-dir { background-color: #eeeeee }
          .even { background-color: #eeeeee }
          .odd-dir {background-color: #ffffff }
          .odd { background-color: #ffffff }
          th { white-space:nowrap; text-align:left; padding-right: 20px;}
          td { vertical-align: top; }
          div { margin-top: 20px; }
        </style>
        </head><body style="margin-bottom: 50px;">
        <div id="container"  style="width:650px; padding:30px 0px 0px 0px;">
        <div style="text-align:right"><a href="http://www.missioneternity.org/"><img style="border:0;" src="http://angelapp.missioneternity.org/moin/share/moin/htdocs/rightsidebar/img/m221e-batch-logo.jpg" alt="MISSION ETERNITY"></a></div>
        <div class="directory-listing">       
        <h1><a href="http://angelapp.missioneternity.org/">angel-app</a>: %s</h1>""" % (title, linkList)
        s += "<div> Clones: " + formatClones(self.path) + "</div>"
        s+='<div><table width="100%">'
        s+="<tr><th>Filename</th><th>Size</th><th>Last Modified</th><th>File Type</th><th>Clones</th></tr>"
        even = False
        for row in self.data_listing(request, None):
            s+='<tr class="%s">' % (even and 'even' or 'odd',)
            s+='\n<td><a href="%(link)s">%(linktext)s</a></td><td align="right">%(size)s</td><td>%(lastmod)s</td><td>%(type)s</td><td>%(clones)s</td></tr>' % row
            even = not even
                
        s+="""</table></div>
        </div></div></body></html>"""
        response = http.Response(200, {}, s)
        response.headers.setHeader("content-type", http_headers.MimeType('text', 'html'))
        return response

__all__ = ['DirectoryLister']
