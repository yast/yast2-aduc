#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
import copy
from complex import Connection
from adcommon.strings import strcmp
from random import randint
from yast import import_module
import_module('Wizard')
import_module('UI')
from yast import *
import six
from ldap.filter import filter_format
from adcommon.yldap import SCOPE_SUBTREE as SUBTREE
from adcommon.creds import YCreds
from adcommon.ui import CreateMenu, DeleteButtonBox

def have_x():
    from subprocess import Popen, PIPE
    p = Popen(['xset', '-q'], stdout=PIPE, stderr=PIPE)
    return p.wait() == 0
have_advanced_gui = have_x()

def dump(obj):
    ycpbuiltins.y2debug("len obj %d" % len(obj))
    i = 0
    ycpbuiltins.y2debug("cn %s" % obj[0])
    for key in obj[1].keys():
        value = obj[1][key]
        ycpbuiltins.y2debug("item[%d] key %s value type %s value ->%s<-" % (i,key, type(value), value))
        i = i + 1

class MessageBox:
    def __init__(self, message):
        self.message = message

    def Show(self):
        UI.OpenDialog(
          VBox(
            Label(
              self.message
            ),
            PushButton(Opt("default"), "&OK")
          )
        )
        UI.UserInput()
        UI.CloseDialog()

UserDataModel = {
    'general' : {
        'givenName' : 'First Name:',
        'initials' : 'Initials:',
        'sn' : 'Last name:',
        'displayName' : 'Display name:',
        'description' : 'Description:',
        'physicalDeliveryOfficeName' : 'Office:',
        'telephoneNumber' : 'Telephone number:',
        'mail' : 'E-mail:',
        'wWWHomePage' : 'Web page:' },
    'address' : {
        'streetAddress' : 'Street:',
        'l' : 'City:',
        'postOfficeBox' : 'P.O. Box:',
        'st' : 'State/province:',
        'postalCode' : 'Zip/Postal Code:',
        'co' : 'Country/Region:' },
    'account' : {
        'userPrincipalName' : 'User Logon name:',
        'sAMAccountName' : 'User Logon name (pre-windows 2000):',
        'pwdLastSet' : 'User must change password at next logon',
        'userAccountControl' : None,
        },
    'unix_attrs' : {
        'uidNumber' : 'UID number:',
        'gidNumber' : 'GID number:',
        'gecos' : 'GECOS:',
        'homeDirectory' : 'Home directory:',
        'loginShell' : 'Login shell:',
        }
    }

def account_hook(key, val):
    if strcmp('userPrincipalName', key):
        urealm = UI.QueryWidget('urealm', 'Value')
        val = '%s%s' % (val, urealm)
    elif strcmp('pwdLastSet', key):
        if val:
            val = '0'
        else:
            val = '-1'
    elif strcmp('userAccountControl', key):
        passwd_never_expires = UI.QueryWidget('passwd_never_expires', 'Value')
        account_disabled = UI.QueryWidget('account_disabled', 'Value')
        uac = int(val)
        if passwd_never_expires:
            uac |= 0x10000
        else:
            uac &= 0x10000
        if account_disabled:
            uac |= 0x0002
        else:
            uac &= 0x0002
        val = str(uac)
    return val

UserTabContents = {
        'general' : {
            'content' : (lambda conn, model: VBox(Left(HBox(
                InputField(Id('givenName'), Opt('hstretch'), UserDataModel['general']['givenName'], model.get_value('givenName')),
                InputField(Id('initials'), Opt('hstretch'), UserDataModel['general']['initials'], model.get_value('initials')))),
                Left(InputField(Id('sn'), Opt('hstretch'), UserDataModel['general']['sn'], model.get_value('sn'))),
                Left(InputField(Id('displayName'), Opt('hstretch'), UserDataModel['general']['displayName'], model.get_value('displayName'))),
                Left(InputField(Id('description'), Opt('hstretch'), UserDataModel['general']['description'], model.get_value('description'))),
                Left(InputField(Id('physicalDeliveryOfficeName'), Opt('hstretch'), UserDataModel['general']['physicalDeliveryOfficeName'], model.get_value('physicalDeliveryOfficeName'))),
                Left(InputField(Id('telephoneNumber'), Opt('hstretch'), UserDataModel['general']['telephoneNumber'], model.get_value('telephoneNumber'))),
                Left(InputField(Id('mail'), Opt('hstretch'), UserDataModel['general']['mail'], model.get_value('mail'))),
                Left(InputField(Id('wWWHomePage'), Opt('hstretch'), UserDataModel['general']['wWWHomePage'], model.get_value('wWWHomePage')))
            )),
            'data' : UserDataModel['general'],
            'title' : 'General',
            'set_hook' : None,
            'input_hook' : None,
            },
        'address' : {
            'content' : (lambda conn, model: VBox(
                Left(MultiLineEdit(Id('streetAddress'), Opt('hstretch'), UserDataModel['address']['streetAddress'], model.get_value('streetAddress'))),
                Left(InputField(Id('postOfficeBox'), Opt('hstretch'), UserDataModel['address']['postOfficeBox'], model.get_value('postOfficeBox'))),
                Left(InputField(Id('l'), Opt('hstretch'), UserDataModel['address']['l'], model.get_value('l'))),
                Left(InputField(Id('st'), Opt('hstretch'), UserDataModel['address']['st'], model.get_value('st'))),
                Left(InputField(Id('postalCode'), Opt('hstretch'), UserDataModel['address']['postalCode'], model.get_value('postalCode',))),
                Left(InputField(Id('co'), Opt('hstretch'), UserDataModel['address']['co'], model.get_value('co')))
            )),
            'data' : UserDataModel['address'],
            'title' : 'Address',
            'set_hook' : None,
            'input_hook' : None,
            },
        'account' : {
            'content' : (lambda conn, model: VBox(
                Left(Label(UserDataModel['account']['userPrincipalName'])),
                HBox(
                    InputField(Id('userPrincipalName'), Opt('hstretch'), '', model.get_value('userPrincipalName').split(six.b('@'))[0] if model.contains('userPrincipalName') else ''),
                    InputField(Id('urealm'), Opt('hstretch', 'disabled'), '', six.b('@%s') % model.get_value('userPrincipalName').split(six.b('@'))[-1] if model.contains('userPrincipalName') else '')
                ),
                InputField(Id('sAMAccountName'), Opt('hstretch'), UserDataModel['account']['sAMAccountName'], model.get_value('sAMAccountName')),
                Left(Label('Account options:')),
                Left(CheckBox(Id('pwdLastSet'), Opt('hstretch'), UserDataModel['account']['pwdLastSet'], True if strcmp(model.get_value('pwdLastSet'), '0') else False)),
                Left(CheckBox(Id('passwd_never_expires'), Opt('hstretch'), 'Password never expires', True if int(model.get_value('userAccountControl')) & 0x10000 else False)),
                Left(CheckBox(Id('account_disabled'), Opt('hstretch'), 'Account is disabled', True if int(model.get_value('userAccountControl')) & 0x0002 else False)),
            )),
            'data' : UserDataModel['account'],
            'title' : 'Account',
            'set_hook' : account_hook,
            'input_hook' : None,
        },
        'unix_attrs' : {
            'content' : (lambda conn, model: VBox(
                TextEntry(Id('uidNumber'), Opt('hstretch'), UserDataModel['unix_attrs']['uidNumber'], model.get_value('uidNumber') if model.contains('uidNumber') else ''),
                TextEntry(Id('gidNumber'), Opt('hstretch'), UserDataModel['unix_attrs']['gidNumber'], model.get_value('gidNumber') if model.contains('gidNumber') else ''),
                TextEntry(Id('gecos'), Opt('hstretch'), UserDataModel['unix_attrs']['gecos'], model.get_value('gecos') if model.contains('gecos') else ''),
                TextEntry(Id('homeDirectory'), Opt('hstretch'), UserDataModel['unix_attrs']['homeDirectory'], model.get_value('homeDirectory') if model.contains('homeDirectory') else ''),
                TextEntry(Id('loginShell'), Opt('hstretch'), UserDataModel['unix_attrs']['loginShell'], model.get_value('loginShell') if model.contains('loginShell') else ''),
            )),
            'data' : UserDataModel['unix_attrs'],
            'title' : 'Unix Attributes',
            'set_hook' : None,
            'input_hook' : None,
        }
        }

