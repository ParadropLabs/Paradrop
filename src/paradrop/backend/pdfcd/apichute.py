# Import ParaDrop related stuff
from lib.utils.output import out, logPrefix
from lib.utils.pdutils import json2str, str2json, timeint, urlDecodeMe

from lib.api.pdrest import APIDecorator
from lib.api import pdapi


#########################################################################################################################
# DB API AP module
#########################################################################################################################

class ChuteAPI:
    def __init__(self, rest):
        self.rest = rest
        self.rest.register('POST', '^/v1/chute/create$', self.POST_createChute)



    @APIDecorator(requiredArgs=["sessionToken"])
    def POST_createChute(self, apiPackage):
        """
           Description:
               Get the network config of all chutes under an AP  from the vnet_network table
           Arguments:
               POST request:
                  @sessionToken
                  @apid
           Returns:
               On success:
                  List of:
                      * radioid: INT
                      * isprimary: 0/1
                      * config: JSON
               On failure: A string explain the reason of failure
        """
        #token, apid = pdutils.explode(apiPackage.inputArgs, "sessionToken", "apid")
        
        out.info('-- {} Creating chute...\n'.format(logPrefix()))
        
        # TODO implement
        result = dict(success=True, message='Successfully launched chute')
        
        if(result is None):
            apiPackage.setFailure(errType=pdapi.ERR_BADAUTH, countFailure=False)
        else:
            apiPackage.setSuccess(json2str(result))



    
