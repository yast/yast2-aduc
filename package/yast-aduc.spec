#
# spec file for package yast-aduc
#
# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           yast-aduc
Version:        1.0
Release:        0
Summary:        Active Directory Users and Computers for YaST
License:        GPL-3.0
Group:          Productivity/Networking/Samba
Url:            http://www.github.com/dmulder/yast-aduc
Source:         %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       krb5-client
Requires:       samba-client
Requires:       samba-python
Requires:       yast2
Requires:       yast2-python-bindings >= 4.0.0
Requires:       python2-ldap3
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  perl-XML-Writer
BuildRequires:  python
BuildRequires:  update-desktop-files
BuildRequires:  yast2
BuildRequires:  yast2-devtools
BuildRequires:  yast2-testsuite

%description
The Active Directory Users and Computers for YaST module provides tools for
creating and modifying Users, Groups, and Computer objects in Active Directory.

%prep
%setup -q

%build
autoreconf -if
%configure --prefix=%{_prefix}
make

%install
make DESTDIR=$RPM_BUILD_ROOT install

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%dir %{_datadir}/YaST2/include/aduc
%{_datadir}/YaST2/clients/aduc.py
%{_datadir}/YaST2/include/aduc/complex.py
%{_datadir}/YaST2/include/aduc/dialogs.py
%{_datadir}/YaST2/include/aduc/wizards.py
%{_datadir}/YaST2/include/aduc/defaults.py
%{_datadir}/applications/YaST2/aduc.desktop
%dir %{_datadir}/doc/yast2-aduc
%{_datadir}/doc/yast2-aduc/COPYING

%changelog