def compare(obj1, obj2):
    if type(obj1) is list and type(obj2) is list:
        if len(obj1) == len(obj2):
            return all([compare(obj1[i], obj2[i]) for i in range(0, len(obj1))])
    elif type(obj1) is dict and type(obj2) is dict:
        if compare(sorted(obj1.keys()), sorted(obj2.keys())):
            return all([compare(obj1[k], obj2[k]) for k in obj1.keys()])
    elif all([isinstance(val, six.string_types+(bytes,)) for val in (obj1, obj2)]):
        return strcmp(obj1, obj2)
    else:
        return obj1 == obj2

class TabModel:
    def __init__(self, props_map):
        self.props_orig = props_map
        self.props_map = copy.deepcopy(props_map)
        self.modified = False

    def set_value(self, key, value):
        oldvalue = self.props_map.get(key, [six.b("")])
        if type(oldvalue) == list and type(value) != list:
            value = [value]
        if not compare(oldvalue, value):
            self.props_map[key] = value
            if not self.modified:
                self.modified = True

    def get_value(self, key):
        value = self.props_map.get(key, [""])
        if len(value) == 1:
            value = value[-1]
        return value

    def contains(self, key):
        return key in self.props_map

    def is_modified(self):
        return self.modified

    def update_from_view(self, tabData, hook):
        for key in tabData.keys():
            value = UI.QueryWidget(key, 'Value')
            if hook:
                if value is None:
                    value = self.props_orig[key][-1]
                value = hook(key, value)
            if value is not None:
                self.set_value(key, value)

    def apply_changes(self, conn):
        if self.is_modified():
            modattr = {}
            for key in self.props_map.keys():
                # filter out temporary placeholder keys  (like idontknow)
                if key.startswith('idontknow'):
                    continue
                if key in self.props_orig.keys():
                    if not strcmp(self.props_map[key], self.props_orig[key]):
                        ycpbuiltins.y2debug('attribute %s changed.. old %s -> new %s' % (key, self.props_orig.get(key, [])[-1], self.get_value(key)))
                        if len(self.props_map[key]) == 0:
                            ycpbuiltins.y2debug("deleting %s" % key)
                            modattr[key] = []
                        else:
                            modattr[key] = self.props_map[key]
                else:
                    ycpbuiltins.y2debug('attribute was added %s ->%s<-'%(key, self.props_map[key]))
                    modattr[key] = self.props_map[key]

            if conn.update(self.props_map['distinguishedName'][-1], self.props_orig, modattr, {}):
                # sync attributes with succsessful ldap commit
                for key in modattr:
                    # modified
                    if len(modattr[key]):
                        self.props_orig[key] = modattr[key]
                    # deleted
                    else:
                        self.props_orig.pop(key, None)
                        self.props_map.pop(key, None)

