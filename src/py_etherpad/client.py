#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger('py_etherpad.client')

import sys
import time
import urllib2
import argparse
import requests

from socketIO_client import SocketIO

from EtherpadLiteClient import APIClient
from SocketIOClient import EtherpadService
from Cursors import Cursors
from Authors import Authors
from Style import STYLES


def run_socketio(args):
    log.debug("launched as socket.io client")

    def printout(text):
        if not text is None:
            print chr(27) + "[2J" # clear screen
            t = text.decorated(style=STYLES[args.style]())
            print "--------8<----------------8<----------------8<---------------8<--------"
            print t
            print "-------->8---------------->8---------------->8--------------->8--------"

    res = requests.get("http://%s:%s/p/%s" % (args.host, args.port, args.pad))

    cookie = res.headers['set-cookie']
    cookie = dict([(cookie[:cookie.find("=")], cookie[cookie.find("=")+1:])])

    reconnect = True
    while reconnect:
        socketIO = SocketIO(args.host, args.port, EtherpadService,
                                                            transports=['xhr-polling',
                                                                        'websocket'],
                                                            cookies=cookie,
                                                            padid=args.pad,
                                                            cb=printout)
        reconnect = socketIO.wait()
        del socketIO


def run_api(args):
    log.debug("launched as API client")
    mypad = APIClient(args.apikey, "http://%s:%s/api" % (args.host,
                                                                   args.port))

    text = Text(Attributes(mypad, args.pad), Authors(), Cursors())
    idx = 0
    while True:
        try:
            cnt = int(mypad.getRevisionsCount(args.pad)["revisions"])
            if cnt+1 != idx:
                print chr(27) + "[2J" # clear screen
                print ""
                for i in range(idx, cnt+1):
                    cs = mypad.getRevisionChangeset(args.pad, str(i))
                    text.update(cs)
                else:
                    idx = cnt+1
                print text.decorated(style=STYLES[args.style]())
            time.sleep(1)
        except urllib2.URLError:
            log.error("Can't connect to pad '%s' at url 'http://%s:%s/api/'" % (args.pad,
                                                                            args.host,
                                                                            args.port))
            time.sleep(2)
            continue

def run():
    parser = argparse.ArgumentParser(prog=sys.argv[0],
            description="Tablesoccer B12:0 embedded client")

    parser.add_argument("-A", "--api",
                        dest="api",
                        action="store_true",
                        help="run API based version – needs a special etherpadlite service")

    parser.add_argument("-k",
                        "--key",
                        dest="apikey",
                        help='API Key')

    parser.add_argument("-H", "--host",
                        dest="host",
                        default="127.0.0.1")
    parser.add_argument("-P", "--port",
                        dest="port",
                        default="9001")

    parser.add_argument("-r", "--refresh",
                        dest="refresh",
                        default="1",
                        help="interval time between two text refresh")

    parser.add_argument("-K", "--keepalive",
                        dest="keepalive",
                        default="5",
                        help="interval time between two connection tries")

    parser.add_argument("-s", "--style",
                        dest="style",
                        choices=STYLES.keys(),
                        default='Default')

    parser.add_argument("-v",
                        "--verbose",
                        dest="debug",
                        action="store_true",
                        help='enables debug output')

    parser.add_argument(dest="pad",
                        help="Pad to connect to")

    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig()
    if args.debug:
        logging.root.setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.INFO)
    else:
        logging.root.setLevel(logging.INFO)
        logging.getLogger('urllib3').setLevel(logging.WARN)

    if args.api:
        run_api(args)
    else:
        run_socketio(args)


if __name__ == "__main__":
    run()

