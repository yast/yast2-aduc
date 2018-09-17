#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
import copy
from complex import Connection, strcmp
from random import randint
from yast import import_module
import_module('Wizard')
import_module('UI')
from yast import *
import six

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
        'sAMAccountName' : 'User Logon name (pre-windows 2000):' }
    }

UserTabContents = {
        'address' : {
            'content' : (lambda model: MinSize(50, 30, VBox(HBox(
                Label(Id('street'), UserDataModel['address']['streetAddress']),
                RichText(Id('streetAddress'), model.get_value('streetAddress'))),
                Left(InputField(Id('postOfficeBox'), Opt('hstretch'), UserDataModel['address']['postOfficeBox'], model.get_value('postOfficeBox'))),
                Left(InputField(Id('l'), Opt('hstretch'), UserDataModel['address']['l'], model.get_value('l'))),
                Left(InputField(Id('st'), Opt('hstretch'), UserDataModel['address']['st'], model.get_value('st'))),
                Left(InputField(Id('postalCode'), Opt('hstretch'), UserDataModel['address']['postalCode'], model.get_value('postalCode',))),
                Left(InputField(Id('co'), Opt('hstretch'), UserDataModel['address']['co'], model.get_value('co')))))),
            'data' : UserDataModel['address'],
            'title' : 'Address'
            },
        'general' : {
            'content' : (lambda model: MinSize(50, 30, VBox(Left(HBox(
                InputField(Id('givenName'), Opt('hstretch'), UserDataModel['general']['givenName'], model.get_value('givenName')),
                InputField(Id('initials'), Opt('hstretch'), UserDataModel['general']['initials'], model.get_value('initials')))),
                Left(InputField(Id('sn'), Opt('hstretch'), UserDataModel['general']['sn'], model.get_value('sn'))),
                Left(InputField(Id('displayName'), Opt('hstretch'), UserDataModel['general']['displayName'], model.get_value('displayName'))),
                Left(InputField(Id('description'), Opt('hstretch'), UserDataModel['general']['description'], model.get_value('description'))),
                Left(InputField(Id('physicalDeliveryOfficeName'), Opt('hstretch'), UserDataModel['general']['physicalDeliveryOfficeName'], model.get_value('physicalDeliveryOfficeName'))),
                Left(InputField(Id('telephoneNumber'), Opt('hstretch'), UserDataModel['general']['telephoneNumber'], model.get_value('telephoneNumber'))),
                Left(InputField(Id('mail'), Opt('hstretch'), UserDataModel['general']['mail'], model.get_value('mail'))),
                Left(InputField(Id('wWWHomePage'), Opt('hstretch'), UserDataModel['general']['wWWHomePage'], model.get_value('wWWHomePage')))
            ))),
            'data' : UserDataModel['general'],
            'title' : 'General'
            },
        'account' : {
            'content' : (lambda model: MinSize(50, 30, VBox(
                InputField(Id('userPrincipalName'), Opt('hstretch'), UserDataModel['account']['userPrincipalName'], model.get_value('userPrincipalName')),
                InputField(Id('sAMAccountName'), Opt('hstretch'), UserDataModel['account']['sAMAccountName'], model.get_value('sAMAccountName')),
            ))),
            'data' : UserDataModel['account'],
            'title' : 'Account'
        }
        }

class TabModel:
    def __init__(self, props_map):
        self.props_orig = props_map
        self.props_map = copy.deepcopy(props_map)
        self.modified = False
    def set_value(self, key, value):
        oldvalue = self.props_map.get(key, [six.b("")])[-1]
        value = six.b(value) if six.PY3 else value
        if not strcmp(value, oldvalue):
            self.props_map[key] = [value]
            if not self.modified:
                self.modified = True
    def get_value(self, key):
        value = self.props_map.get(key, [""])[-1]
        return value

    def is_modified(self):
        return self.modified

    def update_from_view(self, tabData):
        for key in tabData.keys():
            value = UI.QueryWidget(key, 'Value')
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
        #dump(obj)

    def __multitab(self):
        raise NotImplementedError()

    def Show(self):
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
                    self.tabModel.update_from_view(self.contents[previous_tab]['data'])
                    #switch tabs
                    UI.ReplaceWidget('tabContents', self.contents[next_tab]['content'](self.tabModel))
                    self.current_tab = next_tab
            if self.HandleInput(ret):
                break

   # return True (continue processing user input)
   # return False to break out
    def HandleInput(self, ret):
        ycpbuiltins.y2debug('TabProps.Handleinput %s'%ret)
        if str(ret) in ('ok', 'cancel', 'apply') :
            ycpbuiltins.y2debug('updating model from tab view %s'%self.current_tab)
            self.tabModel.update_from_view(self.contents[self.current_tab]['data'])
            if str(ret) != 'cancel':
                self.tabModel.apply_changes(self.conn)
            if str(ret) == 'apply':
                return False
            UI.CloseDialog()
            return True
        return False

