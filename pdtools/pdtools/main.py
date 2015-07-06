"""Paradrop build tools.

Usage:
    paradrop install <chute-directory> <host> <port>
    paradrop snapinstall <host> <port>
    paradrop (-h | --help)
    paradrop --version
Options:
    -h --help     Show this screen.
    --version     Show version.
"""



from docopt import docopt


def main():
    # args = createArgs().parse_args()
    # print(args)

    arguments = docopt(__doc__, version='Paradrop build tools v0.1')
    print(arguments)


if __name__ == '__main__':
    main()
