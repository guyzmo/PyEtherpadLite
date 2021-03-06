#!/usr/bin/env python
"""Module to talk to EtherpadLite API."""

import json
import urllib
import urllib2

class APIClient:
    """Client to talk to EtherpadLite API."""
    API_VERSION = "1.2.8"

    CODE_OK = 0
    CODE_INVALID_PARAMETERS = 1
    CODE_INTERNAL_ERROR = 2
    CODE_INVALID_FUNCTION = 3
    CODE_INVALID_API_KEY = 4
    TIMEOUT = 20

    apiKey = ""
    baseUrl = "http://localhost:9001/api"

    def __init__(self, apiKey=None, baseUrl=None, post=False):
        if apiKey:
            self.apiKey = apiKey

        if baseUrl:
            self.baseUrl = baseUrl

        self.post = post

    def call(self, function, arguments=None):
        """Create a dictionary of all parameters"""
        url = '%s/%s/%s' % (self.baseUrl, self.API_VERSION, function)

        params = arguments or {}
        params.update({'apikey': self.apiKey})
        data = urllib.urlencode(params, True)

        try:
            opener = urllib2.build_opener()
            request = url + "?" + data
            if self.post:
                request = urllib2.Request(url=url, data=data)
            response = opener.open(request, timeout=self.TIMEOUT)
            result = response.read()
            response.close()
        except urllib2.HTTPError:
            raise

        result = json.loads(result)
        if result is None:
            raise ValueError("JSON response could not be decoded")

        return self.handleResult(result)

    def handleResult(self, result):
        """Handle API call result"""
        if 'code' not in result:
            raise Exception("API response has no code")
        if 'message' not in result:
            raise Exception("API response has no message")

        if 'data' not in result:
            result['data'] = None

        if result['code'] == self.CODE_OK:
            return result['data']
        elif result['code'] == self.CODE_INVALID_PARAMETERS or result['code'] == self.CODE_INVALID_API_KEY:
            raise ValueError(result['message'])
        elif result['code'] == self.CODE_INTERNAL_ERROR:
            raise Exception(result['message'])
        elif result['code'] == self.CODE_INVALID_FUNCTION:
            raise Exception(result['message'])
        else:
            raise Exception("An unexpected error occurred whilst handling the response")

    # GLOBALS

    def listAllPads(self):
        """returns all pads (1.2.7)"""
        return self.call("listAllPads")

    def listAllGroups(self):
        """returns all groups"""
        return self.call("listAllGroups")

    def checkToken(self):
        """"""
        return self.call("checkToken")

    # GROUPS
    # Pads can belong to a group. There will always be public pads that do not belong to a group (or we give this group the id 0)

    def createGroup(self):
        """creates a new group"""
        return self.call("createGroup")

    def createGroupIfNotExistsFor(self, groupMapper):
        """this functions helps you to map your application group ids to etherpad lite group ids"""
        return self.call("createGroupIfNotExistsFor", {
            "groupMapper": groupMapper
        })

    def deleteGroup(self, groupID):
        """deletes a group"""
        return self.call("deleteGroup", {
            "groupID": groupID
        })

    def listPads(self, groupID):
        """returns all pads of this group"""
        return self.call("listPads", {
            "groupID": groupID
        })

    def createGroupPad(self, groupID, padName, text=''):
        """creates a new pad in this group"""
        params = {
            "groupID": groupID,
            "padName": padName,
        }
        if text:
            params['text'] = text
        return self.call("createGroupPad", params)

    # AUTHORS
    # Theses authors are bind to the attributes the users choose (color and name).

    def createAuthor(self, name=''):
        """creates a new author"""
        params = {}
        if name:
            params['name'] = name
        return self.call("createAuthor", params)

    def createAuthorIfNotExistsFor(self, authorMapper, name=''):
        """this functions helps you to map your application author ids to etherpad lite author ids"""
        params = {
            'authorMapper': authorMapper
        }
        if name:
            params['name'] = name
        return self.call("createAuthorIfNotExistsFor", params)

    def getAuthorName(self, authorID):
        return self.call("getAuthorName", {
            "authorID": authorID
        })


    def listPads(self, groupID):
        """returns all pads of this author (1.2.7)"""
        return self.call("listPadsOfAuthor", {
            "authorID": authorID
        })

    # SESSIONS
    # Sessions can be created between a group and a author. This allows
    # an author to access more than one group. The sessionID will be set as
    # a cookie to the client and is valid until a certain date.

    def createSession(self, groupID, authorID, validUntil):
        """creates a new session"""
        return self.call("createSession", {
            "groupID": groupID,
            "authorID": authorID,
            "validUntil": validUntil
        })

    def deleteSession(self, sessionID):
        """deletes a session"""
        return self.call("deleteSession", {
            "sessionID": sessionID
        })

    def getSessionInfo(self, sessionID):
        """returns informations about a session"""
        return self.call("getSessionInfo", {
            "sessionID": sessionID
        })

    def listSessionsOfGroup(self, groupID):
        """returns all sessions of a group"""
        return self.call("listSessionsOfGroup", {
            "groupID": groupID
        })

    def listSessionsOfAuthor(self, authorID):
        """returns all sessions of an author"""
        return self.call("listSessionsOfAuthor", {
            "authorID": authorID
        })

    # PAD CONTENT
    # Pad content can be updated and retrieved through the API

    def getAttributePool(self, padID):
        """returns the text of a pad"""
        return self.call("getAttributePool", {"padID": padID})

    def getText(self, padID, rev=None):
        """returns the text of a pad"""
        params = {"padID": padID}
        if rev is not None:
            params['rev'] = rev
        return self.call("getText", params)

    # introduced with pull request merge
    def getHtml(self, padID, rev=None):
        """returns the html of a pad"""
        params = {"padID": padID}
        if rev is not None:
            params['rev'] = rev
        return self.call("getHTML", params)

    def setText(self, padID, text):
        """sets the text of a pad"""
        return self.call("setText", {
            "padID": padID,
            "text": text
        })

    def setHtml(self, padID, html):
        """sets the text of a pad from html"""
        return self.call("setHTML", {
            "padID": padID,
            "html": html
        })

    # PAD
    # Group pads are normal pads, but with the name schema
    # GROUPID$PADNAME. A security manager controls access of them and its
    # forbidden for normal pads to include a  in the name.

    def createPad(self, padID, text=''):
        """creates a new pad"""
        params = {
            "padID": padID,
        }
        if text:
            params['text'] = text
        return self.call("createPad", params)

    def createDiffHTML(self, padID, startRev, endRev):
        """creates a diff between two pads"""
        params = {
            "padID": padID,
            "startRev": startRev,
            "endRev": endRev
        }
        return self.call("createDiffHTML", params)

    def getLastEdited(self, padID):
        return self.call("getLastEdited", {
            "padID": padID
        })

    def getRevisionChangeset(self, padID, rev=None):
        """return the changeset at given rev of this pad"""
        params = {"padID": padID}
        if rev:
            params["rev"] = rev
        return self.call("getRevisionChangeset", params)

    def getRevisionsCount(self, padID):
        """returns the number of revisions of this pad"""
        return self.call("getRevisionsCount", {
            "padID": padID
        })

    def listAuthorsOfPad(self, padID):
        """returns the list of the authors of this pad"""
        return self.call("listAuthorsOfPad", {
            "padID": padID
        })

    def padUsers(self, padID):
        """returns the list of users of this pad"""
        return self.call("padUsers", {
            "padID": padID
        })

    def padUsersCount(self, padID):
        """returns the number of users of this pad"""
        return self.call("padUsersCount", {
            "padID": padID
        })

    def deletePad(self, padID):
        """deletes a pad"""
        return self.call("deletePad", {
            "padID": padID
        })

    def getReadOnlyID(self, padID):
        """returns the read only link of a pad"""
        return self.call("getReadOnlyID", {
            "padID": padID
        })

    def setPublicStatus(self, padID, publicStatus):
        """sets a boolean for the public status of a pad"""
        return self.call("setPublicStatus", {
            "padID": padID,
            "publicStatus": publicStatus
        })

    def getPublicStatus(self, padID):
        """return true of false"""
        return self.call("getPublicStatus", {
            "padID": padID
        })

    def setPassword(self, padID, password):
        """returns ok or a error message"""
        return self.call("setPassword", {
            "padID": padID,
            "password": password
        })

    def isPasswordProtected(self, padID):
        """returns true or false"""
        return self.call("isPasswordProtected", {
            "padID": padID
        })

    # MESSAGE

    def sendClientsMessage(self, padID, msg):
        return self.call("sendClientsMessage", {
            "padID": padID,
            "msg": msg
        })

    def getChatHistory(self, padID, start=None, end=None):
        params = {
            "padID": padID
        }
        if not start is None and not end is None:
            params["start"] = start
            params["end"] = end
        return self.call("getChatHistory", params)

    def getChatHead(self, padID):
        return self.call("getChatHead", {
            "padID": padID
        })


