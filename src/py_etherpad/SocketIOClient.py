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

from EtherpadLiteClient import APIClient
from Text import Text
from Attributes import Attributes
from Changeset import pack
from Cursors import Cursors
from Authors import Authors
from utils import id_generator

class EtherpadDispatch(object):
    def __init__(self):
        self.events = dict(CLIENT_VARS=self.on_clientvars,
                    NEW_CHANGES=self.on_new_changes,
                    USER_NEWINFO=self.on_user_newinfo,
                    CUSTOM=self.on_custom)
        self.rev = -1
        self.text = ""
        # self.author_name = None
        # self.author_userid = None
        # self.author_colorid = None
        self.authors = Authors()
        self.cursors = Cursors()

    def on_clientvars(self, data):
        log.debug("on_clientvars: %s" % data)
        vars = data["collab_client_vars"]

        text  = vars["initialAttributedText"]["text"]
        csd   = dict(old_len=len(text),
                     new_len=len(text),
                     ops=vars["initialAttributedText"]["attribs"],
                     char_bank="")
        apool = vars["apool"]

        self.text = Text(text=text, cursors=self.cursors, attribs=Attributes(pool=apool), authors=self.authors)
        csd = pack(csd)
        self.text.update(csd)

        self.rev           = vars["rev"]
        for author, d in vars["historicalAuthorData"].iteritems():
            self.authors.add(author, name=d['name'], color=d['colorId'], padIDs=d['padIDs'])
        self.authors.set_color_palette(data["colorPalette"])
    def on_new_changes(self, data):
        log.debug("on_new_changes: %s" % data)
        newRev = data["newRev"]
        changeset = data["changeset"]
        if 'apool' in data.keys():
            self.text._attributes._pool = data['apool']
        if newRev > self.rev:
            log.debug("apply changeset %s at rev %s" % (changeset, newRev))
            self.text.update(changeset)
        else:
            log.error("ERROR: new revision prior to current revision")
    def on_user_newinfo(self, data):
        log.debug("on_user_newinfo: %s" % data)
        userid = data["userInfo"]["userId"]
        name = userid
        if "name" in data["userInfo"]:
            name = data["userInfo"]["name"]
        colorid = data["userInfo"]["colorId"]
        self.authors.add(userid, name=name, color=colorid)
        log.debug("new author: %s (id:%s, color:%s)" % (name, userid, colorid))
    def on_custom(self, data):
        if data["payload"]["action"] == "cursorPosition":
            log.debug("on_custom:cursorPosition: %s" % data)
            locationX = data["payload"]["locationX"]
            locationY = data["payload"]["locationY"]
            authorId = data["payload"]["authorId"]
            authorName = data["payload"]["authorName"]
            self.cursors.update(authorId, locationX, locationY)
            log.debug("change cursor position of (%s, %s) to (%s, %s)" % (authorId,
                                                                        authorName,
                                                                        locationX,
                                                                        locationY))

class EtherpadService(BaseNamespace, EtherpadDispatch):
    def __init__(self, *args, **kwarg):
        BaseNamespace.__init__(self, *args, **kwarg)
        EtherpadDispatch.__init__(self)
    def on_authorization(self, *args):
        log.debug('[Auth] %s' % (args,))
    def on_connect(self, socketIO):
        log.debug('[Connected]')
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
        log.info('[Disconnected]')
    def on_error(self, data):
        log.error('[Error] %s' % (data,))
    def on_message(self, msg):
        print chr(27) + "[2J" # clear screen
        log.debug('[Message] %s:' % (msg["type"]),)
        if msg["type"] in self.events.keys():
            self.events[msg["type"]](msg["data"])
        elif msg["type"] == "COLLABROOM" and msg["data"]["type"] in self.events.keys():
            self.events[msg["data"]["type"]](msg["data"])
            ret = self.socketIO.params["cb"](self.text)
            print "--------8<-------------------8<-----------"
            print ret
            print "-------->8------------------->8-----------"
        else:
            typ = msg["type"]
            if typ == "COLLABROOM" and "type" in msg["data"].keys():
                typ = msg["data"]["type"]
            log.error("Unknown event %s" % typ) # XXX raise ?
