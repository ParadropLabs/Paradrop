from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import argparse
import json
import os
import subprocess
import sys
import urllib.request, urllib.parse, urllib.error
from time import sleep

SNAP_COMMON = os.environ['SNAP_COMMON']
LOG_FILE = os.path.join(SNAP_COMMON, "logs", "log")

def parseLine(line):
    try:
        data = json.loads(line)
        msg = urllib.parse.unquote(data['message'])
        print(msg)
    except:
        pass


def runTail(logFile):
    cmd = ['tail', '-n', '100', '-f', LOG_FILE]
    while (True):
        try:
            proc = subprocess.Popen(cmd, \
                                    stdout=subprocess.PIPE, \
                                    universal_newlines=True)

            for line in iter(proc.stdout.readline, ''):
                yield line

            proc.stdout.close()
            proc.wait()
        except subprocess.CalledProcessError:
            print('Failed to open the log file, will try again...')
            sleep(1)
            continue

        sleep(2)

def main():
    p = argparse.ArgumentParser(description='Paradrop log tool')
    p.add_argument('-f',
                   help='Wait for additional data to be appended to the log file when end of file is reached',
                   action='store_true',
                   dest='f')
    args = p.parse_args()

    try:
        if args.f:
            for line in runTail(LOG_FILE):
                parseLine(line)
        else:
            with open(LOG_FILE, "r") as inputFile:
                for line in inputFile:
                    parseLine(line)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
