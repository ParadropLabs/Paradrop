
'''
updateObject module.

This holds onto the UpdateObject class.
It allows us to easily abstract away different update types and provide a uniform
way to interpret the results through a set of basic actionable functions.
'''

class UpdateObject(object):
    """
    The base UpdateObject class, covers a few basic methods but otherwise all the intelligence
    exists in the inherited classes above.
    """
    def __init__(self, obj):
        # Pull in all the keys from the obj identified
        self.__dict__.update(obj)
        # No results yet
        self.result = None
    
    def __str__(self):
        return "<Update({}) :: {} - {} @ {}>".format(self.updateClass, self.name, self.updateType, self.tok)

    def complete(self, **kwargs):
        """
            Signal to the API server that any action we need to perform is complete and the API 
            server can finish its connection with the client that initiated the API request.
        """
        # Set our results
        self.result = kwargs
        # Call the function we were provided
        self.func(self)

class UpdateChute(UpdateObject):
    """
    Updates specifically tailored to chute actions like create, delete, etc...
    """
    def __init__(self, obj):
        super(UpdateChute, self).__init__(obj)







UPDATE_CLASSES = {
    "CHUTE": UpdateChute
}

def parse(obj):
    """
    Determines the update type and returns the proper class.
    """
    uclass = obj.get('updateClass', None)
    cls = UPDATE_CLASSES.get(uclass, None)

    if(cls is None):
        raise Exception('BadUpdateType')
    return cls(obj)
