#!/usr/bin/env python
# -+- encoding: utf-8 -+-

import logging
log = logging.getLogger('py_etherpad.Text')

import sys
import inspect

class Style(object):
    def make_color(self, color):
        raise NotImplementedError
    def make_attr(self, attr):
        raise NotImplementedError
    def make_cr(self):
        raise NotImplementedError


class Default(Style):
    def make_color(self, color):
        return ("["+color+"]{", "}")

    def make_attr(self, attr):
        if attr[1] == "true":
            return ("["+attr[0]+"]{", "}")
        return ("["+attr[0]+":"+attr[1]+"]{", "}")

    def make_cr(self):
        return ""



class Raw(Style):
    def make_color(self, color):
        return ("", "")
    def make_attr(self, attr):
        return ("", "")
    def make_cr(self):
        return ""


class Markdown(Style):
    def make_color(self, color):
        return ("<span style='color: "+color+"'>", "</span>")
    def make_attr(self, attr):
        if attr[1] == "true":
            attr = attr[0]
        else:
            attr = attr[0]+":"+attr[1]
        if attr == "bold":
            return ("**", "**")
        elif attr == "italic":
            return ("*", "*")
        elif attr == "underline":
            return ("<span style='text-decoration: underline'>", "</span>")
        elif attr == "strikethrough":
            return ("<span style='text-decoration: line-through'>", "</span>")
        elif attr == "list":
            n = int(param[-1])
            if param.startswith("number"):
                return ((" "*n)+".1", "")
            return ((" "*n)+"*", "")
        else:
            return ("<!-- "+attr+" -->", "<!-- /"+attr+" -->")
    def make_cr(self):
        return ""


class Html(Style):
    def make_color(self, color):
        return ("<span style='color: "+color+"'>", "</span>")

    def make_attr(self, attr):
        if attr[1] == "true":
            attr = attr[0]
        else:
            attr = attr[0]+":"+attr[1]
        if attr == "bold":
            return ("<span style='font-style: bold'>", "</span>")
        elif attr == "italic":
            return ("<span style='font-style: italic'>", "</span>")
        elif attr == "underline":
            return ("<span style='text-decoration: underline'>", "</span>")
        elif attr == "strikethrough":
            return ("<span style='text-decoration: line-through'>", "</span>")
        elif attr == "list":
            if param.startswith("number"):
                return ("<ol><li>", "</li></ol>")
            return ("<ul><li>", "</li></ul>")
        else:
            return ("<!-- "+attr+" -->", "<!-- /"+attr+" -->")

    def make_cr(self):
        return "<br />"


STYLES = dict(inspect.getmembers(sys.modules[__name__],
              lambda c: inspect.isclass(c) and c.__name__ != "Style"))

