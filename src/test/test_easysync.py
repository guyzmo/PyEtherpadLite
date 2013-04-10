#!/usr/bin/env python

from py_etherpad.Changeset import Changeset, unpack, pack, op_code_match
from py_etherpad.Text import Text
from py_etherpad.client import Cursors, Authors
from py_etherpad.Attributes import Attributes

from pprint import pprint

apool = {'nextNum': 5,
            'numToAttrib': {'1': ['bold', 'true'],
                            '0': ['author', 'a.zGeBqBBOaN4Fr8Ot'],
                            '2': ['italic', 'true'],
                            '3': ['underline', 'true'],
                            '4': ['strikethrough', 'true']}}
attributes = Attributes(pool=apool)
changeset = Changeset(attributes)

class Tests:
    def __init__(self):
        for member in dir(self):
            if member.startswith('test_'):
                print self.__class__.__name__, member.upper() + " ",
                getattr(self, member)()


class UpdateTests(Tests):
    def test(self, text, cs, expected):
        t = Text(text=text, cursors=Cursors(), attribs=attributes, authors=Authors())
        changeset.apply_to_text(cs, t)
        res = str(t)
        print res == expected

    def test_insert_before_cr(self):
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        changeset = "Z:1x>3=v*0+3$XXX"
        expected = "He who makes a beast of himselfXXX\n"+\
                   "gets rid of the pain of being a man\n"
        self.test(text, changeset, expected)

    def test_insert_before_cr_wrong(self):
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        changeset = "Z:1w<3|=v+3|1=3=x$XXX"
        expected = "He who makes a beast of himselfXXX\n"+\
                   "gets rid of the pain of being a man\n"
        self.test(text, changeset, expected)

    def test_insert_after_cr(self):
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        changeset = "Z:1x>3|1=w*0+3$XXX"
        expected = "He who makes a beast of himself\n"+\
                   "XXXgets rid of the pain of being a man\n"
        self.test(text, changeset, expected)

    def test_insert_after_start(self):
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        changeset = "Z:1x>3*0+3$XXX"
        expected = "XXXHe who makes a beast of himself\n"+\
                   "gets rid of the pain of being a man\n"
        self.test(text, changeset, expected)

    def test_insert_before_end(self):
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        changeset = "Z:1x>3|2=1w*0+3$XXX"
        expected = "He who makes a beast of himself\n"+\
                   "gets rid of the pain of being a man\nXXX"
        self.test(text, changeset, expected)


class DiffTests(Tests):
    def test(self, o, n, expected):
        res = changeset.get_from_text(o, n)
        r = pack(res)
        print r == expected, r, 'vs expected:', expected
        pprint(res, indent=4, width=20)

    def test_insert_before_cr(self):
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himselfXXX\n"+\
                "gets rid of the pain of being a man\n"
        self.test(s_old, s_new, "Z:1x>3=v*0+3$XXX")

    def test_insert_after_cr(self):
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "XXXgets rid of the pain of being a man\n"
        self.test(s_old, s_new, "Z:1x>3|1=w*0+3$XXX")

    def test_insert_after_start(self):
        s_old = "XXXHe who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.test(s_old, s_new, "Z:1x>3*0+3$XXX")

    def test_insert_before_end(self):
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\nXXX\n"
        self.test(s_old, s_new, "Z:1x>3|2=1w*0+3$XXX")


if __name__ == "__main__":
    DiffTests()
    UpdateTests()



