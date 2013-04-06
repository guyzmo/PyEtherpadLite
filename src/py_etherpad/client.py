#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger('py_etherpad.client')

import sys
import time
import string
import random
import urllib2
import cookielib
import argparse

from socketIO_client import SocketIO, BaseNamespace

from EtherpadLiteClient import EtherpadLiteClient
from Text import Text
from Attributes import Attributes
from Changeset import pack

def id_generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for x in range(size))

class Cursors(object):
    def __init__(self):
        self._cur_pos = {}
        self._cursors = {}

    def update(self, authorid, posx, posy):
        npos = (posx, posy)
        if authorid in self._cursors.keys():
            pos = self._cursors[authorid]
            del self._cur_pos[pos]
        self._cursors[authorid] = npos
        self._cur_pos[npos] = authorid

    def get(self, x, y):
        if (x, y) in self._cur_pos.keys():
            return self._cur_pos[(x, y)]
        return None

class Authors(object):
    def __init__(self, authors={}):
        self._authors = authors

    def set_color_palette(self, cp):
        self._color_palette = cp

    def add(self, a, name=None, color="#000000", padIDs={}):
        self._authors[a] = dict(name=name, color=color, padIDs=padIDs)

    def get_color(self, a):
        if self._authors[a]['color'] in self._color_palette:
            return self._color_palette[self._authors[a]['color']]
        return self._color_palette[0]

    def get_name(self, a):
        return self._authors[a]['name']

    def get_pads(self, a):
        return self._authors[a]['padIDs']

    def has(self, a):
        if a in self._authors.keys():
            return True
        return False

class EtherpadDispatch(object):
    def __init__(self):
        self.events = dict(CLIENT_VARS=self.on_clientvars,
                    NEW_CHANGES=self.on_new_changes,
                    USER_NEWINFO=self.on_user_newinfo,
                    CUSTOM=self.on_custom)
        self.rev = -1
        self.text = ""
        self.author_name = None
        self.author_userid = None
        self.author_colorid = None
        self.authors = Authors()
        self.cursors = Cursors()

    def on_clientvars(self, data):
        vars = data["collab_client_vars"]

        text  = vars["initialAttributedText"]["text"]
        csd   = dict(old_len=len(text),
                     new_len=len(text),
                     ops=vars["initialAttributedText"]["attribs"],
                     char_bank="")
        apool = vars["apool"]

        self.text = Text(text=text, cursors=self.cursors, attribs=Attributes(pool=apool), authors=self.authors)
        csd = pack(csd)
        print "first changeset:", csd
        self.text.update(csd)

        self.rev           = vars["rev"]
        print vars["historicalAuthorData"]
        for author, d in vars["historicalAuthorData"].iteritems():
            self.authors.add(author, name=d['name'], color=d['colorId'], padIDs=d['padIDs'])
        self.authors.set_color_palette(data["colorPalette"])
    def on_new_changes(self, data):
        newRev = data["newRev"]
        changeset = data["changeset"]
        if 'apool' in data.keys():
            self.text._attributes._pool = data['apool']
        if newRev > self.rev:
            print "apply changeset %s at rev %s" % (changeset, newRev)
            self.text.update(changeset)
        else:
            print "ERROR: new revision prior to current revision"
    def on_user_newinfo(self, data):
        print data["userInfo"]
        name = data["userInfo"]["name"]
        userid = data["userInfo"]["userId"]
        colorid = data["userInfo"]["colorId"]
        self.authors.add(userid, name=name, color=colorid)
        print "new author: %s (id:%s, color:%s)" % (self.author_name, self.author_userid, self.author_colorid)
    def on_custom(self, data):
        if data["payload"]["action"] == "cursorPosition":
            locationX = data["payload"]["locationX"]
            locationY = data["payload"]["locationY"]
            authorId = data["payload"]["authorId"]
            authorName = data["payload"]["authorName"]
            self.cursors.update(authorId, locationX, locationY)
            print "change cursor position of (%s, %s) to (%s, %s)" % (authorId,
                                                                        authorName,
                                                                        locationX,
                                                                        locationY)

class EtherpadService(BaseNamespace, EtherpadDispatch):
    def __init__(self, *args, **kwarg):
        BaseNamespace.__init__(self, *args, **kwarg)
        EtherpadDispatch.__init__(self)
    def on_authorization(self, *args):
        print '[Auth] %s' % (args,)
    def on_connect(self, socketIO):
        print '[Connected] %s' % socketIO
        def on_response(self, *args):
            print "[Connected:Response]", args
        socketIO.emit('message', dict(component='pad',
                                           type="CLIENT_READY",
                                           padId=socketIO.params['padid'],
                                           sessionID=None,
                                           password=None,
                                           token="t.%s" % (id_generator(20),),
                                           protocolVersion=2), on_response)
    def on_disconnect(self):
        print '[Disconnected]'
    def on_error(self, data):
        print '[Error] %s' % (data,)
    def on_message(self, msg):
        print chr(27) + "[2J" # clear screen
        print '[Message] %s:' % (msg["type"]),
        if msg["type"] in self.events.keys():
            self.events[msg["type"]](msg["data"])
        elif msg["type"] == "COLLABROOM" and msg["data"]["type"] in self.events.keys():
            self.events[msg["data"]["type"]](msg["data"])
            print "--------8<-------------------8<-----------"
            print self.text.decorated()
            print "-------->8------------------->8-----------"
        else:
            typ = msg["type"]
            if msg["type"] == "COLLABROOM" and "type" in msg["data"].keys():
                typ = msg["data"]["type"]
            print "Unknown event %s" % typ # XXX raise ?


def run_socketio(args):
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    res = opener.open("http://%s:%s/p/%s" % (args.host, args.port, args.pad))

    session = res.headers['set-cookie']

    socketIO = SocketIO(args.host, args.port, EtherpadService,
                                                        session=session,
                                                        padid=args.pad)
    socketIO.wait()


def run_api(args):
    mypad = EtherpadLiteClient(args.apikey, "http://%s:%s/api" % (args.host,
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
                print text.decorated()
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

    if args.api:
        run_api(args)
    else:
        run_socketio(args)


if __name__ == "__main__":
    run()

