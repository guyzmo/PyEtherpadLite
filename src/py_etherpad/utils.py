#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger('py_etherpad.client')

import string
import random

def id_generator(size=6, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for x in range(size))

def num_to_str(num, b=36, numerals=string.digits + string.ascii_lowercase):
    """
    Converts integer num into a string representation on base b
    @param b {int} base to use
    @param numerals {string} characters used for string representation
    @returns {string} string representation of num in base b
    """
    # http://stackoverflow.com/questions/2267362/convert-integer-to-a-string-in-a-given-numeric-base-in-python
    return ((num == 0) and numerals[0]) \
            or (num_to_str(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b])

