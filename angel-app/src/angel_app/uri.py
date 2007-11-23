"""
URI parser for angel-app.
"""

legalMatters = """
 Copyright (c) 2005, etoy.VENTURE ASSOCIATION
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without modification, 
 are permitted provided that the following conditions are met:
 *  Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
 *  Redistributions in binary form must reproduce the above copyright notice, 
    this list of conditions and the following disclaimer in the documentation 
    and/or other materials provided with the distribution.
 *  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to 
    endorse or promote products derived from this software without specific prior 
    written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
 EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
 OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
 SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT 
 OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
"""

author = """Vincent Kraeutler, 2007"""

from angel_app.config import config
from netaddress.rfc3986 import port, host, path_abempty
from pyparsing import Literal, Optional, Or

AngelConfig = config.getConfig()
providerport = AngelConfig.getint("provider", "listenPort")
    
scheme = Or([Literal("http"), Literal("https")]).setResultsName("scheme")
prefix = Optional(scheme + Literal("//:"))
path = path_abempty.setResultsName("path")

angelPort = Optional(Literal(":") + port, default = providerport)
angelPath = Optional(path, default = "/")
angelHost = Optional(host, default = "localhost")
# URI grammar as used in angel-app
angelURI = prefix + angelHost + angelPort + angelPath

def parse(uri = ""):
    try:
        return angelURI.parseString(uri)
    except:
        raise ValueError, "Failed to parse URI: " + `uri`
