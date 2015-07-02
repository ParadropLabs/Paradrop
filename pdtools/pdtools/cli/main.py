'''
Entry point for CLI interaction with PD Tools
'''

import argparse


def createArgs():
    parser = argparse.ArgumentParser(description='Paradrop build tools')

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('integers', metavar='N', type=int, nargs='+', help='an integer for the accumulator')

    parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max,
                        help='sum the integers (default: find the max)')

    return parser


def main():
    '''
    Entry point for CLI tools
    '''

    args = createArgs().parse_args()
    print(args.accumulate(args.integers))
