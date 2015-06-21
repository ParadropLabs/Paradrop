from flask import Flask

import frontend

def main():
    """This function does something.

    :param name: The name to use. 
    :type name: str. 
    :param state: Current state to be in. 
    :type state: bool. 
    :returns: int -- the return code. 
    :raises: AttributeError, KeyError
    """ 
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return 'hello world!'

    #assign to eth0 dynamically (or run it on 80)
    # app.run('10.0.2.15', port = 7777)

    #running locally
    #TODO: determine if running locally or on snappy 
    app.run(port = 7777)

if __name__ == "__main__":
    main()
