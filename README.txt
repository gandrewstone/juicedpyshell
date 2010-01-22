<section name="home">
<html>
<h2>Introduction</h2>
Juiced PyShell is a Python shell that you can install into your Firefox browser.  You can run any Python program within this shell, but of course it makes the most sense to run programs that need to access and modify web pages!

<h2>Why do it this way?</h2>

<h3>Web 2.0</h3>
There are other technologies that allow Python to access web pages.  In fact, it is very easy to "get" web pages using Python's standard httplib and urllib libraries.  However, web pages are becoming significantly more sophisticated.  With the adoption of the asynchronous design patterns that the industry calls "web 2.0", urllib and httplib simply will not work.  To read Web 2.0 pages as the end user does, you need a full Javascript interpreter on the client.  So the client needs to be a very sophisticated piece of software, instead of just a protocol engine.  The simplest way to get this sophistication is to merge Python with one the already exists!

<h3>Local Markup</h3>
Additionally, you may not want a standalone program that crawls web pages.  Instead, you may be looking for computer-assisted browsing.  In other words, the Python program accesses a local or remote resource (a database for example) and combines information from that resource into your browsing experience.  A simple example would be to mark up every link with information about when it was last browsed (sort of integrating the "history" information with the current page).  A more complex example would be to highlight all differences between this and prior viewings of a page.  Or to eliminate pesky advertising.  And so on.

<h2>Features</h2>
Juiced PyShell gives you complete access to the Python language, standard libraries, and libraries that you install.  It lets you modify the browser's view of any web page, including itself.  All of this is actually provided via the <a href="http://pyxpcomext.mozdev.org/">pyXPCOMext</a>plugin and the <a href="http://pyxpcomext.mozdev.org/samples.html#pyshell">PyShell</a> sample upon which Juiced PyShell is based.  In fact those projects are the majority of the work and deserve all the credit!
<br/>
What Juiced PyShell gives you is a bit of user-friendliness on top of the pyXPCOMext engine. It:
<ul>
<li>Wraps common XPCOM functions such as getting a browser window, waiting for pages to load up, etc.</li>
<li>Provides simple but powerful DOM (document-object-model) access functions that allow your script to quickly zero in on the data you need</li>
<li>Provides a powerful DOM creation engine so you can easily modify web pages.</li>
<li>Hides browser threading, and display issues and gotchas</li>

<li>Does all of the above for the Juiced PyShell window itself, which allows your Python programs to easily add GUI widgets</li>
<li>And finally it provides an enhanced Python shell experience, including display of HTML within the shell output, and GUI display and control of running threads</li>
</ul>

</html>
</section>


<section name="Examples">
<section name="Driving The Browser">
<html>
This example demonstrates how to drive the web browser.  It goes to google, enters a search, and then follows a link to the searched page
<br/>
<pre class="code">
# Standard imports
import deferreddomhelper as ddh
#import domhelper as dh

#<br/>
# First we'll go over to google and search for something
(win,tab,doc) = ddh.refresh()                                                # Get the "active" browser page
ddh.load("http://www.google.com/",tab)                                       # Pop over to google search engine
(win,tab,doc)=ddh.refresh()                                                  # Get the search engine DOM

#<br/>
# Now I'll access the DOM with names discovered by looking at the html source.
# This code fill in a search term, clicks a button and submits the form.

qbox = ddh.findDeepChildWith(doc,"name","q")                                  # Get the search input box
qbox.value = "JuicedPyShell"                                                 # Add in my search term
button = ddh.findDeepChildWith(doc,"title","Google Search")                   # Get the button
ddh.click(doc,button,False)                                                  # "click" just the button

form = ddh.findParentWith(button,"*tag*","FORM")                              # Get the enclosing form
form.submit()                                                                # submit the form

#<br/>
# Now wait for the page to load
dh.pageEvent.waitForLoad()                                                   # Wait for the search page to load
(win,tab,doc)=ddh.refresh()                                                  # Get the new DOM

