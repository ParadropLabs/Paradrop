#!/usr/bin/python

import json
import urllib

LOG_FILE = "/root/apps/paradrop/0.1.0/logs/log"

if __name__ == "__main__":
    with open(LOG_FILE, "r") as inputFile:
        for line in inputFile:
            try:
                data = json.loads(line)
                msg = urllib.unquote(data['message'])
                print(msg)
            except:
                pass
