#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
import os.path, sys
from samba.net import Net
from samba.dcerpc import nbt
import uuid
import re
from subprocess import Popen, PIPE
from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT
import traceback
from yast import ycpbuiltins
import ldap3, ssl

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

def modlist(old_entry, new_entry):
    ret = {}
    for key, val in new_entry.items():
        if type(val) != list:
            val = [val]
        if key in old_entry:
            ret[key] = (ldap3.MODIFY_REPLACE, val)
        else:
            ret[key] = (ldap3.MODIFY_ADD, val)
    for key, val in old_entry.items():
        if not key in new_entry:
            if type(val) != list:
                val = [val]
            ret[key] = (ldap3.MODIFY_DELETE, val)
    return ret

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
        self.net = Net(creds=creds, lp=lp)
        cldap_ret = self.net.finddc(domain=self.realm, flags=(nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS))
        if self.__kinit_for_gssapi():
            server = ldap3.Server(cldap_ret.pdc_dns_name)
            self.l = ldap3.Connection(server, authentication=ldap3.SASL, sasl_mechanism=ldap3.KERBEROS)
            self.l.bind()
            ycpbuiltins.y2debug('Connected to ldap server %s via GSSAPI' % cldap_ret.pdc_dns_name)
        else:
            self.l = ldap3.Connection(cldap_ret.pdc_dns_name, user='%s\\%s' % (lp.get('workgroup'), creds.get_username()), password=creds.get_password(), authentication=ldap3.NTLM, auto_bind=True)
            ycpbuiltins.y2debug('Connected to ldap server %s via NTLM' % cldap_ret.pdc_dns_name)
        self.wellKnownObjects = None

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
        if not self.wellKnownObjects and self.l.search(self.realm_to_dn(self.realm), '(objectClass=domain)', search_scope='BASE', attributes=['wellKnownObjects']):
            self.wellKnownObjects = {v.split(':')[2]: v.split(':')[-1] for v in self.l.entries[0].wellKnownObjects.values}
        return self.wellKnownObjects[wkguiduc]

    def containers(self):
        search = '(&(|(objectClass=organizationalUnit)(objectCategory=Container)(objectClass=builtinDomain))(!(|(cn=System)(cn=Program Data))))'
        try:
            self.l.search(self.realm_to_dn(self.realm), search, search_scope='LEVEL', attributes=['name', 'distinguishedName'])
        except Exception as e:
            print(str(e))
        return [(e['distinguishedName'].value, e['name'].value) for e in self.l.entries]

    def objects_list(self, container):
        try:
            self.l.search(container, '(|(objectCategory=person)(objectCategory=group)(objectCategory=computer))', attributes=ldap3.ALL_ATTRIBUTES)
            return [(i.distinguishedName.value, i.entry_raw_attributes) for i in self.l.entries]
        except Exception as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error(str(e))

    def add_user(self, user_attrs, container=None):
        if not container:
            container = self.__well_known_container('users')
        if user_attrs['userPassword'] != user_attrs['confirm_passwd']:
            raise Exception('The passwords do not match.')
        attrs = {}

        attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user']
        attrs['objectCategory'] = 'CN=Person,CN=Schema,CN=Configuration,%s' % self.realm_to_dn(self.realm)

        attrs['displayName'] = user_attrs['cn']
        attrs['name'] = user_attrs['cn']
        attrs['cn'] = user_attrs['cn']
        attrs['sn'] = user_attrs['sn']
        attrs['givenName'] = user_attrs['givenName']
        attrs['initials'] = user_attrs['initials']
        attrs['userPrincipalName'] = '%s@%s' % (user_attrs['logon_name'], self.realm.lower())
        attrs['loginShell'] = user_attrs['loginShell']
        attrs['homeDirectory'] = user_attrs['homeDirectory']
        attrs['uidNumber'] = user_attrs['uidNumber']
        attrs['gidNumber'] = user_attrs['gidNumber']
        attrs['sAMAccountName'] = user_attrs['sAMAccountName']
        attrs['gecos'] = user_attrs['gecos']
        attrs['userAccountControl'] = ['514']
        dn = 'CN=%s,%s' % (attrs['cn'], container)
        attrs['distinguishedName'] = dn
        if user_attrs['must_change_passwd']:
            attrs['pwdLastSet'] = '0'
        else:
            attrs['pwdLastSet'] = '-1'

        self.l.add(dn, attributes=stringify_ldap(attrs))

        try:
            self.net.set_password(attrs['sAMAccountName'], self.realm, user_attrs['userPassword'])
        except Exception as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error(str(e))
        # self.l.extend.microsoft.modify_password(user=dn, new_password=user_attrs['userPassword'])

        uac = 0x0200
        # Direct modification of the cannot change password bit isn't allowed
        #if user_attrs['cannot_change_passwd'] and not user_attrs['passwd_never_expires']:
        #    uac |= 0x0040
        if user_attrs['passwd_never_expires']:
            uac |= 0x10000
        if user_attrs['account_disabled']:
            uac |= 0x0002
        self.l.modify(dn, stringify_ldap(modlist({'userAccountControl': attrs['userAccountControl']}, {'userAccountControl': [str(uac)]})))

    def add_group(self, group_attrs, container=None):
        if not container:
            container = self.__well_known_container('users')

        attrs = {}
        attrs['objectClass'] = ['top', 'group']
        attrs['name'] = group_attrs['name']
        attrs['sAMAccountName'] = group_attrs['sAMAccountName']
        dn = 'CN=%s,%s' % (attrs['name'], container)
        attrs['distinguishedName'] = dn
        attrs['instanceType'] = '4'
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

        self.l.add(dn, attributes=stringify_ldap(attrs))

    def add_computer(self, computer_attrs, container=None):
        if not container:
            container = self.__well_known_container('computers')

        attrs = {}
        attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user', 'computer']
        attrs['name'] = computer_attrs['name']
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

        self.l.add(dn, attributes=stringify_ldap(attrs))

    def update(self, dn, orig_map, modattr, addattr):
        try:
            if len(modattr):
                oldattr = {}
                for key in modattr:
                    oldattr[key] = orig_map.get(key, [])
                self.l.modify(dn, modlist(oldattr, modattr))
            if len(addattr):
                self.l.add(dn, attributes=stringify_ldap(addattr))
        except Exception as e:
            ycpbuiltins.y2error(traceback.format_exc())
            ycpbuiltins.y2error(str(e))
            return False
        return True

