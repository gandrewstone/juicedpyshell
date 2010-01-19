"""?? The handle module assigns string 'handles' to any object.  The purpose is to create a cookie that can be passed into javascript or into the html/xul document.

If you are not familiar with a cookie the basic idea is that javascript/html/xul cannot deal with raw Python.  For example you cannot put python code in an "onclick" handler.  So instead you associate your python code with a handle, and put this handle in the "onclick" handler (its a string) with a little javascript wrapper around it that calls into Python and passes the handle back.  

So now when the onclick handler is run, a Python function is called with your handle.  This function looks up the handle and gets the original python object and then operates on that (for example if the Python object is a function closure, it would call the function).

<license>
MPL 1.1/GPL 2.0/LGPL 2.1
</license>
"""


curHdl = 0  #?? The number of handles that have been created
hdlTab = {} #?? A hash table to store the handle->object mapping

def handleCreate(it):
    """?? Return a new handle associated with the passed object
    <arg name="it">the object you want a handle to</arg>
    <return>A string handle</return>
    """
    global curHdl
    tmp = curHdl
    curHdl+=1
    h = "h%d" % tmp
    hdlTab[h] = it
    return h

def handleDelete(hdl):
    """?? Remove a handle from the lookup table.  If you don't call this when your handle is no longer needed, you will "leak" handles and eventually run out of memory!
    <arg name="hdl">the handle given to you by 'handleCreate'</arg>
    """
    global hdlTab
    del hdlTab[hdl]

def handleGet(hdl):
    """?? Look up an object based on its handle
    <arg name='hdl'> A string handle</arg>
    <exception type='KeyError'>An exception is raised if the handle cannot be found</exception>
    """
    global hdlTab
    return hdlTab[hdl]
