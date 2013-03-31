#!/usr/bin/env python
"""Module to talk to EtherpadLite API."""

import re
import json
import urllib
import urllib2

class Changeset:
# /**
#  * Unpacks a string encoded Changeset into a proper Changeset object
#  * @params cs {string} String encoded Changeset
#  * @returns {Changeset} a Changeset class
#  */
# exports.unpack = function (cs) {
#   var headerRegex = /Z:([0-9a-z]+)([><])([0-9a-z]+)|/;
#   var headerMatch = headerRegex.exec(cs);
#   if ((!headerMatch) || (!headerMatch[0])) {
#     exports.error("Not a exports: " + cs);
#   }
#   var oldLen = exports.parseNum(headerMatch[1]);
#   var changeSign = (headerMatch[2] == '>') ? 1 : -1;
#   var changeMag = exports.parseNum(headerMatch[3]);
#   var newLen = oldLen + changeSign * changeMag;
#   var opsStart = headerMatch[0].length;
#   var opsEnd = cs.indexOf("$");
#   if (opsEnd < 0) opsEnd = cs.length;
#   return {
#     oldLen: oldLen,
#     newLen: newLen,
#     ops: cs.substring(opsStart, opsEnd),
#     charBank: cs.substring(opsEnd + 1)
#   };
# };
    def unpack(self, cs):
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
        return {
                 "old_len": old_len,
                 "new_len": new_len,
                 "ops": cs[ops_start:ops_end],
                 "char_bank": cs[ops_end+1:]
                }

    def pack(self, csd):
        def numToStr(num,b=36,numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
            # http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python
            return ((num == 0) and numerals[0]) or (baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

        len_diff = csd["new_len"] - csd["old_len"]
        len_diff_str = "<" + numToStr(len_diff) if len_diff >= 0 else "<" + numToStr(-len_diff)
        a = [ 'Z:', numToStr(old_len), len_diff_str, csd["ops"], csd["char_bank"] ]
        return a.join('')

# /**
#  * Applies a Changeset to a string
#  * @params cs {string} String encoded Changeset
#  * @params str {string} String to which a Changeset should be applied
#  */
# exports.applyToText = function (cs, str) {
#   var unpacked = exports.unpack(cs);
#   exports.assert(str.length == unpacked.oldLen, "mismatched apply: ", str.length, " / ", unpacked.oldLen);
#   var csIter = exports.opIterator(unpacked.ops);
#   var bankIter = exports.stringIterator(unpacked.charBank);
#   var strIter = exports.stringIterator(str);
#   var assem = exports.stringAssembler();
#   while (csIter.hasNext()) {
#     var op = csIter.next();
#     switch (op.opcode) {
#     case '+':
#       assem.append(bankIter.take(op.chars));
#       break;
#     case '-':
#       strIter.skip(op.chars);
#       break;
#     case '=':
#       assem.append(strIter.take(op.chars));
#       break;
#     }
#   }
#   assem.append(strIter.take(strIter.remaining()));
#   return assem.toString();
# };
    def apply_to_text(self, cs, txt):
        unpacked = self.unpack(cs)
        print "LOC  LEN:", len(txt)
        print " OLD LEN:", unpacked['old_len']
        print " NEW LEN:", unpacked['new_len']
        print "     OPS:", unpacked["ops"]
        print "    BANK:", unpacked["char_bank"]
        assert len(txt)+1 == unpacked['old_len']
        bank = unpacked['char_bank']
        bank_idx, txt_idx = (0, 0)
        out = ""
        for op in self.op_iterator(unpacked['ops']):
            if (op["op_code"] == "+"):
                out += bank[bank_idx:bank_idx+op["chars"]]
                bank_idx += op["chars"]
            elif (op["op_code"] == "-"):
                txt_idx += op["chars"]
            elif (op["op_code"] == "="):
                out += txt[txt_idx:txt_idx+op["chars"]]
                txt_idx += op["chars"]
        return out + txt[txt_idx:]


# /**
#  * this function creates an iterator which decodes string changeset operations
#  * @param opsStr {string} String encoding of the change operations to be performed
#  * @param optStartIndex {int} from where in the string should the iterator start
#  * @return {Op} type object iterator
#  */
# exports.opIterator = function (opsStr, optStartIndex) {
#   //print(opsStr);
#   var regex = /((?:\*[0-9a-z]+)*)(?:\|([0-9a-z]+))?([-+=])([0-9a-z]+)|\?|/g;
#   var startIndex = (optStartIndex || 0);
#   var curIndex = startIndex;
#   var prevIndex = curIndex;

#   function nextRegexMatch() {
#     prevIndex = curIndex;
#     var result;
#     regex.lastIndex = curIndex;
#     result = regex.exec(opsStr);
#     curIndex = regex.lastIndex;
#     if (result[0] == '?') {
#       exports.error("Hit error opcode in op stream");
#     }

#     return result;
#   }
#   var regexResult = nextRegexMatch();
#   var obj = exports.newOp();

#   function next(optObj) {
#     var op = (optObj || obj);
#     if (regexResult[0]) {
#       op.attribs = regexResult[1];
#       op.lines = exports.parseNum(regexResult[2] || 0);
#       op.opcode = regexResult[3];
#       op.chars = exports.parseNum(regexResult[4]);
#       regexResult = nextRegexMatch();
#     } else {
#       exports.clearOp(op);
#     }
#     return op;
#   }

#   function hasNext() {
#     return !!(regexResult[0]);
#   }

#   function lastIndex() {
#     return prevIndex;
#   }
#   return {
#     next: next,
#     hasNext: hasNext,
#     lastIndex: lastIndex
#   };
# };
    def op_iterator(self, opstr, op_start_idx=0):
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
            yield op
        return

