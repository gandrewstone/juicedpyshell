"""?? Helper routines to manipulate the DOM (Document Object Model).
<html>
This file contains helper functions used to manipulate the DOM.  These function may be called within any context.  If not in the browser's thread, the call will be pushed onto a work queue and this thread will be blocked.
<br/>
Periodically the browser thread will execute items on the work queue, and unblock the thread when complete.  All of these functions begin with d_, however if the NODS variable is set to true (and it is by default) in this file, then every d_ function will have an equivalent without that prefix.  The purpose of this is to avoid conflicts with the functions defined in domhelper.
<br/>
Note that any function can be deferred into the browser thread using the "browserContext" object.  So a lot of these routines are simply for convenience and code beautification.  For example:

<pre>
import deferreddomhelper as ddh
(app,tab,doc) = ddh.refresh() 

# These 2 lines get the same element in two different ways
aNode       = ddh.browserContext.call(lambda d: d.getElementById("anIdentifier",doc)
theSameNode = ddh.getElementById("anIdentifier")

</pre>
</html>

<license name='MPL 1.1, GPL 2.0, or LGPL 2.1'>

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

from xpcom import components
import xpcom

import domhelper as dh
from threadhelper import *

#?? This variable controls whether this module defines symbols without the "d_" for example "deepChildList"
NODS = True

def d_refresh():
  """?? Grab the object describing in the active window, the active tab, and the active document
  <return>A tuple (win,tab,doc)</return>
  """  
  return browserContext.call(dh.refresh)

# getTagSurroundingText("A","Ozymandias",dialog)
def d_getTagSurroundingText(tag,text,node=None):
  """?? Search for some text and return the closest parent (surrounding) node that matches a specified tag.
  For example, this routine can be used to discover the hyperlink connected to some text in the following way:
  <code>
  getTagSurroundingText("A","click me")
  </code>
  <arg name="tag">What xml tag to look for</arg>
  <arg name="text">What to look for</arg>
  <arg name="node">Search this node and all children recursively</arg>
  """
  #log("getSurroundingText(%s,%s,%s)" % (tag,text,node.nodeName if node else "None"))
  if not node: (win,tab,node) = d_refresh()
  tnode = d_findDeepChildWith(node,"*value*",text)
  if not tnode: return None
  p = d_findParentWith(tnode,"*tag*",tag)
  return p

def d_getElementById(n,idd):
  """?? Deferred version of the DOM getElementById function call"""
#  return browserContext.call(lambda x,y:x.getElementById(y),n,idd)
  return browserContext.call(lambda x,y:x.getElementById(y),n,idd)

def d_deepChildList(node):
  """?? Returns a list of all children and children's children recursively"""
#  return browserContext.call(lambda x: deepChildList(x),node)
  return browserContext.call(lambda x: dh.deepChildList(x),node)

def d_getTitle(doc):
  """?? Returns the contents of the title of the document"""
  return browserContext.call(lambda d: dh.getTitle(d),doc)

def d_getH1(doc):
  """?? Returns the contents of the first h1 header in the document"""
  return browserContext.call(lambda d: dh.getH1(d),doc)


