"""?? This module implements functions to dynamically change the pyShell XUL user interface definition.
Unless otherwise stated these functions must be run in the browser thread.

<license>
Version: MPL 1.1/GPL 2.0/LGPL 2.1

The contents of this file are subject to the Mozilla Public License
Version 1.1 (the "License"); you may not use this file except in
compliance with the License. You may obtain a copy of the License at
http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS IS"
basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
License for the specific language governing rights and limitations
under the License.

The Original Code is PyShell code.

The Initial Developer of the Original Code is Andrew Stone
Portions created by the Initial Developer are Copyright (C) 2010.
All Rights Reserved.

Contributor(s):
  Andrew Stone

Alternatively, the contents of this file may be used under the terms of
either the GNU General Public License Version 2 or later (the "GPL"), or
the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
in which case the provisions of the GPL or the LGPL are applicable instead
of those above. If you wish to allow use of your version of this file only
under the terms of either the GPL or the LGPL, and not to allow others to
use your version of this file under the terms of the MPL, indicate your
decision by deleting the provisions above and replace them with the notice
and other provisions required by the GPL or the LGPL. If you do not delete
the provisions above, a recipient may use your version of this file under
the terms of any one of the MPL, the GPL or the LGPL.
</license>
"""

from types import *

from xpcom import components, ServerException, nsError
from xpcom.server import WrapObject

import domhelper as dh
import deferreddomhelper as ddh
from handle import *

import threadhelper

theWin         = None       #? The DOM window
theXulDoc      = None       #? The DOM XUL Document (i.e. user interface description)
theXul         = None       #? The DOM XUL

theCtntDoc     = None       #? The PyShell Content Document
theCtnt        = None       #? The PyShell content DOM
theShellOutput = None       #? The pyShell output

class FakeLock:
    def acquire(self):
        pass
    def release(self):
        pass

docLock = FakeLock()

#? <section name='private'>

def init(document_lock=None):
    """This function is called as the XUL window is coming up"""
    global theWin,theXulDoc,theXul,docLock

    if document_lock:
      docLock = document_lock
    else: docLock = FakeLock()

    docLock.acquire()
    try:
      theWin,theXulDoc,theXul=getPyShellXul()
      initCtnt()
      threadPaneInit()
    finally:
      docLock.release()

def initCtnt():
    """This function has to be called after the window is up.  It is called by init and hooks into the PyShell contents"""
    global theCtnt, theCtntDoc
    global theShellOutput

    docLock.acquire()
    try:
      if theWin.content: # The window isn't up yet... this init happenned too soon!
        theCtntDoc = theWin.content.document
        theCtnt    = theCtntDoc.childNodes.item(1)
        theShellOutput = theCtntDoc.getElementById("output")
    finally:
      docLock.release()   

def getWinLst(kind=""):
  ret = []
  w = components.classes["@mozilla.org/appshell/window-mediator;1"].getService(components.interfaces.nsIWindowMediator)
  e = w.getEnumerator(kind)
  while(e.hasMoreElements()):
    wi = e.getNext()
    if not wi: break
    ret.append(wi)
  return ret

def getWin(kind="navigator:browser"):
  w = components.classes["@mozilla.org/appshell/window-mediator;1"].getService(components.interfaces.nsIWindowMediator)
  return w.getMostRecentWindow(kind)


def getPyShellXul():
    wis = getWinLst()
    for w in wis:
        gsh = w.document.getElementById("python_shell_window")
        if gsh:
            return (w,w.document,gsh)
#? </section>

def hprt(s):
  """?? Print HTML"""
  #docLock.acquire()
  try:
    if type(s) in StringTypes:
      n = theCtntDoc.createElement("div")
      n.innerHTML = s
    else:
      n = dh.bld(s,theCtntDoc)
      
    theShellOutput.appendChild(n)
  finally:
    #docLock.release()
    pass

def log(s,severity="info"):
  hprt("<div class='log %s'>%s</div>" % (severity,s))

if not dh.log:
  dh.log = log


# dynxul.addMenu(("menu",{"label":"m1"},[("menupopup",None,[("menuitem", {"label":"test","onclick":"alert('hi');"},None)])]))
# dynxul.addMenu(("menu",{"label":"m2"},[("menupopup",None,[("menuitem", {"label":"test1","id":"test1"},None)])]))
def addMenu(menuspec,xul=None):
    """?? Creates a new menu.  Your menu will be appended to the XUL node named "themenubar"
    <arg name='menuspec'>The specification of the menu in <ref>domhelper.bld</ref> format i.e. (tag,{attr:values},[children])</arg>
    <arg name='xul'>The XUL document to add the menu to.</arg>
    """
    if not xul: xul=theXulDoc
    mb = xul.getElementById("themenubar")
    mb.appendChild(dh.bld(menuspec,theXulDoc))