#<br/>
# Then we'll look for a particular search result and follow that
link = ddh.getTagSurroundingText("A","Project Hosting on Google Code",doc)   # Look for the "A" DOM node (i.e. link) that encloses some text
ddh.click(doc,link,False)                                                    # Click that text
</pre>
</html>
Note the use of the "ddh" module or "deferreddomhelper".  This module can be used in spawned threads.  The equivalently named functions in the "domhelper" module CAN ONLY be used in the Juiced PyShell main thread!  You CANNOT directly touch the DOM from spawned threads!  If your browser crashes, that's what happened!
[Note: the way deferreddomhelper works is to put your function on a job list, and the Juiced PyShell main thread periodically executes the jobs on this list]
</section>

<section name="Printing HTML">
<html>

<textarea cols="80" rows="12" style="font-family:monospace">
import dynxul

# Let's print a red header
dynxul.hprt("<h1 style='color:red'>RED HEADING</h1>")

# Now let's print an image
dynxul.hprt("<img src='http://juicedpyshell.googlecode.com/svn/trunk/doc/html/medlogo.png'/>")
</textarea>

<h3> Output </h3>
The output should look like this:

<div><h1 style='color:red'>RED HEADING</h1></div>
<div>None</div>

<div><img src='http://juicedpyshell.googlecode.com/svn/trunk/doc/html/medlogo.png'/></div>
<div>None</div>

</html>
</section>


<section name="Threading">
Cut and paste this into your Juiced PyShell window.
<html><pre>
# Threading Example
import time
import dynxul

def countdown(amt): 
  while amt > 0: 
    time.sleep(1)
    dynxul.threadPaneStatus(None,"Countdown %d" % amt)
    amt -= 1
</pre></html>

Now spawn off a thread running your code

<html><pre>
!run countdown(10)
</pre></html>

Note how the thread appears in the thread status tab in the left sidebar.  And note how the countdown function can modify its status.
</section>

<section name="Modifying the JuicedPyShell GUI">
This example shows how to modify the Juiced PyShell GUI itself.  It adds a new tab to the sidebar and specifies 2 buttons in that tab.  The buttons are hooked to Python functions when clicked.

Next it shows how to modify what Python function is called when the button is clicked.  This technique is useful for debugging!
<html>
<textarea cols="120" rows="20" style="font-family:monospace">
# Modifying the JuicedPyShell frame
import dynxul

# Define a button handler function.  There's nothing special except that it takes 1 argument, which will be the XUL DOM object of the clicked button
# Note that this function saves the handle it uses to a global variable.  The purpose of this is so we can modify that handle later (and therefore modify the button's behavior.
myHdl = None
def myfunc(this):
 global myHdl
 myHdl = this.getAttribute("onclickhdl")
 dynxul.hprt("The button you pressed is labelled '%s'.\nThe onclick handle is '%s'." % (this.getAttribute("label"),this.getAttribute("onclickhdl")))

# This defines the new GUI look and feel.  To understand this you have to be familiar with XUL.
tabSpec = ("vbox",{"flex":1},[("button", {"label":"Print The Time","onclick":lambda x: dynxul.hprt("<h2>" + time.asctime() + "</h2>")},None),("button",{"label":"Click Me!","onclick":myfunc},None)])

# Ok now add the new tab!
dynxul.addSidebarTab("Example",[tabSpec])
</textarea>
<br/>
Test this by pressing the 2 buttons.  You should see the time appear in the Juiced PyShell window (you may need to scroll down).  And you should see the button clicked message.  
<br/>
Now let's modify the handler function.  We squirreled the handle away into a global variable, so it will be easy to just modify the handle.  Incidently, you could also modify the behavior by changing the DOM using the dynxul.theXulDoc global variable.
<br/>

<textarea cols="120" rows="11" style="font-family:monospace">
import handle

# Define a new function
def myfunc2(this):
 dynxul.hprt("""<h2 style='color:yellow'>The button you pressed is labelled '%s'.\nThe onclick handle is '%s'.</h2>""" % (this.getAttribute("label"),this.getAttribute("onclickhdl")))

tmp = handle.hdlTab[myHdl]                 # Temporarily store what's currently there
handle.hdlTab[myHdl] = (myfunc2,tmp[1])    # Overwrite it with my new function, but keep the same argument
</textarea>
<br/>
Now click the "Click Me!" button again and this new function (which prints in yellow) will be executed.
</html>
</section>

</section>
