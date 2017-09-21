#!/usr/bin/env python

import ldap, ldap.modlist, ldap.sasl
import os.path, sys
from samba.net import Net
from samba.dcerpc import nbt
import uuid
import re
from subprocess import Popen, PIPE
from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT

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
        result = self.l.search_s('<WKGUID=%s,%s>' % (wkguiduc, self.realm_to_dn(self.realm)), ldap.SCOPE_SUBTREE, '(objectClass=container)', ['distinguishedName'])
        if result and len(result) > 0 and len(result[0]) > 1 and 'distinguishedName' in result[0][1] and len(result[0][1]['distinguishedName']) > 0:
            return result[0][1]['distinguishedName'][-1]

    def user_group_list(self):
        return self.l.search_s(self.__well_known_container('users'), ldap.SCOPE_SUBTREE, '(objectCategory=person)', []) + self.l.search_s(self.__well_known_container('users'), ldap.SCOPE_SUBTREE, '(objectCategory=group)', [])

    def computer_list(self):
        return self.l.search_s(self.__well_known_container('computers'), ldap.SCOPE_SUBTREE, '(objectCategory=computer)', [])