class TabProps(object):
    def __init__(self, conn, obj, contents, start_tab):
        self.obj = obj
        self.conn = conn
        self.keys = self.obj[1].keys()
        self.props_map = self.obj[1]
        self.tabModel = TabModel(self.props_map)
        self.contents = contents
        self.initial_tab = start_tab
        self.dimensions = (60, 33)
        #dump(obj)

    def multitab(self):
        multi = MinSize(*self.dimensions, VBox(
          DumbTab(Id('multitab'),
            [
               Item(Id(key), self.contents[key]['title']) for key in self.contents.keys()
            ],
            HBox(HSpacing(1), Left(
                VBox(
                    VSpacing(0.3),
                    Top(
                        ReplacePoint(Id('tabContents'), self.content(self.initial_tab))
                    ),
                    VSpacing(1),
                    Bottom(
                        HBox(PushButton(Id('ok'), "OK"), PushButton(Id('cancel'), "Cancel"),
                        PushButton(Id('apply'), "Apply")),
                    ),
                    VSpacing(0.3),
                ),
            ),
          HSpacing(1))),
        ))
        return multi

    def content(self, next_tab):
        return self.contents[next_tab]['content'](self.conn, self.tabModel)

    def Show(self):
        UI.SetApplicationTitle(six.b('%s Properties') % self.tabModel.get_value('name'))
        UI.OpenDialog(self.multitab())
        next_tab = self.initial_tab
        UI.ChangeWidget('multitab', 'CurrentItem', Id(next_tab))
        self.current_tab = next_tab
        while True:
            ret = UI.UserInput()
            ycpbuiltins.y2debug("tab dialog input is %s"%ret)
            if str(ret) in self.contents.keys():
                previous_tab = next_tab
                next_tab = str(ret)
                if next_tab != previous_tab:
                    # update the model of the tab we are switching away from
                    self.tabModel.update_from_view(self.contents[previous_tab]['data'], self.contents[previous_tab]['set_hook'])
                    #switch tabs
                    UI.ReplaceWidget('tabContents', self.content(next_tab))
                    self.current_tab = next_tab
            if str(ret) in ('ok', 'apply'):
                ycpbuiltins.y2debug('TabProps.Handleinput %s'%ret)
                ycpbuiltins.y2debug('updating model from tab view %s'%self.current_tab)
                self.tabModel.update_from_view(self.contents[self.current_tab]['data'], self.contents[self.current_tab]['set_hook'])
                self.tabModel.apply_changes(self.conn)
            if str(ret) in ('ok', 'cancel'):
                break
            if self.contents[self.current_tab]['input_hook']:
                self.contents[self.current_tab]['input_hook'](ret, self.conn, self.tabModel)
                continue
        UI.CloseDialog()

class UserProps(TabProps):
    def __init__(self, conn, obj):
        TabProps.__init__(self, conn, obj, UserTabContents, 'general')

ComputerDataModel = {
        'general' : {
            'name' : 'Computer name (pre-Windows 2000):',
            'dNSHostName' : 'DNS-name:',
            'idontknow' : 'Workstation or server:',
            'description' : 'Description:'
            },
        'operating_system' : {
            'operatingSystem' : 'Name:',
            'operatingSystemVersion' : 'Operating System:',
            'operatingSystemServicePack' : 'Service Pack:'
            },
        'location' : {
            'location' : 'Location:'
            },
        }

