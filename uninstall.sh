#!/bin/sh

cd /
/usr/local/cpanel/bin/unregister_appconfig coi

/bin/rm -Rfv /usr/local/cpanel/whostmgr/docroot/cgi/cprocks/ 

echo "Done."
exit
