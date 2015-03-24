The Juiced Python Firefox Shell lets you automate a browser using python scripts. It requires that the pyxpcomext extension be installed.  It is useful for browser automation, including automated testing of web sites.  It makes it easy to do screen scraping and html manipulation using Python.

This project is a fork of the pyShell project.  You can find the original pyShell in the pyxpcomext examples.

Documentation is available <a href='http://juicedpyshell.googlecode.com/svn/trunk/doc/html/index.html'>here</a>

## Introduction ##
Juiced PyShell is a Python shell that you can install into your Firefox browser. You can run any Python program within this shell, but of course it makes the most sense to run programs that need to access and modify web pages!

## Why do it this way? ##
### Web 2.0 ###
There are other technologies that allow Python to access web pages. In fact, it is very easy to "get" web pages using Python's standard httplib and urllib libraries. However, web pages are becoming significantly more sophisticated. With the adoption of the asynchronous design patterns that the industry calls "web 2.0", urllib and httplib simply will not work. To read Web 2.0 pages as the end user does, you need a full Javascript interpreter on the client. So the client needs to be a very sophisticated piece of software, instead of just a protocol engine. The simplest way to get this sophistication is to merge Python with one the already exists!
### Local Markup ###
Additionally, you may not want a standalone program that crawls web pages. Instead, you may be looking for computer-assisted browsing. In other words, the Python program accesses a local or remote resource (a database for example) and combines information from that resource into your browsing experience. A simple example would be to mark up every link with information about when it was last browsed (sort of integrating the "history" information with the current page). A more complex example would be to highlight all differences between this and prior viewings of a page. Or to eliminate pesky advertising. And so on.
### Features ###
Juiced PyShell gives you complete access to the Python language, standard libraries, and libraries that you install. It lets you modify the browser's view of any web page, including itself. All of this is actually provided via the pyXPCOMext plugin and the PyShell sample upon which Juiced PyShell is based. In fact those projects are the majority of the work and deserve all the credit!
What Juiced PyShell gives you is a bit of user-friendliness on top of the pyXPCOMext engine. It:

  * Wraps common XPCOM functions such as getting a browser window, waiting for pages to load up, etc.
  * Provides simple but powerful DOM (document-object-model) access functions that allow your script to quickly zero in on the data you need
  * Provides a powerful DOM creation engine so you can easily modify web pages.
  * Hides browser threading, and display issues and gotchas
  * Does all of the above for the Juiced PyShell window itself, which allows your Python programs to easily add GUI widgets
  * And finally it provides an enhanced Python shell experience, including display of HTML within the shell output, and GUI display and control of running threads