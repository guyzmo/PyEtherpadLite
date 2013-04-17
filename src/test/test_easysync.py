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
        self.attributes = Attributes(pool=self.apool)
        self.changeset = Changeset(self.attributes)

    def tearDown(self):
        self.apool = None
        self.attributes = None
        self.changeset = None


class UpdateTests(EasySyncTests):
    """Changeset generation"""
    def apply(self, text, cs, expt):
        t = Text(text=text,
                 cursors=Cursors(),
                 attribs=self.attributes,
                 authors=Authors())
        self.changeset.apply_to_text(cs, t)
        res = str(t)
        assert_equal(res, expt)

    ###

    def test_insert_before_cr(self):
        """Inserts some text before <CR>"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3=v*0+3$XXX"
        expt = "He who makes a beast of himselfXXX\n"+\
              "gets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_before_cr_wrong(self):
        """Inserts some text before <CR>. NOT!"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1w<3|=v+3|1=3=x$XXX"
        expt = "He who makes a beast of himselfXXX\n"+\
                   "gets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_after_cr(self):
        """Inserts some text after <CR>"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3|1=w*0+3$XXX"
        expt = "He who makes a beast of himself\n"+\
                   "XXXgets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_after_start(self):
        """Inserts some text at begining"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3*0+3$XXX"
        expt = "XXXHe who makes a beast of himself\n"+\
                   "gets rid of the pain of being a man\n"
        self.apply(text, cset, expt)

    def test_insert_before_end(self):
        """Inserts some text at the end"""
        text = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        cset = "Z:1x>3|2=1w*0+3$XXX"
        expt = "He who makes a beast of himself\n"+\
                   "gets rid of the pain of being a man\nXXX"
        self.apply(text, cset, expt)


class DiffTests(EasySyncTests):
    """Changeset interpretation"""
    def apply(self, o, n, expected):
        res = self.changeset.get_from_text(o, n)
        r = pack(res)
        assert_equal(r, expected) #, r, 'vs expected:', expected
        #pprint(res, indent=4, width=20)

    ###

    def test_insert_before_cr(self):
        """Inserts some text before <CR>"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himselfXXX\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1x>3=v*0+3$XXX")

    def test_insert_after_cr(self):
        """Inserts some text after <CR>"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "XXXgets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1x>3|1=w*0+3$XXX")

    def test_insert_after_start(self):
        """Inserts some text at begining"""
        s_old = "XXXHe who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        self.apply(s_old, s_new, "Z:1x>3*0+3$XXX")

    def test_insert_before_end(self):
        """Inserts some text at the end"""
        s_old = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\n"
        s_new = "He who makes a beast of himself\n"+\
                "gets rid of the pain of being a man\nXXX\n"
        self.apply(s_old, s_new, "Z:1x>3|2=1w*0+3$XXX")


