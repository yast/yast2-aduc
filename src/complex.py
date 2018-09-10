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

import six

def strcmp(first, second):
    if six.PY3:
        if isinstance(first, six.string_types):
            first = six.binary_type(first, 'utf8')
        if isinstance(second, six.string_types):
            second = six.binary_type(second, 'utf8')
    return first == second

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

def ldap_search_s(l, *args):
    try:
        return l.search_s(*args)
    except Exception as e:
        ycpbuiltins.y2error(traceback.format_exc())
        ycpbuiltins.y2error('ldap.search_s: %s\n' % _ldap_exc_msg(e))

def ldap_search(l, *args):
    result = []
    try:
        res_id = l.search(*args)
        while 1:
            t, d = l.result(res_id, 0)
            if d == []:
                break
            else:
                if t == ldap.RES_SEARCH_ENTRY:
                    result.append(d[0])
    except ldap.LDAPError:
        pass
    except Exception as e:
        ycpbuiltins.y2error(traceback.format_exc())
        ycpbuiltins.y2error('ldap.search: %s\n' % _ldap_exc_msg(e))
    return result

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
    elif six.PY2 and type(data) == unicode:
        return str(data)
    elif six.PY3 and isinstance(data, six.string_types):
        return data.encode('utf-8') # python3-ldap requires a bytes type
    else:
        return data

