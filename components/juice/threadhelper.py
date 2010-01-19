"""?? Thread and Thread Pane Routines

This module contains some useful thread routines and connections to the thread pane in the pyShell's left-hand thread tab

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

The Original Code is JuicedPyShell code.

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

import time
import threading
import thread
import sys
import types
import traceback

import dynxul

class ThreadAborted(Exception):
  """?? This exception is raised when a thread is marked as aborted in the thread's context"""
  pass

#? <section name="private">
class container:
  pass

class ThreadTracker:
  """?? One of these is created for each thread and put into the <ref>threadDb</ref> global variable"""
  def __init__(self,idd,name):
    self.id = idd
    self.name = name
    self.abort = False
    self.pause = False
    self.log  = []
#?</section>

class Defer:
  """?? This class lets you execute functions with another thread context.
  It also detects and handles thread pause and abort requests.  Usually, it is only useful through the <ref>browserContext</ref> object also defined in this module
  """
  
  deferredLst = []
  lock = threading.Lock()
  cond = threading.Condition(lock)
  def __init__(self):
    """?? Constructor"""
    self.runThrdIdent = thread.get_ident()
    self.runThread = threading.currentThread()
    pass


  def runDeferred(self,glbl=None,lcl=None):
    """?? Run all the deferred function calls.  This function should be called periodically by the thread who will be running the deferred calls"""
    self.lock.acquire()
    try:
      for c in self.deferredLst:
        cmd = c.cmd
        c.result = exc(c.cmd,c.args,glbl,lcl)
      self.deferredLst = []
      self.cond.notifyAll()
    finally:
      self.lock.release()


  def inThread(self):
    """?? Returns true if I am already in the correct context."""
    tid = thread.get_ident()
    if self.runThrdIdent == tid:  # I am already in the right context
      return True
    return False


  def async(self,fn,*args):
    """?? Run a deferred call asynchronously; i.e. just return -- don't wait for it to run"""
    self.lock.acquire()
    try:
      c = container()
      c.cmd = fn
      c.args = args
      self.deferredLst.append(c)
    finally:
      self.lock.release()

    return True
  
  def call(self,fn,*args):
    """?? Run a function in another context, wait for it to return and return its return value"""
    tid = thread.get_ident()
    if self.runThrdIdent == tid:  # I am already in the right context
      #print "in the context!"  
      return exc(fn,args)
    else:
      try:
        tdb = threadDb[tid]
        if tdb.pause:
          self.async(dynxul.threadPaneStatus,tdb.name,"paused")
          while tdb.pause:
            #print "thread %d paused" % tid
            time.sleep(1)
          self.async(dynxul.threadPaneStatus,tdb.name,"resumed")
          
        if tdb.abort:
          self.async(dynxul.threadPaneStatus,tdb.name,"aborted")
          raise ThreadAborted("Abort flag set")
      except KeyError:
        print "Thread %d not found" % tid
        pass
      
    self.lock.acquire()
    try:
      c = container()
      c.cmd = fn
      c.args = args
      self.deferredLst.append(c)
      self.cond.wait()
    finally:
     self.lock.release()

    #print "deferred call returned"
    return c.result


def threadStart(name,fn,*args):
  """?? Start a new thread
  <arg name='name'>A string identifier of the thread to start</arg>
  <arg name='fn'>What function to run</arg>
  <arg name='args'>A variable # of subsequent arguments that shall become arguments to the passed function</arg>
  """
  global threadDb
  dynxul.threadPaneAdd(name,None) 
  thr = thread.start_new_thread(threadWrapper, (name, fn) + args)
  tt = ThreadTracker(thr,name)
  threadDb[thr] = tt  # Allow lookups by thread id and name
  threadDb[name] = tt
  dynxul.hprt("<h3 style='color:green'>thread: %s is %d</h3>" % (name,thr))
  return thr

def threadStacks():
  """?? Print the current stack trace of every thread"""
  cf = sys._current_frames()
  for (id,frame) in cf.items():
     s = traceback.format_stack(frame)
     print "Thread %d" % id
     print s
     try:
       dynxul.hprt("<pre>" + s + "</pre>")
     except Exception, e:
       pass

def threadName():
  """?? return this thread's name"""
  global threadDb
  tid = thread.get_ident()
  if threadDb.has_key(tid):
    return threadDb[tid].name
  return "" # The "main" thread
  

def threadAbort(nameOrId):
  """?? Abort a thread.  This routine merely sets a global variable indicating that the thread should be aborted.  Certain functions (namely any deferred call) will check this flag and raise the ThreadAborted exception if it is True.
  <arg name='nameOrId'>A string name or numerical identifier that indicates which thread to operate on.</arg> 
  """
  global threadDb
  if threadDb.has_key(nameOrId):
    threadDb[nameOrId].abort = True

def threadPause(nameOrId,state=True):
  """?? Pause a thread.  This routine merely sets a global variable indicating that the thread should be paused.  Certain functions (namely any deferred call) will check this flag and go into a wait loop if it is True
  <arg name='nameOrId'>A string name or numerical identifier that indicates which thread to operate on.</arg> 
  <arg name='state'>By default True meaning pause the thread, or pass False which means to resume it</arg>
  """  
  global threadDb
  if threadDb.has_key(nameOrId):
    threadDb[nameOrId].pause = state

def logExc(prefix=""):
  """?? Log an exception in pretty HTML"""    
  et,ev,eb = sys.exc_info()
  s = "<div class='pyException'>%s%s</div>" % (prefix,"".join(traceback.format_exception(et,ev,eb)))
  dynxul.hprt(s)

#? <section name="private">

def exc(cmd,args,glbl=None,lcl=None):
    """?? eval or exec depending on what is needed to get the job done!
    """
    result = None
    try:
      if type(cmd) in types.StringTypes:
        try:
          result = eval(cmd,glbl,lcl)
        except SyntaxError:
          exec cmd in glbl,lcl
          result = None
      if type(cmd) is types.FunctionType:
        result = cmd(*args)
    except Exception,e:
       logExc("Exception running: %s\n" % str(cmd))
    return result

def threadWrapper(name,fn,*args):
  """?? Thread startup function.  Not to be called directly."""
  global browserContext
  global threadDb
  try:
    ret = fn(*args)
    #print "done!"
    browserContext.async(dynxul.threadPaneStatus,name,"completed")
    return ret
  except Exception, e:
    #print str(e)
    exc_tb = traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)
    logExc(exc_tb)
    browserContext.call(dynxul.threadPaneStatus,name,"exception")
    #myPrinter(str(exc_tb))
    #print exc_tb
  finally:
    #print "sleep"
    time.sleep(5)
    #print "sldone"
    browserContext.async(dynxul.threadPaneRemove,name)
    del threadDb[name]

#? </section>


threadDb = {}               #?? Global thread database
browserContext = Defer()    #?? A singleton class that lets you execute functions in the web browser context

