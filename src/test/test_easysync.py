#!/usr/bin/env python

import logging
log = logging.getLogger('Test_easysync')

#testing framework
import unittest

from nose.tools import istest
from nose.tools import assert_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises
from nose.tools import raises

from py_etherpad.Changeset import Changeset, unpack, pack, op_code_match
from py_etherpad.Text import Text
from py_etherpad.client import Cursors, Authors
from py_etherpad.Attributes import Attributes

from pprint import pprint

class EasySyncTests(unittest.TestCase):
    def setUp(self):
        self.apool = {'nextNum': 5,
                    'numToAttrib': {'1': ['bold', 'true'],
                                    '0': ['author', 'a.zGeBqBBOaN4Fr8Ot'],
                                    '2': ['italic', 'true'],
                                    '3': ['underline', 'true'],
                                    '4': ['strikethrough', 'true']}}
        self.authors = Authors()
        self.authors.add('a.zGeBqBBOaN4Fr8Ot', "John Doe", "#124269")
        self.attributes = Attributes(pool=self.apool)
        self.changeset = Changeset(self.attributes)

    def tearDown(self):
        self.apool = None
        self.attributes = None
        self.changeset = None


class UpdateTests(EasySyncTests):
    """Changeset received"""
    def apply(self, text, cs, expt):
        t = Text(text=text,
                 cursors=Cursors(),
                 attribs=self.attributes,
                 authors=self.authors)
        self.changeset.apply_to_text(cs, t)
        res = str(t)
        assert_equal(res, expt)

    ###

    def test_insert_before_cr(self):
        """Update: Inserts some text before <CR>"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3=v*0+3$XXX"
        expt = "He who makes a beast of himselfXXX\n"+\
              "gets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_before_cr_wrong(self):
        """Update: Inserts some text before <CR>. NOT!"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1w<3|=v+3|1=3=x$XXX"
        expt = "He who makes a beast of himselfXXX\n"+\
                   "gets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_after_cr(self):
        """Update: Inserts some text after <CR>"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3|1=w*0+3$XXX"
        expt = "He who makes a beast of himself\n"+\
                   "XXXgets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_after_start(self):
        """Update: Inserts some text at begining"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3*0+3$XXX"
        expt = "XXXHe who makes a beast of himself\n"+\
                   "gets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_before_end(self):
        """Update: Inserts some text at the end"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3|2=1w*0+3$XXX"
        expt = "He who makes a beast of himself\n"+\
                   "gets rid of the pain of being a man\nXXX"
        self.apply(text, cset, expt)


class DiffTests(EasySyncTests):
    """Changeset to be sent"""
    def apply(self, o, n, expected):
        self.authors.set_user_id("0", "#424242")
        t = Text(text=o,
                 cursors=Cursors(),
                 attribs=self.attributes,
                 authors=self.authors)
        for i in range(0, len(t)):
            t._t.authors[i] = "0"
        res = self.changeset.get_from_text(t, n)
        r = pack(res)
        print "EXPECTED"
        pprint(unpack(expected), indent=4, width=20)
        print "GOT"
        pprint(res, indent=4, width=20)
        assert_equal(r, expected)

    ###

    def test_insert_after_start(self):
        """Diff: Inserts some text at begining"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "XXXHe who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1w>3*0+3$XXX")

    def test_insert_before_end(self):
        """Diff: Inserts some text at the end"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\nXXX"
        self.apply(s_old, s_new, "Z:1w>3|2=1w*0+3$XXX")

    def test_insert_before_cr(self):
        """Diff: Inserts some text before <CR>"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himselfXXX\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1w>3=v*0+3$XXX")

    def test_insert_after_cr(self):
        """Diff: Inserts some text after <CR>"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "XXXgets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1w>3|1=w*0+3$XXX")


    def test_delete_after_start(self):
        """Diff: Deletes some text after begining"""
        s_old = "XXXHe who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1z<3-3$")

    def test_delete_before_end(self):
        """Diff: Deletes some text before end"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a manXXX\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1z<3|1=w=z-3$")

    def test_delete_before_cr(self):
        """Diff: Deletes some text before <CR>"""
        s_old = "He who makes a beast of himselfXXX\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1z<3=v-3$")

    def test_delete_after_cr(self):
        """Diff: Deletes some text after <CR>"""
        s_old = "He who makes a beast of himself\n"+\
                "XXXgets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1z<3|1=w-3$")

