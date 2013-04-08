#!/usr/bin/env python
# -+- encoding: utf-8 -+-

import logging
log = logging.getLogger('py_etherpad.Text')

from Attributes import Attributes
from Changeset import Changeset
from Style import Style


class TextRepr:
    def __init__(self):
        self.chars = {}
        self.attribs = dict()
        self.authors = dict()
        self.attrlist = dict()


class Text:
    def __init__(self, attribs, authors, cursors, text=None):
        log.debug("Text()")
        self._t = TextRepr()

        self._cursors = cursors
        self._authors = authors
        self._attributes = attribs
        self._changeset = Changeset(self._attributes)

        if text:
            for i in range(0, len(text)):
                self._t.chars[i] = text[i]
                self._t.attribs[i] = list()
                self._t.authors[i] = None

    def length(self):
        return len(self._t.chars.keys())

    def __len__(self):
        return self.length()

    def insert_at(self, idx, substr, attr=None):
        log.debug("Text.insert_at(%s, %s, %s)" % (idx, substr, attr))
        ls = len(substr)
        lt = len(self)
        chars = dict()
        attribs = dict()
        authors = dict()

        for i in range(0, idx):
            chars[i] = self._t.chars[i]
            attribs[i] = self._t.attribs[i]
            authors[i] = self._t.authors[i]

        for i, c in zip(range(idx, idx+ls), substr):
            chars[i] = c
            attribs[i] = list()
            authors[i] = None

        for i in range(idx+ls, lt+ls):
            chars[i] = self._t.chars[i-ls]
            attribs[i] = self._t.attribs[i-ls]
            authors[i] = self._t.authors[i-ls]

        self._t.chars = chars
        self._t.attribs = attribs
        self._t.authors = authors

    def remove(self, idx, length, attr=None):
        """
        """
        log.debug("Text.remove(%s, %s, %s)" % (idx, length, attr))
        for i in range(idx, len(self)-length):
            j = i+length
            self._t.chars[i] = self._t.chars[j]
            self._t.attribs[i] = self._t.attribs[j]
            self._t.authors[i] = self._t.authors[j]
        for i in range(len(self)-length, len(self)):
            del self._t.chars[i]
            del self._t.attribs[i]
            del self._t.authors[i]

    def set_attr(self, idx, attribs, length=1):
        """
        sets the attribute of character at given line
        """
        attr, param = self._attributes.extract(attribs)
        log.debug("Text.set_attr(%s, %s, %s): %s, %s" % (idx, attribs, length, attr, param))
        for i in range(idx, idx+length):
            if attr == "list":
                atd = dict(self._t.attribs[i])
                if "list" in atd.keys():
                    self._t.attribs[i].remove(("list", atd["list"]))
                self._t.attribs[i].append((attr, param))
            elif attr.startswith("author"):
                self._t.authors[i] = param
            elif param == "true":
                self._t.attribs[i].append((attr, param))
            elif not param:
                if (attr, param) in self._t.attribs[i]:
                    self._t.attribs[i].remove((attr, param))
                elif (attr, "true") in self._t.attribs[i]:
                    self._t.attribs[i].remove((attr, "true"))
                else:
                    log.error("Attribute (%s, %s) not removed for character %d." % (attr, param, i))
                atd = dict(self._t.attribs[i])
                if attr in atd.keys():
                    self._t.attribs[i].remove((attr, atd[attr]))

    def get_attr(self, idx):
        """
        returns the attributes of character at index idx
        """
        log.debug("Text.get_attr(%s)" % (idx,))
        return self._t.attribs[idx]

    def set_author(self, idx, author):
        """
        sets the author of current character
        :param idx:
        :param author:
        """
        log.debug("Text.set_author(%s, %s)" % (idx, author))
        self._t.authors[idx] = author

    def get_author(self, idx):
        """
        returns the color of the author of given character
        :param idx: int being the index of a character in text
        """
        log.debug("Text.get_author(%s)" % (idx,))
        if self._authors.has(self._t.authors[idx]):
            return self._authors.get_color(self._t.authors[idx])
        return self._t.authors[idx]

    def update(self, cs):
        """
        Updates current text with changeset
        :param cs: str representation of a changeset
        """
        log.debug("Text.update(%s)" % (cs,))
        self._changeset.apply_to_text(cs, self)

    def __str__(self):
        """
        Outputs current text as plain raw
        """
        pre = "--------------8<-----------------8<----------------\n"
        post = "\n-------------->8----------------->8----------------"
        return pre + "".join([c for c in self._t.chars.values()]) + post

    def __repr__(self):
        return "Text<"+"".join([c for c in self._t.chars.values()])[:15] + ">"

    def decorated(self, style=Style()):
        """
        Outputs current text with given style
        :param style: Style based object
        :returns str:
        """
        log.debug("Text.decorated()")
        state = set()
        author = None
        out = ""

        posx = 0
        posy = 0

        for i in range(0,len(self)):
            pre = ""
            aft = ""
            posx += 1
            if self._t.chars[i] == "\n":
                posy += 1
                posx = 0
                pre += style.make_cr()
            if self._cursors.get(posx, posy):
                a = self._cursors.get(posx, posy)
                a = self._authors.get_color(a)
                if not a:
                    aft += "|"
                else:
                    a, b = style.make_color(a)
                    aft += a + "|" + b
            if not author and self.get_author(i):
                author = self.get_author(i)
                a, b = style.make_color(author)
                pre += a
            elif author and self.get_author(i) != author:
                a, b = style.make_color(author)
                aft += b
                author = None
            for attr in self.get_attr(i):
                if not attr in state:
                    state.add(attr)
                    if attr[1] == "true":
                        a, b = style.make_attr(attr)
                        pre += a
                    elif attr[0] == "start":
                        continue
                    else:
                        a, b = style.make_attr(attr)
                        pre += a
                        aft += b
                else:
                    a, b = style.make_attr(attr)
                    state.remove(attr)
                    aft += b
            out += pre + self._t.chars[i] + aft
        return out

