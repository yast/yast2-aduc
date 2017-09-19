#!/usr/bin/env python

import ldap, ldap.modlist, ldap.sasl
import os.path, sys
from samba.net import Net
from samba.dcerpc import nbt
import uuid
import re

