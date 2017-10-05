# Makefile.am for aduc/src

yncludedir = ${prefix}/share/YaST2/include/aduc

clientdir = ${prefix}/share/YaST2/clients
client_DATA =			\
	aduc.py

#TODO: This must be modified to python can know from where can import!
ynclude_DATA =			\
	dialogs.py		\
	complex.py

aduc.desktop: aduc.desktop.in
	sed -e 's;[@]CLIENTDIR[@];$(clientdir);g' < $(srcdir)/aduc.desktop.in > $(srcdir)/aduc.desktop

desktopdir = ${prefix}/share/applications/YaST2
desktop_DATA =			\
	aduc.desktop

moduledir = ${prefix}/share/YaST2/modules

# create a symlink for local build, #145327
aduc:
	ln -sf . $@
ycpchook = aduc

EXTRA_DIST = $(client_DATA) $(ynclude_DATA) $(module_DATA) $(desktop_DATA)
