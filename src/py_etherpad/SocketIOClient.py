#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger('py_etherpad.client')

import string
import requests

from socketIO_client import SocketIO, BaseNamespace

from Text import Text
from Attributes import Attributes
from Changeset import pack
from Cursors import Cursors
from Authors import Authors
from utils import id_generator

class EtherpadIO(object):
    def __init__(self, pad, cb,
                       host='localhost', path='p/', port='9001', secure=False,
                       verbose = False,
                       transports=['xhr-polling', 'websocket'],
                       **kwarg):
        log.debug('EtherpadIO(%s://%s:%s/%s%s")' % ('https' if secure else 'http', host,
                                                  port, path, pad))
        res = requests.get("%s://%s:%s/%s%s" % ('https' if secure else 'http',
                                                  host, port, path, pad))

        cookie = res.headers['set-cookie']
        self.cookie = dict([(cookie[:cookie.find("=")], cookie[cookie.find("=")+1:])])

        self.pad = pad
        self.cb = cb
        self.host = host
        self.path = path
        self.port = port
        self.secure = secure
        self.kwarg = kwarg
        self.transports = transports
        self.__init()

    def __init(self):
        self.epad = SocketIO(self.host, self.port,
                        EtherpadService,
                        secure=self.secure,
                        transports=self.transports,
                        cookies=self.cookie,
                        padid=self.pad,
                        cb=self.cb, **self.kwarg)

    def wait(self):
        reconnect = True
        while reconnect:
            reconnect = self.epad.wait()
            del self.epad
            if reconnect:
                self.__init()

    def has_ended(self):
        return self.epad.has_ended()

    def stop(self):
        self.epad.disconnect()

    def pause(self):
        self.epad.pause()

    def patch_text(self, old, new):
        cs = pack(old.diff(new))
        if cs:
            self.epad.namespace.send_user_changes(old.get_revision(), old.get_apool(), cs)


class EtherpadDispatch(object):
    def __init__(self):
        self.text = None
        self.authors = Authors()
        self.cursors = Cursors()
        self.color = None
        self.user_id = None
        self.changeset = None

    def on_client_vars(self, data):
        log.debug("on_clientvars: %s" % data)
        vars = data["collab_client_vars"]

        text  = vars["initialAttributedText"]["text"]
        csd   = dict(old_len=len(text),
                     new_len=len(text),
                     ops=vars["initialAttributedText"]["attribs"],
                     char_bank="")
        apool = vars["apool"]

        for i, params in apool['numToAttrib'].iteritems():
            if params[0] == 'author' and params[1] == data['userId']:
                user_id = i
                break
        else:
            apool['numToAttrib'][str(int(i)+1)] = ['author', data["userId"]]
            user_id = str(int(i)+1)
        self.authors.set_user_id(user_id, data['userId'], color=data['userColor'])

        self.text = Text(text=text, cursors=self.cursors, attribs=Attributes(pool=apool), authors=self.authors)
        csd = pack(csd)
        self.text.update(csd)

        self.text.set_revision(int(vars["rev"]))
        for author, d in vars["historicalAuthorData"].iteritems():
            name = d['name'] if 'name' in d.keys() else author
            self.authors.add(author, name=name, color=d['colorId'], padIDs=d['padIDs'])
        self.authors.set_color_palette(data["colorPalette"])

    def on_new_changes(self, data):
        log.debug("on_new_changes: %s" % data)
        newRev = int(data["newRev"])
        changeset = data["changeset"]
        if 'apool' in data.keys():
            self.text._attributes._pool = data['apool']
        if newRev > self.text.get_revision():
            log.debug("apply changeset %s at rev %s" % (changeset, newRev))
            self.text.update(changeset)
            self.text.set_revision(newRev)
        else:
            log.error("ERROR: new revision prior to current revision")

    def on_accept_commit(self, data):
        log.debug('on_accept_commit(%s)' % data)
        rev = int(data["newRev"])
        changeset = self.changeset['changeset']
        if 'apool' in self.changeset.keys():
            self.text._attributes._pool = self.changeset['apool']
        if rev > self.text.get_revision():
            log.debug("apply changeset %s at rev %s" % (changeset, rev))
            self.text.update(changeset)
            self.text.set_revision(rev)
        else:
            log.error("base revision different from current")


    def on_user_newinfo(self, data):
        log.debug("on_user_newinfo: %s" % data)
        userid = data["userInfo"]["userId"]
        name = userid
        if "name" in data["userInfo"]:
            name = data["userInfo"]["name"]
        colorid = data["userInfo"]["colorId"]
        self.authors.add(userid, name=name, color=colorid)
        log.debug("new author: %s (id:%s, color:%s)" % (name, userid, colorid))

    def on_user_leave(self, data):
        log.debug("on_user_leave: %s" % data)

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
        elif data["payload"]["action"] == "requestRTC":
            message = {
                "type" : 'RTC',
                "action" : 'declineRTC',
                "padId" : data["payload"]["padId"],
                "targetAuthorId" : data["payload"]["targetAuthorId"],
                "myAuthorId" : data["payload"]["authorId"]
            }
            def on_response(self, *args):
                log.debug("requestRTC:Response(%s)" % args)
            self.socketIO.emit('message', dict(component='pad',
                                            type="CUSTOM",
                                            padId=self.socketIO.params['padid'],
                                            data=dict(payload=message),
                                            protocolVersion=2), on_response)


