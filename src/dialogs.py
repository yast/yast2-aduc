#!/usr/bin/env python

import copy
from complex import Connection
from yast import *

from syslog import syslog, LOG_INFO, LOG_ERR, LOG_DEBUG, LOG_EMERG, LOG_ALERT

def dump(obj):
    print "len obj %d"%len(obj)
    i = 0
    print "cn %s"%obj[0]
    for key in obj[1].keys():
        value = obj[1][key]
        print "item[%d] key %s value type %s value ->%s<-"%(i,key, type(value), value)
        i = i + 1
            
UserDataModel = {
    'general' : {
        'givenName' : 'First Name:',
        'initials' : 'Initials:',
        'sn' : 'Last name:',
        'displayName' : 'Display name:',
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
            'content' : (lambda model: VBox(HBox(
                Label(Id('street'), 'Street:'),
                RichText(Id('streetAddress'), model.get_value('streetAddress'))),
                Left(InputField(Id('postOfficeBox'), "P.O. Box:", model.get_value('postOfficeBox'))),
                Left(InputField(Id('l'), "City:", model.get_value('l'))),
                Left(InputField(Id('st'), "State/province:", model.get_value('st'))),
                Left(InputField(Id('postalCode'), "Zip/Postal Code:", model.get_value('postalCode',))),
                Left(InputField(Id('co'), "Country/Region:", model.get_value('co'))))),
            'data' : UserDataModel['address'],
            'title' : 'Address'
            },
        'general' : {
            'content' : (lambda model: VBox( Left(HBox(
                InputField(Id('givenName'),"First Name:", model.get_value('givenName')),
                InputField(Id('initials'), "Initials:", model.get_value('initials')))),
                Left(InputField(Id('sn'), "Last name:", model.get_value('sn'))),
                Left(InputField(Id('displayName'), "Display name:", model.get_value('displayName'))),
                Left(InputField(Id('physicalDeliveryOfficeName'), "Office:", model.get_value('physicalDeliveryOfficeName'))),
                Left(InputField(Id('telephoneNumber'), "Telephone number:", model.get_value('telephoneNumber'))),
                Left(InputField(Id('mail'), "E-mail:", model.get_value('mail'))),
                Left(InputField(Id('wWWHomePage'), "Web page:", model.get_value('wWWHomePage')))
            )),
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
            addattr = {}
            for key in self.props_map.keys():
                # filter out temporary placeholder keys  (like idontknow)
                if key.startswith('idontknow'):
                    continue
                if key in self.props_orig.keys():
                    if self.props_map[key] != self.props_orig[key]:
                        print 'attribute %s changed.. old %s -> new %s'%(key, self.props_orig.get(key, [""])[-1], self.get_value(key))
                        modattr[key] = self.props_map[key]
                else:
                    addattr[key] = self.props_map[key]

            conn.update(self.props_map['distinguishedName'][-1], self.props_orig, modattr, addattr)

            
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
        self.current_tab = next_tab
        while True:
            ret = UI.UserInput()
            print "tab dialog input is %s"%ret
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
        print 'TabProps.Handleinput %s'%ret
        if str(ret) in ('ok', 'cancel', 'apply') :
            if str(ret) != 'cancel':
                print 'updating model from tab view %s'%self.current_tab
                self.tabModel.update_from_view(self.contents[self.current_tab]['data'])
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
        print 'UserProps.Handleinput %s'%ret
        return TabProps.HandleInput(self, ret)

ComputerDataModel = {
        'general' : {
            'name' : 'Computer name (pre-Windows 2000):',
            'dNSHostName' : 'DNS-name:',
            'idontknow' : 'Workstation or server:',
            'description' : 'Description:'
            },
        'operating_system' : {
            'name' : 'Name:',
            'operatingSystemVersion' : 'Operating System:',
            'operatingSystemServicePack' : 'Service Pack:'
            },
        'location' : {
            'location' : 'Location:'
            },
        }

ComputerTabContents = {
        'general' : {
            'content' : (lambda model: VBox(
                InputField(Id('name'), Opt('disabled'), "Computer name (pre-Windows 2000):", model.get_value('name')),
                InputField(Id('dNSHostName'), Opt('disabled'), "DNS-name:", model.get_value('dNSHostName')),
                # #TODO find out what attribute site is
                InputField(Id('idontknow'), Opt('disabled'), "Site:", "Workstation or server"),
                InputField(Id('description'), "Description:", model.get_value('description')))),

            'data' : ComputerDataModel['general'],
            'title': 'General'
            },

        'operating_system' : {
            'content' : (lambda model: VBox(
                  InputField(Id('name'), Opt('disabled'),"Name:", model.get_value('operatingSystem')),
                  InputField(Id('operatingSystemVersion'), Opt('disabled'), "Operating System", model.get_value('operatingSystemVersion')),
                  InputField(Id('operatingSystemServicePack'), Opt('disabled'), "Service Pack:", model.get_value('operatingSystemServicePack')))),
            'data' : ComputerDataModel['operating_system'],
            'title': 'Operating System'
            },
        'location' : {
            'content' : (lambda model: VBox(
                TextEntry(Id('location'), "Location", model.get_value('location')))),
            'data' : ComputerDataModel['location'],
            'title': 'Location'
            }
        }

class ComputerProps(TabProps):
    def __init__(self, conn, obj):
        TabProps.__init__(self, conn, obj, ComputerTabContents, 'general')

    def multitab(self):
        # 2 problems here,
        #  * ComputerTabContents.keys() doesn't return
        #    the tabs in the desired order (that's just because of the way
        #    python sorts the keys)
        #  * We can't set the initial tab that is selected, we fake
        #    this by making sure 'general' (which is the desired initial_tab)
        #    is the first tab. This seems a problem with the bindings
        TabOrder = ('general', 'operating_system', 'location')

        multi = VBox(
          DumbTab(Id('multitab'),
            [
#               Item(Id(key), ComputerTabContents[key]['title']) for key in ComputerTabContents.keys()
               Item(Id(key), ComputerTabContents[key]['title']) for key in TabOrder 
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
            self.users = self.conn.user_group_list()
            self.computers = self.conn.computer_list()
        except Exception as e:
          syslog(LOG_EMERG, str(e))

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
                searchList = []
                currentItemName = None
                if choice == 'Users':
                    currentItemName = UI.QueryWidget('user_items', 'CurrentItem')
                    searchList = self.users
                elif choice == 'Computers':
                    searchList = self.computers
                    currentItemName = UI.QueryWidget('comp_items', 'CurrentItem')
                currentItem = self.__find_by_name(searchList, currentItemName)
                if choice == 'Computers':
                    edit = ComputerProps(self.conn, currentItem)
                else:
                    edit = UserProps(self.conn, currentItem)
                edit.Show()

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
        items = [Item(user[1]['cn'][-1], user[1]['objectClass'][-1].title(), user[1]['description'][-1] if 'description' in user[1] else '') for user in self.users]
        return Table(Id('user_items'), Header('Name', 'Type', 'Description'), items)

    def __computer_tab(self):
        items = [Item(comp[1]['cn'][-1], comp[1]['objectClass'][-1].title(), comp[1]['description'][-1] if 'description' in comp[1] else '') for comp in self.computers]
        return Table(Id('comp_items'), Header('Name', 'Type', 'Description'), items)

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

