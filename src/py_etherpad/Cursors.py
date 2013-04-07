#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger('py_etherpad.Cursors')

class Cursors(object):
    def __init__(self):
        self._cur_pos = {}
        self._cursors = {}

    def update(self, authorid, posx, posy):
        log.debug("update(a:%s, x:%s, y:%s)" % (authorid, posx, posy))
        npos = (posx, posy)
        if authorid in self._cursors.keys():
            pos = self._cursors[authorid]
            del self._cur_pos[pos]
        self._cursors[authorid] = npos
        self._cur_pos[npos] = authorid

    def get(self, x, y):
        log.debug("get(x:%s, y:%s)" % (x, y))
        if (x, y) in self._cur_pos.keys():
            return self._cur_pos[(x, y)]
        return None

