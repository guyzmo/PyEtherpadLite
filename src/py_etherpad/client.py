#!/usr/bin/env python

import logging
log = logging.getLogger('py_etherpad.client')

import sys
import time
import urllib2
import argparse

from EtherpadLiteClient import EtherpadLiteClient
from Text import Text

def run():
    parser = argparse.ArgumentParser(prog=sys.argv[0],
            description="Tablesoccer B12:0 embedded client")

    parser.add_argument("-k",
                        "--key",
                        dest="apikey",
                        help='API Key')

    parser.add_argument("-u", "--url",
                        dest="url",
                        help="http://127.0.0.1:9001/api")

    parser.add_argument("-r", "--refresh",
                        dest="refresh",
                        default="1",
                        help="interval time between two text refresh")

    parser.add_argument("-K", "--keepalive",
                        dest="keepalive",
                        default="5",
                        help="interval time between two connection tries")

    parser.add_argument("-v",
                        "--verbose",
                        dest="debug",
                        action="store_true",
                        help='enables debug output')

    parser.add_argument(dest="pad",
                        help="Pad to connect to")

    args = parser.parse_args(sys.argv[1:])

    if args.debug:
        logging.root.setLevel(logging.DEBUG)
    else:
        logging.root.setLevel(logging.INFO)

    mypad = EtherpadLiteClient(args.apikey, args.url)

    text = Text(mypad, args.pad)
    idx = 0
    while True:
        try:
            cnt = int(mypad.getRevisionsCount(args.pad)["revisions"])
            if cnt+1 != idx:
                #print chr(27) + "[2J" # clear screen
                print ""
                for i in range(idx, cnt+1):
                    cs = mypad.getRevisionChangeset(args.pad, str(i))
                    text.update(cs)
                else:
                    idx = cnt+1
                print text.decorated()
            time.sleep(1)
        except urllib2.URLError:
            log.error("Can't connect to pad '%s' at url '%s'" % (args.pad,
                                                                 args.url))
            time.sleep(2)
            continue


if __name__ == "__main__":
    run()

