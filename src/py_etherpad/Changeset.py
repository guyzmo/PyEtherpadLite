#!/usr/bin/env python
"""Reverse engineered EtherpadLite Changeset API."""

import logging
log = logging.getLogger('py_etherpad.Changeset')

import re
from difflib import SequenceMatcher

from utils import num_to_str

def op_code_match(opcode, a0, a1, b0, b1, changeset=None, sm=None, text=None):
    optr = ''
    chrb = ''
    print "!@#$", opcode
    if opcode == 'equal':
        print "EQUAL"
        # if substr contains a newlines
        if '\n' in sm.a[a0:a1]:
            # "|L=N" : Keep N characters from the source text,
            #          containing L newlines. The last character kept
            #          MUST be a newline, and the final newline of
            #          the document is allowed.
            nls = [a0+m.start()+1 for m in re.finditer('\n', sm.b[a0:a1])]
            if sm.a[a0:a1][-1] == '\n':
                optr += '|' + num_to_str(len(nls), 36)
                optr += '=' + num_to_str(a1-a0, 36)
            # if substr does not end with a newline
            else:
                nls = [a0] + nls + [a1]
                print nls
                changeset['ops'] += optr
                for c0, c1 in zip(nls, nls[1:]):
                    #print "PYF", repr(sm.a[c0:c1])
                    op_code_match('equal', c0, c1, c0, c1, changeset, sm, text)
        else:
            optr += '=' + num_to_str(a1-a0, 36)
    elif opcode == 'insert':
        # "|L+N" : Insert N characters from the source text,
        #          containing L newlines. The last character
        #          inserted MUST be a newline, but not the
        #          (new) document's final newline.
        if text._authors.get_user_id():
            optr += '*' + text._authors.get_user_id()
        optr += '+' + num_to_str(b1-b0, 36)
        chrb += sm.b[b0:b1]
    elif opcode == 'delete':
        # "|L-N" : Delete N characters from the source text,
        #          containing L newlines. The last character
        #          inserted MUST be a newline, but not the (old)
        #          document's final newline.
        optr += '-' + num_to_str(a1-a0, 36)
    elif opcode == 'replace':
        print "REPLACE"
    changeset['ops'] += optr
    changeset['char_bank'] += chrb

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
    len_diff_str = ">" + num_to_str(len_diff) if len_diff >= 0 else "<" + num_to_str(-len_diff)
    cs = [ 'Z:', num_to_str(csd["old_len"]), len_diff_str, csd["ops"], "$", csd["char_bank"] ]
    cs = ''.join(cs)
    log.debug("pack: returns %s" % (cs,))
    return cs


class Changeset:
    def __init__(self, attr):
        self._attribs = attr

    def get_from_text(self, old, new):
        """
        Gets the differences between `old` text and `new` text and returns a changeset
        :param old: old Text object
        :param new: new text string
        """
        olds = str(old)
        sm = SequenceMatcher(None, olds, new)
        csd = dict(old_len=len(olds)+1,
                    new_len=len(new)+1,
                    ops="",
                    char_bank="")
        opcodes = [opcode_tup for opcode_tup in sm.get_opcodes()]
        last_op = 0
        for i in range(0, len(opcodes)):
            if opcodes[i][0] != "equal":
                last_op = i
            print opcodes[i][0], last_op, i
        for opcode_tup in opcodes[:last_op+1]:
            op_code_match(*opcode_tup, changeset=csd, sm=sm, text=old)
        return csd

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


