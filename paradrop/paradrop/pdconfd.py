'''
Entry point for the pdconfd daemon.
Does not implement any behavior itself.
'''

from twisted.internet import reactor
from paradrop.backend import pdconfd

##########################################################################
# Main Function
##########################################################################

def run_pdconfd():
    reactor.callWhenRunning(pdconfd.main.listen)
    reactor.run()

if __name__ == "__main__":
    run_pdconfd()