class EtherpadService(BaseNamespace, EtherpadDispatch):
    def __init__(self, *args, **kwarg):
        BaseNamespace.__init__(self, *args, **kwarg)
        EtherpadDispatch.__init__(self)
        self.connected = False

    # Events listening

    def on_authorization(self, *args):
        log.debug('[Auth] %s' % (args,))

    def on_connect(self, socketIO):
        log.debug('[Connected]')
        self.connected = True
        self.send_client_ready()

    def on_close(self, *args):
        """Function that can handle graceful shutdown… if needed"""
        self.socketIO.transport.close()

    def on_disconnect(self):
        log.info('[Disconnected]')
        if 'disc_cb' in self.socketIO.params:
            self.socketIO.params['disc_cb']()

    def on_noop(self):
        if not self.connected:
            log.warn("[Reconnecting]")
            self.socketIO.disconnect(reconnect = True)

    def on_error(self, *args):
        log.error('[Error] %s' % (args,))

    def on_message(self, msg):
        log.debug('[Message] %s:' % (msg),)

        if 'disconnect' in msg.keys():
            log.error('on_message: %s' % msg['disconnect'])
            self.socketIO.disconnect()
            self.on_disconnect()
            return

        typ = msg["type"]
        if typ == "COLLABROOM" and "type" in msg["data"].keys():
            typ = msg["data"]["type"]

        if hasattr(EtherpadDispatch, "on_"+typ.lower()):
            getattr(EtherpadDispatch, "on_"+typ.lower())(self, msg["data"])
            self.socketIO.params["cb"](self.text)
        else:
            log.error("Unknown event '%s': missing '%s()' method." % (typ,
                                                            "on_"+typ.lower()))

    # Events sending

    def send_client_ready(self):
        def on_response(self, *args):
            log.debug("[Connected:Response] %s" % args)

        self.socketIO.emit('message', dict(component='pad',
                                           type="CLIENT_READY",
                                           padId=self.socketIO.params['padid'],
                                           sessionID=None,
                                           password=None,
                                           token="t.%s" % (id_generator(20),),
                                           protocolVersion=2), on_response)

    def send_changeset_req(self, data, granularity, start, request_id):
        def on_response(self, *args):
            log.debug("[send_changeset:Response] %s"% args)
        self.socketIO.emit('message', dict(component='pad',
                                           type="CHANGESET_REQ",
                                           padId=self.socketIO.params['padid'],
                                           data=data,
                                           granularity=granularity,
                                           start=start,
                                           requestID=request_id,
                                           protocolVersion=2), on_response)

    def send_user_changes(self, baseRev, apool, changeset):
        """
        :param baseRev: revision on which is based the changeset
        :param apool: attribute pool of all used attributes in the changeset
        :param changeset: packed string representing of a changeset object
        """
        def on_response(self, *args):
            log.debug("[send_user_changes:Response]: %s" % args)
        self.changeset = dict(type="USER_CHANGES",
                                baseRev=baseRev,
                                apool=apool,
                                changeset=changeset)
        self.socketIO.emit('message', dict(component='pad',
                                           type="COLLABROOM",
                                           padId=self.socketIO.params['padid'],
                                           data=self.changeset,
                                           protocolVersion=2), on_response)

    def send_userinfo_update(self, name, colorId):
        def on_response(self, *args):
            log.debug("[send_userinfo_update:Response]: %s" % args)
        self.socketIO.emit('message', dict(component='pad',
                                           type="COLLABROOM",
                                           padId=self.socketIO.params['padid'],
                                           data=dict(type="USERINFO_UPDATE",
                                                     userInfo=dict(name=name,
                                                                   colorId=colorId)
                                                     ),
                                           protocolVersion=2), on_response)

    def send_chat_message(self, text):
        def on_response(self, *args):
            log.debug("[send_changeset:Response]: %s" % args)
        self.socketIO.emit('message', dict(component='pad',
                                           type="COLLABROOM",
                                           data=dict(type="CHAT_MESSAGE",
                                                     text=text),
                                           padId=self.socketIO.params['padid'],
                                           protocolVersion=2), on_response)

    def send_get_chat_messages(self, start, end):
        def on_response(self, *args):
            log.debug("[send_changeset:send_get_chat_message]: %s" % args)
        self.socketIO.emit('message', dict(component='pad',
                                           type="COLLABROOM",
                                           data=dict(type="GET_CHAT_MESSAGES",
                                                     start=start, end=end),
                                           padId=self.socketIO.params['padid'],
                                           protocolVersion=2), on_response)

    def send_save_revision(self, data):
        def on_response(self, *args):
            log.debug("[send_save_revision:Response]: %s" % args)
        self.socketIO.emit('message', dict(component='pad',
                                           type="COLLABROOM",
                                           data=dict(type="SAVE_REVISION"),
                                           padId=self.socketIO.params['padid'],
                                           protocolVersion=2), on_response)

    def send_client_message(self, data):
        def on_response(self, *args):
            log.debug("[send_client_message:Response]: %s" % args)
        self.socketIO.emit('message', dict(component='pad',
                                           type="COLLABROOM",
                                           padId=self.socketIO.params['padid'],
                                           data=dict(
                                                  type="CLIENT_MESSAGE",
                                                  payload=dict(
                                                      type="suggestUserName",
                                                      newName=name,
                                                      unnamedId=authorid
                                                  )
                                           ),
                                           protocolVersion=2), on_response)

