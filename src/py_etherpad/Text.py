#!/usr/bin/env python
# -+- encoding: utf-8 -+-

from Attributes import Attributes
from Changeset import Changeset

class TextRepr:
    def __init__(self):
        self.chars = {}
        self.attribs = dict()
        self.authors = dict()


class Text:
    def __init__(self, attribs, authors, cursors, text=None):
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
        attr, param = self._attributes.extract(attribs)
        for i in range(idx, idx+length):
            if attr == "list":
                atd = dict(self._t.attribs[i])
                if "list" in atd.keys():
                    self._t.attribs[i].remove(("list", atd["list"]))
                self._t.attribs[i].append((attr, param))
            elif attr.startswith("author"):
                print i, attr, param
                self._t.authors[i] = param
            elif param == "true":
                self._t.attribs[i].append((attr, param))
            elif not param:
                self._t.attribs[i].remove((attr, param))
                atd = dict(self._t.attribs[i])
                if attr in atd.keys():
                    self._t.attribs[i].remove((attr, atd[attr]))

    def get_attr(self, idx):
        return self._t.attribs[idx]

    def set_author(self, idx, author):
        self._t.authors[idx] = author

    def get_author(self, idx):
        if  self._authors.has(self._t.authors[idx]):
            return self._authors.get_color(self._t.authors[idx])
        return self._t.authors[idx]

    def update(self, cs):
        self._changeset.apply_to_text(cs, self)

    def __str__(self):
        pre = "--------------8<-----------------8<----------------\n"
        post = "\n-------------->8----------------->8----------------"
        return pre + "".join([c for c in self._t.chars.values()]) + post

    def decorated(self):
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
            if self._cursors.get(posx, posy):
                a = self._cursors.get(posx, posy)
                a = self._authors.get_color(a)
                if not a:
                    aft += "|"
                else:
                    aft += "["+str(a)+"]{|}"
            if not author and self.get_author(i):
                author = self.get_author(i)
                pre += "["+str(author)+"]{"
            elif author and self.get_author(i) != author:
                aft += "}"
                author = None
            for attr in self.get_attr(i):
                if not attr in state:
                    state.add(attr)
                    if attr[1] == "true":
                        pre += "["+attr[0]+"]{"
                    elif attr[0] == "start":
                        continue
                    else:
                        pre += "["+attr[0]+":"+attr[1]+"]{"
                        aft += "}"
                else:
                    state.remove(attr)
                    aft += "}"
            out += pre + self._t.chars[i] + aft
        return out

