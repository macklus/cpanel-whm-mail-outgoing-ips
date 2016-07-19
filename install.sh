#!/bin/sh
#
# cpanel-whm-mail-outgoing-ips installer
# macklus@debianitas.net
#

echo "Installing cpanel-whm-mail-outgoing-ips plugin"

mkdir -p /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/coi
chmod 700 /usr/local/cpanel/whostmgr/docroot/cgi/cprocks
chmod 700 /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/coi

cp -avf coi.cgi coi.conf /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/coi
chmod -v 755 /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/coi/coi.cgi
chmod -v 644 /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/coi/coi.conf

if [ -e "/usr/local/cpanel/bin/register_appconfig" ]; then
    /usr/local/cpanel/bin/register_appconfig  /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/coi/coi.conf
fi

echo "Done."
exit
