"""Paradrop build tools.

Usage:
    paradrop install <chute-directory> <host> <port>
    paradrop snap-install <host> <port>`
    paradrop (-h | --help)
    paradrop --version
Options:
    -h --help     Show this screen.
    --version     Show version.
"""


from docopt import docopt
import requests
import os


def main():
    # args = createArgs().parse_args()
    # print(args)

    args = docopt(__doc__, version='Paradrop build tools v0.1')
    # print(args)

    if args['install']:
        installChute(args['<host>'], args['<port>'], args['<chute-directory>'])

    if args['snap-install']:
        pass

def installChute(host, port, directory):
    '''
    Testing method. Take a local chute and load it onto pd
    '''
    print 'Installing chute'
    
    path = os.abspath(directory)


def installParadrop():
    ''' Testing method. Install paradrop, snappy, etc onto something '''
    pass

if __name__ == '__main__':
    main()
