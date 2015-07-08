

class PDFCError(Exception):
    """
        Exception class related to ParaDrop Framework Control calls.
    """
    def __init__(self, etype, msg=""):
        self.etype = etype
        self.msg = msg
    
    def __str__(self):
        if(len(self.msg) > 0):
            return "PDFCError %s: %s" % (self.etype, self.msg)
        else:
            return "PDFCError %s" % (self.etype)