ComputerTabContents = {
        'general' : {
            'content' : (lambda conn, model: VBox(
                InputField(Id('name'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['name'], model.get_value('name')),
                InputField(Id('dNSHostName'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['dNSHostName'], model.get_value('dNSHostName')),
                # #TODO find out what attribute site is
                InputField(Id('idontknow'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['idontknow'], "Workstation or server"),
                InputField(Id('description'), Opt('hstretch'), ComputerDataModel['general']['description'], model.get_value('description')))),

            'data' : ComputerDataModel['general'],
            'title': 'General',
            'set_hook' : None,
            'input_hook' : None,
            },

        'operating_system' : {
            'content' : (lambda conn, model: VBox(
                  InputField(Id('operatingSystem'), Opt('disabled', 'hstretch'), ComputerDataModel['operating_system']['operatingSystem'], model.get_value('operatingSystem')),
                  InputField(Id('operatingSystemVersion'), Opt('disabled', 'hstretch'),ComputerDataModel['operating_system']['operatingSystemVersion'], model.get_value('operatingSystemVersion')),
                  InputField(Id('operatingSystemServicePack'), Opt('disabled', 'hstretch'), ComputerDataModel['operating_system']['operatingSystemServicePack'], model.get_value('operatingSystemServicePack')))),
            'data' : ComputerDataModel['operating_system'],
            'title': 'Operating System',
            'set_hook' : None,
            'input_hook' : None,
            },
        'location' : {
            'content' : (lambda conn, model: VBox(
                TextEntry(Id('location'), Opt('hstretch'), ComputerDataModel['location']['location'], model.get_value('location')))),
            'data' : ComputerDataModel['location'],
            'title': 'Location',
            'set_hook' : None,
            'input_hook' : None,
            }
        }

class ComputerProps(TabProps):
    def __init__(self, conn, obj):
        TabProps.__init__(self, conn, obj, ComputerTabContents, 'general')
        self.dimensions = (60, 19)

GroupDataModel = {
    'general' : {
        'sAMAccountName' : 'Group name (pre-Windows 2000):',
        'gidNumber' : 'GID number:',
        'description' : 'Description:',
        'mail' : 'E-mail:',
        'groupType' : None,
    },
    'members' : {
        'member' : None,
    }
}

def group_general_hook(key, val):
    if strcmp(key, 'groupType'):
        domain_local = UI.QueryWidget('domain_local', 'Value')
        global_val = UI.QueryWidget('global', 'Value')
        universal = UI.QueryWidget('universal', 'Value')
        security = UI.QueryWidget('security', 'Value')
        groupType = 0
        if domain_local:
            groupType |= 0x00000004
        elif global_val:
            groupType |= 0x00000002
        elif universal:
            groupType |= 0x00000008
        if security:
            groupType |= 0x80000000
        val = str(groupType)
    return val

def search_group_member_dialog(conn):
    return HBox(HSpacing(1), VBox(
        VSpacing(.3),
        Left(Label('Select this object type:')),
        HBox(
            TextEntry(Id('obj_type'), Opt('disabled'), '', 'Users, Groups, or Other objects'),
            PushButton(Id('choose_obj_type'), Opt('disabled'), 'Object Types...'),
        ),
        Left(Label('From this location:')),
        HBox(
            TextEntry(Id('location'), Opt('disabled'), '', conn.realm_to_dn(conn.realm)),
            PushButton(Id('choose_location'), 'Locations...'),
        ),
        Left(Label('Enter the object name to select:')),
        HBox(
            MinSize(10, 3,
                ReplacePoint(Id('check_name_rp'),
                    MultiLineEdit(Id('name'), ''),
                ),
            ),
            PushButton(Id('check_name'), 'Check Name')
        ),
        Right(HBox(
            PushButton(Id('select_ok'), 'OK'),
            PushButton(Id('select_cancel'), 'Cancel')
        )),
        VSpacing(.3),
    ), HSpacing(1))

def sub_tree(conn, dn):
    tree_containers = conn.containers(dn)
    return [Item(Id(c[0]), c[1], False, sub_tree(conn, c[0])) for c in tree_containers]

def search_group_member_location_dialog(conn):
    tree_containers = conn.containers()
    items = [Item(Id(c[0]), c[1], False, sub_tree(conn, c[0])) for c in tree_containers]

    return MinSize(10, 5, HBox(HSpacing(1), VBox(
        VSpacing(.3),
        Tree(Id('location_tree'), '', [
            Item(Id(conn.realm_to_dn(conn.realm)), conn.realm.lower(), True, items),
        ]),
        Right(HBox(
            PushButton(Id('location_ok'), 'OK'),
            PushButton(Id('location_cancel'), 'Cancel')
        )),
        VSpacing(.3),
    ), HSpacing(1)))

def search_group_member_location_input(conn):
    UI.SetApplicationTitle('Locations')
    UI.OpenDialog(search_group_member_location_dialog(conn))
    location = None
    while True:
        ret = UI.UserInput()
        if str(ret) == 'abort' or str(ret) == 'location_cancel':
            break
        elif str(ret) == 'location_ok':
            location = UI.QueryWidget('location_tree', 'CurrentItem')
            break
    UI.CloseDialog()
    return location

def select_name_list(results):
    items = [Item(Id(r[0]), six.b('%s (%s)') % (r[-1]['name'][-1], r[-1]['userPrincipalName'][-1]) if 'userPrincipalName' in r[-1] else r[-1]['name'][-1], False, []) for r in results]
    return Tree(Id('name_list'), '', items)

def group_members_input(ret, conn, model):
    members = model.get_value('member')
    if members and type(members) is not list:
        members = [members]
    if not members:
        members = []
    if str(ret) == 'add':
        selection = None
        UI.SetApplicationTitle('Select Users, Contacts, Computers, or Groups')
        UI.OpenDialog(search_group_member_dialog(conn))
        while True:
            ret = UI.UserInput()
            if str(ret) == 'abort' or str(ret) == 'select_cancel':
                selection = None
                break
            elif str(ret) == 'check_name':
                name = UI.QueryWidget('name', 'Value')
                location = UI.QueryWidget('location', 'Value')
                query = filter_format('(&(|(name=%s*)(cn=%s*)(sAMAccountName=%s*))(|(objectClass=person)(objectClass=group)))', (name, name, name))
                results = conn.ldap_search(location, SUBTREE, query, ['name', 'userPrincipalName'])
                UI.ReplaceWidget('check_name_rp', select_name_list(results))
            elif str(ret) == 'select_ok':
                selection = UI.QueryWidget('name_list', 'CurrentItem')
                break
            elif str(ret) == 'choose_location':
                location = search_group_member_location_input(conn)
                if location is not None:
                    UI.ChangeWidget('location', 'Value', location)
        UI.CloseDialog()
        if selection is not None:
            members.append(selection)
            model.set_value('member', members)
            UI.ReplaceWidget('group_members_tab', group_members_content(conn, members))
    elif str(ret) == 'remove':
        selected = UI.QueryWidget('members', 'Value')
        members = [m for m in members if not strcmp(m, selected)]
        model.set_value('member', members)
        UI.ReplaceWidget('group_members_tab', group_members_content(conn, members))

def group_members_content(conn, members):
    if members and type(members) is not list:
        members = [members]
    items = []
    for member in members:
        if six.PY3 and type(member) is bytes:
            member = member.decode('utf-8')
        obj = conn.obj(member, attrs=['displayName', 'userPrincipalName'])[-1]
        if 'userPrincipalName' in obj:
            realm = obj['userPrincipalName'][-1].split(six.b('@'))[-1]
            if six.PY3:
                realm = realm.decode('utf-8')
            realm_dn = ','.join(['DC=%s' % part for part in realm.lower().split('.')])
            loc_dn = member[:member.lower().find(realm_dn.lower())-1]
            location = '/'.join([i[3:] for i in reversed(loc_dn.split(','))])
        else:
            location = ''
        if 'displayName' in obj:
            displayName = obj['displayName'][-1]
        else:
            displayName = member.split(',')[0][3:]
        items.append(Item(Id(member), displayName, location))
    opts = tuple()
    if len(members) == 0:
        opts = (Opt('disabled'),)
    return Frame('Members:', VBox(
        VSpacing(.3),
        VWeight(8, Table(Id('members'), Opt('notify'), Header('Name', 'Active Directory Domain Services Folder'), items)),
        VStretch(),
        VWeight(1, Left(HBox(
            PushButton(Id('add'), 'Add...'),
            PushButton(Id('remove'), *opts, 'Remove'),
        )))
    ))

def group_members_tab(conn, members):
    content = group_members_content(conn, members)
    return ReplacePoint(Id('group_members_tab'), content)

GroupTabContents = {
    'general' : {
        'content' : (lambda conn, model: VBox(
            TextEntry(Id('sAMAccountName'), Opt('hstretch'), GroupDataModel['general']['sAMAccountName'], model.get_value('sAMAccountName')),
            TextEntry(Id('gidNumber'), Opt('hstretch'), GroupDataModel['general']['gidNumber'], model.get_value('gidNumber')),
            TextEntry(Id('description'), Opt('hstretch'), GroupDataModel['general']['description'], model.get_value('description')),
            TextEntry(Id('mail'), Opt('hstretch'), GroupDataModel['general']['mail'], model.get_value('mail')),
            HBox(
                Top(RadioButtonGroup(Id('group_scope'), VBox(
                    Left(Label('Group scope')),
                    Left(RadioButton(Id('domain_local'), Opt('disabled' if int(model.get_value('groupType')) & 0x00000002 else ''), 'Domain local', True if int(model.get_value('groupType')) & 0x00000004 else False)),
                    Left(RadioButton(Id('global'), Opt('disabled' if int(model.get_value('groupType')) & 0x00000004 else ''), 'Global', True if int(model.get_value('groupType')) & 0x00000002 else False)),
                    Left(RadioButton(Id('universal'), 'Universal', True if int(model.get_value('groupType')) & 0x00000008 else False)),
                ))),
                Top(RadioButtonGroup(Id('group_type'), VBox(
                    Left(Label('Group type')),
                    Left(RadioButton(Id('security'), 'Security', True if int(model.get_value('groupType')) & 0x80000000 else False)),
                    Left(RadioButton(Id('distribution'), 'Distribution', False if int(model.get_value('groupType')) & 0x80000000 else True)),
                )))
            ),
        )),
        'data' : GroupDataModel['general'],
        'title' : 'General',
        'set_hook' : group_general_hook,
        'input_hook' : None,
    },
    'members' : {
        'content' : (lambda conn, model: group_members_tab(conn, model.get_value('member'))),
        'data' : GroupDataModel['members'],
        'title' : 'Members',
        'set_hook' : None,
        'input_hook' : group_members_input,
    }
}

class GroupProps(TabProps):
    def __init__(self, conn, obj):
        TabProps.__init__(self, conn, obj, GroupTabContents, 'general')
        self.dimensions = (60, 24)

class NewObjDialog:
    def __init__(self, lp, obj_type, location):
        self.lp = lp
        self.obj = {}
        self.obj_type = obj_type
        self.dialog_seq = 0
        self.dialog = None
        self.realm = self.lp.get('realm')
        realm_dn = ','.join(['DC=%s' % part for part in self.realm.lower().split('.')])
        loc_dn = location[:location.lower().find(realm_dn.lower())-1]
        self.location = '/'.join([i[3:] for i in reversed(loc_dn.split(','))])

    def __new(self):
        pane = self.__fetch_pane()
        return MinSize(56, 22, HBox(HSpacing(3), VBox(
                VSpacing(1),
                Label('Create in:\t%s/%s' % (self.realm, self.location)),
                ReplacePoint(Id('new_pane'), pane),
                VSpacing(1),
            ), HSpacing(3)))

    def __fetch_pane(self):
        if not self.dialog:
            if strcmp(self.obj_type, 'user'):
                self.dialog = self.__user_dialog()
            elif strcmp(self.obj_type, 'group'):
                self.dialog = self.__group_dialog()
            elif strcmp(self.obj_type, 'computer'):
                self.dialog = self.__computer_dialog()
        return self.dialog[self.dialog_seq][0]

    def __user_dialog(self):
        def unix_user_hook():
            if 'homeDirectory' not in self.obj:
                homedir = '/home/%s/%s' % (self.lp.get('workgroup'), self.obj['logon_name'])
                UI.ChangeWidget('homeDirectory', 'Value', homedir)
            if 'gecos' not in self.obj:
                UI.ChangeWidget('gecos', 'Value', self.obj['cn'])
        return [
            [VBox(
                HBox(
                    TextEntry(Id('givenName'), UserDataModel['general']['givenName']),
                    TextEntry(Id('initials'), UserDataModel['general']['initials']),
                ),
                TextEntry(Id('sn'), UserDataModel['general']['sn']),
                TextEntry(Id('cn'), 'Full name:'),
                Left(Bottom(Label(Id('logon_name_label'), 'User Logon name:'))),
                Left(Left(HBox(InputField(Id('logon_name'), Opt('hstretch'), ''), InputField(Id('domainName'), Opt('hstretch', 'disabled'), '', '@%s' % self.realm)))),
                Left(Bottom(Label(Id('sAMAccountName_label'), 'User Logon name (pre-windows 2000):'))),
                Left(Left(HBox(InputField(Opt('hstretch', 'disabled'), '', '%s\\' % self.lp.get('workgroup')), InputField(Id('sAMAccountName'), Opt('hstretch'), '')))),
                Bottom(Right(HBox(
                    PushButton(Id('back'), Opt('disabled'), '< Back'),
                    PushButton(Id('next'), 'Next >'),
                    PushButton(Id('cancel'), 'Cancel'),
                ))),
            ),
            ['givenName', 'initials', 'sn', 'cn', 'logon_name', 'sAMAccountName'], # known keys
            ['cn', 'logon_name', 'sAMAccountName'], # required keys
            None, # dialog hook
            ],
            [VBox(
                TextEntry(Id('uidNumber'), UserDataModel['unix_attrs']['uidNumber'], str(randint(1000, 32767))),
                TextEntry(Id('gidNumber'), UserDataModel['unix_attrs']['gidNumber']),
                TextEntry(Id('gecos'), UserDataModel['unix_attrs']['gecos']),
                TextEntry(Id('homeDirectory'), UserDataModel['unix_attrs']['homeDirectory']),
                TextEntry(Id('loginShell'), UserDataModel['unix_attrs']['loginShell'], '/bin/sh'),
                Bottom(Right(HBox(
                    PushButton(Id('back'), '< Back'),
                    PushButton(Id('next'), 'Next >'),
                    PushButton(Id('cancel'), 'Cancel'),
                ))),
            ),
            ['uidNumber', 'gidNumber', 'gecos', 'homeDirectory', 'loginShell'], # known keys
            [], # required keys
            unix_user_hook, # dialog hook
            ],
            [VBox(
                Left(Password(Id('userPassword'), Opt('hstretch'), 'Password:')),
                Left(Password(Id('confirm_passwd'), Opt('hstretch'), 'Confirm password:')),
                Left(CheckBox(Id('must_change_passwd'), UserDataModel['account']['pwdLastSet'], True)),
                Left(CheckBox(Id('cannot_change_passwd'), Opt('disabled'), 'User cannot change password')),
                Left(CheckBox(Id('passwd_never_expires'), 'Password never expires')),
                Left(CheckBox(Id('account_disabled'), 'Account is disabled')),
                Bottom(Right(HBox(
                    PushButton(Id('back'), '< Back'),
                    PushButton(Id('finish'), 'Finish'),
                    PushButton(Id('cancel'), 'Cancel')
                ))),
            ),
            ['userPassword', 'confirm_passwd', 'must_change_passwd', 'cannot_change_passwd', 'passwd_never_expires', 'account_disabled'], # known keys
            ['userPassword', 'confirm_passwd'], # required keys
            None, # dialog hook
            ],
        ]

    def __group_dialog(self):
        return [
            [VBox(
                TextEntry(Id('name'), 'Group name:'),
                TextEntry(Id('sAMAccountName'), GroupDataModel['general']['sAMAccountName']),
                TextEntry(Id('gidNumber'), GroupDataModel['general']['gidNumber'], str(randint(1000, 32767))),
                HBox(
                    Top(RadioButtonGroup(Id('group_scope'), VBox(
                        Left(Label('Group scope')),
                        Left(RadioButton(Id('domain_local'), 'Domain local')),
                        Left(RadioButton(Id('global'), 'Global', True)),
                        Left(RadioButton(Id('universal'), 'Universal')),
                    ))),
                    Top(RadioButtonGroup(Id('group_type'), VBox(
                        Left(Label('Group type')),
                        Left(RadioButton(Id('security'), 'Security', True)),
                        Left(RadioButton(Id('distribution'), 'Distribution')),
                    )))
                ),
                Bottom(Right(HBox(
                    PushButton(Id('finish'), 'OK'),
                    PushButton(Id('cancel'), 'Cancel'),
                ))),
            ),
            ['name', 'sAMAccountName', 'gidNumber', 'domain_local', 'global', 'universal', 'security'], # known keys
            ['name', 'sAMAccountName'], # required keys
            None, # dialog hook
            ],
        ]

    def __computer_dialog(self):
        return [
            [VBox(
                TextEntry(Id('name'), 'Computer name:'),
                TextEntry(Id('sAMAccountName'), 'Computer name (pre-Windows 2000):'),
                Left(Label(Opt('disabled'), 'The following user or group can join this computer to a domain.')),
                TextEntry(Id('join_id'), Opt('disabled'), 'User or group:', 'Default: Domain Admins'),
                CheckBox(Id('pre_win2k'), Opt('disabled'), 'Assign this computer account as a pre-Windows 2000 computer'),
                Bottom(Right(HBox(
                    PushButton(Id('finish'), 'OK'),
                    PushButton(Id('cancel'), 'Cancel'),
                ))),
            ),
            ['name', 'sAMAccountName', 'join_id', 'pre_win2k'], # known keys
            ['name', 'sAMAccountName'], # required keys
            None, # dialog hook
            ],
        ]

    def __warn_label(self, key):
        label = UI.QueryWidget('%s_label' % key, 'Value')
        if not label:
            label = UI.QueryWidget(key, 'Label')
        if label[-2:] != ' *':
            if not UI.ChangeWidget('%s_label' % key, 'Value', '%s *' % label):
                UI.ChangeWidget(key, 'Label', '%s *' % label)

    def __fetch_values(self, back=False):
        ret = True
        known_value_keys = self.dialog[self.dialog_seq][1]
        for key in known_value_keys:
            value = UI.QueryWidget(key, 'Value')
            if value or type(value) == bool:
                self.obj[key] = value
        required_value_keys = self.dialog[self.dialog_seq][2]
        for key in required_value_keys:
            if not key in self.obj or not self.obj[key]:
                self.__warn_label(key)
                ycpbuiltins.y2error('Missing value for %s' % key)
                ret = False
        return ret

    def __set_values(self):
        for key in self.obj:
            UI.ChangeWidget(key, 'Value', self.obj[key])

    def __dialog_hook(self):
        hook = self.dialog[self.dialog_seq][3]
        if hook:
            hook()

    def Show(self):
        UI.SetApplicationTitle('New Object - %s' % self.obj_type.title())
        UI.OpenDialog(self.__new())
        while True:
            self.__dialog_hook()
            ret = UI.UserInput()
            if str(ret) == 'abort' or str(ret) == 'cancel':
                ret = None
                break
            elif str(ret) == 'next':
                if self.__fetch_values():
                    self.dialog_seq += 1
                    UI.ReplaceWidget('new_pane', self.__fetch_pane())
                    self.__set_values()
            elif str(ret) == 'back':
                self.__fetch_values(True)
                self.dialog_seq -= 1;
                UI.ReplaceWidget('new_pane', self.__fetch_pane())
                self.__set_values()
            elif str(ret) == 'finish':
                if self.__fetch_values():
                    ret = self.obj
                    break
        UI.CloseDialog()
        return ret

class SearchDialog:
    def __init__(self, lp, conn, container):
        self.lp = lp
        self.conn = conn

        self.realm = self.lp.get('realm')
        realm_dn = ','.join(['DC=%s' % part for part in self.realm.lower().split('.')])
        if container:
            loc_dn = container[:container.lower().find(realm_dn.lower())-1]
            self.container = container
            self.location = '/'.join([i[3:] for i in reversed(loc_dn.split(','))])
        else:
            loc_dn = realm_dn
            self.container = self.realm
            self.location = self.realm.lower()

    def __show_properties(self, dn):
        currentItem = self.conn.obj(dn)
        if six.b('computer') in currentItem[1]['objectClass']:
            edit = ComputerProps(self.conn, currentItem)
        elif six.b('user') in currentItem[1]['objectClass']:
            edit = UserProps(self.conn, currentItem)
        elif six.b('group') in currentItem[1]['objectClass']:
            edit = GroupProps(self.conn, currentItem)
        else:
            return

        edit.Show()

    def Show(self):
        UI.SetApplicationTitle('Find Users, Contacts, and Groups')
        UI.OpenDialog(self.__dialog())
        while True:
            ret = UI.UserInput()
            if str(ret) == 'abort' or str(ret) == 'cancel':
                ret = None
                break
            elif str(ret) == 'find':
                location = UI.QueryWidget('obj_container', 'Value')
                if location == self.location:
                    location = self.container
                elif location == self.realm:
                    location = self.realm
                obj_type = UI.QueryWidget('obj_type', 'Value')
                name = UI.QueryWidget('name', 'Value')
                if name:
                    name = filter_format('(name=%s*)(cn=%s*)(sAMAccountName=%s*)', (name, name, name))
                desc = UI.QueryWidget('description', 'Value')
                if desc:
                    desc = filter_format('(description=%s*)', (desc,))
                if not name and not desc:
                    continue
                if obj_type == 'Users, Contacts, and Groups':
                    query = '(&(|%s%s)(|(objectClass=person)(objectClass=group)))' % (name, desc)
                    results = self.conn.ldap_search(location, SUBTREE, query, ['name', 'description', 'objectClass'])
                elif obj_type == 'Computers':
                    query = '(&(|%s%s)(objectCategory=computer))' % (name, desc)
                    results = self.conn.ldap_search(location, SUBTREE, query, ['name', 'description', 'objectClass'])
                UI.ReplaceWidget('search_results', self.search_results(results))
            elif str(ret) == 'results_table':
                dn = UI.QueryWidget('results_table', 'Value')
                self.__show_properties(dn)
        UI.CloseDialog()
        return ret

    def __search_buttons(self):
        return VBox(
            PushButton(Id('find'), 'Find Now'),
            PushButton(Id('cancel'), 'Cancel'),
        )

    def __user_search(self):
        return Frame('Users, Contacts, and Groups',
            VBox(VSpacing(1), HBox(
                VBox(
                    Left(Label('Name:')),
                    Left(Label('Description:')),
                ),
                VBox(
                    Left(TextEntry(Id('name'), '')),
                    Left(TextEntry(Id('description'), '')),
                ),
                self.__search_buttons()
            ))
        )

    def search_results(self, results):
        if not results or len(results) < 1:
            return Empty()
        items = [Item(Id(r[0]), r[-1]['name'][-1], r[-1]['objectClass'][-1].title(), r[-1]['description'][-1] if 'description' in r[-1] else '') for r in results]
        return VBox(
            Left(Label('Search results:')),
            VSpacing(.3),
            MinHeight(10,
                Table(Id('results_table'), Opt('notify'), Header('Name', 'Type', 'Description'), items),
            ),
            VSpacing(.3),
        )

    def __dialog(self):
        containers = [Item(self.location, True)]
        if self.location != self.realm.lower():
            containers.append(self.realm.lower())
        return MinSize(50, 10, HBox(HSpacing(3), VBox(VSpacing(.3),
            Left(HBox(
                Label('Find:'),
                ComboBox(Id('obj_type'), '', [Item('Users, Contacts, and Groups', True), 'Computers']),
                Label('In:'),
                ComboBox(Id('obj_container'), '', containers)
            )),
            VSpacing(1),
            Left(
                self.__user_search()
            ),
            ReplacePoint(Id('search_results'), Empty()),
            VSpacing(.3)
        ), HSpacing(3)))

class ADUC:
    def __init__(self, lp, creds):
        self.realm = lp.get('realm')
        self.lp = lp
        self.creds = creds
        self.__setup_menus()
        ycred = YCreds(creds)
        self.got_creds = ycred.get_creds()
        while self.got_creds:
            try:
                self.conn = Connection(lp, creds)
                break
            except Exception as e:
                ycpbuiltins.y2error(str(e))
                self.got_creds = ycred.get_creds()

    def __setup_menus(self, container=False, obj=False):
        menus = [{'title': '&File', 'id': 'file', 'type': 'Menu'},
                 {'title': 'Exit', 'id': 'abort', 'type': 'MenuEntry', 'parent': 'file'},
                 {'title': 'Action', 'id': 'action', 'type': 'Menu'}]
        if container:
            menus.append({'title': 'Find...', 'id': 'find', 'type': 'MenuEntry', 'parent': 'action'})
            menus.append({'title': 'New', 'id': 'new_but', 'type': 'SubMenu', 'parent': 'action'})
            menus.append({'title': 'User', 'id': 'context_add_user', 'type': 'MenuEntry', 'parent': 'new_but'})
            menus.append({'title': 'Group', 'id': 'context_add_group', 'type': 'MenuEntry', 'parent': 'new_but'})
            menus.append({'title': 'Computer', 'id': 'context_add_computer', 'type': 'MenuEntry', 'parent': 'new_but'})
            menus.append({'title': 'Refresh', 'id': 'refresh', 'type': 'MenuEntry', 'parent': 'action'})
        elif obj:
            menus.append({'title': 'Delete', 'id': 'delete', 'type': 'MenuEntry', 'parent': 'action'})
            menus.append({'title': 'Properties', 'id': 'properties', 'type': 'MenuEntry', 'parent': 'action'})
        CreateMenu(menus)

    def __delete_selected_obj(self, container):
        currentItemName = UI.QueryWidget('items', 'CurrentItem')
        searchList = self.conn.objects_list(container)
        currentItem = self.__find_by_name(searchList, currentItemName)
        if self.__warn_delete(currentItem[-1]['name'][-1]):
            self.conn.ldap_delete(currentItem[0])

    def __show_properties(self, container):
        searchList = []
        currentItemName = None
        currentItemName = UI.QueryWidget('items', 'CurrentItem')
        searchList = self.conn.objects_list(container)
        currentItem = self.__find_by_name(searchList, currentItemName)
        if currentItem is None:
            return
        if six.b('computer') in currentItem[1]['objectClass']:
            edit = ComputerProps(self.conn, currentItem)
        elif six.b('user') in currentItem[1]['objectClass']:
            edit = UserProps(self.conn, currentItem)
        elif six.b('group') in currentItem[1]['objectClass']:
            edit = GroupProps(self.conn, currentItem)
        else:
            return

        edit.Show()

        # update after property sheet closes
        if edit.tabModel.is_modified():
            self.__refresh(container, currentItemName)

    def __objs_context_menu(self):
        return Term('menu', [
            #Item(Id('context_delegate_control'), 'Delegate Control...'),
            Item(Id('find'), 'Find...'),
            Term('menu', 'New', [
                    Item(Id('context_add_computer'), 'Computer'),
                    #Item(Id('context_add_contact'), 'Contact'),
                    Item(Id('context_add_group'), 'Group'),
                    #Item(Id('context_add_inetorgperson'), 'InetOrgPerson'),
                    #Item(Id('context_add_msmq_queue_alias'), 'MSMQ Queue Alias'),
                    #Item(Id('context_add_printer'), 'Printer'),
                    Item(Id('context_add_user'), 'User'),
                    #Item(Id('context_add_shared_folder'), 'Shared Folder')
                ]),
            Item(Id('refresh'), 'Refresh'),
            #Item(Id('context_properties'), 'Properties'),
            #Item(Id('context_help'), 'Help'),
            ])

    def __obj_context_menu(self):
        return Term('menu', [
            Item(Id('properties'), 'Properties'),
            Item(Id('delete'), 'Delete')
        ])

    def Show(self):
        if not self.got_creds:
            return Symbol('abort')
        Wizard.SetContentsButtons('Active Directory Users and Computers', self.__aduc_page(), self.__help(), 'Back', 'Close')
        menu_open = False
        DeleteButtonBox()
        UI.SetFocus('aduc_tree')
        current_container = None
        while True:
            event = UI.WaitForEvent()
            if 'WidgetID' in event:
                ret = event['WidgetID']
            elif 'ID' in event:
                ret = event['ID']
            else:
                raise Exception('ID not found in response %s' % str(event))
            choice = UI.QueryWidget('aduc_tree', 'Value')
            if str(ret) == 'abort' or (str(ret) == 'cancel' and not menu_open):
                break
            if str(ret) == 'aduc_tree':
                if 'DC=' in choice:
                    current_container = choice
                    self.__refresh(current_container)
                    self.__setup_menus(container=True)
                else:
                    current_container = None
                    UI.ReplaceWidget('rightPane', Empty())
                    self.__setup_menus()
                if event['EventReason'] == 'ContextMenuActivated':
                    if current_container:
                        menu_open = True
                        UI.OpenContextMenu(self.__objs_context_menu())
            elif str(ret) == 'next':
                return Symbol('abort')
            elif str(ret) == 'items':
                if event['EventReason'] == 'ContextMenuActivated':
                    check = UI.QueryWidget('items', 'CurrentItem')
                    if check is None:
                        UI.OpenContextMenu(self.__objs_context_menu())
                    else:
                        UI.OpenContextMenu(self.__obj_context_menu())
                elif event['EventReason'] == 'SelectionChanged':
                    self.__setup_menus(obj=True)
                elif event['EventReason'] == 'Activated':
                    self.__show_properties(current_container)
            elif str(ret) == 'properties':
                self.__show_properties(current_container)
            elif str(ret) == 'context_add_user':
                user = NewObjDialog(self.lp, 'user', current_container).Show()
                if user:
                    self.conn.add_user(user, current_container)
                    self.__refresh(current_container, user['cn'])
            elif str(ret) == 'context_add_group':
                group = NewObjDialog(self.lp, 'group', current_container).Show()
                if group:
                    self.conn.add_group(group, current_container)
                    self.__refresh(current_container, group['name'])
            elif str(ret) == 'context_add_computer':
                computer = NewObjDialog(self.lp, 'computer', current_container).Show()
                if computer:
                    self.conn.add_computer(computer, current_container)
                    self.__refresh(current_container, computer['name'])
            elif str(ret) == 'delete':
                self.__delete_selected_obj(current_container)
                self.__refresh(current_container)
            elif str(ret) == 'find':
                SearchDialog(self.lp, self.conn, current_container).Show()
            elif str(ret) == 'refresh':
                self.__refresh(current_container)
            UI.SetApplicationTitle('Active Directory Users and Computers')
        return Symbol(ret)

    def __warn_delete(self, name):
        if six.PY3 and type(name) is bytes:
            name = name.decode('utf-8')
        ans = False
        UI.SetApplicationTitle('Delete')
        UI.OpenDialog(Opt('warncolor'), HBox(HSpacing(1), VBox(
            VSpacing(.3),
            Label('Are you sure you want to delete \'%s\'?' % name),
            Right(HBox(
                PushButton(Id('yes'), 'Yes'),
                PushButton(Id('no'), 'No')
            )),
            VSpacing(.3),
        ), HSpacing(1)))
        ret = UI.UserInput()
        if str(ret) == 'yes':
            ans = True
        elif str(ret) == 'no' or str(ret) == 'abort' or str(ret) == 'cancel':
            ans = False
        UI.CloseDialog()
        return ans

    def __refresh(self, current_container, obj_id=None):
        if current_container:
            UI.ReplaceWidget('rightPane', self.__objects_tab(current_container))
            if obj_id:
                UI.ChangeWidget('items', 'CurrentItem', obj_id)
        else:
            UI.ReplaceWidget('rightPane', Empty())

    def __help(self):
        return ''

    def __find_by_name(self, alist, name):
        if name:
            for item in alist:
                if strcmp(item[1]['cn'][-1], name):
                    return item
        return None 

    def __objects_tab(self, container):
        items = [Item(obj[1]['cn'][-1], obj[1]['objectClass'][-1].title(), obj[1]['description'][-1] if 'description' in obj[1] else '') for obj in self.conn.objects_list(container)]
        return Table(Id('items'), Opt('notify', 'immediate', 'notifyContextMenu'), Header('Name', 'Type', 'Description'), items)

    def __sub_tree(self, dn):
        tree_containers = self.conn.containers(dn)
        return [Item(Id(c[0]), c[1], False, self.__sub_tree(c[0])) for c in tree_containers]

    def __aduc_tree(self):
        tree_containers = self.conn.containers()
        items = [Item(Id(c[0]), c[1], False, self.__sub_tree(c[0])) for c in tree_containers]

        return VBox(
            Tree(Id('aduc_tree'), Opt('notify', 'immediate', 'notifyContextMenu'), '', [
                Item(self.realm.lower(), True, items),
            ]),
        )

    def __aduc_page(self):
        return HBox(
            HWeight(1, self.__aduc_tree()),
            HWeight(2, ReplacePoint(Id('rightPane'), Empty()))
        )

