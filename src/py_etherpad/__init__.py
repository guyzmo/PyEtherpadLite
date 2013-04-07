#!/usr/bin/env python
"""Module to talk to EtherpadLite API."""

from Text import Text
from Cursors import Cursors
from Authors import Authors
from Changeset import Changeset
from Attributes import Attributes

from EtherpadLiteClient import APIClient
from SocketIOClient import EtherpadService

from client import run as cli