class UserProps(TabProps):
    def __init__(self, conn, obj):
        TabProps.__init__(self, conn, obj, UserTabContents, 'general')

    def multitab(self):
        multi = VBox(
          DumbTab(Id('multitab'),
            [
               Item(Id(key), self.contents[key]['title']) for key in self.contents.keys()
            ],
            Left(
                Top(
                    VBox(
                        VSpacing(0.3),
                        HBox(
                            HSpacing(1), ReplacePoint(Id('tabContents'), UserTabContents[self.initial_tab]['content'](self.tabModel)))
                        )
                    )
                )
          ), # true: selected
          HBox(PushButton(Id('ok'), "OK"), PushButton(Id('cancel'), "Cancel"),
              PushButton(Id('apply'), "Apply"))
        )
        return multi

   # return True (continue processing user input)
   # return False to break out
    def HandleInput(self, ret):
        ycpbuiltins.y2debug('UserProps.Handleinput %s'%ret)
        return TabProps.HandleInput(self, ret)

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
            'content' : (lambda model: MinSize(50, 30, VBox(
                InputField(Id('name'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['name'], model.get_value('name')),
                InputField(Id('dNSHostName'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['dNSHostName'], model.get_value('dNSHostName')),
                # #TODO find out what attribute site is
                InputField(Id('idontknow'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['idontknow'], "Workstation or server"),
                InputField(Id('description'), Opt('hstretch'), ComputerDataModel['general']['description'], model.get_value('description'))))),

            'data' : ComputerDataModel['general'],
            'title': 'General'
            },

        'operating_system' : {
            'content' : (lambda model: MinSize(50, 30, VBox(
                  InputField(Id('operatingSystem'), Opt('disabled', 'hstretch'), ComputerDataModel['operating_system']['operatingSystem'], model.get_value('operatingSystem')),
                  InputField(Id('operatingSystemVersion'), Opt('disabled', 'hstretch'),ComputerDataModel['operating_system']['operatingSystemVersion'], model.get_value('operatingSystemVersion')),
                  InputField(Id('operatingSystemServicePack'), Opt('disabled', 'hstretch'), ComputerDataModel['operating_system']['operatingSystemServicePack'], model.get_value('operatingSystemServicePack'))))),
            'data' : ComputerDataModel['operating_system'],
            'title': 'Operating System'
            },
        'location' : {
            'content' : (lambda model: MinSize(50, 30, VBox(
                TextEntry(Id('location'), Opt('hstretch'), ComputerDataModel['location']['location'], model.get_value('location'))))),
            'data' : ComputerDataModel['location'],
            'title': 'Location'
            }
        }

class ComputerProps(TabProps):
    def __init__(self, conn, obj):
        TabProps.__init__(self, conn, obj, ComputerTabContents, 'general')

    def multitab(self):
        multi = VBox(
          DumbTab(Id('multitab'),
            [
               Item(Id(key), ComputerTabContents[key]['title']) for key in ComputerTabContents.keys() 
            ],
            Left(
                Top(
                    VBox(
                        VSpacing(0.3),
                        HBox(
                            HSpacing(1), ReplacePoint(Id('tabContents'), ComputerTabContents[self.initial_tab]['content'](self.tabModel)))
                        )
                    )
                )
          ), # true: selected
          HBox(PushButton(Id('ok'), "OK"), PushButton(Id('cancel'), "Cancel"),
              PushButton(Id('apply'), "Apply"))
        )

        return multi

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
                TextEntry(Id('uidNumber'), 'UID number:', str(randint(1000, 32767))),
                TextEntry(Id('gidNumber'), 'GID number:'),
                TextEntry(Id('gecos'), 'GECOS:'),
                TextEntry(Id('homeDirectory'), 'Home directory:'),
                TextEntry(Id('loginShell'), 'Login shell:', '/bin/sh'),
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
                Left(Password(Id('userPassword'), 'Password:')),
                Left(Password(Id('confirm_passwd'), 'Confirm password:')),
                Left(CheckBox(Id('must_change_passwd'), 'User must change password at next logon', True)),
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
                TextEntry(Id('sAMAccountName'), 'Group name (pre-Windows 2000):'),
                TextEntry(Id('gidNumber'), 'GID number:', str(randint(1000, 32767))),
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

class ADUC:
    def __init__(self, lp, creds):
        self.realm = lp.get('realm')
        self.lp = lp
        self.creds = creds
        self.got_creds = self.__get_creds(creds)
        while self.got_creds:
            try:
                self.conn = Connection(lp, creds)
                break
            except Exception as e:
                ycpbuiltins.y2error(str(e))
                creds.set_password('')
                self.got_creds = self.__get_creds(creds)


    def __delete_selected_obj(self, container):
        currentItemName = UI.QueryWidget('items', 'CurrentItem')
        searchList = self.conn.objects_list(container)
        currentItem = self.__find_by_name(searchList, currentItemName)
        self.conn.delete_obj(currentItem[0])

    def __get_creds(self, creds):
        if not creds.get_password():
            UI.OpenDialog(self.__password_prompt(creds.get_username()))
            while True:
                subret = UI.UserInput()
                if str(subret) == 'creds_ok':
                    user = UI.QueryWidget('username_prompt', 'Value')
                    password = UI.QueryWidget('password_prompt', 'Value')
                    UI.CloseDialog()
                    if not password:
                        return False
                    creds.set_username(user)
                    creds.set_password(password)
                    return True
                if str(subret) == 'creds_cancel':
                    UI.CloseDialog()
                    return False
        return True

    def __password_prompt(self, user):
        return MinWidth(30, HBox(HSpacing(1), VBox(
            VSpacing(.5),
            Left(Label('To continue, type an administrator password')),
            Left(TextEntry(Id('username_prompt'), Opt('hstretch'), 'Username', user)),
            Left(Password(Id('password_prompt'), Opt('hstretch'), 'Password')),
            Right(HBox(
                PushButton(Id('creds_ok'), 'OK'),
                PushButton(Id('creds_cancel'), 'Cancel'),
            )),
            VSpacing(.5)
        ), HSpacing(1)))

    def __show_properties(self, container):
        searchList = []
        currentItemName = None
        currentItemName = UI.QueryWidget('items', 'CurrentItem')
        searchList = self.conn.objects_list(container)
        currentItem = self.__find_by_name(searchList, currentItemName)
        if six.b('computer') in currentItem[1]['objectClass']:
            edit = ComputerProps(self.conn, currentItem)
        elif six.b('user') in currentItem[1]['objectClass']:
            edit = UserProps(self.conn, currentItem)
        else:
            return

        edit.Show()

        # update after property sheet closes
        if edit.tabModel.is_modified():
            self.__refresh(container, currentItemName)

    def __objs_context_menu(self):
        return Term('menu', [
            #Item(Id('context_delegate_control'), 'Delegate Control...'),
            #Item(Id('context_find'), 'Find...'),
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
            #Item(Id('context_refresh'), 'Refresh'),
            #Item(Id('context_properties'), 'Properties'),
            #Item(Id('context_help'), 'Help'),
            ])

    def __obj_context_menu(self):
        return Term('menu', [
            Item(Id('delete'), 'Delete')
        ])

    def Show(self):
        if not self.got_creds:
            return Symbol('abort')
        Wizard.SetContentsButtons('Active Directory Users and Computers', self.__aduc_page(), self.__help(), 'Back', 'Close')
        Wizard.HideBackButton()
        Wizard.HideAbortButton()
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
            menu_open = False
            if str(ret) == 'aduc_tree':
                if event['EventReason'] == 'ContextMenuActivated':
                    if 'DC=' in choice:
                        current_container = choice
                    if current_container:
                        menu_open = True
                        UI.OpenContextMenu(self.__objs_context_menu())
                elif 'DC=' in choice:
                    current_container = choice
                    self.__refresh(current_container)
                    if not have_advanced_gui:
                        UI.ReplaceWidget('new_but',  MenuButton(Id('new'), "New", [
                            Item(Id('context_add_user'), 'User'),
                            Item(Id('context_add_group'), 'Group'),
                            Item(Id('context_add_computer'), 'Computer')
                        ]))
                        UI.ChangeWidget(Id('delete'), "Enabled", True)
                else:
                    current_container = None
                    UI.ReplaceWidget('rightPane', Empty())
                    if not have_advanced_gui:
                        UI.ReplaceWidget('new_but',  MenuButton(Id('new'), Opt('disabled'), "New", []))
                        UI.ChangeWidget(Id('delete'), "Enabled", False)
            elif str(ret) == 'next':
                return Symbol('abort')
            elif str(ret) == 'items':
                if event['EventReason'] == 'ContextMenuActivated':
                    UI.OpenContextMenu(self.__obj_context_menu())
                else:
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
        return ret

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
        return Table(Id('items'), Opt('notify', 'notifyContextMenu'), Header('Name', 'Type', 'Description'), items)

    def __aduc_tree(self):
        tree_containers = self.conn.containers()
        items = [Item(Id(c[0]), c[1], True) for c in tree_containers]
        if not have_advanced_gui:
            menu = HBox(ReplacePoint(Id('new_but'),
                MenuButton(Id('new'), Opt('disabled'), "New", [])),
                PushButton(Id('delete'), Opt('disabled'), "Delete")
            )
        else:
            menu = Empty()

        return VBox(
            Tree(Id('aduc_tree'), Opt('notify', 'immediate', 'notifyContextMenu'), '', [
                Item(self.realm.lower(), True, items),
            ]),
            menu
        )

    def __aduc_page(self):
        return HBox(
            HWeight(1, self.__aduc_tree()),
            HWeight(2, ReplacePoint(Id('rightPane'), Empty()))
        )

