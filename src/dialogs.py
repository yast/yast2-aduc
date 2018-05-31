#!/usr/bin/env python

from __future__ import absolute_import, division, print_function, unicode_literals
import copy
from complex import Connection
from yast import import_module
import_module('Wizard')
import_module('UI')
from yast import *

from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT

def dump(obj):
    print("len obj %d" % len(obj))
    i = 0
    print("cn %s" % obj[0])
    for key in obj[1].keys():
        value = obj[1][key]
        print("item[%d] key %s value type %s value ->%s<-" % (i,key, type(value), value))
        i = i + 1
            
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
        'co' : 'Country/Region:' }
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
            }
        }

class TabModel:
    def __init__(self, props_map):
        self.props_orig = props_map
        self.props_map = copy.deepcopy(props_map)
        self.modified = False
    def set_value(self, key, value):
        oldvalue = self.props_map.get(key, [""])[-1]
        if value != oldvalue:
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
                    if self.props_map[key] != self.props_orig[key]:
                        print('attribute %s changed.. old %s -> new %s' % (key, self.props_orig.get(key, [])[-1], self.get_value(key)))
                        if len(self.props_map[key]):
                            print("deleting %s" % key)
                            modattr[key] = []
                        else:
                            modattr[key] = self.props_map[key]
                else:
                    print('attribute was added %s ->%s<-'%(key, self.props_map[key]))
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
        dump(obj)

    def __multitab(self):
        raise NotImplementedError()

    def Show(self):
        UI.OpenDialog(self.multitab())
        next_tab = self.initial_tab
        UI.ChangeWidget('multitab', 'CurrentItem', Id(next_tab))
        self.current_tab = next_tab
        while True:
            ret = UI.UserInput()
            print("tab dialog input is %s"%ret)
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
        print('TabProps.Handleinput %s'%ret)
        if str(ret) in ('ok', 'cancel', 'apply') :
            print('updating model from tab view %s'%self.current_tab)
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
        print('UserProps.Handleinput %s'%ret)
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
                InputField(Id('dNSHostName'), Opt('disabled', 'hstretch'), ComputerDataModel['general']['name'], model.get_value('dNSHostName')),
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

class ADUC:
    def __init__(self, lp, creds):
        self.__get_creds(creds)
        self.realm = lp.get('realm')
        self.lp = lp
        self.creds = creds
        try:
            self.conn = Connection(lp, creds)
        except Exception as e:
          syslog(LOG_EMERG, str(e))
    def users(self): 
        users = {}
        try:
            users = self.conn.user_group_list()
        except Exception as e:
            syslog(LOG_EMERG, str(e))
        return users
    def computers(self):
        computers = {}
        try:
            computers = self.conn.computer_list()
        except Exception as e:
            syslog(LOG_EMERG, str(e))
        return computers

    def __get_creds(self, creds):
        if not creds.get_username() or not creds.get_password():
            UI.OpenDialog(self.__password_prompt(creds.get_username(), creds.get_password()))
            while True:
                subret = UI.UserInput()
                if str(subret) == 'creds_ok':
                    user = UI.QueryWidget('username_prompt', 'Value')
                    password = UI.QueryWidget('password_prompt', 'Value')
                    creds.set_username(user)
                    creds.set_password(password)
                if str(subret) == 'creds_cancel' or str(subret) == 'creds_ok':
                    UI.CloseDialog()
                    break

    def __password_prompt(self, user, password):
        return MinWidth(30, VBox(
            Left(TextEntry(Id('username_prompt'), Opt('hstretch'), 'Username')),
            Left(Password(Id('password_prompt'), Opt('hstretch'), 'Password')),
            Right(HBox(
                PushButton(Id('creds_ok'), 'OK'),
                PushButton(Id('creds_cancel'), 'Cancel'),
            ))
        ))

    def __show_properties(self, prop_sheet_name):
        searchList = []
        currentItemName = None
        if prop_sheet_name == 'Users':
            currentItemName = UI.QueryWidget('user_items', 'CurrentItem')
            searchList = self.users()
            currentItem = self.__find_by_name(searchList, currentItemName)
            edit = UserProps(self.conn, currentItem)
        elif prop_sheet_name == 'Computers':
            searchList = self.computers()
            currentItemName = UI.QueryWidget('comp_items', 'CurrentItem')
            currentItem = self.__find_by_name(searchList, currentItemName)
            edit = ComputerProps(self.conn, currentItem)

        edit.Show()

        # update after property sheet closes
        if edit.tabModel.is_modified():
            if prop_sheet_name == 'Users':
                UI.ReplaceWidget('rightPane', self.__users_tab())
                UI.ChangeWidget('user_items', 'CurrentItem', currentItemName)
            elif prop_sheet_name == 'Computers':
                UI.ReplaceWidget('rightPane', self.__computer_tab())
                UI.ChangeWidget('comp_items', 'CurrentItem', currentItemName)
            else:
                UI.ReplaceWidget('rightPane', Empty())

    def Show(self):
        Wizard.SetContentsButtons('Active Directory Users and Computers', self.__aduc_page(), self.__help(), 'Back', 'Edit')
        Wizard.DisableBackButton()
        UI.SetFocus('aduc_tree')
        while True:
            ret = UI.UserInput()
            choice = UI.QueryWidget('aduc_tree', 'Value')
            if str(ret) == 'abort' or str(ret) == 'cancel':
                break
            elif str(ret) == 'aduc_tree':
                if choice == 'Users':
                    UI.ReplaceWidget('rightPane', self.__users_tab())
                elif choice == 'Computers':
                    UI.ReplaceWidget('rightPane', self.__computer_tab())
                else:
                    UI.ReplaceWidget('rightPane', Empty())
            elif str(ret) == 'next':
                self.__show_properties(choice)
            elif str(ret) == 'user_items':
                self.__show_properties('Users')
            elif str(ret) == 'comp_items':
                self.__show_properties('Computers')

        return ret

    def __help(self):
        return ''
    def __find_by_name(self, alist, name):
        if name:
            for item in alist:
                
                if item[1]['cn'][-1] == name:
                    return item
        return None 
    def __users_tab(self):
        items = [Item(user[1]['cn'][-1], user[1]['objectClass'][-1].title(), user[1]['description'][-1] if 'description' in user[1] else '') for user in self.users()]
        return Table(Id('user_items'), Opt('notify'), Header('Name', 'Type', 'Description'), items)

    def __computer_tab(self):
        items = [Item(comp[1]['cn'][-1], comp[1]['objectClass'][-1].title(), comp[1]['description'][-1] if 'description' in comp[1] else '') for comp in self.computers()]
        return Table(Id('comp_items'), Opt('notify'), Header('Name', 'Type', 'Description'), items)

    def __aduc_tree(self):
        return Tree(Id('aduc_tree'), Opt('notify'), 'Active Directory Users and Computers', [
            Item(self.realm.lower(), True, [
                Item('Users', True),
                Item('Computers', True),
            ]),
        ])

    def __aduc_page(self):
        return HBox(
            HWeight(1, self.__aduc_tree()),
            HWeight(2, ReplacePoint(Id('rightPane'), Empty()))
        )

