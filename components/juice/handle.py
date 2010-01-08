

curHdl = 0
hdlTab = {}
def handleCreate(it):
    global curHdl
    tmp = curHdl
    curHdl+=1
    h = "h%d" % tmp
    hdlTab[h] = it
    return h

def handleDelete(hdl):
    global hdlTab
    del hdlTab[hdl]

def handleGet(hdl):
    global hdlTab
    return hdlTab[hdl]
