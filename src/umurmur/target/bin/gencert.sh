#!/bin/sh
# Copyright 2010 Antoine Bertin
# <diaoulael [ignore this] at users.sourceforge period net>
#
# This file is part of syno-packager.
#
# syno-packager is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# syno-packager is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with syno-packager.  If not, see <http://www.gnu.org/licenses/>.

# Certificate generation
/usr/local/umurmur/bin/openssl req -x509 -newkey rsa:1024 -keyout /usr/local/umurmur/etc/umurmur.key -nodes -sha1 -days 365 -out /usr/local/umurmur/etc/umurmur.crt -config /usr/local/umurmur/var/openssl.cnf < /usr/local/umurmur/var/cert.fields > /dev/null 2>&1

# Exit status for further use in postinst
if [ $? -ne 0 ]; then
	echo "Certificate generation for uMurmur failed"
	exit 1
fi

echo "uMurmur's certificate successfuly generated"
exit 0
