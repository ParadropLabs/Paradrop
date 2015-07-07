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
        print 'Not implemented. Sorry, love.'


def installChute(host, port, directory):
    '''
    Testing method. Take a git url from github and load it onto snappy-pd. 
    '''

    print 'Installing chute'

    # path = os.abspath(directory)

    # The project directory can either be cloned to the backend or installed locally,
    # doesn't matter which one-- we still have to stream the files over

    params = {'url': directory}
    r = requests.post('http://' + host + ':' + str(port) + '/v1/chute/create', params=params)
    print r.text

    print 'Finished installing chute'


def installParadrop():
    ''' Testing method. Install paradrop, snappy, etc onto SD card '''
    pass

if __name__ == '__main__':
    main()
