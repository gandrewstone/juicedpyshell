#!/usr/bin/env python

#**** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
# 
# The Original Code is PyShell code.
# 
# The Initial Developer of the Original Code is Todd Whiteman.
# Portions created by the Initial Developer are Copyright (C) 2007-2008.
# All Rights Reserved.
# 
# Contributor(s):
#   Todd Whiteman
#   Andrew Stone
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
#**** END LICENSE BLOCK *****

#
# Overview:
#   Provides Python evaluation and completions for the PyShell UI.
#

import os
import sys
import time
import traceback
import thread
import types
import threading

# Add this script directory into the path.
sys.path.append(os.path.dirname(__file__) + os.sep + "juice")

# Add the user's ~ directory to the module path.
homeDir = os.environ["HOME"]
if homeDir:
  sys.path.append(homeDir)

print sys.path
#print os.getcwd()

import handle
import dynxul
from threadhelper import *

from cStringIO import StringIO

from xpcom import components, ServerException, nsError
from xpcom.server import WrapObject

toPrint = []
def myPrinter(s):
  toPrint.append(s)


class pyShell:
    _com_interfaces_ = [components.interfaces.pyIShell]
    _reg_clsid_ = "{4e5c9764-d465-4fef-ae24-8032f257d174}"
    _reg_contractid_ = "@twhiteman.netfirms.com/pyShell;1"
    _reg_desc_ = "Python shell service"
    periodicCallCount = 0
    returned = []    

    pyshellGlobals = {
        # Give away some free items...
        "os": os,
        "sys": sys,
        "time": time,
        # And xpcom accessors.
        "components": components,
        "Components": components,
        # And manipulation of the PyShell itself
        "dynxul": dynxul,
        # And then the threaded print and logging
        "log": myPrinter,
        "prt": myPrinter,
        "hprt": dynxul.hprt,
        "_log_": myPrinter
        # does not work: "docLock": docLock        
    }

    def __init__(self):
        global threadDb,browserContext
        self.deferred = browserContext
        self.pyshellGlobals["browserContext"]= browserContext
        self.thrd = threadDb
        self.pyshellGlobals["threads"]= threadDb
        self.pyshellGlobals["me"] = self
#        self.docLock.acquire()

    def initFinish(self):
        """?? This function is needed due to a chicken-and-egg issue when starting up the XUL window and this pyShell.
        This function is called by the pyShell content document i.e. pyshell.html once it is loaded and running.
        """
        dynxul.init(None) #self.docLock)

        # Start user code if it is available
        self.evalPythonString("try:\n  from psStartup import *\n  psStartup()\nexcept ImportError:\n  pass\n")        

    def _eval_code_and_return_result(self, code):
        return eval(code, self.pyshellGlobals, self.pyshellGlobals)

    # This little exec snippet comes from the python mailing list, see:
    # http://mail.python.org/pipermail/python-list/2005-June/328628.html
    def _exec_code_and_get_output(self, code):
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exec str(code) in self.pyshellGlobals, self.pyshellGlobals
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

    def periodic(self):
        global toPrint
        #outp = ""
        #old_stdout = sys.stdout
        #sys.stdout = StringIO()
        try:
          #print "+"
          
          self.deferred.runDeferred(self.pyshellGlobals,self.pyshellGlobals)
        finally:
          #sys.stdout = old_stdout
          pass

        outp = "\n".join([str(x) for x in toPrint])
        toPrint = []
          
        t = outp + "\n".join([repr(x) for x in self.returned])
        self.returned = []
        #if not t: t = "."
        #if self.periodicCallCnt&127==0: print ".",
        #self.periodicCallCnt+=1
        self.unlockDoc()
        return t

    def unlockDoc(self):
      """?? This function unlocks the document mutex so that threads that need to access the doc can do so"""
      return
  
      #dynxul.prt("[")
      #self.docLock.release()
      #try:
      #  time.sleep(.1) # Yield to let other threads run
      #finally:
      #  self.docLock.acquire()
      #dynxul.prt("]")

    def threadit(self,inp):
        spl = inp.find(" ")

        name = inp[1:spl]
        code = inp[spl+1:].strip()
        if not name:
          lim = min([name.find(c) for c in [" ","(","[","*"]])
          if lim!=-1:
            name = sp[2][0:lim] 
          else:
            name = "thrd"

        thr = threadStart(name,lambda s,x: s.returned.append(s.evalit(x)),self,code)

        return thr

    def evalHandle(self,hdl):
      #print "evalhandle %s" % hdl
      (fn,args) = handle.handleGet(hdl)
      return fn(*args)

    def evalPythonString(self, code):
        if code == "**init**": return self.initFinish()
        elif code == "**periodic**": return self.periodic()
        elif code[0:3] == "**h": return self.evalHandle(code[2:])
        elif code[0] == "!": return self.threadit(code)
        else: return self.evalit(code)

    def evalit(self,code):
        # Ensure the code ends with an empty newline
        code += '\n\n'
        try:
            try:
                result = self._eval_code_and_return_result(code)
                try:
                    # See if the result can be turned into an xpcom object
                    return WrapObject(result, components.interfaces.nsIVariant)
                except ValueError:
                    # else, we'll just return a string representation
                    return repr(result)
            except SyntaxError:
                return self._exec_code_and_get_output(code)
        except Exception, e:
            # Format the exception, removing the exec/eval sections.
            logExc()
            exc_tb = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
            return "".join(exc_tb[:1] + exc_tb[3:])

    def getCompletionsForName(self, objname, prefix):
        #print "getCompletionsForName:: obname: %r, prefix: %r" % (objname, prefix, )
        # Global scope.
        if not objname:
            cplns = self.pyshellGlobals.keys()
        # Hack for nice xpcom completions.
        elif objname.lower() == "components.interfaces":
            cplns = components.interfaces.keys()
        elif objname.lower() == "components.classes":
            cplns = components.classes.keys()
        # Object scope.
        else:
            foundObject = None
            names = objname.split(".")
            foundObject = self.pyshellGlobals[names[0]]
            for name in names[1:]:
                foundObject = getattr(foundObject, name)
            # Got the object, now return the matches
            cplns = dir(foundObject)

        if prefix:
            cplns = [x for x in cplns if x.startswith(prefix)]
        return cplns

