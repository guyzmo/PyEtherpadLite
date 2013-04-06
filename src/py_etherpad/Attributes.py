#!/usr/bin/env python

class Attributes:
    def __init__(self, conn=None, pad=None,
                        pool=dict(numToAttrib={}, attribToNum={})):
        self._conn = conn
        self._pad = pad
        self._pool = pool

        self._attrinorder = list()
        self._attrlists = dict()
        self._authors = dict()

        self._attribs = dict()

    def get(self, attr):
        attr = str(int(attr, 36))
        if attr in self._pool['numToAttrib'].keys():
            attr, param = self._pool['numToAttrib'][attr]
        elif self._pool and self._pad:
            self._pool = self._conn.getAttributePool(self._pad)['pool']
            return self.get(attr)
        elif not attr in self._pool['numToAttrib'].keys():
                raise Exception("Attribute not found:", attr)
        else:
            attr, param = self._pool['numToAttrib'][attr]
        if param != "false":
            return attr, param
        return attr, False

    def update(self, attr, text):
        return "[" + attr + "]{" + text + "}"

    def reset_list(self, idx):
        if idx in self._attrlists.keys():
            params = tuple((idx,) + self._attrlists[idx])
            self._attrinorder.remove(params)
            del self._attrlists[idx]
            return True
        return False

    def apply(self, text):
        char_dict = {}
        for i in range(0, len(text)):
            char_dict[i] = dict(char=text[i], attr=[], param=[])

        for idx, length, attr, param in self._attrinorder:
            for i in range(idx, idx+length):
                if attr == "list":
                    if "list" in char_dict[i]["attr"]:
                         l = char_dict[i]["attr"].index("list")
                         char_dict[i]["attr"].remove("list")
                         del char_dict[i]["param"][l]
                #elif attr == "start":
                #    continue
                elif attr.startswith("insertorder"):
                    continue
                elif attr.startswith("lmkr"):
                    continue

                char_dict[i]['attr'].append(attr)
                char_dict[i]['param'].append(param)

        out = ""
        state = set()
        for i in range(0, len(text)):
            before = ""
            after = ""
            c = char_dict[i]["char"]
            if i in self._authors.keys():
                before += "[" + self._authors[i] + "]"
            for a, p in zip(char_dict[i]["attr"], char_dict[i]["param"]):
                if not a in state:
                    before += "[" + a + "]{"
                    state.add(a)
                if not a in char_dict[i+1]["attr"]:
                    after += "}"
                    state.remove(a)

            out += before + char_dict[i]["char"] + after

        return out

    def store(self, op, idx):
        attr = op["attribs"]
        idx += 1
        for attr in attr.split("*")[1:]:
            attr, param = self.get(attr)
            if attr == "list":
                self._attrlists[idx] = (op["chars"], attr, param)
                self._attrinorder.append((idx, op["chars"], attr, param))
            elif attr == "author":
                self._authors[idx] = param
            elif param == "true":
                self._attrinorder.append((idx, op["chars"], attr, param))
            elif not param:
                self._attrinorder.remove((idx, op["chars"], attr, "true"))
            # else:
            #     print "XX", idx, op["chars"], attr, param

    def extract(self, attr):
        for attr in attr.split("*")[1:]:
            return self.get(attr)

