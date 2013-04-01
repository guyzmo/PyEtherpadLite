#!/usr/bin/env python

from Attributes import Attributes
from Changeset import Changeset

class Text:
    def __init__(self, conn, pad, text=None):
        self.conn = conn
        self.pad = pad
        self._attributes = Attributes(conn, pad)
        self._changeset = Changeset(self._attributes)
        if text:
            for i in range(0, len(text)):
                self._chars[i] = text[i]
                self._attribs[i] = list()
                self._authors[i] = None
        else:
            self._chars = {}
            self._attribs = dict()
            self._authors = dict()

    def length(self):
        return len(self._chars.keys())

    def __len__(self):
        return self.length()

    def insert_at(self, idx, substr, attr=None):
        ls = len(substr)
        lt = len(self)
        chars = dict()
        attribs = dict()
        authors = dict()

        for i in range(0, idx):
            chars[i] = self._chars[i]
            attribs[i] = self._attribs[i]
            authors[i] = self._authors[i]

        for i, c in zip(range(idx, idx+ls), substr):
            chars[i] = c
            attribs[i] = list()
            authors[i] = None

        for i in range(idx+ls, lt+ls):
            chars[i] = self._chars[i-ls]
            attribs[i] = self._attribs[i-ls]
            authors[i] = self._authors[i-ls]

        self._chars = chars
        self._attribs = attribs
        self._authors = authors

    def remove(self, idx, length, attr=None):
        for i in range(idx, len(self)-length):
            j = i+length
            self._chars[i] = self._chars[j]
            self._attribs[i] = self._attribs[j]
            self._authors[i] = self._authors[j]
        for i in range(len(self)-length, len(self)):
            del self._chars[i]
            del self._attribs[i]
            del self._authors[i]

    def set_attr(self, idx, attribs, length=1):
        attr, param = self._attributes.extract(attribs)
        for i in range(idx, idx+length):
            if attr == "list":
                atd = dict(self._attribs[i])
                if "list" in atd.keys():
                    self._attribs[i].remove(("list", atd["list"]))
                self._attribs[i].append((attr, param))
            elif attr.startswith("author"):
                self._authors[i] = param
            elif param == "true":
                self._attribs[i].append((attr, param))
            elif not param:
                self._attribs[i].remove((attr, param))
                atd = dict(self._attribs[i])
                if attr in atd.keys():
                    self._attribs[i].remove((attr, atd[attr]))

    def get_attr(self, idx):
        return self._attribs[idx]

    def set_author(self, idx, author):
        self._authors[idx] = author

    def get_author(self, idx):
        return self._authors[idx]

    def update(self, cs):
        self._changeset.apply_to_text(cs, self)

    def __str__(self):
        pre = "--------------8<-----------------8<----------------\n"
        post = "\n-------------->8----------------->8----------------"
        return pre + "".join([c for c in self._chars.values()]) + post

    def decorated(self):
        state = set()
        author = None
        out = ""

        for i in range(0,len(self)):
            pre = ""
            aft = ""
            if self.get_author(i) != author:
                author = self.get_author(idx)
                pre += "["+author+"]"
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
            out += pre + self._chars[i] + aft
        return out

