#!/usr/bin/env python
"""Reverse engineered EtherpadLite Changeset API."""

import logging
log = logging.getLogger('py_etherpad.Changeset')

import re

from utils import num_to_str

def unpack(cs):
    """
    Unpacks a string encoded Changeset into a proper Changeset dict
    @param cs {string} String encoded Changeset
    @returns {dict} a Changeset class
    """
    log.debug("unpack: %s" % cs)
    header_regex = r"Z:([0-9a-z]+)([><])([0-9a-z]+)|"
    header_match = re.match(header_regex, cs)
    headers = header_match.groups()

    if header_match is None or len(headers) == 0:
        return dict()

    old_len     = int(headers[0], 36)
    change_sign = 1 if headers[1] == ">" else -1
    change_mag  = int(headers[2], 36)
    new_len     = old_len + change_sign * change_mag
    ops_start   = len(headers[0])+len(headers[1])+len(headers[2])
    ops_end     = cs.find("$")
    if ops_end < 0:
        ops_end = len(cs)
    csd = {
            "old_len": old_len,
            "new_len": new_len,
            "ops": cs[ops_start:ops_end],
            "char_bank": cs[ops_end+1:]
          }
    log.debug("unpack: returns %s" % csd)
    return csd

def pack(csd):
    """
    Packs a Changeset dict into a string encoded Changeset
    @param cs {dict} a Changeset dict
    @returns {string} String encoded Changeset
    """
    log.debug("pack: %s" % (csd,))
    len_diff = csd["new_len"] - csd["old_len"]
    len_diff_str = "<" + num_to_str(len_diff) if len_diff >= 0 else "<" + num_to_str(-len_diff)
    cs = [ 'Z:', num_to_str(csd["old_len"]), len_diff_str, "|", csd["ops"], "$", csd["char_bank"] ]
    cs = ''.join(cs)
    log.debug("pack: returns %s" % (cs,))
    return cs


class Changeset:
    def __init__(self, attr):
        self._attribs = attr

    def apply_to_text(self, cs, txt):
        """
        Applies a Changeset to a string
        @params cs {string} String encoded Changeset
        @params str {string} String to which a Changeset should be applied
        """
        log.debug("apply_to_text: %s, %s" % (cs, repr(txt)))
        unpacked = unpack(cs)
        assert len(txt)+1 in (unpacked['old_len'], unpacked['old_len']+1)
        bank = unpacked['char_bank']
        bank_idx, txt_idx = (0, 0)
        for op in self.op_iterator(unpacked['ops']):
            if op["op_code"] == "+":
                txt.insert_at(txt_idx, bank[bank_idx:bank_idx+op["chars"]], op['attribs'])
                if not len(op['attribs']) is 0:
                    txt.set_attr(txt_idx, op['attribs'], op['chars'])
                bank_idx += op["chars"]
                txt_idx += op["chars"]
            elif op["op_code"] == "-":
                txt.remove(txt_idx, op["chars"])
            elif op["op_code"] == "=":
                if not len(op['attribs']) is 0:
                    txt.set_attr(txt_idx, op['attribs'], op['chars'])
                txt_idx += op["chars"]

    def op_iterator(self, opstr, op_start_idx=0):
        """
        this function creates an iterator which decodes string changeset operations
        @param opsStr {string} String encoding of the change operations to be performed
        @param optStartIndex {int} from where in the string should the iterator start
        @return {Op} type object iterator
        """
        log.debug("op_iterator: %s, %s" % (opstr, op_start_idx))
        regex = r"((?:\*[0-9a-z]+)*)(?:\|([0-9a-z]+))?([-+=\<\>])([0-9a-z]+)|\?|"
        start_idx = op_start_idx
        curr_idx  = start_idx
        prev_idx  = curr_idx
        last_idx  = 0
        match     = None
        has_next  = True
        regex_res = []

        prev_idx = curr_idx
        for match in re.finditer(regex, opstr):
            if match.start() != match.end():
                regex_res = match.groups()
                if regex_res[0] == '?':
                    print "Hit error opcode in op stream"
                    continue
                op = dict(attribs=regex_res[0],
                            lines=int(regex_res[1], 36) if not regex_res[1] is None else 0,
                          op_code=regex_res[2],
                            chars=int(regex_res[3], 36))
            else:
                op = dict(attribs='', lines=0, op_code='', chars=0)
            log.debug("op_iterator: next op: %s" % op)
            yield op
        return

if __name__ == "__main__":
    # tests
    from Text import Text
    from client import Cursors, Authors
    from Attributes import Attributes
    apool = {'nextNum': 5,
             'numToAttrib': {'1': ['bold', 'true'],
                             '0': ['author', 'a.zGeBqBBOaN4Fr8Ot'],
                             '2': ['italic', 'true'],
                             '3': ['underline', 'true'],
                             '4': ['strikethrough', 'true']}}
    attributes = Attributes(pool=apool)
    changeset = Changeset(attributes)

    attribs = '+j*0+3|2+2*1+4+1*2+3+1*3+4+1*4+2|4+5a'
    text = "Welcome to Etherpad...\n\nThis pad text is synchronized as you type, so that everyone viewing this page sees the same text. This allows you to collaborate seamlessly on documents!\n\nGet involved with Etherpad at http://etherpad.org"

    csd   = dict(old_len=len(text),
                 new_len=len(text),
                 ops=attribs,
                 char_bank="")

    t = Text(text=text, cursors=Cursors(), attribs=attributes, authors=Authors())

    print csd

    cs = pack(csd)

    csd2 = unpack(cs)

    print csd2

    changeset.apply_to_text(cs, t)

    print t