def addSidebarTab(label,contents=None):
    """?? Creates a new tab in the sidebar.
    <arg name='label'>The name of the tab (and also the ID of the XUL DOM node)</arg>
    <arg name='contents'>A list of the menu contents in <ref>domhelper.bld</ref> format i.e. (tag,{attr:values},[children])</arg>
    """
    sp = theXulDoc.getElementById("sidepanel")
    sp.childNodes.item(0).appendChild(dh.bld(("tab",{"label":label, "id":label},None),theXulDoc))
    sp.childNodes.item(1).appendChild(dh.bld(("tabpanel",{"flex":"1", "id":"panel_" + label},contents)))
    return "panel_" + label



def hookStrto(pythonStr,node,event="onclick"):
    """?? Attaches a string to a node and event.
    This function creates sets the event attribute (by default "onclick") of a DOM node to execute the passed Python string.
    It is implemented by setting the event attribute to a chunk of Javascript code that calls into pyShell with the string.

    <arg name="pythonStr">A python of python code that will be executed</arg>
    <arg name="node">The DOM node to hook this function into</arg>
    <arg name="event">What DOM event do you want to call this function for? Default: onclick</arg>
    """
    node.setAttribute(event,'_pyEvalSvc.evalPythonString("%s")' % str(pythonStr))

tst = """
worked = False
node = dynxul.theXulDoc.getElementById("test1")
def cb():
    global log
    global worked
    log("button pressed")
    worked=True
dynxul.hookto(cb,tuple(),node)
"""

def hookto(fn, args, node,event="onclick"):
    """?? Attaches a python function closure to a node and event.
    This function creates sets the event attribute (by default "onclick") of a DOM node to execute the passed Python function with the passed args.
    It is implemented by mapping a newly created handle to the function and arguments, and setting the event attribute to a chunk of Javascript code that
    calls into pyShell with the handle.  Inside the pyShell thread, the handle is accessed and so the function you passed is called.
    This means that your function will be called within the browser's context, so "deferred" calls are not necessary.

    <arg name="fn">A python function (or lambda) event handler</arg>
    <arg name="args">A tuple containing the arguments to your function</arg>
    <arg name="node">The DOM node to hook this function into</arg>
    <arg name="event">What DOM event do you want to call this function for? Default: onclick</arg>

    <return>The registered handle.  You need to delete this handle when it no longer becomes useful.</return>
    
    """
  
    hdl = handleCreate((fn,args));
    node.setAttribute(event,'_pyEvalSvc.evalPythonString("**%s")' % hdl)
    return hdl


#? <section name='private'>
def getCheckedThreads():
  ret = []
  pane = theXulDoc.getElementById("threadlist")
  i = -1
  while 1:
    i+=1
    trd = pane.childNodes.item(i)
    if not trd: break

    chk = trd.childNodes.item(0)
    if chk:
      if chk.getAttribute("checked") == 'true':
        ret.append(trd.getAttribute("threadname"))
#        ret.append(trd.getAttribute("id"))
  return ret  

def pauseCheckedThreads(this):
    """This function is called when you click the Pause button in the GUI
    """
    ct = getCheckedThreads()
    for t in ct:
      threadhelper.threadPause(t,not threadhelper.threadDb[t].pause)
  
def killCheckedThreads(this):
    """This function is called when you click the Kill button in the GUI
    """
    ct = getCheckedThreads()
    for t in ct:
      threadhelper.threadAbort(t)

def threadPaneInit(doc=None):
  if not doc: doc = theXulDoc
  panel = doc.getElementById("threadpane")
  if panel:
    dh.removeChildren(panel)
    panel.appendChild(dh.bld(("vbox",{"flex":1},[("vbox",{"flex":1,"id":"threadlist"},None),("hbox",{"flex":1},[("button", {"label":"un/pause","onclick":pauseCheckedThreads},None),("button",{"label":"kill","onclick":killCheckedThreads},None)])]),theXulDoc))      
#? </section>    


def threadPaneAdd(name,obj):
    """?? Adds a information (a thread) to the thread pane.  Should be called when a thread is created.
    """
    pane = theXulDoc.getElementById("threadlist")
    pane.appendChild(dh.bld(("hbox",{"flex":1,"id":"thread_" + name,"threadname":name,"ref":handleCreate(obj)},[("checkbox",{"label":name},None),("label",{"value":"running","id":"threadStatus_"+name},None)]),theXulDoc))

def threadPaneRemove(name,delHandle=True):
    """?? Removes information (i.e. a thread) from the thread pane.  Should be called when a thread is deleted.
    """
    tp = theXulDoc.getElementById("thread_" + name)
    if tp:
      hdl = tp.getAttribute("ref")
      tp.parentNode.removeChild(tp)
      if delHandle:
        handleDelete(hdl)
        hdl = None
      return hdl
    return None

def threadPaneStatus(threadName,status):
    """?? Changes a thread's status display.  Can be called from any context.
    <arg name='threadName'>The thread's name</arg>
    <arg name='status'>The string you want displayed</arg>
    """
    if threadName is None:
        threadName = threadhelper.threadName()
    pane = ddh.getElementById(theXulDoc,"threadStatus_" + threadName)
    ddh.browserContext.call(lambda x,y:x.setAttribute("value",str(y)),pane,status)
