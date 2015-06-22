'''
Core module. Contains the entry point into Paradrop and establishes all other modules.
Does not implement any behavior itself.
'''

from flask import Flask
import frontend


def main():
    """
    This function does something. Right now what its doing is demonstrating
    a docstring with sphinxy additions.

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

    # assign to eth0 dynamically (or run it on 80)
    # app.run('10.0.2.15', port = 7777)

    # running locally
    # TODO: determine if running locally or on snappy
    app.run(port=7777)

    # Just playing with anaconda autocomplete
    frontend.stuff.afunction()

if __name__ == "__main__":
    main()
