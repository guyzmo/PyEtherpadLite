#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger('py_etherpad.Authors')

class Authors(object):
    def __init__(self, authors={}):
        self._authors = authors
        self._user_id = None
        self._user_col = None

    def set_user_id(self, i, aid, name=None, color="#000000"):
        self._user_id = i
        self._user_color = color
        self._authors[aid] = dict(name=name, color=color, padIDs={})

    def get_user_id(self):
        return self._user_id

    def get_user_color(self):
        return self._user_col

    def set_color_palette(self, cp):
        log.debug("set_color_palette")
        self._color_palette = cp

    def add(self, a, name=None, color="#000000", padIDs={}):
        log.debug("add(%s, %s, %s, %s)" % (a, name, color, padIDs))
        self._authors[a] = dict(name=name, color=color, padIDs=padIDs)

    def get_color(self, a):
        log.debug("get_color(%s)" % (a,))
        if not a or not self._authors[a]['color']:
            return '#000000'
        if self._authors[a]['color'] < len(self._color_palette):
            return self._color_palette[self._authors[a]['color']]
        return self._authors[a]['color']

    def get_color_idx(self, a):
        log.debug('get_color_idx(%s)' % a)
        if not a:
            return 0
        if self._authors[a]['color'] in self._color_palette:
            log.debug('get_color_idx(%s): %s' % (a, self._color_palette.index(_authors[a]['color'])))
            return self._color_palette.index(_authors[a]['color'])
        log.debug('get_color_idx(%s): NOT IN PALETTE' % a)
        return 0

    def get_name(self, a):
        log.debug("get_name")
        return self._authors[a]['name']

    def get_pads(self, a):
        log.debug("get_pads")
        return self._authors[a]['padIDs']

    def has(self, a):
        log.debug("has")
        if a in self._authors.keys():
            return True
        return False

