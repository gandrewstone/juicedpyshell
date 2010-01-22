"""?? Helper routines to manipulate the DOM (Document Object Model).

This file contains helper functions used to manipulate the DOM.
These function must be called within the browser's threaad, NOT within any thread spawn by you.  Therefore you may want to use the functions in
<ref>deferreddomhelper</ref> instead since these will work in any context.

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
import threading

from xpcom import components
import xpcom


from types import *
from handle import *

log = None

class DocLoadException(Exception):
    """?? This exception is raised when the document is unable to be loaded in all threads that are waiting for the load to finish
    """
    pass

class PageEvent:
  """?? The PageEvent class registers for page events and reports them.  In particular, it is able to notify threads when a document is finished loading and whether the load failed.
  """    
  _com_interfaces_ = components.interfaces.nsIObserver
  def __init__(self):
    """?? Constructor"""
    self.lock = threading.Lock()
    self.cond = threading.Condition(self.lock)
    self.wrapped = xpcom.server.WrapObject(self,components.interfaces.nsIObserver)
    self.obSvc =  components.classes["@mozilla.org/observer-service;1"].getService(components.interfaces.nsIObserverService)
    self.obSvc.addObserver(self.wrapped,"EndDocumentLoad",True)
    self.obSvc.addObserver(self.wrapped,"FailDocumentLoad",True)
    self.pageLoadCnt = 0
    
#? <section name='internal'>    
  def observe(self,subject,topic,data):
    """?? The callback that is called whenever a document event comes in.  You should not call this directly."""
    if topic == "EndDocumentLoad":
      self.lock.acquire()
      try:
        self.event = "EndDocumentLoad"
        self.pageLoadCnt+=1
        self.cond.notifyAll()
      finally:
        self.lock.release()
    elif topic == "FailDocumentLoad":
      self.lock.acquire()
      try:
        print "DOCUMENT LOAD FAILED!"
        print str(subject),str(topic),str(data)
        self.event = "FailDocumentLoad"
        #self.pageLoadCnt+=1
        self.cond.notifyAll()
      finally:
        self.lock.release()
      
    else:
      print str(subject),str(topic),str(data)
#? </section>        


  def inject(self,event="EndDocumentLoad"):
    """?? This function lets you inject fake events into this class for debugging purposes.
    <arg name='event'>The name of the event as specified in the Mozilla documentation (components.interfaces.nsIObserver)</arg>
    """
    self.observe(None,event,None)

  def waitForLoad(self,maxWaitTime=15,loadnum=None):
    """?? Block this thread until the document is loaded.
    <html>
    The typical use of this function would be something like:
    <pre>
    deferreddomhandler.click(obj)
    pageEvent.waitForLoad()
    </pre>

    This is technically incorrect because what if the document load completed before the waitForLoad function was even called?  In practice, this never happens (famous last words!).  Additionally, as every heavy web user knows, every once in a while the http connect gets lost and it is necessary to retry.  But the above code does not handle that case.
    <br/>
    The correct way to implement this is as follows.

    <pre>
    loadnum = pageEvent.pageLoadCnt+1
    waittime = 20
    deferreddomhandler.click(obj)
    try:
      pageEvent.waitForLoad(waittime,loadnum)
    except DocLoadException, e:
      # Do something
      pass
    </pre>
    </html>
    It is perhaps better to use the <ref>doAndWait</ref> function which handles all of this for you.
    <arg name='maxWaitTime'>Wait a maximum of this number of seconds for an event to come in</arg>
    <arg name='loadnum'>Every time the document is loaded a counter is incremented. Your thread is not unblocked unless that counter is >= this value.  If None is passed, the load number will be 1+the current value.</arg>
    """
    self.lock.acquire()
    try:
      if loadnum is None: loadnum = self.pageLoadCnt+1
      while (loadnum > self.pageLoadCnt):
        #print "waiting..."
        self.cond.wait(maxWaitTime)
        if self.event == "FailDocumentLoad":
          raise DocLoadException()
    finally:   
      self.lock.release()

  def doAndWait(self,op,maxWaitTime=15,numRetries=3):
    """?? Execute a function and then block this thread until the document is correctly loaded.
    Typically "op" would be a call to something like <ref>deferreddomhelper.click()</ref>.
    This function will execute that call and then wait for the document to finish loading.
    On document load error, it will attempt to handle the problem by refreshing the page or even going "back" and calling "op" again.
    <arg name='op'>A lambda function to call that will cause the page to update</arg>
    <arg name='maxWaitTime'>How long to wait for the page to refresh before retrying</arg>
    <arg name='numRetries'>This many attempts will be undertaken to successfully load the page before giving up</arg>
    <exception type='DocLoadException'>If the page cannot be loaded an exception will be raised</exception>
    """
    for retry in range(0,numRetries):
      self.lock.acquire()
      loadnum = self.pageLoadCnt+1
      try:
        op()
        while (loadnum > self.pageLoadCnt):
          self.event = None
          self.cond.wait(maxWaitTime)
          if self.event is None:  # Timeout!
            continue
          if self.event == "FailDocumentLoad":
            if retry==numRetries-1:
                raise DocLoadException()
            continue
        return
      finally:   
        self.lock.release()


#?? The Mozilla components.interfaces.fuelIApplication object
fuelApp = components.classes["@mozilla.org/fuel/application;1"].getService(components.interfaces.fuelIApplication)
#fuel = fuelApp.queryInterface(components.interfaces.fuelIApplication)

#?? The pageEvent Singleton object.  This object is what you use to wait for events, most importantly document reload and the associated reload failure modes.
pageEvent = PageEvent()

def load(uriStr,tab=None):
    """?? Loads a URI up in the browser
    <arg name='uriStr' type='StringType'>A uri, i.e. 'http:://www.google.com/'</arg>
    <arg name='tab' type='fuelIBrowserTab'>The tab to load the page into (or None) to mean the current tab</arg>
    """
    uriFactory = components.classes["@mozilla.org/network/io-service;1"].getService(components.interfaces.nsIIOService)
    uri = uriFactory.newURI(uriStr,"utf-8",None)
    if not tab: (win,tab,doc) = refresh()
    tab.load(uri)
    return uri


def childList(node):
  """?? Returns a list of all children of the passed DOM node.
  <arg name='node' type='nsIDOMNode'>a DOM node</arg>
  """
  stl=[]
  for n in childiter(node): stl.append(n)
  return stl

def childiter(node):
  """?? Generator that iterates through all children of a DOM node
  <arg name='node' type='nsIDOMNode'>a DOM node</arg>
  """  
  lst = node.childNodes
  cnt = 0
  while cnt<lst.length:
    yield lst.item(cnt)
    cnt+=1

def domiter(lst):
  """?? Generator that lets you write for loops for DOM containers
  <arg name='lst' type='nsIDOMNodeList'>a DOM list container (actually any container will work that has .length and .item() members).</arg>
  """
  cnt = 0
  while cnt<lst.length:
    yield lst.item(cnt)
    cnt+=1

def deepiter(lst):
  """?? Generator that iterates through all children and children's children recursively
  <arg name='lst' type='nsIDOMNodeList'>a DOM list container (actually any container will work that has .length and .item() members).</arg>
  """
  cnt = 0
  while cnt<lst.length:
    yield lst.item(cnt)
    try:
      for n in deepiter(lst.item(cnt).childNodes):
        yield n
    except:
      pass
    cnt+=1

def deepChildList(node):
  """?? Returns a list of all children and children's children recursively
  <arg name='node' type='nsIDOMNode'>a DOM node</arg>
  """
  ret = []
  for n in deepiter(node.childNodes):
    ret.append(n)
  return ret

# lambda d: d.getElementsByTagName("h1").item(0).childNodes.item(0).nodeValue
def getH1(doc):
  """?? Returns the contents of the first h1 header in the document
  <arg name='doc' type='nsIDOMDocument'>a DOM document, obtainable through the <ref>domhelper.refresh()</ref> function</arg>
  <return type='string'>The contents of the h1 header</return>
  """
  tag = doc.getElementsByTagName("h1").item(0)
  if tag:
      tag = tag.childNodes.item(0)
      if tag:
          tag = tag.nodeValue
  return tag

# d.getElementsByTagName("title").item(0).childNodes.item(0).nodeValue,doc)
def getTitle(doc):
  """?? Returns the contents of the title of the document
  <arg name='doc' type='nsIDOMDocument'>a DOM document, obtainable through the <ref>domhelper.refresh()</ref> function</arg>
  <return type='string'>The contents of the title</return>
  """
  tag = doc.getElementsByTagName("title").item(0)
  if tag:
      tag = tag.childNodes.item(0)
      if tag:
          tag = tag.nodeValue
  return tag


def removeChildren(node):
    """?? Remove all children from the passed node
    <arg name='node' type='nsIDOMNode'>a DOM node</arg>
    """
    while node.hasChildNodes():
        node.removeChild(node.childNodes.item(0))


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
    node.setAttribute(event + "hdl", str(hdl))
    return hdl


def bld(it,doc):
    """?? This function takes a structure and turns it into DOM elements.
    <arg name='it' type='tuple (see description)'>Turn this into DOM elements</arg>
    <arg name='doc' type='nsIDOMDocument'>Pass the document that the elements will be put into</arg>
    <html>
    The structure is recursive of the format: (tag,{attributes},[children]).
    For example: bld(("test",{"foo":"bar"},[("c",None,None)])) would create the following xml ([] used instead of lt,gt so this example is not interpreted as XML):
    [test foo="bar"]
      [c /]
    [/test]
    </html>
    It is also possible to pass a python function as the value of an attribute (for use with "onclick" et al).  In this case, the system automatically allocates a handle for this operation, sets the value to the correct javascript to call python with this handle, so the function will be executed see <ref>hookto</ref>  The function should take one argument "this" which will be the DOM node that the attribute is attached to.
    
    <return type='nsIDOMNode'>A DOM node and children hierarchy</return>
    """
      
    n = doc.createElement(str(it[0]))
    #print it
    if it[1]:
      for (k,v) in it[1].items():
        if type(v) is FunctionType:
          hookto(v, (n,), n,k)
        else:
          n.setAttribute(str(k),str(v))
    if it[2]:
      for child in it[2]:
          cn = bld(child,doc)
          n.appendChild(cn)
    return n



def pall(n):
  for n in deepiter(n.childNodes): p(n)
  
def p(node):
  try:
    ido = node.attributes
    if ido: ido = ido.getNamedItem("id")
    if ido: ids = str(ido.value)
    else: ids = ""
    log( "Name: %s Type: %s, value %s, id: %s" % (str(node.nodeName),str(node.nodeType),str(node.nodeValue),ids))
  except UnicodeEncodeError:
    log( "unicode error")

def mouse(doc,ident,event="click"):
  """?? Simulate a mouse event.  Note to simulate the exact mouse behavior when the user 'clicks', it is best to use <ref>deferreddomhelper.click</ref>.
  <arg name="doc">The DOM Document</arg>
  <arg name="ident">The DOM Node to simulate the event in, OR a string containing a node ID</arg>
  <arg name="event">What event to simulate. By default a "click" event is Simulated</arg>
  """
  if type(ident) is type(""): node = doc.getElementById(ident)
  else: node = ident
  me = doc.createEvent("MouseEvents")
  me.initMouseEvent(event,True,True,doc.defaultView,1,0,0,0,0,False,False,False,False,0,None)
  node.dispatchEvent(me)


def refresh():
  """?? Grab the object describing in the active window, the active tab, and the active document
  <return>A tuple (win,tab,doc)</return>
  """
  win = fuelApp.activeWindow
  tab = fuelApp.activeWindow.activeTab 
  doc = fuelApp.activeWindow.activeTab.document
  return(win,tab,doc)

def attr2dict(n):
  """?? Converts the attributes in a node to a dictionary of attribute/values.  This dictionary can be accessed outside of the browser thread
  <arg name='n' type='nsIDOMNode'>a DOM node</arg>
  """
  if not n.attributes:
    return {}
  i = 0
  a = n.attributes.item(i)
  ret = {}
  while a:
    if a.specified:
        ret[a.name] = a.value    
    i+=1
    a = n.attributes.item(i)
  return ret  

def dom2str(n,indent=0,indentIncr=2):
  """?? Converts a DOM node and children back into html
  <arg name="n" type='nsIDOMNode'>a DOM node</arg>
  <arg name="indent">The initial indentation depth</arg>
  <arg name="indentIncr">The indentation increment amount (by default 2 spaces)</arg>
  <return>A string</return>
  """
  if str(n.nodeName) == "#text":
      return n.nodeValue
  attr = attr2dict(n)
  attrslst = [] 
  for (k,v) in attr.items():
    if "'" in v:
      attrslst.append('%s="%s"' % (k,v))
    else:
      attrslst.append("%s='%s'" % (k,v))          
  pfx = "%s<%s %s>\n" % (" "*indent, n.nodeName, " ".join(attrslst))
  sfx = "%s</%s>\n" % (" "*indent, n.nodeName)
  chldslst = []
  for c in childiter(n):
    chldslst.append(dom2str(c,indent+indentIncr))
  return pfx + "".join(chldslst) + sfx
    

# findParentWith(t,"*tag*","A")
def findParentWith(node,attr,s):
  """?? Recursively traverse the parent links, looking for one with a particular attribute,tag, or value.
  <arg name="node" type='nsIDOMNode'>The DOM node. This node will NOT be tested</arg>
  <arg name="attr" type='string'>The attribute to look for, or "*tag*" to test the tag, or "*value*" to test the node's value</arg>
  <return>None or a DOM node</return>
  """
  try:
    x = node.parentNode
  except AttributeError, e:
    log("No parent with attr: %s -> %s found!" % (attr, s))
    return None
  try:
    if attr == "*tag*": 
        if s == x.nodeName:
          return x
    if attr == "*value*":
        #print x.nodeValue
        if s in x.nodeValue:
          return x
    if s in x.getAttribute(attr):
        return x
  except AttributeError,e:
    pass
  return findParentWith(x,attr,s)


def findDeepChildWith(node,attr,lst):
  """?? Recursively look for any child node with an tag,value, or attribute that matches any item in the passed list.
  <arg name='node' type='nsIDOMNode'>The root of the tree. This node itself is NOT tested</arg>
  <arg name='attr' type='string'>Either an attribute string or the special strings: "*tag*" to mean the node's tag (or .nodeName in the DOM), "*value*" to mean text inside the node (i.e. .nodeValue in the DOM)</arg>
  <arg name='lst' type='list of strings'>A string or list of strings to compare against.  If any one of these strings matches, the node will be returned</arg>
    <return>A DOM node, or None</return>
  """
  #log("findDeepChildWith(%s,%s,%s)" % (node.nodeName,attr,lst))
  if not type(lst) is ListType:
    lst = [lst]
    
  for x in deepiter(node.childNodes):
    for s in lst:
      try:
      #p(x)
        if attr == "*tag*": 
          if s == x.nodeName:
            return x
        if attr == "*value*":
          #print x.nodeValue
          if s in x.nodeValue:
            return x
        if s in x.getAttribute(attr):
          return x
      except AttributeError,e:
        pass
      except TypeError,e:
        pass

def findDeepChildrenWith(node,attr,lst):
  """?? Recursively look for all child nodes with a tag,value, or attribute that matches any item in the passed list.
  <arg name='node' type='nsIDOMNode'>The root of the tree. This node itself is NOT tested</arg>
  <arg name='attr' type='string'>Either an attribute string or the special strings: "*tag*" to mean the node's tag (or .nodeName in the DOM), "*value*" to mean text inside the node (i.e. .nodeValue in the DOM)</arg>
  <arg name='lst' type='list of strings'>A string or list of strings to compare against.  If any one of these strings matches, the node will be added to the list of returned nodes</arg>
  <return>A list of all matching nodes</return>
  """    
  #log("findDeepChildWith(%s,%s,%s)" % (node.nodeName,attr,lst))
  if not type(lst) is ListType:
    lst = [lst]

  ret = []
  for x in deepiter(node.childNodes):
    for s in lst:
      try:
      #p(x)
        if attr == "*tag*": 
          if s == x.nodeName:
            ret.append(x)
        if attr == "*value*":
          #print x.nodeValue
          if s in x.nodeValue:
            ret.append(x)
        if s in x.getAttribute(attr):
          ret.append(x)
      except AttributeError,e:
        pass
      except TypeError,e:
        pass
  return ret