class Connection:
    def __init__(self, lp, creds):
        self.lp = lp
        self.creds = creds
        self.realm = lp.get('realm')
        self.net = Net(creds=creds, lp=lp)
        cldap_ret = self.net.finddc(domain=self.realm, flags=(nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS))
        self.l = ldap.initialize('ldap://%s' % cldap_ret.pdc_dns_name)
        if self.__kinit_for_gssapi():
            auth_tokens = ldap.sasl.gssapi('')
            self.l.sasl_interactive_bind_s('', auth_tokens)
        else:
            self.l.bind_s('%s@%s' % (creds.get_username(), self.realm) if not self.realm in creds.get_username() else creds.get_username(), creds.get_password())

    def __kinit_for_gssapi(self):
        p = Popen(['kinit', '%s@%s' % (self.creds.get_username(), self.realm) if not self.realm in self.creds.get_username() else self.creds.get_username()], stdin=PIPE, stdout=PIPE)
        p.stdin.write(('%s\n' % self.creds.get_password()).encode())
        p.stdin.flush()
        return p.wait() == 0

    def realm_to_dn(self, realm):
        return ','.join(['DC=%s' % part for part in realm.lower().split('.')])

    def __well_known_container(self, container):
        if strcmp(container, 'system'):
            wkguiduc = 'AB1D30F3768811D1ADED00C04FD8D5CD'
        elif strcmp(container, 'computers'):
            wkguiduc = 'AA312825768811D1ADED00C04FD8D5CD'
        elif strcmp(container, 'dcs'):
            wkguiduc = 'A361B2FFFFD211D1AA4B00C04FD7D83A'
        elif strcmp(container, 'users'):
            wkguiduc = 'A9D1CA15768811D1ADED00C04FD8D5CD'
        result = ldap_search_s(self.l, '<WKGUID=%s,%s>' % (wkguiduc, self.realm_to_dn(self.realm)), ldap.SCOPE_SUBTREE, '(objectClass=container)', stringify_ldap(['distinguishedName']))
        if result and len(result) > 0 and len(result[0]) > 1 and 'distinguishedName' in result[0][1] and len(result[0][1]['distinguishedName']) > 0:
            return result[0][1]['distinguishedName'][-1]

    def containers(self):
        search = '(&(|(objectClass=organizationalUnit)(objectCategory=Container)(objectClass=builtinDomain))(!(|(cn=System)(cn=Program Data))))'
        ret = ldap_search(self.l, self.realm_to_dn(self.realm), ldap.SCOPE_ONELEVEL, search, ['name', 'distinguishedName'])
        return [(e[0], e[1]['name'][-1]) for e in ret]

    def obj(self, dn, attrs=[]):
        if six.PY3 and type(dn) is bytes:
            dn = dn.decode('utf-8')
        return ldap_search(self.l, dn, ldap.SCOPE_BASE, '(objectClass=*)', attrs)[-1]

    def search(self, query, container, attrs=[]):
        return ldap_search_s(self.l, container, ldap.SCOPE_SUBTREE, query, attrs)

    def objects_list(self, container):
        return ldap_search_s(self.l, container, ldap.SCOPE_SUBTREE, '(|(objectCategory=person)(objectCategory=group)(objectCategory=computer))', [])

    def add_user(self, user_attrs, container=None):
        if not container:
            container = self.__well_known_container('users')
        if not strcmp(user_attrs['userPassword'], user_attrs['confirm_passwd']):
            raise Exception('The passwords do not match.')
        attrs = {}

        attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user']
        attrs['objectCategory'] = 'CN=Person,CN=Schema,CN=Configuration,%s' % self.realm_to_dn(self.realm)

        attrs['displayName'] = user_attrs['cn']
        attrs['name'] = user_attrs['cn']
        attrs['cn'] = user_attrs['cn'].strip()
        if 'sn' in user_attrs:
            attrs['sn'] = user_attrs['sn']
        if 'givenName' in user_attrs:
            attrs['givenName'] = user_attrs['givenName']
        if 'initials' in user_attrs:
            attrs['initials'] = user_attrs['initials']
        attrs['userPrincipalName'] = '%s@%s' % (user_attrs['logon_name'], self.realm.lower())
        if 'loginShell' in user_attrs:
            attrs['loginShell'] = user_attrs['loginShell']
        if 'homeDirectory' in user_attrs:
            attrs['homeDirectory'] = user_attrs['homeDirectory']
        if 'uidNumber' in user_attrs:
            attrs['uidNumber'] = user_attrs['uidNumber']
        if 'gidNumber' in user_attrs:
            attrs['gidNumber'] = user_attrs['gidNumber']
        attrs['sAMAccountName'] = user_attrs['sAMAccountName']
        if 'gecos' in user_attrs:
            attrs['gecos'] = user_attrs['gecos']
        attrs['userAccountControl'] = ['514']
        dn = 'CN=%s,%s' % (attrs['cn'], container)
        attrs['distinguishedName'] = dn
        if user_attrs['must_change_passwd']:
            attrs['pwdLastSet'] = '0'
        else:
            attrs['pwdLastSet'] = '-1'

        try:
            ldap_add(self.l, dn, addlist(stringify_ldap(attrs)))
        except LdapException as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error('ldap.add_s: %s\n' % e.info if e.info else e.msg)
            return

        try:
            if six.PY3:
                name = attrs['sAMAccountName'].decode('utf-8')
            else:
                name = attrs['sAMAccountName']
            self.net.set_password(name, self.realm, user_attrs['userPassword'])
        except Exception as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error(str(e))

        uac = 0x0200
        # Direct modification of the cannot change password bit isn't allowed
        #if user_attrs['cannot_change_passwd'] and not user_attrs['passwd_never_expires']:
        #    uac |= 0x0040
        if user_attrs['passwd_never_expires']:
            uac |= 0x10000
        if user_attrs['account_disabled']:
            uac |= 0x0002
        ldap_modify(self.l, dn, modlist(stringify_ldap({'userAccountControl': attrs['userAccountControl']}), stringify_ldap({'userAccountControl': [str(uac)]})))

    def add_group(self, group_attrs, container=None):
        if not container:
            container = self.__well_known_container('users')

        attrs = {}
        attrs['objectClass'] = ['top', 'group']
        attrs['name'] = group_attrs['name'].strip()
        attrs['sAMAccountName'] = group_attrs['sAMAccountName']
        dn = 'CN=%s,%s' % (attrs['name'], container)
        attrs['distinguishedName'] = dn
        attrs['instanceType'] = '4'
        if 'gidNumber' in group_attrs:
            attrs['gidNumber'] = group_attrs['gidNumber']
        attrs['msSFU30Name'] = attrs['name']
        attrs['msSFU30NisDomain'] = self.realm.split('.')[0]

        groupType = 0
        if group_attrs['domain_local']:
            groupType |= 0x00000004
        elif group_attrs['global']:
            groupType |= 0x00000002
        elif group_attrs['universal']:
            groupType |= 0x00000008
        if group_attrs['security']:
            groupType |= 0x80000000
        attrs['groupType'] = [str(groupType)]

        try:
            ldap_add(self.l, dn, addlist(stringify_ldap(attrs)))
        except LdapException as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error('ldap.add_s: %s\n' % e.info if e.info else e.msg)

    def add_computer(self, computer_attrs, container=None):
        if not container:
            container = self.__well_known_container('computers')

        attrs = {}
        attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user', 'computer']
        attrs['name'] = computer_attrs['name'].strip()
        attrs['cn'] = computer_attrs['name']
        attrs['sAMAccountName'] = '%s$' % computer_attrs['sAMAccountName']
        attrs['displayName'] = attrs['sAMAccountName']
        dn = 'CN=%s,%s' % (attrs['name'], container)
        attrs['distinguishedName'] = dn
        attrs['objectCategory'] = 'CN=Computer,CN=Schema,CN=Configuration,%s' % self.realm_to_dn(self.realm)
        attrs['instanceType'] = '4'
        attrs['userAccountControl'] = '4096'
        attrs['accountExpires'] = '0'
        attrs['dNSHostName'] = '.'.join([attrs['name'], self.realm])
        attrs['servicePrincipalName'] = ['HOST/%s' % attrs['name'], 'HOST/%s' % attrs['dNSHostName']]

        try:
            ldap_add(self.l, dn, addlist(stringify_ldap(attrs)))
        except LdapException as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error('ldap.add_s: %s\n' % e.info if e.info else e.msg)

    def update(self, dn, orig_map, modattr, addattr):
        dn = dn if isinstance(dn, six.string_types) else dn.decode('utf8')
        try:
            if len(modattr):
                oldattr = {}
                for key in modattr:
                    oldattr[key] = orig_map.get(key, [])
                ldap_modify(self.l, dn, modlist(oldattr, stringify_ldap(modattr)))
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

    def delete_obj(self, dn):
        ldap_delete(self.l, dn)

