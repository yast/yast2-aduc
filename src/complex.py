#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
import ldap, ldap.modlist, ldap.sasl
import os.path, sys
from samba.net import Net
from samba.dcerpc import nbt
import uuid
import re
from subprocess import Popen, PIPE
from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT
from ldap.modlist import addModlist as addlist
from ldap.modlist import modifyModlist as modlist
import traceback
from yast import ycpbuiltins

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

class LdapException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        if len(self.args) > 0:
            self.msg = self.args[0]
        else:
            self.msg = None
        if len(self.args) > 1:
            self.info = self.args[1]
        else:
            self.info = None

def _ldap_exc_msg(e):
    if len(e.args) > 0 and \
      type(e.args[-1]) is dict and \
      'desc' in e.args[-1]:
        return e.args[-1]['desc']
    else:
        return str(e)

def _ldap_exc_info(e):
    if len(e.args) > 0 and \
      type(e.args[-1]) is dict and \
      'info' in e.args[-1]:
        return e.args[-1]['info']
    else:
        return ''

def ldap_search(l, *args):
    try:
        return l.search_s(*args)
    except Exception as e:
        ycpbuiltins.y2error(traceback.format_exc())
        ycpbuiltins.y2error('ldap.search_s: %s\n' % _ldap_exc_msg(e))

def ldap_add(l, *args):
    try:
        return l.add_s(*args)
    except Exception as e:
        raise LdapException(_ldap_exc_msg(e), _ldap_exc_info(e))

def ldap_modify(l, *args):
    try:
        return l.modify(*args)
    except Exception as e:
        ycpbuiltins.y2error(traceback.format_exc())
        ycpbuiltins.y2error('ldap.modify: %s\n' % _ldap_exc_msg(e))

def ldap_delete(l, *args):
    try:
        return l.delete_s(*args)
    except Exception as e:
        ycpbuiltins.y2error(traceback.format_exc())
        ycpbuiltins.y2error('ldap.delete_s: %s\n' % _ldap_exc_msg(e))

def stringify_ldap(data):
    if type(data) == dict:
        for key, value in data.items():
            data[key] = stringify_ldap(value)
        return data
    elif type(data) == list:
        new_list = []
        for item in data:
            new_list.append(stringify_ldap(item))
        return new_list
    elif type(data) == tuple:
        new_tuple = []
        for item in data:
            new_tuple.append(stringify_ldap(item))
        return tuple(new_tuple)
    elif PY2 and type(data) == unicode:
        return str(data)
    elif PY3 and type(data) == bytes:
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data
    else:
        return data

class Connection:
    def __init__(self, lp, creds):
        self.lp = lp
        self.creds = creds
        self.realm = lp.get('realm')
        net = Net(creds=creds, lp=lp)
        cldap_ret = net.finddc(domain=self.realm, flags=(nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS))
        self.l = ldap.initialize('ldap://%s' % cldap_ret.pdc_dns_name)
        if self.__kinit_for_gssapi():
            auth_tokens = ldap.sasl.gssapi('')
            self.l.sasl_interactive_bind_s('', auth_tokens)
        else:
            self.l.bind_s('%s@%s' % (creds.get_username(), self.realm) if not self.realm in creds.get_username() else creds.get_username(), creds.get_password())

    def __kinit_for_gssapi(self):
        p = Popen(['kinit', '%s@%s' % (self.creds.get_username(), self.realm) if not self.realm in self.creds.get_username() else self.creds.get_username()], stdin=PIPE, stdout=PIPE)
        p.stdin.write('%s\n' % self.creds.get_password())
        return p.wait() == 0

    def realm_to_dn(self, realm):
        return ','.join(['DC=%s' % part for part in realm.lower().split('.')])

    def __well_known_container(self, container):
        if container == 'system':
            wkguiduc = 'AB1D30F3768811D1ADED00C04FD8D5CD'
        elif container == 'computers':
            wkguiduc = 'AA312825768811D1ADED00C04FD8D5CD'
        elif container == 'dcs':
            wkguiduc = 'A361B2FFFFD211D1AA4B00C04FD7D83A'
        elif container == 'users':
            wkguiduc = 'A9D1CA15768811D1ADED00C04FD8D5CD'
        result = ldap_search(self.l, '<WKGUID=%s,%s>' % (wkguiduc, self.realm_to_dn(self.realm)), ldap.SCOPE_SUBTREE, '(objectClass=container)', stringify_ldap(['distinguishedName']))
        if result and len(result) > 0 and len(result[0]) > 1 and 'distinguishedName' in result[0][1] and len(result[0][1]['distinguishedName']) > 0:
            return result[0][1]['distinguishedName'][-1]

    def user_group_list(self):
        return ldap_search(self.l, self.__well_known_container('users'), ldap.SCOPE_SUBTREE, '(objectCategory=person)', []) + ldap_search(self.l, self.__well_known_container('users'), ldap.SCOPE_SUBTREE, '(objectCategory=group)', [])

    def computer_list(self):
        return ldap_search(self.l, self.__well_known_container('computers'), ldap.SCOPE_SUBTREE, '(objectCategory=computer)', [])

    def update(self, dn, orig_map, modattr, addattr):
        try:
            if len(modattr):
                oldattr = {}
                for key in modattr:
                    oldattr[key] = orig_map.get(key, [])
                ldap_modify(self.l, dn, stringify_ldap(modlist(oldattr, modattr)))
            if len(addattr):
                try:
                    ldap_add(self.l, dn, addlist(stringify_ldap(addattr)))
                except LdapException as e:
                    ycpbuiltins.y2error(traceback.format_exc())
                    ycpbuiltins.y2error('ldap.add_s: %s\n' % e.info if e.info else e.msg)
        except Exception as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error(str(e))
            return False
        return True