def d_click(doc,id,wait4Load=True):
  """?? Simulates a mouse click on a node and optionally waits for it to take effect.
  This function simulates a mouse click by issuing the following events: mouseover, mousedown, mouseup,click, mouseout.
  It then optionally waits for a new page to be loaded in the browser.
  If certain errors occur during loading "Page Load Error", and "Concurrency conflict", then click will be retried
  <arg name='doc'>The enclosing document</arg>
  <arg name='id' type="nsIDOM3Node or StringType">The DOM node to "click".  Note if you "click" a DOM node that is not a href and does not have a click handler, Mozilla will propagate the click upwards to the parent that DOES have a click handler</arg>
  <arg name='wait4Load'>If True (the default) this routine will not return until the click has loaded another document.  If False, the routine will return right away</arg>
  <return>(win,tab,doc) of the new page if wait4Load is True, otherwise (None,None,None)</return>
  """
  pg = dh.pageEvent.pageLoadCnt + 1
  d = browserContext
  d.call(lambda doc,id: [mouse(doc,id,"mouseover"),mouse(doc,id,"mousedown")],doc,id)
  time.sleep(.125)
  d.call(lambda doc,id: [mouse(doc,id,"mouseup"), mouse(doc,id,"click"), mouse(doc,id,"mouseout")],doc,id)
  (win,tab,doc) = (None,None,None)

  if wait4Load:
    if browserContext.inThread():
      raise Exception("Deferred click cannot wait for load WITHIN the main thread!")  
    dh.pageEvent.waitForLoad(pg)
    (win,tab,doc) = refresh()
    title = getTitle(doc)
    if str(title) == "Page Load Error":
      b = d_getElementById(doc,"errorTryAgain")
      if b:
        return d_click(doc,b,True)
    h1 = getH1(doc)
    if str(h1) == "Concurrency Conflict":
      time.sleep(7.5)
      
  return (win,tab,doc)

def d_mouse(doc,ident,event="click"):
  """?? Simulate a mouse event.  Note to simulate the exact mouse behavior when the user 'clicks', it is best to use <ref>deferreddomhelper.click</ref>.
  <arg name="doc">The DOM Document</arg>
  <arg name="ident">The DOM Node to simulate the event in, OR a string containing a node ID</arg>
  <arg name="event">What event to simulate. By default a "click" event is Simulated</arg>
  """  
  return browserContext.call(lambda a,b,c: dh.mouse(a,b,c),doc,ident,event)

def d_findParentWith(node,attr,s):
  """?? Recursively traverse the parent links, looking for one with a particular attribute,tag, or value.
  <arg name="node">The DOM node. This node will NOT be tested</arg>
  <arg name="attr">The attribute to look for, or "*tag*" to test the tag, or "*value*" to test the node's value</arg>
  <arg name="s" type="StringType">The value to look for, or a list of values</arg>  
  <return>None or a DOM node</return>
  """
  return browserContext.call(lambda x,y,z: dh.findParentWith(x,y,z),node,attr,s)

def d_findDeepChildWith(node,attr,s):
  """?? Recursively look for any child node with an tag,value, or attribute that matches any item in the passed list.
  <arg name='node'>The root of dthe tree. This node itself is NOT tested</arg>
  <arg name='attr'>Either an attribute string or the special strings: "*tag*" to mean the node's tag (or .nodeName in the DOM), "*value*" to mean text inside the node (i.e. .nodeValue in the DOM)</arg>
  <arg name='lst'>A string or list of strings to compare against.  If any one of these strings matches, the node will be returned</arg>
    <return>A DOM node, or None</return>
  """  
  return browserContext.call(lambda x,y,z: dh.findDeepChildWith(x,y,z),node,attr,s)

def d_findDeepChildrenWith(node,attr,lst):
  """?? Recursively look for all child nodes with a tag,value, or attribute that matches any item in the passed list.
  <arg name='node'>The root of the tree. This node itself is NOT tested</arg>
  <arg name='attr'>Either an attribute string or the special strings: "*tag*" to mean the node's tag (or .nodeName in the DOM), "*value*" to mean text inside the node (i.e. .nodeValue in the DOM)</arg>
  <arg name='lst'>A string or list of strings to compare against.  If any one of these strings matches, the node will be added to the list of returned nodes</arg>
  <return>A list of all matching nodes</return>
  """
  return browserContext.call(lambda x,y,z: dh.findDeepChildrenWith(x,y,z),node,attr,lst)

# Add the other symbols if desired
if NODS:
    findDeepChildWith = d_findDeepChildWith
    findDeepChildrenWith = d_findDeepChildrenWith
    findParentWith = d_findParentWith
    mouse = d_mouse
    click = d_click
    deepChildList = d_deepChildList
    getElementById = d_getElementById
    findDeepChildWith = d_findDeepChildWith
    refresh = d_refresh
    getTagSurroundingText = d_getTagSurroundingText
    click = d_click
    getTitle = d_getTitle
    getH1 = d_getH1
    
